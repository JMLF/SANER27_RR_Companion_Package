"""Enrich candidate repositories with content-based signals for filtering.

Two independent passes, each cached in a JSONL file so runs can be resumed:

* ``hits``  : downloads the files matched by the code search (raw.githubusercontent.com,
              no API quota) and checks whether they really contain training code.
* ``trees`` : fetches the full file tree of the repository (1 GitHub API call per repo)
              to compute structural features (notebook dispersion, slides, packaging...),
              then downloads the README (raw, no quota).

Usage (from the dataset/ directory):

    uv run python src/dataset/enrich.py hits  --input candidates_filtered_v2.csv
    GITHUB_TOKEN=ghp_xxx uv run python src/dataset/enrich.py trees --input candidates_filtered_v2.csv

``--input`` must contain at least ``full_name``, ``default_branch`` and ``files`` (hits pass).
Use ``--limit`` to test on a few repositories, ``--names`` to restrict to a list of repos.
"""

import argparse
import json
import os
import re
import sys
import threading
import time
import tomllib
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path, PurePosixPath

import pandas as pd
from tqdm import tqdm

OUT_DIR = Path("data/enrichment")
UA = "ml-repo-filter/0.1"

# ---------------------------------------------------------------------------
# Training / inference constructs (applied on code only: no markdown, no comments)
# ---------------------------------------------------------------------------

TRAIN_PATTERNS = {
    "fit": r"\.fit(_generator)?\s*\(",
    "partial_fit": r"\.partial_fit\s*\(",
    "train_on_batch": r"\.train_on_batch\s*\(",
    "backward": r"\.backward\s*\(",
    "optimizer_step": r"\b\w*(optimizer|optim|opt)\w*\.step\s*\(",
    "gradient_tape": r"GradientTape\s*\(",
    "trainer_call": r"\b\w*[Tt]rainer\w*\.(train|fit)\s*\(",
    "learn": r"\.learn\s*\(\s*(total_timesteps|\d)",
    "boost_train": r"\b(xgb|lgb|lightgbm|xgboost|catboost)\.(train|cv)\s*\(",
    "search_cv": r"\b(GridSearchCV|RandomizedSearchCV|cross_val_score|cross_validate)\s*\(",
    "train_call": r"\b(model|net|learner|clf|regressor|classifier)\w*\.train\s*\([^)]",
    "train_mode": r"\.train\s*\(\s*\)",
    "trainer_init": r"\b\w*Trainer\s*\(",
    "amp_scaler": r"\b(scaler\.scale|loss_scaler)\s*\(",
    "train_fn_call": r"(?<![\w.])(train|train_model|train_one_epoch|train_epoch|run_epoch|fit_model|finetune|fine_tune)\s*\(\s*[a-zA-Z_]",
    "keras_compile": r"\.compile\s*\(\s*(optimizer|loss)",
}
# early_stopping used as a boolean kwarg is the HF `generate()` beam search option, not training
GENERATE_EARLY_STOP = r"[\"']?early_stopping[\"']?\s*[=:]\s*(True|False)\b"
INFERENCE_PATTERNS = {
    "generate": r"\.generate\s*\(",
    "pipeline": r"\bpipeline\s*\(",
    "llm_api": r"\b(openai|anthropic|ChatOpenAI|ChatAnthropic|genai|ollama|groq)\b",
    "rag": r"\b(vectorstore|VectorStore|retriever|Qdrant|Chroma|FAISS|LlamaIndex|langchain)\b",
}

# ---------------------------------------------------------------------------
# Tree features
# ---------------------------------------------------------------------------

PACKAGING = {"requirements.txt", "setup.py", "setup.cfg", "pyproject.toml", "environment.yml",
             "environment.yaml", "pipfile", "dockerfile", "makefile", "poetry.lock", "uv.lock"}
SLIDES_EXT = {".pdf", ".ppt", ".pptx", ".key", ".odp"}
DATA_EXT = {".csv", ".tsv", ".xlsx", ".xls", ".parquet", ".json", ".zip", ".npy", ".npz", ".pkl", ".h5"}
VENDORED = re.compile(r"(^|/)(\.?venv|env|virtualenv|site-packages|node_modules)(/|$)", re.I)
NUMBERED = re.compile(r"^(\d{1,3}[\s_\-.]|(week|wk|lab|lecture|lesson|day|chapter|ch|hw|ex|task|module|unit|part)[\s_\-.]?\d+)", re.I)
TRAIN_NAME = re.compile(r"(train|fine.?tun|finetun|fit)", re.I)


def strip_code(text: str) -> str:
    """Drop comment lines and docstring-free trailing comments, keep code."""
    out = []
    for line in text.splitlines():
        s = line.lstrip()
        if s.startswith("#"):
            continue
        out.append(line.split("  #")[0])
    return "\n".join(out)


def notebook_code(raw: str) -> str:
    try:
        nb = json.loads(raw)
    except json.JSONDecodeError:
        return raw
    cells = nb.get("cells") or [c for ws in nb.get("worksheets", []) for c in ws.get("cells", [])]
    parts = []
    for cell in cells:
        if cell.get("cell_type") == "code":
            src = cell.get("source", cell.get("input", ""))
            parts.append("".join(src) if isinstance(src, list) else str(src))
    return "\n".join(parts)


def analyse_code(path: str, raw: str) -> dict:
    code = notebook_code(raw) if path.endswith(".ipynb") else raw
    code = strip_code(code)
    train = {k: len(re.findall(p, code)) for k, p in TRAIN_PATTERNS.items()}
    infer = {k: len(re.findall(p, code)) for k, p in INFERENCE_PATTERNS.items()}
    return {
        "n_train": sum(train.values()),
        "train_kinds": [k for k, v in train.items() if v],
        "infer_kinds": [k for k, v in infer.items() if v],
        "generate_early_stopping": bool(re.search(GENERATE_EARLY_STOP, code)),
        "keras_early_stopping": bool(re.search(r"EarlyStopping\s*\(", code)),
        "n_code_lines": sum(1 for l in code.splitlines() if l.strip()),
    }


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------

TRANSIENT = -1  # request failed after all retries: the repo is not cached and is retried on the next run


def load_tokens(secrets: str | None) -> list[str]:
    env = os.environ.get("GITHUB_TOKEN")
    if env:
        return [t.strip() for t in env.split(",") if t.strip()]
    if secrets and Path(secrets).exists():
        gh = tomllib.loads(Path(secrets).read_text()).get("github", {})
        return gh.get("tokens") or ([gh["token"]] if gh.get("token") else [])
    return []


def log(msg: str):
    tqdm.write(msg, file=sys.stderr)


class GitHub:
    """Minimal REST client: picks the token with quota left, waits for the earliest reset when all are exhausted,
    and honours secondary rate limits (403/429 with Retry-After)."""

    def __init__(self, tokens: list[str]):
        self.tokens = tokens or [None]
        self.remaining = {t: None for t in self.tokens}  # None = unknown
        self.reset = {t: 0.0 for t in self.tokens}
        self.pause_until = 0.0
        self.lock = threading.Lock()
        self.n_waits = 0

    def _pick_token(self):
        while True:
            with self.lock:
                now = time.time()
                if self.pause_until > now:
                    wait = self.pause_until - now
                else:
                    for t in self.tokens:  # quota is restored after the reset time
                        if self.remaining[t] == 0 and self.reset[t] <= now:
                            self.remaining[t] = None
                    usable = [t for t in self.tokens if self.remaining[t] != 0]
                    if usable:
                        t = max(usable, key=lambda t: float("inf") if self.remaining[t] is None else self.remaining[t])
                        if self.remaining[t] is not None:
                            self.remaining[t] -= 1  # reserve one call, corrected by the response headers
                        return t
                    wait = min(self.reset.values()) - now + 1
                    self.pause_until = now + wait
                    self.n_waits += 1
                    log(f"[api] all {len(self.tokens)} token(s) exhausted, waiting {wait:.0f}s for the reset")
            time.sleep(max(wait, 1))

    def _update(self, token, headers):
        rem, reset = headers.get("X-RateLimit-Remaining"), headers.get("X-RateLimit-Reset")
        with self.lock:
            if rem is not None:
                self.remaining[token] = int(rem)
            if reset is not None:
                self.reset[token] = float(reset)

    def _pause(self, seconds: float, why: str):
        with self.lock:
            if time.time() + seconds > self.pause_until:
                self.pause_until = time.time() + seconds
                self.n_waits += 1
                log(f"[api] {why}, pausing {seconds:.0f}s")

    def get(self, url: str, retries: int = 6):
        for attempt in range(retries):
            token = self._pick_token()
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/vnd.github+json"})
            if token:
                req.add_header("Authorization", f"Bearer {token}")
            try:
                with urllib.request.urlopen(req, timeout=60) as r:
                    self._update(token, r.headers)
                    return r.status, json.loads(r.read())
            except urllib.error.HTTPError as e:
                self._update(token, e.headers)
                if e.code in (403, 429):
                    if e.headers.get("Retry-After"):  # secondary rate limit
                        self._pause(int(e.headers["Retry-After"]) + 1, f"secondary rate limit ({e.code})")
                        continue
                    if e.headers.get("X-RateLimit-Remaining") == "0":  # primary limit: switch token / wait reset
                        continue
                    if e.code == 429:
                        self._pause(60 * 2 ** attempt, "429 without Retry-After")
                        continue
                    return e.code, None  # 403 forbidden (e.g. DMCA, blocked repo)
                if e.code in (404, 409, 451):  # missing, empty repo, unavailable for legal reasons
                    return e.code, None
                time.sleep(2 ** attempt)  # 5xx
            except (urllib.error.URLError, TimeoutError, ConnectionError, json.JSONDecodeError):
                time.sleep(2 ** attempt)
        return TRANSIENT, None


class RawClient:
    """raw.githubusercontent.com downloads. They do not use the REST quota but are rate limited per IP
    (stricter when unauthenticated): requests are spaced by `min_interval`, and on 429/403 every thread
    pauses with an exponential backoff (or Retry-After) that is reset after successes."""

    def __init__(self, tokens: list[str], max_rps: float):
        self.tokens = [t for t in tokens if t]
        self.min_interval = 1 / max_rps if max_rps > 0 else 0
        self.next_slot = 0.0
        self.pause_until = 0.0
        self.backoff = 30.0
        self.lock = threading.Lock()
        self.i = 0
        self.n_waits = 0

    def _wait_turn(self):
        while True:
            with self.lock:
                now = time.time()
                if self.pause_until <= now:
                    slot = max(now, self.next_slot)
                    self.next_slot = slot + self.min_interval
                    token = self.tokens[self.i % len(self.tokens)] if self.tokens else None
                    self.i += 1
                    break
                wait = self.pause_until - now
            time.sleep(wait)
        time.sleep(max(slot - time.time(), 0))
        return token

    def _rate_limited(self, headers):
        with self.lock:
            retry_after = headers.get("Retry-After") if headers else None
            wait = int(retry_after) + 1 if retry_after and retry_after.isdigit() else self.backoff
            if time.time() + wait > self.pause_until:
                self.pause_until = time.time() + wait
                self.backoff = min(self.backoff * 2, 900)
                self.n_waits += 1
                log(f"[raw] rate limited, pausing {wait:.0f}s")

    def get(self, full_name: str, branch: str, path: str, max_bytes: int = 5_000_000, retries: int = 6):
        url = "https://raw.githubusercontent.com/{}/{}/{}".format(
            full_name, urllib.parse.quote(str(branch), safe=""), urllib.parse.quote(path))
        for attempt in range(retries):
            token = self._wait_turn()
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            if token:
                req.add_header("Authorization", f"token {token}")
            try:
                with urllib.request.urlopen(req, timeout=60) as r:
                    body = r.read(max_bytes).decode("utf-8", errors="replace")
                with self.lock:
                    self.backoff = max(30.0, self.backoff * 0.9)
                return r.status, body
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    return 404, None
                if e.code in (403, 429):
                    self._rate_limited(e.headers)
                    continue
                time.sleep(2 ** attempt)  # 5xx
            except (urllib.error.URLError, TimeoutError, ConnectionError):
                time.sleep(2 ** attempt)
        return TRANSIENT, None


# ---------------------------------------------------------------------------
# Passes
# ---------------------------------------------------------------------------

def done_names(path: Path) -> set[str]:
    if not path.exists():
        return set()
    done = set()
    with path.open() as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            # records written by older versions could hold transient failures: retry them
            statuses = [rec.get("status")] + [x.get("status") for x in rec.get("files", [])]
            if TRANSIENT not in statuses:
                done.add(rec["full_name"])
    return done


def hits_record(raw_client: RawClient, row) -> dict | None:
    """None when a download failed transiently (not cached, retried on the next run)."""
    files = [f for f in str(row.files).split(";") if f and f != "nan"]
    per_file = []
    for path in files[:10]:
        status, raw = raw_client.get(row.full_name, row.default_branch, path)
        if status == TRANSIENT:
            return None
        rec = {"path": path, "status": status}
        if raw is not None:
            rec.update(analyse_code(path, raw))
        per_file.append(rec)
    fetched = [f for f in per_file if f["status"] == 200]
    return {
        "full_name": row.full_name,
        "n_files": len(files),
        "n_fetched": len(fetched),
        "n_missing": sum(f["status"] == 404 for f in per_file),
        "n_files_with_training": sum(f["n_train"] > 0 for f in fetched),
        "train_kinds": sorted({k for f in fetched for k in f["train_kinds"]}),
        "infer_kinds": sorted({k for f in fetched for k in f["infer_kinds"]}),
        "generate_early_stopping": any(f["generate_early_stopping"] for f in fetched),
        "keras_early_stopping": any(f["keras_early_stopping"] for f in fetched),
        "files": per_file,
    }


def tree_record(gh: GitHub, raw_client: RawClient, row) -> dict | None:
    """None when the API call failed transiently (not cached, retried on the next run)."""
    status, data = gh.get(f"https://api.github.com/repos/{row.full_name}/git/trees/"
                          f"{urllib.parse.quote(str(row.default_branch), safe='')}?recursive=1")
    if status == TRANSIENT:
        return None
    rec = {"full_name": row.full_name, "status": status}
    if not data:
        return rec
    blobs = [t["path"] for t in data.get("tree", []) if t["type"] == "blob"]
    real = [p for p in blobs if not VENDORED.search(p)]
    nbs = [p for p in real if p.endswith(".ipynb")]
    pys = [p for p in real if p.endswith(".py")]
    names = [PurePosixPath(p).name for p in real]
    ext = [PurePosixPath(p).suffix.lower() for p in real]
    top = {p.split("/")[0] for p in real if "/" in p}
    nb_dirs = {str(PurePosixPath(p).parent) for p in nbs}
    code_top = {p.split("/")[0] for p in nbs + pys if "/" in p}
    readme = next((p for p in blobs if "/" not in p and p.lower().startswith("readme")), None)
    rec.update({
        "truncated": data.get("truncated", False),
        "n_files": len(real),
        "n_vendored_files": len(blobs) - len(real),
        "n_py": len(pys),
        "n_ipynb": len(nbs),
        "n_ipynb_dirs": len(nb_dirs),
        "n_top_dirs": len(top),
        "n_code_top_dirs": len(code_top),
        "n_numbered_code": sum(bool(NUMBERED.match(PurePosixPath(p).name)) or
                               any(NUMBERED.match(part) for part in PurePosixPath(p).parts[:-1])
                               for p in nbs + pys),
        "n_train_named": sum(bool(TRAIN_NAME.search(PurePosixPath(p).name)) for p in nbs + pys),
        "n_slides": sum(e in SLIDES_EXT for e in ext),
        "n_data": sum(e in DATA_EXT for e in ext),
        "has_packaging": any(n.lower() in PACKAGING for n in names),
        "has_package_dir": any(p.endswith("/__init__.py") for p in pys),
        "max_depth": max((p.count("/") for p in real), default=0),
        "readme_path": readme,
        "train_named_files": [p for p in nbs + pys if TRAIN_NAME.search(PurePosixPath(p).name)][:20],
    })
    if readme:
        readme_status, text = raw_client.get(row.full_name, row.default_branch, readme, max_bytes=20_000)
        if readme_status == TRANSIENT:
            return None
        rec["readme"] = (text or "")[:8000]
    return rec


def run(kind: str, df: pd.DataFrame, workers: int, secrets: str | None, raw_rps: float):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"{kind}.jsonl"
    todo = df[~df.full_name.isin(done_names(out))]
    print(f"{kind}: {len(df) - len(todo)} cached, {len(todo)} to fetch -> {out}")
    tokens = [t for t in load_tokens(secrets) if t]
    print(f"  {len(tokens)} token(s)" + ("" if tokens else
          " - unauthenticated: 60 API req/h, stricter raw.githubusercontent.com limits"))
    raw_client = RawClient(tokens, raw_rps)
    gh = GitHub(tokens) if kind == "trees" else None
    fn = (lambda r: tree_record(gh, raw_client, r)) if kind == "trees" else (lambda r: hits_record(raw_client, r))

    n_ok = n_failed = 0
    with out.open("a") as f, ThreadPoolExecutor(workers) as pool, \
            tqdm(total=len(todo), desc=kind, unit="repo", dynamic_ncols=True) as bar:
        futures = {pool.submit(fn, r): r.full_name for r in todo.itertuples()}
        for fut in as_completed(futures):
            try:
                rec = fut.result()
            except Exception as e:  # a bug on one repo must not lose the whole run
                log(f"[error] {futures[fut]}: {e!r}")
                rec = None
            if rec is None:
                n_failed += 1
            else:
                n_ok += 1
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                f.flush()
            bar.update()
            bar.set_postfix(ok=n_ok, failed=n_failed,
                            waits=raw_client.n_waits + (gh.n_waits if gh else 0), refresh=False)
    if n_failed:
        print(f"{n_failed} repo(s) failed transiently and were not cached: re-run the same command to retry them.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("kind", choices=["hits", "trees"])
    ap.add_argument("--input", required=True, help="CSV with full_name, default_branch, files")
    ap.add_argument("--names", help="optional text file / CSV column 'Repository' restricting the repos")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--secrets", default="../Bagger-GH/secrets.toml")
    ap.add_argument("--raw-rps", type=float, default=10,
                    help="max raw.githubusercontent.com requests per second, all threads (0 = no cap)")
    args = ap.parse_args()

    df = pd.read_csv(args.input, usecols=["full_name", "default_branch", "files"], low_memory=False)
    if args.names:
        p = Path(args.names)
        names = (pd.read_csv(p, sep=None, engine="python").iloc[:, 0] if p.suffix == ".csv"
                 else pd.Series(p.read_text().split()))
        df = df[df.full_name.isin(set(names))]
    if args.limit:
        df = df.head(args.limit)
    run(args.kind, df, args.workers if args.kind == "hits" else min(args.workers, 4), args.secrets, args.raw_rps)


if __name__ == "__main__":
    main()

import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Candidate filtering v2

    Second iteration of the candidate filtering (see `dataset.py` for v1). Every rule is
    **evaluated against the manually labeled repositories** (run1 + run2 + consensus), so we can see
    how many `not_ml_project` it removes and how many true ML projects it loses before using it.

    Rules come in three stages, by cost:

    1. **metadata**: only uses `candidates.csv` (name, description, hit paths, query names).
    2. **hit content**: downloads the matched files (`src/dataset/enrich.py hits`, no API quota).
    3. **repository tree + README**: one API call per repo (`src/dataset/enrich.py trees`).

    Each rule is either `exclude` (drops the repo) or `flag` (kept, annotated for inspection).
    """)
    return


@app.cell
def _():
    import json
    import re
    from pathlib import Path

    import marimo as mo
    import pandas as pd

    RUN_DIR = Path("data/ml-pipelines-20261013-163440")
    ENRICH_DIR = Path("data/enrichment")
    MANUAL_DIR = Path("manual_verification_results")
    return ENRICH_DIR, MANUAL_DIR, RUN_DIR, mo, pd, re


@app.cell
def _(RUN_DIR, pd):
    candidates = pd.read_csv(RUN_DIR / "candidates.csv", low_memory=False)
    candidates["repo_owner"] = candidates["full_name"].str.split("/").str[0]
    candidates["repo_name"] = candidates["full_name"].str.split("/").str[1]
    candidates["hit_files"] = candidates["files"].fillna("").str.split(";")
    candidates = candidates.set_index("full_name", drop=False)
    len(candidates)
    return (candidates,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Labeled repositories (evaluation set)
    """)
    return


@app.cell
def _(MANUAL_DIR, pd):
    def read_labels(path):
        df = pd.read_csv(path, sep=";", dtype=str)
        df = df[["Repository", "Label", "Reason_code"]].dropna(subset=["Label"])
        df["Label"] = df["Label"].str.strip().str.lower()
        return df[df["Label"].isin(["ml_project", "not_ml_project"])]

    # later files override earlier ones (consensus wins)
    labels = pd.concat([
        read_labels(MANUAL_DIR / "run1/consensus_manual_verification.csv"),
        read_labels(MANUAL_DIR / "run2/author_1_manual_verification.csv"),
        read_labels(MANUAL_DIR / "consensus_not_ml_projects.csv"),
    ]).drop_duplicates("Repository", keep="last").set_index("Repository")
    labels["Reason_code"] = labels["Reason_code"].fillna("-")
    labels["Label"].value_counts()
    return (labels,)


@app.cell
def _(candidates, labels, pd):
    def evaluate(rules: pd.DataFrame) -> pd.DataFrame:
        """One row per rule: negatives caught / positives lost on the labeled set, and impact on the population.

        `rules` is a boolean DataFrame indexed by full_name (True = rule matches). NaN = rule not computed.
        """
        lab = labels.join(rules, how="inner")
        neg = lab["Label"] == "not_ml_project"
        rows = []
        for rule in rules.columns:
            hit = lab[rule].fillna(False).astype(bool)
            known = rules[rule].notna()
            rows.append({
                "rule": rule,
                "neg_caught": int((hit & neg).sum()),
                "pos_lost": int((hit & ~neg).sum()),
                "labeled_covered": int(lab[rule].notna().sum()),
                "neg_reasons": ", ".join(f"{k}:{v}" for k, v in lab[hit & neg]["Reason_code"].value_counts().items()),
                "pop_matched": int(rules.loc[known, rule].astype(bool).sum()),
                "pop_covered": int(known.sum()),
                "pop_pct": round(100 * rules.loc[known, rule].astype(bool).mean(), 2) if known.any() else None,
            })
        print(f"labeled: {neg.sum()} not_ml_project / {(~neg).sum()} ml_project, population: {len(candidates)}")
        return pd.DataFrame(rows)

    def matches(rules: pd.DataFrame, rule: str) -> pd.DataFrame:
        """Labeled repositories matched by a rule."""
        lab = labels.join(rules[[rule]], how="inner")
        return lab[lab[rule].fillna(False).astype(bool)][["Label", "Reason_code"]]

    return evaluate, matches


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Stage 0: v1 filters, fixed

    Two bugs in `dataset.py`:

    * `owner.str.lower().isin(name_to_ignore)` compares a lowercase owner with a mixed case list:
      `GoogleCloudPlatform`, `Azure`, `IBM`, `NVIDIA`, `NVlabs`, ... never match (~400 repos slip through).
    * a missing comma after `"kaggle"` creates the single word `"kaggleпример"`, so neither is applied.

    Also, the noise words are matched as **substrings** (`term` removes `Deterministic-…`, `Terminal`,
    `watermarking`; `demo` removes `democracy`). Here they are matched as **tokens** of the name
    (camelCase, `-`, `_`, `.` are split). The unsure words (`notebook`, `colab`, `kaggle`) are a separate rule.
    """)
    return


@app.cell
def _():
    # copied from dataset.py
    name_to_ignore = [
        "google", "google-research", "google-deepmind", "deepmind", "GoogleCloudPlatform",
        "googleapis", "google-gemini", "google-ai-edge", "googlecolab",
        "microsoft", "Azure", "Azure-Samples", "MicrosoftDocs",
        "facebook", "facebookresearch", "facebookincubator", "meta-llama", "pytorch-labs",
        "aws", "awslabs", "aws-samples", "amazon-science",
        "apple", "ml-explore",
        "IBM", "Trusted-AI",
        "NVIDIA", "NVIDIA-AI-IOT", "NVlabs", "rapidsai", "triton-inference-server",
        "intel", "IntelLabs", "intel-analytics", "openvinotoolkit", "oneapi-src", "uxlfoundation",
        "ROCm", "amd", "Xilinx", "quic", "tenstorrent",
        "salesforce", "SalesforceAIResearch", "adobe", "oracle", "SAP",
        "sony", "Netflix", "spotify", "uber", "airbnb", "linkedin", "twitter", "pinterest", "nubank",
        "alibaba", "AlibabaResearch", "modelscope", "Tencent", "baidu", "PaddlePaddle",
        "bytedance", "huawei-noah", "mindspore-ai", "yandex", "naver", "clovaai",
        "INRIA", "opendsm", "schneiderkamplab",
        "openai", "anthropics", "mistralai", "cohere-ai", "deepseek-ai", "QwenLM", "THUDM",
        "01-ai", "InternLM", "OpenGVLab", "OpenBMB", "Stability-AI", "CompVis",
        "EleutherAI", "allenai", "bigscience-workshop", "LAION-AI", "mlfoundations", "lm-sys",
        "togethercomputer", "NousResearch",
        "tensorflow", "keras-team", "pytorch", "jax-ml", "Lightning-AI", "PyTorchLightning",
        "dmlc", "onnx", "huggingface", "fastai", "unifyai", "pyg-team", "deepinv",
        "Deep-Spark", "unslothai", "vllm-project", "ggml-org", "ollama",
        "scikit-learn", "scikit-learn-contrib", "statsmodels", "lightgbm-org", "catboost",
        "autogluon", "skorch-dev", "mlpack", "pycaret", "EpistasisLab", "automl", "mljar",
        "alteryx", "optuna", "hyperopt", "h2oai", "cleanlab", "interpretml",
        "pymc-devs", "pyro-ppl", "stan-dev",
        "geomstats", "pyRiemann", "numenta",
        "sktime", "unit8co", "Nixtla", "tslearn-team", "blue-yonder",
        "explosion", "nltk", "stanfordnlp", "flairNLP", "UKPLab", "RasaHQ", "jina-ai", "deepset-ai",
        "open-mmlab", "ultralytics", "roboflow", "albumentations-team", "kornia",
        "Farama-Foundation", "DLR-RM", "Unity-Technologies",
        "numpy", "scipy", "pandas-dev", "matplotlib", "plotly", "bokeh", "dask", "networkx",
        "apache", "ray-project", "databricks", "databrickslabs", "Snowflake-Labs",
        "langchain-ai", "run-llama", "chroma-core", "qdrant", "weaviate", "milvus-io",
        "zilliztech", "pinecone-io", "towhee-io", "agential-ai",
        "mlflow", "wandb", "comet-ml", "neptune-ai", "aimhubio", "allegroai", "clearml",
        "kubeflow", "bentoml", "iterative", "zenml-io", "kedro-org", "PrefectHQ", "dagster-io",
        "feast-dev", "SeldonIO", "evidentlyai", "great-expectations", "determined-ai",
        "ludwig-ai", "run-house", "streamlit", "gradio-app", "modal-labs", "replicate",
        "DataRobot", "Kaggle",
        "probml",
    ]
    noise_words = [
        "example", "examples", "tutorial", "tutorials", "demo", "demos",
        "docs", "course", "courses", "lecture", "lectures",
        "lesson", "lessons", "term", "terms", "exam", "exams",
        "пример", "примеры", "руководство", "руководства", "туториал", "туториалы",
        "демо", "демонстрация", "тест", "тесты", "документация", "курс", "курсы",
        "лекция", "лекции", "урок", "уроки", "семестр", "семестры", "экзамен", "экзамены",
        "示例", "例子", "范例", "教程", "演示", "测试", "文档", "课程", "讲座", "讲义", "课", "学期", "考试",
    ]
    unsure_words = ["notebook", "notebooks", "colab", "kaggle"]
    # descriptions are free text: "demo" ("includes a Streamlit demo app"), "term" ("long-term"), "exam" and
    # "docs" mostly describe a part of a real project there, so they are only used on names
    noise_words_description = [w for w in noise_words if w not in {
        "demo", "demos", "term", "terms", "exam", "exams", "docs", "демо", "演示", "文档", "документация"}]
    return name_to_ignore, noise_words, noise_words_description, unsure_words


@app.cell
def _(re):
    def tokens(text) -> set[str]:
        """Lowercase word tokens; splits camelCase, digits, `-`, `_`, `.`, spaces."""
        if not isinstance(text, str):
            return set()
        text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)
        text = re.sub(r"([A-Za-z])(\d)|(\d)([A-Za-z])", r"\1\3 \2\4", text)
        return {t for t in re.split(r"[^\w]+|_", text.lower()) if t}

    def has_token(series, words) -> "pd.Series":
        words = {w.lower() for w in words}
        cjk = [w for w in words if not w.isascii() and not re.search(r"[а-я]", w)]  # no word boundaries in CJK
        return series.apply(lambda s: bool(tokens(s) & words) or any(w in str(s) for w in cjk))

    return has_token, tokens


@app.cell
def _(
    candidates,
    has_token,
    name_to_ignore,
    noise_words,
    noise_words_description,
    pd,
    unsure_words,
):
    _ignore = {n.lower() for n in name_to_ignore}
    stage0 = pd.DataFrame({
        "s0_owner_ignored": candidates["repo_owner"].str.lower().isin(_ignore),
        "s0_owner_eq_name": candidates["repo_owner"].str.lower() == candidates["repo_name"].str.lower(),
        "s0_noise_name": has_token(candidates["repo_name"], noise_words),
        "s0_noise_description": has_token(candidates["description"], noise_words_description),
        "s0_unsure_name": has_token(candidates["repo_name"], unsure_words),
        "s0_unsure_description": has_token(candidates["description"], unsure_words),
    }, index=candidates.index)
    return (stage0,)


@app.cell
def _(evaluate, stage0):
    evaluate(stage0)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The labeled repos were sampled **after** v1, so stage 0 should catch almost none of them; what matters is
    whether the fixed version loses positives (e.g. `kaggle` in a name is often a real competition project).

    ## Stage 1: metadata rules

    Observations from the labeled set that drive these rules:

    * `not_ml_project` repos are **bigger, older and have more commits** than ML projects (median 34 vs 15 commits,
      18 MB vs 6 MB), which is why `commit_count` / `open_issues` thresholds did not help: course material and
      personal dumps are long-lived. Thresholds would have to go the *other* way, which is not defensible.
    * 30 of 35 negatives are `file_storage`: personal "Data-Science", "Deep-Learning", course repos.
      Their **names are generic** and their **hit paths look like lessons** (`week02/`, `Task3.ipynb`, `lab3/`).
    * Single-project class assignments (`cv2526-assignment2`, `EC523_LoRA`) are labeled `ml_project`,
      so education words alone must not exclude: they are only a flag.
    """)
    return


@app.cell
def _():
    # Repo names made only of these tokens are generic topic names ("Deep-Learning", "Data_Science.", "AI-study")
    GENERIC_NAME_TOKENS = {
        "machine", "learning", "deep", "data", "science", "sciences", "ai", "ml", "dl", "artificial", "intelligence",
        "inteligencia", "aprendizaje", "automatico", "profundo", "apprentissage", "ia", "ds", "de", "e", "y", "et",
        "projects", "project", "notebooks", "notebook", "study", "studies", "practice", "practices", "python",
        "kaggle", "nlp", "cv", "llm", "llms", "my", "personal", "codes", "code", "scripts", "stuff", "misc",
        "work", "works", "repo", "repository", "neural", "networks", "network", "from", "scratch", "and", "with",
        "the", "of", "for", "in", "pytorch", "tensorflow", "keras", "sklearn", "models", "algorithms",
        "basics", "basic", "fundamentals", "journey", "resources", "notes", "lab", "labs", "exercises",
        "exercise", "homework", "assignments", "learn", "generative", "genai", "engineering", "daily",
        "100", "days", "all", "collection", "computer", "vision", "reinforcement", "statistics", "analytics",
    }
    # Hit paths that look like teaching material: week02/, lab3_, hw1, Milestone4/, lectures/
    # ("task\d" is left out: GSoC / job application tasks are single coherent projects)
    COURSE_PATH = (
        r"(^|/)(week|wk|lab|hw|homework|assignment|lecture|lesson|seminar|practice|exercise|chapter|day|module"
        r"|milestone|sem)[\s_\-.]?\d+"
        r"|(^|/)(assignments?|homeworks?|labs|lectures?|lessons?|seminars?|exercises?|course|coursework)(/|$)"
    )
    # Hits only in vendored deps or benchmarks (path_noise misses `site-packages`: its token matcher splits on `-`)
    VENDORED_PATH = r"(^|/)(\.?venv|env|virtualenv|site-packages|node_modules|third_party|vendor|benchmarks?)(/|$)"
    # Education words (name + description) and course codes (CS229, EC523, MADS508, PHYS 498)
    EDU_WORDS = (
        r"\b(courses?|coursework|lectures?|lessons?|syllabus|bootcamp|curriculum|homeworks?|hw ?\d+|seminars?"
        r"|semester|university|universit[àéy]|materia|cours|kurs|講義|授業|课程|作业|강의|과제|курсы?)\b"
    )
    COURSE_CODE = (
        r"\b(?!(?:COVID|GPT|YOLO|IEEE|ICCV|CVPR|ECCV|NIPS|AAAI|IJCV|IJCAI|ICML|ICLR|SIGIR|MICCAI|LLM|RTX|ESP|ISO)\b)"
        r"[A-Z]{2,5} ?\d{3,4}[A-Z]?\b"
    )
    # Hits coming only from queries whose construct also appears in non-training code
    WEAK_LIBRARIES = {"generic_early_stopping", "generic_mlflow", "generic_tensorboard"}
    # Copies of well known projects that are not GitHub forks
    COPY_NAME = r"yolo(v\d+)?|ultralytics|nanogpt|llama.?factory|stable.?diffusion|detectron2|mmdet|\bfork\b|\bclone\b|\bmirror\b|\bbackup\b"
    return (
        COPY_NAME,
        COURSE_CODE,
        COURSE_PATH,
        EDU_WORDS,
        GENERIC_NAME_TOKENS,
        VENDORED_PATH,
        WEAK_LIBRARIES,
    )


@app.cell
def _(
    COPY_NAME,
    COURSE_CODE,
    COURSE_PATH,
    EDU_WORDS,
    GENERIC_NAME_TOKENS,
    VENDORED_PATH,
    WEAK_LIBRARIES,
    candidates,
    pd,
    re,
    tokens,
):
    def _split(s):
        return re.sub(r"([a-z])([A-Z])", r"\1 \2", s).replace("_", " ").replace("-", " ")

    _text = (candidates["repo_name"] + " " + candidates["description"].fillna("")).map(_split)
    _libs = candidates["libraries"].fillna("").str.replace("generi_", "generic_").str.split(";").map(set)

    stage1 = pd.DataFrame({
        "m_generic_name": candidates["repo_name"].map(lambda n: (t := tokens(n)) != set() and t <= GENERIC_NAME_TOKENS),
        "m_course_paths": candidates["hit_files"].map(lambda fs: any(re.search(COURSE_PATH, f, re.I) for f in fs)),
        "m_vendored_hits_only": candidates["hit_files"].map(lambda fs: all(re.search(VENDORED_PATH, f, re.I) for f in fs)),
        "m_edu_text": _text.str.contains(EDU_WORDS, case=False, regex=True)
                      | _text.str.contains(COURSE_CODE, case=True, regex=True),
        "m_weak_signal_only": _libs.map(lambda s: s <= WEAK_LIBRARIES),
        "m_copy_name": candidates["repo_name"].str.contains(COPY_NAME, case=False, regex=True),
        "m_notebook_hits_only": candidates["hit_files"].map(lambda fs: all(f.endswith(".ipynb") for f in fs)),
    }, index=candidates.index)
    return (stage1,)


@app.cell
def _(evaluate, stage1):
    evaluate(stage1)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    `m_generic_name`, `m_course_paths` and `m_vendored_hits_only` remove negatives with (almost) no loss.
    `m_edu_text`, `m_weak_signal_only`, `m_notebook_hits_only` are too noisy alone: they are flags that can be
    combined with stage 3 structure.

    ## Stage 2: hit content

    `uv run python src/dataset/enrich.py hits --input candidates_stage1.csv` downloads every hit file and looks
    for training constructs (`.fit(`, `.backward(`, `optimizer.step(`, `Trainer(`, `model.train()`, ...) and
    inference constructs (`.generate(`, `pipeline(`, LLM API clients, RAG), on code only (no markdown, no comments).

    Notable: `sig_early_stopping` also matches the Hugging Face **`generate(..., early_stopping=True)`** beam search
    option, which is pure inference (two of the `inference_only` negatives).
    """)
    return


@app.cell
def _(ENRICH_DIR, pd):
    def load_jsonl(name):
        path = ENRICH_DIR / f"{name}.jsonl"
        if not path.exists():
            return pd.DataFrame(columns=["full_name"]).set_index("full_name")
        return pd.read_json(path, lines=True).drop_duplicates("full_name", keep="last").set_index("full_name")

    hits_content = load_jsonl("hits")
    trees = load_jsonl("trees")
    print(f"hit content for {len(hits_content)} repos, trees for {len(trees)} repos")
    return hits_content, trees


@app.cell
def _(hits_content):
    hits_content
    return


@app.cell
def _(candidates, hits_content, pd):
    _h = hits_content.reindex(index=candidates.index, columns=[
        "n_fetched", "n_missing", "n_files_with_training", "infer_kinds", "generate_early_stopping", "keras_early_stopping"])
    _known = _h["n_fetched"].notna()
    _no_train = (_h["n_fetched"] > 0) & (_h["n_files_with_training"] == 0)
    stage2 = pd.DataFrame({
        # hit files contain inference code (generate, pipeline, LLM API, RAG) and no training construct
        "c_inference_no_train": _no_train & _h["infer_kinds"].map(lambda k: isinstance(k, list) and len(k) > 0),
        # no training construct in any hit file (hit is config/helper, or false positive): needs a deeper look
        "c_no_train_in_hits": _no_train,
        # early_stopping only as a generate() kwarg
        "c_generate_early_stopping": _h["generate_early_stopping"].astype("boolean") & ~_h["keras_early_stopping"].astype("boolean"),
        # every hit file is gone from the default branch (code removed since collection)
        "c_hits_missing": (_h["n_fetched"] == 0) & (_h["n_missing"] > 0),
    }, index=candidates.index).astype("boolean")
    stage2[~_known] = pd.NA
    return (stage2,)


@app.cell
def _(evaluate, stage2):
    evaluate(stage2)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Stage 3: repository structure and README

    `GITHUB_TOKEN=... uv run python src/dataset/enrich.py trees --input candidates_stage2.csv` (1 API call per repo,
    5000/h per token; the tool also reads the tokens of `../Bagger-GH/secrets.toml`).

    On the labeled subset, `file_storage` repos are dominated by notebooks spread over many directories
    (median notebook ratio 0.83 vs 0.02 for ML projects), contain slides (`.pdf`, `.pptx`), and numbered
    lesson files (`01_…`, `week3/`, `lab_2`). Thresholds below were picked on 35 negatives / 20 positives only:
    **re-check them on a larger set of positives** before trusting them.
    """)
    return


@app.cell
def _(trees):
    trees
    return


@app.cell
def _(trees):
    trees['n_files'].describe()
    return


@app.cell
def _(trees):
    trees[trees['n_files'] < 10]
    return


@app.cell
def _(trees):
    trees[trees['n_files'] > 25]
    return


@app.cell
def _(re):
    README_EDU = (
        r"\b(this course|the course|course material|lecture notes?|lab sessions?|homeworks?|assignments? \d|weekly"
        r"|week \d+|semester|syllabus|bootcamp|my (notes|learning journey|solutions)"
        r"|solutions? (to|for) (the )?(exercises|assignments)|practice notebooks?"
        r"|learning (repo|repository)|collection of (notebooks|projects))\b"
    )
    README_LIBRARY = r"pip install (?!-r)[\w\-]+|pypi\.org/project|readthedocs\.io"
    readme_edu_re = re.compile(README_EDU, re.I)
    readme_lib_re = re.compile(README_LIBRARY, re.I)
    return readme_edu_re, readme_lib_re


@app.cell
def _(candidates, pd, readme_edu_re, readme_lib_re, stage1, trees):
    _t = trees.reindex(index=candidates.index, columns=[
        "n_files", "n_py", "n_ipynb", "n_ipynb_dirs", "n_slides", "n_numbered_code", "n_vendored_files",
        "has_package_dir", "readme"])
    _known = _t["n_files"].notna()
    _nb_ratio = _t["n_ipynb"] / (_t["n_ipynb"] + _t["n_py"]).clip(lower=1)
    _readme = _t["readme"].fillna("")
    stage3 = pd.DataFrame({
        # mostly notebooks, many of them, and no Python package
        "t_notebook_dump": (_nb_ratio >= 0.75) & (_t["n_ipynb"] >= 10) & ~_t["has_package_dir"].astype("boolean"),
        # notebooks spread over many directories
        "t_dispersed_notebooks": _t["n_ipynb_dirs"] >= 10,
        # lecture slides
        "t_slides": _t["n_slides"] >= 10,
        # many numbered lesson files (01_intro.ipynb, week3/, lab_2.py)
        "t_numbered_files": _t["n_numbered_code"] >= 20,
        # committed virtualenv / site-packages
        "t_vendored_env": _t["n_vendored_files"] >= 500,
        "t_readme_edu": _readme.str.contains(readme_edu_re),
        "t_readme_library": _readme.str.contains(readme_lib_re),
        # education wording in name/description + notebook-heavy repo
        "t_edu_and_notebooks": stage1["m_edu_text"] & (_nb_ratio >= 0.5) & (_t["n_ipynb"] >= 5),
        # Add minimal number of files?
    }, index=candidates.index).astype("boolean")
    stage3[~_known] = pd.NA
    return (stage3,)


@app.cell
def _(evaluate, stage3):
    evaluate(stage3)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Combined decision

    Edit `ACTIONS` to promote a flag to an exclusion (or the reverse) and re-run.
    Rules whose data is missing for a repo (not enriched yet) do not exclude it.
    """)
    return


@app.cell
def _():
    ACTIONS = {
        "s0_owner_ignored": "exclude",
        "s0_owner_eq_name": "exclude",
        "s0_noise_name": "exclude",
        "s0_noise_description": "exclude",
        # "s0_unsure_name": "flag",
        "s0_unsure_name": "exclude",
        # "s0_unsure_description": "flag",
        "s0_unsure_description": "exclude",
        "m_generic_name": "exclude",
        "m_course_paths": "exclude",
        "m_vendored_hits_only": "exclude",
        "m_edu_text": "flag",
        "m_weak_signal_only": "flag",
        "m_copy_name": "flag",
        "m_notebook_hits_only": "flag",
        "c_inference_no_train": "exclude",
        "c_no_train_in_hits": "flag",
        "c_generate_early_stopping": "flag",
        "c_hits_missing": "flag",
        "t_notebook_dump": "exclude",
        "t_dispersed_notebooks": "exclude",
        "t_slides": "exclude",
        "t_numbered_files": "exclude",
        "t_vendored_env": "flag",
        "t_readme_edu": "exclude",
        "t_readme_library": "flag",
        "t_edu_and_notebooks": "exclude",
    }
    return (ACTIONS,)


@app.cell
def _(ACTIONS, candidates, pd, stage0, stage1, stage2, stage3):
    all_rules = pd.concat([stage0, stage1, stage2, stage3], axis=1).fillna(False).astype(bool)

    def _reasons(kind):
        cols = [c for c, a in ACTIONS.items() if a == kind]
        return all_rules[cols].apply(lambda r: ";".join(c for c in cols if r[c]), axis=1)

    decisions = candidates[["full_name"]].copy()
    decisions["excluded_by_v2"] = _reasons("exclude")
    decisions["flags_v2"] = _reasons("flag")
    decisions["selected_v2"] = decisions["excluded_by_v2"] == ""
    decisions["selected_v2"].value_counts()
    return all_rules, decisions


@app.cell
def _(all_rules, mo):
    rule_picker = mo.ui.dropdown(list(all_rules.columns), value="m_generic_name", label="Labeled repos matched by")
    rule_picker
    return (rule_picker,)


@app.cell
def _(all_rules, matches, rule_picker):
    matches(all_rules, rule_picker.value)
    return


@app.cell
def _(ACTIONS, all_rules, evaluate, pd):
    _excl = [c for c, a in ACTIONS.items() if a == "exclude"]
    _by_stage = pd.DataFrame({
        f"stage<={s}": all_rules[[c for c in _excl if c[0] in prefixes]].any(axis=1)
        for s, prefixes in [(0, "s"), (1, "sm"), (2, "smc"), (3, "smct")]
    })
    evaluate(_by_stage)
    return


@app.cell
def _(decisions, labels):
    _lab = labels.join(decisions.set_index("full_name"), how="inner")
    _precision_before = (_lab["Label"] == "ml_project").mean()
    _kept = _lab[_lab["selected_v2"]]
    print(f"labeled precision before: {_precision_before:.3f} (n={len(_lab)}), "
          f"after v2 on labeled: {(_kept['Label'] == 'ml_project').mean():.3f} (n={len(_kept)})")
    # remaining negatives: what is still missed
    _kept[_kept["Label"] == "not_ml_project"][["Reason_code", "flags_v2"]]
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Exports

    * `candidates_v2_decisions.csv`: every candidate with its exclusion reasons and flags.
    * `candidates_filtered_v2.csv`: selected candidates (input of the next enrichment stage / sampling).
    * `manual_verification_results/run3/sample.csv`: fresh sample **excluding already labeled repos**,
      to measure precision on data the rules were not tuned on.
    """)
    return


@app.cell
def _(candidates, decisions):
    decisions.to_csv("candidates_v2_decisions.csv", index=False)
    candidates_filtered_v2 = candidates.join(decisions.set_index("full_name")[["flags_v2"]])[decisions["selected_v2"].values]
    candidates_filtered_v2.drop(columns=["hit_files"]).to_csv("candidates_filtered_v2.csv", index=False)
    len(candidates_filtered_v2)
    return (candidates_filtered_v2,)


@app.cell
def _(candidates_filtered_v2, labels, mo):
    _pool = candidates_filtered_v2[~candidates_filtered_v2.index.isin(labels.index)]
    run3_sample = _pool.sample(n=min(160, len(_pool)), random_state=2026)[
        ["full_name", "html_url", "description", "files", "flags_v2"]]
    save_sample = mo.ui.run_button(label="Write manual_verification_results/run3/sample.csv")
    mo.vstack([save_sample, run3_sample])
    return run3_sample, save_sample


@app.cell
def _(MANUAL_DIR, mo, run3_sample, save_sample):
    mo.stop(not save_sample.value)
    (MANUAL_DIR / "run3").mkdir(exist_ok=True)
    run3_sample.to_csv(MANUAL_DIR / "run3/sample.csv", index=False, sep=";")
    return


if __name__ == "__main__":
    app.run()

import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Github project dataset
    """)
    return


@app.cell
def _():
    import marimo as mo
    import pandas as pd

    return mo, pd


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The collection funnel of project is displayed bellow. After the first filtering steps we end with 168,608 repositories:
    """)
    return


@app.cell
def _(pd):
    funnel = pd.read_csv("data/ml-pipelines-20261013-163440/funnel.csv")
    funnel
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    On those project, now need to filter the repositories owner
    """)
    return


@app.cell
def _(pd):
    candidates = pd.read_csv("data/ml-pipelines-20261013-163440/candidates.csv")
    candidates
    return (candidates,)


@app.cell
def _(candidates):
    candidates['repo_owner'] = candidates['full_name'].str.split('/').str[0]
    candidates['repo_owner']
    return


@app.cell
def _(candidates):
    candidates['repo_name'] = candidates['full_name'].str.split('/').str[1]
    candidates['repo_name']
    return


@app.cell
def _(candidates):
    candidates['repo_owner'].nunique()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Let drop the projects that where the owner name correpond to one of the name we want to not consider.
    After the first run of manual verification, we have entended this list.
    """)
    return


@app.cell
def _():
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
    return (name_to_ignore,)


@app.cell
def _(candidates, name_to_ignore):
    candidates[candidates['repo_owner'].isin(name_to_ignore)]
    return


@app.cell
def _(candidates, name_to_ignore):
    candidates_filtered = candidates[~candidates['repo_owner'].str.lower().isin(name_to_ignore)]
    candidates_filtered = candidates_filtered[~(candidates_filtered['repo_name'] == candidates_filtered['repo_owner'])] # In the case where the repo owner and repo name is the same we drop it too
    candidates_filtered
    return (candidates_filtered,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    After run1 of the manual verification we also added a check on the repository name and description to see if it contain one of the word we want to ignore.
    """)
    return


@app.cell
def _():
    noise_word = [
        # Anglais
        "example", "examples", "tutorial", "tutorials", "demo", "demos",
        "docs", "course", "courses", "lecture", "lectures", 
        "lesson", "lessons", "term", "terms", "exam", "exams",

        #I am not sure of the following ones, let try to see
        "notebook", "notebooks", "colab", "kaggle"

        # Russe
        "пример", "примеры",                # example(s)
        "руководство", "руководства",       # tutorial(s)
        "туториал", "туториалы",            # tutorial(s)
        "демо", "демонстрация",             # demo(s)
        "тест", "тесты",                    # test(s)
        "документация",                     # docs
        "курс", "курсы",                    # course(s)
        "лекция", "лекции",                 # lecture(s)
        "урок", "уроки",                    # lesson(s)
        "семестр", "семестры",              # term(s)
        "экзамен", "экзамены",              # exam(s)

        # Chinois (simplifié)
        "示例", "例子", "范例",              # example(s)
        "教程",                             # tutorial(s)
        "演示",                             # demo(s)
        "测试",                             # test(s)
        "文档",                             # docs
        "课程",                             # course(s)
        "讲座", "讲义",                      # lecture(s)
        "课",                               # lesson(s)
        "学期",                             # term(s)
        "考试",                             # exam(s)
    ]
    return (noise_word,)


@app.cell
def _(candidates_filtered, noise_word):
    import re

    pattern = "|".join(map(re.escape, noise_word))

    mask_repo_name = candidates_filtered["repo_name"].str.contains(pattern, case=False, na=False, regex=True)

    noisy_repo_name = candidates_filtered[mask_repo_name]  
    # clean = candidates_filtered[~mask]   # repos sans aucun de ces termes
    return mask_repo_name, noisy_repo_name, pattern


@app.cell
def _(noisy_repo_name):
    noisy_repo_name
    return


@app.cell
def _(candidates_filtered, mask_repo_name):
    candidates_filtered_noise_name = candidates_filtered[~mask_repo_name]
    len(candidates_filtered_noise_name)
    return (candidates_filtered_noise_name,)


@app.cell
def _(candidates_filtered_noise_name, pattern):
    mask_noise_description = candidates_filtered_noise_name["description"].str.contains(pattern, case=False, na=False, regex=True)
    noisy_repo_desc = candidates_filtered_noise_name[mask_noise_description] 
    return mask_noise_description, noisy_repo_desc


@app.cell
def _(noisy_repo_desc):
    noisy_repo_desc
    return


@app.cell
def _(candidates_filtered_noise_name, mask_noise_description):
    candidates_filtered_noise_name_desc = candidates_filtered_noise_name[~mask_noise_description]
    len(candidates_filtered_noise_name_desc)
    return (candidates_filtered_noise_name_desc,)


@app.cell
def _(candidates_filtered_noise_name_desc):
    candidates_filtered_noise_name_desc.to_csv('candidates_filtered.csv')
    return


@app.cell
def _(candidates_filtered_noise_name_desc):
    candidates_filtered_noise_name_desc.sample(n=160, random_state=42)
    return


@app.cell
def _(candidates_filtered_noise_name_desc):
    candidates_filtered_noise_name_desc[candidates_filtered_noise_name_desc["full_name"] == "bmqube/image-colorization"]
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The previous project is strange, on the web, the last commit was in 2024, but with the api, pushed_at (last commit event) is 2025. On github the date displayed is the commit date not the push date.
    """)
    return


@app.cell
def _(candidates_filtered_noise_name_desc, pd):
    candidates_filtered_noise_name_desc["created_at"] = pd.to_datetime(candidates_filtered_noise_name_desc["created_at"], utc=True)
    candidates_filtered_noise_name_desc["pushed_at"] = pd.to_datetime(candidates_filtered_noise_name_desc["pushed_at"], utc=True)
    candidates_filtered_noise_name_desc

    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Regardons si on peut garder uniquement les projets qui on minimum 3 mois de durée de vie (entre la creation et le dernier commit).
    """)
    return


@app.cell
def _(candidates_filtered_noise_name_desc, pd):
    # Garde les lignes où date2 est au moins 3 mois après date1
    df_filtre = candidates_filtered_noise_name_desc[candidates_filtered_noise_name_desc["pushed_at"] >= candidates_filtered_noise_name_desc["created_at"] + pd.DateOffset(months=3)]
    df_filtre
    return (df_filtre,)


@app.cell
def _(df_filtre):
    df_filtre_min_commit = df_filtre[df_filtre['commit_count'] >= 10]
    df_filtre_min_commit
    return (df_filtre_min_commit,)


@app.cell
def _(df_filtre_min_commit):
    df_filtre_min_commit[df_filtre_min_commit['open_issues'] >= 1]
    return


if __name__ == "__main__":
    app.run()

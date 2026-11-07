# Labeling Guidelines: Manual Validation of ML Project Identification

These guidelines are used to manually validate the precision of the ML project identification process (Section V-B of the registered report). The first two authors independently label each repository of the random sample (initially 73 repositories) using the procedure below.

## 1. Definition

A repository is an **ML project** if it contains source code that **trains or fine-tunes at least one ML model**.

*Training* means running an optimization or fitting procedure that learns model parameters from data. *Fine-tuning* means updating the parameters of an existing (pre-trained) model, fully or partially (e.g., LoRA, adapters, last-layer retraining).

The training code must:

- be written in **Python scripts or Jupyter notebooks**, consistent with the scope of the study;
- belong to the **repository's own code**, i.e., outside example, test, teaching, and vendored dependency directories (the same exclusions as the filtering step);
- be **executable as part of the project**: code that would train a model if run, including code behind a flag or option. It does not need to have been run, and no trained weights need to be present.

## 2. Labels

Each repository receives exactly one label:

| Label | Meaning |
|---|---|
| `ml_project` | The repository meets the definition above. |
| `not_ml_project` | The repository does not meet the definition above. |

For every `not_ml_project` label, annotators also record **one reason code**. Reason codes are not used to compute agreement. They support the analysis of false positives if the precision threshold is not met (Section V-B).

| Reason code | Description |
|---|---|
| `inference_only` | Loads a pre-trained model or calls a model API for prediction, evaluation, or generation, without training it (e.g., prompting an LLM, RAG pipelines, agent frameworks, running a downloaded checkpoint). |
| `preprocessing_only` | Fits only data transformers used as preprocessing (e.g., `StandardScaler`, `TfidfVectorizer`, `LabelEncoder`, tokenizer training), with no model trained on top. |
| `wrapper_or_tool` | Wraps or extends an ML library (e.g., utilities, plugins, interfaces) without itself training a model. |
| `ml_library` | The repository is an ML library or framework, or a fork or mirror of one, not removed by the filters. |
| `excluded_location_only` | Training code exists only in example, tutorial, test, documentation, or vendored dependency directories. |
| `dead_code` | Training code exists but cannot run as part of the project (e.g., fully commented out, unreachable). |
| `file_storage` | The repository is used to store files (e.g., dumps of unrelated scripts, backups, course material collections) rather than to develop a project. |
| `no_ml_code` | The search hit is incidental (e.g., a method named `fit` unrelated to ML) and the repository contains no ML training code. |
| `other` | Any other reason; a free-text justification is mandatory. |

## 3. Procedure

Annotators label each repository independently and do not discuss repositories before both labels are recorded. Annotators are not given the coding-agent adoption status of the repository.

1. **Read the README** to understand the purpose of the repository.
2. **Inspect the search hits**, i.e., the files matched by the code-search queries. Check whether the matched construct actually trains a model.
3. **If the hits are inconclusive, inspect the rest of the repository.** The label applies to the repository as a whole: a repository whose hits are false positives is still an `ml_project` if other files train a model. Search for training constructs (e.g., `.fit(`, `.train(`, `optimizer.step(`, `loss.backward(`, `Trainer(`, `trainer.fit(`, `model.learn(`).
4. **Decide** using the definition (Section 1) and the edge cases (Section 4).
5. **Record** the label, the evidence, and, where applicable, the reason code (Section 5).

## 4. Edge cases

| Situation | Label |
|---|---|
| Classical ML model fitted with scikit-learn, XGBoost, LightGBM, etc. (e.g., `RandomForestClassifier().fit(X, y)`) | `ml_project` |
| Unsupervised model fitted as the analysis goal (e.g., `KMeans`, topic models, an autoencoder) | `ml_project` |
| Preprocessing transformer fitted alone, without a downstream model (e.g., only `PCA` or `StandardScaler`) | `not_ml_project` (`preprocessing_only`) |
| High-level one-line training API (e.g., Ultralytics `model.train(...)`, Keras `model.fit(...)`, AutoML `fit`) | `ml_project` |
| Hyperparameter search or cross-validation that trains models (e.g., `GridSearchCV`, Optuna) | `ml_project` |
| Fine-tuning a pre-trained model locally (full, LoRA, adapters, RLHF, DPO) | `ml_project` |
| Fine-tuning through a remote provider API (e.g., submitting a job to a hosted fine-tuning endpoint) | `not_ml_project` (`inference_only`): the training does not run in the repository's code |
| Training a reinforcement learning agent (e.g., Stable-Baselines3 `model.learn(...)`) | `ml_project` |
| Training happens only after a CLI flag or config option is set (e.g., `--train`) | `ml_project` |
| Training cells exist in a notebook, even without saved outputs | `ml_project` |
| Training code fully commented out | `not_ml_project` (`dead_code`) |
| Statistical model fitted only for hypothesis testing or coefficient interpretation (e.g., `statsmodels` OLS summary) | `not_ml_project` (`other`, justify) |
| Statistical or forecasting model fitted to make predictions (e.g., ARIMA, Prophet used for forecasting) | `ml_project` |
| Evaluation or benchmarking scripts that only load existing checkpoints | `not_ml_project` (`inference_only`) |
| Training code copied from a tutorial but placed in the project's own source tree | `ml_project` |
| Collection of many unrelated training notebooks or scripts with no common purpose (e.g., a personal snippets dump) | `not_ml_project` (`file_storage`) |
| Course or tutorial repository whose main content is exercises with training code | `not_ml_project` (`excluded_location_only`) if it should have been caught by the teaching filter, otherwise `ml_project` if it is a single coherent project |

When none of these cases applies and the decision remains uncertain, annotators choose the label they find most defensible and set the `uncertain` flag (Section 5) so that the case is discussed during consensus.

## 5. Annotation record

Each annotator fills one row per repository:

| Column | Content |
|---|---|
| `repository` | `owner/name` |
| `annotator` | Annotator identifier |
| `label` | `ml_project` or `not_ml_project` |
| `reason_code` | Required if `not_ml_project`, empty otherwise |
| `evidence` | File path (and line or notebook cell) of the training code, or a short description of why none was found |
| `uncertain` | `true` if the annotator was unsure, `false` otherwise |
| `comment` | Free text; mandatory for reason code `other` |



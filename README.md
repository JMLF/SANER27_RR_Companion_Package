# Adoption of Coding Agents in Machine Learning Projects
This repository is the companion package for the register report: Adoption of Coding Agents in Machine Learning Projects.


## Github project mining
To collect ML project from Github we developed and use [this tool](Bagger-GH/). 
The tool levrage the Github search api to collect files that "hit" (respond) to a search querie. The queries are scoped to Python and Jupyter Notebook files using the `language:python` and `language:"Jupyter Notebook"` qualifiers.
We will use the following queries:


| Name | Library | Query | 
| --- | --- | --- | 
| sig_model_fit | generic_fit | `"model.fit(" language:Python` | 
| sig_model_fit_nb | generic_fit | `"model.fit(" language:"Jupyter Notebook"` | 
| sig_epoch_loop | generic_epoch_loop | `"for epoch in range" loss language:Python` | 
| sig_epoch_loop_nb | generic_epoch_loop | `"for epoch in range" loss language:"Jupyter Notebook"` | 
| sig_num_epochs | generi_epoch | `"num_epochs" loss language:Python` | 
| sig_num_epochs_nb | generic_epoch | `"num_epochs" loss language:"Jupyter Notebook"` | 
| sig_val_loss | generic_loss | `"val_loss" "train_loss" language:Python` | 
| sig_val_loss_nb | generic_loss | `"val_loss" "train_loss" language:"Jupyter Notebook"` | 
| sig_early_stopping | generic_early_stopping | `"early_stopping" language:Python` | 
| sig_early_stopping_nb | generic_early_stopping | `"early_stopping" language:"Jupyter Notebook"` | 
| sig_wandb_init | generic_wandb | `"wandb.init" language:Python` | 
| sig_wandb_init_nb | generic_wandb | `"wandb.init" language:"Jupyter Notebook"` | 
| sig_mlflow | generic_mlflow | `"mlflow.log_metric" language:Python` | 
| sig_mlflow_nb | generic_mlflow | `"mlflow.log_metric" language:"Jupyter Notebook"` |
| sig_tensorboard | generic_tensorboard | `"tensorboard" "log_dir" language:Python` | 
| sig_tensorboard_nb | generic_tensorboard | `"tensorboard" "log_dir" language:"Jupyter Notebook"` | 

After collection of the hits for each queries, we will run a set of filter and aggregate the hits per repositories.
The filter used are the following:


| ID | Level | Rule | Keep if | Rationale |
| --- | --- | --- | --- | --- |
| **F1** | Hit | Path noise | No segment of the file path matches a noise keyword* (case-insensitive, singular or plural) | Discards illustrative, vendored, or teaching code that is not part of the project's own pipeline. |
| **F2** | Repo | Fork | The repository is not a fork | Avoids duplicates, as forks share their history with the upstream repository. |
| **F3** | Repo | Language | GitHub's main language is Python or Jupyter Notebook | Ensures ML code is central to the project rather than an incidental script. |
| **F4** | Repo | Ownership | Owner name of the repository does not match any ML organization developing ML libraries or tools**. | Repository owned by organization developing ML libraries may hit our search queries without code that implement ML pipelines but rather library code and example. |
| **F5** | Repo | History | ≥ 3 commits | Excludes repositories used as file storage (e.g., a single upload). |
| **F6** | Repo | Recent activity | ≥ 1 commit after 2025-01-01 | Coding-agent adoption can only be observed in projects active since agents became available. |

**Manual verification guideline**
To asses the validity of our mining approach, we will randomly sample 73 projects from the collection.
For each project, the annotators will clone the project. Read the README file and project description, look at the files in the project and label each project as "ML-project" if the project does contain ML pipeline code or "non-ML-project" if the project does not caontain an ML pipeline or should not have been mined.
Manual validation guidelines in [this file](ml_project_labeling_guidelines.md)

*. Keyword noise: "example", "examples", "tutorial", "tutorials", "demo", "demos", "sample", "samples", "test", "tests", "docs", "site-packages", "dataset", "datasets", "agent", "agents", "course", "courses", "lecture", "lectures", "lesson", "lessons"

**. Organization name: "tensorflow", "google-research", "microsoft", "google", "google-deepmind", "GoogleCloudPlatform", "wandb", "probml", "google", "agential-ai", "IBM", "huggingface", "Kaggle", "AlibabaResearch", "Deep-Spark", "autogluon", "aws-samples", "Azure", "INRIA", "facebookresearch", "facebook", "tenstorrent", "keras-team", "scikit-learn", "pytorch", "dmlc", "PaddlePaddle", "jax-ml", "Lightning-AI", "statsmodels", "apache", "lightgbm-org", "catboost", "fastai", "unifyai", "jina-ai", "mlpack", "explosion", "ludwig-ai", "skorch-dev", "ROCm", "geomstats", "pyRiemann", "numenta", "determined-ai", "sony", "deepinv", "towhee-io", "nubank", "run-house", "mlflow", "wandb" ... Also, if the reposotory and the organization have the same name we drop them.


## Project Type ($P_{type}$) 
The guidelines are in [this file](project_type_taxonomie.md/)

## Sample size 
To propoerly compute the a priori sample size using G\*Power (version 3.1.9.6) we had to convert the r type effect of Rrb to d type effect (G\*Power uses dz effect).
We used the convertion formula [1,2] implemented in [this R script](effect_size_convertion.R/).
For an effect of 0.1 in r that gives us 0.2010076 in d.
We used this d value in G\*Power.
The complete settings used and result are in [this file](G_Power_power.txt/).

1. Aaron, B., Kromrey, J. D., & Ferron, J. (1998). Equating.
2. Borenstein, M., Cooper, H., Hedges, L., & Valentine, J. (2009). Effect sizes for continuous data. The handbook of research synthesis and meta-analysis, 2, 221-235.


## RQ1. Agent detection
On the final dataset of ML repositories collected on Github, we will use the [reproduction package](agent-impact/) of Robbes et al. [1,2] to detect the presence of agent in repositories.
Their tool levrage a set of detection heuristics generated by [this project](agent-mining/) [3].

On their last study [2], Robbes et al. were searching for 56 coding agents.
In the last version of the [detection heuristics](agent-mining/), they were detecting 65 coding agents:  


| Agent | Implementers |
| --- | --- |
| `abacus` | Robbes et al. |
| `aider` | Robbes et al. |
| `alibaba_lingma` | Robbes et al. |
| `amazon_q` | Robbes et al. |
| `amp` | Robbes et al. |
| `atlassian_rovodev` | Robbes et al. |
| `augment_code` | Robbes et al. |
| `baidu_comate` | Robbes et al. |
| `brokk` | Robbes et al. |
| `charlie` | Robbes et al. |
| `chatgpt` | Robbes et al. |
| `claude_code` | Robbes et al. |
| `cline` | Robbes et al. |
| `codebuddy` | Robbes et al. |
| `codegen` | Robbes et al. |
| `coderabbit` | Robbes et al. |
| `codex` | Robbes et al. |
| `continue` | Robbes et al. |
| `copilot` | Robbes et al. |
| `crush` | Robbes et al. |
| `cursor` | Robbes et al. |
| `deepsource` | Robbes et al. |
| `devin` | Robbes et al. |
| `factory_droid` | Robbes et al. |
| `fly` | Robbes et al. |
| `gemini` | Robbes et al. |
| `generic` | Robbes et al. |
| `goose` | Robbes et al. |
| `gpt-engineer` | Robbes et al. |
| `gpt_engineer` | Robbes et al. |
| `gru` | Robbes et al. |
| `jules` | Robbes et al. |
| `junie` | Robbes et al. |
| `kilo_code` | Robbes et al. |
| `kimi_code` | Robbes et al. |
| `kiro` | Robbes et al. |
| `langchain_open_swe` | Robbes et al. |
| `letta_code` | Robbes et al. |
| `microsoft_amplifier` | Robbes et al. |
| `mistral_vibe` | Robbes et al. |
| `ona` | Robbes et al. |
| `opencode` | Robbes et al. |
| `openhands` | Robbes et al. |
| `paperclip` | Robbes et al. |
| `pi` | Robbes et al. |
| `plandex` | Robbes et al. |
| `qodo` | Robbes et al. |
| `qwen_code` | Robbes et al. |
| `qwen_coder` | Robbes et al. |
| `roo_code` | Robbes et al. |
| `rulesync` | Robbes et al. |
| `sentry_seer` | Robbes et al. |
| `serena` | Robbes et al. |
| `sketch` | Robbes et al. |
| `sourcery` | Robbes et al. |
| `speckit` | Robbes et al. |
| `specstory` | Robbes et al. |
| `superpowers` | Robbes et al. |
| `sweep` | Robbes et al. |
| `taskmaster` | Robbes et al. |
| `tessl` | Robbes et al. |
| `trae` | Robbes et al. |
| `verdent` | Robbes et al. |
| `warp` | Robbes et al. |
| `windsurf` | Robbes et al. |

We plan to add at least 8 more coding agents:

| Agent | Type | Implementers |
| --- | --- | --- |
| `qoder` | Generic | Us
| `Cosine` | Generic | Us 
| `Tembo` | Generic | Us 
| `VTCode` | Generic | Us 
| `StatPack` | Generic | Us 
| `fast-agent` | Generic | Us 
| `Forge` | Generic | US 
| `Code Assistant` | Generic | Us
<!-- | `MLEvolve` | ML-specific |
| `MLZero` | ML-specific |
| `Aide` | ML-specific |
| `Ml-master` | ML-specific |
| `Mle-star` | ML-specific |
| `AIBuildAI` | ML-specific | -->

<!-- Aide / Weco seems to be identifliable using the name https://github.com/aiden-weco of the agent and inside python import aide as a lib. -->




1. Robbes, R., Matricon, T., Degueule, T., Hora, A., & Zacchiroli, S. (2026). Agentic much? adoption of coding agents on github. ACM Transactions on Software Engineering and Methodology.

2. Robbes, R., Matricon, T., Degueule, T., Hora, A., & Zacchiroli, S. (2026). Agentic Very Much! Adoption of Coding Agent in New GitHub Projects. arXiv preprint arXiv:2606.07448.

3. Robbes, R., Matricon, T., Degueule, T., Hora, A., & Zacchiroli, S. (2026, April). Promises, perils, and (timely) heuristics for mining coding agent activity. In Proceedings of the 23rd International Conference on Mining Software Repositories (pp. 496-507).

## RQ2. Skills Collection
Skill files categorization guide in [this file](skill_categorization_guidelines.md)

## RQ4 
For RQ4, we will reuse and adapt this analysis pipeline: https://zenodo.org/records/21464700


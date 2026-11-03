# Adoption of Coding Agents in Machine Learning Projects
This repository is the companion package for the register report: Adoption of Coding Agents in Machine Learning Projects.

## Github project mining
To collect ML project from Github we developed and use [this tool](Bagger-GH/). 
The tool levrage the Github search api to collect files that "hit" (respond) to a search querie.
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

*. Keyword noise: "example", "examples", "tutorial", "tutorials", "demo", "demos", "sample", "samples", "test", "tests", "docs", "site-packages", "dataset", "datasets", "agent", "agents", "course", "courses", "lecture", "lectures", "lesson", "lessons"

**. Organization name: "tensorflow", "google-research", "microsoft", "GoogleCloudPlatform", "wandb", "probml", "google", "agential-ai", "IBM", "huggingface", "Kaggle", "AlibabaResearch", "Deep-Spark", "autogluon", "aws-samples", "Azure", "INRIA", "facebookresearch", "facebook", "tenstorrent" ...



IF the repo and the organization have the same name we drop them.
Do we keep the labs? google-research or Alibaba, they have libs and paper...
probml is a book we can certainly drop it

## Sample size 
To propoerly compute the a priori sample size using G\*Power we had to convert the r type effect of Rrb to d type effect (G\*Power uses dz effect).
We used the convertion formula [1,2] implemented in [this R script](effect_size_convertion.R/).
For an effect of 0.1 in r that gives us 0.2010076 in d.
We used this d value in G\*Power.
The complete settings used and result are in [this file](G_Power_power.txt/).

1. Aaron, B., Kromrey, J. D., & Ferron, J. (1998). Equating.
2. Borenstein, M., Cooper, H., Hedges, L., & Valentine, J. (2009). Effect sizes for continuous data. The handbook of research synthesis and meta-analysis, 2, 221-235.


## RQ1. Agent detection

- Tool
- Agent supported by default
- New agents

## RQ2. Skills Collection

- Categorization guidelines of the skill files

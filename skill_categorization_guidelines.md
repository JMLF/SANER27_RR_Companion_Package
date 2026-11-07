# Categorization Guidelines: Agent Skills ($S_{category}$)

These guidelines are used to categorize the unique skills collected in agent-assisted ML projects. They apply in both cases described in the report:

- **At most 500 unique skills:** the first two authors categorize all of them.
- **More than 500 unique skills:** an LLM categorizes all of them using these definitions, and the first two authors label a validation sample.

## 1. Unit of analysis

The unit is a **unique skill**: one skill file (e.g., `.claude/skills/<name>/SKILL.md`) after deduplication by content hash. The categorization is based on:

1. the frontmatter `name` and `description`, which state when the agent should load the skill;
2. the body of the skill file (its instructions).

Annotators may consult the other files bundled in the skill folder (scripts, references, templates) only when the body is too short to decide, for instance when it only points to these files. The repository the skill was found in is **not** used: the same skill can appear in several repositories, and its category must not depend on where it was found.

## 2. Validity check

Before categorization, each skill is checked for validity. A skill is **invalid** if it contains no usable instructions, for example:

- an empty file or a file containing only frontmatter;
- an unmodified template or placeholder (e.g., "Describe your skill here");
- a file that is not a skill despite its name or location (e.g., a README of an unrelated folder, a broken or binary file).

Invalid skills are marked `invalid` and excluded from the categorization and from the proportions reported for $S_{category}$. Their number is reported separately.

## 3. Categories

Each valid skill receives exactly one category:

| Category | Definition |
|---|---|
| `ml_specific` | The main purpose of the skill is an activity of the ML model lifecycle: preparing data for training, designing or training models, fine-tuning, evaluating models, tuning hyperparameters, tracking experiments, or packaging, serving, and monitoring trained models. Skills dedicated to using an ML library or framework (e.g., PyTorch, scikit-learn, Hugging Face Transformers, Lightning, XGBoost) also belong here. |
| `general_purpose` | The main purpose of the skill is not specific to ML: general software engineering (coding style, testing, refactoring, debugging, documentation, Git, CI/CD, dependency management), general data handling or visualization, writing, project management, or any other non-ML domain. |

### Typical examples

| `ml_specific` | `general_purpose` |
|---|---|
| Fine-tune a model with LoRA on a custom dataset | Write unit tests with pytest |
| Set up a PyTorch training loop with mixed precision | Follow the project's Python code style |
| Run a hyperparameter search with Optuna | Write commit messages and open pull requests |
| Evaluate a classifier and report metrics (F1, ROC-AUC, confusion matrix) | Build a FastAPI endpoint |
| Build a train/validation/test split and avoid data leakage | Clean and explore a CSV with pandas |
| Log experiments with MLflow or Weights & Biases | Create plots with matplotlib |
| Launch distributed or multi-GPU training | Write a LaTeX paper section |
| Export and serve a trained model (ONNX, TorchServe) | Manage a Docker environment |
| Run this project's training pipeline (project-specific instructions) | Review code for security issues |

## 4. Decision rules

1. **Main purpose decides.** Categorize according to the main purpose stated in the `name` and `description`. If they are missing or vague, use the purpose of the majority of the instructions in the body.
2. **Incidental ML mentions do not count.** A general-purpose skill that mentions ML only in passing (e.g., a testing skill whose example tests a model function) is `general_purpose`.
3. **Generic skills applied to ML are ML-specific.** A skill that adapts a general practice specifically to ML code (e.g., "testing ML training code", "reproducibility of training runs with fixed seeds", "code review checklist for ML pipelines") is `ml_specific`.
4. **Data work.** Data loading, cleaning, exploration, and visualization are `general_purpose` unless the skill explicitly targets model training (e.g., feature engineering, dataset construction for training, label processing, data augmentation, leakage prevention), in which case they are `ml_specific`.
5. **LLM applications.** Skills about *using* pre-trained models through APIs or frameworks without training or fine-tuning them (e.g., prompt engineering, calling an LLM API, building RAG or agent applications) are `general_purpose`. Skills about training, fine-tuning, evaluating, or serving models, including LLMs, are `ml_specific`. This keeps the category consistent with our definition of ML projects, which train or fine-tune models.
6. **Domain science.** Skills tied to an application domain (e.g., bioinformatics, finance, chemistry) are `general_purpose` unless their main purpose is an ML lifecycle activity in that domain (e.g., "train a molecular property predictor").
7. **Scientific computing.** Numerical computing (NumPy, SciPy), notebooks, and GPU programming that is not tied to model training (e.g., CUDA kernels for simulation) are `general_purpose`.
8. **Uncertain cases.** When the rules above do not settle the case, annotators choose the category they find most defensible and set the `uncertain` flag so that the case is discussed during consensus.

## 5. Procedure

Annotators label each skill independently and do not discuss skills before both labels are recorded. When validating the LLM categorization, annotators do not see the LLM label.

1. Read the frontmatter (`name`, `description`).
2. Read the body of the skill file; consult bundled files only if needed (Section 1).
3. Apply the validity check (Section 2).
4. Assign a category using the definitions (Section 3) and decision rules (Section 4).
5. Record the annotation (Section 6).

## 6. Annotation record

Each annotator (or the LLM) fills one row per unique skill:

| Column | Content |
|---|---|
| `skill_hash` | Content hash of the skill file |
| `skill_name` | Frontmatter `name` (or folder name if missing) |
| `annotator` | Annotator identifier, or `llm` |
| `valid` | `true` or `false` (Section 2) |
| `category` | `ml_specific` or `general_purpose`; empty if `valid` is `false` |
| `justification` | One sentence citing the element of the skill that supports the category |
| `uncertain` | `true` if the annotator was unsure, `false` otherwise (human annotators only) |

LLM output uses the same fields in JSON:

```json
{
  "skill_hash": "3f2a9c...",
  "skill_name": "lora-finetuning",
  "valid": true,
  "category": "ml_specific",
  "justification": "The description states the skill is used to fine-tune language models with LoRA adapters."
}
```

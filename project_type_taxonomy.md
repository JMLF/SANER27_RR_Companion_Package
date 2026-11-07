# Project Type Taxonomy ($P_{type}$)

This document defines the two taxonomies used to classify the project type ($P_{type}$) of each ML project. Each project receives **exactly one label per dimension**:

1. **ML task**: what the trained or fine-tuned model does.
2. **Project kind**: why the repository exists and how it is meant to be used.

The same definitions are used by the LLM classifier and by the two human annotators who label the validation sample.

## General rules

- **Input.** Classification is based on the repository README. Annotators may additionally look at the repository name, description and file tree to disambiguate, but the label must be justifiable from the README whenever possible.
- **Single label.** Each dimension takes a single label. When several labels apply, follow the decision rules of that dimension.
- **Trained models only.** The ML task refers to models the repository *trains or fine-tunes*, not to pre-trained models it only calls for inference (e.g., a project that fine-tunes a classifier and uses an off-the-shelf LLM for prompting is labeled with the classifier's task).
- **Unclear.** If the README is missing, empty, written in a way that does not allow a decision, or contradicts itself, use `unclear`. Do not guess from the code alone.
- **Other.** Use `other` only when the information is clear but no category fits. Annotators should note a short free-text justification for every `other` label.

---

## Dimension 1: ML task

| Label | Definition | Typical examples |
|---|---|---|
| `classification` | The model assigns one or more discrete labels to an input, including token-level labeling. | Image classification, sentiment analysis, spam detection, tabular churn prediction, named-entity recognition, intent detection |
| `regression` | The model predicts a continuous value from features, without a temporal forecasting horizon. | House price prediction, property prediction, age estimation |
| `forecasting` | The model predicts future values of one or more time series from past observations. | Stock price forecasting, energy load forecasting, demand forecasting |
| `detection_segmentation` | The model localizes objects or regions in images, video, or point clouds. | Object detection (YOLO), instance or semantic segmentation, pose estimation, medical image segmentation |
| `generation` | The model produces content (text, images, audio, video, code, molecules) or transforms one sequence into another. | LLM pre-training or fine-tuning, chatbots, diffusion models, GANs, translation, summarization, speech recognition, image captioning, text-to-speech |
| `recommendation_retrieval` | The model ranks, retrieves, or recommends items for a query or user. | Recommender systems, learning-to-rank, dense retrievers, re-rankers |
| `representation_learning` | The model is trained primarily to produce embeddings or features that are not the end goal of the project. | Self-supervised or contrastive pre-training, embedding models, autoencoders used for feature extraction |
| `clustering` | The model groups or reduces data without labels. | Customer segmentation, topic modeling, dimensionality reduction |
| `anomaly_detection` | The model identifies rare or abnormal instances. | Fraud detection, intrusion detection, defect detection, outlier detection |
| `reinforcement_learning` | An agent is trained through interaction with an environment and a reward signal. | Game-playing agents, robotics control, RL environments with training loops |
| `multiple` | The repository trains models for several distinct tasks, none of which dominates. | Benchmark suites, collections of unrelated models, multi-task frameworks |
| `other` | The task is clear but fits no category above. | Must be justified in free text |
| `unclear` | The README does not allow the task to be determined. | |

### Decision rules (ML task)

1. **Primary task first.** Label the task that corresponds to the project's stated main goal (usually in the title or first paragraph of the README). Secondary or auxiliary models are ignored.
2. **Use `multiple` sparingly.** Use it only when two or more tasks are presented with equal importance and no single goal is stated.
3. **Fine-tuning for RLHF or preference alignment** (e.g., DPO, PPO on an LLM) is labeled `generation`, not `reinforcement_learning`, because the end product is a generative model.
4. **Anomaly detection framed as binary classification** (e.g., fraud vs. non-fraud with a supervised classifier) is labeled `anomaly_detection` when the README frames the goal as detecting rare or abnormal cases, and `classification` otherwise.
5. **Segmentation of sequences** (e.g., token tagging) is `classification`; segmentation of images, video, or 3D data is `detection_segmentation`.
6. **Representation learning vs. downstream task.** If embeddings are trained and then evaluated on a downstream task that is the stated goal, label the downstream task. Use `representation_learning` only when the embeddings themselves are the deliverable.

---

## Dimension 2: Project kind

| Label | Definition | Typical signals in the README |
|---|---|---|
| `competition_entry` | Code written for a data-science competition, challenge, or hackathon. | Mentions Kaggle, DrivenData, AIcrowd, a shared task, a challenge leaderboard, a hackathon |
| `research_prototype` | Code supporting scientific research: accompanying a paper, thesis, or experiments meant to produce or reproduce results. | Links to a paper or arXiv preprint, BibTeX citation, "official implementation", "reproduce the results", tables of experimental results, thesis or lab project |
| `library_tool` | Reusable software meant to be used by other developers to build, train, or evaluate models. | Installation via `pip install`, API documentation, usage as an import, versioned releases, a CLI meant for general use |
| `application` | A system or service that delivers a trained model's functionality to end users. | Web or mobile app, REST API, bot, dashboard, deployment instructions (Docker, cloud), screenshots or demo of a user interface |
| `learning_portfolio` | Personal, educational, or showcase project whose main purpose is learning or demonstrating skills. | Course assignment, tutorial follow-along, "my first project", bootcamp or university coursework, portfolio piece, practice on a public dataset |
| `other` | The kind is clear but fits no category above (e.g., internal company pipeline, data analysis for a client). | Must be justified in free text |
| `unclear` | The README does not allow the kind to be determined. | |

### Decision rules (project kind)

Apply the rules **in order** and stop at the first that matches:

1. If the README states that the code was written for a competition, challenge, or hackathon → `competition_entry`, even if it is also a learning project or was later published as a paper.
2. If the README links to or cites a scientific publication, preprint, or thesis that the code implements → `research_prototype`.
3. If the repository is primarily meant to be installed or imported by others → `library_tool`.
4. If the repository delivers a model to end users through an interface or deployed service → `application`.
5. If the README presents the project as coursework, a tutorial, practice, or a portfolio piece → `learning_portfolio`.
6. Otherwise → `other` (with justification) or `unclear`.

Notes:

- A research project that also ships a demo (e.g., a Gradio or Hugging Face Space) remains `research_prototype` (rule 2 precedes rule 4).
- A personal project that wraps a model in a small web app is `application` only if the app is presented as the main deliverable; if the README frames it as practice or a portfolio piece, use `learning_portfolio`.
- Repositories of major ML libraries are already removed during dataset filtering (Section V-B); `library_tool` covers the remaining smaller tools and wrappers.

---

## Output format

Each project is labeled with the following record (used both for LLM outputs and for human annotations):

```json
{
  "repository": "owner/name",
  "ml_task": "classification",
  "project_kind": "research_prototype",
  "justification": "One or two sentences citing the README elements that support the labels."
}
```

Only the labels defined above are allowed. The `justification` field is mandatory for `other` and `unclear` and recommended otherwise.

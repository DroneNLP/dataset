
**Overview**
- **Objective:** Provide two text-classification datasets (binary and multiclass) for identifying anomalous or problematic drone flight-log messages to support digital forensics investigations of drone devices.

**Dataset Structure**
- **Binary task:** Located in `/development/annotated/problem_identification/binary`. Each of `train.csv` and `test.csv` contains two columns: `text` and `labels`. The labels are `Normal` and `Problem` and were chosen to be directly compatible with the SimpleTransformers library.
- **Multiclass (severity) task:** Located in `development/annotated/problem_identification/severity`. There are two subfolders: `duplicate` and `unique` (samples with or without duplicate messages). Each CSV contains two columns: `message` and `label`. The classes are `Normal`, `Low`, `Medium`, and `High` describing severity levels.

**Labels**
- **Binary:** `Normal`, `Problem` (2 classes).
- **Multiclass:** `Normal`, `Low`, `Medium`, `High` (4 classes). Use an explicit mapping to integer labels when training (example below).

**How this helps digital forensics**
- **Purpose:** Assist investigators by automatically flagging flight-log messages that are likely to indicate device malfunctions, unsafe behaviour, or other events of forensic interest.
- **Use cases:** triage large collections of flight logs, surface candidate time ranges for manual inspection, prioritize logs in incident response, and speed up annotation for case studies.

**Preparing data for model development**
- SimpleTransformers expects `text` and `labels` columns. The binary files are already formatted this way. For multiclass files, rename columns and map labels to integers before training. Example mapping: `{'Normal':0, 'Low':1, 'Medium':2, 'High':3}`.
- Minimal preprocessing recommended: keep original message text, remove obvious machine-only metadata if present (timestamp columns not required), and preserve tokenization-sensitive content (punctuation, abbreviations) since models benefit from raw signal.

**Quick start — training with SimpleTransformers**
- Example: binary classification using a pretrained transformer (replace model and paths as desired):

```python
import pandas as pd
from simpletransformers.classification import ClassificationModel

# Load binary dataset
train_df = pd.read_csv('development/annotated/problem_identification/binary/train.csv')
eval_df = pd.read_csv('development/annotated/problem_identification/binary/test.csv')

model = ClassificationModel(
	'roberta',
	'roberta-base',
	num_labels=2,
	args={'reprocess_input_data': True, 'overwrite_output_dir': True}
)
model.train_model(train_df)
result, model_outputs, wrong_predictions = model.eval_model(eval_df)
```

- Example: multiclass (severity) — rename and map labels first:

```python
import pandas as pd
from simpletransformers.classification import ClassificationModel

mapping = {'Normal':0, 'Low':1, 'Medium':2, 'High':3}
df = pd.read_csv('development/annotated/problem_identification/severity/unique/filtered_train.csv')
df = df.rename(columns={'message':'text', 'label':'labels'})
df['labels'] = df['labels'].map(mapping)

model = ClassificationModel('roberta', 'roberta-base', num_labels=4, args={'overwrite_output_dir': True})
model.train_model(df)
```

**Evaluation and prediction**
- Use `model.eval_model(eval_df)` to compute metrics on an evaluation set (make sure `eval_df` has `text` and `labels`).
- For single predictions use `preds, raw_outputs = model.predict(['example message'])`. Map predicted indices back to label names using the inverse of your label mapping.

**Real-world case study**
- A collection of flight logs for case studies is available under [case-study](case-study). Annotated flight logs for these case studies will be added soon (binary task annotations arriving first). Once present, convert those annotations into the same `text`/`labels` CSV format to reuse the training and evaluation recipes above.

**Best practices and notes**
- **Label balance:** inspect class distribution; apply stratified splits or class weights for imbalanced classes.
- **Duplicate samples (multiclass):** experiments can compare `duplicate` vs `unique` folders to measure sensitivity to repeated messages.
- **Reproducibility:** pin model checkpoints (e.g., `roberta-base`) and record training args and random seeds.
- **Forensics caution:** automated labels are triage aids, not final evidence — manual analyst review is required for investigative conclusions.

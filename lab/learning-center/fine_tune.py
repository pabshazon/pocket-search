from transformers import AutoModelForSequenceClassification, AutoTokenizer
from transformers import Trainer, TrainingArguments
from datasets import load_dataset, load_dataset_builder

model = AutoModelForSequenceClassification.from_pretrained("distilbert-base-uncased", num_labels=2)
tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")

ds_info = load_dataset_builder("imdb")
print(ds_info.info)
exit()
print(ds_info.info.splits)
print(ds_info.info.dataset_name)
print(ds_info.info.description)
print(ds_info.info.dataset_size)
print(ds_info.info.features)
print(ds_info.get_all_exported_dataset_infos())

dataset_train = load_dataset("imdb", split="train")
dataset_eval = load_dataset("imdb", split="test")
dataset_train.set_format(type="torch", columns=["text", "label"])

def tokenization(sequence):
    return tokenizer(sequence["text"], padding="max_length", truncation=True)

dataset_train_tokenized = dataset_train.map(tokenization, batched=True)
dataset_eval_tokenized  = dataset_eval.map(tokenization, batched=True)

dataset_train_tokenized.set_format(type="torch", columns=["input_ids", "attention_mask", "label"])
dataset_eval_tokenized.set_format(type="torch", columns=["input_ids", "attention_mask", "label"])

training_args = TrainingArguments(
    output_dir="../../service/python/reasoning-engine/src/domain/on_metal/nlp/output",
    eval_strategy="epoch",
    learning_rate=2e-5,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=16,
    num_train_epochs=2,
    weight_decay=0.01,
    logging_steps=50
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=dataset_train_tokenized,
    eval_dataset=dataset_eval_tokenized
)

trainer.train()

import numpy as np

predictions       = trainer.predict(dataset_eval_tokenized)
prediction_labels = np.argmax(predictions.predictions, axis=1)
true_labels       = np.array(dataset_eval_tokenized["label"])

accuracy = (prediction_labels == true_labels).mean()
print("Test Accuracy: ", accuracy)

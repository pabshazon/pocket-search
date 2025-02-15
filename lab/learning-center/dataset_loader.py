from datasets import load_dataset_builder, load_dataset, get_dataset_split_names, get_dataset_config_names
from transformers import AutoTokenizer

dataset_builder = load_dataset_builder("rotten_tomatoes")

print("Inspect info of ds:\n")
print(dataset_builder.info.dataset_name)
print(dataset_builder.info.description)
print(dataset_builder.info.dataset_size)
print(dataset_builder.info.features)

# dataset = load_dataset("rotten_tomatoes")
dataset_train = load_dataset("rotten_tomatoes", split="train")

print(get_dataset_split_names("rotten_tomatoes"))
#
# print(dataset)
print(dataset_train)

# print(get_dataset_config_names("PolyAI/minds14"))
#
# mindsEN = load_dataset("PolyAI/minds14", "en-US", split="train")

tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
print(dataset_train[0]["text"])

print(tokenizer(dataset_train[0]["text"]))

def tokenization(sequence):
    return tokenizer(sequence["text"])

dataset = dataset_train.map(tokenization, batched=True)
dataset.set_format(type="torch", columns=["input_ids", "token_type_ids", "attention_mask", "label"])
print(dataset.format["type"])

labels = dataset["label"]

# Check labels distribution in pytorch:
import torch
unique_labels, counts = torch.unique(dataset["label"], return_counts=True)
for label, count in zip(unique_labels.tolist(), counts.tolist()):
    print(f"Label {label}: {count} samples ({count/len(dataset)*100:.2f}%)")


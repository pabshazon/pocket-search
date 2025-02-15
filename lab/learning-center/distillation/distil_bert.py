from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    Trainer,
    TrainingArguments
)
import torch
import torch.nn as nn
from torch.nn import functional as F
from datasets import load_dataset
import numpy as np


# 1. Define the smaller student architecture
class DistilledBERTStudent(nn.Module):
    def __init__(self, hidden_size=256, num_layers=3, num_labels=2):
        super().__init__()
        self.embeddings = nn.Embedding(30522, hidden_size)  # BERT vocab size

        # Smaller transformer blocks
        self.layers = nn.ModuleList([
            nn.TransformerEncoderLayer(
                d_model=hidden_size,
                nhead=4,  # Reduced from BERT's 12
                dim_feedforward=hidden_size * 4,
                dropout=0.1
            ) for _ in range(num_layers)
        ])

        self.classifier = nn.Linear(hidden_size, num_labels)

    def forward(self, input_ids, attention_mask=None):
        x = self.embeddings(input_ids)

        # Apply transformer layers
        for layer in self.layers:
            x = layer(x)

        # Pool and classify
        pooled = x.mean(dim=1)  # Simple mean pooling
        logits = self.classifier(pooled)
        return logits


# 2. Distillation loss function
def distillation_loss(student_logits, teacher_logits, labels, temperature=2.0, alpha=0.5):
    """
    Combine soft and hard targets for knowledge distillation
    """
    # Soft targets with temperature
    soft_targets = F.softmax(teacher_logits / temperature, dim=-1)
    soft_prob = F.log_softmax(student_logits / temperature, dim=-1)
    soft_loss = -(soft_targets * soft_prob).sum(dim=-1).mean()

    # Hard targets
    hard_loss = F.cross_entropy(student_logits, labels)

    # Combine losses
    return (alpha * temperature * temperature * soft_loss +
            (1 - alpha) * hard_loss)


# 3. Custom trainer for distillation
class DistillationTrainer(Trainer):
    def __init__(self, teacher_model, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.teacher_model = teacher_model

    def compute_loss(self, model, inputs, return_outputs=False):
        # Get teacher predictions
        with torch.no_grad():
            teacher_outputs = self.teacher_model(**inputs)
            teacher_logits = teacher_outputs.logits

        # Get student predictions
        student_outputs = model(**inputs)
        student_logits = student_outputs.logits

        # Calculate distillation loss
        loss = distillation_loss(
            student_logits=student_logits,
            teacher_logits=teacher_logits,
            labels=inputs["labels"],
            temperature=2.0,
            alpha=0.5
        )

        return (loss, student_outputs) if return_outputs else loss


def main():
    # Load teacher model (e.g., BERT for sentiment analysis)
    teacher_model = AutoModelForSequenceClassification.from_pretrained(
        "bert-base-uncased",
        num_labels=2
    )
    tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")

    # Create student model
    student_model = DistilledBERTStudent(
        hidden_size=256,  # Smaller than BERT's 768
        num_layers=3,  # Smaller than BERT's 12
        num_labels=2
    )

    # Load and prepare dataset (e.g., IMDB)
    dataset = load_dataset("imdb")

    def tokenize_function(examples):
        return tokenizer(
            examples["text"],
            padding="max_length",
            truncation=True,
            max_length=128
        )

    tokenized_datasets = dataset.map(
        tokenize_function,
        batched=True,
        remove_columns=dataset["train"].column_names
    )

    # Training arguments
    training_args = TrainingArguments(
        output_dir="./distilled_model",
        num_train_epochs=3,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=64,
        warmup_steps=500,
        weight_decay=0.01,
        logging_dir="./logs",
        evaluation_strategy="epoch",
    )

    # Initialize trainer
    trainer = DistillationTrainer(
        teacher_model=teacher_model,
        model=student_model,
        args=training_args,
        train_dataset=tokenized_datasets["train"],
        eval_dataset=tokenized_datasets["test"],
    )

    # Train the model
    trainer.train()

    # Evaluate
    metrics = trainer.evaluate()
    print(f"Evaluation metrics: {metrics}")

    # Compare model sizes
    def count_parameters(model):
        return sum(p.numel() for p in model.parameters())

    teacher_size = count_parameters(teacher_model)
    student_size = count_parameters(student_model)

    print(f"Teacher model size: {teacher_size:,} parameters")
    print(f"Student model size: {student_size:,} parameters")
    print(f"Size reduction: {(1 - student_size / teacher_size) * 100:.2f}%")


if __name__ == "__main__":
    main()
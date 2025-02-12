from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.domain.on_metal.nlp.tokenizers import TokenizerFactory

import torch
import torch.nn as nn


class EmbeddingsController:
    def __init__(self):
        pass

    @staticmethod
    def embed(text: str, model_type: str = "encoder_focus_bert", task):
        tokenizer, model  = TokenizerFactory.make(model_type)
        text_tensors      = tokenizer(text, return_tensors="pt", truncation=True, padding=True)

        # Forward pass through the model
        with torch.no_grad():
            outputs = model(**text_tensors)
        
        # Extract embeddings (use the [CLS] token embedding for BERT, or equivalent for GPT)
        embeddings = outputs.last_hidden_state[:, 0, :].squeeze().tolist()
        response   = { "embeddings": embeddings, "text": text, "model": model, "task": task }
        
        return response

    @staticmethod
    def search(
            text: str,
            search_space: dict = {"name": "default", "model_type": "encoder_focus_bert"},
            distance: dict = {"type": "cosine", "value": 0.8}):

        tokenizer, model = TokenizerFactory.make(search_space.model_type)
        text_tensors     = tokenizer(text, return_tensors="pt", truncation=True, padding=True)

        # Forward pass through the model
        with torch.no_grad():
            outputs = model(**text_tensors)

        # Extract embeddings (use the [CLS] token embedding for BERT, or equivalent for GPT)
        embeddings = outputs.last_hidden_state[:, 0, :].squeeze().tolist()
        response = {"embeddings": embeddings, "text": text, "model": model, "task": task}

        return response



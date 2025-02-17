from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class ModelConfig:
    name: str
    max_length: int
    device_priority: list[str] = ("cuda", "cpu")  # mps can be added if needed
    model_params: Dict[str, Any] = None

    def __post_init__(self):
        if self.model_params is None:
            self.model_params = {}

class ModelsConfig:
    # Summarization Models
    SUMMARIZER = ModelConfig(
        name="facebook/bart-large-cnn",
        max_length=1024,
        model_params={
            "num_beams": 4,
            "length_penalty": 2.0,
            "early_stopping": True,
            "no_repeat_ngram_size": 3
        }
    )

    # Document Layout Analysis
    LAYOUT = ModelConfig(
        name="microsoft/layoutlmv3-base",
        max_length=512,
        model_params={
            "padding": True,
            "truncation": True
        }
    )

    # Code Analysis
    CODE = ModelConfig(
        name="microsoft/codebert-base",
        max_length=512,
        model_params={
            "padding": True,
            "truncation": True
        }
    )

    # Visual Language Model
    VISION = ModelConfig(
        name="dandelin/vilt-b32-finetuned-vqa",
        max_length=512,
        model_params={
            "padding": True,
            "return_tensors": "pt"
        }
    )

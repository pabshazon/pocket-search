from dataclasses import dataclass

@dataclass
class ModelInfo:
    max_tokens: int
    tokenizer_chars_per_token: int

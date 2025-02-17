import torch
from typing import Optional

class DeviceConfig:
    @staticmethod
    def get_device(priority_list: list[str] = None) -> torch.device:
        if priority_list is None:
            priority_list = ["cuda", "cpu"]
        
        for device in priority_list:
            if device == "cuda" and torch.cuda.is_available():
                return torch.device("cuda")
            elif device == "mps" and torch.backends.mps.is_available():
                return torch.device("mps")
            elif device == "cpu":
                return torch.device("cpu")
        
        return torch.device("cpu")  # fallback

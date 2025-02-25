import platform
import psutil

from argparse import ArgumentError
from typing import Dict, Optional

import torch
from transformers import AutoTokenizer

from src.domain.on_metal.nlp.model_info import ModelInfo


class VRamMemory:
    def __init__(self):
        self.is_apple_silicon = self._detect_hardware()
        self.models_info      = self._initialize_models_info()

    def get_available_memory(self, units: str = "tokens"):
        if units != "tokens": raise ArgumentError(None, "Units argument cannot be None.")

        if units == "tokens":
            bytes_per_token         = 2048  # @todo get from the tokenizer and/or as argument?
            available_memory_bytes  = self._get_available_memory()  # @todo confirm this is in bytes?
            available_memory_tokens = available_memory_bytes / bytes_per_token

            return available_memory_tokens
        else:
            raise ArgumentError(f"Units '{units}' is not implemented yet. Only 'tokens' unit is available for now.")

    def get_memory_info(self) -> float:
        if self.available_bytes is not None:
            return round(self.available_bytes / (1024 ** 3), 2)
        return 0.0

    def get_hardware_info(self) -> str:
        if not self.is_apple_silicon:
            return "CPU"  # @todo - would be x86_64 if not Apple Silicon. and then need to decide cpu or gpu.

        has_mps = torch.backends.mps.is_available() and torch.backends.mps.is_built()
        return "mps" if has_mps else "cpu"

    def estimate_model_contexts(self) -> dict:
        return {
            "system_info": {
                "available_ram": self.get_memory_info(),
                "hardware":      self.get_hardware_info()
            },
            "models": {
                model_name: self._get_model_context_info(model_name, info) for model_name, info in self.models_info.items()
            }
        }

    def _get_available_memory(self) -> Optional[int]:
        try:
            return psutil.virtual_memory().available
        except ImportError:
            return self._get_memory_fallback()
    
    def _get_memory_fallback(self) -> Optional[int]:
        try:
            system = platform.system()
            if system == "Darwin":
                return self._get_macos_memory()
            elif system == "Linux":
                return self._get_linux_memory()
            elif system == "Windows":
                return self._get_windows_memory()
        except Exception:
            return None

    @staticmethod
    def _get_macos_memory() -> int:
        import subprocess
        mem_bytes = subprocess.check_output(["sysctl", "hw.memsize"])
        return int(mem_bytes.split()[1])

    @staticmethod
    def _get_linux_memory() -> Optional[int]:
        with open("/proc/meminfo", "r") as f:
            meminfo = f.read()
        import re
        match = re.search(r'MemAvailable:\s+(\d+) kB', meminfo)
        if match:
            return int(match.group(1)) * 1024
        match = re.search(r'MemTotal:\s+(\d+) kB', meminfo)
        if match:
            return int(match.group(1)) * 1024
        return None

    @staticmethod
    def _get_windows_memory() -> int:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        mem_kb = ctypes.c_ulonglong(0)
        kernel32.GetPhysicallyInstalledSystemMemory(ctypes.byref(mem_kb))
        return int(mem_kb.value) * 1024

    @staticmethod
    def _detect_hardware() -> bool:
        return platform.system() == "Darwin" and platform.machine() == "arm64"
    
    def _initialize_models_info(self) -> Dict[str, ModelInfo]:
        models_info = {
            "T5": ModelInfo(512, 4),
            "BART": ModelInfo(1024, 4),
            "LLaMA 3.3": ModelInfo(130000, 4)
        }
        self._update_with_huggingface_info(models_info)
        return models_info

    @staticmethod
    def _update_with_huggingface_info(models: Dict[str, ModelInfo]) -> None:
        try:
            hf_model_names = {
                "T5": "t5-base",
                "BART": "facebook/bart-large-cnn",
                "LLaMA 3.3": "meta-llama/Llama-3.3-70B-Instruct"
            }
            for model, name in hf_model_names.items():
                try:
                    tokenizer = AutoTokenizer.from_pretrained(name)
                    max_len = getattr(tokenizer, "model_max_length", None)
                    if max_len and isinstance(max_len, int):
                        models[model].max_tokens = max_len
                except Exception:
                    continue
        except ImportError:
            pass

    def _get_model_context_info(self, info: ModelInfo) -> dict:
        approx_chars = info.max_tokens * info.tokenizer_chars_per_token
        approx_kb    = approx_chars / 1024.0
        
        return {
            "max_tokens":           info.max_tokens,
            "approx_characters":    approx_chars,
            "approx_input_size_kb": round(approx_kb, 2),
        }

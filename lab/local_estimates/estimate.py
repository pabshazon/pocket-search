import platform
import math

# Try to get available RAM in bytes
try:
    import psutil
    available_bytes = psutil.virtual_memory().available
    print(f"Available RAM: {available_bytes}")
except ImportError:
    # Fallback method if psutil is not installed
    available_bytes = None
    try:
        # Attempt OS-specific approaches
        if platform.system() == "Darwin":  # macOS (including Apple Silicon)
            import subprocess
            mem_bytes = subprocess.check_output(["sysctl", "hw.memsize"])
            available_bytes = int(mem_bytes.split()[1])
        elif platform.system() == "Linux":
            with open("/proc/meminfo", "r") as f:
                meminfo = f.read()
            # Parse MemAvailable if possible, else MemTotal
            import re
            match = re.search(r'MemAvailable:\s+(\d+) kB', meminfo)
            if match:
                available_bytes = int(match.group(1)) * 1024
            else:
                match = re.search(r'MemTotal:\s+(\d+) kB', meminfo)
                if match:
                    available_bytes = int(match.group(1)) * 1024
        elif platform.system() == "Windows":
            import ctypes
            kernel32 = ctypes.windll.kernel32
            c_ulonglong = ctypes.c_ulonglong
            mem_kb = c_ulonglong(0)
            kernel32.GetPhysicallyInstalledSystemMemory(ctypes.byref(mem_kb))
            available_bytes = int(mem_kb.value) * 1024  # from kB to bytes
    except Exception:
        available_bytes = None

# Convert available memory to a human-readable format (GB)
if available_bytes is not None:
    available_gb = available_bytes / (1024**3)
    mem_info = f"{available_gb:.2f} GB"
else:
    mem_info = "Unknown"

# Detect if running on Apple Silicon
is_apple_silicon = (platform.system() == "Darwin" and platform.machine() == "arm64")
hardware = "Apple Silicon" if is_apple_silicon else "CPU"

# Predefined model context limits (tokens) and tokenizer char-per-token estimates.
# We'll use a dictionary for ease of extension.
models = {
    "T5": {
        "max_tokens": 512,    # typical T5-base max input trained on&#8203;:contentReference[oaicite:8]{index=8}
        "tokenizer_chars_per_token": 4  # approx average chars per token
    },
    "BART": {
        "max_tokens": 1024,   # BART absolute positional embedding limit&#8203;:contentReference[oaicite:9]{index=9}
        "tokenizer_chars_per_token": 4
    },
    "LLaMA 3.3": {
        "max_tokens": 130000, # LLaMA 3.3 theoretical context window&#8203;:contentReference[oaicite:10]{index=10}
        "tokenizer_chars_per_token": 4
    }
}

# If Hugging Face transformers is available, attempt to get exact tokenizer model_max_length
# for more accuracy (especially in case defaults differ or using different variants).
try:
    from transformers import AutoTokenizer
    # Update max_tokens from tokenizer config if possible
    # (Using common model identifiers; adjust if needed for specific versions)
    hf_model_names = {
        "T5": "t5-base",
        "BART": "facebook/bart-large-cnn",         # BART model fine-tuned for summarization
        "LLaMA 3.3": "meta-llama/Llama-3.3-70B-Instruct"  # LLaMA 3.3 70B Instruct model
    }
    for model, name in hf_model_names.items():
        try:
            tokenizer = AutoTokenizer.from_pretrained(name)
            max_len = getattr(tokenizer, "model_max_length", None)
            if max_len and isinstance(max_len, int):
                models[model]["max_tokens"] = max_len
        except Exception:
            continue  # If any tokenizer isn't available or requires large downloads, skip
except ImportError:
    pass

# Estimate and display maximum context size for each model
print(f"Available RAM: {mem_info}")
print(f"Hardware: {hardware}")
print("Estimated Maximum Input Sizes per Model:\n")

for model, info in models.items():
    max_tokens = info["max_tokens"]
    chars_per_tok = info.get("tokenizer_chars_per_token", 4)
    # Calculate character count (approx) and size in KB
    approx_chars = max_tokens * chars_per_tok
    approx_kb   = approx_chars / 1024.0

    # Prepare notes about any adjustments or warnings due to memory
    notes = ""
    if available_bytes:
        # Rough heuristic: assume each token might use ~2 KB of memory for model's internal states (varies by model size).
        # This is a simplistic estimate to warn for extremely large token counts on limited RAM.
        per_token_mem = 2048  # bytes per token (2 KB per token as a rough average for large models)
        required_mem = max_tokens * per_token_mem
        if required_mem > available_bytes:
            notes = "(Memory may be insufficient for full context)"
    # Print the results in a readable format
    print(f"{model}:")
    print(f"  - Max tokens: {max_tokens:,} tokens")
    print(f"  - Approx. characters: ~{approx_chars:,} chars")
    print(f"  - Approx. input size: ~{approx_kb:.2f} KB {notes}")
    print("")

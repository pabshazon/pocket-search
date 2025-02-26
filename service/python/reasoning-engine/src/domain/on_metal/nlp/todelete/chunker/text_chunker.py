import math
import logging
from argparse import ArgumentError
from typing import List

from src.domain.on_metal.context.vram_memory import VRamMemory

logging.basicConfig(
    level=logging.INFO,  # @todo abstract from env variable
    format='%(message)s'
)
logger = logging.getLogger(__name__)

# @todo improve the guestimate approach
guestimate_chars_per_token = 4


class TextChunker:

    @staticmethod
    def token_chunks_that_fit_in_memory(full_text: str, tokenizer=None, ensure_free_kbs: int = 0, min_num_of_chunks: int = 1) -> List[str]:
        if tokenizer is not None:
            full_text_tokens = tokenizer.encode(full_text)
            full_text_num_tokens = len(full_text_tokens)
        else:
            raise ArgumentError("tokenizer", "Tokenizer cannot be None.")
            #@todo argument type above

        available_memory_tokens = VRamMemory().get_available_memory(unit="tokens")
        available_memory_tokens -= ensure_free_kbs / guestimate_chars_per_token

        num_chunks            = max(min_num_of_chunks, math.ceil(full_text_num_tokens / available_memory_tokens))
        tokens_size_per_chunk = full_text_num_tokens / num_chunks

        logger.debug(f"Text contains {len(full_text)} chars and {full_text_num_tokens} tokens.")
        logger.debug(f"Split text into {num_chunks} chunks based on token count of {tokens_size_per_chunk} tokens each.")

        chunks = TextChunker._chunk(full_text_num_tokens, num_chunks)

        return chunks

    @staticmethod
    def _chunk(full_text_num_tokens, num_chunks):
        chunks = []
        current_chunk = ""
        current_tokens = 0
        words = full_text_num_tokens.split()
        for word in words:
            word_tokens = len(self.tokenizer.encode(word))
            if current_tokens + word_tokens > max_safe_tokens:
                chunks.append(current_chunk.strip())
                current_chunk = word
                current_tokens = word_tokens
            else:
                current_chunk += " " + word if current_chunk else word
                current_tokens += word_tokens
        if current_chunk:
            chunks.append(current_chunk.strip())
        return chunks

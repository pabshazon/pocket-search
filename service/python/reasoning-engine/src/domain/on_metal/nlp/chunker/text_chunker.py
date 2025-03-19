import math
import logging
from argparse import ArgumentError
from typing import List

from src.domain.on_metal.context.vram_memory import VRamMemory
from src.domain.on_metal.logger import get_logger
logger = get_logger(__name__)


# @todo improve the guestimate approach
guestimate_chars_per_token = 4
guestimate_overlap_tokens = 50

class TextChunker:

    @staticmethod
    def token_chunks_that_fit_in_memory(full_text: str, tokenizer=None, ensure_free_kbs: int = 0, min_num_of_chunks: int = 1) -> List[str]:
        if tokenizer is not None:
            full_text_tokens = tokenizer.encode(full_text)
            full_text_num_tokens = len(full_text_tokens)
        else:
            raise ArgumentError("tokenizer", "Tokenizer cannot be None.")
            #@todo argument type above

        max_context_size_tokens = VRamMemory().get_max_context_size(units="tokens")
        max_context_size_tokens -= ensure_free_kbs / guestimate_chars_per_token

        num_chunks            = max(min_num_of_chunks, math.ceil(full_text_num_tokens / max_context_size_tokens))
        tokens_size_per_chunk = full_text_num_tokens / num_chunks

        logger.debug(f"TextChunker - Text contains {len(full_text)} chars and {full_text_num_tokens} tokens.")
        logger.debug(f"TextChunker - Split text into {num_chunks} chunks based on token count of {tokens_size_per_chunk} tokens each.")

        chunks = TextChunker._chunk(full_text, num_chunks, tokenizer, tokens_size_per_chunk, guestimate_overlap_tokens)

        return chunks

    @staticmethod
    def _chunk(full_text: str, num_chunks: int, tokenizer, tokens_size_per_chunk: float, overlap_tokens: int = 0) -> List[str]:
        words = full_text.split()
        total_tokens = len(tokenizer.encode(full_text))
        # Adjust min_tokens considering overlap
        effective_total = total_tokens + (overlap_tokens * (num_chunks - 1))
        min_tokens_per_chunk = effective_total / num_chunks
        
        chunks = []
        current_chunk = ""
        current_chunk_words = []
        current_tokens = 0
        overlap_words = []
        overlap_tokens_count = 0
        
        for word in words:
            word_tokens = len(tokenizer.encode(word))
            
            # If this chunk is full (considering overlap requirement)
            if current_tokens + word_tokens > tokens_size_per_chunk - overlap_tokens:
                # Store the current chunk
                chunks.append(current_chunk.strip())
                
                # Initialize next chunk with overlap words
                if overlap_tokens > 0:
                    # Calculate overlap from current chunk
                    overlap_words = []
                    overlap_tokens_count = 0
                    for w in reversed(current_chunk_words):
                        w_tokens = len(tokenizer.encode(w))
                        if overlap_tokens_count + w_tokens > overlap_tokens:
                            break
                        overlap_words.insert(0, w)
                        overlap_tokens_count += w_tokens
                    
                    # Start new chunk with overlap
                    current_chunk = " ".join(overlap_words)
                    current_chunk_words = overlap_words.copy()
                    current_tokens = overlap_tokens_count
                else:
                    current_chunk = ""
                    current_chunk_words = []
                    current_tokens = 0
            
            # Add the current word
            current_chunk += " " + word if current_chunk else word
            current_chunk_words.append(word)
            current_tokens += word_tokens
        
        # Add the last chunk if there's anything left
        if current_chunk:
            chunks.append(current_chunk.strip())
            
        # Adjust number of chunks if needed
        while len(chunks) < num_chunks:
            # Find the chunk with the most tokens
            chunk_tokens = [(i, len(tokenizer.encode(chunk))) 
                          for i, chunk in enumerate(chunks)]
            largest_idx, _ = max(chunk_tokens, key=lambda x: x[1])
            
            # Split the largest chunk
            words_to_split = chunks[largest_idx].split()
            mid = len(words_to_split) // 2
            
            # Calculate overlap for the split
            overlap_start = max(0, mid - (overlap_tokens // 2))
            overlap_end = min(len(words_to_split), mid + (overlap_tokens // 2))
            
            first_half = " ".join(words_to_split[:overlap_end])
            second_half = " ".join(words_to_split[overlap_start:])
            
            chunks[largest_idx] = first_half
            chunks.insert(largest_idx + 1, second_half)
        
        # If we have too many chunks, combine smallest adjacent pairs
        while len(chunks) > num_chunks:
            smallest_pair_idx = 0
            smallest_pair_tokens = float('inf')
            
            for i in range(len(chunks) - 1):
                combined = chunks[i] + " " + chunks[i + 1]
                pair_tokens = len(tokenizer.encode(combined))
                if pair_tokens < smallest_pair_tokens and pair_tokens <= tokens_size_per_chunk:
                    smallest_pair_idx = i
                    smallest_pair_tokens = pair_tokens
            
            # Combine the smallest pair
            chunks[smallest_pair_idx] = chunks[smallest_pair_idx] + " " + chunks[smallest_pair_idx + 1]
            chunks.pop(smallest_pair_idx + 1)
            
        return chunks

    @staticmethod
    def split_for_map_reduce(text: str, tokenizer, chunk_size: int = 4000, chunk_overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks for map-reduce summarization"""
        if not text:
            return []
            
        tokens = tokenizer.encode(text)
        chunks = []
        
        for i in range(0, len(tokens), chunk_size - chunk_overlap):
            chunk_tokens = tokens[i:i + chunk_size]
            chunk_text = tokenizer.decode(chunk_tokens, skip_special_tokens=True)
            chunks.append(chunk_text)
            
        return chunks
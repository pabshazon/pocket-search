import logging
from typing import List
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch
import math
import time

from src.domain.on_metal.nlp.models.context_estimator   import ContextEstimator
from src.config.models_config                           import ModelsConfig
from src.config.device_config                           import DeviceConfig

logging.basicConfig(
    level=logging.INFO,  # @todo abstract from env variable
    format='%(message)s'
)
logger = logging.getLogger(__name__)


class PdfSummarizer:
    def __init__(self):
        try:
            logger.debug(f"> Initializing PdfSummarizer")
            self.config             = ModelsConfig.SUMMARIZER
            self.model              = self.config.model
            self.tokenizer          = self.config.tokenizer
            self.device             = self.config.device
            self.max_chunk_length   = self.config.max_length
            self.max_summary_length = 250
        except Exception as e:
            logger.error(f"Failed to initialize PdfSummarizer: {str(e)}", exc_info=True)
            raise

    def summarize(self, text_content: str, min_num_of_chunks: int = 1) -> str:
        if not text_content:
            logger.warning("Empty text to summarize provided")
            return ""
            
        try:
            start_time = time.time()
            logger.debug(f"Starting summarization of {len(text_content)} characters")
            
            context_estimator = ContextEstimator()
            model_contexts    = context_estimator.estimate_model_contexts()
            bart_context      = model_contexts["models"]["BART"]
            
            content_num_tokens = len(self.tokenizer.encode(text_content))
            max_safe_tokens = self.max_chunk_length
            
            logger.debug(f"Text contains {content_num_tokens} tokens")
            num_chunks = max(min_num_of_chunks, math.ceil(content_num_tokens / max_safe_tokens))
            
            logger.debug(f"Split text into {num_chunks} chunks based on token count")
            
            chunking_start_time = time.time()
            chunks = []
            current_chunk = ""
            current_tokens = 0
            words = text_content.split()
            
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
                
            chunking_time = time.time() - chunking_start_time
            logger.debug(f"Text chunking took {chunking_time:.2f}s")
            
            macro_chunks_summaries  = []
            total_tokenization_time = 0
            total_generation_time   = 0
            
            for i in range(num_chunks):
                start_idx   = i * max_safe_tokens
                end_idx     = min((i + 1) * max_safe_tokens, len(text_content))
                chunk_text  = text_content[start_idx:end_idx]
                
                chunk_summary, tok_time, gen_time = self._summarize_chunk(chunk_text)
                total_tokenization_time += tok_time
                total_generation_time += gen_time
                
                if chunk_summary:
                    macro_chunks_summaries.append(chunk_summary)
            
            if not macro_chunks_summaries:
                logger.warning("No valid summaries generated from macro chunks")
                return ""
            
            final_summary, final_tok_time, final_gen_time = self._create_final_summary(macro_chunks_summaries)
            total_time = time.time() - start_time
            
            logger.debug(f"Summarization Performance Metrics:")
            logger.debug(f"- Total time: {total_time:.2f}s")
            logger.debug(f"- Chunking time: {chunking_time:.2f}s")
            logger.debug(f"- Total tokenization time: {total_tokenization_time + final_tok_time:.2f}s")
            logger.debug(f"- Total generation time: {total_generation_time + final_gen_time:.2f}s")
            logger.debug(f"- Average tokenization time per chunk: {total_tokenization_time/num_chunks:.2f}s")
            logger.debug(f"- Average generation time per chunk: {total_generation_time/num_chunks:.2f}s")
            logger.debug(f"Generated final summary of {len(final_summary)} characters")
            logger.debug(f"Final summary: {final_summary}")
            
            return final_summary
                
        except Exception as e:
            logger.error(f"Unexpected error in summarize method: {str(e)}", exc_info=True)
            return ""
    
    def _summarize_chunk(self, text: str) -> tuple[str, float, float]:
        if not isinstance(text, str):
            logger.error(f"Invalid input type for summarization: {type(text)}")
            return "", 0.0, 0.0
            
        if not text.strip():
            logger.warning("Empty text provided for summarization")
            return "", 0.0, 0.0
            
        try:
            tok_start = time.time()
            inputs = self.tokenizer(
                text,
                max_length=self.max_chunk_length,
                truncation=True,
                return_tensors="pt"
            ).to(self.device)
            tokenization_time = time.time() - tok_start
            
            try:
                gen_start = time.time()
                with torch.no_grad():
                    summary_ids = self.model.generate(
                        inputs["input_ids"],
                        max_length=self.max_summary_length,
                        num_beams=4,
                        length_penalty=2.0,
                        early_stopping=True,
                        no_repeat_ngram_size=3
                    )
                generation_time = time.time() - gen_start
                
                summary = self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)
                if not summary.strip():
                    logger.warning("Generated empty summary")
                    return "", tokenization_time, generation_time
                    
                logger.debug(f"Chunk processing times - Tokenization: {tokenization_time:.2f}s, Generation: {generation_time:.2f}s")
                return summary, tokenization_time, generation_time
                
            except torch.cuda.OutOfMemoryError as e:
                logger.error("CUDA out of memory error", exc_info=True)
                torch.cuda.empty_cache()
                return text[:self.max_summary_length], 0.0, 0.0  # Fallback
                
            except Exception as e:
                logger.error(f"Error in model generation: {str(e)}", exc_info=True)
                return "", tokenization_time, 0.0
                
        except Exception as e:
            logger.error(f"Error in chunk summarization: {str(e)}", exc_info=True)
            return "", 0.0, 0.0
    
    def _create_final_summary(self, chunk_summaries: List[str]) -> tuple[str, float, float]:
        if not chunk_summaries:
            logger.warning("Empty chunk summaries provided")
            return "", 0.0, 0.0
            
        try:
            logger.debug(f"Creating final summary from {len(chunk_summaries)} chunk summaries")
            combined_summary = " ".join(chunk_summaries)
            return self._summarize_chunk(combined_summary)
        except Exception as e:
            logger.error(f"Error creating final summary: {str(e)}", exc_info=True)
            return chunk_summaries[0] if chunk_summaries else "", 0.0, 0.0

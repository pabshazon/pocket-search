import time

from src.config.models_config import ModelsConfig
from src.domain.on_metal.nlp.chunker.text_chunker import TextChunker

from src.domain.on_metal.logger import get_logger
logger = get_logger(__name__)

MAP_PROMPT = """Write a concise summary of the following text:
{text}

CONCISE SUMMARY:"""

REDUCE_PROMPT = """Write a concise summary of the following summaries:
{text}

CONCISE SUMMARY:"""

# class TextSummarizerInterface(ABC):
#     @abstractmethod
#     async def summarize(self, text: str) -> str:
#         pass
#
#     @abstractmethod
#     async def summarize_map_reduce(self, text: str) -> str:
#         pass

class TextSummarizer():
    def __init__(self):
        try:
            logger.debug(f"> Initializing PdfSummarizer")
            self.model_config       = ModelsConfig.SUMMARIZER
            self.model              = self.model_config.model
            self.tokenizer          = self.model_config.tokenizer
            self.device             = self.model_config.device
            self.max_chunk_length   = self.model_config.max_tokens_input_length

        except Exception as e:
            logger.error(f"Failed to initialize PdfSummarizer: {str(e)}", exc_info=True)
            raise

    async def summarize_with_seq_to_seq(self, text_content: str, min_num_of_chunks: int = 1) -> str:
        if not text_content:
            logger.warning("Empty text to summarize provided")
            return ""

        try:
            chunks = TextChunker.token_chunks_that_fit_in_memory(
                full_text=text_content,
                tokenizer=self.tokenizer,
                ensure_free_kbs=5000,
                min_num_of_chunks=1
            )

            logger.info(f"Got {len(chunks)} chunks")
            chunk_summaries = [self.summarize_chunk(chunk) for chunk in chunks]
            final_summary   = self.summarize_chunk(" -- ".join(chunk_summaries))

            return final_summary

        except Exception as e:
            logger.error(f"Unexpected error in summarize method: {str(e)}", exc_info=True)
            return ""

    def summarize_chunk(self, chunk: str) -> str:
        try:
            start_time = time.time()
            chunk_size = len(chunk)
            logger.info(f"Starting chunk summarization (size: {chunk_size} chars)")
            logger.info(f"Model has max_tokens_input_length of {self.model_config.max_tokens_input_length} tokens.")

            # Tokenization phase
            tok_start = time.time()
            inputs = self.tokenizer(
                chunk,
                max_length=self.model_config.max_tokens_input_length,
                truncation=True,
                padding=True,
                return_tensors="pt"
            ).to(self.device)
            tok_time = time.time() - tok_start
            num_tokens = len(inputs['input_ids'][0])
            logger.debug(f"Tokenization completed: {num_tokens} tokens in {tok_time:.2f}s")

            # Generation phase
            gen_start = time.time()
            outputs = self.model.generate(
                **inputs,
                max_length=self.model_config.max_tokens_output_length,
                min_length=self.model_config.min_tokens_output_length,
                num_return_sequences=1,
                early_stopping=True
            )
            gen_time = time.time() - gen_start
            logger.debug(f"Summary generation completed in {gen_time:.2f}s")

            # Decoding phase
            dec_start = time.time()
            summary = self.tokenizer.decode(
                outputs[0],
                skip_special_tokens=True,
                clean_up_tokenization_spaces=True
            )
            dec_time = time.time() - dec_start
            
            # Final stats
            total_time = time.time() - start_time
            summary_size = len(summary)
            compression_ratio = (chunk_size - summary_size) / chunk_size * 100
            
            logger.info(f"Chunk summarized: {chunk_size:,} chars → {summary_size:,} chars >> {compression_ratio:.1f}% reduction) in {total_time:.2f}s >> Times: tokenize={tok_time:.2f}s, generate={gen_time:.2f}s, decode={dec_time:.2f}s")
            
            return summary.strip()
            
        except Exception as e:
            logger.error(f"Error summarizing chunk: {str(e)}")
            return ""




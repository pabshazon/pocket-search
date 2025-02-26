# from typing import List
#
# import torch
# import time
#
# from src.config.models_config import ModelsConfig
# from src.domain.on_metal.nlp.chunker.text_chunker import TextChunker
#
# import logging
#
# logging.basicConfig(
#     level=logging.INFO,  # @todo abstract from env variable
#     format='%(message)s'
# )
# logger = logging.getLogger(__name__)
#
#
# class TextSummarizer:
#     def __init__(self):
#         try:
#             logger.debug(f"> Initializing PdfSummarizer")
#             self.config             = ModelsConfig.SUMMARIZER
#             self.model              = self.config.model
#             self.tokenizer          = self.config.tokenizer
#             self.device             = self.config.device
#             self.max_chunk_length   = self.config.max_length
#             self.max_summary_length = 250
#         except Exception as e:
#             logger.error(f"Failed to initialize PdfSummarizer: {str(e)}", exc_info=True)
#             raise
#
#     def summarize(self, text_content: str, min_num_of_chunks: int = 1) -> str:
#         if not text_content:
#             logger.warning("Empty text to summarize provided")
#             return ""
#
#         try:
#             num_chunks = TextChunker.token_chunks_that_fit_in_memory(
#                 full_text           = text_content,
#                 tokenizer           = self.tokenizer,
#                 ensure_free_kbs     = 5000,
#                 min_num_of_chunks   = 1
#             )
#
#             start_summarization_time                      = time.time()
#             final_summary, final_tok_time, final_gen_time = self._create_final_summary(macro_chunks_summaries)
#             total_summarization_time                      = time.time() - start_summarization_time
#
#             logger.debug(f"- Summarization time: {total_summarization_time:.2f}s")
#             logger.debug(f"- Final summary: {final_summary}")
#
#             return final_summary
#
#         except Exception as e:
#             logger.error(f"Unexpected error in summarize method: {str(e)}", exc_info=True)
#             return ""
#
#     def _summarize_chunk(self, text: str) -> tuple[str, float, float]:
#         if not isinstance(text, str):
#             logger.error(f"Invalid input type for summarization: {type(text)}")
#             return "", 0.0, 0.0
#
#         if not text.strip():
#             logger.warning("Empty text provided for summarization")
#             return "", 0.0, 0.0
#
#         try:
#             tok_start = time.time()
#             inputs = self.tokenizer(
#                 text,
#                 max_length=self.max_chunk_length,
#                 truncation=True,
#                 return_tensors="pt"
#             ).to(self.device)
#             tokenization_time = time.time() - tok_start
#
#             try:
#                 gen_start = time.time()
#                 with torch.no_grad():
#                     summary_ids = self.model.generate(
#                         inputs["input_ids"],
#                         max_length=self.max_summary_length,
#                         num_beams=4,
#                         length_penalty=2.0,
#                         early_stopping=True,
#                         no_repeat_ngram_size=3
#                     )
#                 generation_time = time.time() - gen_start
#
#                 summary = self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)
#                 if not summary.strip():
#                     logger.warning("Generated empty summary")
#                     return "", tokenization_time, generation_time
#
#                 logger.debug(
#                     f"Chunk processing times - Tokenization: {tokenization_time:.2f}s, Generation: {generation_time:.2f}s")
#                 return summary, tokenization_time, generation_time
#
#             except torch.cuda.OutOfMemoryError as e:
#                 logger.error("CUDA out of memory error", exc_info=True)
#                 torch.cuda.empty_cache()
#                 return text[:self.max_summary_length], 0.0, 0.0  # Fallback
#
#             except Exception as e:
#                 logger.error(f"Error in model generation: {str(e)}", exc_info=True)
#                 return "", tokenization_time, 0.0
#
#         except Exception as e:
#             logger.error(f"Error in chunk summarization: {str(e)}", exc_info=True)
#             return "", 0.0, 0.0
#
#     def _create_final_summary(self, chunk_summaries: List[str]) -> tuple[str, float, float]:
#         if not chunk_summaries:
#             logger.warning("Empty chunk summaries provided")
#             return "", 0.0, 0.0
#
#         try:
#             logger.debug(f"Creating final summary from {len(chunk_summaries)} chunk summaries")
#             combined_summary = " ".join(chunk_summaries)
#             return self._summarize_chunk(combined_summary)
#         except Exception as e:
#             logger.error(f"Error creating final summary: {str(e)}", exc_info=True)
#             return chunk_summaries[0] if chunk_summaries else "", 0.0, 0.0

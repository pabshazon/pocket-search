import logging
from typing import List
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch
from src.domain.on_metal.tasks.pdf.analyzers.semantic_analyzer import SemanticChunk
from src.config.models_config import ModelsConfig
from src.config.device_config import DeviceConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PdfSummarizer:
    def __init__(self):
        try:
            logger.info(f"Initializing PdfSummarizer")
            config = ModelsConfig.SUMMARIZER
            self.device = DeviceConfig.get_device(config.device_priority)
            self.model_name = config.name
            
            try:
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name).to(self.device)
            except Exception as e:
                logger.error(f"Failed to load model or tokenizer: {str(e)}", exc_info=True)
                raise RuntimeError(f"Model initialization failed: {str(e)}")
                
            self.max_chunk_length = config.max_length
            self.max_summary_length = 150
            logger.info(f"PdfSummarizer initialized successfully on device: {self.device}")
        except Exception as e:
            logger.error(f"Failed to initialize PdfSummarizer: {str(e)}", exc_info=True)
            raise

    def summarize(self, semantic_chunks: List[SemanticChunk]) -> str:
        if not semantic_chunks:
            logger.warning("Empty semantic chunks provided")
            return ""
            
        try:
            logger.info(f"Starting summarization of {len(semantic_chunks)} semantic chunks")
            chunk_summaries = []
            
            for i, chunk in enumerate(semantic_chunks, 1):
                # Convert dict to SemanticChunk if necessary
                if isinstance(chunk, dict):
                    try:
                        # Provide default values for required fields if missing
                        default_values = {
                            'confidence': 1.0,
                            'page_num': 1,
                            'bbox': [0, 0, 0, 0],
                            'relationships': [],
                            'content': '',
                            'chunk_type': 'paragraph'
                        }
                        # Merge defaults with provided data
                        chunk_data = {**default_values, **chunk}
                        # Filter out unexpected arguments
                        valid_chunk_data = {
                            k: v for k, v in chunk_data.items() 
                            if k in SemanticChunk.__annotations__
                        }
                        chunk = SemanticChunk(**valid_chunk_data)
                    except Exception as e:
                        logger.error(f"Failed to convert dict to SemanticChunk at index {i}: {str(e)}")
                        continue

                if not isinstance(chunk, SemanticChunk):
                    logger.error(f"Invalid chunk type at index {i}: {type(chunk)}")
                    continue
                    
                if chunk.chunk_type in ["paragraph", "heading"]:
                    try:
                        logger.debug(f"Processing chunk {i}/{len(semantic_chunks)} of type: {chunk.chunk_type}")
                        summary = self._summarize_chunk(chunk.content)
                        if summary:
                            chunk_summaries.append(summary)
                    except Exception as e:
                        logger.error(f"Error processing chunk {i}: {str(e)}", exc_info=True)
                        continue
            
            if chunk_summaries:
                logger.info(f"Generated {len(chunk_summaries)} chunk summaries, creating final summary")
                try:
                    final_summary = self._create_final_summary(chunk_summaries)
                    logger.info("Final summary generated successfully")
                    return final_summary
                except Exception as e:
                    logger.error(f"Failed to create final summary: {str(e)}", exc_info=True)
                    return " ".join(chunk_summaries[:3])  # Fallback: return first 3 chunk summaries
            
            logger.warning("No valid chunks to summarize, returning empty string")
            return ""
            
        except Exception as e:
            logger.error(f"Unexpected error in summarize method: {str(e)}", exc_info=True)
            return ""
    
    def _summarize_chunk(self, text: str) -> str:
        if not isinstance(text, str):
            logger.error(f"Invalid input type for summarization: {type(text)}")
            return ""
            
        if not text.strip():
            logger.warning("Empty text provided for summarization")
            return ""
            
        try:
            logger.debug(f"Summarizing chunk of length: {len(text)} characters")
            inputs = self.tokenizer(
                text,
                max_length=self.max_chunk_length,
                truncation=True,
                return_tensors="pt"
            ).to(self.device)
            
            try:
                with torch.no_grad():
                    summary_ids = self.model.generate(
                        inputs["input_ids"],
                        max_length=self.max_summary_length,
                        num_beams=4,
                        length_penalty=2.0,
                        early_stopping=True,
                        no_repeat_ngram_size=3
                    )
                
                summary = self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)
                if not summary.strip():
                    logger.warning("Generated empty summary")
                    return ""
                    
                logger.debug(f"Successfully generated summary of length: {len(summary)} characters")
                return summary
                
            except torch.cuda.OutOfMemoryError as e:
                logger.error("CUDA out of memory error", exc_info=True)
                torch.cuda.empty_cache()
                return text[:self.max_summary_length]  # Fallback: return truncated original text
                
            except Exception as e:
                logger.error(f"Error in model generation: {str(e)}", exc_info=True)
                return ""
                
        except Exception as e:
            logger.error(f"Error in chunk summarization: {str(e)}", exc_info=True)
            return ""
    
    def _create_final_summary(self, chunk_summaries: List[str]) -> str:
        if not chunk_summaries:
            logger.warning("Empty chunk summaries provided")
            return ""
            
        try:
            logger.debug(f"Creating final summary from {len(chunk_summaries)} chunk summaries")
            combined_summary = " ".join(chunk_summaries)
            return self._summarize_chunk(combined_summary)
        except Exception as e:
            logger.error(f"Error creating final summary: {str(e)}", exc_info=True)
            return chunk_summaries[0] if chunk_summaries else ""  # Fallback: return first chunk summary

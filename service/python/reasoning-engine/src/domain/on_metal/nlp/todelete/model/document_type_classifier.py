# from typing import Tuple
# import logging
# import torch
#
# from src.config.models_config import ModelsConfig
# from src.config.document_types_config import DocumentTypesConfig
# from src.domain.on_metal.context.vram_memory import VRamMemory
#
# logger = logging.getLogger(__name__)
#
# class DocumentTypeClassifier:
#     TYPE_PROMPT     = DocumentTypesConfig.TYPE_PROMPT
#     SUBTYPES_MAP    = DocumentTypesConfig.SUBTYPES_MAP
#     SUBTYPE_PROMPT  = DocumentTypesConfig.SUBTYPE_PROMPT
#
#     def __init__(self):
#         try:
#             self.llm_config = ModelsConfig.LLM_OLLAMA
#             self.ll_model   = self.llm_config.model
#
#         except Exception as e:
#             logger.error(f"Failed to initialize document classifier: {str(e)}")
#             raise
#
#     def classify(self, text: str) -> tuple[str, str]:
#         if not text:
#             logger.warning("Empty text content provided for classification.")
#             return "no_text", "no_text"
#
#         try:
#             text_chunks = TextChunker.chunk_to_fit_in_memory(text)
#
#
#
#
#         except Exception e:
#             logger.error(f"Error during document classification: {str(e)}")
#             logger.error(f"Text tried to cllasify: {text}")
#             return "error", "error"
#
#
#
#     def classify(self, text_content: str) -> Tuple[str, str]:
#
#         try:
#             doc_types_config = DocumentTypesConfig()
#
#             safe_text = self._get_safe_text_for_context_size(text_content)
#
#             type_task_prompt = doc_types_config.get_type_prompt(safe_text)
#             classification_type = self._classify_with_llm(type_task_prompt)
#             logger.info(f">> Document type classification: {classification_type}")
#
#             if classification_type not in self.SUBTYPES_MAP:
#                 logger.info(f">> Not part of: {self.SUBTYPES_MAP}")
#                 # @todo: decide what we do here @lab; for now we continue
#
#             subtype_task_prompt = doc_types_config.get_subtype_prompt(
#                 document_text=safe_text,
#                 doc_type=classification_type
#             )
#             classification_subtype = self._classify_with_llm(subtype_task_prompt)
#             logger.info(f">> Classified document as {classification_type}/{classification_subtype}")
#             return classification_type, classification_subtype
#
#         except Exception as e:
#             logger.error(f"Error during document classification: {str(e)}")
#             return "unknown", "unknown"
#
#     def _classify_with_llm(self, prompt: str) -> str:
#         """Use LLM to classify based on prompt."""
#         try:
#             # Simplified to only use Ollama service
#             response = self.model.generate(
#                 prompt=prompt,
#                 temperature=0.7
#             )
#             clean_response = response.strip().lower()
#
#             logger.info(f"**LLM** Raw Response: {clean_response}")
#             classification = clean_response.split()[0] if clean_response else "unknown"
#             logger.info(f"**LLM** Classification: {classification}")
#             return classification
#
#         except Exception as e:
#             logger.error(f"Error in LLM classification: {str(e)}")
#             return "unknown"
#
#     def _get_safe_text_for_context_size(self, text: str) -> str:
#         """
#         Returns a safe version of the text limited to a maximum character length
#         based on the LLM configuration. Uses ContextEstimator if available to determine
#         a more fine-grained context window size.
#         """
#         try:
#             from src.domain.on_metal.nlp.model.context_estimator import ContextEstimator
#             context_estimator = ContextEstimator()
#             model_contexts = context_estimator.estimate_model_contexts()
#             # Optionally, if your LLM configuration can be mapped to one of the keys in model_contexts,
#             # you could refine the safe context length using the estimated "approx_characters".
#             # For now, this block shows how you might leverage that information.
#         except Exception as e:
#             logger.warning(f"Context estimation failed: {str(e)}. Falling back to default safe length.")
#
#         # Default approach: assume ~4 characters per token.
#         safe_max_chars = self.llm_config.max_length * 4
#
#         if len(text) <= safe_max_chars:
#             return text
#
#         safe_text = text[:safe_max_chars]
#         # Trim further to the last complete word (if possible) to avoid cutting words in half.
#         last_space = safe_text.rfind(" ")
#         if last_space != -1:
#             safe_text = safe_text[:last_space]
#
#         logger.info(f"Truncated text to {len(safe_text)} characters from original {len(text)} characters.")
#         return safe_text

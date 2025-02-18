from typing import Tuple
import logging
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

from src.config.models_config import ModelsConfig
from src.config.device_config import DeviceConfig

class DocumentTypeClassifier:
    """Classifies PDF documents into types and subtypes based on their content."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        try:
            # Initialize type classifier
            self.type_config = ModelsConfig.CLASSIFIER_DOC_TYPE
            self.type_model = self.type_config.model
            self.type_tokenizer = self.type_config.tokenizer
            
            # Initialize subtype classifier
            self.subtype_config = ModelsConfig.CLASSIFIER_DOC_SUBTYPE
            self.subtype_model = self.subtype_config.model
            self.subtype_tokenizer = self.subtype_config.tokenizer
            
            # Both models should use the same device
            self.device = self.type_config.device
            
        except Exception as e:
            self.logger.error(f"Failed to initialize document classifier: {str(e)}")
            raise
    
    def classify(self, text_content: str) -> Tuple[str, str]:
        if not text_content:
            self.logger.warning("Empty text content provided for classification")
            return "unknown", "unknown"
            
        try:
            inputs = self.type_tokenizer(
                text_content,
                truncation=True,
                max_length=512,
                return_tensors="pt"
            ).to(self.device)
            
            with torch.no_grad():
                outputs = self.type_model(**inputs)
                predictions = outputs.logits
                
            doc_type = self._get_document_type(predictions)
            doc_subtype = self._get_document_subtype(predictions, doc_type)
            
            self.logger.info(f"Classified document as {doc_type}/{doc_subtype}")
            return doc_type, doc_subtype
            
        except Exception as e:
            self.logger.error(f"Error during document classification: {str(e)}")
            return "unknown", "unknown"
    
    def _get_document_type(self, predictions) -> str:
        """Maps model predictions to document types."""
        try:
            predicted_class = torch.argmax(predictions).item()
            document_types = { 
                0: "research",
                1: "legal",
                2: "finance",
                3: "hr"
            }
            return document_types.get(predicted_class, "unknown")
        except Exception as e:
            self.logger.error(f"Error determining document type: {str(e)}")
            return "unknown"
    
    def _get_document_subtype(self, predictions, doc_type: str) -> str:
        """Determines document subtype based on type and model predictions."""
        subtypes = {
             "research": {
                0: "research_paper",
                1: "research_proposal",
                2: "research_review",
                3: "research_benchmark_tests",
                4: "other"
            },
            "legal": {
                0: "nda",
                1: "employee_contract",
                2: "compliance_guideline",
                3: "company_bylaws",
                4: "company_incorporation",
                5: "litigation",
                6: "patent",
                7: "other"
            },
            "finance": {
                0: "bank_document",
                1: "financial_statement",
                2: "financial_report",
                3: "financial_analysis",
                4: "financial_forecast",
                5: "financial_report",
                6: "other"
            },
            "hr": {
                0: "cv",
                1: "cover_letter",
                2: "job_application",
                3: "job_interview_guidelines",
                4: "job_offer",
                5: "job_post",
                6: "other"
            }
        }
        
        try:
            probs         = torch.softmax(predictions, dim=1)[0]
            subtype_class = torch.argmax(probs).item() % len(subtypes.get(doc_type, {}))
            
            type_subtypes = subtypes.get(doc_type, {})
            if not type_subtypes:
                return "unknown"
                
            return list(type_subtypes.values())[subtype_class]
        except Exception as e:
            self.logger.error(f"Error determining document subtype: {str(e)}")
            return "unknown"

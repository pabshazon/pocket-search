from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import torch
from transformers import (
    AutoModel,
    AutoTokenizer, 
    AutoModelForSeq2SeqLM,
    AutoModelForSequenceClassification,
    AutoModelForMaskedLM,
    ViltProcessor,
    ViltForQuestionAnswering,
    LayoutLMv3ForSequenceClassification,
    RobertaForSequenceClassification,
    AutoModelForCausalLM,
    AutoConfig,
    utils
)
import logging
import os
from pathlib import Path

# HuggingFace offline config
os.environ['HF_DATASETS_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
utils.logging.set_verbosity_error()  # Reduce logging noise

from .device_config import DeviceConfig

logger = logging.getLogger(__name__)

@dataclass
class ModelConfig:
    name: str
    max_length: int
    device_priority: list[str]      = field(default_factory=lambda: [ "mps", "cuda", "cpu"])
    model_params: Dict[str, Any]    = field(default_factory=dict)
    model_class: Optional[Any]      = None
    _model: Optional[Any]           = field(default=None, init=False, repr=False)
    _tokenizer: Optional[Any]       = field(default=None, init=False, repr=False)
    _device: Optional[torch.device] = field(default=None, init=False, repr=False)
    _is_initialized: bool = field(default=False, init=False)

    def __post_init__(self):
        if self.model_params is None:
            self.model_params = {}
    
    @property
    def local_path(self) -> Path:
        base_path = Path(os.getenv('POCKET_GITHUB_PATH', '').rstrip('/')) / 'service' / 'python' / 'reasoning-engine' / 'models'
        model_path = base_path / self.name.replace("/", "--")
        logger.debug(f"Checking model path: {model_path}, exists: {model_path.exists()}")
        return model_path

    def download_model(self):
        """Download model and tokenizer to local storage"""
        logger.info(f"Checking model {self.name} at path {self.local_path}")
        if not self.local_path.exists():
            logger.info(f"Downloading model {self.name} to {self.local_path}")
            try:
                self.local_path.mkdir(parents=True, exist_ok=True)
                
                # Temporarily disable offline mode for download
                original_transformers = os.environ.get('TRANSFORMERS_OFFLINE')
                original_hf = os.environ.get('HF_DATASETS_OFFLINE')
                
                os.environ['TRANSFORMERS_OFFLINE'] = '0'
                os.environ['HF_DATASETS_OFFLINE'] = '0'
                
                try:
                    # First create the configuration with our parameters
                    config = AutoConfig.from_pretrained(
                        self.name,
                        **self.model_params
                    )
                    
                    # Download tokenizer and model
                    logger.info(f"Downloading tokenizer for {self.name}")
                    tokenizer = AutoTokenizer.from_pretrained(self.name)
                    
                    model_class = self.model_class or AutoModel
                    logger.info(f"Downloading model {self.name} using class {model_class.__name__}")
                    model = model_class.from_pretrained(
                        self.name,
                        config=config,
                        ignore_mismatched_sizes=True  # Added this parameter
                    )
                    
                    # Save everything to local storage
                    logger.info(f"Saving tokenizer, config and model to {self.local_path}")
                    config.save_pretrained(str(self.local_path))
                    tokenizer.save_pretrained(str(self.local_path))
                    model.save_pretrained(str(self.local_path))
                    
                finally:
                    # Restore original offline settings
                    if original_transformers is not None:
                        os.environ['TRANSFORMERS_OFFLINE'] = original_transformers
                    if original_hf is not None:
                        os.environ['HF_DATASETS_OFFLINE'] = original_hf
                
                logger.info(f"Successfully downloaded model {self.name}")
            except Exception as e:
                logger.error(f"Failed to download model {self.name}: {str(e)}")
                raise
        else:
            logger.info(f"Model {self.name} already exists at {self.local_path}")

    @property
    def device(self) -> torch.device:
        if self._device is None:
            self._device = DeviceConfig.get_device(self.device_priority)
        return self._device

    @property
    def tokenizer(self):
        if self._tokenizer is None:
            try:
                logger.info(f"Loading tokenizer from local path: {self.local_path}")
                if not self.local_path.exists():
                    raise ValueError(f"Model path does not exist: {self.local_path}. Please run download_all_models() first.")
                self._tokenizer = AutoTokenizer.from_pretrained(
                    str(self.local_path),
                    local_files_only=True,
                    trust_remote_code=False  # Added to prevent remote code execution
                )
            except Exception as e:
                logger.error(f"Failed to load tokenizer for {self.name} from {self.local_path}: {str(e)}")
                raise
        return self._tokenizer

    @property
    def model(self):
        if self._model is None:
            try:
                logger.info(f"Loading model from local path: {self.local_path}")
                if not self.local_path.exists():
                    raise ValueError(f"Model path does not exist: {self.local_path}. Please run download_all_models() first.")
                
                # First create the configuration with our parameters
                config = AutoConfig.from_pretrained(
                    str(self.local_path),
                    local_files_only=True,
                    trust_remote_code=False,
                    **self.model_params
                )
                
                # Then initialize the model with this config
                model_class = self.model_class or AutoModel
                self._model = model_class.from_pretrained(
                    str(self.local_path),
                    config=config,
                    local_files_only=True,
                    trust_remote_code=False,
                    ignore_mismatched_sizes=True  # Added this parameter
                ).to(self.device)
                
                # Configure generation parameters if they exist
                if hasattr(self._model, 'generation_config'):
                    for key, value in self.model_params.items():
                        if hasattr(self._model.generation_config, key):
                            setattr(self._model.generation_config, key, value)
                
            except Exception as e:
                logger.error(f"Failed to load model {self.name} from {self.local_path}: {str(e)}")
                raise
        return self._model

class ModelsConfig:
    _instance = None
    _is_initialized = False

    @classmethod
    def download_all_models(cls):
        """Download all models to local storage"""
        logger.info("Starting download of all models")
        try:
            cls.SUMMARIZER.download_model()
            cls.LAYOUT.download_model()
            cls.CODE.download_model()
            cls.VISION.download_model()
            cls.LLM.download_model()
            cls.CLASSIFIER_DOC_TYPE.download_model()
            cls.CLASSIFIER_DOC_SUBTYPE.download_model()
            cls.CLASSIFIER_LEGAL.download_model()
            
            logger.info("Successfully downloaded all models")
        except Exception as e:
            logger.error(f"Failed to download models: {str(e)}")
            raise

    SUMMARIZER = ModelConfig(
        name="facebook/bart-large-cnn",
        max_length=1024,
        model_class=AutoModelForSeq2SeqLM,
        device_priority=["mps", "cuda", "cpu"],
        model_params={
            "forced_bos_token_id": 0,
            "forced_eos_token_id": 2,
            "decoder_start_token_id": 2,
            "eos_token_id": 2,
            "pad_token_id": 1,
            "bos_token_id": 0,
            "num_beams": 4,
            "length_penalty": 2.0,
            "early_stopping": True,
            "no_repeat_ngram_size": 3,
            "max_length": 142,
            "min_length": 56,
            "max_new_tokens": 1024,
            "do_sample": False
        }
    )
        
    # Summarization Models
    # SUMMARIZER = ModelConfig(
    #     name="google/long-t5-tglobal-base",
    #     max_length=16384,
    #     device_priority=["mps", "cuda", "cpu"],  # Added MPS as first priority.
    #     model_params={
    #         "num_beams": 4,
    #         "length_penalty": 1.0,
    #         "early_stopping": True,
    #         "no_repeat_ngram_size": 3,
    #         "do_sample": False,
    #         "min_length": 50,
    #         "max_new_tokens": 1024,
    #         "padding": True,
    #         "truncation": True
    #     }
    # )

    # Document Layout Analysis
    LAYOUT = ModelConfig(
        name="microsoft/layoutlmv3-base",
        max_length=512,
        model_class=LayoutLMv3ForSequenceClassification,
        model_params={
            "padding": True,
            "truncation": True
        }
    )

    # Code Analysis
    CODE = ModelConfig(
        name="microsoft/codebert-base",
        max_length=512,
        model_class=RobertaForSequenceClassification,
        model_params={
            "padding": True,
            "truncation": True
        }
    )

    # Visual Language Model
    VISION = ModelConfig(
        name="dandelin/vilt-b32-finetuned-vqa",
        max_length=512,
        model_class=ViltForQuestionAnswering,
        model_params={
            "padding": True,
            "return_tensors": "pt"
        }
    )

    # Large Language Model Decoder
    LLM = ModelConfig(
        name="TinyLlama/TinyLlama-1.1B-Chat-v1.0",  # Much smaller Llama-based model
        max_length=2048,
        model_class=AutoModelForCausalLM,
        model_params={
            "padding": True,
            "return_tensors": "pt",
            "trust_remote_code": True,
            "use_cache": True
        }
    )

    # Document Type Classifier
    CLASSIFIER_DOC_TYPE = ModelConfig(
        name="allenai/longformer-base-4096",
        max_length=4096,
        model_class=AutoModelForSequenceClassification,
        model_params={
            "num_labels": 4,  # research, legal, finance, hr
            "problem_type": "single_label_classification",
            "id2label": {
                0: "research",
                1: "legal",
                2: "finance",
                3: "hr"
            },
            "label2id": {
                "research": 0,
                "legal": 1,
                "finance": 2,
                "hr": 3
            }
        }
    )

    # Document Subtype Classifier
    CLASSIFIER_DOC_SUBTYPE = ModelConfig(
        name="allenai/longformer-base-4096",
        max_length=4096,
        model_class=AutoModelForSequenceClassification,
        model_params={
            "num_labels": 8,  # Maximum number of subtypes across all categories
            "problem_type": "single_label_classification",
            "id2label": {
                0: "research_paper",
                1: "nda",
                2: "bank_document",
                3: "cv",
                4: "research_proposal",
                5: "employee_contract",
                6: "financial_statement",
                7: "cover_letter"
            },
            "label2id": {
                "research_paper": 0,
                "nda": 1,
                "bank_document": 2,
                "cv": 3,
                "research_proposal": 4,
                "employee_contract": 5,
                "financial_statement": 6,
                "cover_letter": 7
            }
        }
    )

    # Legal Document Classifier
    CLASSIFIER_LEGAL = ModelConfig(
        name="nlpaueb/legal-bert-base-uncased",  # Legal domain-specific BERT
        max_length=512,  # Standard BERT max length
        model_class=AutoModelForSequenceClassification,
        model_params={
            "padding": True,
            "truncation": True,
            "return_tensors": "pt"
        }
    )

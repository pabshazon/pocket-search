import string
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

import os
from pathlib import Path
from src.config.document_types_config import DocumentTypesConfig
from src.service.ollama import OllamaService
# HuggingFace offline config
os.environ['HF_DATASETS_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
utils.logging.set_verbosity_error()  # Reduce logging noise

from src.domain.on_metal.logger         import get_logger
logger = get_logger(__name__)
from .device_config import DeviceConfig


@dataclass
class ModelConfig:
    name: str
    # Input/Output constraints (all in tokens unless specified otherwise)
    max_tokens_input_length: int    = field(default=None)
    max_tokens_output_length: int   = field(default=None)
    min_tokens_output_length: int   = field(default=None)
    device_priority: list[str]      = field(default_factory=lambda: ["mps", "cuda", "cpu"])
    model_params: Dict[str, Any]    = field(default_factory=dict)
    model_class: Optional[Any]      = None
    _model: Optional[Any]           = field(default=None, init=False, repr=False)
    _tokenizer: Optional[Any]       = field(default=None, init=False, repr=False)
    _device: Optional[torch.device] = field(default=None, init=False, repr=False)
    _is_initialized: bool           = field(default=False, init=False)

    def __post_init__(self):
        if self.model_params is None:
            self.model_params = {}
    
    @property
    def local_path(self, name: string = None) -> Path:
        base_path = Path(os.getenv('POCKET_GITHUB_PATH', '').rstrip('/')) / 'service' / 'python' / 'reasoning-engine' / 'models'
        if name is None:
            model_path = base_path / self.name.replace("/", "--")
        else:
            model_path = base_path / name.replace("/", "--")
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
                
                # Set up authentication token for accessing gated repositories.
                # If the environment variable HUGGINGFACE_TOKEN is not set, use True to rely on local credentials.
                auth_token = os.getenv("HUGGINGFACE_TOKEN") or True

                try:
                    # First create the configuration with our parameters
                    config = AutoConfig.from_pretrained(
                        self.name,
                        use_auth_token=auth_token,
                        **self.model_params
                    )
                    
                    # Download tokenizer and model
                    logger.info(f"Downloading tokenizer for {self.name}")
                    tokenizer = AutoTokenizer.from_pretrained(self.name, use_auth_token=auth_token)
                    
                    model_class = self.model_class or AutoModel
                    logger.info(f"Downloading model {self.name} using class {model_class.__name__}")
                    model = model_class.from_pretrained(
                        self.name,
                        config=config,
                        ignore_mismatched_sizes=True,
                        use_auth_token=auth_token
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
                raise ValueError(f"Error: {str(e)}")
        return self._tokenizer

    @property
    def model(self):
        if self._model is None:
            try:
                # Special handling for Ollama models
                if self.name.startswith("ollama://"):
                    logger.info(f"Initializing Ollama model: {self.name}")
                    self._model = self.model_class.from_pretrained(
                        self.name,
                        **self.model_params
                    )
                    return self._model

                # Regular HuggingFace model loading
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
                    ignore_mismatched_sizes=True
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
            cls.LLM.download_model()
            # cls.CLASSIFIER_DOC_TYPE.download_model()
            # cls.CLASSIFIER_DOC_SUBTYPE.download_model()
            # cls.CLASSIFIER_LEGAL.download_model()
            # cls.LAYOUT.download_model()
            # cls.CODE.download_model()
            # cls.VISION.download_model()
            
            logger.info("Successfully downloaded all models")
        except Exception as e:
            logger.error(f"Failed to download models: {str(e)}")
            raise

    def _build_doc_type_params():
        """Build model parameters for document type classifier from DocumentTypesConfig"""
        # Extract unique document types from TYPE_PROMPT
        doc_types = [t.strip() for t in DocumentTypesConfig.TYPE_PROMPT.split(':')[1].split('Document')[0].strip().split(',')]
        doc_types = [t.strip() for t in doc_types[0].split('or')]  # Handle the "or other" part
        doc_types = [t.strip() for t in ' '.join(doc_types).split()]  # Clean up and split
        doc_types.append('unknown')  # Add unknown type
        
        return {
            "num_labels": len(doc_types),
            "problem_type": "single_label_classification",
            "id2label": {i: label for i, label in enumerate(doc_types)},
            "label2id": {label: i for i, label in enumerate(doc_types)}
        }

    def _build_doc_subtype_params():
        """Build model parameters for document subtype classifier from DocumentTypesConfig"""
        # Collect all unique subtypes
        all_subtypes = set()
        for subtypes in DocumentTypesConfig.SUBTYPES_MAP.values():
            all_subtypes.update(subtypes)
        all_subtypes.add('unknown')
        
        # Convert to sorted list for consistent indexing
        subtypes_list = sorted(all_subtypes)
        
        return {
            "num_labels": len(subtypes_list),
            "problem_type": "single_label_classification",
            "id2label": {i: label for i, label in enumerate(subtypes_list)},
            "label2id": {label: i for i, label in enumerate(subtypes_list)}
        }

    # SUMMARIZER = ModelConfig(
    #     name="ibm-granite/granite-3.1-8b-instruct",
    #     max_length=128000,
    #     model_class=AutoModelForCausalLM,
    #     device_priority=["cuda", "cpu"],
    #     model_params={
    #         # Basic model loading parameters
    #         "torch_dtype": "bfloat16",
    #         "low_cpu_mem_usage": True,
    #         "device_map": "auto",
    #
    #         # Generation configuration
    #         "generation_config": {
    #             "max_length": 128000,
    #             "min_length": 100,
    #             "length_penalty": 1.2,
    #             "max_new_tokens": 1024,
    #             "temperature": 0.7,
    #             "top_p": 0.9,
    #             "do_sample": True,
    #             "num_beams": 4,
    #             "early_stopping": True,
    #             "no_repeat_ngram_size": 3
    #         }
    #     }
    # )
    SUMMARIZER = ModelConfig(
        name="facebook/bart-large-cnn",
        max_tokens_input_length=1024,
        max_tokens_output_length=142,
        min_tokens_output_length=56,
        model_class=AutoModelForSeq2SeqLM,
        device_priority=["mps", "cuda", "cpu"],
        model_params={
            "max_length": 142,
            "min_length": 56,
            "do_sample": False
        }
    )


    # SUMMARIZER = ModelConfig(
    #     name="facebook/bart-large-cnn",
    #     max_tokens_input_length=1024,
    #     max_tokens_output_length=142,
    #     min_tokens_output_length=56,
    #     model_class=AutoModelForSeq2SeqLM,
    #     device_priority=["mps", "cuda", "cpu"],
    #     model_params={
    #         # Model configuration parameters
    #         "architectures": ["BartForConditionalGeneration"],
    #         "pad_token_id": 1,
    #         "bos_token_id": 0,
    #         "eos_token_id": 2,
    #         "decoder_start_token_id": 2,
    #         "forced_eos_token_id": 2,
    #
    #         # Generation configuration parameters
    #         "max_length": 142,
    #         "min_length": 56,
    #         # "length_penalty": 2.0,
    #         "max_new_tokens": 1024,
    #         "do_sample": False
    #     }
    # )

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
        max_tokens_input_length=512,  # @todo review - placeholder
        max_tokens_output_length=142, # @todo review - placeholder
        min_tokens_output_length=56,  # @todo review - placeholder
        model_class=LayoutLMv3ForSequenceClassification,
        model_params={
            "padding": True,
            "truncation": True
        }
    )

    # Code Analysis
    CODE = ModelConfig(
        name="microsoft/codebert-base",
        max_tokens_input_length=512,  # @todo review - placeholder
        max_tokens_output_length=142,  # @todo review - placeholder
        min_tokens_output_length=56,  # @todo review - placeholder
        model_class=RobertaForSequenceClassification,
        model_params={
            "padding": True,
            "truncation": True
        }
    )

    # Visual Language Model
    VISION = ModelConfig(
        name="dandelin/vilt-b32-finetuned-vqa",
        max_tokens_input_length=512,  # @todo review - placeholder
        max_tokens_output_length=142,  # @todo review - placeholder
        min_tokens_output_length=56,  # @todo review - placeholder
        model_class=ViltForQuestionAnswering,
        model_params={
            "padding": True,
            "return_tensors": "pt"
        }
    )

    # LLM = ModelConfig(
    #     name="meta-llama/Llama-3.2-1B-Instruct",
    #     max_length=2048,
    #     model_class=AutoModelForCausalLM,
    #     model_params={
    #         "padding": True,
    #         "return_tensors": "pt",
    #         "use_cache": True
    #     }
    # )

    LLM_LLAMA = ModelConfig(
        name="meta-llama/Llama-3.2-1B-Instruct",
        max_tokens_input_length=2048,  # @todo review - placeholder
        max_tokens_output_length=142, # @todo review - placeholder
        min_tokens_output_length=56,  # @todo review - placeholder
        model_class=AutoModelForCausalLM,
        model_params={
            "padding": True,
            "return_tensors": "pt",
            "use_cache": True
        }
    )

    LLM = ModelConfig(
        name="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        max_tokens_input_length=2048,  # @todo review - placeholder
        max_tokens_output_length=142, # @todo review - placeholder
        min_tokens_output_length=56,  # @todo review - placeholder
        model_class=AutoModelForCausalLM,
        model_params={
            "padding": True,
            "return_tensors": "pt",
            "use_cache": True
        }
    )
    # Document Type Classifier
    CLASSIFIER_DOC_TYPE = ModelConfig(
        name="allenai/longformer-base-4096",
        max_tokens_input_length=4096,  # @todo review - placeholder
        max_tokens_output_length=142, # @todo review - placeholder
        min_tokens_output_length=56,  # @todo review - placeholder
        model_class=AutoModelForSequenceClassification,
        model_params=_build_doc_type_params()
    )

    # Document Subtype Classifier
    CLASSIFIER_DOC_SUBTYPE = ModelConfig(
        name="allenai/longformer-base-4096",
        max_tokens_input_length=4096,  # @todo review - placeholder
        max_tokens_output_length=142, # @todo review - placeholder
        min_tokens_output_length=56,  # @todo review - placeholder
        model_class=AutoModelForSequenceClassification,
        model_params=_build_doc_subtype_params()
    )

    # Legal Document Classifier
    CLASSIFIER_LEGAL = ModelConfig(
        name="nlpaueb/legal-bert-base-uncased",  # Legal domain-specific BERT
        max_tokens_input_length=512,  # @todo review - placeholder
        max_tokens_output_length=142, # @todo review - placeholder
        min_tokens_output_length=56,  # @todo review - placeholder        model_class=AutoModelForSequenceClassification,
        model_params={
            "padding": True,
            "truncation": True,
            "return_tensors": "pt"
        }
    )

    LLM_OLLAMA = ModelConfig(
        name="ollama://phi3:medium-128k",
        max_tokens_input_length=4096,  # @todo review - placeholder
        max_tokens_output_length=142, # @todo review - placeholder
        min_tokens_output_length=56,  # @todo review - placeholder        model_class=OllamaService,
        model_params={
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
            },
            "system_prompt": "You are a helpful AI assistant."
        }
    )

    DOCLING = ModelConfig(
        name="docling",
    )



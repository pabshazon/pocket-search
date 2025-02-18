import logging
import os
from src.config.models_config import ModelsConfig
from huggingface_hub import login

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def setup_huggingface_auth():
    """Setup Hugging Face authentication using token from environment"""
    token = os.getenv('HUGGINGFACE_TOKEN')
    if not token:
        logger.error("HUGGINGFACE_TOKEN environment variable is not set")
        raise ValueError("HUGGINGFACE_TOKEN environment variable is required")
    
    logger.info("Authenticating with Hugging Face using token...")
    login(token)
    logger.info("Successfully authenticated with Hugging Face")

def main():
    logger.info("Starting model download process")
    setup_huggingface_auth()
    ModelsConfig.download_all_models()
    logger.info("Model download process completed")

if __name__ == "__main__":
    main()

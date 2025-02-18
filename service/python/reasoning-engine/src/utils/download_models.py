import logging
from src.config.models_config import ModelsConfig

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting model download process")
    ModelsConfig.download_all_models()
    logger.info("Model download process completed")

if __name__ == "__main__":
    main()

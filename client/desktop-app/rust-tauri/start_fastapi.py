import sys
import os
import logging

# Add the src-python directory to the Python path
sys.path.append(os.path.join(os.environ['POCKET_GITHUB_PATH'] + 'service/python/reasoning-engine/'))

import uvicorn
from src.main import app

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.DEBUG)
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="debug")
    

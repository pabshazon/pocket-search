import sys
import os

# Add the src-python directory to the Python path
sys.path.append(os.path.join(os.environ['POCKET_GITHUB_PATH'] + 'service/python/reasoning-engine/'))

import uvicorn
from src.main import app

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)

# Activate the Python virtual environment
source ${POCKET_GITHUB_PATH}service/python/reasoning-engine/.venv_reasoning_engine/bin/activate

# Change directory to the desktop-app
cd ${POCKET_GITHUB_PATH}service/python/reasoning-engine/
rm -rf models
mkdir models
python3 -m src.utils.download_models

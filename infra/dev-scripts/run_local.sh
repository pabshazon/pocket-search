#!/bin/sh
echo "@todo: fix the Remember you have to manually npm install from desktop-app folder."

# Kill any process using port 8000
PORT=8000
PID=$(lsof -t -i:$PORT)
if [ -n "$PID" ]; then
  echo "Killing process $PID using port $PORT"
  kill -9 $PID
fi

# Activate the Python virtual environment
source ${POCKET_GITHUB_PATH}service/python/reasoning-engine/.venv_reasoning_engine/bin/activate

# Change directory to the desktop-app
cd ${POCKET_GITHUB_PATH}client/desktop-app

# Start the Tauri application
npx tauri dev

#!/bin/sh
echo "@todo: fix the Remember you have to manually npm install from desktop-app folder."
echo "@todo: fix the Remember you have to manually pip install -r requirements.txt from python service folder."
# Kill any process using port 8000
PORT=8000
PID=$(lsof -t -i:$PORT)
if [ -n "$PID" ]; then
  echo "Killing process $PID using port $PORT"
  kill -9 $PID
fi

# Activate the Python virtual environment
source ${POCKET_GITHUB_PATH}service/python/reasoning-engine/.venv_reasoning_engine/bin/activate

# Only perform cleaning when "clean" argument is passed
if [ "$1" = "clean" ]; then
    echo "Cleaning SQLite configuration..."
    # Make sure we don't use the system sqlite3 because it disallows extension loading, we need to compile our own sqlite.
    cd ${POCKET_GITHUB_PATH}client/desktop-app/rust-tauri
    export LIBSQLITE3_SYS_USE_PKG_CONFIG=0
    export SQLITE3_CFLAGS="-DSQLITE_ENABLE_LOAD_EXTENSION=1"
    cargo clean
fi

# Change directory to the desktop-app
cd ${POCKET_GITHUB_PATH}client/desktop-app

# Start the Tauri application
npx tauri dev
#!/bin/sh
echo "@todo: fix the Remember you have to manually npm install from desktop-app folder."
source ${POCKET_GITHUB_PATH}service/python/reasoning-engine/.venv_reasoning_engine/bin/activate
cd ${POCKET_GITHUB_PATH}client/desktop-app
npx tauri dev

#!/bin/bash
# First-time setup: create venv and install requirements
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
echo "Setup complete. Now run ./run.sh to start the app."

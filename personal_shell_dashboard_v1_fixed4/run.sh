#!/bin/bash
# Activate the virtual environment and start the app
source .venv/bin/activate
uvicorn backend.main:app --reload

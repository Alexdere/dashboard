# PowerShell script for Windows
# Activate venv and run the server
.\.venv\Scripts\Activate.ps1
uvicorn backend.main:app --reload

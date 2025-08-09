# PowerShell setup script for Windows
# First-time setup: create venv and install requirements
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Write-Output "Setup complete. Now run ./run.ps1 to start the app."

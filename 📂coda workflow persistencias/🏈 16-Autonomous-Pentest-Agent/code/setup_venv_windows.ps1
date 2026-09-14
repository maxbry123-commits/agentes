# Navigate to your project directory
cd "C:\Users\jackgilbert\OneDrive - Microsoft\Desktop\tools\autonomous-pentest-agent"

# Create venv (use 'python' not 'python3' on Windows)
python -m venv venv

# Activate venv (Windows PowerShell uses different activation script)
.\venv\Scripts\Activate.ps1

# If you get an execution policy error, run this first:
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Verify you're in the venv (should show venv path)
Get-Command python

# Install dependencies
pip install -r requirements.txt
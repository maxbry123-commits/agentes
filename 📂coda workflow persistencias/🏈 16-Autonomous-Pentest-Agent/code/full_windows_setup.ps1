# 1. Navigate to project
cd "C:\Users\jackgilbert\OneDrive - Microsoft\Desktop\tools\autonomous-pentest-agent"

# 2. Create and activate venv
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env from example
Copy-Item .env.example .env
# Then edit .env and add your ANTHROPIC_API_KEY
notepad .env

# 5. Run tests (should work on Windows — no Linux tools needed)
python -m pytest tests/ -v

# 6. Run dry-run (validates Claude API + logic, no tools executed)
python -m src.main --target 10.10.10.56 --machine shocker --attacker-ip 10.10.14.1 --dry-run

# 7. Initialize git and push
git init
git branch -M main
git add .
git commit -m "Initial prototype: Autonomous Pentest Agent"

# Create GitHub repo (need gh CLI installed, or do it on github.com)
gh repo create autonomous-pentest-agent --private --source=. --push
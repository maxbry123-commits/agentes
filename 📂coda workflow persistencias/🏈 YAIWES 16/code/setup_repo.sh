#!/bin/bash
# Run these commands to initialize the repository

# 1. Create project directory
mkdir autonomous-pentest-agent
cd autonomous-pentest-agent

# 2. Initialize git
git init
git branch -M main

# 3. Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# 4. Copy all the files from above into the correct paths
# (you should have already saved them)

# 5. Install dependencies
pip install -r requirements.txt

# 6. Copy .env.example to .env and add your API key
cp .env.example .env
# Edit .env with your actual ANTHROPIC_API_KEY

# 7. Run tests to verify everything imports correctly
python -m pytest tests/ -v

# 8. Create GitHub repo (private)
gh repo create autonomous-pentest-agent --private --source=. --push

# 9. Initial commit
git add .
git commit -m "Initial prototype: Autonomous Pentest Agent"
git push -u origin main
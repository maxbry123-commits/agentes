import os
import sys
import requests
import json

print("=== Minimal GitHub API Test ===")

# 1. Check if GitHub token exists
print("\n1. Checking for GitHub token...")
token = os.environ.get("GITHUB_TOKEN")

if not token:
    token_paths = [
        os.path.expanduser("~/.github_token"),
        os.path.expanduser("~/.github/token"),
        os.path.expanduser("~/.config/github/token"),
    ]

    for token_file in token_paths:
        if os.path.exists(token_file):
            try:
                with open(token_file, "r") as f:
                    token = f.read().strip()
                    if token:
                        print(f"✅ Found token in {token_file}")
                        break
            except Exception as e:
                print(f"❌ Error reading {token_file}: {e}")

if token:
    # Clean the token if it exists
    if token.lower().startswith(("bearer ", "token ")):
        token = token.split(" ", 1)[1]
    token = token.strip("\"'")
    print("✅ GitHub token is available")

    # Mask token for display
    masked_token = token[:4] + "..." + token[-4:] if len(token) > 8 else "****"
    print(f"Token (masked): {masked_token}")
else:
    print("❌ No GitHub token found")
    print("You can create a token at: https://github.com/settings/tokens")
    print("Then set it with: export GITHUB_TOKEN=your_token_here")

# 2. Test basic GitHub API connectivity
print("\n2. Testing GitHub API connectivity...")
headers = {"Accept": "application/vnd.github.v3+json"}
if token:
    headers["Authorization"] = f"Bearer {token}"

try:
    # Try to get user info if authenticated
    if token:
        user_response = requests.get("https://api.github.com/user", headers=headers)
        if user_response.status_code == 200:
            user_data = user_response.json()
            print(f"✅ Successfully authenticated as: {user_data.get('login')}")
        else:
            print(f"❌ Authentication failed: {user_response.status_code}")
            print(f"Response: {user_response.text}")

    # Try to get a public repository (should work even without auth)
    repo_response = requests.get(
        "https://api.github.com/repos/psf/requests", headers=headers
    )

    if repo_response.status_code == 200:
        repo_data = repo_response.json()
        print(f"✅ Successfully connected to GitHub API")
        print(f"Repository: {repo_data.get('full_name')}")
        print(f"Stars: {repo_data.get('stargazers_count')}")
    else:
        print(f"❌ API call failed: {repo_response.status_code}")
        print(f"Response: {repo_response.text}")

    # 3. Check rate limits
    print("\n3. Checking API rate limits...")
    rate_response = requests.get("https://api.github.com/rate_limit", headers=headers)

    if rate_response.status_code == 200:
        rate_data = rate_response.json()
        core = rate_data.get("resources", {}).get("core", {})
        search = rate_data.get("resources", {}).get("search", {})

        print(
            f"Core API: {core.get('remaining', 0)}/{core.get('limit', 0)} requests remaining"
        )
        print(
            f"Search API: {search.get('remaining', 0)}/{search.get('limit', 0)} requests remaining"
        )

        # Save rate limit info to a file for reference
        with open("github_rate_limits.json", "w") as f:
            json.dump(rate_data, f, indent=2)
        print("Rate limit details saved to github_rate_limits.json")
    else:
        print(f"❌ Failed to check rate limits: {rate_response.status_code}")

except Exception as e:
    print(f"❌ Error connecting to GitHub API: {e}")

print("\nTest completed!")

import os
import sys
import requests

# Add the current directory to the path to ensure imports work correctly
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from swebench_get_repo_copy import get_github_token, check_github_api_status


def test_github_token():
    """Test if GitHub token is available and valid."""
    print("Testing GitHub token retrieval...")

    # Get GitHub token
    github_token = get_github_token()

    if github_token:
        print("✅ GitHub token found!")

        # Setup headers with token
        headers = {"Accept": "application/vnd.github.v3+json"}
        headers["Authorization"] = f"Bearer {github_token}"

        # Test token validity with a simple API call
        response = requests.get("https://api.github.com/user", headers=headers)

        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ Token is valid! Authenticated as: {user_data.get('login')}")

            # Check API rate limits
            if check_github_api_status(headers):
                print("✅ API rate limits are sufficient for testing")
            else:
                print("⚠️ API rate limits may be too low for extensive testing")

            return True
        else:
            print(
                f"❌ Token validation failed with status code: {response.status_code}"
            )
            print(f"Response: {response.text}")
    else:
        print(
            "❌ No GitHub token found. Please set the GITHUB_TOKEN environment variable."
        )
        print("You can create a token at: https://github.com/settings/tokens")
        print("Then set it with: export GITHUB_TOKEN=your_token_here")

    return False


if __name__ == "__main__":
    print("GitHub Token Test")
    print("-----------------")
    test_github_token()

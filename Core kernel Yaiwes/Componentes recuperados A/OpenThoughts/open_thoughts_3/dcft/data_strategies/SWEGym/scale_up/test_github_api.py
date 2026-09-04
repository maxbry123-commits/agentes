#!/usr/bin/env python3
"""
Simple script to test GitHub API connectivity and token validity.
"""
import requests
import os
import sys
import json
from pathlib import Path


def get_github_token():
    """Get GitHub token from environment or file"""
    # First try environment variable
    token = os.environ.get("GITHUB_TOKEN")

    # Then try from a token file
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
                            break
                except:
                    pass

    # Clean the token if it exists
    if token:
        # Remove any "Bearer " or "token " prefix if present
        if token.lower().startswith(("bearer ", "token ")):
            token = token.split(" ", 1)[1]
        # Remove any quotes
        token = token.strip("\"'")

    return token


def test_github_api():
    """Test GitHub API connectivity and token validity"""
    token = get_github_token()

    if not token:
        print("No GitHub token found.")
        print("Would you like to enter a token now? (y/n)")
        response = input().strip().lower()
        if response == "y":
            token = input("Enter your GitHub token: ").strip()
            save = input("Save this token to ~/.github_token? (y/n): ").strip().lower()
            if save == "y":
                token_file = os.path.expanduser("~/.github_token")
                os.makedirs(os.path.dirname(token_file), exist_ok=True)
                with open(token_file, "w") as f:
                    f.write(token)
                print(f"Token saved to {token_file}")

    if not token:
        print("No token provided. Testing with unauthenticated access.")
        headers = {"Accept": "application/vnd.github.v3+json"}
    else:
        print("Testing with provided GitHub token.")
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"Bearer {token}",
        }

    # Test endpoints
    endpoints = [
        ("Rate Limit", "https://api.github.com/rate_limit"),
        ("User Info", "https://api.github.com/user"),
        (
            "Search Repositories",
            "https://api.github.com/search/repositories?q=language:python&sort=stars&per_page=1",
        ),
        ("Topics", "https://api.github.com/search/topics?q=is:featured&per_page=1"),
    ]

    print("\n=== GitHub API Test Results ===")
    all_successful = True

    for name, url in endpoints:
        try:
            print(f"\nTesting: {name} ({url})")
            response = requests.get(url, headers=headers, timeout=10)

            print(f"Status Code: {response.status_code}")

            if response.status_code == 200:
                print("✅ Success!")

                # Print rate limit info if available
                if "X-RateLimit-Limit" in response.headers:
                    print(
                        f"Rate Limit: {response.headers['X-RateLimit-Remaining']}/{response.headers['X-RateLimit-Limit']}"
                    )
                    reset_time = int(response.headers["X-RateLimit-Reset"])
                    import time
                    from datetime import datetime

                    reset_datetime = datetime.fromtimestamp(reset_time)
                    print(f"Reset at: {reset_datetime}")

                # Print a sample of the response
                data = response.json()
                if name == "Rate Limit":
                    print("\nRate Limit Details:")
                    print(
                        f"Core: {data['resources']['core']['remaining']}/{data['resources']['core']['limit']}"
                    )
                    print(
                        f"Search: {data['resources']['search']['remaining']}/{data['resources']['search']['limit']}"
                    )
                elif name == "User Info" and "login" in data:
                    print(f"Authenticated as: {data['login']}")
                elif (
                    name == "Search Repositories" and "items" in data and data["items"]
                ):
                    repo = data["items"][0]
                    print(
                        f"Top repository: {repo['full_name']} ({repo['stargazers_count']} stars)"
                    )
                elif name == "Topics" and "items" in data and data["items"]:
                    topic = data["items"][0]
                    print(f"Featured topic: {topic['name']} - {topic['display_name']}")
            else:
                print(f"❌ Failed: {response.text}")
                all_successful = False

        except Exception as e:
            print(f"❌ Error: {str(e)}")
            all_successful = False

    print("\n=== Summary ===")
    if all_successful:
        print("✅ All GitHub API tests passed! Your token is working correctly.")
    else:
        print("❌ Some tests failed. Check the details above.")

    return all_successful


if __name__ == "__main__":
    test_github_api()

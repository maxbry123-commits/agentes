import os
import sys
import asyncio
import requests
import json
from pathlib import Path

# Ensure we can import from the current directory
file_path = os.path.abspath(__file__)
dir_path = os.path.dirname(file_path)
if dir_path not in sys.path:
    sys.path.append(dir_path)

# Import the necessary functions
try:
    from swebench_get_repo_copy import (
        get_github_token,
        RateLimiter,
        check_github_api_status,
    )

    print("✅ Successfully imported from swebench_get_repo_copy.py")
except ImportError as e:
    print(f"❌ Error importing from swebench_get_repo_copy.py: {e}")
    print(f"Current directory: {os.getcwd()}")
    print(f"Python path: {sys.path}")
    sys.exit(1)


def test_github_token():
    """Test if GitHub token is available and valid."""
    print("\n=== Testing GitHub Token ===")

    # Get GitHub token
    github_token = get_github_token()

    if github_token:
        print("✅ GitHub token found!")

        # Setup headers with token
        headers = {"Accept": "application/vnd.github.v3+json"}
        headers["Authorization"] = f"Bearer {github_token}"

        # Test token validity with a simple API call
        try:
            response = requests.get("https://api.github.com/user", headers=headers)

            if response.status_code == 200:
                user_data = response.json()
                print(f"✅ Token is valid! Authenticated as: {user_data.get('login')}")

                # Check API rate limits
                if check_github_api_status(headers):
                    print("✅ API rate limits are sufficient for testing")
                else:
                    print("⚠️ API rate limits may be too low for extensive testing")

                return headers, True
            else:
                print(
                    f"❌ Token validation failed with status code: {response.status_code}"
                )
                print(f"Response: {response.text}")
        except Exception as e:
            print(f"❌ Error testing token: {e}")
    else:
        print(
            "❌ No GitHub token found. Please set the GITHUB_TOKEN environment variable."
        )
        print("You can create a token at: https://github.com/settings/tokens")
        print("Then set it with: export GITHUB_TOKEN=your_token_here")

    # Return unauthenticated headers
    return {"Accept": "application/vnd.github.v3+json"}, False


def test_simple_api_call(headers):
    """Test a simple GitHub API call to verify connectivity."""
    print("\n=== Testing GitHub API Connectivity ===")

    try:
        # Try to get a popular repository
        response = requests.get(
            "https://api.github.com/repos/psf/requests", headers=headers
        )

        if response.status_code == 200:
            repo_data = response.json()
            print(f"✅ Successfully connected to GitHub API")
            print(f"Repository: {repo_data.get('full_name')}")
            print(f"Stars: {repo_data.get('stargazers_count')}")
            print(f"Description: {repo_data.get('description')}")
            return True
        else:
            print(f"❌ API call failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error making API call: {e}")
        return False


def get_repo_issues(headers, owner="psf", repo="requests", max_issues=3):
    """Get issues from a repository."""
    print(f"\n=== Getting Issues from {owner}/{repo} ===")

    try:
        # Get closed issues with the most comments (likely to have solutions)
        params = {
            "state": "closed",
            "sort": "comments",
            "direction": "desc",
            "per_page": max_issues,
        }
        response = requests.get(
            f"https://api.github.com/repos/{owner}/{repo}/issues",
            headers=headers,
            params=params,
        )

        if response.status_code == 200:
            issues = response.json()
            print(f"✅ Successfully retrieved {len(issues)} issues")

            # Filter out pull requests
            issues = [issue for issue in issues if "pull_request" not in issue]
            print(f"✅ Found {len(issues)} issues (excluding PRs)")

            return issues
        else:
            print(f"❌ Failed to get issues: {response.status_code}")
            print(f"Response: {response.text}")
            return []
    except Exception as e:
        print(f"❌ Error getting issues: {e}")
        return []


def get_issue_comments(headers, owner, repo, issue_number):
    """Get comments for a specific issue."""
    print(f"\n=== Getting Comments for Issue #{issue_number} ===")

    try:
        response = requests.get(
            f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/comments",
            headers=headers,
        )

        if response.status_code == 200:
            comments = response.json()
            print(f"✅ Successfully retrieved {len(comments)} comments")
            return comments
        else:
            print(f"❌ Failed to get comments: {response.status_code}")
            print(f"Response: {response.text}")
            return []
    except Exception as e:
        print(f"❌ Error getting comments: {e}")
        return []


def find_solution(comments):
    """Find the best solution in the comments."""
    if not comments:
        return None

    # Sort by reactions count (total)
    sorted_comments = sorted(
        comments,
        key=lambda c: c.get("reactions", {}).get("total_count", 0),
        reverse=True,
    )

    # Return the most liked comment
    if sorted_comments:
        best_comment = sorted_comments[0]
        return {
            "body": best_comment.get("body", ""),
            "author": best_comment.get("user", {}).get("login", ""),
            "created_at": best_comment.get("created_at", ""),
            "url": best_comment.get("html_url", ""),
            "reactions": best_comment.get("reactions", {}).get("total_count", 0),
        }

    return None


def save_results(issues_with_solutions, filename="github_issues_test_results.json"):
    """Save the results to a JSON file."""
    try:
        with open(filename, "w") as f:
            json.dump(issues_with_solutions, f, indent=2)
        print(f"\n✅ Results saved to {filename}")
    except Exception as e:
        print(f"\n❌ Error saving results: {e}")


def main():
    print("=== GitHub Issue Collection Test ===")

    # Test GitHub token
    headers, is_authenticated = test_github_token()

    # Test API connectivity
    if not test_simple_api_call(headers):
        print("❌ Cannot proceed due to API connectivity issues")
        return

    # Repository to test with
    owner = "psf"
    repo = "requests"
    max_issues = 3

    # Get issues
    issues = get_repo_issues(headers, owner, repo, max_issues)

    if not issues:
        print("❌ No issues found to process")
        return

    # Process issues and find solutions
    issues_with_solutions = []

    for issue in issues:
        issue_number = issue["number"]
        print(f"\n--- Processing Issue #{issue_number}: {issue['title']} ---")

        # Get comments
        comments = get_issue_comments(headers, owner, repo, issue_number)

        # Find solution
        solution = find_solution(comments)

        if solution:
            print(
                f"✅ Found solution by {solution['author']} with {solution['reactions']} reactions"
            )

            # Create processed issue
            processed_issue = {
                "repo_name": f"{owner}/{repo}",
                "issue_number": issue_number,
                "title": issue["title"],
                "body": issue["body"] if issue["body"] else "",
                "url": issue["html_url"],
                "created_at": issue["created_at"],
                "state": issue["state"],
                "solution_body": solution["body"],
                "solution_author": solution["author"],
                "solution_url": solution["url"],
                "solution_reactions": solution["reactions"],
            }

            # Print snippet of solution
            solution_snippet = (
                solution["body"][:150] + "..."
                if len(solution["body"]) > 150
                else solution["body"]
            )
            print(f"Solution snippet: {solution_snippet}")

            issues_with_solutions.append(processed_issue)
        else:
            print("❌ No solution found for this issue")

    # Print summary
    print(f"\n=== Summary ===")
    print(
        f"Found {len(issues_with_solutions)} issues with solutions out of {len(issues)} issues"
    )

    # Save results
    if issues_with_solutions:
        save_results(issues_with_solutions)


if __name__ == "__main__":
    main()

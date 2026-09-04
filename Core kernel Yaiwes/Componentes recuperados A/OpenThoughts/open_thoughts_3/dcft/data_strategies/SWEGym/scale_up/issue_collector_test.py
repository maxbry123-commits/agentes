import os
import sys
import requests
import json
from pathlib import Path

print("=== GitHub Issue Collection Test ===")

# 1. Get GitHub token
print("\n1. Getting GitHub token...")
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
else:
    print("❌ No GitHub token found")
    print("You can create a token at: https://github.com/settings/tokens")
    print("Then set it with: export GITHUB_TOKEN=your_token_here")

# 2. Setup headers
headers = {"Accept": "application/vnd.github.v3+json"}
if token:
    headers["Authorization"] = f"Bearer {token}"
    print("Using authenticated requests")
else:
    print("WARNING: Using unauthenticated requests (rate limits will be low)")

# 3. Test repository access
print("\n2. Testing repository access...")
repo_owner = "psf"
repo_name = "requests"

try:
    repo_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
    repo_response = requests.get(repo_url, headers=headers)

    if repo_response.status_code == 200:
        repo_data = repo_response.json()
        print(f"✅ Successfully accessed repository: {repo_data.get('full_name')}")
        print(f"Stars: {repo_data.get('stargazers_count')}")
        print(f"Description: {repo_data.get('description')}")
    else:
        print(f"❌ Failed to access repository: {repo_response.status_code}")
        print(f"Response: {repo_response.text}")
        sys.exit(1)
except Exception as e:
    print(f"❌ Error accessing repository: {e}")
    sys.exit(1)

# 4. Get issues
print("\n3. Getting issues...")
max_issues = 3  # Small number for testing

try:
    # Get closed issues with the most comments (likely to have solutions)
    params = {
        "state": "closed",
        "sort": "comments",
        "direction": "desc",
        "per_page": max_issues,
    }
    issues_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues"
    issues_response = requests.get(issues_url, headers=headers, params=params)

    if issues_response.status_code == 200:
        issues = issues_response.json()
        print(f"✅ Successfully retrieved {len(issues)} issues")

        # Filter out pull requests
        issues = [issue for issue in issues if "pull_request" not in issue]
        print(f"Found {len(issues)} issues (excluding PRs)")

        if not issues:
            print("No issues found to process")
            sys.exit(1)
    else:
        print(f"❌ Failed to get issues: {issues_response.status_code}")
        print(f"Response: {issues_response.text}")
        sys.exit(1)
except Exception as e:
    print(f"❌ Error getting issues: {e}")
    sys.exit(1)

# 5. Process issues and find solutions
print("\n4. Processing issues and finding solutions...")
issues_with_solutions = []

for issue in issues:
    issue_number = issue["number"]
    print(f"\n--- Processing Issue #{issue_number}: {issue['title']} ---")

    try:
        # Get comments
        comments_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues/{issue_number}/comments"
        comments_response = requests.get(comments_url, headers=headers)

        if comments_response.status_code == 200:
            comments = comments_response.json()
            print(f"✅ Retrieved {len(comments)} comments")

            # Find best solution (most reactions)
            if comments:
                # Sort by reactions count (total)
                sorted_comments = sorted(
                    comments,
                    key=lambda c: c.get("reactions", {}).get("total_count", 0),
                    reverse=True,
                )

                # Get the most liked comment
                best_comment = sorted_comments[0]
                solution = {
                    "body": best_comment.get("body", ""),
                    "author": best_comment.get("user", {}).get("login", ""),
                    "created_at": best_comment.get("created_at", ""),
                    "url": best_comment.get("html_url", ""),
                    "reactions": best_comment.get("reactions", {}).get(
                        "total_count", 0
                    ),
                }

                print(
                    f"✅ Found solution by {solution['author']} with {solution['reactions']} reactions"
                )

                # Create processed issue
                processed_issue = {
                    "repo_name": f"{repo_owner}/{repo_name}",
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
                print("❌ No comments found for this issue")
        else:
            print(f"❌ Failed to get comments: {comments_response.status_code}")
            print(f"Response: {comments_response.text}")
    except Exception as e:
        print(f"❌ Error processing issue #{issue_number}: {e}")

# 6. Save results
print(f"\n5. Saving results...")
if issues_with_solutions:
    try:
        output_file = "github_issues_test_results.json"
        with open(output_file, "w") as f:
            json.dump(issues_with_solutions, f, indent=2)
        print(f"✅ Results saved to {output_file}")

        # Print summary
        print(f"\n=== Summary ===")
        print(
            f"Found {len(issues_with_solutions)} issues with solutions out of {len(issues)} issues"
        )
    except Exception as e:
        print(f"❌ Error saving results: {e}")
else:
    print("❌ No issues with solutions found")

print("\nTest completed!")

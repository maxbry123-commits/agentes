import os
import sys
import asyncio
import json
import time
from pathlib import Path
from datasets import Dataset
from huggingface_hub import HfApi, login

# Add the current directory to the path to ensure imports work correctly
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from swebench_get_repo_copy import (
    get_github_token,
    RateLimiter,
    process_repository,
    check_github_api_status,
)


async def collect_issues_from_repos(repos, max_issues_per_repo=5):
    """Collect issues from a list of repositories."""
    print(f"Collecting issues from {len(repos)} repositories...")

    # Get GitHub token
    github_token = get_github_token()

    # Setup headers
    headers = {"Accept": "application/vnd.github.v3+json"}
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"
        print("Using GitHub authentication token")
    else:
        print(
            "WARNING: No GitHub token found. API rate limits will be severely restricted."
        )

    # Create rate limiter
    rate_limiter = RateLimiter(calls_per_second=0.5)

    # Check API status
    if not check_github_api_status(headers):
        print("GitHub API rate limits may be too low to complete the task.")
        return []

    all_issues = []

    # Process each repository
    for repo_info in repos:
        owner, repo_name, topic = repo_info
        print(f"\nProcessing repository: {owner}/{repo_name}")

        # Process the repository without try/catch to expose errors
        issues = await process_repository(
            (owner, repo_name), topic, max_issues_per_repo, headers, rate_limiter
        )

        # Print results
        print(f"Collected {len(issues)} issues with solutions from {owner}/{repo_name}")

        if issues:
            all_issues.extend(issues)

            # Print a sample issue
            if issues:  # Check if the list is not empty
                sample_issue = issues[0]
                print(f"Sample issue: {sample_issue['title']}")
                solution_snippet = (
                    sample_issue["solution_body"][:100] + "..."
                    if len(sample_issue["solution_body"]) > 100
                    else sample_issue["solution_body"]
                )
                print(f"Solution snippet: {solution_snippet}")
            else:
                print("No issues found with solutions")

    return all_issues


def upload_to_huggingface(issues, repo_id):
    """Upload the collected issues to Hugging Face."""
    print(f"\nUploading {len(issues)} issues to Hugging Face dataset: {repo_id}")

    # Convert to Dataset
    dataset = Dataset.from_list(issues)
    # Add metadata
    # dataset = dataset.cast_column("labels", [str])

    # Save locally first
    output_file = "github_issues_dataset.json"
    with open(output_file, "w") as f:
        json.dump(issues, f, indent=2)
    print(f"Saved dataset to {output_file}")

    # Get HF token from environment
    hf_token = os.environ.get("HF_TOKEN")
    if not hf_token:
        print("No Hugging Face token found in environment (HF_TOKEN).")
        print("Will try to upload without authentication.")

    try:
        # Login to Hugging Face
        if hf_token:
            login(token=hf_token)

        # Push to Hugging Face
        dataset.push_to_hub(repo_id=repo_id, private=False, token=hf_token)

        print(f"Successfully uploaded dataset to {repo_id}")
        print(f"View at: https://huggingface.co/datasets/{repo_id}")
        return True
    except Exception as e:
        print(f"Error uploading to Hugging Face: {e}")
        print("Dataset is still available locally at github_issues_dataset.json")
        return False


async def main():
    # List of repositories to collect issues from
    # Format: (owner, repo_name, topic)
    repos = [
        ("psf", "requests", "http"),
    ]

    # Collect issues
    issues = await collect_issues_from_repos(repos, max_issues_per_repo=100)

    if issues:
        print(f"\nCollected a total of {len(issues)} issues with solutions")

        # Upload to Hugging Face
        upload_to_huggingface(issues, "mlfoundations-dev/etashggithubsolutions")
    else:
        print("No issues collected.")


if __name__ == "__main__":
    print("=== GitHub Issue Collection and Upload ===")

    # Run the async main function
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()

    print("\nProcess completed!")

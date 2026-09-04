import os
import asyncio
import sys
from datasets import Dataset

# Add the current directory to the path to ensure imports work correctly
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from swebench_get_repo_copy import (
    get_github_token,
    RateLimiter,
    collect_github_issues_by_topic,
    check_github_api_status,
    get_github_repo_dataset,
    process_repository,
)


async def test_specific_repo_async():
    """Test collecting issues from a specific repository."""
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
        print("GitHub API rate limits may be too low to complete the test.")
        return

    # Test with a popular Python repository
    repo_owner = "psf"
    repo_name = "requests"

    # Process a single repository
    print(f"\nTesting with repository: {repo_owner}/{repo_name}")
    repo_info = (repo_owner, repo_name)
    topic = "python-requests"
    max_issues = 5  # Small number for testing

    # Import the function
    from swebench_get_repo_copy import process_repository

    # Process the repository
    issues = await process_repository(
        repo_info, topic, max_issues, headers, rate_limiter
    )

    # Print results
    print(
        f"\nCollected {len(issues)} issues with solutions from {repo_owner}/{repo_name}"
    )

    if issues:
        print("\nSample issue:")
        sample_issue = issues[0]
        print(f"Title: {sample_issue['title']}")
        print(f"URL: {sample_issue['url']}")
        print(f"Solution snippet: {sample_issue['solution_body'][:100]}...")

    return issues


def test_collect_by_topic():
    """Test collecting issues by topic."""
    # Test parameters
    topics = ["requests"]  # Just one topic for testing
    repos_per_topic = 2
    max_issues_per_repo = 3

    print(f"\nTesting collect_github_issues_by_topic with topics: {topics}")

    # Collect issues
    dataset = collect_github_issues_by_topic(
        topics=topics,
        num_topics=1,
        repos_per_topic=repos_per_topic,
        max_issues_per_repo=max_issues_per_repo,
        output_file="test_github_issues.json",
    )

    # Print results
    if isinstance(dataset, Dataset):
        print(f"\nSuccessfully collected dataset with {len(dataset)} issues")
        if len(dataset) > 0:
            print("\nSample columns:", dataset.column_names)
            print(
                "\nFirst issue title:",
                (
                    dataset[0]["title"]
                    if "title" in dataset.column_names
                    else "Title not found"
                ),
            )
    else:
        print("\nFailed to collect dataset")

    return dataset


def test_specific_repo_function():
    """Test the get_github_repo_dataset function."""
    try:
        # Test with a specific repository and issue
        repo_owner = "psf"
        repo_name = "requests"
        issue_number = 5000  # Choose a specific issue number that exists

        print(
            f"\nTesting get_github_repo_dataset with {repo_owner}/{repo_name} issue #{issue_number}"
        )

        # Get dataset
        dataset = get_github_repo_dataset(
            repo_owner=repo_owner,
            repo_name=repo_name,
            issue_number=issue_number,
            get_solutions=True,
            close_issue=False,  # Don't close the issue in testing
        )

        # Print results
        if dataset and hasattr(dataset, "rows") and dataset.rows:
            print(f"\nSuccessfully collected dataset with {len(dataset.rows)} issues")
            if dataset.rows:
                print(
                    "\nIssue title:",
                    dataset.rows[0].get("issue_title", "Title not found"),
                )
                print("Has solution:", "solution" in dataset.rows[0])
                if "solution" in dataset.rows[0]:
                    print("Solution snippet:", dataset.rows[0]["solution"][:100], "...")
        else:
            print("\nFailed to collect dataset or no issues found")

        return dataset
    except Exception as e:
        print(f"Error in test_specific_repo_function: {e}")
        return None


if __name__ == "__main__":
    print("Testing GitHub Issue Collector")

    # Test the async repository processing
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        issues = loop.run_until_complete(test_specific_repo_async())
    finally:
        loop.close()

    # Test collecting by topic
    dataset = test_collect_by_topic()

    # Test specific repo function
    repo_dataset = test_specific_repo_function()

    print("\nTests completed!")

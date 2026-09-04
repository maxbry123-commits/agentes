import requests
import pandas as pd
import time
import os
import concurrent.futures
import threading
import asyncio
import aiohttp
from datasets import Dataset, DatasetDict
import datetime
from tqdm import tqdm
import json
from typing import List, Dict, Tuple, Optional, Any, Set


class RateLimiter:
    """Smart rate limiter for GitHub API requests that respects rate limit headers."""

    def __init__(self, calls_per_second=1):
        self.calls_per_second = 1  # Default to conservative rate
        self.last_call = 0
        self.lock = threading.Lock()
        self.remaining_calls = 60  # Default GitHub unauthenticated limit
        self.reset_time = time.time() + 3600  # Default reset after an hour
        self.authenticated = False
        self.core_limit = {}  # Track core API limits
        self.search_limit = {}  # Track search API limits
        self.semaphore = asyncio.Semaphore(10)  # Limit concurrent requests

        # Track resource-specific limits
        self.resource_limits = {
            "core": {"remaining": 60, "limit": 60, "reset": time.time() + 3600},
            "search": {"remaining": 10, "limit": 10, "reset": time.time() + 3600},
        }

    def wait(self):
        with self.lock:
            current_time = time.time()

            # If we're past the reset time, reset our counter
            if current_time > self.reset_time:
                self.remaining_calls = 60 if not self.authenticated else 5000

            # If we're out of calls, wait until reset
            if self.remaining_calls <= 5:  # Keep a small buffer
                wait_time = max(0, self.reset_time - current_time)
                if wait_time > 0:
                    print(
                        f"Rate limit reached. Waiting {wait_time:.1f} seconds for reset..."
                    )
                    time.sleep(wait_time + 2)  # Add 2 second buffer

            # Standard rate limiting
            time_since_last_call = current_time - self.last_call
            time_to_wait = max(0, 1 / self.calls_per_second - time_since_last_call)

            if time_to_wait > 0:
                time.sleep(time_to_wait)

            self.last_call = time.time()
            self.remaining_calls -= 1

    async def async_wait(self, resource="core"):
        """Async version of wait for use with aiohttp"""
        async with self.semaphore:
            # Use a context manager for the lock to ensure it's always released
            lock_acquired = False
            try:
                self.lock.acquire()
                lock_acquired = True

                current_time = time.time()

                # Get resource-specific limits
                res_limit = self.resource_limits.get(
                    resource,
                    {"remaining": 60, "limit": 60, "reset": time.time() + 3600},
                )

                # If we're past the reset time, reset our counter
                if current_time > res_limit["reset"]:
                    res_limit["remaining"] = res_limit["limit"]

                # If we're out of calls, wait until reset
                if res_limit["remaining"] <= 5:  # Keep a small buffer
                    wait_time = max(0, res_limit["reset"] - current_time)
                    if wait_time > 0:
                        print(
                            f"Rate limit reached for {resource}. Waiting {wait_time:.1f} seconds for reset..."
                        )
                        # Release the lock during the wait
                        self.lock.release()
                        lock_acquired = False

                        # Cap the wait time to avoid extremely long waits
                        wait_time = min(wait_time, 300)  # Max 5 minutes wait
                        await asyncio.sleep(wait_time + 2)  # Add 2 second buffer

                        self.lock.acquire()
                        lock_acquired = True

                # Standard rate limiting
                time_since_last_call = current_time - self.last_call
                time_to_wait = max(0, 1 / self.calls_per_second - time_since_last_call)

                if time_to_wait > 0:
                    # Release the lock during the wait
                    self.lock.release()
                    lock_acquired = False

                    await asyncio.sleep(time_to_wait)

                    self.lock.acquire()
                    lock_acquired = True

                self.last_call = time.time()
                res_limit["remaining"] -= 1
                self.resource_limits[resource] = res_limit
            finally:
                # Always release the lock if we acquired it
                if lock_acquired:
                    self.lock.release()

    def update_from_headers(self, headers):
        """Update rate limit info from GitHub API response headers"""
        with self.lock:
            # Check if we're authenticated based on rate limits
            if "X-RateLimit-Limit" in headers:
                limit = int(headers["X-RateLimit-Limit"])
                if limit > 60:
                    self.authenticated = True

            # Update remaining calls
            if "X-RateLimit-Remaining" in headers:
                self.remaining_calls = int(headers["X-RateLimit-Remaining"])

                # Print warning if we're running low
                if self.remaining_calls < 20:
                    print(
                        f"⚠️ Only {self.remaining_calls} API calls remaining before rate limit"
                    )

            # Update reset time
            if "X-RateLimit-Reset" in headers:
                self.reset_time = int(headers["X-RateLimit-Reset"])

            # Track which API we're using (core vs search)
            if "X-RateLimit-Resource" in headers:
                resource = headers["X-RateLimit-Resource"]
                if resource == "core":
                    self.core_limit = {
                        "limit": int(headers.get("X-RateLimit-Limit", 0)),
                        "remaining": int(headers.get("X-RateLimit-Remaining", 0)),
                        "reset": int(headers.get("X-RateLimit-Reset", 0)),
                    }
                    self.resource_limits["core"] = self.core_limit
                elif resource == "search":
                    self.search_limit = {
                        "limit": int(headers.get("X-RateLimit-Limit", 0)),
                        "remaining": int(headers.get("X-RateLimit-Remaining", 0)),
                        "reset": int(headers.get("X-RateLimit-Reset", 0)),
                    }
                    self.resource_limits["search"] = self.search_limit

    def update_from_aiohttp_headers(self, headers):
        """Update rate limit info from aiohttp response headers"""
        with self.lock:
            # Check if we're authenticated based on rate limits
            if "X-RateLimit-Limit" in headers:
                limit = int(headers["X-RateLimit-Limit"])
                if limit > 60:
                    self.authenticated = True

            # Update remaining calls
            if "X-RateLimit-Remaining" in headers:
                self.remaining_calls = int(headers["X-RateLimit-Remaining"])

            # Update reset time
            if "X-RateLimit-Reset" in headers:
                self.reset_time = int(headers["X-RateLimit-Reset"])

            # Track which API we're using (core vs search)
            if "X-RateLimit-Resource" in headers:
                resource = headers["X-RateLimit-Resource"]
                if resource == "core":
                    self.core_limit = {
                        "limit": int(headers.get("X-RateLimit-Limit", 0)),
                        "remaining": int(headers.get("X-RateLimit-Remaining", 0)),
                        "reset": int(headers.get("X-RateLimit-Reset", 0)),
                    }
                    self.resource_limits["core"] = self.core_limit
                elif resource == "search":
                    self.search_limit = {
                        "limit": int(headers.get("X-RateLimit-Limit", 0)),
                        "remaining": int(headers.get("X-RateLimit-Remaining", 0)),
                        "reset": int(headers.get("X-RateLimit-Reset", 0)),
                    }
                    self.resource_limits["search"] = self.search_limit


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


def get_github_topics(limit=30):
    """
    Fetch a list of popular Python-related GitHub topics.

    Parameters:
    - limit: Maximum number of topics to retrieve
    - github_token: GitHub personal access token (recommended to avoid rate limits)
    - rate_limiter: RateLimiter instance to control request rate

    Returns:
    - Dataset with topics column containing list of Python-related topics
    """
    # Setup API request headers
    # Get token if not provided
    github_token = get_github_token()
    rate_limiter = None
    headers = {"Accept": "application/vnd.github.v3+json"}

    # Get token if not provided
    if not github_token:
        github_token = get_github_token()

    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"
        print("Using GitHub authentication token")
    else:
        print(
            "WARNING: No GitHub token found. API rate limits will be severely restricted."
        )

    rate_limiter = RateLimiter(calls_per_second=0.5)

    base_url = "https://api.github.com/search/topics"

    all_topics = []
    page = 1
    per_page = min(100, limit)  # GitHub API allows max 100 per page
    remaining = limit

    print(f"Fetching up to {limit} Python-related GitHub topics...")

    # Try different search queries if one fails
    search_queries = [
        "python",  # Simple search for python
        "topic:python",  # Explicit topic search
        "language:python",  # Language-based search
        "python framework",  # Python frameworks
        "python library",  # Python libraries
    ]

    for query in search_queries:
        if len(all_topics) >= limit:
            break

        print(f"Trying search query: {query}")

        while remaining > 0:
            # Search for Python-related topics
            params = {
                "q": query,
                "per_page": min(per_page, remaining),
                "page": page,
            }
            if rate_limiter:
                rate_limiter.wait()

            response = requests.get(base_url, headers=headers, params=params)

            # Print response details for debugging
            print(f"Response status: {response.status_code}")

            # Update rate limiter with response headers
            if rate_limiter and response.headers:
                rate_limiter.update_from_headers(response.headers)

            if response.status_code == 403:
                reset_time = int(
                    response.headers.get("X-RateLimit-Reset", time.time() + 3600)
                )
                wait_time = max(0, reset_time - time.time())
                print(f"Rate limit exceeded. Reset in {wait_time:.1f} seconds.")
                if (
                    wait_time > 0 and wait_time < 3600
                ):  # Only wait if reasonable (<1 hour)
                    print(f"Waiting for rate limit reset...")
                    time.sleep(wait_time + 2)  # Add buffer
                    continue
                else:
                    print("Rate limit wait time too long. Please use a GitHub token.")
                    break
            elif response.status_code != 200:
                print(f"Error fetching topics: Status {response.status_code}")
                print(f"Response: {response.text}")
                break

            data = response.json()
            items = data.get("items", [])

            print(f"Found {len(items)} items in response")

            if not items:
                break

            # Less strict filtering - include more Python-related topics
            for item in items:
                topic_name = item.get("name", "").lower()
                if topic_name and topic_name not in [t.lower() for t in all_topics]:
                    all_topics.append(item["name"])

                    # Print each topic we're adding
                    print(f"Adding topic: {item['name']}")

                    if len(all_topics) >= limit:
                        break

            fetched = len(items)
            remaining -= fetched

            if (
                fetched < per_page or len(all_topics) >= limit
            ):  # Less than requested or we have enough
                break

            page += 1
            time.sleep(1)  # Be nice to the API

        # Reset for next query
        page = 1

    # If we still don't have topics, add some common Python topics manually
    if not all_topics:
        print("No Python topics found via API. Using fallback list.")
        all_topics = [
            "python",
            "django",
            "flask",
            "fastapi",
            "pandas",
            "numpy",
            "pytorch",
            "tensorflow",
            "scikit-learn",
            "matplotlib",
            "data-science",
            "machine-learning",
            "web-development",
            "api",
            "automation",
            "scraping",
            "nlp",
            "deep-learning",
        ]
        # Only take up to the limit
        all_topics = all_topics[:limit]

    # Create dataset with topics column
    dataset = Dataset.from_dict({"topics": all_topics})  # Each topic as a separate row

    print(f"Retrieved {len(all_topics)} Python-related topics")
    return dataset


async def get_repositories_async(
    search_query, max_repos, headers, rate_limiter, max_retries=3
):
    """Get repositories matching the search query using async."""
    params = {
        "q": search_query,
        "sort": "stars",
        "order": "desc",
        "per_page": min(100, max_repos),  # GitHub API max is 100 per page
    }

    url = "https://api.github.com/search/repositories"
    all_repos = []

    async with aiohttp.ClientSession() as session:
        # Get first page
        await rate_limiter.async_wait("search")

        for retry in range(max_retries):
            try:
                async with session.get(
                    url, headers=headers, params=params, timeout=30
                ) as response:
                    # Update rate limiter with response headers
                    rate_limiter.update_from_aiohttp_headers(response.headers)

                    if response.status == 403:
                        # Check if this is a rate limit issue
                        remaining = response.headers.get("X-RateLimit-Remaining")
                        if remaining and int(remaining) == 0:
                            reset_time = int(
                                response.headers.get(
                                    "X-RateLimit-Reset", time.time() + 3600
                                )
                            )
                            wait_time = max(0, reset_time - time.time())
                            print(
                                f"Rate limit exceeded when searching repos. Reset in {wait_time:.1f} seconds."
                            )
                            if (
                                wait_time > 0 and wait_time < 3600
                            ):  # Only wait if reasonable (<1 hour)
                                print(f"Waiting for rate limit reset...")
                                await asyncio.sleep(wait_time + 2)  # Add buffer
                                continue  # Try again after waiting
                            else:
                                print(
                                    "Rate limit wait time too long. Please use a GitHub token."
                                )
                                return []
                        else:
                            # This might be a secondary rate limit or abuse detection
                            retry_after = int(response.headers.get("Retry-After", 60))
                            print(
                                f"GitHub API temporary restriction. Waiting {retry_after} seconds before retry."
                            )
                            await asyncio.sleep(retry_after)
                            continue
                    # Handle other error responses
                    elif response.status == 401:
                        print("Authentication failed. Check your GitHub token.")
                        return []
                    elif response.status == 404:
                        print(f"Resource not found: {url}")
                        return []
                    elif response.status == 422:
                        text = await response.text()
                        print(f"Query error: {text}")
                        # Try with a simpler query
                        if "stars:>" in search_query:
                            simplified_query = search_query.split("stars:>")[0].strip()
                            print(f"Trying with simplified query: {simplified_query}")
                            return await get_repositories_async(
                                simplified_query,
                                max_repos,
                                headers,
                                rate_limiter,
                                max_retries - 1,
                            )
                        return []
                    elif response.status != 200:
                        text = await response.text()
                        print(f"Error searching repositories: Status {response.status}")
                        print(f"Response: {text}")
                        # Wait before retry
                        await asyncio.sleep(10 * (retry + 1))
                        continue

                    # Success!
                    result = await response.json()
                    repos = result.get("items", [])
                    all_repos.extend(repos)

                    # If we need more repos and there are multiple pages, fetch them in parallel
                    if len(all_repos) < max_repos and len(repos) == 100:
                        # Check if there are more pages
                        link_header = response.headers.get("Link", "")
                        next_urls = []

                        # Parse Link header to find next URLs
                        if 'rel="next"' in link_header:
                            parts = link_header.split(",")
                            for part in parts:
                                if 'rel="next"' in part:
                                    url_part = part.split(";")[0].strip()
                                    next_url = url_part[1:-1]  # Remove < and >
                                    next_urls.append(next_url)
                                    break

                        if next_urls:
                            print(
                                f"Fetched {len(all_repos)} repos, getting more to reach {max_repos}..."
                            )

                            # Fetch next pages in parallel
                            tasks = []
                            for next_url in next_urls[
                                : min(5, max_repos // 100)
                            ]:  # Limit to 5 pages max
                                tasks.append(
                                    fetch_next_page(
                                        session, next_url, headers, rate_limiter
                                    )
                                )

                            if tasks:
                                next_pages_results = await asyncio.gather(*tasks)
                                for page_repos in next_pages_results:
                                    all_repos.extend(page_repos)
                                    if len(all_repos) >= max_repos:
                                        break

                    return all_repos[:max_repos]  # Ensure we don't exceed max_repos

            except asyncio.TimeoutError:
                print(
                    f"Request timed out (attempt {retry+1}/{max_retries}). Retrying..."
                )
                await asyncio.sleep(5)
            except Exception as e:
                print(
                    f"Exception when searching repositories (attempt {retry+1}/{max_retries}): {e}"
                )
                await asyncio.sleep(5)

    print("Failed to fetch repositories after multiple attempts")
    return all_repos[:max_repos] if all_repos else []


async def fetch_next_page(session, url, headers, rate_limiter):
    """Fetch a single page of repository results."""
    await rate_limiter.async_wait("search")

    try:
        async with session.get(url, headers=headers, timeout=30) as response:
            # Update rate limiter
            rate_limiter.update_from_aiohttp_headers(response.headers)

            if response.status == 200:
                result = await response.json()
                return result.get("items", [])
            else:
                print(f"Error fetching next page: Status {response.status}")
                return []
    except Exception as e:
        print(f"Error fetching next page: {e}")
        return []


def get_repositories(search_query, max_repos, headers, rate_limiter, max_retries=3):
    """Synchronous wrapper for get_repositories_async."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(
            get_repositories_async(
                search_query, max_repos, headers, rate_limiter, max_retries
            )
        )
    finally:
        loop.close()


async def get_issues_page_async(
    repo_info, page, per_page, headers, rate_limiter, max_retries=3
):
    """Get a single page of issues for a repository using async."""
    owner, repo_name = repo_info

    params = {"state": "all", "per_page": per_page, "page": page}

    url = f"https://api.github.com/repos/{owner}/{repo_name}/issues"

    async with aiohttp.ClientSession() as session:
        for retry in range(max_retries):
            try:
                # Wait for rate limiter
                await rate_limiter.async_wait("core")

                async with session.get(
                    url, headers=headers, params=params, timeout=30
                ) as response:
                    # Update rate limiter with response headers
                    rate_limiter.update_from_aiohttp_headers(response.headers)

                    # Handle rate limiting
                    if response.status == 403:
                        # Check if this is a rate limit issue
                        remaining = response.headers.get("X-RateLimit-Remaining")
                        if remaining and int(remaining) == 0:
                            reset_time = int(
                                response.headers.get(
                                    "X-RateLimit-Reset", time.time() + 3600
                                )
                            )
                            wait_time = max(0, reset_time - time.time())
                            print(
                                f"Rate limit exceeded for {owner}/{repo_name}. Reset in {wait_time:.1f} seconds."
                            )
                            if (
                                wait_time > 0 and wait_time < 3600
                            ):  # Only wait if reasonable (<1 hour)
                                print(f"Waiting for rate limit reset...")
                                await asyncio.sleep(wait_time + 2)  # Add buffer
                                continue  # Try again after waiting
                            else:
                                print(
                                    "Rate limit wait time too long. Please use a GitHub token."
                                )
                                return owner, repo_name, []
                        else:
                            # This might be a secondary rate limit or abuse detection
                            retry_after = int(response.headers.get("Retry-After", 60))
                            print(
                                f"GitHub API temporary restriction for {owner}/{repo_name}. Waiting {retry_after} seconds."
                            )
                            await asyncio.sleep(retry_after)
                            continue
                    # Handle other error responses
                    elif response.status == 401:
                        print(
                            f"Authentication failed for {owner}/{repo_name}. Check your GitHub token."
                        )
                        return owner, repo_name, []
                    elif response.status == 404:
                        print(f"Repository not found or no access: {owner}/{repo_name}")
                        return owner, repo_name, []
                    elif response.status != 200:
                        text = await response.text()
                        print(
                            f"Error fetching issues for {owner}/{repo_name} (page {page}): Status {response.status}"
                        )
                        print(f"Response: {text}")
                        # Wait before retry
                        await asyncio.sleep(5 * (retry + 1))
                        continue

                    # Success!
                    return owner, repo_name, await response.json()

            except asyncio.TimeoutError:
                print(
                    f"Request timed out for {owner}/{repo_name} (attempt {retry+1}/{max_retries}). Retrying..."
                )
                await asyncio.sleep(5)
            except Exception as e:
                print(
                    f"Exception when fetching issues for {owner}/{repo_name} (page {page}) (attempt {retry+1}/{max_retries}): {e}"
                )
                await asyncio.sleep(5)

        print(f"Failed to fetch issues for {owner}/{repo_name} after multiple attempts")
        return owner, repo_name, []


def get_issues_page(repo_info, page, per_page, headers, rate_limiter, max_retries=3):
    """Synchronous wrapper for get_issues_page_async."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(
            get_issues_page_async(
                repo_info, page, per_page, headers, rate_limiter, max_retries
            )
        )
    finally:
        loop.close()


def process_issues(owner, repo_name, issues, topic_name, max_issues=None):
    """Process issue data into the desired format."""
    processed_issues = []
    full_repo_name = f"{owner}/{repo_name}"

    for issue in issues:
        # Skip pull requests
        if "pull_request" in issue:
            continue

        # Clean and prepare the data
        issue_data = {
            "repo_name": full_repo_name,
            "topic": topic_name,
            "issue_number": issue["number"],
            "title": issue["title"],
            "body": issue["body"] if issue["body"] else "",
            "state": issue["state"],
            "created_at": issue["created_at"],
            "updated_at": issue["updated_at"],
            "url": issue["html_url"],
            "labels": [label["name"] for label in issue.get("labels", [])],
        }

        # Add user info if available
        if "user" in issue and issue["user"]:
            issue_data["user_login"] = issue["user"]["login"]

        # Add comments count if available
        if "comments" in issue:
            issue_data["comments_count"] = issue["comments"]

        processed_issues.append(issue_data)

        # Only limit if max_issues is specified
        if max_issues is not None and len(processed_issues) >= max_issues:
            break

    return processed_issues


async def collect_github_issues_by_topic_async(
    topics=None,
    num_topics=5,
    repos_per_topic=3,
    max_issues_per_repo=50,
    github_token=None,
    max_workers=5,
    min_stars=100,
    output_file=None,
):
    """
    Collect GitHub issues across multiple topics using async.

    Parameters:
    - topics: List of topic names to search (if None, will fetch popular topics)
    - num_topics: Number of topics to include if topics=None
    - repos_per_topic: Number of repositories to collect per topic
    - max_issues_per_repo: Maximum number of issues to collect per repository
    - github_token: GitHub personal access token (recommended to avoid rate limits)
    - max_workers: Maximum number of parallel workers for API requests
    - min_stars: Minimum number of stars for repositories to include

    Returns:
    - DatasetDict with train and test splits, organized by topic
    """
    try:
        # Get token if not provided
        if not github_token:
            github_token = get_github_token()

        # Setup API request headers
        headers = {"Accept": "application/vnd.github.v3+json"}
        if github_token:
            headers["Authorization"] = f"Bearer {github_token}"
            print("Using GitHub authentication token")
        else:
            print(
                "WARNING: No GitHub token found. API rate limits will be severely restricted."
            )
            print(
                "Create a token at https://github.com/settings/tokens and set it as GITHUB_TOKEN env variable"
            )
            print("or save it to ~/.github_token file")

            # Reduce workers when unauthenticated to avoid rate limits
            max_workers = min(2, max_workers)
            repos_per_topic = min(5, repos_per_topic)
            print(
                f"Reducing workers to {max_workers} and repos_per_topic to {repos_per_topic} due to no auth token"
            )

        # Create a rate limiter with slightly higher calls per second when authenticated
        calls_per_second = 1.0 if github_token else 0.5
        rate_limiter = RateLimiter(calls_per_second=calls_per_second)

        # Get topics if not provided
        if topics is None:
            topics_df = get_github_topics(
                limit=num_topics, github_token=github_token, rate_limiter=rate_limiter
            )
            if topics_df.empty:
                print("Could not fetch topics. Exiting.")
                return DatasetDict()
            topics = topics_df["name"].tolist()

        print(f"Collecting issues for {len(topics)} topics: {', '.join(topics)}")

        all_issues_data = []

        # Process topics in smaller batches to avoid overwhelming the API
        topic_batch_size = 2  # Process 2 topics at a time (reduced from 3)
        topic_batches = [
            topics[i : i + topic_batch_size]
            for i in range(0, len(topics), topic_batch_size)
        ]

        for topic_batch in topic_batches:
            # Create tasks for each topic in the batch
            topic_tasks = []
            for topic in topic_batch:
                task = process_topic(
                    topic,
                    repos_per_topic,
                    max_issues_per_repo,
                    headers,
                    rate_limiter,
                    max_workers,
                    min_stars,
                )
                topic_tasks.append(task)

            # Run all topic tasks concurrently with exception handling
            results = await asyncio.gather(*topic_tasks, return_exceptions=True)

            # Collect results
            for result in results:
                # Skip exceptions
                if isinstance(result, Exception):
                    print(f"Error processing topic batch: {result}")
                    continue

                all_issues_data.extend(result)

            # Save intermediate results to avoid losing data on interruption
            if output_file and all_issues_data:
                intermediate_file = (
                    f"{os.path.splitext(output_file)[0]}_intermediate.json"
                )
                try:
                    with open(intermediate_file, "w") as f:
                        json.dump(all_issues_data, f)
                    print(
                        f"Saved {len(all_issues_data)} issues to intermediate file: {intermediate_file}"
                    )
                except Exception as e:
                    print(f"Error saving intermediate results: {e}")

        # Process the collected data
        if not all_issues_data:
            print("No issues collected across any topics.")
            return DatasetDict()

        # Save raw data to JSON file if requested
        if output_file:
            print(f"Saving raw data to {output_file}")
            with open(output_file, "w") as f:
                json.dump(all_issues_data, f, indent=2)

        # Create the Hugging Face Dataset
        print(
            f"\nCreating dataset with {len(all_issues_data)} issues across {len(topics)} topics..."
        )
        dataset = Dataset.from_pandas(pd.DataFrame(all_issues_data))

        # Add dataset metadata
        topic_list = ", ".join(topics)
        dataset.info.description = (
            f"GitHub issues collected from repositories with topics: {topic_list}"
        )
        dataset.info.homepage = "https://github.com"
        dataset.info.license = "See individual repositories for license information"
        dataset.info.version = datetime.datetime.now().strftime("%Y.%m.%d")

        # Split the dataset
        dataset_dict = dataset.train_test_split(test_size=0.2, seed=42)

        # Summary statistics
        topic_counts = {}
        repo_counts = {}

        for issue in all_issues_data:
            topic = issue["topic"]
            repo = issue["repo_name"]

            if topic not in topic_counts:
                topic_counts[topic] = 0
            topic_counts[topic] += 1

            if repo not in repo_counts:
                repo_counts[repo] = 0
            repo_counts[repo] += 1

        print("\nIssues per topic:")
        for topic, count in topic_counts.items():
            print(f"  {topic}: {count} issues")

        print("\nIssues per repository:")
        for repo, count in sorted(
            repo_counts.items(), key=lambda x: x[1], reverse=True
        )[:10]:
            print(f"  {repo}: {count} issues")

        print(f"\nTrain split: {len(dataset_dict['train'])} issues")
        print(f"Test split: {len(dataset_dict['test'])} issues")

        return dataset

    except Exception as e:
        print(f"Error in collect_github_issues_by_topic_async: {e}")
        return DatasetDict()


async def process_topic(
    topic,
    repos_per_topic,
    max_issues_per_repo,
    headers,
    rate_limiter,
    max_workers,
    min_stars,
):
    """Process a single topic to collect issues from its repositories."""
    print(f"\n--- Processing topic: {topic} ---")

    try:
        # Search for repositories with this topic and language:python
        search_query = f"topic:{topic} language:python stars:>{min_stars}"
        print(f"Searching for repositories with query: {search_query}")

        repos = await get_repositories_async(
            search_query, repos_per_topic, headers, rate_limiter
        )

        if not repos:
            print(f"No repositories found for topic '{topic}'. Skipping.")
            return []

        repo_count = len(repos)
        print(f"Found {repo_count} repositories for topic '{topic}'")

        # Prepare repository data for parallel processing
        repo_data = [(repo["owner"]["login"], repo["name"]) for repo in repos]

        # Process repositories in parallel - but limit to a reasonable number
        # to avoid overwhelming the API
        max_concurrent = min(max_workers, 10)  # Cap at 10 concurrent repos max
        repo_batch_size = 20  # Process repos in batches of 20

        all_topic_issues = []

        # Process repositories in batches to avoid creating too many tasks at once
        for i in range(0, len(repo_data), repo_batch_size):
            batch = repo_data[i : i + repo_batch_size]

            # Process repositories in parallel
            repo_tasks = []
            for repo_info in batch:
                task = process_repository(
                    repo_info, topic, max_issues_per_repo, headers, rate_limiter
                )
                repo_tasks.append(task)

            # Run repository tasks concurrently with a semaphore to limit concurrency
            semaphore = asyncio.Semaphore(max_concurrent)

            async def process_with_semaphore(task):
                async with semaphore:
                    return await task

            bounded_tasks = [process_with_semaphore(task) for task in repo_tasks]

            # Gather results with exception handling
            repo_results = await asyncio.gather(*bounded_tasks, return_exceptions=True)

            # Flatten results
            for result in repo_results:
                # Skip exceptions
                if isinstance(result, Exception):
                    print(f"Error processing repository in topic {topic}: {result}")
                    continue

                all_topic_issues.extend(result)

            # If we've collected enough issues, we can stop
            # Only check if max_issues_per_repo is specified
            if (
                max_issues_per_repo is not None
                and len(all_topic_issues) >= repos_per_topic * max_issues_per_repo / 2
            ):
                break

        return all_topic_issues
    except Exception as e:
        print(f"Error processing topic {topic}: {e}")
        return []


async def process_repository(
    repo_info, topic, max_issues_per_repo, headers, rate_limiter
):
    """Process a single repository to collect its issues."""
    owner, repo_name = repo_info

    try:
        # First, get page 1
        _, _, issues = await get_issues_page_async(
            repo_info, 1, 100, headers, rate_limiter
        )

        if not issues:
            return []

        # Calculate how many pages we need
        issues_on_first_page = len([i for i in issues if "pull_request" not in i])
        if issues_on_first_page == 0:
            return []

        # Process first page issues - don't limit the number of issues
        processed_issues = process_issues(owner, repo_name, issues, topic)

        # Check if there are more pages (GitHub returns 100 items per page max)
        page = 2
        max_pages = 10  # Fetch up to 10 pages (1000 issues) per repository

        # If there are likely more pages (full page of 100 items)
        while len(issues) == 100 and page <= max_pages:
            try:
                # Fetch the next page
                await rate_limiter.async_wait("core")
                _, _, page_issues = await get_issues_page_async(
                    repo_info, page, 100, headers, rate_limiter
                )

                if page_issues:
                    # Process all issues from this page
                    new_issues = process_issues(owner, repo_name, page_issues, topic)
                    processed_issues.extend(new_issues)
                    print(
                        f"Collected {len(new_issues)} additional issues from {owner}/{repo_name} (page {page})"
                    )

                    # If this page wasn't full, we've reached the end
                    if len(page_issues) < 100:
                        break
                else:
                    # No more issues
                    break

                # Move to next page
                page += 1

            except Exception as e:
                print(f"Error processing page {page} for {owner}/{repo_name}: {e}")
                break

        print(
            f"Collected total of {len(processed_issues)} issues from {owner}/{repo_name}"
        )
        return processed_issues
    except Exception as e:
        print(f"Error processing repository {owner}/{repo_name}: {e}")
        return []


def collect_github_issues_by_topic(
    topics=None,
    num_topics=5,
    repos_per_topic=3,
    max_issues_per_repo=50,
    github_token=None,
    max_workers=5,
    min_stars=100,
    output_file=None,
) -> Dataset:
    """Synchronous wrapper for collect_github_issues_by_topic_async."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(
            collect_github_issues_by_topic_async(
                topics=topics,
                num_topics=num_topics,
                repos_per_topic=repos_per_topic,
                max_issues_per_repo=max_issues_per_repo,
                github_token=github_token,
                max_workers=max_workers,
                min_stars=min_stars,
                output_file=output_file,
            )
        )
    finally:
        loop.close()


def push_to_mlfoundations_dev(dataset_dict, hf_token=None):
    """
    Push the dataset to mlfoundations-dev/github-issues on Hugging Face Hub.

    Parameters:
    - dataset_dict: The dataset to push
    - hf_token: Hugging Face API token (if None, will try to read from environment)

    Returns:
    - URL to the dataset on Hugging Face Hub
    """
    # Get token from environment if not provided
    if hf_token is None:
        hf_token = os.environ.get("HF_TOKEN")
        if not hf_token:
            print("No Hugging Face token provided or found in environment.")
            print("Saving dataset locally only.")
            local_path = "./github-issues-dataset"
            dataset_dict.save_to_disk(local_path)
            return local_path

    repo_id = "mlfoundations-dev/github-issues"

    try:
        print(f"Pushing dataset to Hugging Face Hub: {repo_id}")
        dataset_dict.push_to_hub(repo_id=repo_id, token=hf_token)

        hub_url = f"https://huggingface.co/datasets/{repo_id}"
        print(f"Dataset successfully pushed to: {hub_url}")
        return hub_url
    except Exception as e:
        print(f"Error pushing to Hugging Face Hub: {e}")

        # Save locally as fallback
        local_path = "./github-issues-dataset"
        dataset_dict.save_to_disk(local_path)
        print(f"Dataset saved locally to {local_path}")
        return local_path


# Add a function to check GitHub API status
def check_github_api_status(headers):
    """Check GitHub API status and rate limits"""
    try:
        # Check rate limit endpoint
        response = requests.get(
            "https://api.github.com/rate_limit", headers=headers, timeout=10
        )

        if response.status_code == 200:
            limits = response.json()
            core = limits.get("resources", {}).get("core", {})
            search = limits.get("resources", {}).get("search", {})

            # Calculate time until reset
            core_reset = core.get("reset", 0)
            search_reset = search.get("reset", 0)
            now = time.time()

            core_wait = max(0, core_reset - now)
            search_wait = max(0, search_reset - now)

            print("\n=== GitHub API Status ===")
            print(
                f"Core API: {core.get('remaining', 0)}/{core.get('limit', 0)} requests remaining"
            )
            print(f"Reset in: {core_wait/60:.1f} minutes")
            print(
                f"Search API: {search.get('remaining', 0)}/{search.get('limit', 0)} requests remaining"
            )
            print(f"Reset in: {search_wait/60:.1f} minutes")

            # Return True if we have enough remaining calls
            return core.get("remaining", 0) > 50 and search.get("remaining", 0) > 10
        else:
            print(f"Failed to check API status: {response.status_code}")
            return False
    except Exception as e:
        print(f"Error checking GitHub API status: {e}")
        return False


def get_github_repo_dataset(
    dataset: Dataset,
    topics_column: str = "topics",
    repos_per_topic=3,
    max_issues_per_repo=50,
    github_token=None,
    max_workers=5,
    min_stars=100,
    output_file=None,
) -> Dataset:
    # Set a default token for testing (you should replace this with your own token)
    # This is just for convenience during development
    default_token = None  # Removed hardcoded token for security

    # Check for GitHub token
    github_token = get_github_token() or default_token

    if not github_token:
        print("\n" + "=" * 80)
        print("WARNING: No GitHub token found. You will likely hit rate limits.")
        print("Create a token at https://github.com/settings/tokens")
        print("Then either:")
        print(
            "1. Set it as an environment variable: export GITHUB_TOKEN=your_token_here"
        )
        print("2. Save it to ~/.github_token file")
        print("=" * 80 + "\n")

        # Create token file option
        try:
            create_token = (
                input("Would you like to create a token file now? (y/n): ")
                .strip()
                .lower()
            )
            if create_token == "y":
                token = input("Enter your GitHub token: ").strip()
                if token:
                    token_file = os.path.expanduser("~/.github_token")
                    with open(token_file, "w") as f:
                        f.write(token)
                    print(f"Token saved to {token_file}")
                    github_token = token
                else:
                    print("No token entered.")

            if not github_token:
                response = input("Continue without a token? (y/n): ").strip().lower()
                if response != "y":
                    print("Exiting. Please set up a GitHub token and try again.")
                    exit(0)
        except:
            pass  # If running non-interactively, continue anyway
    else:
        # Check API status with the token
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"Bearer {github_token}",
        }
        if not check_github_api_status(headers):
            print(
                "\nWARNING: GitHub API rate limits may be too low to complete the task."
            )
            try:
                response = input("Continue anyway? (y/n): ").strip().lower()
                if response != "y":
                    print("Exiting. Please try again later when rate limits reset.")
                    exit(0)
            except:
                pass  # If running non-interactively, continue anyway

    # Create output directory if it doesn't exist
    output_dir = "./github_issues_data"
    os.makedirs(output_dir, exist_ok=True)

    # Generate timestamp for filenames if no output file specified
    if output_file is None:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"{output_dir}/github_issues_{timestamp}.json"

    # Set max_workers based on input parameter
    max_workers = max_workers if github_token else 2

    # Get topics from dataset
    topics = list(set(dataset[topics_column]))

    try:
        # Collect GitHub issues by topic using passed parameters
        github_dataset = collect_github_issues_by_topic(
            topics=topics,
            repos_per_topic=repos_per_topic,
            max_issues_per_repo=max_issues_per_repo,
            min_stars=min_stars,
            github_token=github_token,
            max_workers=max_workers,
            output_file=output_file,
        )

        return github_dataset
    except KeyboardInterrupt:
        print("\n\nScript interrupted by user. Exiting gracefully...")

        # Try to load any intermediate results
        intermediate_file = f"{os.path.splitext(output_file)[0]}_intermediate.json"
        if os.path.exists(intermediate_file):
            print(f"Found intermediate results at {intermediate_file}")
            print("You can use these results for partial data recovery.")
    except Exception as e:
        print(f"\nAn error occurred: {e}")

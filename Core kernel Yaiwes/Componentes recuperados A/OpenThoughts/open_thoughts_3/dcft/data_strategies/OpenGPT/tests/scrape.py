# Standard library imports
import random
import re
import string
import time
from concurrent.futures import ThreadPoolExecutor

# Third-party imports
import requests
from bs4 import BeautifulSoup
from datasets import Dataset, concatenate_datasets


def scrape_nhs_conditions_descriptions() -> Dataset:
    dataset = scrape_nhs_conditions_urls()
    urls = dataset["url"]
    topics = dataset["topic"]

    # Good way to get your IP banned is setting this high.
    with ThreadPoolExecutor(max_workers=4) as executor:
        unfiltered = list(
            executor.map(scrape_nhs_conditions_description_from_url, topics, urls)
        )

    rows = list(filter(None, unfiltered))
    print(f"Filtered out {len(unfiltered) - len(rows)} empty results")

    dataset = Dataset.from_list(rows)
    print(f"Got {len(dataset)} descriptions in total")

    return dataset


def scrape_nhs_conditions_urls() -> Dataset:
    url = "https://www.nhs.uk/conditions/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.google.com/",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

    session = requests.Session()
    max_retries = 5
    for attempt in range(max_retries):
        try:
            response = session.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            break
        except requests.RequestException as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                wait_time = random.uniform(1, 5)
                print(f"Waiting for {wait_time:.2f} seconds before retrying...")
                time.sleep(wait_time)
            else:
                print("Max retries reached. Unable to fetch the webpage.")
                return Dataset.from_dict({"links": []})

    soup = BeautifulSoup(response.content, "html.parser")

    selectors = [
        "ul.nhsuk-list-nav li a",
        ".nhsuk-list-nav li a",
        'a[href^="/conditions/"]',
        ".nhsuk-list--letter a",
    ]

    all_datasets = []

    for selector in selectors:
        urls = soup.select(selector)
        print(f"Selector '{selector}' found {len(urls)} urls")
        urls_col = [f"https://www.nhs.uk{url['href']}" for url in urls]
        topics_col = [url.text.strip() for url in urls]
        all_datasets.append(Dataset.from_dict({"url": urls_col, "topic": topics_col}))

    all_urls = concatenate_datasets(all_datasets)
    print(f"Found {len(all_urls)} urls in total")
    return all_urls


def scrape_nhs_conditions_description_from_url(topic, url):
    # Ignore these urls as they are not conditions
    ban_list = [
        "https://www.nhs.uk/conditions/social-care-and-support-guide/",
        "https://www.nhs.uk/conditions/",
    ]
    for letter in string.ascii_uppercase:
        ban_list.append(f"https://www.nhs.uk/conditions/#{letter}")
    if url in ban_list:
        return None

    # Try to scrape the description
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")

        text = soup.find("article").get_text()
        cleaned_text = clean_text_preserve_structure(text)
        print(f"Successfully scraped description from {url}")

        return {"topic": topic, "url": url, "text": cleaned_text}
    except Exception as e:
        print(f"Error scraping {url}: {e}")

    print(f"Failed to scrape description from {url}")


def clean_text_preserve_structure(text):
    # Remove excessive newlines (keep max of 2 for paragraph separation)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Split into paragraphs (only split on double newlines)
    paragraphs = [p for p in text.split("\n\n") if p.strip()]

    # Patterns to identify review-related content
    review_patterns = [r"Media last reviewed:", r"Page last reviewed:"]

    # Clean each paragraph and filter out unwanted content
    cleaned_paragraphs = []
    for para in paragraphs:
        # Skip if paragraph matches any review pattern
        if any(pattern.lower() in para.lower() for pattern in review_patterns):
            break

        # Remove extra spaces while preserving single newlines
        lines = para.split("\n")
        cleaned_lines = []
        for line in lines:
            # Remove extra spaces within each line
            cleaned_line = " ".join(line.split())
            if cleaned_line:  # Only add non-empty lines
                cleaned_lines.append(cleaned_line)

        # Join lines back with single newlines
        cleaned_para = "\n".join(cleaned_lines)

        # Add proper spacing after periods (only within lines, not at line breaks)
        cleaned_para = re.sub(r"\.(?=[A-Z])", ". ", cleaned_para)

        if cleaned_para.strip():
            cleaned_paragraphs.append(cleaned_para.strip())

    # Join paragraphs with double newlines
    return "\n\n".join(cleaned_paragraphs)

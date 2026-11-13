import logging
import math
import os
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Union

import py7zr
import requests
from bs4 import BeautifulSoup
from datasets import Dataset
from tqdm import tqdm


def clean_unicode_surrogates(texts: List[str]) -> List[str]:
    """
    Clean Unicode surrogate characters from a list of strings.

    Args:
        texts (List[str]): List of strings to clean

    Returns:
        List[str]: New list with cleaned strings

    Raises:
        TypeError: If input is not a list of strings

    Examples:
        >>> texts = ['hello 👋', 'test\udcff', 'good\udc00bye']
        >>> clean_unicode_surrogates(texts)
        ['hello 👋', 'test', 'goodbye']
    """
    if not isinstance(texts, list):
        raise TypeError(f"Expected list, got {type(texts)}")

    cleaned_texts = []
    for text in texts:
        if not isinstance(text, str):
            raise TypeError(f"Expected string elements, got {type(text)}")
        cleaned_texts.append(text.encode("utf-8", "ignore").decode("utf-8"))

    return cleaned_texts


def download_file(url: str, save_path: str) -> bool:
    """
    Download a file from a URL and save it to the specified path.

    Args:
        url (str): The URL of the file to download.
        save_path (str): The local path where the downloaded file should be saved.

    Returns:
        bool: True if download was successful, False otherwise.

    Raises:
        Exception: If there is an error during the download process.
    """
    try:
        logging.info("Downloading file")
        response = requests.get(url, stream=True)
        response.raise_for_status()

        with open(save_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        logging.info(f"Error downloading file: {e}")
        return False


def extract_7z(archive_path: str, extract_path: str) -> bool:
    """
    Extract a 7z archive to the specified path.

    Args:
        archive_path (str): Path to the 7z archive file.
        extract_path (str): Directory path where the archive contents should be extracted.

    Returns:
        bool: True if extraction was successful, False otherwise.

    Raises:
        Exception: If there is an error during the extraction process.
    """
    try:
        logging.info("Extracting file")
        with py7zr.SevenZipFile(archive_path, "r") as archive:
            archive.extractall(extract_path)
        return True
    except Exception as e:
        logging.info(f"Error extracting archive: {e}")
        return False


def find_xml_file(directory: str, filename: str) -> Optional[str]:
    """
    Find an XML file in the directory tree.

    Args:
        directory (str): Root directory to start the search.
        filename (str): Name of the XML file to find.

    Returns:
        Optional[str]: Full path to the found XML file, or None if not found.
    """
    for root, _, files in os.walk(directory):
        if filename in files:
            return os.path.join(root, filename)
    return None


def get_line_count(xml_path: str) -> int:
    """
    Count the number of lines in an XML file.

    Args:
        xml_path (str): Path to the XML file.

    Returns:
        int: Total number of lines in the file.
    """
    with open(xml_path, "rb") as f:
        # Count raw lines using binary read for better performance
        lines = sum(1 for _ in f)
    return lines


def extract_post_history(
    xml_path: str, split_index: int, split_factor: int
) -> List[str]:
    """
    Extract post history entries from XML file.

    Args:
        xml_path (str): Path to the XML file containing post history.
        split_index (int): Index of the chunk to process (0-based).
        split_factor (int): Number of chunks to split the processing into.

    Returns:
        List[str]: List of extracted post history text entries.

    Notes:
        The function processes only a chunk of the XML file based on split_index
        and split_factor to enable parallel processing.
    """
    # Skip until start of our chunk
    total_lines = get_line_count(xml_path)
    batch_size = math.ceil(total_lines / split_factor)

    post_histories = []
    current_index = 0
    start_index = split_index * batch_size
    logging.info(f"Total Lines: {total_lines}")
    logging.info(f"XML Path: {xml_path}")
    for _, elem in tqdm(
        ET.iterparse(xml_path, events=("end",)), total=start_index + batch_size
    ):
        if elem.tag == "row":
            if current_index >= start_index:
                if len(post_histories) >= batch_size:
                    break
                if elem.get("PostTypeId") != "1":
                    continue
                post_histories.append(
                    BeautifulSoup(elem.get("Body"), "html.parser").get_text()
                )
            elem.clear()
            current_index += 1
    return post_histories


def process_archive(
    url: str, split_index: int, split_factor: int, xml_filename: str = "Posts.xml"
) -> List[str]:
    """
    Download, extract, and process the 7z archive containing post history.

    Args:
        url (str): URL of the 7z archive to download.
        split_index (int): Index of the chunk to process (0-based).
        split_factor (int): Number of chunks to split the processing into.
        xml_filename (str, optional): Name of the XML file to process. Defaults to "Posts.xml".

    Returns:
        List[str]: List of processed post histories from the specified chunk.

    Notes:
        The function handles the complete pipeline from downloading the archive
        to extracting post histories, operating on a specific chunk of data.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        # Download the 7z file
        archive_path = os.path.join(temp_dir, "archive.7z")
        logging.info(f"Downloading archive from {url}...")
        if not download_file(url, archive_path):
            return []

        # Extract the archive
        extract_path = os.path.join(temp_dir, "extracted")
        os.makedirs(extract_path, exist_ok=True)
        logging.info("Extracting archive...")
        if not extract_7z(archive_path, extract_path):
            return []

        # Find and process the XML file
        xml_path = find_xml_file(extract_path, xml_filename)
        if not xml_path:
            logging.info(f"Could not find {xml_filename} in the archive")
            return []

        logging.info(f"Processing {xml_filename}...")
        return extract_post_history(xml_path, split_index, split_factor)


def analyze_post_history(
    url: str, split_index: int = 0, split_factor: int = 15
) -> Dataset:
    """
    Analyze post histories from a Stack Exchange data dump.

    Args:
        url (str): URL of the Stack Exchange data dump archive.
        split_index (int, optional): Index of the chunk to process (0-based). Defaults to 0.
        split_factor (int, optional): Number of chunks to split the processing into. Defaults to 15.

    Returns:
        Dataset: A HuggingFace Dataset containing the processed post histories.

    Notes:
        The function splits the processing into chunks to enable parallel processing
        of large datasets. Each chunk processes approximately 1/split_factor of the
        total data.
    """
    all_prompts = process_archive(url, split_index, split_factor, "Posts.xml")
    dataset = Dataset.from_dict({"instruction": clean_unicode_surrogates(all_prompts)})
    return dataset

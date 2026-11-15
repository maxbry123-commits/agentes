import os
from pathlib import Path
from setuptools import setup, find_packages

VERSION = "0.0.1"

common_setup_kwargs = {
    "version": VERSION,
    "name": "opencoconut",
    "author": "Casper Hansen",
    "license": "Apache 2.0",
    "python_requires": ">=3.8.0",
    "description": "OpenCoconut intends to replicate the Chain of Continuous Thought (COCONUT) to implement their novel latent reasoning paradigm.",
    "long_description": (Path(__file__).parent / "README.md").read_text(
        encoding="UTF-8"
    ),
    "long_description_content_type": "text/markdown",
    "url": "https://github.com/casper-hansen/OpenCoconut",
    "keywords": ["opencoconut", "coconut"],
    "platforms": ["linux", "windows"],
    "classifiers": [
        "Natural Language :: English",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
}

requirements = [
    "torch",
    "transformers",
    "accelerate",
    "datasets",
]

setup(
    packages=find_packages(),
    install_requires=requirements,
    **common_setup_kwargs,
)
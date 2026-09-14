# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys

# Assuming conf.py is in docs/source/, the project root directory (containing isek/) is ../../
sys.path.insert(0, os.path.abspath("../../"))

project = "ISEK"
copyright = "2025, ISEK Team"
author = "Moshi"
release = "0.2.0"
version = "0.2.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",  # Core: generate docs from docstrings
    "sphinx.ext.napoleon",  # Support Google/NumPy style docstrings
    "sphinx.ext.intersphinx",  # Link to other libraries' docs (like Python)
    "sphinx.ext.viewcode",  # Add source code links
    "sphinx.ext.githubpages",  # Support GitHub Pages deployment
    # 'sphinx_rtd_theme',     # If using ReadTheDocs theme
]

templates_path = ["_templates"]
exclude_patterns = []

language = "English"

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# html_theme = 'alabaster'
html_static_path = ["_static"]
intersphinx_mapping = {"python": ("https://docs.python.org/3", None)}

# import sphinx_rtd_theme # If using
# html_theme = 'sphinx_rtd_theme' # or 'alabaster', 'pydata_sphinx_theme', etc.
html_permalinks_icon = "<span>#</span>"
html_theme = "sphinxawesome_theme"
# html_theme_path = [sphinx_rtd_theme.get_html_theme_path()] # If path needs to be specified

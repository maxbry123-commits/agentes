************
Installation
************

This guide covers how to install the ISEK framework and its dependencies.

Prerequisites
=============

*   **Python 3.10 or higher** - ISEK requires modern Python features
*   **Node.js 18+** - Required for P2P networking functionality
*   **Git** - For development installations

Check your versions:

.. code-block:: bash

   python --version
   node --version
   git --version

Standard Installation (Recommended)
===================================

We strongly recommend installing ISEK within a Python virtual environment to manage dependencies effectively.

1.  **Create and activate a virtual environment:**

    .. code-block:: bash

       # Create virtual environment
       python -m venv .venv

       # Activate the environment
       # On Linux/macOS:
       source .venv/bin/activate
       # On Windows (Command Prompt):
       # .venv\Scripts\activate.bat
       # On Windows (PowerShell):
       # .venv\Scripts\Activate.ps1

2.  **Install ISEK:**

    .. code-block:: bash

       pip install isek

3.  **Run ISEK setup (Required):**

    .. code-block:: bash

       isek setup

    This command installs JavaScript dependencies and configures the P2P networking components.

Installation Verification
========================

Verify your installation:

.. code-block:: bash

   isek --help
   isek example list

You should see the ISEK CLI help and a list of available examples.

Installation from Source (Development)
=====================================

For development or to use the latest features:

1.  **Clone the repository:**

    .. code-block:: bash

       git clone https://github.com/your-org/isek.git
       cd isek

2.  **Install in editable mode:**

    .. code-block:: bash

       pip install -e .
       isek setup

    The `-e` flag installs in "editable" mode, so code changes are reflected immediately.

Troubleshooting
==============

**macOS: `faiss-cpu` Installation Error**

If you encounter `faiss-cpu` errors on macOS:

.. code-block:: bash

   brew install swig
   pip install isek

**Node.js Dependencies Issues**

If P2P features don't work:

.. code-block:: bash

   cd isek/protocol/p2p
   npm install
   cd ../../..
   isek setup

**Permission Errors**

On Linux/macOS, if you get permission errors:

.. code-block:: bash

   pip install --user isek
   # or use sudo (not recommended)
   # sudo pip install isek

Next Steps
==========

After installation:

1.  Configure your LLM API keys (see :doc:`quickstart`)
2.  Try running an example: `isek example run lv1_single_agent`
3.  Explore the :doc:`user_guide/index` for advanced usage

For issues or questions, please open an issue on GitHub or contact the ISEK team.
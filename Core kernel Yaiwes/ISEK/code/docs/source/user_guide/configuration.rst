***************
Configuration
***************

ISEK uses environment variables and Python-based configuration to simplify setup and deployment. This approach provides flexibility while maintaining security for sensitive credentials like API keys.

Basic Structure
===============

ISEK configuration is primarily handled through:

* **Environment variables** (in a `.env` file) for API keys and sensitive information
* **Python code** for agent and model configuration
* **Registry settings** for agent discovery and networking

Environment Configuration
=========================

Create a `.env` file in your project root:

.. code-block:: bash

   # OpenAI Configuration
   OPENAI_API_KEY=your_openai_api_key
   OPENAI_BASE_URL=https://api.openai.com/v1
   OPENAI_MODEL_NAME=gpt-4o-mini

   # Alternative Models (via LiteLLM)
   ANTHROPIC_API_KEY=your_anthropic_key
   GOOGLE_API_KEY=your_google_key
   AZURE_API_KEY=your_azure_key
   AZURE_API_BASE=your_azure_endpoint

   # Registry Configuration
   ETCD_HOST=127.0.0.1
   ETCD_PORT=2379

Example ``.env`` File
=====================

Store sensitive credentials safely in a ``.env`` file (this file is typically *not* committed to version control):

.. code-block:: bash

   # This file is usually loaded by a library like python-dotenv in your application
   OPENAI_API_KEY="your-actual-openai-api-key"
   OPENAI_BASE_URL="https://api.openai.com/v1" # Optional, if not using default
   OPENAI_MODEL_NAME="gpt-4o-mini" # Can be overridden by YAML

Agent Configuration
===================

The ``agent`` section defines basic behaviors:

* ``debug_level``: Sets the logging verbosity (e.g., "DEBUG", "INFO").
* ``persona_path``: Specifies the file path to load your agent's persona definition.

Distributed Mode
================

Configure network-enabled agents:

* ``distributed.enabled``: Set ``true`` for network-enabled agents; ``false`` for single, local agents.
* ``distributed.server``: If ``enabled`` is ``true``, this nested section defines the ``host`` and ``port`` your agent listens on for peer communication.

LLM and Embeddings
==================

Specify your language model (LLM) and embedding model:

* **LLM settings** (``llm`` section):
    * ``mode``: Specifies the LLM provider (e.g., "openai").
    * Provider-specific section (e.g., ``llm.openai``): Contains parameters like ``model_name``, and potentially ``api_key`` (though environment variables are preferred for keys).
* **Embedding settings** (``embedding`` section):
    * ``mode``: Specifies the embedding provider.
    * Provider-specific section (e.g., ``embedding.openai``): Contains parameters like ``model_name``.

Registry Configuration
======================

The registry is used by distributed agents for peer discovery:

* ``registry.mode``: Set to either ``"etcd"`` (for a production-grade distributed registry) or ``"isek_center"`` (for a simpler, built-in demo registry).
* ``registry.etcd`` or ``registry.isek_center``: Nested sections containing specific connection parameters for the chosen registry type.

Python Configuration
====================

Configure agents programmatically:

.. code-block:: python

   from dotenv import load_dotenv
   from isek.agent.isek_agent import IsekAgent
   from isek.models.openai import OpenAIModel
   from isek.models.litellm import LiteLLMModel

   # Load environment variables
   load_dotenv()

   # OpenAI Agent
   openai_agent = IsekAgent(
       name="OpenAI Agent",
       model=OpenAIModel(model_id="gpt-4o-mini"),
       description="An agent using OpenAI"
   )

   # LiteLLM Agent (for other models)
   litellm_agent = IsekAgent(
       name="Claude Agent",
       model=LiteLLMModel(model_id="claude-3-sonnet-20240229"),
       description="An agent using Claude"
   )


Best Practices
==============

* Always store sensitive information, such as API keys, in a secure ``.env`` file, and ensure this file is in your ``.gitignore``.
* Your application code (e.g., `IsekConfig` or model initializers) should be responsible for loading values from environment variables (e.g., using `os.environ.get("VARIABLE_NAME")`). Standard YAML loaders do not automatically interpolate `${VARIABLE_NAME}` syntax; this requires custom logic or a specialized YAML loader.
* Keep persona definitions and potentially large model configurations organized.
* Use the ``debug_level`` in the agent configuration for detailed logging during development.
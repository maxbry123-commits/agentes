************
Agents
************

In ISEK, an **Agent** is an intelligent entity that autonomously acts, communicates, collaborates, and learns within a decentralized network. Each agent combines reasoning, tool usage, memory, and distinct personas to perform tasks and achieve goals.

Agent Architecture
==================

An ISEK Agent is structured into several key components:

* **Agent Core**: Responsible for internal reasoning, decision-making, task execution, and memory management
* **LLM Backend**: Provides intelligence through various language models (OpenAI, Claude, etc.)
* **Communication Layer**: Manages networking aspects such as registration, peer discovery, and message exchange
* **Tool Integration**: Enables agents to use external APIs, scripts, and services

This modular approach ensures flexible deployment—agents think locally but coordinate globally.

Creating an Agent
=================

Basic agent creation with OpenAI:

.. code-block:: python

   from isek.agent.isek_agent import IsekAgent
   from isek.models.openai import OpenAIModel

   agent = IsekAgent(
       name="Research Assistant",
       model=OpenAIModel(model_id="gpt-4o-mini"),
       description="An AI research assistant specializing in machine learning",
       instructions=["Be thorough in research", "Cite sources when possible"],
       success_criteria="Provide accurate, well-researched information"
   )

Using LiteLLM for other models:

.. code-block:: python

   from isek.agent.isek_agent import IsekAgent
   from isek.models.litellm import LiteLLMModel

   agent = IsekAgent(
       name="Code Assistant",
       model=LiteLLMModel(model_id="claude-3-sonnet-20240229"),
       description="A coding assistant with expertise in Python and web development",
       instructions=["Write clean, well-documented code", "Explain your reasoning"],
       success_criteria="Generate working, maintainable code"
   )

Agent Capabilities
==================

ISEK agents provide powerful built-in features:

* **Intelligent Reasoning**: Advanced reasoning through integrated LLMs
* **Tool Integration**: Use external APIs, scripts, and services via FastMCP
* **Memory Management**: Remember interactions and maintain context
* **Peer Discovery**: Find and connect with other agents in the network
* **Collaborative Tasks**: Work together with other agents to solve complex problems

Running an Agent
================

Simple interaction:

.. code-block:: python

   response = agent.run("What are the latest trends in AI?")
   print(response)

Interactive CLI mode:

.. code-block:: python

   agent.run_cli()  # Starts interactive command-line interface

Multi-Agent Collaboration
=========================

Agents can collaborate with each other in teams:

.. code-block:: python

   from isek.team.isek_team import IsekTeam

   # Create a team of specialized agents
   team = IsekTeam(
       name="Research Team",
       agents=[agent1, agent2, agent3],
       description="A collaborative research team"
   )

   # Run a collaborative task
   result = team.run("Conduct a comprehensive analysis of quantum computing")
   print(result)

Memory and Context
==================

Agents maintain memory of interactions:

.. code-block:: python

   # First interaction
   response1 = agent.run("What is machine learning?")
   
   # Second interaction - agent remembers context
   response2 = agent.run("Can you elaborate on the types you mentioned?")
   
   # Agent will reference the previous conversation

Tool Integration
================

Agents can use tools through FastMCP integration:

.. code-block:: python

   from isek.tools.fastmcp_toolkit import FastMCPToolkit

   # Agent with tool capabilities
   agent_with_tools = IsekAgent(
       name="Data Analyst",
       model=OpenAIModel(model_id="gpt-4o-mini"),
       description="A data analysis specialist",
       tools=FastMCPToolkit()  # Enables tool usage
   )

   # Agent can now use tools for data analysis, web searches, etc.
   response = agent_with_tools.run("Analyze the stock market data for AAPL")

Best Practices
==============

* **Clear Instructions**: Provide specific, actionable instructions for your agent
* **Appropriate Model Selection**: Choose models based on your use case (speed vs. quality)
* **Memory Management**: Leverage agent memory for context-aware interactions
* **Tool Integration**: Enable tools for agents that need to interact with external systems
* **Team Formation**: Use teams for complex tasks requiring multiple perspectives

Advanced Configuration
======================

Customize agent behavior:

.. code-block:: python

   agent = IsekAgent(
       name="Custom Agent",
       model=OpenAIModel(model_id="gpt-4o-mini"),
       description="A highly customized agent",
       instructions=[
           "Always think step by step",
           "Provide detailed explanations",
           "Ask clarifying questions when needed"
       ],
       success_criteria="User receives comprehensive, accurate responses",
       temperature=0.7,  # Control creativity vs. consistency
       max_tokens=2000   # Limit response length
   )
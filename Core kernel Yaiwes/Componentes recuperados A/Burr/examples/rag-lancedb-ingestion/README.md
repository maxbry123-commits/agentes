<!--
     Licensed to the Apache Software Foundation (ASF) under one
     or more contributor license agreements.  See the NOTICE file
     distributed with this work for additional information
     regarding copyright ownership.  The ASF licenses this file
     to you under the Apache License, Version 2.0 (the
     "License"); you may not use this file except in compliance
     with the License.  You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

     Unless required by applicable law or agreed to in writing,
     software distributed under the License is distributed on an
     "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
     KIND, either express or implied.  See the License for the
     specific language governing permissions and limitations
     under the License.
-->

# Burr RAG with LanceDB and dlt document ingestion

This example shows how to build a chatbot with RAG over Substack blogs (or any RSS feed) stored into LanceDB.

![burr ui](burr-ui.gif)

> Burr UI brings a new level of observability to your RAG application via OpenTelemetry

Burr + [LanceDB](https://lancedb.github.io/lancedb/) constitute a powerful, but lightweight combo to build retrieval-augmented generative (RAG) agents. Burr allows to define complex agents in an easy-to-understand and debug manner. It also provides all the right features to help you productionize agents including: monitoring, storing interactions, streaming, and a fully-featured open-source UI.

LanceDB makes it easy to swap embedding providers, and hides this concern from the Burr application layer. For this example, we'll be using [OpenAI](https://github.com/openai/openai-python) for embedding and response generation.

By leveraging the [Burr integration with OpenTelemetry](https://blog.dagworks.io/p/building-generative-ai-agent-based), we get full visibility into the OpenAI API requests/responses and the LanceDB operations for free.

To ingest data, we use [dlt and its LanceDB integration](https://dlthub.com/devel/dlt-ecosystem/destinations/lancedb), which makes it very simple to query, embed, and store blogs from the web into LanceDB tables.

## Content

- `notebook.ipynb` contains a tutorial
- `application.py` has the `burr` code for the chatbot
- `ingestion.py` has the `dlt` code for document ingestion
- `utils.py` contains functions utility functions to setup `OpenTelemetry` instrumentation and environment variables

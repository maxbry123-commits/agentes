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

# Divide and Conquer

A single agent can usually operate effectively using a handful of tools within a single domain, but even using powerful models like `gpt-4`, it can be less effective at using many tools.

One way to approach complicated tasks is through a "divide-and-conquer" approach: create a "specialized agent" for each task or domain and route tasks to the correct "expert". This means that each agent can become a sequence of LLM calls that chooses how to use a specific "tool".

The examples we link to below are inspired by the paper [AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation by Wu, et. al.](https://arxiv.org/abs/2308.08155).
They can be found in [this part of our repository](https://github.com/apache/burr/tree/main/examples/multi-agent-collaboration).

![](./_divide-and-conquer.png)

We provide two implementations of this idea: with [Hamilton](https://github.com/apache/burr/tree/main/examples/multi-agent-collaboration/hamilton) and with [LangChain LCEL](https://github.com/apache/burr/tree/main/examples/multi-agent-collaboration/lcel). From Burr's standpoint, both look similar and you're free to use your preferred framework within an `action`.

## With Hamilton

<a target="_blank" href="https://colab.research.google.com/github/apache/burr/blob/main/examples/multi-agent-collaboration/hamilton/notebook.ipynb">
    <img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/>
</a>



## With LangChain Expression Language (LCEL)

<a target="_blank" href="https://colab.research.google.com/github/apache/burr/blob/main/examples/multi-agent-collaboration/lcel/notebook.ipynb">
    <img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/>
</a>

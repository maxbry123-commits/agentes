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

# Tool-calling

This example shows the basic tool-calling design pattern for agents.

While this leverages the [OpenAI API](https://platform.openai.com/docs/guides/function-calling), the lessons are the same whether you use different tool-calling APIs (E.G. [Anthropic](https://docs.anthropic.com/en/docs/build-with-claude/tool-use)), or general structured outputs (E.G. with [instructor](https://useinstructor.com/)).

Rather than explain the code here, we direct you to the [blog post](https://blog.dagworks.io/p/agentic-design-pattern-1-tool-calling)

# Files

- [application.py](application.py) -- contains code for calling tools + orchestrating them
- [notebook.ipynb](notebook.ipynb) -- walks you through the example with the same code
- [requirements.txt] -- install this to get the right environment

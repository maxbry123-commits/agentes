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

# Deep Researcher

## Introduction

The structure of the research assistant is taken from a [langchain and langgraph example](https://github.com/langchain-ai/local-deep-researcher). It is rewritten here in the Burr framework in `application.py`.

![Deep Researcher](statemachine.png)

The helper code in `prompts.py` and `utils.py` is directly taken from the original deep researcher codebase. The MIT license for the code is included in both those files.

## Prerequisites

Set the configuration variables at the beginning of the main section of `application.py`.

Then install Python modules
```sh
pip install -r requirements.txt
```

You will need accounts for [Tavily search](https://tavily.com/) and the [OpenAI API](https://platform.openai.com/docs/overview). Once you have those accounts, set the environment variables TAVILY_API_KEY and OPENAI_API_KEY and run the script.

```sh
export OPENAI_API_KEY="YOUR_OPENAI_KEY"
export TAVILY_API_KEY="YOUR_TAVILY_API_KEY"
python application.py
```

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

# Conversational RAG examples
Here we curate different examples of how to build a Conversational RAG agent using different approaches/backends.

## [Simple Example](simple_example/)
This example demonstrates how to build a conversational RAG agent with "memory".

The "memory" here is stored in state, which Burr then can help you track,
manage, and introspect.


## [Graph DB Example](graph_db_example/)
This demo illustrates how to build a RAG Q&A AI agent over the [UFC stats dataset](https://www.kaggle.com/datasets/rajeevw/ufcdata).
This one uses a Knowledge Graph that is stored in [FalkorDB](https://www.falkordb.com/) to query for
information about UFC fighters and fights.

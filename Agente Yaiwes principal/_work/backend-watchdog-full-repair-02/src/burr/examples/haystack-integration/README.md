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

# Haystack + Burr integration

Haystack is a Python library to build AI pipelines. It assembles `Component` objects into a `Pipeline`, which is a graph of operations. One benefit of Haystack is that it provides many pre-built components to manage documents and interact with LLMs.

This notebook shows how to convert a Haystack `Component` into a Burr `Action` and a `Pipeline` into a `Graph`. This allows you to integrate Haystack with Burr and leverage other Burr and Burr UI features!

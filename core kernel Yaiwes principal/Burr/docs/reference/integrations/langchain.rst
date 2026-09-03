..
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


---------
Langchain
---------

Burr works out of the box with langchain, as Burr delegates to any python code.

There are multiple examples of Burr leveraging langchain, including:

- `Multi agent collaboration <https://github.com/apache/burr/tree/main/examples/multi-agent-collaboration/lcel>`_
- `LCEL + Hamilton together <https://github.com/apache/burr/tree/main/examples/multi-agent-collaboration/hamilton>`_

Burr also provides custom ser/deserialization for langchain objects. See the following resources:
1. `Example <https://github.com/apache/burr/tree/main/examples/custom-serde>`_
2. :ref:`Custom serialization docs <serde>`
3. `Langchain serialization plugin <https://github.com/apache/burr/blob/main/burr/integrations/serde/langchain.py>`_

We are working on adding more builtin support for LCEL (LCELActions), and considering adding burr callbacks for tracing langgraph in the Burr
UI. If you have any suggestions, please let us know.

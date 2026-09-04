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


================================
SDLC with LLMs
================================
If you're building an LLM-based application, you'll want to follow a slightly different software development lifecycle (SDLC)
than you would for a traditional software project. Here's a rough outline of what that might look like:

.. image:: ../_static/burr_sdlc.png
   :alt: SDLC with LLMs
   :align: center

The two cycles that exist are:

1. App Dev Loop.
2. Test Driven Development Loop.

and you will use one to feed into the other, etc.

Walking through the diagram the SDLC looks like this:

1. Write code with Burr.
2. Use Burr's integrated observability, and trace all parts of your application.
3. With the data collected, you can: (1) annotate what was captured and export it, or (2) create a pytest fixture with it.
4. Create a data set from the annotated data or by running tests.
5. Evaluate the data set.
6. Analyze the results.
7. Either adjust code or prompts, or ship the code.
8. Iterate using one of the loops...

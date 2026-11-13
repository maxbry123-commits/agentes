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


===========
Cheat Sheet
===========

This is a quick overview of Burr's design -- the concepts are explored in more detail in the following sections. Read over this for a very high-level overview, or use this as a cheat sheet later.

- With Burr you write an :ref:`Application <applications>` -- this manages control flow (allowing for automated or user-blocking workflows), :ref:`persistence <state-persistence>` to DBs, logs :ref:`telemetry <tracking>`, and delegates to a variety of plugins/integrations.
- Applications are composed of :ref:`actions <actions>` (functions that write to/read from state), and :ref:`transitions <transitions>` (functions that determine the next action to execute based on state).
- :ref:`State <state>` is immutable and uses the special Burr :py:class:`State <burr.core.state.State>` API. You write to it by applying a state operation (e.g. ``state = state.update(key=value)``, which returns a new state instance with the updated value.
- All other production/debugging concerns are implemented as :ref:`hooks <hooks>`, which are simple callbacks that are called at various points in the application lifecycle (store/retrieve state, log information, etc...).

Note that we did not mention LLMs above at all! That's good -- you want your LLM frameworks to be ever-so-slightly decoupled from them for the best experience (all of AI is just software, plain and simple, after all...).

And that's the basics! Let's dive into the details.

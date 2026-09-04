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


=========
Why Burr?
=========

Why do you need a state machine for your applications? Won't the normal programming constructs suffice?

**Yes, until a point.** Let's take a look at what you need to build a production-level LLM application:

1. **Tracing/telemetry** -- LLMs can be chaotic, and you need visibility into what decisions it made and how long it took to make them.
2. **State persistence** -- thinking about how to save/load your application is a whole other level of infrastructure you need to worry about.
3. **Visualization/debugging** -- when developing you'll want to be able to view what it is doing/did + load up the data at any point
4. **Manage interaction between users/LLM** -- pause for input in certain conditions
5. **Data gathering for evaluation + test generation** -- storing data run in production to use for later analysis/fine-tuning

You can always patch together various frameworks or build it all yourself, but at that point you're going to be spending a lot of time on tasks that
are not related to the core value proposition of your software.

**Burr was built to make these all easier.**

By modeling your application as a state machine of simple python constructs you can have the best of both worlds.
Bring in whatever infrastructure/tooling you want and get all of the above. Burr is meant to start off as an extremely lightweight tool to
make building LLM (+ a wide swath of other) applications easier. The value compounds as you leverage more of the ecosystems, plugins, and additional
features it provides.

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


.. _opentelintegrationref:

--------------
OpenTelemetry
--------------

Burr has two integrations with OpenTelemetry:


1. Burr can log traces to OpenTelemetry
2. Burr can capture any traces logged within an action and log them to OpenTelemetry

See the following resources for more information:

- :ref:`Tracing/OpenTelemetry <opentelref>`
- `Example in the repository <https://github.com/apache/burr/tree/main/examples/opentelemetry>`_
- `Blog post <https://blog.dagworks.io/p/9ef2488a-ff8a-4feb-b37f-1d9a781068ac/>`_
- `OpenTelemetry <https://opentelemetry.io/>`_

Reference for the various useful methods:

.. autoclass:: burr.integrations.opentelemetry.OpenTelemetryBridge
    :members:

.. autofunction:: burr.integrations.opentelemetry.init_instruments

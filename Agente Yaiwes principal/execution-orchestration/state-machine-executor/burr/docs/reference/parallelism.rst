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


.. _parallelismref:

===========
Parallelism
===========

Tools to make sub-actions/sub-graphs easier to work with. Read the docs on :ref:`parallelism` for more information.

.. autoclass:: burr.core.parallelism.RunnableGraph
   :members:

.. autoclass:: burr.core.parallelism.SubGraphTask
   :members:

.. autoclass:: burr.core.parallelism.TaskBasedParallelAction
   :members:

.. autoclass:: burr.core.parallelism.MapActionsAndStates
    :members:

.. autoclass:: burr.core.parallelism.MapActions
    :members:

.. autoclass:: burr.core.parallelism.MapStates
    :members:

.. automethod:: burr.core.parallelism.map_reduce_action

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


=======================
Conditions/Transitions
=======================

.. _transitionref:

Conditions represent choices to move between actions -- these are read by the application builder when executing the graph.
Note that these will always be specified in order -- the first condition that evaluates to ``True`` will be the selected action.

.. autoclass:: burr.core.action.Condition
   :special-members: __and__, __or__, __invert__
   :members:

   .. automethod:: __init__

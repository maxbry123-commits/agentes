# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

from burr.core import State
from burr.core.action import Action


class Placeholder(Action):
    """This is a placeholder action -- you would expect it to break if you tried to run it. It is specifically
    for the following workflow:
    1. Create your state machine out of placeholders to model it
    2. Visualize the state machine
    2. Replace the placeholders with real actions as you see fit
    """

    def __init__(self, reads: list[str], writes: list[str]):
        super().__init__()
        self._reads = reads
        self._writes = writes

    def run(self, state: State) -> dict:
        raise NotImplementedError(
            f"This is a placeholder action and thus you are unable to run. Please implement: {self}!"
        )

    def update(self, result: dict, state: State) -> State:
        raise NotImplementedError(
            f"This is a placeholder action and thus cannot update state. Please implement: {self}!"
        )

    @property
    def reads(self) -> list[str]:
        return self._reads

    @property
    def writes(self) -> list[str]:
        return self._writes

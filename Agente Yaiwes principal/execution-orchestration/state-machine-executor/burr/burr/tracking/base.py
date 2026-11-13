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

import abc

from burr.lifecycle import (
    PostApplicationCreateHook,
    PostEndSpanHook,
    PostRunStepHook,
    PreRunStepHook,
    PreStartSpanHook,
)
from burr.lifecycle.base import (
    DoLogAttributeHook,
    PostEndStreamHook,
    PostStreamItemHook,
    PreStartStreamHook,
)


class SyncTrackingClient(
    PostApplicationCreateHook,
    PreRunStepHook,
    PostRunStepHook,
    PreStartSpanHook,
    PostEndSpanHook,
    DoLogAttributeHook,
    PreStartStreamHook,
    PostStreamItemHook,
    PostEndStreamHook,
    abc.ABC,
):
    """Base class for synchronous tracking clients. All tracking clients must implement from this
    TODO -- create an async tracking client"""

    @abc.abstractmethod
    def copy(self):
        pass


TrackingClient = SyncTrackingClient

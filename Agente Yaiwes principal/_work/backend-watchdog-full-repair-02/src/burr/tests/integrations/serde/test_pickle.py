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

from burr.core import serde, state
from burr.integrations.serde import pickle


class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email


def test_serde_of_pickle_object():
    pickle.register_type_to_pickle(User)
    user = User(name="John Doe", email="john.doe@example.com")
    og = state.State({"user": user, "test": "test"})
    serialized = og.serialize()
    assert serialized == {
        "user": {
            serde.KEY: "pickle",
            "value": b"\x80\x04\x95Q\x00\x00\x00\x00\x00\x00\x00\x8c\x0btest_pi"
            b"ckle\x94\x8c\x04User\x94\x93\x94)\x81\x94}\x94(\x8c\x04na"
            b"me\x94\x8c\x08John Doe\x94\x8c\x05email\x94\x8c\x14john"
            b".doe@example.com\x94ub.",
        },
        "test": "test",
    }
    ng = state.State.deserialize(serialized)
    assert isinstance(ng["user"], User)
    assert ng["user"].name == "John Doe"
    assert ng["user"].email == "john.doe@example.com"

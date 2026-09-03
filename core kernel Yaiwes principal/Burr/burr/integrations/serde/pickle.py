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

# Pickle serde registration
# This is not automatically registered because we want to register
# it based on class type.
import pickle

from burr.core import serde


def register_type_to_pickle(cls):
    """Register a class to be serialized/deserialized using pickle.

    Note: `pickle_kwargs` are passed to the pickle.dumps and pickle.loads functions.

    This will register the passed in class to be serialized/deserialized using pickle.

    .. code-block:: python

        class User:
            def __init__(self, name, email):
                self.name = name
                self.email = email

        from burr.integrations.serde import pickle
        pickle.register_type_to_pickle(User) # this will register the User class to be serialized/deserialized using pickle.


    :param cls: The class to register
    """

    @serde.serialize.register(cls)
    def serialize_pickle(value: cls, pickle_kwargs: dict = None, **kwargs) -> dict:
        """Serializes the value using pickle.

        :param value: the value to serialize.
        :param pickle_kwargs: not required. Optional.
        :param kwargs:
        :return: dictionary of serde.KEY and value
        """
        if pickle_kwargs is None:
            pickle_kwargs = {}
        return {
            serde.KEY: "pickle",
            "value": pickle.dumps(value, **pickle_kwargs),
        }

    @serde.deserializer.register("pickle")
    def deserialize_pickle(value: dict, pickle_kwargs: dict = None, **kwargs) -> cls:
        """Deserializes the value using pickle.

        :param value: the value to deserialize from.
        :param pickle_kwargs: note required. Optional.
        :param kwargs:
        :return: object of type cls
        """
        if pickle_kwargs is None:
            pickle_kwargs = {}
        return pickle.loads(value["value"], **pickle_kwargs)

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

import logging
from typing import List, Optional

import burr.core
from burr.core import Application, Result, State, default, expr
from burr.core.action import action
from burr.core.persistence import SQLLitePersister
from burr.lifecycle import LifecycleAdapter

logger = logging.getLogger(__name__)


@action(reads=["counter"], writes=["counter"])
def counter(state: State) -> State:
    result = {"counter": state["counter"] + 1}
    print(f"counted to {result['counter']}")
    return state.update(**result)


def application(
    count_up_to: int = 10,
    partition_key: str = "demo-user",
    app_id: Optional[str] = None,
    storage_dir: Optional[str] = "~/.burr",
    hooks: Optional[List[LifecycleAdapter]] = None,
) -> Application:
    persister = SQLLitePersister("demos.db", "counter", connect_kwargs={"check_same_thread": False})
    persister.initialize()
    logger.info(
        f"{partition_key} has these prior invocations: {persister.list_app_ids(partition_key)}"
    )
    return (
        burr.core.ApplicationBuilder()
        .with_actions(counter=counter, result=Result("counter"))
        .with_transitions(
            ("counter", "counter", expr(f"counter < {count_up_to}")),
            ("counter", "result", default),
        )
        .with_identifiers(partition_key=partition_key, app_id=app_id)
        .initialize_from(
            persister,
            resume_at_next_action=True,
            default_state={"counter": 0},
            default_entrypoint="counter",
        )
        .with_state_persister(persister)
        .with_tracker(project="demo_counter", params={"storage_dir": storage_dir})
        .with_hooks(*hooks if hooks else [])
        .build()
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app = application(app_id="a7c8e525-58f9-4e84-b4b3-f5b80b5b0d0e")
    action, result, state = app.run(halt_after=["result"])
    app.visualize(
        output_file_path="statemachine.png", include_conditions=True, view=False, format="png"
    )
    print(state["counter"])

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

import random
import time
from typing import Tuple

import cowsay

from burr.core import Action, Application, ApplicationBuilder, State, default, expr
from burr.core.action import action
from burr.lifecycle import PostRunStepHook


class PrintWhatTheCowSaid(PostRunStepHook):
    def post_run_step(self, *, state: "State", action: "Action", **future_kwargs):
        if action.name != "cow_should_say" and state["cow_said"] is not None:
            print(state["cow_said"])


class CowCantSpeakFast(PostRunStepHook):
    def __init__(self, sleep_time: float):
        super(PostRunStepHook, self).__init__()
        self.sleep_time = sleep_time

    def post_run_step(self, *, state: "State", action: "Action", **future_kwargs):
        if action.name != "cow_should_say":  # no need to print if we're not saying anything
            time.sleep(self.sleep_time)


@action(reads=[], writes=["cow_said"])
def cow_said(state: State, say_what: list[str]) -> Tuple[dict, State]:
    said = random.choice(say_what)
    result = {"cow_said": cowsay.get_output_string("cow", said) if say_what is not None else None}
    return result, state.update(**result)


@action(reads=[], writes=["cow_should_speak"])
def cow_should_speak(state: State) -> Tuple[dict, State]:
    result = {"cow_should_speak": random.randint(0, 3) == 0}
    return result, state.update(**result)


def application(in_terminal: bool = False) -> Application:
    hooks = (
        [
            PrintWhatTheCowSaid(),
            CowCantSpeakFast(sleep_time=2.0),
        ]
        if in_terminal
        else []
    )
    return (
        ApplicationBuilder()
        .with_state(cow_said=None)
        .with_actions(
            say_nothing=cow_said.bind(say_what=None),
            say_hello=cow_said.bind(
                say_what=["Hello world!", "What's up?", "Are you Aaron Burr, sir?"]
            ),
            cow_should_speak=cow_should_speak,
        )
        .with_transitions(
            ("cow_should_speak", "say_hello", expr("cow_should_speak")),
            ("say_hello", "cow_should_speak", default),
            ("cow_should_speak", "say_nothing", expr("not cow_should_speak")),
            ("say_nothing", "cow_should_speak", default),
        )
        .with_entrypoint("cow_should_speak")
        .with_hooks(*hooks)
        .build()
    )


if __name__ == "__main__":
    app = application(in_terminal=True)
    app.visualize(output_file_path="digraph", include_conditions=True, view=True, format="png")
    while True:
        action, result, state = app.step()

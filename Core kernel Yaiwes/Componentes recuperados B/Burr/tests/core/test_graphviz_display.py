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

import pathlib

import pytest

from burr.core.graph import GraphBuilder

from tests.core.test_graph import PassedInAction


@pytest.fixture
def base_counter_action():
    yield PassedInAction(
        reads=["count"],
        writes=["count"],
        fn=lambda state: {"count": state.get("count", 0) + 1},
        update_fn=lambda result, state: state.update(**result),
        inputs=[],
    )


@pytest.fixture
def graph(base_counter_action):
    yield (
        GraphBuilder()
        .with_actions(counter=base_counter_action)
        .with_transitions(("counter", "counter"))
        .build()
    )


@pytest.mark.parametrize(
    "filename, write_dot", [("app", False), ("app.png", False), ("app", True), ("app.png", True)]
)
def test_visualize_dot_output(graph, tmp_path: pathlib.Path, filename: str, write_dot: bool):
    """Handle file generation with `graph.Digraph` `.render()` and `.pipe()`"""
    output_file_path = f"{tmp_path}/{filename}"

    graph.visualize(
        output_file_path=output_file_path,
        write_dot=write_dot,
    )

    # assert pathlib.Path(tmp_path, "app.png").exists()
    assert pathlib.Path(tmp_path, "app").exists() == write_dot


def test_visualize_no_dot_output(graph, tmp_path: pathlib.Path):
    """Check that no dot file is generated when output_file_path=None"""
    dot_file_path = tmp_path / "dag"

    graph.visualize(output_file_path=None)

    assert not dot_file_path.exists()

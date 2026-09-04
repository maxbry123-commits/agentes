import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Callable, List, Literal, Optional, Protocol, TypeVar

import ray
from datasets import Dataset
from pydantic import BaseModel, Field

from engine.operators.operator import (
    DatasetRefs,
    ExecutionContext,
    ManyShardRefsGenerator,
    Operator,
    OperatorSpecificConfig,
    ShardRef,
)

T = TypeVar("T")


class Node(BaseModel):
    """Base class for search tree nodes"""

    reasoning_step: str
    is_terminal: bool = False
    parent: Optional["Node"] = Field(default=None, repr=False)
    level: int = 0


class SearchState(str, Enum):
    """Possible states of the tree search"""

    FRONTIER_EMPTY = "FRONTIER_EMPTY"
    STEP_COMPLETE = "STEP_COMPLETE"
    BUDGET_EXCEEDED = "BUDGET_EXCEEDED"


class TreeSearchOperatorConfig(OperatorSpecificConfig):
    """
    Configuration for tree search operators.

    Attributes:
        type: Always "tree_search"
        prompt_column: Column containing the input prompt
        node_budget: Maximum number of nodes to explore
        beam_width: Maximum number of successors per node
        beam_depth: Maximum depth of search tree
    """

    type: Literal["tree_search"] = "tree_search"
    prompt_column: str = "instruction"
    node_budget: Optional[int] = Field(default=None)
    beam_width: Optional[int] = Field(default=None)
    beam_depth: Optional[int] = Field(default=None)


class TreeSearchOperator(Operator, ABC):
    """
    Abstract base class for tree search operators.

    Implements the core tree search logic while allowing subclasses to define
    specific expansion strategies through abstract methods.
    """

    def __init__(
        self,
        id: str,
        input_ids: List[str],
        config: TreeSearchOperatorConfig,
        execution_context: ExecutionContext,
    ):
        super().__init__(id, input_ids, config, execution_context)
        self.config = config

    @abstractmethod
    @ray.remote(num_cpus=0.01)
    def get_initial_state(self, prompt: str) -> Node:
        """
        Create the initial root node for the search.
        Typically requires GPU resources for LLM inference.
        """
        pass

    @abstractmethod
    @ray.remote(num_cpus=0.01)  # CPU-only task
    def get_successors(self, node: Node, prompt: str) -> List[Node]:
        """
        Generate successor nodes from the current node.
        Can be CPU-bound for simpler successor functions.
        """
        pass

    @abstractmethod
    @ray.remote(num_cpus=0.01)  # Lightweight CPU task
    def is_terminal(self, node: Node) -> bool:
        """
        Check if node is a terminal state.
        Typically a lightweight operation.
        """
        pass

    @abstractmethod
    @ray.remote(num_cpus=0.01)  # Lightweight CPU task
    def get_container(self) -> SearchContainer[Node]:
        """
        Get the container implementation for storing nodes.
        Lightweight initialization operation.
        """
        pass

    def compute(self, inputs: DatasetRefs) -> ManyShardRefsGenerator:
        """
        Execute tree search on input datasets.

        For each input shard, runs tree search algorithm and yields results.
        """
        all_shards = []
        for input_id, input_shards in inputs.items():
            all_shards.extend(input_shards)

        dataset = self.concatenate.remote(all_shards, add_shard_id_column)

        all_prompts = dataset[self.config.prompt_column]

        for prompt in all_prompts:
            prompt_promise = self.search_prompt.remote(prompt)

    @staticmethod
    @ray.remote
    def concatenate(shards: List[ShardRef], add_shard_id_column: bool) -> Dataset:
        """
        Concatenate the input shards.

        Args:
            shards (List[ShardRef]): List of dataset shard references.

        Returns:
            Dataset: Concatenateed and shuffled dataset.
        """
        datasets = []
        for shard_id, shards in shards.items():
            for shard in shards:
                dataset_shard = ray.get(shard)
                if add_shard_id_column:
                    dataset_shard = dataset_shard.add_column(
                        "shard_id", [shard_id] * len(dataset_shard)
                    )
                datasets.append(dataset_shard)
        combined_dataset = concatenate_datasets(datasets)
        return combined_dataset

    @ray.remote(num_cpus=0.01)  # Higher resource allocation for main search
    def search_prompt(self, prompt: str) -> Dataset:
        """
        Executes tree search on a single dataset shard.

        Args:
            prompt: Instruction to perform reasoning on
            node_budget: Maximum nodes to explore
            beam_width: Maximum successors per node
            beam_depth: Maximum tree depth

        Returns:
            Dataset containing search results
        """

        # Initialize search with remote calls
        initial_state = ray.get(self.get_initial_state.remote(prompt))
        container = ray.get(self.get_container.remote())
        container.append(initial_state)

        visited_nodes: List[Node] = []

        while container:
            # Check budget
            if (
                self.config.node_budget
                and len(visited_nodes) + len(container) >= self.config.node_budget
            ):
                logging.info(f"Node budget exceeded: {self.config.node_budget}")
                break

            # Get next node
            current = container.popleft()
            visited_nodes.append(current)

            # Check terminal with remote call
            if ray.get(self.is_terminal.remote(current)):
                logging.info(f"Terminal node found at depth {current.level}")
                continue

            # Check depth
            if self.config.beam_depth and current.level >= self.config.beam_depth:
                logging.info(f"Max depth reached: {self.config.beam_depth}")
                continue

            # Expand node with remote call
            successors = ray.get(self.get_successors.remote(current, prompt))
            if self.config.beam_width:
                successors = successors[: self.config.beam_width]

            # Add valid successors
            for successor in successors:
                if (
                    self.config.node_budget
                    and len(visited_nodes) + len(container) >= self.config.node_budget
                ):
                    break
                container.append(successor)

        # Convert results to dataset
        results = []
        for node in visited_nodes:
            trace = node.get_reasoning_trace()
            results.append(
                {
                    "steps": [n.reasoning_step for n in trace],
                    "is_terminal": node.is_terminal,
                    "depth": node.level,
                }
            )

        return Dataset.from_list(results)


# Example concrete implementation
class BreadthFirstSearchOperator(TreeSearchOperator):
    """Example implementation using breadth-first search strategy"""

    @ray.remote(num_cpus=1, num_gpus=0.5)
    def get_initial_state(self, prompt: str) -> Node:
        return Node(reasoning_step="Initial state", level=0)

    @ray.remote(num_cpus=1)
    def get_successors(self, node: Node, prompt: str) -> List[Node]:
        # Implementation would depend on specific use case
        pass

    @ray.remote(num_cpus=0.1)
    def is_terminal(self, node: Node) -> bool:
        # Implementation would depend on specific use case
        pass

    @ray.remote(num_cpus=0.1)
    def get_container(self) -> SearchContainer[Node]:
        from collections import deque

        return deque()  # BFS uses a queue

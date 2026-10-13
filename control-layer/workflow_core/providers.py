from typing import Protocol


class SandboxProvider(Protocol):

    def create(self, request: object) -> str:
        ...

    def execute(self, sandbox_id: str, command: str) -> object:
        ...

    def destroy(self, sandbox_id: str) -> None:
        ...


class MemoryProvider(Protocol):

    def store(self, record: object) -> None:
        ...

    def query(self, query: object) -> object:
        ...

    def link(self, source: object, target: object) -> None:
        ...

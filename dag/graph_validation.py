from __future__ import annotations

from typing import Generic, Hashable, TypeVar

from .graph_reachability import has_path
from .graph_storage import GraphStorage


NodeT = TypeVar("NodeT", bound=Hashable)


class DAGValidationError(Exception):
    """Raised when a graph mutation would violate DAG constraints."""


class CycleValidator(Generic[NodeT]):
    """Prevents edge insertions that would introduce a directed cycle.

    Before adding `source -> target`, the validator checks whether `target`
    already reaches `source`. If it does, the new edge would close a cycle.
    This is a targeted reachability check instead of a whole-graph copy and
    revalidation pass.
    """

    def __init__(self, storage: GraphStorage[NodeT]):
        self._storage = storage

    def ensure_edge_can_be_added(self, source: NodeT, target: NodeT) -> None:
        if source == target:
            raise DAGValidationError("self-referential edges are not allowed")
        if has_path(self._storage, target, source):
            raise DAGValidationError("edge would create a cycle")

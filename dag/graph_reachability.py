from __future__ import annotations

from collections import deque
from typing import Dict, Generic, Hashable, List, Set, TypeVar

from .graph_storage import GraphStorage


NodeT = TypeVar("NodeT", bound=Hashable)


def reachable_from(storage: GraphStorage[NodeT], source: NodeT) -> List[NodeT]:
    """Return all nodes reachable from `source` via outbound edges."""

    storage.downstream(source)
    visited: Set[NodeT] = set()
    queue = deque([source])

    while queue:
        current = queue.popleft()
        for child in storage.downstream(current):
            if child not in visited:
                visited.add(child)
                queue.append(child)

    return list(visited)


def reachable_to(storage: GraphStorage[NodeT], target: NodeT) -> List[NodeT]:
    """Return all nodes that can reach `target` via directed paths."""

    storage.predecessors(target)
    visited: Set[NodeT] = set()
    queue = deque([target])

    while queue:
        current = queue.popleft()
        for parent in storage.predecessors(current):
            if parent not in visited:
                visited.add(parent)
                queue.append(parent)

    return list(visited)


def has_path(storage: GraphStorage[NodeT], source: NodeT, target: NodeT) -> bool:
    """Return whether a directed path exists from `source` to `target`."""

    if source not in storage or target not in storage:
        missing = source if source not in storage else target
        raise KeyError("node %s is not in graph" % missing)
    if source == target:
        return True

    visited = {source}
    stack = [source]
    while stack:
        current = stack.pop()
        for child in storage.downstream(current):
            if child == target:
                return True
            if child not in visited:
                visited.add(child)
                stack.append(child)
    return False


def transitive_closure(storage: GraphStorage[NodeT]) -> Dict[NodeT, Set[NodeT]]:
    """Return the reachability set for every node in the graph."""

    return {node: set(reachable_from(storage, node)) for node in storage.nodes()}


class ReachabilityIndex(Generic[NodeT]):
    """Facade for directed reachability and ancestry queries."""

    def __init__(self, storage: GraphStorage[NodeT]):
        self._storage = storage

    def descendants(self, node: NodeT) -> List[NodeT]:
        return reachable_from(self._storage, node)

    def ancestors(self, node: NodeT) -> List[NodeT]:
        return reachable_to(self._storage, node)

    def has_path(self, source: NodeT, target: NodeT) -> bool:
        return has_path(self._storage, source, target)

    def transitive_closure(self) -> Dict[NodeT, Set[NodeT]]:
        return transitive_closure(self._storage)

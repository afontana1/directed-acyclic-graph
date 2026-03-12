from __future__ import annotations

from typing import Generic, Hashable, List, Set, TypeVar

from .graph_storage import GraphStorage


NodeT = TypeVar("NodeT", bound=Hashable)


def strongly_connected_components(storage: GraphStorage[NodeT]) -> List[List[NodeT]]:
    """Return strongly connected components using Tarjan's algorithm."""

    index = 0
    stack: List[NodeT] = []
    on_stack: Set[NodeT] = set()
    indices = {}
    low_links = {}
    components: List[List[NodeT]] = []

    def strong_connect(node: NodeT) -> None:
        nonlocal index
        indices[node] = index
        low_links[node] = index
        index += 1
        stack.append(node)
        on_stack.add(node)

        for child in storage.downstream(node):
            if child not in indices:
                strong_connect(child)
                low_links[node] = min(low_links[node], low_links[child])
            elif child in on_stack:
                low_links[node] = min(low_links[node], indices[child])

        if low_links[node] == indices[node]:
            component: List[NodeT] = []
            while True:
                current = stack.pop()
                on_stack.remove(current)
                component.append(current)
                if current == node:
                    break
            components.append(component)

    for node in storage.nodes():
        if node not in indices:
            strong_connect(node)

    return components


def weakly_connected_components(storage: GraphStorage[NodeT]) -> List[List[NodeT]]:
    """Return weakly connected components by ignoring edge direction."""

    remaining = set(storage.nodes())
    components: List[List[NodeT]] = []

    while remaining:
        start = remaining.pop()
        stack = [start]
        component = [start]

        while stack:
            current = stack.pop()
            neighbors = storage.downstream_set(current) | storage.predecessor_set(current)
            for neighbor in neighbors:
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
                    component.append(neighbor)

        components.append(component)

    return components


class ConnectivityIndex(Generic[NodeT]):
    """Facade for directed-graph connectivity algorithms."""

    def __init__(self, storage: GraphStorage[NodeT]):
        self._storage = storage

    def strongly_connected_components(self) -> List[List[NodeT]]:
        return strongly_connected_components(self._storage)

    def weakly_connected_components(self) -> List[List[NodeT]]:
        return weakly_connected_components(self._storage)

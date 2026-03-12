from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from typing import Dict, Iterable, List, Optional
from uuid import uuid4

from dag import DAG, DAGValidationError

from .models import EdgeModel, GraphSummary, NodeId, WeightedEdgeModel


class GraphNotFoundError(KeyError):
    """Raised when the requested graph does not exist."""


class GraphConflictError(ValueError):
    """Raised when the requested graph operation conflicts with existing state."""


@dataclass
class ManagedGraph:
    graph_id: str
    dag: DAG[str]
    node_weights: Dict[str, float]


class GraphService:
    """Application service that manages graph instances and graph algorithms."""

    def __init__(self):
        self._graphs: Dict[str, ManagedGraph] = {}
        self._lock = RLock()

    def list_graphs(self) -> List[dict]:
        with self._lock:
            return [
                {
                    "graph_id": managed.graph_id,
                    "node_count": managed.dag.size(),
                    "edge_count": self._edge_count(managed.dag),
                }
                for managed in self._graphs.values()
            ]

    def create_graph(self, graph_id: Optional[str] = None, adjacency: Optional[Dict[str, List[str]]] = None) -> GraphSummary:
        with self._lock:
            resolved_id = graph_id or str(uuid4())
            if resolved_id in self._graphs:
                raise GraphConflictError("graph %s already exists" % resolved_id)

            dag = DAG[str]()
            if adjacency:
                dag.from_dict(self._coerce_adjacency(adjacency))

            managed = ManagedGraph(
                graph_id=resolved_id,
                dag=dag,
                node_weights=self._default_weights(dag),
            )
            self._graphs[resolved_id] = managed
            return self._summarize(managed)

    def ensure_graph(self, graph_id: str) -> GraphSummary:
        with self._lock:
            return self._summarize(self._get_managed(graph_id))

    def delete_graph(self, graph_id: str) -> None:
        with self._lock:
            if graph_id not in self._graphs:
                raise GraphNotFoundError("graph %s was not found" % graph_id)
            del self._graphs[graph_id]

    def reset_graph(self, graph_id: str, adjacency: Dict[str, List[str]]) -> GraphSummary:
        with self._lock:
            managed = self._get_managed(graph_id)
            managed.dag.reset_graph()
            if adjacency:
                managed.dag.from_dict(self._coerce_adjacency(adjacency))
            managed.node_weights = self._default_weights(managed.dag)
            return self._summarize(managed)

    def add_node(self, graph_id: str, node_id: Optional[NodeId], weight: float = 1.0) -> GraphSummary:
        with self._lock:
            managed = self._get_managed(graph_id)
            resolved_node_id = node_id or self._next_node_id(managed.dag)
            managed.dag.add_node(resolved_node_id)
            managed.node_weights[resolved_node_id] = float(weight)
            return self._summarize(managed)

    def delete_node(self, graph_id: str, node_id: NodeId) -> GraphSummary:
        with self._lock:
            managed = self._get_managed(graph_id)
            managed.dag.delete_node(node_id)
            managed.node_weights.pop(node_id, None)
            return self._summarize(managed)

    def add_edge(self, graph_id: str, source: NodeId, target: NodeId) -> GraphSummary:
        with self._lock:
            managed = self._get_managed(graph_id)
            managed.dag.add_edge(source, target)
            return self._summarize(managed)

    def delete_edge(self, graph_id: str, source: NodeId, target: NodeId) -> GraphSummary:
        with self._lock:
            managed = self._get_managed(graph_id)
            managed.dag.delete_edge(source, target)
            return self._summarize(managed)

    def topological_sort(self, graph_id: str) -> List[NodeId]:
        with self._lock:
            return self._get_managed(graph_id).dag.topological_sort()

    def topological_levels(self, graph_id: str) -> List[List[NodeId]]:
        with self._lock:
            return self._get_managed(graph_id).dag.topological_levels()

    def transitive_reduction(self, graph_id: str) -> Dict[NodeId, List[NodeId]]:
        with self._lock:
            reduced = self._get_managed(graph_id).dag.transitive_reduction()
            return self._normalize_adjacency(reduced)

    def transitive_closure(self, graph_id: str) -> Dict[NodeId, List[NodeId]]:
        with self._lock:
            closure = self._get_managed(graph_id).dag.transitive_closure()
            return self._normalize_adjacency(closure)

    def descendants(self, graph_id: str, node_id: NodeId) -> List[NodeId]:
        with self._lock:
            return sorted(self._get_managed(graph_id).dag.descendants(node_id))

    def ancestors(self, graph_id: str, node_id: NodeId) -> List[NodeId]:
        with self._lock:
            return sorted(self._get_managed(graph_id).dag.ancestors(node_id))

    def has_path(self, graph_id: str, source: NodeId, target: NodeId) -> bool:
        with self._lock:
            return self._get_managed(graph_id).dag.has_path(source, target)

    def shortest_path(self, graph_id: str, source: NodeId, target: NodeId) -> List[NodeId]:
        with self._lock:
            return self._get_managed(graph_id).dag.shortest_path(source, target)

    def dijkstra_shortest_path(
        self,
        graph_id: str,
        source: NodeId,
        target: NodeId,
        weights: Iterable[WeightedEdgeModel],
    ) -> dict:
        with self._lock:
            dag = self._get_managed(graph_id).dag
            weight_index = {(edge.source, edge.target): edge.weight for edge in weights}

            def resolve_weight(from_node: NodeId, to_node: NodeId) -> float:
                key = (from_node, to_node)
                if key not in weight_index:
                    raise KeyError("missing weight for edge %s -> %s" % key)
                return weight_index[key]

            return dag.dijkstra_shortest_path(source, target, resolve_weight)

    def critical_path(self, graph_id: str, durations: Dict[NodeId, float]) -> dict:
        with self._lock:
            managed = self._get_managed(graph_id)
            effective_durations = dict(managed.node_weights)
            effective_durations.update(durations)
            return managed.dag.critical_path(durations=effective_durations)

    def set_node_weight(self, graph_id: str, node_id: NodeId, weight: float) -> GraphSummary:
        with self._lock:
            managed = self._get_managed(graph_id)
            if node_id not in managed.dag.graph:
                raise KeyError("node %s is not in graph" % node_id)
            managed.node_weights[node_id] = float(weight)
            return self._summarize(managed)

    def strongly_connected_components(self, graph_id: str) -> List[List[NodeId]]:
        with self._lock:
            components = self._get_managed(graph_id).dag.strongly_connected_components()
            return [sorted(component) for component in components]

    def weakly_connected_components(self, graph_id: str) -> List[List[NodeId]]:
        with self._lock:
            components = self._get_managed(graph_id).dag.weakly_connected_components()
            return [sorted(component) for component in components]

    def summary(self, graph_id: str) -> GraphSummary:
        with self._lock:
            return self._summarize(self._get_managed(graph_id))

    def graph_count(self) -> int:
        with self._lock:
            return len(self._graphs)

    def _get_managed(self, graph_id: str) -> ManagedGraph:
        if graph_id not in self._graphs:
            raise GraphNotFoundError("graph %s was not found" % graph_id)
        return self._graphs[graph_id]

    def _summarize(self, managed: ManagedGraph) -> GraphSummary:
        dag = managed.dag
        is_valid, validation_message = dag.validate()
        return GraphSummary(
            graph_id=managed.graph_id,
            node_count=dag.size(),
            edge_count=self._edge_count(dag),
            nodes=sorted(dag.graph.keys()),
            edges=self._edge_models(dag.graph),
            adjacency=self._normalize_adjacency(dag.graph),
            node_weights=self._normalize_weights(managed.node_weights, dag.graph.keys()),
            roots=sorted(dag.ind_nodes()),
            leaves=sorted(dag.all_leaves()),
            is_valid=is_valid,
            validation_message=validation_message,
        )

    @staticmethod
    def _edge_count(graph: DAG[str]) -> int:
        return sum(len(targets) for targets in graph.graph.values())

    @staticmethod
    def _edge_models(adjacency: Dict[NodeId, Iterable[NodeId]]) -> List[EdgeModel]:
        edges = [
            EdgeModel(edge_id=GraphService._edge_id(source, target), source=source, target=target)
            for source, targets in adjacency.items()
            for target in targets
        ]
        return sorted(edges, key=lambda edge: (edge.source, edge.target))

    @staticmethod
    def _normalize_adjacency(adjacency: Dict[NodeId, Iterable[NodeId]]) -> Dict[NodeId, List[NodeId]]:
        return {node: sorted(list(targets)) for node, targets in adjacency.items()}

    @staticmethod
    def _coerce_adjacency(adjacency: Dict[NodeId, List[NodeId]]) -> Dict[NodeId, List[NodeId]]:
        normalized = {node: list(targets) for node, targets in adjacency.items()}
        for targets in adjacency.values():
            for target in targets:
                normalized.setdefault(target, [])
        return normalized

    @staticmethod
    def _next_node_id(graph: DAG[str]) -> str:
        existing = set(graph.graph.keys())
        index = 1
        while True:
            candidate = f"node-{index}"
            if candidate not in existing:
                return candidate
            index += 1

    @staticmethod
    def _edge_id(source: NodeId, target: NodeId) -> str:
        return f"edge:{source}->{target}"

    @staticmethod
    def _default_weights(graph: DAG[str]) -> Dict[str, float]:
        return {node_id: 1.0 for node_id in graph.graph.keys()}

    @staticmethod
    def _normalize_weights(weights: Dict[NodeId, float], nodes: Iterable[NodeId]) -> Dict[NodeId, float]:
        return {node_id: float(weights.get(node_id, 1.0)) for node_id in nodes}

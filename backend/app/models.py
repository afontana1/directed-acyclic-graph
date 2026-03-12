from __future__ import annotations

from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


NodeId = str


class EdgeModel(BaseModel):
    edge_id: Optional[str] = None
    source: NodeId = Field(..., min_length=1)
    target: NodeId = Field(..., min_length=1)


class GraphCreateRequest(BaseModel):
    graph_id: Optional[str] = Field(default=None, min_length=1)
    adjacency: Dict[NodeId, List[NodeId]] = Field(default_factory=dict)


class GraphListItem(BaseModel):
    graph_id: str
    node_count: int
    edge_count: int


class GraphSummary(BaseModel):
    graph_id: str
    node_count: int
    edge_count: int
    nodes: List[NodeId]
    edges: List[EdgeModel]
    adjacency: Dict[NodeId, List[NodeId]]
    node_weights: Dict[NodeId, float]
    roots: List[NodeId]
    leaves: List[NodeId]
    is_valid: bool
    validation_message: str


class NodeCreateRequest(BaseModel):
    node_id: Optional[NodeId] = Field(default=None, min_length=1)
    weight: float = 1.0


class NodeWeightUpdateRequest(BaseModel):
    weight: float


class GraphResetRequest(BaseModel):
    adjacency: Dict[NodeId, List[NodeId]] = Field(default_factory=dict)


class WeightedEdgeModel(EdgeModel):
    weight: float


class CriticalPathRequest(BaseModel):
    durations: Dict[NodeId, float] = Field(default_factory=dict)


class CriticalPathResponse(BaseModel):
    path: List[NodeId]
    duration: float
    distances: Dict[NodeId, float]


class UnweightedPathRequest(BaseModel):
    source: NodeId = Field(..., min_length=1)
    target: NodeId = Field(..., min_length=1)


class DijkstraPathRequest(UnweightedPathRequest):
    weights: List[WeightedEdgeModel] = Field(default_factory=list)


class PathResponse(BaseModel):
    path: List[NodeId]
    distance: Optional[float] = None


class HasPathResponse(BaseModel):
    source: NodeId
    target: NodeId
    exists: bool


class NodeSetResponse(BaseModel):
    node_id: NodeId
    related_nodes: List[NodeId]


class TopologicalOrderResponse(BaseModel):
    order: List[NodeId]


class TopologicalLevelsResponse(BaseModel):
    levels: List[List[NodeId]]


class AdjacencyResponse(BaseModel):
    adjacency: Dict[NodeId, List[NodeId]]


class TransitiveClosureResponse(BaseModel):
    closure: Dict[NodeId, List[NodeId]]


class ComponentsResponse(BaseModel):
    components: List[List[NodeId]]
    connectivity: Literal["strong", "weak"]


class HealthResponse(BaseModel):
    status: Literal["ok"]
    graphs_loaded: int


class ErrorResponse(BaseModel):
    detail: str

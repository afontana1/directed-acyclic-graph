from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query, Response, status
from fastapi.middleware.cors import CORSMiddleware

from .dependencies import get_app_settings, get_graph_service
from .models import (
    AdjacencyResponse,
    ComponentsResponse,
    CriticalPathRequest,
    CriticalPathResponse,
    DijkstraPathRequest,
    EdgeModel,
    ErrorResponse,
    GraphCreateRequest,
    GraphListItem,
    GraphResetRequest,
    GraphSummary,
    HasPathResponse,
    HealthResponse,
    NodeCreateRequest,
    NodeWeightUpdateRequest,
    NodeSetResponse,
    PathResponse,
    TopologicalLevelsResponse,
    TopologicalOrderResponse,
    TransitiveClosureResponse,
    UnweightedPathRequest,
)
from .service import GraphConflictError, GraphNotFoundError, GraphService
from dag import DAGValidationError


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_app_settings()
    service = get_graph_service()
    if settings.create_default_graph and settings.default_graph_id not in {
        graph["graph_id"] for graph in service.list_graphs()
    }:
        service.create_graph(graph_id=settings.default_graph_id)
    yield


def create_app() -> FastAPI:
    settings = get_app_settings()
    app = FastAPI(
        title=settings.title,
        version=settings.version,
        lifespan=lifespan,
        responses={
            400: {"model": ErrorResponse},
            404: {"model": ErrorResponse},
            409: {"model": ErrorResponse},
            422: {"model": ErrorResponse},
        },
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_routes(app)
    return app


def register_routes(app: FastAPI) -> None:
    @app.get("/health", response_model=HealthResponse)
    def health(service: GraphService = Depends(get_graph_service)) -> HealthResponse:
        return HealthResponse(status="ok", graphs_loaded=service.graph_count())

    @app.get("/graphs", response_model=list[GraphListItem])
    def list_graphs(service: GraphService = Depends(get_graph_service)) -> list[GraphListItem]:
        return [GraphListItem(**graph) for graph in service.list_graphs()]

    @app.post("/graphs", response_model=GraphSummary, status_code=status.HTTP_201_CREATED)
    def create_graph(
        request: GraphCreateRequest,
        service: GraphService = Depends(get_graph_service),
    ) -> GraphSummary:
        try:
            return service.create_graph(graph_id=request.graph_id, adjacency=request.adjacency)
        except GraphConflictError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
        except (KeyError, ValueError, DAGValidationError) as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    @app.get("/graphs/{graph_id}", response_model=GraphSummary)
    def get_graph(graph_id: str, service: GraphService = Depends(get_graph_service)) -> GraphSummary:
        try:
            return service.summary(graph_id)
        except GraphNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    @app.delete("/graphs/{graph_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_graph(graph_id: str, service: GraphService = Depends(get_graph_service)) -> Response:
        try:
            service.delete_graph(graph_id)
            return Response(status_code=status.HTTP_204_NO_CONTENT)
        except GraphNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    @app.post("/graphs/{graph_id}/reset", response_model=GraphSummary)
    def reset_graph(
        graph_id: str,
        request: GraphResetRequest,
        service: GraphService = Depends(get_graph_service),
    ) -> GraphSummary:
        try:
            return service.reset_graph(graph_id, request.adjacency)
        except GraphNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        except (KeyError, ValueError, DAGValidationError) as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    @app.post("/graphs/{graph_id}/nodes", response_model=GraphSummary)
    def add_node(
        graph_id: str,
        request: NodeCreateRequest,
        service: GraphService = Depends(get_graph_service),
    ) -> GraphSummary:
        try:
            return service.add_node(graph_id, request.node_id, request.weight)
        except GraphNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    @app.put("/graphs/{graph_id}/nodes/{node_id}/weight", response_model=GraphSummary)
    def update_node_weight(
        graph_id: str,
        node_id: str,
        request: NodeWeightUpdateRequest,
        service: GraphService = Depends(get_graph_service),
    ) -> GraphSummary:
        try:
            return service.set_node_weight(graph_id, node_id, request.weight)
        except GraphNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    @app.delete("/graphs/{graph_id}/nodes/{node_id}", response_model=GraphSummary)
    def delete_node(graph_id: str, node_id: str, service: GraphService = Depends(get_graph_service)) -> GraphSummary:
        try:
            return service.delete_node(graph_id, node_id)
        except GraphNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    @app.post("/graphs/{graph_id}/edges", response_model=GraphSummary)
    def add_edge(graph_id: str, request: EdgeModel, service: GraphService = Depends(get_graph_service)) -> GraphSummary:
        try:
            return service.add_edge(graph_id, request.source, request.target)
        except GraphNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        except DAGValidationError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    @app.delete("/graphs/{graph_id}/edges", response_model=GraphSummary)
    def delete_edge(graph_id: str, request: EdgeModel, service: GraphService = Depends(get_graph_service)) -> GraphSummary:
        try:
            return service.delete_edge(graph_id, request.source, request.target)
        except GraphNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    @app.get("/graphs/{graph_id}/summary", response_model=GraphSummary)
    def summary(graph_id: str, service: GraphService = Depends(get_graph_service)) -> GraphSummary:
        try:
            return service.summary(graph_id)
        except GraphNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    @app.get("/graphs/{graph_id}/topology/topological-sort", response_model=TopologicalOrderResponse)
    def get_topological_sort(graph_id: str, service: GraphService = Depends(get_graph_service)) -> TopologicalOrderResponse:
        try:
            return TopologicalOrderResponse(order=service.topological_sort(graph_id))
        except GraphNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    @app.get("/graphs/{graph_id}/topology/topological-levels", response_model=TopologicalLevelsResponse)
    def get_topological_levels(
        graph_id: str,
        service: GraphService = Depends(get_graph_service),
    ) -> TopologicalLevelsResponse:
        try:
            return TopologicalLevelsResponse(levels=service.topological_levels(graph_id))
        except GraphNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    @app.get("/graphs/{graph_id}/topology/transitive-reduction", response_model=AdjacencyResponse)
    def get_transitive_reduction(
        graph_id: str,
        service: GraphService = Depends(get_graph_service),
    ) -> AdjacencyResponse:
        try:
            return AdjacencyResponse(adjacency=service.transitive_reduction(graph_id))
        except GraphNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    @app.get("/graphs/{graph_id}/reachability/transitive-closure", response_model=TransitiveClosureResponse)
    def get_transitive_closure(
        graph_id: str,
        service: GraphService = Depends(get_graph_service),
    ) -> TransitiveClosureResponse:
        try:
            return TransitiveClosureResponse(closure=service.transitive_closure(graph_id))
        except GraphNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    @app.get("/graphs/{graph_id}/reachability/descendants/{node_id}", response_model=NodeSetResponse)
    def get_descendants(
        graph_id: str,
        node_id: str,
        service: GraphService = Depends(get_graph_service),
    ) -> NodeSetResponse:
        try:
            return NodeSetResponse(node_id=node_id, related_nodes=service.descendants(graph_id, node_id))
        except GraphNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    @app.get("/graphs/{graph_id}/reachability/ancestors/{node_id}", response_model=NodeSetResponse)
    def get_ancestors(
        graph_id: str,
        node_id: str,
        service: GraphService = Depends(get_graph_service),
    ) -> NodeSetResponse:
        try:
            return NodeSetResponse(node_id=node_id, related_nodes=service.ancestors(graph_id, node_id))
        except GraphNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    @app.get("/graphs/{graph_id}/reachability/has-path", response_model=HasPathResponse)
    def get_has_path(
        graph_id: str,
        source: str = Query(..., min_length=1),
        target: str = Query(..., min_length=1),
        service: GraphService = Depends(get_graph_service),
    ) -> HasPathResponse:
        try:
            return HasPathResponse(
                source=source,
                target=target,
                exists=service.has_path(graph_id, source, target),
            )
        except GraphNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    @app.post("/graphs/{graph_id}/pathfinding/shortest-path", response_model=PathResponse)
    def get_shortest_path(
        graph_id: str,
        request: UnweightedPathRequest,
        service: GraphService = Depends(get_graph_service),
    ) -> PathResponse:
        try:
            return PathResponse(path=service.shortest_path(graph_id, request.source, request.target))
        except GraphNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    @app.post("/graphs/{graph_id}/pathfinding/dijkstra", response_model=PathResponse)
    def get_dijkstra_path(
        graph_id: str,
        request: DijkstraPathRequest,
        service: GraphService = Depends(get_graph_service),
    ) -> PathResponse:
        try:
            result = service.dijkstra_shortest_path(graph_id, request.source, request.target, request.weights)
            return PathResponse(path=result["path"], distance=result["distance"])
        except GraphNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        except (KeyError, ValueError) as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    @app.post("/graphs/{graph_id}/analysis/critical-path", response_model=CriticalPathResponse)
    def get_critical_path(
        graph_id: str,
        request: CriticalPathRequest,
        service: GraphService = Depends(get_graph_service),
    ) -> CriticalPathResponse:
        try:
            result = service.critical_path(graph_id, request.durations)
            return CriticalPathResponse(**result)
        except GraphNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        except (KeyError, ValueError) as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    @app.get(
        "/graphs/{graph_id}/connectivity/strongly-connected-components",
        response_model=ComponentsResponse,
    )
    def get_strong_components(
        graph_id: str,
        service: GraphService = Depends(get_graph_service),
    ) -> ComponentsResponse:
        try:
            return ComponentsResponse(
                connectivity="strong",
                components=service.strongly_connected_components(graph_id),
            )
        except GraphNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    @app.get(
        "/graphs/{graph_id}/connectivity/weakly-connected-components",
        response_model=ComponentsResponse,
    )
    def get_weak_components(
        graph_id: str,
        service: GraphService = Depends(get_graph_service),
    ) -> ComponentsResponse:
        try:
            return ComponentsResponse(
                connectivity="weak",
                components=service.weakly_connected_components(graph_id),
            )
        except GraphNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


app = create_app()

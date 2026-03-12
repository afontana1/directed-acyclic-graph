import { useEffect, useMemo, useRef, useState } from "react";
import {
  Background,
  Controls,
  MiniMap,
  ReactFlow,
  useEdgesState,
  useNodesState,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

const CANVAS_WIDTH = 980;
const CANVAS_HEIGHT = 640;

export default function GraphCanvas({
  summary,
  layout,
  selectedNodeIds,
  selectedEdgeId,
  connectMode,
  pendingConnectionSource,
  onSelectEdge,
  onNodeActivate,
}) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [isReady, setIsReady] = useState(false);
  const graphIdRef = useRef(null);
  const lastPositionsRef = useRef({});
  const flowInstanceRef = useRef(null);

  const edgeModels = useMemo(
    () =>
      (layout.edges || []).map((edge) => ({
        id: edge.id,
        source: edge.source,
        target: edge.target,
        animated: false,
        markerEnd: { type: "arrowclosed" },
        className: edge.id === selectedEdgeId ? "flow-edge is-selected" : "flow-edge",
      })),
    [layout.edges, selectedEdgeId],
  );

  useEffect(() => {
    if (!summary?.nodes?.length) {
      setNodes([]);
      setEdges([]);
      setIsReady(false);
      graphIdRef.current = null;
      lastPositionsRef.current = {};
      return;
    }

    const graphChanged = graphIdRef.current !== summary.graph_id;
    const preservedPositions = graphChanged ? {} : lastPositionsRef.current;
    const nextNodes = (summary.nodes || []).map((nodeId) => ({
      id: nodeId,
      type: "default",
      position: preservedPositions[nodeId] || layout.positions[nodeId] || { x: 120, y: 120 },
      data: { label: nodeId },
      className:
        nodeId === pendingConnectionSource
          ? "flow-node is-armed"
          : selectedNodeIds.includes(nodeId)
            ? connectMode
              ? "flow-node is-connect-selected"
              : "flow-node is-selected"
            : "flow-node",
    }));

    graphIdRef.current = summary.graph_id;
    lastPositionsRef.current = Object.fromEntries(nextNodes.map((node) => [node.id, node.position]));
    setNodes(nextNodes);
    setEdges(edgeModels);
    setIsReady(Boolean(nextNodes.length));
  }, [
    edgeModels,
    connectMode,
    layout.positions,
    pendingConnectionSource,
    selectedNodeIds,
    setEdges,
    setNodes,
    summary?.graph_id,
    summary?.nodes,
  ]);

  useEffect(() => {
    lastPositionsRef.current = Object.fromEntries(nodes.map((node) => [node.id, node.position]));
  }, [nodes]);

  useEffect(() => {
    if (!flowInstanceRef.current || !summary?.nodes?.length) {
      return;
    }

    requestAnimationFrame(() => {
      flowInstanceRef.current?.fitView({
        padding: 0.24,
        minZoom: 0.4,
        maxZoom: 1.2,
        duration: 280,
      });
    });
  }, [layout.seed, summary?.nodes?.length]);

  if (!summary?.nodes?.length) {
    return (
      <div className="graph-canvas graph-canvas--empty">
        <div>
          <p>No nodes yet.</p>
          <span>Add nodes from the control rail to start building the graph.</span>
        </div>
      </div>
    );
  }

  return (
    <div className="graph-canvas-shell">
      <div className="graph-canvas flow-shell">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onInit={(instance) => {
            flowInstanceRef.current = instance;
          }}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeClick={(_, node) => onNodeActivate(node.id)}
          onEdgeClick={(_, edge) =>
            onSelectEdge({
              id: edge.id,
              source: edge.source,
              target: edge.target,
            })
          }
          fitView
          fitViewOptions={{ padding: 0.24, minZoom: 0.4, maxZoom: 1.2 }}
          minZoom={0.2}
          maxZoom={2}
          proOptions={{ hideAttribution: true }}
          defaultViewport={{ x: 0, y: 0, zoom: 1 }}
          nodesDraggable
          nodesConnectable={false}
          elementsSelectable
          panOnDrag
          className={isReady ? "flow-ready" : "flow-loading"}
        >
          <MiniMap
            pannable
            zoomable
            nodeStrokeColor={(node) => (selectedNodeIds.includes(node.id) ? "#824800" : "#10322d")}
            nodeColor={(node) => (selectedNodeIds.includes(node.id) ? "#f1b24a" : "#fef6df")}
            maskColor="rgba(16, 50, 45, 0.08)"
          />
          <Controls showInteractive={false} />
          <Background color="rgba(16, 50, 45, 0.12)" gap={24} />
        </ReactFlow>
      </div>
    </div>
  );
}

export { CANVAS_HEIGHT, CANVAS_WIDTH };

import { startTransition, useEffect, useMemo, useState } from "react";
import GraphCanvas from "./components/GraphCanvas";
import { api } from "./api";
import { buildGraphLayout } from "./graphLayout";

const EMPTY_CREATE_FORM = { graphId: "" };
const EMPTY_NODE_FORM = { nodeId: "", weight: "1" };
const EMPTY_EDGE_FORM = { source: "", target: "" };
const EMPTY_DIJKSTRA_FORM = { weightsText: "" };
const EMPTY_CRITICAL_PATH_FORM = { durationsText: "" };
const EMPTY_RESET_FORM = { adjacencyText: "{}" };

export default function App() {
  const [graphs, setGraphs] = useState([]);
  const [activeGraphId, setActiveGraphId] = useState("");
  const [graphSummary, setGraphSummary] = useState(null);
  const [levels, setLevels] = useState({ levels: [] });
  const [selectedNodeIds, setSelectedNodeIds] = useState([]);
  const [selectedEdge, setSelectedEdge] = useState(null);
  const [connectMode, setConnectMode] = useState(false);
  const [pendingConnectionSource, setPendingConnectionSource] = useState("");
  const [algorithmResult, setAlgorithmResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [layoutSeed, setLayoutSeed] = useState(0);
  const [navOpen, setNavOpen] = useState(true);

  const [createForm, setCreateForm] = useState(EMPTY_CREATE_FORM);
  const [nodeForm, setNodeForm] = useState(EMPTY_NODE_FORM);
  const [edgeForm, setEdgeForm] = useState(EMPTY_EDGE_FORM);
  const [dijkstraForm, setDijkstraForm] = useState(EMPTY_DIJKSTRA_FORM);
  const [criticalPathForm, setCriticalPathForm] = useState(EMPTY_CRITICAL_PATH_FORM);
  const [resetForm, setResetForm] = useState(EMPTY_RESET_FORM);
  const [weightDraft, setWeightDraft] = useState("1");

  const activeNodeId = selectedNodeIds[selectedNodeIds.length - 1] || "";
  const pathSelection = {
    source: selectedNodeIds[0] || "",
    target: selectedNodeIds[1] || "",
  };

  useEffect(() => {
    void bootstrap();
  }, []);

  useEffect(() => {
    if (!activeNodeId || !graphSummary?.node_weights) {
      setWeightDraft("1");
      return;
    }
    setWeightDraft(String(graphSummary.node_weights[activeNodeId] ?? 1));
  }, [activeNodeId, graphSummary?.node_weights]);

  async function bootstrap() {
    setLoading(true);
    setError("");
    try {
      const graphList = await api.getGraphs();
      setGraphs(graphList);
      const initialGraphId = graphList[0]?.graph_id || "";
      setActiveGraphId(initialGraphId);
      if (initialGraphId) {
        await refreshActiveGraph(initialGraphId);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function refreshGraphList(nextActiveGraphId) {
    const graphList = await api.getGraphs();
    startTransition(() => {
      setGraphs(graphList);
      if (nextActiveGraphId !== undefined) {
        setActiveGraphId(nextActiveGraphId);
      }
    });
  }

  async function refreshActiveGraph(graphId = activeGraphId) {
    if (!graphId) {
      setGraphSummary(null);
      setLevels({ levels: [] });
      return;
    }

    const [summary, topologicalLevels] = await Promise.all([
      api.getGraph(graphId),
      api.getTopologicalLevels(graphId).catch(() => ({ levels: [] })),
    ]);

    startTransition(() => {
      setGraphSummary(summary);
      setLevels(topologicalLevels);
      setSelectedNodeIds([]);
      setSelectedEdge(null);
      setPendingConnectionSource("");
      setLayoutSeed((current) => current + 1);
    });
  }

  async function runAction(action, successMessage) {
    setError("");
    try {
      const result = await action();
      if (successMessage) {
        setAlgorithmResult({ title: successMessage, payload: result });
      }
      return result;
    } catch (err) {
      setError(err.message);
      return null;
    }
  }

  async function handleCreateGraph(event) {
    event.preventDefault();
    const created = await runAction(
      () => api.createGraph({ graph_id: createForm.graphId.trim() || undefined, adjacency: {} }),
      "Graph created",
    );
    if (!created) return;
    await refreshGraphList(created.graph_id);
    await refreshActiveGraph(created.graph_id);
    setCreateForm(EMPTY_CREATE_FORM);
  }

  async function handleAddNode(event) {
    event.preventDefault();
    if (!activeGraphId) return;
    const summary = await runAction(
      () =>
        api.addNode(activeGraphId, {
          node_id: nodeForm.nodeId.trim() || null,
          weight: Number(nodeForm.weight || 1),
        }),
      "Node added",
    );
    if (!summary) return;
    setNodeForm(EMPTY_NODE_FORM);
    await refreshActiveGraph(activeGraphId);
    await refreshGraphList(activeGraphId);
  }

  async function handleAddEdge(event) {
    event.preventDefault();
    if (!activeGraphId) return;
    const summary = await runAction(
      () => api.addEdge(activeGraphId, { source: edgeForm.source.trim(), target: edgeForm.target.trim() }),
      "Edge added",
    );
    if (!summary) return;
    setEdgeForm(EMPTY_EDGE_FORM);
    await refreshActiveGraph(activeGraphId);
    await refreshGraphList(activeGraphId);
  }

  async function handleSwitchGraph(graphId) {
    setActiveGraphId(graphId);
    await runAction(() => refreshActiveGraph(graphId));
  }

  async function handleDeleteGraph() {
    if (!activeGraphId) return;
    setError("");
    try {
      await api.deleteGraph(activeGraphId);
      setAlgorithmResult({ title: "Graph deleted", payload: { graph_id: activeGraphId } });
    } catch (err) {
      setError(err.message);
      return;
    }
    const graphList = await api.getGraphs();
    const nextGraphId = graphList[0]?.graph_id || "";
    setGraphs(graphList);
    setActiveGraphId(nextGraphId);
    if (nextGraphId) {
      await refreshActiveGraph(nextGraphId);
    } else {
      setGraphSummary(null);
      setLevels({ levels: [] });
      setSelectedNodeIds([]);
      setSelectedEdge(null);
      setPendingConnectionSource("");
    }
  }

  async function handleDeleteSelectedNode() {
    if (!activeGraphId || !activeNodeId) return;
    const summary = await runAction(() => api.deleteNode(activeGraphId, activeNodeId), `Node ${activeNodeId} deleted`);
    if (!summary) return;
    await refreshActiveGraph(activeGraphId);
    await refreshGraphList(activeGraphId);
  }

  async function handleDeleteSelectedEdge() {
    if (!activeGraphId || !selectedEdge) return;
    const summary = await runAction(() => api.deleteEdge(activeGraphId, selectedEdge), "Edge deleted");
    if (!summary) return;
    await refreshActiveGraph(activeGraphId);
    await refreshGraphList(activeGraphId);
  }

  async function handleUpdateSelectedWeight(event) {
    event.preventDefault();
    if (!activeGraphId || !activeNodeId) return;
    const summary = await runAction(
      () => api.updateNodeWeight(activeGraphId, activeNodeId, { weight: Number(weightDraft || 1) }),
      `Updated weight for ${activeNodeId}`,
    );
    if (!summary) return;
    await refreshActiveGraph(activeGraphId);
    await refreshGraphList(activeGraphId);
    setSelectedNodeIds([activeNodeId]);
  }

  async function handleResetGraph(event) {
    event.preventDefault();
    if (!activeGraphId) return;
    let adjacency;
    try {
      adjacency = JSON.parse(resetForm.adjacencyText);
    } catch {
      setError("Reset payload must be valid JSON");
      return;
    }
    const summary = await runAction(() => api.resetGraph(activeGraphId, { adjacency }), "Graph reset");
    if (!summary) return;
    await refreshActiveGraph(activeGraphId);
    await refreshGraphList(activeGraphId);
  }

  async function executeAlgorithm(title, fn) {
    try {
      const result = await fn();
      setAlgorithmResult({ title, payload: result });
      setError("");
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleNodeActivate(nodeId) {
    setSelectedEdge(null);
    if (!activeGraphId) {
      setSelectedNodeIds((current) => pushNodeSelection(current, nodeId));
      return;
    }
    if (connectMode) {
      if (!pendingConnectionSource) {
        setPendingConnectionSource(nodeId);
        setSelectedNodeIds([nodeId]);
        return;
      }
      if (pendingConnectionSource === nodeId) {
        setPendingConnectionSource("");
        return;
      }
      const summary = await runAction(
        () => api.addEdge(activeGraphId, { source: pendingConnectionSource, target: nodeId }),
        `Edge added: ${pendingConnectionSource} -> ${nodeId}`,
      );
      setPendingConnectionSource("");
      setSelectedNodeIds([nodeId]);
      if (!summary) return;
      await refreshActiveGraph(activeGraphId);
      await refreshGraphList(activeGraphId);
      return;
    }
    setSelectedNodeIds((current) => pushNodeSelection(current, nodeId));
  }

  const selectedNodeDetails = useMemo(() => {
    if (!activeNodeId || !graphSummary) return null;
    return {
      incoming: graphSummary.edges.filter((edge) => edge.target === activeNodeId),
      outgoing: graphSummary.edges.filter((edge) => edge.source === activeNodeId),
    };
  }, [activeNodeId, graphSummary]);

  const layout = buildGraphLayout(graphSummary, levels, 980, 640, layoutSeed);

  return (
    <div className={`app-shell app-shell--side-nav ${navOpen ? "nav-expanded" : "nav-collapsed"}`}>
      <aside className={`control-nav ${navOpen ? "is-open" : "is-collapsed"}`}>
        <div className="control-nav__header">
          <div>
            <p className="eyebrow">Controls</p>
            {navOpen ? <h2>Graph Console</h2> : null}
          </div>
          <button type="button" className="ghost-button control-nav__toggle" onClick={() => setNavOpen((current) => !current)}>
            {navOpen ? "Collapse" : "Open"}
          </button>
        </div>

        {navOpen ? (
          <div className="control-nav__content">
            <section className="panel section-card">
              <div className="panel-header">
                <h2>Create Graph</h2>
                <span>{graphs.length}</span>
              </div>
              <form onSubmit={handleCreateGraph} className="stack">
                <input value={createForm.graphId} onChange={(e) => setCreateForm({ graphId: e.target.value })} placeholder="New graph id" />
                <button type="submit">Create graph</button>
              </form>
              <div className="graph-list graph-list--compact">
                {graphs.map((graph) => (
                  <button
                    key={graph.graph_id}
                    className={`graph-chip ${graph.graph_id === activeGraphId ? "is-active" : ""}`}
                    onClick={() => handleSwitchGraph(graph.graph_id)}
                  >
                    <span>{graph.graph_id}</span>
                    <small>{graph.node_count}n / {graph.edge_count}e</small>
                  </button>
                ))}
              </div>
            </section>

            <section className="panel section-card">
              <div className="panel-header">
                <h2>Add Node</h2>
                <span>weight</span>
              </div>
              <form onSubmit={handleAddNode} className="stack">
                <input value={nodeForm.nodeId} onChange={(e) => setNodeForm((c) => ({ ...c, nodeId: e.target.value }))} placeholder="node-id (auto if blank)" />
                <input type="number" step="0.1" value={nodeForm.weight} onChange={(e) => setNodeForm((c) => ({ ...c, weight: e.target.value }))} placeholder="node weight" />
                <button type="submit" disabled={!activeGraphId}>Add node</button>
              </form>
            </section>

            <section className="panel section-card">
              <div className="panel-header">
                <h2>Add Edge</h2>
                <span>manual</span>
              </div>
              <form onSubmit={handleAddEdge} className="stack">
                <input value={edgeForm.source} onChange={(e) => setEdgeForm((c) => ({ ...c, source: e.target.value }))} placeholder="source" />
                <input value={edgeForm.target} onChange={(e) => setEdgeForm((c) => ({ ...c, target: e.target.value }))} placeholder="target" />
                <button type="submit" disabled={!activeGraphId}>Add edge</button>
              </form>
              <div className="inline-actions">
                <button
                  type="button"
                  className={connectMode ? "danger-button" : "ghost-button"}
                  onClick={() => {
                    setConnectMode((current) => !current);
                    setPendingConnectionSource("");
                  }}
                  disabled={!activeGraphId}
                >
                  {connectMode ? "Exit connect mode" : "Connect nodes"}
                </button>
                <button type="button" className="ghost-button" disabled={!selectedEdge} onClick={handleDeleteSelectedEdge}>
                  Delete edge
                </button>
              </div>
            </section>

            <section className="panel section-card">
              <div className="panel-header">
                <h2>Algorithms</h2>
                <span>topology</span>
              </div>
              <div className="algorithm-grid algorithm-grid--nav">
                <button onClick={() => executeAlgorithm("Topological sort", () => api.getTopologicalSort(activeGraphId))} disabled={!activeGraphId}>Topological sort</button>
                <button onClick={() => executeAlgorithm("Topological levels", () => api.getTopologicalLevels(activeGraphId))} disabled={!activeGraphId}>Topological levels</button>
                <button onClick={() => executeAlgorithm("Transitive reduction", () => api.getTransitiveReduction(activeGraphId))} disabled={!activeGraphId}>Transitive reduction</button>
                <button onClick={() => executeAlgorithm("Transitive closure", () => api.getTransitiveClosure(activeGraphId))} disabled={!activeGraphId}>Transitive closure</button>
                <button onClick={() => activeNodeId && executeAlgorithm(`Descendants of ${activeNodeId}`, () => api.getDescendants(activeGraphId, activeNodeId))} disabled={!activeGraphId || !activeNodeId}>Descendants</button>
                <button onClick={() => activeNodeId && executeAlgorithm(`Ancestors of ${activeNodeId}`, () => api.getAncestors(activeGraphId, activeNodeId))} disabled={!activeGraphId || !activeNodeId}>Ancestors</button>
                <button onClick={() => executeAlgorithm("Strong components", () => api.getStrongComponents(activeGraphId))} disabled={!activeGraphId}>Strong components</button>
                <button onClick={() => executeAlgorithm("Weak components", () => api.getWeakComponents(activeGraphId))} disabled={!activeGraphId}>Weak components</button>
              </div>
            </section>

            <section className="panel section-card">
              <div className="panel-header">
                <h2>Pathfinding</h2>
                <span>{pathSelection.source || "none"} {"->"} {pathSelection.target || "none"}</span>
              </div>
              <div className="inline-actions">
                <button type="button" disabled={!activeGraphId || !pathSelection.source || !pathSelection.target} onClick={() => executeAlgorithm("Shortest path", () => api.getShortestPath(activeGraphId, pathSelection))}>Run BFS</button>
                <button type="button" className="ghost-button" disabled={!activeGraphId || !pathSelection.source || !pathSelection.target} onClick={() => executeAlgorithm("Has path", () => api.getHasPath(activeGraphId, pathSelection.source, pathSelection.target))}>Check path</button>
              </div>
              <form
                className="stack"
                onSubmit={(event) => {
                  event.preventDefault();
                  executeAlgorithm("Dijkstra path", () =>
                    api.getDijkstraPath(activeGraphId, {
                      source: pathSelection.source,
                      target: pathSelection.target,
                      weights: parseWeightedEdges(dijkstraForm.weightsText),
                    }),
                  );
                }}
              >
                <textarea className="compact-textarea" value={dijkstraForm.weightsText} onChange={(e) => setDijkstraForm({ weightsText: e.target.value })} rows={3} placeholder={'[{"source":"a","target":"b","weight":2}]'} />
                <button type="submit" disabled={!activeGraphId || !pathSelection.source || !pathSelection.target}>Run Dijkstra</button>
              </form>
            </section>

            <section className="panel section-card">
              <div className="panel-header">
                <h2>Graph Ops</h2>
                <span>maintenance</span>
              </div>
              <form onSubmit={handleResetGraph} className="stack">
                <textarea className="compact-textarea" value={resetForm.adjacencyText} onChange={(e) => setResetForm({ adjacencyText: e.target.value })} rows={5} placeholder='{"a":["b"]}' />
                <button type="submit" disabled={!activeGraphId}>Reset graph</button>
              </form>
              <div className="inline-actions">
                <button type="button" className="ghost-button" onClick={() => refreshActiveGraph(activeGraphId)}>Refresh</button>
                <button type="button" className="danger-button" onClick={handleDeleteGraph} disabled={!activeGraphId}>Delete graph</button>
              </div>
            </section>

            <section className="panel section-card">
              <div className="panel-header">
                <h2>Critical Path</h2>
                <span>weights</span>
              </div>
              <form
                className="stack"
                onSubmit={(event) => {
                  event.preventDefault();
                  executeAlgorithm("Critical path", () => api.getCriticalPath(activeGraphId, { durations: parseJsonObject(criticalPathForm.durationsText) }));
                }}
              >
                <textarea className="compact-textarea" value={criticalPathForm.durationsText} onChange={(e) => setCriticalPathForm({ durationsText: e.target.value })} rows={4} placeholder={'{"a": 2, "b": 4}'} />
                <button type="submit" disabled={!activeGraphId}>Run critical path</button>
              </form>
            </section>
          </div>
        ) : (
          <div className="control-nav__collapsed">
            <button type="button" className="graph-chip is-active" onClick={() => setNavOpen(true)}>
              Controls
            </button>
          </div>
        )}
      </aside>

      <main className="main-stage">
        <section className="canvas-stage canvas-stage--full">
          <div className="canvas-toolbar">
            <div>
              <p className="eyebrow">Graph Workspace</p>
              <h2>{activeGraphId || "No graph selected"}</h2>
            </div>
            <div className="status-pills">
              <span className={`status-pill ${graphSummary?.is_valid ? "is-valid" : "is-invalid"}`}>
                {graphSummary?.is_valid ? "Valid DAG" : "Invalid"}
              </span>
              {connectMode && pendingConnectionSource && <span className="status-pill is-armed">Connect from: {pendingConnectionSource}</span>}
              {selectedNodeIds.length > 0 && <span className="status-pill">Selected: {selectedNodeIds.join(" -> ")}</span>}
              {selectedEdge && <span className="status-pill">Edge: {selectedEdge.id}</span>}
            </div>
          </div>

          {loading ? (
            <div className="graph-canvas graph-canvas--empty">Loading graph workspace...</div>
          ) : (
            <GraphCanvas
              summary={graphSummary}
              layout={layout}
              selectedNodeIds={selectedNodeIds}
              selectedEdgeId={selectedEdge?.id}
              connectMode={connectMode}
              pendingConnectionSource={pendingConnectionSource}
              onSelectEdge={(edge) => {
                setSelectedEdge(edge);
                setPendingConnectionSource("");
              }}
              onNodeActivate={handleNodeActivate}
            />
          )}

          {graphSummary && (
            <div className="canvas-footer">
              <span>Roots: {graphSummary.roots.join(", ") || "none"}</span>
              <span>Leaves: {graphSummary.leaves.join(", ") || "none"}</span>
              <span>{graphSummary.validation_message}</span>
            </div>
          )}
        </section>

        <section className="panel inspector-band">
          <div className="panel-header">
            <h2>Inspector</h2>
            <span>selection</span>
          </div>
          {activeNodeId ? (
            <div className="inspector-grid">
              <div>
                <strong>{activeNodeId}</strong>
                <p>Incoming: {selectedNodeDetails.incoming.map((edge) => edge.source).join(", ") || "none"}</p>
                <p>Outgoing: {selectedNodeDetails.outgoing.map((edge) => edge.target).join(", ") || "none"}</p>
              </div>
              <form onSubmit={handleUpdateSelectedWeight} className="stack">
                <label>Node weight</label>
                <input type="number" step="0.1" value={weightDraft} onChange={(e) => setWeightDraft(e.target.value)} />
                <button type="submit">Update weight</button>
              </form>
              <div className="inline-actions">
                <button type="button" className="ghost-button" onClick={handleDeleteSelectedNode}>Delete selected node</button>
              </div>
            </div>
          ) : selectedEdge ? (
            <div className="inspector-grid">
              <div>
                <strong>{selectedEdge.id}</strong>
                <p>Source: {selectedEdge.source}</p>
                <p>Target: {selectedEdge.target}</p>
              </div>
            </div>
          ) : (
            <p className="muted">Click nodes to select up to two for path algorithms. Enable connect mode to create edges.</p>
          )}
        </section>

        <section className="panel result-panel result-panel--bottom">
          <div className="panel-header">
            <h2>Results</h2>
            <span>json</span>
          </div>
          {error ? <div className="error-banner">{error}</div> : null}
          <pre>{algorithmResult ? JSON.stringify(algorithmResult, null, 2) : "Run an algorithm or graph action to inspect the output."}</pre>
        </section>
      </main>
    </div>
  );
}

function parseWeightedEdges(text) {
  return parseJsonArray(text || "[]");
}

function parseJsonArray(text) {
  try {
    const parsed = JSON.parse(text || "[]");
    if (!Array.isArray(parsed)) throw new Error("Expected a JSON array");
    return parsed;
  } catch (error) {
    throw new Error(`Invalid JSON array: ${error.message}`);
  }
}

function parseJsonObject(text) {
  try {
    const parsed = JSON.parse(text || "{}");
    if (!parsed || Array.isArray(parsed) || typeof parsed !== "object") throw new Error("Expected a JSON object");
    return parsed;
  } catch (error) {
    throw new Error(`Invalid JSON object: ${error.message}`);
  }
}

function pushNodeSelection(current, nodeId) {
  const unique = current.filter((value) => value !== nodeId);
  return [...unique, nodeId].slice(-2);
}

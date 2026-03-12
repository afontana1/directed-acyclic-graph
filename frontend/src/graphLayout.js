export function buildGraphLayout(summary, levelsPayload, width, height, seed = 0) {
  const nodeIds = summary?.nodes || [];
  const adjacency = summary?.adjacency || {};
  const summaryEdges = summary?.edges || [];

  if (!nodeIds.length) {
    return { positions: {}, edges: [] };
  }

  const levels =
    levelsPayload?.levels?.length
      ? levelsPayload.levels
      : buildFallbackLevels(nodeIds, adjacency);

  const positions = {};
  const columnGap = width / (Math.max(levels.length, 1) + 1);

  levels.forEach((level, levelIndex) => {
    const rowGap = height / (level.length + 1);
    level.forEach((nodeId, rowIndex) => {
      positions[nodeId] = {
        x: columnGap * (levelIndex + 1),
        y: rowGap * (rowIndex + 1),
      };
    });
  });

  nodeIds.forEach((nodeId, index) => {
    if (!positions[nodeId]) {
      positions[nodeId] = {
        x: width * 0.82,
        y: ((index + 1) / (nodeIds.length + 1)) * height,
      };
    }
  });

  const edges = summaryEdges.length
    ? summaryEdges.map((edge) => ({
        source: edge.source,
        target: edge.target,
        id: edge.edge_id || `${edge.source}->${edge.target}`,
      }))
    : Object.entries(adjacency).flatMap(([source, targets]) =>
        targets.map((target) => ({
          source,
          target,
          id: `${source}->${target}`,
        })),
      );

  return { positions, edges, seed };
}

function buildFallbackLevels(nodeIds, adjacency) {
  const incoming = Object.fromEntries(nodeIds.map((nodeId) => [nodeId, 0]));
  Object.values(adjacency).forEach((targets) => {
    targets.forEach((target) => {
      incoming[target] = (incoming[target] || 0) + 1;
    });
  });

  const levels = [];
  let frontier = nodeIds.filter((nodeId) => incoming[nodeId] === 0);
  const visited = new Set();

  while (frontier.length) {
    levels.push(frontier);
    const next = [];
    frontier.forEach((nodeId) => {
      visited.add(nodeId);
      (adjacency[nodeId] || []).forEach((target) => {
        incoming[target] -= 1;
        if (incoming[target] === 0) {
          next.push(target);
        }
      });
    });
    frontier = next;
  }

  const remainder = nodeIds.filter((nodeId) => !visited.has(nodeId));
  if (remainder.length) {
    levels.push(remainder);
  }

  return levels;
}

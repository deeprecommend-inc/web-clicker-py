// Minimal Figma plugin: extract node-ids from current selection

function selectionSummary() {
  const sel = figma.currentPage.selection;
  const items = sel.map((n) => ({
    id: n.id,
    name: (n as any).name || n.type,
    type: n.type,
    page: figma.currentPage.name,
    parent: (n.parent && (n.parent as any).name) || undefined,
  }));
  return items;
}

function buildCurl(ids: string[]): string {
  const fileKey = figma.fileKey || "<file_key>";
  const idParam = encodeURIComponent(ids.join(","));
  return `curl -H 'X-FIGMA-TOKEN: <personal access token>' 'https://api.figma.com/v1/files/${fileKey}/nodes?ids=${idParam}'`;
}

function copy(text: string) {
  figma.clipboard.writeText(text);
  figma.notify("Copied to clipboard");
}

figma.on("run", () => {
  const items = selectionSummary();
  if (items.length === 0) {
    figma.notify("No selection. Select objects or frames.");
    // Optionally list top-level frames as guidance
    const topFrames = figma.currentPage.children.filter((n) => n.type === "FRAME");
    if (topFrames.length) {
      const sample = topFrames.slice(0, 5).map((f) => `${(f as any).name} (${f.id})`).join("\n");
      figma.notify(`Top frames:\n${sample}`, { timeout: 4000 });
    }
    figma.closePlugin();
    return;
  }

  // Copy IDs and a ready-to-run curl to clipboard
  const ids = items.map((i) => i.id);
  const payload = {
    fileKey: figma.fileKey,
    page: figma.currentPage.name,
    selection: items,
    curl: buildCurl(ids),
  };
  copy(JSON.stringify(payload, null, 2));

  // Zoom to selection for context
  figma.viewport.scrollAndZoomIntoView(figma.currentPage.selection);
  figma.closePlugin("Selection node-ids copied as JSON + cURL.");
});


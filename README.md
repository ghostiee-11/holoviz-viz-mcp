# holoviz-viz-mcp

An MCP server that gives AI assistants the ability to create **real, interactive** data visualizations using the HoloViz ecosystem (hvPlot, HoloViews, Panel).

Built as a prototype for [Panel #8396](https://github.com/holoviz/panel/issues/8396) — bringing HoloViz's visualization stack to any MCP-compatible AI assistant.

![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)
![Tests](https://img.shields.io/badge/tests-76%20passed-green.svg)
![Tools](https://img.shields.io/badge/MCP%20tools-19-purple.svg)
![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)

---

## Why this exists

Most AI viz tools generate static images or hand-roll JavaScript. This server takes a different approach: it uses **Panel's embed mode** to produce self-contained interactive HTML with the full Bokeh rendering pipeline. That means real pan/zoom/hover, proper linked selections, and actual Panel widgets — not a JavaScript approximation.

The key technical decision: `pn.pane.HoloViews(plot).save(buf, embed=True)` produces a standalone HTML document with all Bokeh JS/CSS inlined. No external server. No CDN dependency. Just a file you can open in any browser.

## What it can do

- **19 tools** covering data loading, transformation, visualization, annotation, crossfiltering, streaming, dashboards, and export
- **Dual output**: every viz returns both a PNG preview (renders inline in chat) and interactive HTML (full Bokeh interactivity)
- **Linked selections / crossfiltering**: brush points in one plot, all other views filter in real time — a HoloViews feature that only works with proper Panel rendering
- **Streaming visualizations**: live-updating charts with play/pause controls
- **Data transformations**: filter, groupby, pivot, derive, merge — so the AI can wrangle data before plotting
- **Annotations**: add threshold lines, highlight bands, text labels, markers to any plot
- **Multi-format loading**: CSV, JSON, Parquet, Excel, or URL
- **MCP Apps support**: `ui://holoviz/viewer` resource for in-chat interactive rendering

## Architecture

```
AI Assistant (Claude / ChatGPT / Copilot)
    |
    v  MCP Protocol (JSON-RPC over stdio)
+-----------------------------------------------+
|  holoviz-viz-mcp Server (FastMCP 3.1)          |
|                                                |
|  Data Layer:              Viz Layer:           |
|    load_data (csv/json/   create_plot (14      |
|      parquet/excel/url)     chart types)       |
|    load_sample_data       modify_plot          |
|    analyze_data           undo_plot            |
|    suggest_visualizations execute_code          |
|    transform_data                              |
|    merge_datasets         Advanced:            |
|                           create_crossfilter   |
|  Rendering:               create_streaming_plot|
|    hvPlot -> HoloViews    annotate_plot        |
|    -> Panel embed         overlay_plots        |
|    Output: PNG + HTML     create_dashboard     |
|                           export_plot          |
|  MCP Apps:                                     |
|    ui://holoviz/viewer                         |
+-----------------------------------------------+
```

## Quick start

```bash
git clone https://github.com/ghostiee-11/holoviz-viz-mcp.git
cd holoviz-viz-mcp
pip install -e ".[test]"

# Run the demo
python demos/quick_demo.py

# Run tests
pytest tests/ -v
```

## Use with Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "holoviz-viz": {
      "command": "holoviz-viz-mcp"
    }
  }
}
```

Then ask Claude: *"Load the iris dataset and create a scatter plot of sepal length vs width, colored by species"*

## Tools (19)

### Data Management (5 tools)

| Tool | What it does |
|------|-------------|
| `load_data` | Load data from CSV/JSON text, URL, or file path. Auto-detects Parquet/Excel/JSON from URL extension |
| `load_sample_data` | Built-in datasets: iris, penguins, tips, stocks |
| `list_datasets` | List all loaded datasets with shapes and columns |
| `analyze_data` | Statistical profile: dtypes, distributions, top correlations |
| `suggest_visualizations` | Auto-suggest plot types based on column types and relationships |

### Data Transformation (2 tools)

| Tool | What it does |
|------|-------------|
| `transform_data` | Filter, groupby, sort, derive columns, sample, drop nulls, pivot |
| `merge_datasets` | Join two datasets on shared columns (inner/left/right/outer) |

### Visualization (5 tools)

| Tool | What it does | Output |
|------|-------------|--------|
| `create_plot` | Create scatter/line/bar/barh/area/step/box/violin/hist/heatmap/hexbin/kde/contour/errorbars | PNG + HTML |
| `modify_plot` | Change title, colors, colormap, size, axis labels, legend | PNG + HTML |
| `undo_plot` | Revert to previous version | PNG + HTML |
| `list_plots` | List all plots with IDs and version counts | Text |
| `execute_code` | Run arbitrary hvPlot/HoloViews/Panel code | PNG + HTML |

### Advanced Visualization (4 tools)

| Tool | What it does | Output |
|------|-------------|--------|
| `create_crossfilter` | Linked brushing across multiple views — select in one, all update | PNG + HTML |
| `create_streaming_plot` | Live-updating chart with play/pause/reset controls | PNG + HTML |
| `annotate_plot` | Add hline/vline/hspan/vspan/text/point annotations | PNG + HTML |
| `overlay_plots` | Composite multiple plots onto shared axes | PNG + HTML |

### Dashboard & Export (3 tools)

| Tool | What it does | Output |
|------|-------------|--------|
| `create_dashboard` | Combine plots in column/row/tabs/grid layout | PNG + HTML |
| `get_plot_html` | Get raw interactive HTML for any plot | HTML |
| `export_plot` | Export to HTML, PNG, or SVG | Encoded content |

## Supported chart types

scatter, line, bar, barh, area, step, box, violin, hist, heatmap, hexbin, kde, contour, errorbars

## How the output works

Each visualization tool returns **three items** in a single MCP response:

1. **TextContent** — Plot ID and description (e.g. "Created plot 'plot_a1b2c3d4' (scatter: sepal_length vs sepal_width)")
2. **ImageContent** — PNG preview, base64-encoded. Renders inline in the chat UI
3. **EmbeddedResource** — Interactive HTML at `viz://plots/{id}`. Self-contained Bokeh document with pan, zoom, hover, save. No server needed

This dual-output pattern means the AI can show a quick preview in-chat while also providing the full interactive version.

## Crossfilter demo

The crossfilter tool creates linked views where brushing in one plot filters all others:

```python
# In Claude Desktop or any MCP client:
# "Load iris and create a crossfilter with scatter, histogram, and box plot"

# Behind the scenes, the server runs:
from holoviews.selection import link_selections

scatter = df.hvplot.scatter('sepal_length', 'sepal_width', c='species')
hist = df.hvplot.hist('petal_length')
box = df.hvplot.box('species', 'petal_width')

linked = link_selections(hv.Layout([scatter, hist, box]))
# -> Selecting points in the scatter filters the histogram and box plot in real time
```

This only works because we render through Panel's embed pipeline, not raw BokehJS.

## Streaming demo

The streaming tool creates live-updating charts:

```python
# "Create a streaming line chart"
# -> Returns HTML with play/pause controls and a random walk that updates every 500ms
```

## Testing

```bash
pytest tests/ -v
# 76 tests covering: state management, data tools, viz tools, transforms,
# crossfilter, streaming, annotations, export, server integration
```

## Project structure

```
src/holoviz_viz_mcp/
  server.py          # FastMCP entry point, tool registration
  state.py           # Dataset + plot state with versioning/undo
  rendering.py       # HoloViews -> PNG/HTML via Panel embed
  tools/
    data.py          # load, analyze, suggest, list, sample
    transform.py     # filter, groupby, pivot, derive, merge
    viz.py           # create, modify, undo, list, execute_code
    crossfilter.py   # linked selections across views
    streaming.py     # live-updating charts
    annotations.py   # hline, vline, spans, text, points, overlays
    dashboard.py     # layout composition
    export.py        # HTML/PNG/SVG export
  apps/
    viewer.html      # MCP Apps interactive viewer
tests/
  test_state.py      # 10 tests
  test_tools.py      # 14 tests
  test_transform.py  # 17 tests
  test_annotations.py # 15 tests
  test_crossfilter.py # 5 tests
  test_streaming.py  # 7 tests
  test_export.py     # 4 tests
  test_server.py     # 4 tests
```

## Technical notes

- **Panel embed vs raw BokehJS**: Most MCP viz tools use `bokeh.embed.json_item()` which gives you a static Bokeh document. Panel's `embed=True` mode goes further — it captures widget state, linked selections, and layout logic into a single HTML file. This is what makes crossfiltering and streaming work without a server.

- **Why hvPlot**: hvPlot provides a consistent `.hvplot()` API across pandas, xarray, dask, and geopandas DataFrames. One API, many backends.

- **State management**: Plots are versioned. Every `modify_plot` creates a new version; `undo_plot` reverts. This lets the AI iterate on visualizations without losing previous work.

- **Code execution**: The `execute_code` tool is the escape hatch for anything the structured tools can't do — custom HoloViews overlays, datashader pipelines, Panel widget layouts. It runs in a sandboxed namespace with pd, np, hv, pn, and all loaded datasets available.

## License

MIT

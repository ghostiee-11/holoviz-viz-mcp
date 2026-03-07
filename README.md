# holoviz-viz-mcp

**The most advanced MCP server for data visualization.** Give any AI assistant the power to create interactive charts, run statistical tests, perform auto-EDA, and build polished dashboards — all using the HoloViz ecosystem.

![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)
![Tests](https://img.shields.io/badge/tests-148%20passed-brightgreen.svg)
![Tools](https://img.shields.io/badge/MCP%20tools-36-purple.svg)
![MCP Apps](https://img.shields.io/badge/MCP%20Apps-8-orange.svg)
![Prompts](https://img.shields.io/badge/prompts-9-yellow.svg)
![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)
![Version](https://img.shields.io/badge/version-0.5.0-blue.svg)

---

## Why this exists

Most AI visualization tools generate static images or hand-roll JavaScript. This server uses **Panel's embed mode** to produce self-contained interactive HTML with the full Bokeh rendering pipeline — real pan/zoom/hover, linked selections, and Panel widgets. Not a JavaScript approximation.

```
pn.pane.HoloViews(plot).save(buf, embed=True)
```

One line. Standalone HTML. All Bokeh JS/CSS inlined. No server. No CDN. Open in any browser.

## Feature highlights

| Category | What you get |
|----------|-------------|
| **36 tools** | Data loading, transforms, 14 chart types, annotations, crossfiltering, streaming, dashboards, export, and more |
| **Intelligent analysis** | One-call auto-EDA, statistical testing (t-test, ANOVA, regression, chi-square), data quality scoring, natural language queries |
| **8 MCP Apps** | Specialized UI viewers for charts, dashboards, streaming, crossfilter, EDA reports, statistics, time series, and data quality |
| **9 workflow prompts** | Guided workflows for EDA, crossfiltering, statistics, time series, big data, comparisons, storytelling, dashboards, and data quality |
| **Big data** | Datashader-powered visualization for 10K-5M+ points |
| **Time series** | Rolling stats, trend decomposition, anomaly detection, multi-series comparison |
| **Dual output** | Every viz returns PNG preview (inline in chat) + interactive HTML (full Bokeh interactivity) |
| **Plot versioning** | Modify freely, undo anytime — every change creates a new version |
| **Session persistence** | Save/load entire analysis sessions as JSON |
| **8 sample datasets** | iris, penguins, tips, stocks, diamonds, gapminder, weather, earthquakes |
| **Professional templates** | Material Design, Bootstrap, and Fast Design dashboard layouts |

---

## Quick start

```bash
git clone https://github.com/ghostiee-11/holoviz-viz-mcp.git
cd holoviz-viz-mcp
pip install -e ".[test]"
```

### One-command setup for any AI client

```bash
bash setup.sh claude-desktop    # Claude Desktop
bash setup.sh claude-code       # Claude Code CLI
bash setup.sh cursor            # Cursor
bash setup.sh vscode            # VS Code Copilot
bash setup.sh all               # All clients at once
```

Restart your AI client and try:

> *"Load the iris dataset and create a scatter plot of sepal_length vs sepal_width, colored by species"*

> *"Run auto_eda on the diamonds dataset"*

> *"Test if sepal_length differs significantly between species using a t-test"*

See [DEMO_PROMPTS.md](DEMO_PROMPTS.md) for 12 ready-to-use demo prompts.

### Manual setup

<details>
<summary>Claude Desktop</summary>

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
</details>

<details>
<summary>Claude Code (CLI)</summary>

```bash
claude mcp add holoviz-viz -- holoviz-viz-mcp
```
</details>

<details>
<summary>Cursor</summary>

Add to `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "holoviz-viz": {
      "command": "holoviz-viz-mcp"
    }
  }
}
```
</details>

<details>
<summary>VS Code Copilot Chat</summary>

Add to `.vscode/settings.json`:

```json
{
  "github.copilot.chat.mcpServers": {
    "holoviz-viz": {
      "command": "holoviz-viz-mcp"
    }
  }
}
```
</details>

---

## Tools (36)

### Data Management (5)

| Tool | Description |
|------|------------|
| `load_data` | Load from CSV/JSON text, URL, or file. Auto-detects Parquet/Excel/JSON from extension |
| `load_sample_data` | 8 built-in datasets: iris, penguins, tips, stocks, diamonds, gapminder, weather, earthquakes |
| `list_datasets` | List all loaded datasets with shapes and columns |
| `analyze_data` | Statistical profile with distributions, correlations, and data types |
| `suggest_visualizations` | Auto-recommend plot types based on column characteristics |

### Data Transformation (2)

| Tool | Description |
|------|------------|
| `transform_data` | Filter, groupby, sort, derive columns, sample, drop nulls, pivot |
| `merge_datasets` | Join two datasets on shared columns (inner/left/right/outer) |

### Visualization (5)

| Tool | Description | Output |
|------|------------|--------|
| `create_plot` | 14 chart types: scatter, line, bar, barh, area, step, box, violin, hist, heatmap, hexbin, kde, contour, errorbars | PNG + HTML |
| `modify_plot` | Change title, colors, colormap, size, axis labels, legend position | PNG + HTML |
| `undo_plot` | Revert to any previous version | PNG + HTML |
| `list_plots` | List all plots with IDs and version counts | Text |
| `execute_code` | Run arbitrary hvPlot/HoloViews/Panel code | PNG + HTML |

### Advanced Visualization (6)

| Tool | Description | Output |
|------|------------|--------|
| `create_crossfilter` | Linked brushing across views — select in one, all update | PNG + HTML |
| `create_streaming_plot` | Live-updating chart with play/pause/reset controls | PNG + HTML |
| `annotate_plot` | Add hline/vline/hspan/vspan/text/point/arrow annotations | PNG + HTML |
| `overlay_plots` | Composite multiple plots onto shared axes | PNG + HTML |
| `create_datashader_plot` | Big data visualization for 10K-5M+ points | PNG + HTML |
| `time_series_analysis` | Rolling stats, decomposition, anomaly detection, multi-series comparison | PNG + HTML |

### Interactive (4)

| Tool | Description |
|------|------------|
| `handle_click` | Process chart clicks — returns percentile, outlier status, group context |
| `set_theme` | Set global theme: default, dark, midnight |
| `launch_panel` | Open any chart as a full Panel app in the browser |
| `stop_panel` | Stop a running Panel server |

### Dashboard & Export (3)

| Tool | Description | Output |
|------|------------|--------|
| `create_dashboard` | Combine plots in column/row/tabs/grid with Material/Bootstrap/Fast templates | PNG + HTML |
| `get_plot_html` | Get raw interactive HTML for embedding | HTML |
| `export_plot` | Export to HTML, PNG, or SVG | Encoded |

### Intelligent Analysis (4)

| Tool | Description | Output |
|------|------------|--------|
| `auto_eda` | One-call complete EDA: distributions, correlations, missing data, outliers, narrative insights | PNG + HTML |
| `statistical_test` | T-test, correlation, regression, chi-square, normality, ANOVA — real p-values + diagnostic plots | PNG + HTML |
| `data_quality_report` | Missing values, outliers, type validation, duplicates, quality score (0-100) | PNG + HTML |
| `compare_datasets` | Side-by-side statistical comparison of two datasets | Text |

### Natural Language (1)

| Tool | Description |
|------|------------|
| `natural_language_query` | Plain English -> structured execution plan. "Show sales by region where revenue > 1M" -> filter + groupby + bar chart |

### Utility (6)

| Tool | Description |
|------|------------|
| `describe_plot` | AI-readable plot description for accessibility and context |
| `clone_plot` | Duplicate a plot for independent modification |
| `get_data_sample` | Return formatted data rows for AI context |
| `save_session` | Persist datasets + plot specs to JSON |
| `load_session` | Restore a saved session |
| `generate_large_dataset` | Generate synthetic data (clusters/spiral/grid/uniform, up to 5M points) |

---

## MCP Apps (8 interactive viewers)

| Resource URI | Viewer | Key features |
|-------------|--------|-------------|
| `ui://holoviz/viz` | Chart Viewer | Theme toggle, save, open in browser |
| `ui://holoviz/dashboard` | Dashboard Viewer | Multi-panel layout with stats sidebar |
| `ui://holoviz/stream` | Stream Viewer | Live pulse indicator, status bar |
| `ui://holoviz/crossfilter` | Crossfilter Viewer | Linked brush hint, open full size |
| `ui://holoviz/eda` | EDA Report | Tabbed insights/charts, completion badge |
| `ui://holoviz/statistics` | Statistics Viewer | P-value highlighting (green/red), side-by-side results+chart |
| `ui://holoviz/timeseries` | Time Series Viewer | Metrics bar, analysis type badge |
| `ui://holoviz/quality` | Quality Report | Score gauge (0-100, color-coded), issue severity cards |

---

## Workflow Prompts (9)

Pre-built step-by-step guides that the AI follows:

| Prompt | Purpose |
|--------|---------|
| `eda_workflow` | Complete exploratory data analysis |
| `crossfilter_workflow` | Build linked brushing dashboards |
| `data_quality_workflow` | Assess and clean data quality |
| `statistical_analysis_workflow` | Rigorous hypothesis testing |
| `storytelling_workflow` | Data storytelling with annotations |
| `time_series_workflow` | Temporal analysis and trend detection |
| `big_data_workflow` | Datashader visualization for large datasets |
| `comparison_workflow` | Compare groups or datasets |
| `dashboard_design_workflow` | Polished, presentation-ready dashboards |

---

## Architecture

```
AI Assistant (Claude / Copilot / Cursor / any MCP client)
    |
    v  MCP Protocol (JSON-RPC 2.0 over stdio)
+------------------------------------------------------------------+
|  holoviz-viz-mcp Server (FastMCP 3.1)                             |
|                                                                   |
|  Data Layer (7 tools)        Viz Layer (11 tools)                 |
|    load_data, analyze_data     create_plot (14 chart types)       |
|    suggest_visualizations      crossfilter, streaming, datashader |
|    transform_data, merge       annotate, overlay, time_series     |
|                                                                   |
|  Intelligence Layer (5 tools)  Utility Layer (6 tools)            |
|    auto_eda                    describe_plot, clone_plot           |
|    statistical_test            get_data_sample                    |
|    data_quality_report         save/load_session                  |
|    natural_language_query      generate_large_dataset             |
|                                                                   |
|  Rendering Pipeline            State Manager                      |
|    hvPlot -> HoloViews           Versioned plots with undo        |
|    -> Panel embed=True           Dataset storage                  |
|    Output: PNG + HTML            Session persistence              |
|                                                                   |
|  8 MCP Apps  |  9 Prompts  |  3 Dashboard Templates              |
+------------------------------------------------------------------+
```

---

## How the output works

Each visualization tool returns **three items** in a single MCP response:

1. **TextContent** — Plot ID and description
2. **ImageContent** — PNG preview (renders inline in chat)
3. **EmbeddedResource** — Interactive HTML at `viz://plots/{id}` (self-contained Bokeh document)

This dual-output pattern means the AI shows a quick preview while providing the full interactive version.

---

## Examples

### Auto-EDA (one call, complete analysis)

```
> "Run auto_eda on the diamonds dataset"

Returns: 6+ charts (distributions, correlations, categories, scatter),
narrative insights (skewness, outliers, strongest correlations),
all in a single tool call.
```

### Statistical testing with real p-values

```
> "Test if sepal_length differs between iris species"

Returns: t-statistic, p-value, Cohen's d effect size,
box plot comparing groups, significance assessment.
```

### Crossfilter (linked brushing)

```python
# Behind the scenes:
from holoviews.selection import link_selections
linked = link_selections(hv.Layout([scatter, hist, box]))
# Brush in scatter -> histogram and box plot filter in real time
```

### Time series decomposition

```
> "Decompose the weather temperature into trend, seasonal, and residual"

Returns: 4-panel decomposition plot + trend stats + seasonal amplitude.
```

### Natural language queries

```
> natural_language_query("iris", "compare sepal_length by species")

Returns structured plan:
  Step 1: transform_data('iris', 'groupby', group_by='species', agg='mean')
  Step 2: create_plot('iris_grouped', 'bar', x='species', y='sepal_length')
```

---

## Demos

```bash
python demos/quick_demo.py                # Full feature tour
python demos/showcase_stock_analysis.py   # Stock prices + annotations + dashboard
python demos/showcase_ml_evaluator.py     # Feature importance + confusion matrix + crossfilter
```

---

## Testing

```bash
pytest tests/ -v
# 148 tests across 16 test files covering:
# state, data, viz, transforms, crossfilter, streaming, annotations,
# export, interaction, auto-EDA, statistics, data quality, NLQ,
# big data, time series, utilities, server integration
```

---

## Project structure

```
src/holoviz_viz_mcp/
  server.py            # FastMCP entry: 36 tools, 8 resources, 9 prompts
  state.py             # Dataset + plot state with versioning/undo
  rendering.py         # HoloViews -> PNG/HTML via Panel embed (+ Material/Bootstrap/Fast templates)
  tools/
    data.py            # load, analyze, suggest, list, sample (8 datasets)
    transform.py       # filter, groupby, pivot, derive, merge
    viz.py             # create, modify, undo, list, execute_code
    crossfilter.py     # linked selections via hv.link_selections
    streaming.py       # live-updating charts with BokehJS streaming
    annotations.py     # hline, vline, spans, text, points, arrows, overlays
    dashboard.py       # layout composition with template support
    export.py          # HTML/PNG/SVG export
    interact.py        # handle_click, set_theme, launch/stop_panel
    auto_eda.py        # one-call complete exploratory analysis
    statistics.py      # t-test, correlation, regression, chi2, normality, ANOVA
    data_quality.py    # quality report + dataset comparison
    nlq.py             # natural language query interpretation
    bigdata.py         # datashader + synthetic data generation
    timeseries.py      # rolling stats, decomposition, anomaly detection
    utils.py           # describe, clone, sample, session management
  apps/
    viz.html           # Chart viewer with toolbar
    dashboard.html     # Dashboard viewer with stats
    stream.html        # Streaming viewer with pulse indicator
    crossfilter.html   # Crossfilter viewer with brush hints
    eda.html           # EDA report with tabbed insights
    statistics.html    # Statistics viewer with p-value highlights
    timeseries.html    # Time series viewer with metrics
    quality.html       # Quality report with score gauge
tests/                 # 148 tests across 16 files
demos/                 # 3 showcase scripts
```

---

## Technical notes

- **Panel embed vs raw BokehJS**: Most MCP viz tools use `bokeh.embed.json_item()` for static Bokeh. Panel's `embed=True` captures widget state, linked selections, and layout logic into standalone HTML. This is what makes crossfiltering work without a server.

- **Why hvPlot**: Consistent `.hvplot()` API across pandas, xarray, dask, and geopandas. One API, many backends.

- **State management**: Plots are versioned. Every `modify_plot` creates a new version; `undo_plot` reverts. The AI iterates freely without losing previous work.

- **Statistical rigor**: Uses scipy.stats for real hypothesis testing — actual p-values, effect sizes, confidence intervals. Not approximations.

- **Code execution**: `execute_code` is the escape hatch — run arbitrary HoloViews/Panel code in a sandboxed namespace with pd, np, hv, pn, and all loaded datasets.

- **Dashboard templates**: `create_dashboard` supports `template_style='material'` (Material Design), `'bootstrap'` (Bootstrap), and `'fast'` (Fast Design) for polished, professional output.

---

## Dependencies

Core: `fastmcp`, `holoviews`, `hvplot`, `panel`, `bokeh`, `pandas`, `numpy`, `scipy`

Optional: `openpyxl` (Excel), `pyarrow` (Parquet), `scikit-learn` (sample data)

## License

MIT

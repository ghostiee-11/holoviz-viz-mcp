"""HoloViz MCP Server — Create interactive visualizations via AI assistants.

Architecture:
  - Tools return dual output: PNG (inline chat preview) + HTML (interactive Panel embed)
  - 4 MCP Apps resources provide specialized UI viewers (viz, dashboard, stream, crossfilter)
  - Panel's embed mode produces self-contained HTML with all Bokeh JS/CSS inlined
  - State manager tracks datasets and plot versions with undo support
  - Bidirectional: handle_click processes chart click events for AI insights
"""

from __future__ import annotations

from pathlib import Path

import holoviews as hv
import panel as pn
from fastmcp import FastMCP

hv.extension("bokeh")
pn.extension(inline=True)

mcp = FastMCP(
    "holoviz-viz-mcp",
    instructions=(
        "You are a data visualization assistant powered by HoloViz. "
        "You can create interactive plots using hvPlot and HoloViews, "
        "analyze datasets, modify existing plots, and build dashboards with Panel. "
        "When the user provides data, first use analyze_data to understand it, "
        "then create appropriate visualizations. "
        "Plots are returned as both PNG previews and interactive HTML. "
        "Use handle_click to process chart click events for AI-driven insights. "
        "Use create_crossfilter for linked brushing across multiple views."
    ),
)


# ── Register tools ────────────────────────────────────────────────

from .tools.data import (  # noqa: E402
    analyze_data,
    list_datasets,
    load_data,
    load_sample_data,
    suggest_visualizations,
)
from .tools.viz import create_plot, execute_code, list_plots, modify_plot, undo_plot  # noqa: E402
from .tools.dashboard import create_dashboard, get_plot_html  # noqa: E402
from .tools.transform import transform_data, merge_datasets  # noqa: E402
from .tools.crossfilter import create_crossfilter  # noqa: E402
from .tools.streaming import create_streaming_plot  # noqa: E402
from .tools.annotations import annotate_plot, overlay_plots  # noqa: E402
from .tools.export import export_plot  # noqa: E402
from .tools.interact import handle_click, set_theme, launch_panel, stop_panel  # noqa: E402

# Data tools
mcp.tool()(load_data)
mcp.tool()(list_datasets)
mcp.tool()(analyze_data)
mcp.tool()(suggest_visualizations)
mcp.tool()(load_sample_data)

# Data transformation tools
mcp.tool()(transform_data)
mcp.tool()(merge_datasets)

# Visualization tools
mcp.tool()(create_plot)
mcp.tool()(modify_plot)
mcp.tool()(undo_plot)
mcp.tool()(list_plots)
mcp.tool()(execute_code)

# Advanced visualization tools
mcp.tool()(create_crossfilter)
mcp.tool()(create_streaming_plot)
mcp.tool()(annotate_plot)
mcp.tool()(overlay_plots)

# Interactive tools
mcp.tool()(handle_click)
mcp.tool()(set_theme)
mcp.tool()(launch_panel)
mcp.tool()(stop_panel)

# Dashboard & export tools
mcp.tool()(create_dashboard)
mcp.tool()(get_plot_html)
mcp.tool()(export_plot)


# ── MCP Apps: 4 UI resources ─────────────────────────────────────

APPS_DIR = Path(__file__).parent / "apps"

VIZ_HTML = (APPS_DIR / "viz.html").read_text()
DASHBOARD_HTML = (APPS_DIR / "dashboard.html").read_text()
STREAM_HTML = (APPS_DIR / "stream.html").read_text()
CROSSFILTER_HTML = (APPS_DIR / "crossfilter.html").read_text()


@mcp.resource(
    "ui://holoviz/viz",
    name="Chart Viewer",
    description="Interactive chart viewer with toolbar — theme toggle, save, open in browser",
    mime_type="text/html",
    app=True,
)
def viz_resource() -> str:
    return VIZ_HTML


@mcp.resource(
    "ui://holoviz/dashboard",
    name="Dashboard Viewer",
    description="Multi-panel dashboard viewer with summary stats and theme toggle",
    mime_type="text/html",
    app=True,
)
def dashboard_resource() -> str:
    return DASHBOARD_HTML


@mcp.resource(
    "ui://holoviz/stream",
    name="Live Stream Viewer",
    description="Live-updating streaming chart viewer with status indicators",
    mime_type="text/html",
    app=True,
)
def stream_resource() -> str:
    return STREAM_HTML


@mcp.resource(
    "ui://holoviz/crossfilter",
    name="Crossfilter Viewer",
    description="Linked selections viewer — brush in one plot to filter all others",
    mime_type="text/html",
    app=True,
)
def crossfilter_resource() -> str:
    return CROSSFILTER_HTML


# ── Prompts ───────────────────────────────────────────────────────


@mcp.prompt()
def eda_workflow(data_description: str) -> str:
    """Step-by-step exploratory data analysis workflow.

    Args:
        data_description: Brief description of the dataset to analyze
    """
    return (
        f"Perform exploratory data analysis on: {data_description}\n\n"
        "Follow this workflow:\n"
        "1. Use load_sample_data or load_data to get the data\n"
        "2. Use analyze_data to get a comprehensive data profile\n"
        "3. Use suggest_visualizations to get recommended plot types\n"
        "4. Create the top 3 suggested visualizations with create_plot\n"
        "5. Look for patterns, outliers, and relationships\n"
        "6. Create a final dashboard combining the best views with create_dashboard"
    )


@mcp.prompt()
def crossfilter_workflow(data_description: str) -> str:
    """Guide for creating a crossfilter exploration dashboard.

    Args:
        data_description: Brief description of the dataset
    """
    return (
        f"Create a crossfilter exploration for: {data_description}\n\n"
        "Steps:\n"
        "1. Load the data with load_data or load_sample_data\n"
        "2. Use analyze_data to identify numeric and categorical columns\n"
        "3. Pick 2-3 complementary views (scatter + hist + box works well)\n"
        "4. Use create_crossfilter with these views\n"
        "5. The output has linked selections — brush in any plot to filter all others\n"
        "6. Try annotating interesting findings with annotate_plot"
    )


# ── Entry point ───────────────────────────────────────────────────


def main():
    mcp.run()


if __name__ == "__main__":
    main()

"""HoloViz MCP Server — Create interactive visualizations via AI assistants.

Architecture:
  - Tools return dual output: PNG (inline chat preview) + HTML (interactive Panel embed)
  - MCP Apps resources provide interactive UI viewers rendered in sandboxed iframes
  - Panel's embed mode produces self-contained HTML with all Bokeh JS/CSS inlined
  - State manager tracks datasets and plot versions with undo support
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
        "Plots are returned as both PNG previews and interactive HTML."
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

# Dashboard & export tools
mcp.tool()(create_dashboard)
mcp.tool()(get_plot_html)
mcp.tool()(export_plot)


# ── MCP Apps: UI resources ────────────────────────────────────────

VIEWER_HTML = (Path(__file__).parent / "apps" / "viewer.html").read_text()


@mcp.resource(
    "ui://holoviz/viewer",
    name="HoloViz Visualization Viewer",
    description="Interactive visualization viewer — renders Panel-embedded charts in-chat",
    mime_type="text/html",
    app=True,
)
def viz_viewer_resource() -> str:
    """Serve the MCP Apps interactive viewer."""
    return VIEWER_HTML


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


# ── Entry point ───────────────────────────────────────────────────


def main():
    mcp.run()


if __name__ == "__main__":
    main()

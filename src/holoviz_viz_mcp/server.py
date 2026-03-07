"""HoloViz MCP Server — Create interactive visualizations via AI assistants.

Architecture:
  - Tools return dual output: PNG (inline chat preview) + HTML (interactive Panel embed)
  - 4 MCP Apps resources provide specialized UI viewers (viz, dashboard, stream, crossfilter)
  - Panel's embed mode produces self-contained HTML with all Bokeh JS/CSS inlined
  - State manager tracks datasets and plot versions with undo support
  - Bidirectional: handle_click processes chart click events for AI insights
  - Auto-EDA, statistical testing, and NLQ provide intelligent analysis
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
        "Use auto_eda for one-call exploratory analysis with multiple charts. "
        "Use statistical_test for rigorous hypothesis testing (t-test, correlation, regression). "
        "Use natural_language_query to interpret plain English data questions. "
        "Use data_quality_report for comprehensive data health checks. "
        "Use handle_click to process chart click events for AI-driven insights. "
        "Use create_crossfilter for linked brushing across multiple views. "
        "Use create_dashboard with template_style='material' for polished output."
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
from .tools.auto_eda import auto_eda  # noqa: E402
from .tools.statistics import statistical_test  # noqa: E402
from .tools.data_quality import data_quality_report, compare_datasets  # noqa: E402
from .tools.nlq import natural_language_query  # noqa: E402

# Data tools (5)
mcp.tool()(load_data)
mcp.tool()(list_datasets)
mcp.tool()(analyze_data)
mcp.tool()(suggest_visualizations)
mcp.tool()(load_sample_data)

# Data transformation tools (2)
mcp.tool()(transform_data)
mcp.tool()(merge_datasets)

# Visualization tools (5)
mcp.tool()(create_plot)
mcp.tool()(modify_plot)
mcp.tool()(undo_plot)
mcp.tool()(list_plots)
mcp.tool()(execute_code)

# Advanced visualization tools (4)
mcp.tool()(create_crossfilter)
mcp.tool()(create_streaming_plot)
mcp.tool()(annotate_plot)
mcp.tool()(overlay_plots)

# Interactive tools (4)
mcp.tool()(handle_click)
mcp.tool()(set_theme)
mcp.tool()(launch_panel)
mcp.tool()(stop_panel)

# Dashboard & export tools (3)
mcp.tool()(create_dashboard)
mcp.tool()(get_plot_html)
mcp.tool()(export_plot)

# Intelligent analysis tools (4)
mcp.tool()(auto_eda)
mcp.tool()(statistical_test)
mcp.tool()(data_quality_report)
mcp.tool()(compare_datasets)

# Natural language tools (1)
mcp.tool()(natural_language_query)


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


@mcp.prompt()
def data_quality_workflow(data_description: str) -> str:
    """Guide for comprehensive data quality assessment.

    Args:
        data_description: Brief description of the dataset to audit
    """
    return (
        f"Assess data quality for: {data_description}\n\n"
        "Steps:\n"
        "1. Load the data with load_data or load_sample_data\n"
        "2. Run data_quality_report to get a full quality assessment\n"
        "3. Check for missing values, outliers, and type issues\n"
        "4. Use transform_data to clean issues (drop_na, filter outliers)\n"
        "5. Run data_quality_report again on cleaned data to verify\n"
        "6. Use compare_datasets to compare original vs cleaned versions"
    )


@mcp.prompt()
def statistical_analysis_workflow(data_description: str) -> str:
    """Guide for rigorous statistical analysis with hypothesis testing.

    Args:
        data_description: Brief description of the analysis goal
    """
    return (
        f"Perform statistical analysis for: {data_description}\n\n"
        "Steps:\n"
        "1. Load the data and run analyze_data for an overview\n"
        "2. Check normality: statistical_test(dataset, 'normality', column)\n"
        "3. For comparing groups: statistical_test(dataset, 'ttest', column, group_column=...)\n"
        "4. For relationships: statistical_test(dataset, 'correlation', col_x, column_y=col_y)\n"
        "5. For prediction: statistical_test(dataset, 'regression', x_col, column_y=y_col)\n"
        "6. For categorical associations: statistical_test(dataset, 'chi2', col_x, column_y=col_y)\n"
        "7. Build a dashboard combining the diagnostic plots"
    )


@mcp.prompt()
def storytelling_workflow(data_description: str) -> str:
    """Guide for creating a data storytelling dashboard.

    Args:
        data_description: Brief description of the story to tell
    """
    return (
        f"Create a data story for: {data_description}\n\n"
        "Steps:\n"
        "1. Load the data and run auto_eda for a comprehensive overview\n"
        "2. Identify the key insight or narrative\n"
        "3. Create 3-4 focused plots that build the story progressively\n"
        "4. Annotate key findings with annotate_plot (thresholds, labels, highlights)\n"
        "5. Add statistical backing with statistical_test where relevant\n"
        "6. Combine into a polished dashboard: create_dashboard(..., template_style='material')\n"
        "7. Export with export_plot for sharing"
    )


# ── Entry point ───────────────────────────────────────────────────


def main():
    mcp.run()


if __name__ == "__main__":
    main()

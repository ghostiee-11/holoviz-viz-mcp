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

from functools import lru_cache
from pathlib import Path

from fastmcp import FastMCP


def _init_extensions() -> None:
    """Initialize HoloViews/Panel extensions once, lazily."""
    import holoviews as hv
    import panel as pn

    if not getattr(hv, "_mcp_initialized", False):
        hv.extension("bokeh")
        pn.extension(inline=True)
        hv._mcp_initialized = True


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


# ── Error-safe tool wrapper ───────────────────────────────────────

import functools
import logging
import traceback

_log = logging.getLogger("holoviz-viz-mcp")


def _safe_tool(fn):
    """Wrap a tool function so unhandled exceptions return an error message
    instead of crashing the MCP server (which forces a restart)."""

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            _init_extensions()
            return fn(*args, **kwargs)
        except KeyError as exc:
            return f"Error: {exc}"
        except Exception:
            tb = traceback.format_exc()
            _log.error("Tool %s failed:\n%s", fn.__name__, tb)
            return f"Error in {fn.__name__}: {tb.splitlines()[-1]}"

    return wrapper


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
from .tools.bigdata import create_datashader_plot, generate_large_dataset  # noqa: E402
from .tools.timeseries import time_series_analysis  # noqa: E402
from .tools.utils import (  # noqa: E402
    describe_plot, clone_plot, get_data_sample, save_session, load_session,
)

_all_tools = [
    # Data tools (5)
    load_data, list_datasets, analyze_data, suggest_visualizations, load_sample_data,
    # Data transformation tools (2)
    transform_data, merge_datasets,
    # Visualization tools (5)
    create_plot, modify_plot, undo_plot, list_plots, execute_code,
    # Advanced visualization tools (6)
    create_crossfilter, create_streaming_plot, annotate_plot, overlay_plots,
    create_datashader_plot, time_series_analysis,
    # Interactive tools (4)
    handle_click, set_theme, launch_panel, stop_panel,
    # Dashboard & export tools (3)
    create_dashboard, get_plot_html, export_plot,
    # Intelligent analysis tools (4)
    auto_eda, statistical_test, data_quality_report, compare_datasets,
    # Natural language tools (1)
    natural_language_query,
    # Utility tools (6)
    describe_plot, clone_plot, get_data_sample, save_session, load_session,
    generate_large_dataset,
]

for _fn in _all_tools:
    mcp.tool()(_safe_tool(_fn))


# ── MCP Apps: 8 UI resources ─────────────────────────────────────

APPS_DIR = Path(__file__).parent / "apps"


@lru_cache(maxsize=None)
def _load_app_html(name: str) -> str:
    return (APPS_DIR / f"{name}.html").read_text()


@mcp.resource(
    "ui://holoviz/viz",
    name="Chart Viewer",
    description="Interactive chart viewer with toolbar — theme toggle, save, open in browser",
    mime_type="text/html",
    app=True,
)
def viz_resource() -> str:
    return _load_app_html("viz")


@mcp.resource(
    "ui://holoviz/dashboard",
    name="Dashboard Viewer",
    description="Multi-panel dashboard viewer with summary stats and theme toggle",
    mime_type="text/html",
    app=True,
)
def dashboard_resource() -> str:
    return _load_app_html("dashboard")


@mcp.resource(
    "ui://holoviz/stream",
    name="Live Stream Viewer",
    description="Live-updating streaming chart viewer with status indicators",
    mime_type="text/html",
    app=True,
)
def stream_resource() -> str:
    return _load_app_html("stream")


@mcp.resource(
    "ui://holoviz/crossfilter",
    name="Crossfilter Viewer",
    description="Linked selections viewer — brush in one plot to filter all others",
    mime_type="text/html",
    app=True,
)
def crossfilter_resource() -> str:
    return _load_app_html("crossfilter")


@mcp.resource(
    "ui://holoviz/eda",
    name="EDA Report Viewer",
    description="Auto-EDA report with tabbed insights and multi-chart exploration",
    mime_type="text/html",
    app=True,
)
def eda_resource() -> str:
    return _load_app_html("eda")


@mcp.resource(
    "ui://holoviz/statistics",
    name="Statistics Viewer",
    description="Statistical test results with p-value highlights and diagnostic plots",
    mime_type="text/html",
    app=True,
)
def statistics_resource() -> str:
    return _load_app_html("statistics")


@mcp.resource(
    "ui://holoviz/timeseries",
    name="Time Series Viewer",
    description="Time series analysis with metrics, trend decomposition, and anomaly detection",
    mime_type="text/html",
    app=True,
)
def timeseries_resource() -> str:
    return _load_app_html("timeseries")


@mcp.resource(
    "ui://holoviz/quality",
    name="Data Quality Viewer",
    description="Data quality report with score gauge, issue cards, and diagnostic charts",
    mime_type="text/html",
    app=True,
)
def quality_resource() -> str:
    return _load_app_html("quality")


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


@mcp.prompt()
def time_series_workflow(data_description: str) -> str:
    """Guide for time series analysis and visualization.

    Args:
        data_description: Brief description of the time series data
    """
    return (
        f"Analyze time series data: {data_description}\n\n"
        "Steps:\n"
        "1. Load the data with load_data or load_sample_data('stocks') / load_sample_data('weather')\n"
        "2. Run time_series_analysis(dataset, date_col, value_col, analysis='overview') for rolling stats\n"
        "3. Run time_series_analysis(..., analysis='decomposition') to separate trend/seasonal/residual\n"
        "4. Run time_series_analysis(..., analysis='change_detection') to find anomalies\n"
        "5. If multiple series, use analysis='comparison' with group_by parameter\n"
        "6. Annotate key findings and build a dashboard"
    )


@mcp.prompt()
def big_data_workflow(data_description: str) -> str:
    """Guide for visualizing large datasets with datashader.

    Args:
        data_description: Brief description of the large dataset
    """
    return (
        f"Visualize large dataset: {data_description}\n\n"
        "Steps:\n"
        "1. Load data or generate_large_dataset(n_points=100000, distribution='clusters')\n"
        "2. Use create_datashader_plot(dataset, x_col, y_col) for density visualization\n"
        "3. Regular plots will be slow for >10K points — datashader rasterizes efficiently\n"
        "4. Try different colormaps: 'fire', 'inferno', 'viridis', 'blues'\n"
        "5. For exploration, sample first with transform_data(..., 'sample', limit=1000)\n"
        "6. Build a dashboard comparing datashader view vs sampled scatter"
    )


@mcp.prompt()
def comparison_workflow(data_description: str) -> str:
    """Guide for comparing multiple datasets or groups.

    Args:
        data_description: Brief description of what to compare
    """
    return (
        f"Compare data: {data_description}\n\n"
        "Steps:\n"
        "1. Load both datasets or split with transform_data(dataset, 'filter', ...)\n"
        "2. Use compare_datasets(dataset_a, dataset_b) for statistical comparison\n"
        "3. Use statistical_test(dataset, 'ttest', column, group_column=...) to test differences\n"
        "4. Create side-by-side plots: create_plot for each group\n"
        "5. Use overlay_plots to combine on shared axes for direct comparison\n"
        "6. Annotate significant differences and build a comparison dashboard"
    )


@mcp.prompt()
def dashboard_design_workflow(data_description: str) -> str:
    """Guide for designing a polished, presentation-ready dashboard.

    Args:
        data_description: Brief description of the dashboard goal
    """
    return (
        f"Design a dashboard for: {data_description}\n\n"
        "Steps:\n"
        "1. Load data and run auto_eda for initial exploration\n"
        "2. Choose 3-5 complementary views (mix chart types: scatter + bar + line + box)\n"
        "3. Create each plot with consistent theming (use theme='dark' or 'midnight')\n"
        "4. Add annotations: thresholds (hline/vline), highlights (hspan/vspan), labels (text)\n"
        "5. Combine with create_dashboard(plot_ids, template_style='material') for Material Design\n"
        "6. Try different layouts: 'tabs' for many plots, 'grid' for overview, 'row' for comparison\n"
        "7. Export with export_plot(plot_id, format='html') for sharing"
    )


# ── Entry point ───────────────────────────────────────────────────


def main():
    mcp.run()


if __name__ == "__main__":
    main()

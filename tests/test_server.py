"""Integration tests: verify the MCP server registers all tools and resources."""

import asyncio

import pytest

from holoviz_viz_mcp.server import mcp


@pytest.fixture
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


def test_server_has_all_tools():
    """Server should register all expected tools."""
    expected = {
        # Data tools
        "load_data", "list_datasets", "analyze_data",
        "suggest_visualizations", "load_sample_data",
        # Transform tools
        "transform_data", "merge_datasets",
        # Viz tools
        "create_plot", "modify_plot", "undo_plot", "list_plots",
        "execute_code",
        # Advanced viz tools
        "create_crossfilter", "create_streaming_plot",
        "annotate_plot", "overlay_plots",
        "create_datashader_plot", "time_series_analysis",
        # Interactive tools
        "handle_click", "set_theme", "launch_panel", "stop_panel",
        # Dashboard & export
        "create_dashboard", "get_plot_html", "export_plot",
        # Intelligent analysis tools
        "auto_eda", "statistical_test", "data_quality_report", "compare_datasets",
        # Natural language
        "natural_language_query",
        # Utility tools
        "describe_plot", "clone_plot", "get_data_sample",
        "save_session", "load_session", "generate_large_dataset",
    }
    tools = asyncio.run(mcp.list_tools())
    registered = {t.name for t in tools}
    assert expected.issubset(registered), f"Missing: {expected - registered}"


def test_server_has_8_resources():
    """Server should register 8 MCP Apps resources."""
    resources = asyncio.run(mcp.list_resources())
    uris = [str(r.uri) for r in resources]
    assert any("viz" in u for u in uris), f"No viz resource in {uris}"
    assert any("dashboard" in u for u in uris), f"No dashboard resource in {uris}"
    assert any("stream" in u for u in uris), f"No stream resource in {uris}"
    assert any("crossfilter" in u for u in uris), f"No crossfilter resource in {uris}"
    assert any("eda" in u for u in uris), f"No eda resource in {uris}"
    assert any("statistics" in u for u in uris), f"No statistics resource in {uris}"
    assert any("timeseries" in u for u in uris), f"No timeseries resource in {uris}"
    assert any("quality" in u for u in uris), f"No quality resource in {uris}"
    assert len(resources) == 8


def test_server_has_prompts():
    """Server should register all 9 workflow prompts."""
    prompts = asyncio.run(mcp.list_prompts())
    names = [p.name for p in prompts]
    assert "eda_workflow" in names
    assert "crossfilter_workflow" in names
    assert "data_quality_workflow" in names
    assert "statistical_analysis_workflow" in names
    assert "storytelling_workflow" in names
    assert "time_series_workflow" in names
    assert "big_data_workflow" in names
    assert "comparison_workflow" in names
    assert "dashboard_design_workflow" in names
    assert len(prompts) == 9


def test_tool_count():
    """Server should have exactly 36 tools."""
    tools = asyncio.run(mcp.list_tools())
    assert len(tools) == 36

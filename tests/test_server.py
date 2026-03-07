"""Integration tests: verify the MCP server registers all tools and resources."""

import asyncio

import pytest

from holoviz_viz_mcp.server import mcp


@pytest.fixture
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


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
        # Dashboard & export
        "create_dashboard", "get_plot_html", "export_plot",
    }
    tools = asyncio.run(mcp.list_tools())
    registered = {t.name for t in tools}
    assert expected.issubset(registered), f"Missing: {expected - registered}"


def test_server_has_viewer_resource():
    """Server should register the MCP Apps viewer resource."""
    resources = asyncio.run(mcp.list_resources())
    uris = [str(r.uri) for r in resources]
    assert any("viewer" in u for u in uris), f"No viewer resource in {uris}"


def test_server_has_eda_prompt():
    """Server should register the EDA workflow prompt."""
    prompts = asyncio.run(mcp.list_prompts())
    names = [p.name for p in prompts]
    assert "eda_workflow" in names


def test_tool_count():
    """Server should have exactly 19 tools."""
    tools = asyncio.run(mcp.list_tools())
    assert len(tools) == 19

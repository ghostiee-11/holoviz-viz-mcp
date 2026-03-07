"""Dashboard composition tools: combine plots into layouts."""

from __future__ import annotations

import base64

from mcp.types import EmbeddedResource, ImageContent, TextContent, TextResourceContents

from ..rendering import render_layout_to_html, render_to_png
from ..state import state

import holoviews as hv


def create_dashboard(
    plot_ids: str,
    title: str = "Dashboard",
    layout: str = "column",
) -> list:
    """Create a dashboard combining multiple plots.

    Returns PNG preview + interactive HTML with full Panel layout.

    Args:
        plot_ids: Comma-separated list of plot IDs to include
        title: Dashboard title
        layout: Layout type — 'column' (vertical), 'row' (horizontal), 'tabs', 'grid'
    """
    ids = [pid.strip() for pid in plot_ids.split(",")]
    plots = []
    for pid in ids:
        plots.append(state.get_plot(pid)["obj"])

    # PNG preview via HoloViews Layout
    if layout == "row":
        combined = hv.Layout(plots).cols(len(plots))
    elif layout == "grid":
        combined = hv.Layout(plots).cols(2)
    else:
        combined = hv.Layout(plots).cols(1)
    combined = combined.opts(title=title)
    png_bytes = render_to_png(combined, width=800, height=400 * len(plots))

    # Interactive HTML via Panel layout
    html = render_layout_to_html(plots, layout=layout, title=title)

    return [
        TextContent(
            type="text",
            text=f"Created dashboard '{title}' with {len(ids)} plots ({layout} layout)",
        ),
        ImageContent(
            type="image",
            data=base64.b64encode(png_bytes).decode(),
            mimeType="image/png",
        ),
        EmbeddedResource(
            type="resource",
            resource=TextResourceContents(
                uri=f"viz://dashboard/{title.lower().replace(' ', '-')}",
                mimeType="text/html",
                text=html,
            ),
        ),
    ]


def get_plot_html(plot_id: str) -> str:
    """Get a plot as standalone interactive HTML for embedding.

    Args:
        plot_id: ID of the plot
    """
    from ..rendering import render_to_html

    version = state.get_plot(plot_id)
    return render_to_html(version["obj"])

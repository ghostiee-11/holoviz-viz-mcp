"""Crossfilter tool: linked brushing across multiple views.

This is a Panel-native capability — selecting points in one plot filters
all other views in real time. Not possible with raw BokehJS output.
"""

from __future__ import annotations

import base64
from typing import Any

import holoviews as hv
import hvplot.pandas  # noqa: F401
from holoviews.selection import link_selections
from mcp.types import EmbeddedResource, ImageContent, TextContent, TextResourceContents

from ..rendering import render_to_html, render_to_png
from ..state import state


def create_crossfilter(
    dataset_name: str,
    views: str,
    color_by: str | None = None,
    title: str = "Crossfilter Dashboard",
) -> list:
    """Create a linked crossfilter dashboard where selections in one view filter all others.

    This is a HoloViews killer feature: brush/select points in any plot and all
    other plots update in real time to show only the matching data. Only possible
    with Panel-native rendering.

    Args:
        dataset_name: Name of the loaded dataset
        views: Semicolon-separated plot specs, each as 'type,x,y' (e.g. 'scatter,x,y;hist,x;box,cat,y')
        color_by: Column to color all views by
        title: Dashboard title
    """
    df = state.get_dataset(dataset_name)
    plots = []

    for view_spec in views.split(";"):
        parts = [p.strip() for p in view_spec.strip().split(",")]
        if len(parts) < 2:
            continue
        plot_type = parts[0]
        x = parts[1]
        y = parts[2] if len(parts) > 2 else None

        kwargs: dict[str, Any] = {"kind": plot_type, "x": x, "width": 350, "height": 280}
        if y:
            kwargs["y"] = y
        if color_by:
            kwargs["c" if plot_type == "scatter" else "color"] = color_by

        plots.append(df.hvplot(**kwargs))

    if not plots:
        return [TextContent(type="text", text="Error: no valid view specs. Use 'type,x,y;type,x' format.")]

    layout = hv.Layout(plots).cols(min(len(plots), 3))
    linked = link_selections(layout)

    plot_id = state.save_plot(linked, {"type": "crossfilter", "views": views, "color_by": color_by}, dataset_name)
    png_bytes = render_to_png(linked, width=800, height=400)
    html = render_to_html(linked, width=900, height=500)

    return [
        TextContent(type="text", text=(
            f"Created crossfilter '{plot_id}' with {len(plots)} linked views. "
            f"Select/brush in any plot to filter all others in real time."
        )),
        ImageContent(type="image", data=base64.b64encode(png_bytes).decode(), mimeType="image/png"),
        EmbeddedResource(
            type="resource",
            resource=TextResourceContents(uri=f"viz://plots/{plot_id}", mimeType="text/html", text=html),
        ),
    ]

"""Annotation and overlay tools: add markers, lines, bands, and text to plots."""

from __future__ import annotations

import base64
from typing import Any

import holoviews as hv
import numpy as np
from mcp.types import EmbeddedResource, ImageContent, TextContent, TextResourceContents

from ..rendering import render_to_html, render_to_png
from ..state import state


def annotate_plot(
    plot_id: str,
    annotation_type: str,
    value: float | None = None,
    x: float | None = None,
    y: float | None = None,
    x_start: float | None = None,
    x_end: float | None = None,
    y_start: float | None = None,
    y_end: float | None = None,
    label: str | None = None,
    color: str = "red",
    line_dash: str = "dashed",
) -> list:
    """Add annotations and overlays to an existing plot.

    Useful for marking thresholds, highlighting regions, or adding reference
    lines and labels.

    Args:
        plot_id: ID of the plot to annotate
        annotation_type: Type — 'hline' (horizontal), 'vline' (vertical), 'hspan' (horizontal band), 'vspan' (vertical band), 'text' (label), 'point' (marker)
        value: Value for hline/vline
        x: X position for text/point
        y: Y position for text/point
        x_start: Start x for vspan
        x_end: End x for vspan
        y_start: Start y for hspan
        y_end: End y for hspan
        label: Text label (for text annotation, or as hover label)
        color: Color for the annotation (default 'red')
        line_dash: Line dash style — 'solid', 'dashed', 'dotted' (default 'dashed')
    """
    version = state.get_plot(plot_id)
    base_obj = version["obj"]

    if annotation_type == "hline":
        if value is None:
            return [TextContent(type="text", text="Error: 'hline' requires 'value' parameter.")]
        overlay = hv.HLine(value).opts(color=color, line_dash=line_dash, line_width=2)

    elif annotation_type == "vline":
        if value is None:
            return [TextContent(type="text", text="Error: 'vline' requires 'value' parameter.")]
        overlay = hv.VLine(value).opts(color=color, line_dash=line_dash, line_width=2)

    elif annotation_type == "hspan":
        if y_start is None or y_end is None:
            return [TextContent(type="text", text="Error: 'hspan' requires 'y_start' and 'y_end'.")]
        overlay = hv.HSpan(y_start, y_end).opts(color=color, alpha=0.15)

    elif annotation_type == "vspan":
        if x_start is None or x_end is None:
            return [TextContent(type="text", text="Error: 'vspan' requires 'x_start' and 'x_end'.")]
        overlay = hv.VSpan(x_start, x_end).opts(color=color, alpha=0.15)

    elif annotation_type == "text":
        if x is None or y is None or not label:
            return [TextContent(type="text", text="Error: 'text' requires 'x', 'y', and 'label'.")]
        overlay = hv.Text(x, y, label).opts(color=color, text_font_size="11pt")

    elif annotation_type == "point":
        if x is None or y is None:
            return [TextContent(type="text", text="Error: 'point' requires 'x' and 'y'.")]
        overlay = hv.Points([(x, y)]).opts(color=color, size=12, marker="circle")

    elif annotation_type == "arrow":
        if x is None or y is None:
            return [TextContent(type="text", text="Error: 'arrow' requires 'x', 'y' (target point). Use x_start/y_start for arrow origin.")]
        direction = "^"
        if x_start is not None and x_start > x:
            direction = ">"
        elif x_start is not None and x_start < x:
            direction = "<"
        overlay = hv.Arrow(x, y, label or "", direction=direction).opts(arrow_size=12)

    else:
        return [TextContent(type="text", text=f"Unknown annotation type '{annotation_type}'. Use: hline, vline, hspan, vspan, text, point, arrow.")]

    annotated = base_obj * overlay
    state.save_plot(annotated, {**version["spec"], "annotation": annotation_type}, version["data_ref"], plot_id=plot_id)

    png_bytes = render_to_png(annotated)
    html = render_to_html(annotated)

    desc = f"Added {annotation_type} annotation to '{plot_id}'"
    if label:
        desc += f": '{label}'"

    return [
        TextContent(type="text", text=desc),
        ImageContent(type="image", data=base64.b64encode(png_bytes).decode(), mimeType="image/png"),
        EmbeddedResource(
            type="resource",
            resource=TextResourceContents(uri=f"viz://plots/{plot_id}", mimeType="text/html", text=html),
        ),
    ]


def overlay_plots(
    plot_ids: str,
    title: str = "Overlay",
) -> list:
    """Overlay multiple plots on top of each other (shared axes).

    Unlike a dashboard which places plots side by side, overlay composites
    them onto a single set of axes — useful for comparing distributions,
    showing model vs actual, etc.

    Args:
        plot_ids: Comma-separated list of plot IDs to overlay
        title: Title for the combined plot
    """
    ids = [pid.strip() for pid in plot_ids.split(",")]
    if len(ids) < 2:
        return [TextContent(type="text", text="Error: need at least 2 plot IDs to overlay.")]

    combined = None
    for pid in ids:
        obj = state.get_plot(pid)["obj"]
        combined = obj if combined is None else combined * obj

    combined = combined.opts(title=title)
    plot_id = state.save_plot(combined, {"type": "overlay", "sources": ids}, ids[0])

    png_bytes = render_to_png(combined)
    html = render_to_html(combined)

    return [
        TextContent(type="text", text=f"Created overlay '{plot_id}' from {len(ids)} plots."),
        ImageContent(type="image", data=base64.b64encode(png_bytes).decode(), mimeType="image/png"),
        EmbeddedResource(
            type="resource",
            resource=TextResourceContents(uri=f"viz://plots/{plot_id}", mimeType="text/html", text=html),
        ),
    ]

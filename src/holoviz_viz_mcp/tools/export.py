"""Export tools: save visualizations to various formats."""

from __future__ import annotations

import base64

from mcp.types import TextContent

from ..rendering import render_to_html, render_to_png
from ..state import state


def export_plot(
    plot_id: str,
    format: str = "html",
    width: int | None = None,
    height: int | None = None,
) -> list:
    """Export a plot to a specified format and return the encoded content.

    Returns the exported content as base64 (for binary formats) or raw text
    (for HTML). The AI assistant can then save it to a file or display it.

    Args:
        plot_id: ID of the plot to export
        format: Export format — 'html', 'png', 'svg'
        width: Override width in pixels
        height: Override height in pixels
    """
    version = state.get_plot(plot_id)
    obj = version["obj"]
    w = width or 700
    h = height or 450

    if format == "html":
        html = render_to_html(obj, width=w, height=h)
        return [
            TextContent(type="text", text=f"Exported '{plot_id}' as interactive HTML ({len(html):,} chars)."),
            TextContent(type="text", text=html),
        ]

    elif format == "png":
        png_bytes = render_to_png(obj, width=w, height=h)
        b64 = base64.b64encode(png_bytes).decode()
        return [
            TextContent(type="text", text=(
                f"Exported '{plot_id}' as PNG ({len(png_bytes):,} bytes). "
                f"Base64-encoded data follows."
            )),
            TextContent(type="text", text=b64),
        ]

    elif format == "svg":
        import panel as pn
        import io
        p = pn.pane.HoloViews(obj, width=w, height=h)
        buf = io.StringIO()
        try:
            p.save(buf, fmt="svg")
            svg_data = buf.getvalue()
            return [
                TextContent(type="text", text=f"Exported '{plot_id}' as SVG ({len(svg_data):,} chars)."),
                TextContent(type="text", text=svg_data),
            ]
        except Exception as e:
            return [TextContent(type="text", text=f"SVG export failed: {e}. Try 'html' or 'png' format.")]

    else:
        return [TextContent(type="text", text=f"Unknown format '{format}'. Use: html, png, svg.")]

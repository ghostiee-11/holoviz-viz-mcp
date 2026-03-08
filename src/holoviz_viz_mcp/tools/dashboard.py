"""Dashboard composition tools: combine plots into layouts."""

from __future__ import annotations

from mcp.types import TextContent

from ..rendering import _HTML_DIR, build_viz_response, render_layout_to_html, render_to_png
from ..state import state

import holoviews as hv


def create_dashboard(
    plot_ids: str,
    title: str = "Dashboard",
    layout: str = "column",
    template_style: str | None = None,
) -> list:
    """Create a dashboard combining multiple plots.

    Returns PNG preview + interactive HTML with full Panel layout.
    Supports professional dashboard templates for polished output.

    Args:
        plot_ids: Comma-separated list of plot IDs to include
        title: Dashboard title
        layout: Layout type — 'column' (vertical), 'row' (horizontal), 'tabs', 'grid'
        template_style: Professional template — None (simple), 'material', 'bootstrap', 'fast'
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

    # Interactive HTML via Panel layout (with optional template)
    html = render_layout_to_html(
        plots, layout=layout, title=title, template_style=template_style
    )

    # Save HTML to temp file
    slug = title.lower().replace(" ", "-")
    html_path = _HTML_DIR / f"dashboard_{slug}.html"
    html_path.write_text(html)

    # Save PNG to file
    png_bytes = render_to_png(combined, width=800, height=400 * len(plots))
    png_note = ""
    if png_bytes is not None:
        png_path = _HTML_DIR / f"dashboard_{slug}.png"
        png_path.write_bytes(png_bytes)
        png_note = f"\nPNG saved to: {png_path}"

    style_note = f" [{template_style} template]" if template_style else ""
    return [
        TextContent(
            type="text",
            text=(
                f"Created dashboard '{title}' with {len(ids)} plots ({layout} layout{style_note})"
                f"{png_note}\nInteractive HTML saved to: {html_path}"
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

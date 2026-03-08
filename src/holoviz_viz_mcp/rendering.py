"""Rendering pipeline: HoloViews/hvPlot objects -> PNG bytes or standalone HTML."""

from __future__ import annotations

import base64
import io
import logging
import tempfile
from pathlib import Path
from typing import Any

from mcp.types import ImageContent, TextContent

logger = logging.getLogger(__name__)

# Directory for saved HTML files
_HTML_DIR = Path(tempfile.gettempdir()) / "holoviz-viz-mcp-output"
_HTML_DIR.mkdir(exist_ok=True)

# Cached flag: can we render PNGs? (requires browser + webdriver)
_png_available: bool | None = None


def _ensure_extensions() -> None:
    from .server import _init_extensions
    _init_extensions()


def _check_png_support() -> bool:
    """Test once whether PNG export works (needs browser + webdriver)."""
    global _png_available
    if _png_available is not None:
        return _png_available
    try:
        import holoviews as hv
        renderer = hv.Store.renderers["bokeh"]
        curve = hv.Curve([(0, 0), (1, 1)])
        renderer(curve, fmt="png")
        _png_available = True
    except Exception:
        _png_available = False
        logger.info("PNG export unavailable (no browser/webdriver); using HTML only")
    return _png_available


def render_to_png(hv_obj: Any, width: int = 700, height: int = 450) -> bytes | None:
    """Render a HoloViews/hvPlot object to PNG bytes.

    Returns None if PNG export is not available (no headless browser).
    """
    _ensure_extensions()
    if not _check_png_support():
        return None
    try:
        import holoviews as hv
        renderer = hv.Store.renderers["bokeh"]
        png_data, _ = renderer(hv_obj.opts(width=width, height=height), fmt="png")
        return png_data
    except Exception as exc:
        logger.warning("PNG rendering failed: %s", exc)
        return None


def build_viz_response(
    hv_obj: Any,
    text: str,
    uri: str,
    width: int = 700,
    height: int = 450,
) -> list:
    """Build standard MCP tool response: text + PNG + HTML file path.

    Used by all visualization tools for consistent output. PNG is returned
    inline for chat display. HTML is saved to a temp file to avoid exceeding
    MCP response size limits (embedded Bokeh JS can be 20KB+ per plot).
    """
    _ensure_extensions()

    # Save interactive HTML to temp file
    html = render_to_html(hv_obj, width=width, height=height)
    slug = uri.replace("://", "_").replace("/", "_")
    html_path = _HTML_DIR / f"{slug}.html"
    html_path.write_text(html)

    result: list = [TextContent(
        type="text",
        text=f"{text}\n\nInteractive HTML saved to: {html_path}",
    )]

    png_bytes = render_to_png(hv_obj, width=width, height=height)
    if png_bytes is not None:
        result.append(ImageContent(
            type="image",
            data=base64.b64encode(png_bytes).decode(),
            mimeType="image/png",
        ))

    return result


def render_to_html(hv_obj: Any, width: int = 700, height: int = 450) -> str:
    """Render a HoloViews/hvPlot object to standalone interactive HTML.

    Uses Panel's embed mode to produce a self-contained HTML document with
    all Bokeh JS/CSS inlined — no external server needed.
    """
    _ensure_extensions()
    import panel as pn

    p = pn.pane.HoloViews(hv_obj, width=width, height=height)
    buf = io.StringIO()
    p.save(buf, embed=True)
    return buf.getvalue()


def render_layout_to_html(
    panels: list[Any],
    layout: str = "column",
    title: str = "Dashboard",
    width: int = 800,
    template_style: str | None = None,
) -> str:
    """Render multiple HoloViews objects as a Panel layout to HTML."""
    _ensure_extensions()
    import panel as pn

    panes = [pn.pane.HoloViews(obj) for obj in panels]

    if template_style in ("material", "bootstrap", "fast"):
        try:
            tmpl_cls = {
                "material": pn.template.MaterialTemplate,
                "bootstrap": pn.template.BootstrapTemplate,
                "fast": pn.template.FastListTemplate,
            }[template_style]
            tmpl = tmpl_cls(title=title)
            for p in panes:
                tmpl.main.append(p)
            buf = io.StringIO()
            tmpl.save(buf, embed=True)
            return buf.getvalue()
        except Exception:
            pass  # Fall through to simple layout

    if layout == "row":
        container = pn.Row(*panes)
    elif layout == "tabs":
        container = pn.Tabs(*[(f"View {i+1}", p) for i, p in enumerate(panes)])
    elif layout == "grid":
        container = pn.GridSpec(sizing_mode="stretch_width")
        cols = 2
        for i, p in enumerate(panes):
            container[i // cols, i % cols] = p
    else:
        container = pn.Column(*panes)

    template = pn.Column(pn.pane.Markdown(f"# {title}"), container)
    buf = io.StringIO()
    template.save(buf, embed=True)
    return buf.getvalue()

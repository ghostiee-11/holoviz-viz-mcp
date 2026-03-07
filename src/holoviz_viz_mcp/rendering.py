"""Rendering pipeline: HoloViews/hvPlot objects → PNG bytes or standalone HTML."""

from __future__ import annotations

import io
from typing import Any

import panel as pn


def render_to_png(hv_obj: Any, width: int = 700, height: int = 450) -> bytes:
    """Render a HoloViews/hvPlot object to PNG bytes via Panel."""
    p = pn.pane.HoloViews(hv_obj, width=width, height=height)
    buf = io.BytesIO()
    p.save(buf, fmt="png")
    buf.seek(0)
    return buf.read()


def render_to_html(hv_obj: Any, width: int = 700, height: int = 450) -> str:
    """Render a HoloViews/hvPlot object to standalone interactive HTML.

    Uses Panel's embed mode to produce a self-contained HTML document with
    all Bokeh JS/CSS inlined — no external server needed. This is the key
    differentiator: real Panel rendering, not hand-rolled BokehJS.
    """
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
    """Render multiple HoloViews objects as a Panel layout to HTML.

    Args:
        panels: List of HoloViews objects to render
        layout: Layout type — 'column', 'row', 'tabs', 'grid'
        title: Dashboard title
        width: Width in pixels
        template_style: Dashboard template — None (simple), 'material', 'bootstrap', 'fast'
    """
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

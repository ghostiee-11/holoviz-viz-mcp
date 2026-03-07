"""Visualization tools: create, modify, undo, and list plots."""

from __future__ import annotations

import base64
from typing import Any

import holoviews as hv
import hvplot.pandas  # noqa: F401
from mcp.types import EmbeddedResource, ImageContent, TextContent, TextResourceContents

from ..rendering import render_to_html, render_to_png
from ..state import state


def _build_hvplot(df, spec: dict) -> Any:
    """Build an hvPlot object from a specification dict."""
    kwargs: dict[str, Any] = {"kind": spec["plot_type"], "x": spec["x"]}
    if spec.get("y"):
        kwargs["y"] = spec["y"]
    if spec.get("color_by"):
        kwargs["c" if spec["plot_type"] == "scatter" else "color"] = spec["color_by"]
    if spec.get("size_by") and spec["plot_type"] == "scatter":
        kwargs["s"] = spec["size_by"]
    if spec.get("title"):
        kwargs["title"] = spec["title"]
    else:
        kwargs["title"] = f"{spec['plot_type'].title()}: {spec['x']}"
        if spec.get("y"):
            kwargs["title"] += f" vs {spec['y']}"
    if spec.get("group_by"):
        kwargs["groupby"] = spec["group_by"]
    if spec.get("cmap"):
        kwargs["cmap"] = spec["cmap"]

    if spec.get("theme") == "dark":
        kwargs["bgcolor"] = "#1a1a2e"
        kwargs["fontcolor"] = "#e0e0e0"
    elif spec.get("theme") == "midnight":
        kwargs["bgcolor"] = "#0d1117"
        kwargs["fontcolor"] = "#c9d1d9"

    kwargs["width"] = spec.get("width", 700)
    kwargs["height"] = spec.get("height", 450)
    kwargs["responsive"] = False

    return df.hvplot(**kwargs)


def create_plot(
    dataset_name: str,
    plot_type: str,
    x: str,
    y: str | None = None,
    color_by: str | None = None,
    size_by: str | None = None,
    title: str | None = None,
    group_by: str | None = None,
    theme: str | None = None,
    width: int | None = None,
    height: int | None = None,
) -> list:
    """Create an interactive plot from a loaded dataset.

    Returns both a PNG preview (for inline chat display) and interactive HTML
    (as an embedded resource for full interactivity).

    Args:
        dataset_name: Name of the loaded dataset
        plot_type: Type — scatter, line, bar, barh, area, step, box, violin, hist, heatmap, hexbin, kde, contour, errorbars
        x: Column name for x-axis
        y: Column name for y-axis (optional for hist/kde)
        color_by: Column name to color points/bars by
        size_by: Column name to size points by (scatter only)
        title: Plot title
        group_by: Column name to create separate subplots by
        theme: Visual theme — None (default), 'dark', 'midnight'
        width: Plot width in pixels (default 700)
        height: Plot height in pixels (default 450)
    """
    df = state.get_dataset(dataset_name)

    spec = {
        "dataset": dataset_name, "plot_type": plot_type,
        "x": x, "y": y, "color_by": color_by, "size_by": size_by,
        "title": title, "group_by": group_by, "theme": theme,
        "width": width or 700, "height": height or 450,
    }
    plot = _build_hvplot(df, spec)
    plot_id = state.save_plot(plot, spec, dataset_name)

    # Dual output: PNG for inline preview + HTML for interactivity
    png_bytes = render_to_png(plot)
    html = render_to_html(plot)

    return [
        TextContent(type="text", text=f"Created plot '{plot_id}' ({plot_type}: {x}{f' vs {y}' if y else ''})"),
        ImageContent(
            type="image",
            data=base64.b64encode(png_bytes).decode(),
            mimeType="image/png",
        ),
        EmbeddedResource(
            type="resource",
            resource=TextResourceContents(
                uri=f"viz://plots/{plot_id}",
                mimeType="text/html",
                text=html,
            ),
        ),
    ]


def modify_plot(
    plot_id: str,
    title: str | None = None,
    color_by: str | None = None,
    width: int | None = None,
    height: int | None = None,
    cmap: str | None = None,
    xlabel: str | None = None,
    ylabel: str | None = None,
    legend_position: str | None = None,
) -> list:
    """Modify an existing plot's appearance. Returns updated PNG + HTML.

    Args:
        plot_id: ID of the plot to modify
        title: New title
        color_by: Column to re-color by
        width: New width in pixels
        height: New height in pixels
        cmap: Colormap name (e.g. 'viridis', 'plasma', 'Set1')
        xlabel: X-axis label
        ylabel: Y-axis label
        legend_position: Legend position (e.g. 'top_right', 'bottom_left')
    """
    version = state.get_plot(plot_id)
    spec = dict(version["spec"])
    obj = version["obj"]

    w = width or spec.get("width", 700)
    h = height or spec.get("height", 450)

    # If color_by changed, rebuild the plot
    if color_by and color_by != spec.get("color_by"):
        spec["color_by"] = color_by
        if title:
            spec["title"] = title
        if cmap:
            spec["cmap"] = cmap
        spec["width"] = w
        spec["height"] = h
        df = state.get_dataset(spec["dataset"])
        obj = _build_hvplot(df, spec)
    else:
        opts_kwargs: dict[str, Any] = {}
        if title:
            opts_kwargs["title"] = title
        if width:
            opts_kwargs["width"] = width
        if height:
            opts_kwargs["height"] = height
        if cmap:
            opts_kwargs["cmap"] = cmap
        if xlabel:
            opts_kwargs["xlabel"] = xlabel
        if ylabel:
            opts_kwargs["ylabel"] = ylabel
        if legend_position:
            opts_kwargs["legend_position"] = legend_position
        if opts_kwargs:
            obj = obj.opts(**opts_kwargs)

    state.save_plot(obj, spec, version["data_ref"], plot_id=plot_id)

    png_bytes = render_to_png(obj, width=w, height=h)
    html = render_to_html(obj, width=w, height=h)

    return [
        TextContent(type="text", text=f"Modified plot '{plot_id}'"),
        ImageContent(
            type="image",
            data=base64.b64encode(png_bytes).decode(),
            mimeType="image/png",
        ),
        EmbeddedResource(
            type="resource",
            resource=TextResourceContents(
                uri=f"viz://plots/{plot_id}",
                mimeType="text/html",
                text=html,
            ),
        ),
    ]


def undo_plot(plot_id: str) -> list:
    """Undo the last modification to a plot. Returns the previous version.

    Args:
        plot_id: ID of the plot to undo
    """
    version = state.undo_plot(plot_id)
    png_bytes = render_to_png(version["obj"])
    html = render_to_html(version["obj"])

    return [
        TextContent(type="text", text=f"Reverted plot '{plot_id}' to previous version"),
        ImageContent(
            type="image",
            data=base64.b64encode(png_bytes).decode(),
            mimeType="image/png",
        ),
        EmbeddedResource(
            type="resource",
            resource=TextResourceContents(
                uri=f"viz://plots/{plot_id}",
                mimeType="text/html",
                text=html,
            ),
        ),
    ]


def execute_code(code: str, dataset_name: str | None = None) -> list:
    """Execute arbitrary hvPlot/HoloViews/Panel code and return the result.

    This is the power-user escape hatch for visualizations that go beyond
    the structured tools — linked selections, overlays, custom widgets, etc.

    The code must assign the final visualization to a variable named `result`.
    Available in scope: pd, np, hv, hvplot, pn, and any loaded datasets.

    Args:
        code: Python code that produces a HoloViews/Panel object in `result`
        dataset_name: Optional dataset to make available as `df`
    """
    import numpy as np
    import pandas as pd
    import panel as pn

    namespace: dict[str, Any] = {
        "pd": pd, "np": np, "hv": hv, "pn": pn,
        "hvplot": __import__("hvplot"),
        "datasets": {k: v.copy() for k, v in state.datasets.items()},
    }
    if dataset_name:
        namespace["df"] = state.get_dataset(dataset_name).copy()

    exec(code, namespace)  # noqa: S102

    result = namespace.get("result")
    if result is None:
        return [TextContent(type="text", text="Code executed but no `result` variable was assigned.")]

    plot_id = state.save_plot(result, {"type": "custom_code"}, dataset_name or "code")
    png_bytes = render_to_png(result)
    html = render_to_html(result)

    return [
        TextContent(type="text", text=f"Custom visualization '{plot_id}' created via code execution"),
        ImageContent(
            type="image",
            data=base64.b64encode(png_bytes).decode(),
            mimeType="image/png",
        ),
        EmbeddedResource(
            type="resource",
            resource=TextResourceContents(
                uri=f"viz://plots/{plot_id}",
                mimeType="text/html",
                text=html,
            ),
        ),
    ]


def list_plots() -> str:
    """List all created plots with their IDs, types, and version counts."""
    plots = state.list_plots()
    if not plots:
        return "No plots created yet. Use create_plot to create one."
    lines = []
    for pid, info in plots.items():
        spec = info["spec"]
        if "plot_type" in spec:
            desc = f"{spec['plot_type']} ({spec.get('x', '?')}"
            if spec.get("y"):
                desc += f" vs {spec['y']}"
            desc += ")"
        else:
            desc = spec.get("type", "custom")
        lines.append(f"- {pid}: {desc} — {info['n_versions']} version(s)")
    return "\n".join(lines)

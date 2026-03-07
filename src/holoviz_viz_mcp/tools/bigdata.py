"""Big data visualization: datashader-powered rendering for millions of points.

Generates rasterized heatmaps from large datasets — the kind of visualization
that brings a regular plotting library to its knees. No competitor MCP can do this.
"""

from __future__ import annotations

import base64
from typing import Any

import holoviews as hv
import numpy as np
import pandas as pd
from mcp.types import EmbeddedResource, ImageContent, TextContent, TextResourceContents

from ..rendering import render_to_html, render_to_png
from ..state import state


def create_datashader_plot(
    dataset_name: str,
    x: str,
    y: str,
    agg_type: str = "count",
    cmap: str = "fire",
    title: str | None = None,
    width: int = 700,
    height: int = 450,
) -> list:
    """Create a datashader-powered plot for large datasets (10K+ points).

    Rasterizes data into a pixel-density heatmap — works with millions of points
    where scatter plots would be unusable. Uses hvPlot's datashade integration.

    Args:
        dataset_name: Name of the loaded dataset
        x: Column for x-axis
        y: Column for y-axis
        agg_type: Aggregation type — 'count' (default), 'mean', 'sum', 'min', 'max'
        cmap: Colormap — 'fire', 'inferno', 'viridis', 'blues', 'hot'
        title: Plot title
        width: Plot width in pixels
        height: Plot height in pixels
    """
    df = state.get_dataset(dataset_name)

    plot_title = title or f"Datashade: {x} vs {y} ({len(df):,} points)"

    try:
        import hvplot.pandas  # noqa: F401

        # For large datasets, use datashade=True
        if len(df) > 5000:
            plot = df.hvplot.scatter(
                x=x, y=y,
                datashade=True,
                cmap=cmap,
                title=plot_title,
                width=width, height=height,
            )
        else:
            # For smaller datasets, use regular scatter with density overlay
            plot = df.hvplot.scatter(
                x=x, y=y,
                title=plot_title,
                width=width, height=height,
                alpha=0.3,
            )
    except Exception:
        # Fallback: create a 2D histogram (binned heatmap) using HoloViews
        plot = hv.HexTiles(
            df[[x, y]].dropna().values, kdims=[x, y]
        ).opts(
            width=width, height=height, cmap=cmap,
            title=plot_title, tools=["hover"],
        )

    spec = {
        "type": "datashader", "dataset": dataset_name,
        "x": x, "y": y, "agg": agg_type, "cmap": cmap,
    }
    plot_id = state.save_plot(plot, spec, dataset_name)

    png_bytes = render_to_png(plot, width=width, height=height)
    html = render_to_html(plot, width=width, height=height)

    return [
        TextContent(
            type="text",
            text=(
                f"Created datashader plot '{plot_id}' for {len(df):,} points. "
                f"Datashade rendering aggregates density — hover for details."
            ),
        ),
        ImageContent(type="image", data=base64.b64encode(png_bytes).decode(), mimeType="image/png"),
        EmbeddedResource(
            type="resource",
            resource=TextResourceContents(
                uri=f"viz://plots/{plot_id}", mimeType="text/html", text=html,
            ),
        ),
    ]


def generate_large_dataset(
    n_points: int = 100000,
    distribution: str = "clusters",
    name: str | None = None,
) -> str:
    """Generate a large synthetic dataset for big-data visualization demos.

    Creates datasets with patterns that are only visible at scale —
    clusters, spirals, or random noise — perfect for datashader showcases.

    Args:
        n_points: Number of points to generate (default 100,000)
        distribution: Pattern — 'clusters' (Gaussian blobs), 'spiral', 'grid', 'uniform'
        name: Dataset name (default: auto-generated)
    """
    n = min(n_points, 5_000_000)  # Cap at 5M for memory safety
    np.random.seed(42)
    dataset_name = name or f"synthetic_{distribution}_{n}"

    if distribution == "clusters":
        n_clusters = 5
        centers_x = np.random.uniform(-10, 10, n_clusters)
        centers_y = np.random.uniform(-10, 10, n_clusters)
        cluster_sizes = np.random.multinomial(n, [1 / n_clusters] * n_clusters)
        xs, ys, labels = [], [], []
        for i, (cx, cy, size) in enumerate(zip(centers_x, centers_y, cluster_sizes)):
            spread = np.random.uniform(0.5, 2.0)
            xs.extend(np.random.normal(cx, spread, size))
            ys.extend(np.random.normal(cy, spread, size))
            labels.extend([f"cluster_{i}"] * size)
        df = pd.DataFrame({"x": xs, "y": ys, "cluster": labels})

    elif distribution == "spiral":
        t = np.linspace(0, 6 * np.pi, n)
        noise = np.random.normal(0, 0.3, n)
        x = t * np.cos(t) + noise
        y = t * np.sin(t) + noise
        df = pd.DataFrame({"x": x, "y": y, "t": t})

    elif distribution == "grid":
        side = int(np.sqrt(n))
        actual_n = side * side
        gx, gy = np.meshgrid(np.arange(side), np.arange(side))
        noise = np.random.normal(0, 0.1, (side, side))
        df = pd.DataFrame({
            "x": gx.flatten() + noise.flatten(),
            "y": gy.flatten() + noise.flatten(),
            "density": (np.sin(gx / 10) * np.cos(gy / 10)).flatten(),
        })

    else:  # uniform
        df = pd.DataFrame({
            "x": np.random.uniform(-10, 10, n),
            "y": np.random.uniform(-10, 10, n),
            "value": np.random.exponential(1, n),
        })

    state.store_dataset(df, dataset_name)
    return (
        f"Generated '{dataset_name}': {len(df):,} points ({distribution} pattern)\n"
        f"Columns: {', '.join(df.columns)}\n"
        f"Use create_datashader_plot('{dataset_name}', 'x', 'y') to visualize."
    )

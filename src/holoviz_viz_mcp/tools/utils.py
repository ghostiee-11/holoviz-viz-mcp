"""Utility tools: describe plots, clone, get data samples, session management.

Quality-of-life tools that make the MCP server feel like a complete product,
not a prototype — clipboard-ready data samples, accessible descriptions,
and state persistence.
"""

from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from ..state import state


def describe_plot(plot_id: str) -> str:
    """Generate a human-readable description of a plot for accessibility and context.

    Provides a natural language summary including chart type, axes, data range,
    notable patterns — useful for screen readers and AI context building.

    Args:
        plot_id: ID of the plot to describe
    """
    version = state.get_plot(plot_id)
    spec = version["spec"]
    data_ref = version["data_ref"]

    lines = [f"# Plot Description: {plot_id}"]

    # Spec-based description
    if "plot_type" in spec:
        lines.append(f"**Type:** {spec['plot_type']}")
        lines.append(f"**X-axis:** {spec.get('x', 'unknown')}")
        if spec.get("y"):
            lines.append(f"**Y-axis:** {spec['y']}")
        if spec.get("color_by"):
            lines.append(f"**Colored by:** {spec['color_by']}")
        if spec.get("title"):
            lines.append(f"**Title:** {spec['title']}")
    elif spec.get("type"):
        lines.append(f"**Type:** {spec['type']}")

    # Data context
    try:
        df = state.get_dataset(data_ref)
        lines.append(f"\n**Source dataset:** {data_ref} ({len(df):,} rows)")

        if "x" in spec and spec["x"] in df.columns:
            x_col = df[spec["x"]]
            if pd.api.types.is_numeric_dtype(x_col):
                lines.append(f"**X range:** {x_col.min():.2f} to {x_col.max():.2f}")
            elif pd.api.types.is_datetime64_any_dtype(x_col):
                lines.append(f"**X range:** {x_col.min()} to {x_col.max()}")
            else:
                lines.append(f"**X categories:** {x_col.nunique()} unique values")

        if spec.get("y") and spec["y"] in df.columns:
            y_col = df[spec["y"]]
            if pd.api.types.is_numeric_dtype(y_col):
                lines.append(f"**Y range:** {y_col.min():.2f} to {y_col.max():.2f}")
                lines.append(f"**Y mean:** {y_col.mean():.2f} (std: {y_col.std():.2f})")

        if spec.get("color_by") and spec["color_by"] in df.columns:
            groups = df[spec["color_by"]].nunique()
            lines.append(f"**Groups:** {groups} distinct values in {spec['color_by']}")
    except (KeyError, Exception):
        lines.append(f"**Source dataset:** {data_ref} (not available)")

    # Version info
    entry = state.plots.get(plot_id, {})
    n_versions = len(entry.get("versions", []))
    lines.append(f"\n**Versions:** {n_versions}")

    return "\n".join(lines)


def clone_plot(
    plot_id: str,
    new_title: str | None = None,
) -> str:
    """Create a copy of an existing plot that can be modified independently.

    Useful for creating variations of a visualization without altering the original.

    Args:
        plot_id: ID of the plot to clone
        new_title: Optional new title for the clone
    """
    version = state.get_plot(plot_id)
    obj = version["obj"]
    spec = dict(version["spec"])

    if new_title:
        spec["title"] = new_title
        try:
            obj = obj.opts(title=new_title)
        except Exception:
            pass

    new_id = state.save_plot(obj, spec, version["data_ref"])
    return f"Cloned plot '{plot_id}' -> '{new_id}'"


def get_data_sample(
    dataset_name: str,
    n_rows: int = 5,
    columns: str | None = None,
    random: bool = False,
) -> str:
    """Get a sample of rows from a dataset as formatted text.

    Useful for providing data context to the AI or for quick inspection.

    Args:
        dataset_name: Name of the loaded dataset
        n_rows: Number of rows to return (default 5, max 50)
        columns: Comma-separated list of columns to include (default: all)
        random: Whether to sample randomly (default: first N rows)
    """
    df = state.get_dataset(dataset_name)
    n = min(n_rows, 50)

    if columns:
        cols = [c.strip() for c in columns.split(",")]
        df = df[cols]

    if random:
        sample = df.sample(n=min(n, len(df)), random_state=42)
    else:
        sample = df.head(n)

    return (
        f"Sample from '{dataset_name}' ({n} of {len(df)} rows):\n\n"
        f"{sample.to_string()}\n\n"
        f"Columns: {', '.join(df.columns)}"
    )


def save_session(file_path: str | None = None) -> str:
    """Save the current session state (datasets + plot specs) to a JSON file.

    Allows resuming work later by loading the session back.
    Note: plot objects are not serialized — only specs and data are saved.

    Args:
        file_path: Path to save the session file (default: holoviz_session.json)
    """
    path = file_path or "holoviz_session.json"

    session = {
        "datasets": {},
        "plots": {},
    }

    for name, df in state.datasets.items():
        session["datasets"][name] = {
            "csv": df.to_csv(index=False),
            "shape": list(df.shape),
        }

    for pid, entry in state.plots.items():
        versions = []
        for v in entry["versions"]:
            versions.append({
                "spec": v["spec"],
                "data_ref": v["data_ref"],
                "timestamp": v["timestamp"],
            })
        session["plots"][pid] = {
            "versions": versions,
            "current": entry["current"],
        }

    with open(path, "w") as f:
        json.dump(session, f, indent=2, default=str)

    n_datasets = len(session["datasets"])
    n_plots = len(session["plots"])
    return f"Session saved to '{path}': {n_datasets} dataset(s), {n_plots} plot(s)"


def load_session(file_path: str | None = None) -> str:
    """Load a previously saved session, restoring datasets and plot specs.

    Args:
        file_path: Path to the session file (default: holoviz_session.json)
    """
    import io

    path = file_path or "holoviz_session.json"

    with open(path) as f:
        session = json.load(f)

    # Restore datasets
    for name, data in session.get("datasets", {}).items():
        df = pd.read_csv(io.StringIO(data["csv"]))
        state.store_dataset(df, name)

    n_datasets = len(session.get("datasets", {}))
    n_plots = len(session.get("plots", {}))

    return (
        f"Session loaded from '{path}': {n_datasets} dataset(s) restored.\n"
        f"Note: {n_plots} plot spec(s) found — recreate plots using create_plot with the original parameters."
    )

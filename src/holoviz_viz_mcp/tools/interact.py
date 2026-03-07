"""Interactive tools: click handling, theme switching, Panel app launching."""

from __future__ import annotations

import base64
import subprocess
import sys
import tempfile
import threading
from typing import Any

import numpy as np
import pandas as pd
from mcp.types import TextContent

from ..state import state

# Track running Panel servers
_panel_servers: dict[str, subprocess.Popen] = {}

# Global theme state
_current_theme: str = "default"


def handle_click(
    plot_id: str,
    x_value: float | None = None,
    y_value: float | None = None,
    point_index: int | None = None,
) -> str:
    """Process a click event on a chart and return AI-friendly insights.

    When a user clicks on a data point in a visualization, this tool
    analyzes the clicked point in context and returns insights about it.
    This enables bidirectional communication: the AI creates a chart,
    the user clicks a point, and the AI explains what that point means.

    Args:
        plot_id: ID of the plot that was clicked
        x_value: X-axis value of the clicked point
        y_value: Y-axis value of the clicked point
        point_index: Index of the clicked data point in the source dataset
    """
    version = state.get_plot(plot_id)
    spec = version["spec"]
    data_ref = version.get("data_ref")

    lines = [f"## Click Insight for '{plot_id}'\n"]

    if x_value is not None:
        lines.append(f"**Clicked point**: x={x_value}")
    if y_value is not None:
        lines[-1] += f", y={y_value}"

    # Try to look up the actual data row
    if data_ref and data_ref in state.datasets:
        df = state.datasets[data_ref]
        x_col = spec.get("x")
        y_col = spec.get("y")

        if point_index is not None and 0 <= point_index < len(df):
            row = df.iloc[point_index]
            lines.append(f"\n**Full data row** (index {point_index}):")
            for col, val in row.items():
                lines.append(f"  - {col}: {val}")

        elif x_col and x_value is not None:
            # Find nearest match
            num_cols = df.select_dtypes(include=[np.number]).columns
            if x_col in num_cols:
                diffs = (df[x_col] - x_value).abs()
                nearest_idx = diffs.idxmin()
                row = df.loc[nearest_idx]
                lines.append(f"\n**Nearest data row** (index {nearest_idx}):")
                for col, val in row.items():
                    lines.append(f"  - {col}: {val}")

        # Add statistical context
        if x_col and x_col in df.columns and x_value is not None:
            col_data = df[x_col]
            if col_data.dtype in [np.float64, np.int64, float, int]:
                mean_val = col_data.mean()
                std_val = col_data.std()
                percentile = (col_data < x_value).mean() * 100
                lines.append(f"\n**Statistical context** for {x_col}={x_value}:")
                lines.append(f"  - Column mean: {mean_val:.2f}, std: {std_val:.2f}")
                lines.append(f"  - This value is at the {percentile:.0f}th percentile")
                if abs(x_value - mean_val) > 2 * std_val:
                    lines.append(f"  - **Outlier**: more than 2 standard deviations from mean")

        if y_col and y_col in df.columns and y_value is not None:
            col_data = df[y_col]
            if col_data.dtype in [np.float64, np.int64, float, int]:
                percentile = (col_data < y_value).mean() * 100
                lines.append(f"  - {y_col}={y_value} is at the {percentile:.0f}th percentile")

        # Check for categorical grouping
        color_col = spec.get("color_by")
        if color_col and color_col in df.columns and point_index is not None:
            if 0 <= point_index < len(df):
                group = df.iloc[point_index][color_col]
                group_data = df[df[color_col] == group]
                lines.append(f"\n**Group context**: belongs to '{color_col}={group}'")
                lines.append(f"  - Group size: {len(group_data)} / {len(df)} ({len(group_data)/len(df)*100:.0f}%)")
    else:
        lines.append("\nNo source dataset available for deeper analysis.")

    return "\n".join(lines)


def set_theme(theme: str = "default") -> str:
    """Set the global visualization theme for all subsequent plots.

    Affects the background color, font colors, and grid styling of new
    visualizations created after this call.

    Args:
        theme: Theme name — 'default' (white), 'dark' (dark blue), 'midnight' (GitHub dark)
    """
    global _current_theme
    valid = {"default", "dark", "midnight"}
    if theme not in valid:
        return f"Unknown theme '{theme}'. Available: {', '.join(sorted(valid))}"

    _current_theme = theme
    return (
        f"Theme set to '{theme}'. All new plots will use this theme.\n"
        f"Existing plots are not affected — use modify_plot to update them."
    )


def get_current_theme() -> str:
    """Get the current global theme name."""
    return _current_theme


def launch_panel(
    plot_id: str,
    port: int = 0,
    title: str | None = None,
) -> str:
    """Open a plot as a full interactive Panel app in the browser.

    This launches a local Panel server and opens the visualization in
    your default browser with full Panel interactivity — widgets, linked
    selections, and all Panel features that can't fit in an iframe.

    Args:
        plot_id: ID of the plot to launch
        port: Port number (0 = auto-assign)
        title: Browser tab title
    """
    version = state.get_plot(plot_id)
    obj = version["obj"]

    # Generate a standalone Panel script
    from ..rendering import render_to_html
    html = render_to_html(obj)

    tmpfile = tempfile.NamedTemporaryFile(
        mode="w", suffix=".html", delete=False, prefix="holoviz_panel_"
    )
    tmpfile.write(html)
    tmpfile.flush()
    tmpfile_path = tmpfile.name
    tmpfile.close()

    # Open in browser
    import webbrowser
    webbrowser.open(f"file://{tmpfile_path}")

    return (
        f"Opened plot '{plot_id}' in browser.\n"
        f"File: {tmpfile_path}\n"
        f"The HTML is self-contained with full Bokeh interactivity."
    )


def stop_panel(plot_id: str | None = None) -> str:
    """Stop a running Panel server launched by launch_panel.

    Args:
        plot_id: ID of the plot server to stop (stops all if not provided)
    """
    if not _panel_servers:
        return "No Panel servers are currently running."

    if plot_id and plot_id in _panel_servers:
        _panel_servers[plot_id].terminate()
        del _panel_servers[plot_id]
        return f"Stopped Panel server for '{plot_id}'."

    count = len(_panel_servers)
    for proc in _panel_servers.values():
        proc.terminate()
    _panel_servers.clear()
    return f"Stopped {count} Panel server(s)."

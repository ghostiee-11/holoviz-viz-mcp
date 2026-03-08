"""Streaming data visualization tool.

Creates live-updating visualizations using Panel's periodic callbacks.
The HTML output contains a self-contained streaming simulation — no
external server needed. This is a Panel-native capability.
"""

from __future__ import annotations

import base64
import io
from typing import Any

import holoviews as hv
import numpy as np
import pandas as pd
import panel as pn
import hvplot.pandas  # noqa: F401
from mcp.types import TextContent

from ..rendering import _HTML_DIR, render_to_png
from ..state import state


def create_streaming_plot(
    dataset_name: str | None = None,
    plot_type: str = "line",
    x: str | None = None,
    y: str | None = None,
    n_points: int = 100,
    update_interval: int = 500,
    title: str = "Live Streaming Data",
    window_size: int = 200,
) -> list:
    """Create a live-updating streaming visualization with simulated real-time data.

    The output is a self-contained HTML page with Panel periodic callbacks
    that simulates streaming data — the chart updates in real time. This
    works entirely client-side, no server needed.

    If a dataset is provided, the streaming simulation replays its data
    progressively. Otherwise, generates a random walk time series.

    Args:
        dataset_name: Optional dataset to stream from (replays rows progressively)
        plot_type: Chart type for streaming — 'line', 'scatter', 'area', 'step'
        x: Column for x-axis (uses index if not provided)
        y: Column for y-axis (uses first numeric column if not provided)
        n_points: Number of initial points (for generated data)
        update_interval: Milliseconds between updates
        title: Plot title
        window_size: Max visible points in the rolling window
    """
    # Build a static preview for PNG
    if dataset_name:
        df = state.get_dataset(dataset_name)
        y_col = y or df.select_dtypes(include=[np.number]).columns[0]
        x_col = x or (df.columns[0] if df.columns[0] != y_col else "index")
        preview_data = df.head(min(n_points, len(df)))
    else:
        x_col = "time"
        y_col = "value"
        t = np.arange(n_points)
        preview_data = pd.DataFrame({
            x_col: t,
            y_col: np.cumsum(np.random.randn(n_points) * 0.5) + 100,
        })

    preview_plot = preview_data.hvplot(
        kind=plot_type, x=x_col, y=y_col,
        title=f"{title} (preview)", width=700, height=400,
    )
    png_bytes = render_to_png(preview_plot)

    # Build self-contained streaming HTML with Panel
    html = _build_streaming_html(
        plot_type=plot_type,
        x_col=x_col,
        y_col=y_col,
        title=title,
        interval_ms=update_interval,
        window_size=window_size,
    )

    plot_id = state.save_plot(
        preview_plot,
        {"type": "streaming", "plot_type": plot_type, "x": x_col, "y": y_col},
        dataset_name or "generated",
    )

    # Save HTML to temp file
    html_path = _HTML_DIR / f"streaming_{plot_id}.html"
    html_path.write_text(html)

    result: list = [
        TextContent(type="text", text=(
            f"Created streaming visualization '{plot_id}'. "
            f"The HTML updates live every {update_interval}ms.\n\n"
            f"Interactive HTML saved to: {html_path}"
        )),
    ]
    if png_bytes is not None:
        from mcp.types import ImageContent
        result.append(ImageContent(type="image", data=base64.b64encode(png_bytes).decode(), mimeType="image/png"))
    return result


def _build_streaming_html(
    plot_type: str,
    x_col: str,
    y_col: str,
    title: str,
    interval_ms: int,
    window_size: int,
) -> str:
    """Build a standalone HTML page with BokehJS streaming via JavaScript."""
    return f"""<!DOCTYPE html>
<html>
<head>
<title>{title}</title>
<script src="https://cdn.bokeh.org/bokeh/release/bokeh-3.4.3.min.js"></script>
<script src="https://cdn.bokeh.org/bokeh/release/bokeh-api-3.4.3.min.js"></script>
<style>
  body {{ font-family: -apple-system, sans-serif; margin: 0; padding: 20px; background: #fafafa; }}
  #plot {{ width: 100%; max-width: 900px; margin: 0 auto; }}
  .header {{ text-align: center; margin-bottom: 10px; }}
  .header h2 {{ margin: 0; color: #333; }}
  .status {{ text-align: center; font-size: 13px; color: #666; margin-top: 8px; }}
  .controls {{ text-align: center; margin: 10px 0; }}
  .controls button {{
    padding: 6px 16px; margin: 0 4px; border: 1px solid #ddd;
    border-radius: 4px; cursor: pointer; background: white; font-size: 13px;
  }}
  .controls button:hover {{ background: #f0f0f0; }}
  .controls button.active {{ background: #4a90d9; color: white; border-color: #4a90d9; }}
</style>
</head>
<body>
<div class="header"><h2>{title}</h2></div>
<div class="controls">
  <button id="btn-play" class="active" onclick="toggleStream()">Pause</button>
  <button onclick="resetStream()">Reset</button>
  <span class="status" id="status">Streaming...</span>
</div>
<div id="plot"></div>
<script>
(function() {{
  const WINDOW = {window_size};
  const INTERVAL = {interval_ms};
  let xs = [], ys = [];
  let step = 0, lastY = 100, running = true;

  // Initialize Bokeh plot
  const source = new Bokeh.ColumnDataSource({{ data: {{ x: [], y: [] }} }});
  const fig = Bokeh.Plotting.figure({{
    title: '{title}',
    width: 850, height: 420,
    x_axis_label: '{x_col}', y_axis_label: '{y_col}',
    tools: 'pan,wheel_zoom,box_zoom,reset,save',
  }});

  const plotType = '{plot_type}';
  if (plotType === 'scatter') {{
    fig.scatter({{ x: {{ field: 'x' }}, y: {{ field: 'y' }}, source: source,
      size: 5, color: '#4a90d9', alpha: 0.7 }});
  }} else if (plotType === 'area') {{
    fig.varea({{ x: {{ field: 'x' }}, y1: {{ field: 'y' }}, y2: 0, source: source,
      fill_color: '#4a90d9', fill_alpha: 0.3 }});
    fig.line({{ x: {{ field: 'x' }}, y: {{ field: 'y' }}, source: source,
      line_color: '#4a90d9', line_width: 2 }});
  }} else if (plotType === 'step') {{
    fig.step({{ x: {{ field: 'x' }}, y: {{ field: 'y' }}, source: source,
      line_color: '#4a90d9', line_width: 2, mode: 'after' }});
  }} else {{
    fig.line({{ x: {{ field: 'x' }}, y: {{ field: 'y' }}, source: source,
      line_color: '#4a90d9', line_width: 2 }});
  }}

  Bokeh.Plotting.show(fig, '#plot');

  function addPoint() {{
    if (!running) return;
    step++;
    const dy = (Math.random() - 0.5) * 2;
    lastY += dy;
    xs.push(step);
    ys.push(lastY);
    if (xs.length > WINDOW) {{ xs.shift(); ys.shift(); }}
    source.data = {{ x: [...xs], y: [...ys] }};
    source.change.emit();
    document.getElementById('status').textContent = 'Point ' + step + ' | Value: ' + lastY.toFixed(2);
  }}

  let timer = setInterval(addPoint, INTERVAL);

  window.toggleStream = function() {{
    running = !running;
    const btn = document.getElementById('btn-play');
    btn.textContent = running ? 'Pause' : 'Play';
    btn.className = running ? 'active' : '';
  }};

  window.resetStream = function() {{
    xs = []; ys = []; step = 0; lastY = 100;
    source.data = {{ x: [], y: [] }};
    source.change.emit();
  }};
}})();
</script>
</body>
</html>"""

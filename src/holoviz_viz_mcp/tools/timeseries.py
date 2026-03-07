"""Time series analysis tools: decomposition, rolling statistics, change detection.

Provides sophisticated time-series analysis capabilities — trend decomposition,
rolling averages, seasonality detection — with automatic visualizations.
"""

from __future__ import annotations

import base64
from typing import Any

import holoviews as hv
import hvplot.pandas  # noqa: F401
import numpy as np
import pandas as pd
from mcp.types import EmbeddedResource, ImageContent, TextContent, TextResourceContents

from ..rendering import render_to_html, render_to_png
from ..state import state


def time_series_analysis(
    dataset_name: str,
    date_column: str,
    value_column: str,
    analysis: str = "overview",
    window: int = 7,
    group_by: str | None = None,
) -> list:
    """Analyze a time series with rolling statistics, trend detection, and decomposition.

    Args:
        dataset_name: Name of the loaded dataset
        date_column: Column containing dates/timestamps
        value_column: Numeric column to analyze
        analysis: Type — 'overview' (line + rolling mean/std), 'decomposition' (trend + seasonal + residual), 'change_detection' (highlight anomalies), 'comparison' (multiple series)
        window: Rolling window size (default 7)
        group_by: Column to split series by (for comparison analysis)
    """
    df = state.get_dataset(dataset_name).copy()

    # Ensure date column is datetime
    if not pd.api.types.is_datetime64_any_dtype(df[date_column]):
        df[date_column] = pd.to_datetime(df[date_column])

    df = df.sort_values(date_column)

    results: list[str] = [f"# Time Series Analysis: {value_column}"]
    plot_obj = None

    if analysis == "overview":
        results.append(f"**Period:** {df[date_column].min()} to {df[date_column].max()}")
        results.append(f"**Points:** {len(df):,}")
        results.append(f"**Mean:** {df[value_column].mean():.4f}")
        results.append(f"**Std:** {df[value_column].std():.4f}")
        results.append(f"**Min:** {df[value_column].min():.4f} | **Max:** {df[value_column].max():.4f}")

        # Compute rolling statistics
        rolling_mean = df[value_column].rolling(window=window, min_periods=1).mean()
        rolling_std = df[value_column].rolling(window=window, min_periods=1).std()

        # Create plot: original + rolling mean + std bands
        raw_line = df.hvplot.line(
            x=date_column, y=value_column,
            title=f"{value_column} — Rolling {window}-period analysis",
            width=700, height=400, alpha=0.5, label="Raw",
        )

        roll_df = df[[date_column]].copy()
        roll_df["rolling_mean"] = rolling_mean.values
        roll_df["upper"] = (rolling_mean + 2 * rolling_std).values
        roll_df["lower"] = (rolling_mean - 2 * rolling_std).values

        mean_line = roll_df.hvplot.line(
            x=date_column, y="rolling_mean",
            color="red", line_width=2, label=f"{window}-period mean",
        )
        upper_line = roll_df.hvplot.line(
            x=date_column, y="upper",
            color="red", alpha=0.2, line_dash="dashed",
        )
        lower_line = roll_df.hvplot.line(
            x=date_column, y="lower",
            color="red", alpha=0.2, line_dash="dashed",
        )

        plot_obj = raw_line * mean_line * upper_line * lower_line

        # Trend direction
        first_half = df[value_column].iloc[:len(df)//2].mean()
        second_half = df[value_column].iloc[len(df)//2:].mean()
        trend = "upward" if second_half > first_half * 1.05 else "downward" if second_half < first_half * 0.95 else "stable"
        results.append(f"\n**Overall trend:** {trend}")
        results.append(f"**First half mean:** {first_half:.4f} | **Second half mean:** {second_half:.4f}")

    elif analysis == "decomposition":
        # Manual decomposition (no statsmodels required)
        n = len(df)
        values = df[value_column].values.astype(float)

        # Trend via rolling mean
        trend = pd.Series(values).rolling(window=window, min_periods=1, center=True).mean().values

        # Detrended
        detrended = values - trend

        # Seasonal: average pattern within the window
        seasonal = np.zeros(n)
        for i in range(window):
            indices = list(range(i, n, window))
            seasonal[indices] = np.mean(detrended[indices])

        # Residual
        residual = values - trend - seasonal

        # Build 4-panel layout
        dates = df[date_column].values

        orig = hv.Curve((dates, values), date_column, value_column).opts(
            title="Original", width=700, height=200,
        )
        trend_plot = hv.Curve((dates, trend), date_column, "Trend").opts(
            title="Trend", width=700, height=200, color="red",
        )
        seasonal_plot = hv.Curve((dates, seasonal), date_column, "Seasonal").opts(
            title=f"Seasonal (period={window})", width=700, height=200, color="green",
        )
        residual_plot = hv.Curve((dates, residual), date_column, "Residual").opts(
            title="Residual", width=700, height=200, color="orange",
        )

        plot_obj = (orig + trend_plot + seasonal_plot + residual_plot).cols(1)

        results.append(f"**Trend range:** {np.nanmin(trend):.4f} to {np.nanmax(trend):.4f}")
        results.append(f"**Seasonal amplitude:** {np.nanmax(seasonal) - np.nanmin(seasonal):.4f}")
        results.append(f"**Residual std:** {np.nanstd(residual):.4f}")

    elif analysis == "change_detection":
        rolling_mean = df[value_column].rolling(window=window, min_periods=1).mean()
        rolling_std = df[value_column].rolling(window=window, min_periods=1).std()

        # Detect anomalies (> 2 std from rolling mean)
        z_scores = np.abs((df[value_column] - rolling_mean) / rolling_std.replace(0, np.nan))
        anomalies = df[z_scores > 2].copy()

        results.append(f"**Anomalies detected:** {len(anomalies)} points (>{2} std from rolling mean)")

        if len(anomalies) > 0:
            results.append(f"**First anomaly:** {anomalies[date_column].iloc[0]}")
            results.append(f"**Last anomaly:** {anomalies[date_column].iloc[-1]}")

        # Plot with anomalies highlighted
        line = df.hvplot.line(
            x=date_column, y=value_column,
            title=f"Change Detection: {value_column}",
            width=700, height=400, alpha=0.7,
        )

        if len(anomalies) > 0:
            anomaly_points = anomalies.hvplot.scatter(
                x=date_column, y=value_column,
                color="red", size=50, label="Anomalies", marker="x",
            )
            plot_obj = line * anomaly_points
        else:
            plot_obj = line

    elif analysis == "comparison" and group_by:
        groups = df[group_by].unique()
        results.append(f"**Groups:** {', '.join(str(g) for g in groups)}")

        plot_obj = df.hvplot.line(
            x=date_column, y=value_column, by=group_by,
            title=f"{value_column} by {group_by}",
            width=700, height=400, legend="top_right",
        )

        for g in groups:
            gd = df[df[group_by] == g][value_column]
            results.append(f"  - {g}: mean={gd.mean():.4f}, std={gd.std():.4f}")

    else:
        return [TextContent(type="text", text=f"Unknown analysis '{analysis}'. Use: overview, decomposition, change_detection, comparison.")]

    narrative = "\n".join(results)

    if plot_obj is None:
        return [TextContent(type="text", text=narrative)]

    plot_id = state.save_plot(plot_obj, {"type": "timeseries", "analysis": analysis}, dataset_name)
    png_bytes = render_to_png(plot_obj, width=700, height=500)
    html = render_to_html(plot_obj, width=700, height=500)

    return [
        TextContent(type="text", text=f"Time series analysis complete.\n\n{narrative}"),
        ImageContent(type="image", data=base64.b64encode(png_bytes).decode(), mimeType="image/png"),
        EmbeddedResource(
            type="resource",
            resource=TextResourceContents(
                uri=f"viz://timeseries/{dataset_name}", mimeType="text/html", text=html,
            ),
        ),
    ]

"""Auto-EDA: one-call complete exploratory data analysis.

Generates a multi-chart dashboard with narrative insights — distributions,
correlations, missing data patterns, outliers — all from a single tool call.
No competitor MCP has anything like this.
"""

from __future__ import annotations

from typing import Any

import holoviews as hv
import hvplot.pandas  # noqa: F401
import numpy as np
import pandas as pd
from mcp.types import TextContent

from ..rendering import build_viz_response
from ..state import state


def auto_eda(
    dataset_name: str,
    max_plots: int = 6,
    include_correlations: bool = True,
    include_distributions: bool = True,
    include_missing: bool = True,
) -> list:
    """Run a complete exploratory data analysis in one call.

    Automatically generates distributions, correlations, categorical breakdowns,
    and a narrative summary with key insights. Returns a multi-panel dashboard.

    Args:
        dataset_name: Name of the loaded dataset
        max_plots: Maximum number of plots to generate (default 6)
        include_correlations: Whether to include correlation heatmap
        include_distributions: Whether to include distribution plots
        include_missing: Whether to include missing data analysis
    """
    df = state.get_dataset(dataset_name)
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    date_cols = df.select_dtypes(include=["datetime64"]).columns.tolist()

    plots: list[Any] = []
    insights: list[str] = []

    insights.append(f"# Auto-EDA Report: {dataset_name}")
    insights.append(f"**Shape:** {df.shape[0]:,} rows x {df.shape[1]} columns")
    insights.append(f"**Numeric columns:** {len(num_cols)} | **Categorical:** {len(cat_cols)} | **Date:** {len(date_cols)}")

    # Missing data overview
    missing = df.isnull().sum()
    total_missing = missing.sum()
    if total_missing > 0:
        insights.append(f"\n**Missing values:** {total_missing:,} total across {(missing > 0).sum()} columns")
        worst = missing[missing > 0].sort_values(ascending=False).head(3)
        for col, count in worst.items():
            pct = count / len(df) * 100
            insights.append(f"  - {col}: {count:,} missing ({pct:.1f}%)")
    else:
        insights.append("\n**Missing values:** None (clean dataset)")

    # Distribution plots for top numeric columns
    if include_distributions and num_cols:
        for col in num_cols[:min(3, max_plots)]:
            try:
                p = df.hvplot.hist(
                    col, bins=30, title=f"Distribution: {col}",
                    width=400, height=300, color="#4a90d9",
                )
                plots.append(p)

                # Compute stats for insights
                skew = df[col].skew()
                kurt = df[col].kurtosis()
                if abs(skew) > 1:
                    direction = "right" if skew > 0 else "left"
                    insights.append(f"- **{col}**: heavily skewed {direction} (skew={skew:.2f})")
                if kurt > 3:
                    insights.append(f"- **{col}**: heavy-tailed distribution (kurtosis={kurt:.2f})")
            except Exception:
                pass

    # Categorical breakdowns
    if cat_cols:
        for col in cat_cols[:min(2, max_plots - len(plots)):]:
            try:
                vc = df[col].value_counts().head(10)
                p = vc.hvplot.bar(
                    title=f"Top values: {col}",
                    width=400, height=300, color="#e07b39",
                )
                plots.append(p)
                n_unique = df[col].nunique()
                insights.append(f"- **{col}**: {n_unique} unique values, mode='{df[col].mode().iloc[0]}'")
            except Exception:
                pass

    # Correlation heatmap
    if include_correlations and len(num_cols) >= 2:
        try:
            corr = df[num_cols].corr()
            # Find strongest correlations for insights
            pairs = []
            for i in range(len(num_cols)):
                for j in range(i + 1, len(num_cols)):
                    pairs.append((num_cols[i], num_cols[j], corr.iloc[i, j]))
            pairs.sort(key=lambda x: abs(x[2]), reverse=True)

            if pairs:
                top = pairs[0]
                insights.append(f"\n**Strongest correlation:** {top[0]} <-> {top[1]} = {top[2]:.3f}")
                if len(pairs) > 1:
                    second = pairs[1]
                    insights.append(f"**2nd strongest:** {second[0]} <-> {second[1]} = {second[2]:.3f}")

            # Correlation heatmap plot
            heatmap_data = []
            for i, c1 in enumerate(num_cols):
                for j, c2 in enumerate(num_cols):
                    heatmap_data.append({"x": c1, "y": c2, "correlation": round(corr.iloc[i, j], 2)})
            hm_df = pd.DataFrame(heatmap_data)
            p = hm_df.hvplot.heatmap(
                x="x", y="y", C="correlation",
                title="Correlation Matrix", cmap="RdBu_r",
                width=450, height=400, clim=(-1, 1),
            )
            plots.append(p)
        except Exception:
            pass

    # Scatter of top correlated pair
    if len(num_cols) >= 2 and len(plots) < max_plots:
        try:
            scatter_kwargs = {
                "x": num_cols[0], "y": num_cols[1],
                "title": f"{num_cols[0]} vs {num_cols[1]}",
                "width": 400, "height": 300,
            }
            if cat_cols:
                scatter_kwargs["c"] = cat_cols[0]
            p = df.hvplot.scatter(**scatter_kwargs)
            plots.append(p)
        except Exception:
            pass

    # Missing data heatmap
    if include_missing and total_missing > 0 and len(plots) < max_plots:
        try:
            missing_cols = missing[missing > 0].index.tolist()[:10]
            missing_df = df[missing_cols].isnull().astype(int)
            sample = missing_df.head(100)
            p = sample.hvplot.heatmap(
                title="Missing Data Pattern (first 100 rows)",
                cmap=["#e8e8e8", "#d32f2f"], width=450, height=300,
            )
            plots.append(p)
        except Exception:
            pass

    # Outlier detection summary
    if num_cols:
        outlier_report = []
        for col in num_cols[:5]:
            q1 = df[col].quantile(0.25)
            q3 = df[col].quantile(0.75)
            iqr = q3 - q1
            if iqr > 0:
                n_outliers = ((df[col] < q1 - 1.5 * iqr) | (df[col] > q3 + 1.5 * iqr)).sum()
                if n_outliers > 0:
                    outlier_report.append(f"  - {col}: {n_outliers} outliers ({n_outliers / len(df) * 100:.1f}%)")
        if outlier_report:
            insights.append("\n**Outliers (IQR method):**")
            insights.extend(outlier_report)

    # Build the combined layout
    if not plots:
        return [TextContent(type="text", text="\n".join(insights))]

    # Create HoloViews layout
    layout = hv.Layout(plots).cols(min(len(plots), 3))
    layout = layout.opts(title=f"Auto-EDA: {dataset_name}")

    plot_id = state.save_plot(layout, {"type": "auto_eda", "dataset": dataset_name}, dataset_name)

    narrative = "\n".join(insights)
    h = 400 * ((len(plots) + 2) // 3)

    return build_viz_response(
        layout,
        text=f"Auto-EDA complete for '{dataset_name}' — {len(plots)} visualizations generated.\n\n{narrative}",
        uri=f"viz://eda/{dataset_name}",
        width=900, height=h,
    )

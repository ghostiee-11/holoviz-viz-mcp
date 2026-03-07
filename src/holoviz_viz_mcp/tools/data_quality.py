"""Data quality tools: missing value analysis, outlier detection, type validation.

Generates a comprehensive data quality report with visualizations — the kind
of analysis a data engineer does before any ML pipeline.
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


def data_quality_report(
    dataset_name: str,
    outlier_method: str = "iqr",
    outlier_threshold: float = 1.5,
) -> list:
    """Generate a comprehensive data quality report with visualizations.

    Analyzes missing values, outliers, data types, uniqueness, and consistency.
    Returns a narrative report with diagnostic plots.

    Args:
        dataset_name: Name of the loaded dataset
        outlier_method: Method for outlier detection — 'iqr' (default) or 'zscore'
        outlier_threshold: Threshold for outlier detection (IQR multiplier or z-score cutoff)
    """
    df = state.get_dataset(dataset_name)
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    report: list[str] = [f"# Data Quality Report: {dataset_name}"]
    report.append(f"**Shape:** {df.shape[0]:,} rows x {df.shape[1]} columns")
    report.append(f"**Memory usage:** {df.memory_usage(deep=True).sum() / 1024:.1f} KB")
    plots: list[Any] = []

    # 1. Missing values analysis
    report.append("\n## Missing Values")
    missing = df.isnull().sum()
    missing_pct = (missing / len(df) * 100).round(2)
    total_cells = df.shape[0] * df.shape[1]
    total_missing = missing.sum()
    completeness = (1 - total_missing / total_cells) * 100

    report.append(f"**Overall completeness:** {completeness:.1f}%")
    report.append(f"**Total missing cells:** {total_missing:,} / {total_cells:,}")

    cols_with_missing = missing[missing > 0].sort_values(ascending=False)
    if len(cols_with_missing) > 0:
        report.append(f"**Columns with missing data:** {len(cols_with_missing)}")
        for col, count in cols_with_missing.items():
            report.append(f"  - {col}: {count:,} ({missing_pct[col]:.1f}%)")

        # Missing values bar chart
        try:
            missing_df = pd.DataFrame({
                "column": cols_with_missing.index[:15],
                "missing_pct": [missing_pct[c] for c in cols_with_missing.index[:15]],
            })
            p = missing_df.hvplot.barh(
                x="column", y="missing_pct",
                title="Missing Values (%)",
                width=450, height=350, color="#d32f2f",
            )
            plots.append(p)
        except Exception:
            pass
    else:
        report.append("**No missing values** — dataset is complete")

    # 2. Data type analysis
    report.append("\n## Data Types")
    type_counts = df.dtypes.value_counts()
    for dtype, count in type_counts.items():
        report.append(f"  - {dtype}: {count} columns")

    # Potential type issues
    type_issues = []
    for col in df.columns:
        if df[col].dtype == "object":
            # Check if it could be numeric
            try:
                numeric = pd.to_numeric(df[col], errors="coerce")
                valid_pct = numeric.notna().sum() / df[col].notna().sum() * 100 if df[col].notna().sum() > 0 else 0
                if valid_pct > 80:
                    type_issues.append(f"  - **{col}**: stored as text but {valid_pct:.0f}% parseable as numeric")
            except Exception:
                pass
            # Check if it could be datetime
            try:
                dates = pd.to_datetime(df[col], errors="coerce")
                valid_pct = dates.notna().sum() / df[col].notna().sum() * 100 if df[col].notna().sum() > 0 else 0
                if valid_pct > 80:
                    type_issues.append(f"  - **{col}**: stored as text but {valid_pct:.0f}% parseable as datetime")
            except Exception:
                pass
    if type_issues:
        report.append("\n**Potential type issues:**")
        report.extend(type_issues)

    # 3. Uniqueness analysis
    report.append("\n## Uniqueness")
    for col in df.columns:
        nunique = df[col].nunique()
        pct = nunique / len(df) * 100
        if pct == 100:
            report.append(f"  - **{col}**: all unique (potential ID column)")
        elif pct < 0.5 and df[col].dtype in ("object", "category"):
            report.append(f"  - **{col}**: very low cardinality ({nunique} values)")

    # Check for duplicate rows
    n_dupes = df.duplicated().sum()
    if n_dupes > 0:
        report.append(f"\n**Duplicate rows:** {n_dupes:,} ({n_dupes / len(df) * 100:.1f}%)")
    else:
        report.append("\n**Duplicate rows:** None")

    # 4. Outlier detection
    report.append("\n## Outlier Detection")
    outlier_summary: dict[str, int] = {}

    for col in num_cols:
        data = df[col].dropna()
        if len(data) == 0:
            continue

        if outlier_method == "iqr":
            q1 = data.quantile(0.25)
            q3 = data.quantile(0.75)
            iqr = q3 - q1
            if iqr > 0:
                lower = q1 - outlier_threshold * iqr
                upper = q3 + outlier_threshold * iqr
                n_outliers = ((data < lower) | (data > upper)).sum()
                if n_outliers > 0:
                    outlier_summary[col] = n_outliers
                    report.append(
                        f"  - **{col}**: {n_outliers} outliers "
                        f"(range: [{lower:.2f}, {upper:.2f}], actual: [{data.min():.2f}, {data.max():.2f}])"
                    )
        elif outlier_method == "zscore":
            z_scores = np.abs((data - data.mean()) / data.std())
            n_outliers = (z_scores > outlier_threshold).sum()
            if n_outliers > 0:
                outlier_summary[col] = n_outliers
                report.append(f"  - **{col}**: {n_outliers} outliers (|z| > {outlier_threshold})")

    if not outlier_summary:
        report.append("  No significant outliers detected")
    else:
        # Outlier counts bar chart
        try:
            outlier_df = pd.DataFrame({
                "column": list(outlier_summary.keys()),
                "outliers": list(outlier_summary.values()),
            }).sort_values("outliers", ascending=True)
            p = outlier_df.hvplot.barh(
                x="column", y="outliers",
                title=f"Outliers by Column ({outlier_method.upper()})",
                width=450, height=350, color="#ff9800",
            )
            plots.append(p)
        except Exception:
            pass

    # 5. Distribution shapes for numerics
    if num_cols:
        report.append("\n## Distribution Summary")
        for col in num_cols[:8]:
            data = df[col].dropna()
            skew = data.skew()
            kurt = data.kurtosis()
            shape = "symmetric"
            if abs(skew) > 1:
                shape = "right-skewed" if skew > 0 else "left-skewed"
            elif abs(skew) > 0.5:
                shape = "slightly right-skewed" if skew > 0 else "slightly left-skewed"
            report.append(f"  - {col}: {shape} (skew={skew:.2f}, kurtosis={kurt:.2f})")

    # 6. Constant/near-constant columns
    low_variance = []
    for col in df.columns:
        if df[col].nunique() <= 1:
            low_variance.append(f"  - **{col}**: constant (only value: {df[col].dropna().unique()[0] if df[col].notna().any() else 'NaN'})")
        elif df[col].nunique() == 2 and df[col].dtype in ("object", "category"):
            vc = df[col].value_counts()
            minority_pct = vc.iloc[-1] / len(df) * 100
            if minority_pct < 1:
                low_variance.append(f"  - **{col}**: near-constant ({vc.iloc[0]} '{vc.index[0]}' vs {vc.iloc[-1]} '{vc.index[-1]}')")

    if low_variance:
        report.append("\n## Low-Variance Columns (consider removing)")
        report.extend(low_variance)

    # Quality score
    score = completeness
    if n_dupes > 0:
        score -= min(10, n_dupes / len(df) * 100)
    if type_issues:
        score -= len(type_issues) * 2
    if outlier_summary:
        total_outlier_pct = sum(outlier_summary.values()) / (len(df) * len(num_cols)) * 100
        score -= min(10, total_outlier_pct)
    score = max(0, min(100, score))

    report.insert(2, f"**Quality Score:** {score:.0f}/100")

    # Build output
    narrative = "\n".join(report)

    if not plots:
        return [TextContent(type="text", text=narrative)]

    layout = hv.Layout(plots).cols(min(len(plots), 2))
    plot_id = state.save_plot(layout, {"type": "data_quality", "dataset": dataset_name}, dataset_name)
    png_bytes = render_to_png(layout, width=900, height=400)
    html = render_to_html(layout, width=900, height=400)

    return [
        TextContent(type="text", text=narrative),
        ImageContent(type="image", data=base64.b64encode(png_bytes).decode(), mimeType="image/png"),
        EmbeddedResource(
            type="resource",
            resource=TextResourceContents(
                uri=f"viz://quality/{dataset_name}",
                mimeType="text/html",
                text=html,
            ),
        ),
    ]


def compare_datasets(
    dataset_a: str,
    dataset_b: str,
) -> str:
    """Compare two datasets side-by-side: shapes, columns, distributions, and statistical differences.

    Useful for comparing train/test splits, before/after transformations,
    or different time periods.

    Args:
        dataset_a: Name of the first dataset
        dataset_b: Name of the second dataset
    """
    df_a = state.get_dataset(dataset_a)
    df_b = state.get_dataset(dataset_b)

    report = [f"# Dataset Comparison: {dataset_a} vs {dataset_b}\n"]

    # Shape comparison
    report.append("## Shape")
    report.append(f"  {dataset_a}: {df_a.shape[0]:,} rows x {df_a.shape[1]} cols")
    report.append(f"  {dataset_b}: {df_b.shape[0]:,} rows x {df_b.shape[1]} cols")

    # Column overlap
    cols_a = set(df_a.columns)
    cols_b = set(df_b.columns)
    common = cols_a & cols_b
    only_a = cols_a - cols_b
    only_b = cols_b - cols_a

    report.append(f"\n## Column Overlap")
    report.append(f"  Common columns: {len(common)}")
    if only_a:
        report.append(f"  Only in {dataset_a}: {', '.join(sorted(only_a))}")
    if only_b:
        report.append(f"  Only in {dataset_b}: {', '.join(sorted(only_b))}")

    # Statistical comparison for common numeric columns
    num_common = [c for c in common if pd.api.types.is_numeric_dtype(df_a[c]) and pd.api.types.is_numeric_dtype(df_b[c])]
    if num_common:
        report.append(f"\n## Numeric Column Comparison")
        for col in num_common[:10]:
            a_data = df_a[col].dropna()
            b_data = df_b[col].dropna()
            mean_diff = abs(a_data.mean() - b_data.mean())
            std_diff = abs(a_data.std() - b_data.std())
            report.append(
                f"  **{col}**: mean {a_data.mean():.3f} vs {b_data.mean():.3f} (diff={mean_diff:.3f}), "
                f"std {a_data.std():.3f} vs {b_data.std():.3f}"
            )

    # Categorical comparison
    cat_common = [c for c in common if df_a[c].dtype == "object" and df_b[c].dtype == "object"]
    if cat_common:
        report.append(f"\n## Categorical Column Comparison")
        for col in cat_common[:5]:
            vals_a = set(df_a[col].dropna().unique())
            vals_b = set(df_b[col].dropna().unique())
            new_vals = vals_b - vals_a
            missing_vals = vals_a - vals_b
            report.append(f"  **{col}**: {len(vals_a)} vs {len(vals_b)} unique values")
            if new_vals:
                report.append(f"    New in {dataset_b}: {', '.join(str(v) for v in list(new_vals)[:5])}")
            if missing_vals:
                report.append(f"    Missing from {dataset_b}: {', '.join(str(v) for v in list(missing_vals)[:5])}")

    return "\n".join(report)

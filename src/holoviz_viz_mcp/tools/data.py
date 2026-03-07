"""Data management tools: load, analyze, list, and sample datasets."""

from __future__ import annotations

import io

import numpy as np
import pandas as pd

from ..state import state


def load_data(
    csv_data: str | None = None,
    name: str | None = None,
    url: str | None = None,
    format: str = "csv",
    json_data: str | None = None,
) -> str:
    """Load data into the server from CSV text, JSON text, or a URL.

    Supports CSV, JSON, Parquet, and Excel formats. For URL loading, the
    format is auto-detected from the file extension.

    Args:
        csv_data: CSV-formatted string data
        name: Optional name for the dataset (auto-generated if not provided)
        url: URL to fetch data from (supports csv, json, parquet, xlsx)
        format: Data format when using csv_data/json_data — 'csv' or 'json'
        json_data: JSON-formatted string data (records or columnar orientation)
    """
    if url:
        ext = url.rsplit(".", 1)[-1].lower() if "." in url.split("/")[-1] else "csv"
        if ext in ("parquet", "pq"):
            df = pd.read_parquet(url)
        elif ext in ("xlsx", "xls"):
            df = pd.read_excel(url)
        elif ext == "json":
            df = pd.read_json(url)
        else:
            df = pd.read_csv(url)
        if not name:
            name = url.split("/")[-1].rsplit(".", 1)[0][:30]
    elif json_data:
        df = pd.read_json(io.StringIO(json_data))
    elif csv_data:
        df = pd.read_csv(io.StringIO(csv_data))
    else:
        return "Error: provide csv_data, json_data, or url."

    data_id = state.store_dataset(df, name)

    lines = [f"Loaded dataset '{data_id}': {df.shape[0]} rows x {df.shape[1]} columns\n"]
    lines.append("Columns:")
    for col in df.columns:
        dtype = df[col].dtype
        nunique = df[col].nunique()
        nulls = df[col].isna().sum()
        lines.append(f"  - {col} ({dtype}, {nunique} unique, {nulls} nulls)")
    lines.append(f"\nFirst 3 rows:\n{df.head(3).to_string()}")
    return "\n".join(lines)


def list_datasets() -> str:
    """List all loaded datasets with their shapes and column names."""
    datasets = state.list_datasets()
    if not datasets:
        return "No datasets loaded. Use load_data to load CSV data."
    lines = []
    for name, (rows, cols, columns) in datasets.items():
        col_str = ", ".join(columns[:10])
        if len(columns) > 10:
            col_str += f"... (+{len(columns) - 10} more)"
        lines.append(f"- {name}: {rows} rows x {cols} cols [{col_str}]")
    return "\n".join(lines)


def analyze_data(dataset_name: str) -> str:
    """Generate a comprehensive data profile for a loaded dataset.

    Args:
        dataset_name: Name of a previously loaded dataset
    """
    df = state.get_dataset(dataset_name)
    lines = [
        f"# Data Profile: {dataset_name}",
        f"Shape: {df.shape[0]} rows x {df.shape[1]} columns\n",
    ]

    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if num_cols:
        lines.append("## Numeric Columns")
        lines.append(df[num_cols].describe().round(2).to_string())
        lines.append("")

    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    if cat_cols:
        lines.append("## Categorical Columns")
        for col in cat_cols:
            top = df[col].value_counts().head(5)
            lines.append(f"  {col}: {df[col].nunique()} unique — top: {dict(top)}")
        lines.append("")

    if len(num_cols) >= 2:
        lines.append("## Top Correlations")
        corr = df[num_cols].corr()
        pairs = []
        for i in range(len(num_cols)):
            for j in range(i + 1, len(num_cols)):
                pairs.append((num_cols[i], num_cols[j], abs(corr.iloc[i, j])))
        pairs.sort(key=lambda x: x[2], reverse=True)
        for a, b, c in pairs[:5]:
            lines.append(f"  {a} <-> {b}: {c:.3f}")

    return "\n".join(lines)


def suggest_visualizations(dataset_name: str) -> str:
    """Suggest appropriate visualization types based on data characteristics.

    Args:
        dataset_name: Name of a previously loaded dataset
    """
    df = state.get_dataset(dataset_name)
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    date_cols = df.select_dtypes(include=["datetime64"]).columns.tolist()

    suggestions = ["# Suggested Visualizations\n"]

    if len(num_cols) >= 2:
        s = f"1. **Scatter**: `create_plot('{dataset_name}', 'scatter', x='{num_cols[0]}', y='{num_cols[1]}')`"
        if cat_cols:
            s += f" — try color_by='{cat_cols[0]}'"
        suggestions.append(s)

    if num_cols and cat_cols:
        suggestions.append(
            f"2. **Bar chart**: `create_plot('{dataset_name}', 'bar', x='{cat_cols[0]}', y='{num_cols[0]}')`"
        )
        suggestions.append(
            f"3. **Box plot**: `create_plot('{dataset_name}', 'box', x='{cat_cols[0]}', y='{num_cols[0]}')`"
        )

    if num_cols:
        suggestions.append(
            f"4. **Histogram**: `create_plot('{dataset_name}', 'hist', x='{num_cols[0]}')`"
        )

    if len(num_cols) >= 3:
        suggestions.append(
            f"5. **Heatmap**: `create_plot('{dataset_name}', 'heatmap', x='{num_cols[0]}', y='{num_cols[1]}')`"
        )

    if date_cols and num_cols:
        suggestions.append(
            f"6. **Time series**: `create_plot('{dataset_name}', 'line', x='{date_cols[0]}', y='{num_cols[0]}')`"
        )

    return "\n".join(suggestions)


def load_sample_data(dataset: str = "iris") -> str:
    """Load a built-in sample dataset for quick demos.

    Args:
        dataset: Name of sample dataset — 'iris', 'penguins', 'tips', 'stocks'
    """
    if dataset == "iris":
        from sklearn.datasets import load_iris

        data = load_iris(as_frame=True)
        df = data.frame
        df.columns = [
            "sepal_length", "sepal_width", "petal_length", "petal_width", "species",
        ]
        df["species"] = df["species"].map(
            {0: "setosa", 1: "versicolor", 2: "virginica"}
        )
    elif dataset == "penguins":
        try:
            url = "https://raw.githubusercontent.com/mwaskom/seaborn-data/master/penguins.csv"
            df = pd.read_csv(url).dropna()
        except Exception:
            np.random.seed(42)
            n = 150
            df = pd.DataFrame({
                "species": np.random.choice(["Adelie", "Chinstrap", "Gentoo"], n),
                "bill_length_mm": np.random.normal(44, 5, n).round(1),
                "bill_depth_mm": np.random.normal(17, 2, n).round(1),
                "flipper_length_mm": np.random.normal(200, 14, n).round(0),
                "body_mass_g": np.random.normal(4200, 800, n).round(0),
            })
    elif dataset == "tips":
        np.random.seed(42)
        n = 244
        df = pd.DataFrame({
            "total_bill": np.random.uniform(3, 50, n).round(2),
            "tip": np.random.uniform(1, 10, n).round(2),
            "sex": np.random.choice(["Male", "Female"], n),
            "smoker": np.random.choice(["Yes", "No"], n),
            "day": np.random.choice(["Thu", "Fri", "Sat", "Sun"], n),
            "time": np.random.choice(["Lunch", "Dinner"], n),
            "size": np.random.choice([1, 2, 3, 4, 5, 6], n),
        })
    elif dataset == "stocks":
        np.random.seed(42)
        dates = pd.date_range("2023-01-01", periods=252, freq="B")
        df = pd.DataFrame({
            "date": np.tile(dates, 3),
            "price": np.concatenate([
                100 + np.cumsum(np.random.randn(252) * 2),
                80 + np.cumsum(np.random.randn(252) * 1.5),
                120 + np.cumsum(np.random.randn(252) * 3),
            ]).round(2),
            "company": np.repeat(["AAPL", "GOOG", "MSFT"], 252),
        })
    else:
        return f"Unknown dataset '{dataset}'. Available: iris, penguins, tips, stocks"

    state.store_dataset(df, dataset)
    return (
        f"Loaded sample dataset '{dataset}': {df.shape[0]} rows x {df.shape[1]} columns\n"
        f"Columns: {', '.join(df.columns)}\n\n"
        f"First 3 rows:\n{df.head(3).to_string()}"
    )

"""Data transformation tools: filter, group, pivot, derive columns."""

from __future__ import annotations

import pandas as pd

from ..state import state


def transform_data(
    dataset_name: str,
    operation: str,
    output_name: str | None = None,
    column: str | None = None,
    value: str | None = None,
    group_by: str | None = None,
    agg: str = "mean",
    expression: str | None = None,
    new_column: str | None = None,
    sort_by: str | None = None,
    ascending: bool = True,
    limit: int | None = None,
) -> str:
    """Transform a dataset using common operations. Saves the result as a new dataset.

    Args:
        dataset_name: Source dataset name
        operation: One of 'filter', 'groupby', 'sort', 'derive', 'sample', 'drop_na', 'pivot'
        output_name: Name for the resulting dataset (auto-generated if not provided)
        column: Column to operate on (for filter/sort)
        value: Filter value or expression (e.g. '> 5', '== "setosa"', 'in ["A","B"]')
        group_by: Column(s) to group by (comma-separated for multiple)
        agg: Aggregation function for groupby — mean, sum, count, min, max, median, std
        expression: Python expression for derive (e.g. 'col_a * col_b')
        new_column: Name for derived column
        sort_by: Column to sort by
        ascending: Sort ascending (default True)
        limit: Limit number of rows in output
    """
    df = state.get_dataset(dataset_name).copy()
    out_name = output_name or f"{dataset_name}_{operation}"

    if operation == "filter":
        if not column or not value:
            return "Error: 'filter' requires 'column' and 'value' parameters."
        query = f"`{column}` {value}" if not value.startswith("==") else f"`{column}` {value}"
        df = df.query(query, engine="python")

    elif operation == "groupby":
        if not group_by:
            return "Error: 'groupby' requires 'group_by' parameter."
        cols = [c.strip() for c in group_by.split(",")]
        agg_func = agg if agg in ("mean", "sum", "count", "min", "max", "median", "std") else "mean"
        df = df.groupby(cols, as_index=False).agg(agg_func, numeric_only=True)

    elif operation == "sort":
        col = sort_by or column
        if not col:
            return "Error: 'sort' requires 'sort_by' or 'column' parameter."
        df = df.sort_values(col, ascending=ascending)

    elif operation == "derive":
        if not expression or not new_column:
            return "Error: 'derive' requires 'expression' and 'new_column' parameters."
        df[new_column] = df.eval(expression)

    elif operation == "sample":
        n = limit or min(100, len(df))
        df = df.sample(n=n, random_state=42)

    elif operation == "drop_na":
        before = len(df)
        if column:
            df = df.dropna(subset=[column])
        else:
            df = df.dropna()
        dropped = before - len(df)
        state.store_dataset(df, out_name)
        return (
            f"Created '{out_name}': dropped {dropped} rows with NaN values. "
            f"{len(df)} rows remaining.\n"
            f"Columns: {', '.join(df.columns)}"
        )

    elif operation == "pivot":
        if not column or not group_by:
            return "Error: 'pivot' requires 'column' (values) and 'group_by' (index) parameters."
        pivot_cols = [c.strip() for c in group_by.split(",")]
        if len(pivot_cols) >= 2:
            df = df.pivot_table(values=column, index=pivot_cols[0], columns=pivot_cols[1], aggfunc=agg)
            df = df.reset_index()
        else:
            return "Error: 'pivot' needs at least 2 columns in group_by (index,columns)."

    else:
        return f"Unknown operation '{operation}'. Use: filter, groupby, sort, derive, sample, drop_na, pivot."

    if limit and operation != "sample":
        df = df.head(limit)

    state.store_dataset(df, out_name)
    return (
        f"Created '{out_name}' from '{dataset_name}' ({operation}): "
        f"{df.shape[0]} rows x {df.shape[1]} columns\n"
        f"Columns: {', '.join(df.columns)}\n\n"
        f"First 3 rows:\n{df.head(3).to_string()}"
    )


def merge_datasets(
    left_name: str,
    right_name: str,
    on: str,
    how: str = "inner",
    output_name: str | None = None,
) -> str:
    """Merge two datasets together on a common column.

    Args:
        left_name: Name of the left dataset
        right_name: Name of the right dataset
        on: Column name(s) to join on (comma-separated for multiple)
        how: Join type — 'inner', 'left', 'right', 'outer'
        output_name: Name for the merged dataset
    """
    left = state.get_dataset(left_name)
    right = state.get_dataset(right_name)
    on_cols = [c.strip() for c in on.split(",")]
    out_name = output_name or f"{left_name}_{right_name}_merged"

    merged = pd.merge(left, right, on=on_cols, how=how)
    state.store_dataset(merged, out_name)

    return (
        f"Merged '{left_name}' + '{right_name}' on {on_cols} ({how} join) -> '{out_name}'\n"
        f"Result: {merged.shape[0]} rows x {merged.shape[1]} columns\n"
        f"Columns: {', '.join(merged.columns)}"
    )

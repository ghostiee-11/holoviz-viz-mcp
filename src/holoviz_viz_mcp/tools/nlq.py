"""Natural language query tool: plain English -> data transformations + visualizations.

This is the crown jewel — the AI assistant becomes conversational:
"show me sales by region where revenue > 1M" translates to filter + groupby + bar chart.
No competitor has anything close to this level of intelligence.
"""

from __future__ import annotations

import re

import numpy as np
import pandas as pd

from ..state import state


def natural_language_query(
    dataset_name: str,
    query: str,
) -> str:
    """Interpret a natural language query about a dataset and return a structured plan.

    Analyzes the query against the dataset's columns and types to produce
    a step-by-step execution plan using the MCP tools. The AI assistant
    can then execute these steps.

    Args:
        dataset_name: Name of the loaded dataset
        query: Natural language question or command (e.g., "show average salary by department", "what are the top 10 products by revenue", "is there a correlation between age and income")
    """
    df = state.get_dataset(dataset_name)
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    date_cols = df.select_dtypes(include=["datetime64"]).columns.tolist()
    all_cols = list(df.columns)

    query_lower = query.lower().strip()

    # Build structured plan
    steps: list[str] = [f"# Query Plan for: \"{query}\"", f"**Dataset:** {dataset_name} ({df.shape[0]} rows)\n"]

    # Detect mentioned columns
    mentioned_cols = [col for col in all_cols if col.lower() in query_lower or col.lower().replace("_", " ") in query_lower]

    # Detect intent
    intent = _detect_intent(query_lower)
    steps.append(f"**Detected intent:** {intent}")

    if mentioned_cols:
        steps.append(f"**Referenced columns:** {', '.join(mentioned_cols)}")

    # Detect filter conditions
    filters = _detect_filters(query_lower, all_cols, df)
    if filters:
        steps.append(f"\n## Step 1: Filter data")
        for f in filters:
            steps.append(f"```\ntransform_data('{dataset_name}', 'filter', column='{f['col']}', value='{f['expr']}', output_name='{dataset_name}_filtered')\n```")

    # Generate steps based on intent
    source = f"{dataset_name}_filtered" if filters else dataset_name

    if intent == "distribution":
        col = _best_col(mentioned_cols, num_cols) or (num_cols[0] if num_cols else None)
        if col:
            steps.append(f"\n## {'Step 2' if filters else 'Step 1'}: Create distribution")
            steps.append(f"```\ncreate_plot('{source}', 'hist', x='{col}', title='Distribution of {col}')\n```")

    elif intent == "comparison":
        x_col = _best_col(mentioned_cols, cat_cols) or (cat_cols[0] if cat_cols else None)
        y_col = _best_col(mentioned_cols, num_cols) or (num_cols[0] if num_cols else None)
        if x_col and y_col:
            steps.append(f"\n## {'Step 2' if filters else 'Step 1'}: Group and compare")
            steps.append(f"```\ntransform_data('{source}', 'groupby', group_by='{x_col}', agg='mean', output_name='{source}_grouped')\n```")
            steps.append(f"\n## Next: Create comparison chart")
            steps.append(f"```\ncreate_plot('{source}_grouped', 'bar', x='{x_col}', y='{y_col}', title='Average {y_col} by {x_col}')\n```")

    elif intent == "trend":
        time_col = _best_col(mentioned_cols, date_cols) or (date_cols[0] if date_cols else None)
        val_col = _best_col(mentioned_cols, num_cols) or (num_cols[0] if num_cols else None)
        if time_col and val_col:
            steps.append(f"\n## {'Step 2' if filters else 'Step 1'}: Create trend")
            steps.append(f"```\ncreate_plot('{source}', 'line', x='{time_col}', y='{val_col}', title='{val_col} over time')\n```")
        elif val_col:
            steps.append(f"\n## {'Step 2' if filters else 'Step 1'}: Create line plot")
            x_col = all_cols[0] if all_cols[0] != val_col else (all_cols[1] if len(all_cols) > 1 else val_col)
            steps.append(f"```\ncreate_plot('{source}', 'line', x='{x_col}', y='{val_col}', title='{val_col} trend')\n```")

    elif intent == "correlation":
        cols = [c for c in mentioned_cols if c in num_cols]
        if len(cols) >= 2:
            x, y = cols[0], cols[1]
        elif len(num_cols) >= 2:
            x, y = num_cols[0], num_cols[1]
        else:
            x, y = None, None
        if x and y:
            steps.append(f"\n## {'Step 2' if filters else 'Step 1'}: Run correlation test")
            steps.append(f"```\nstatistical_test('{source}', 'correlation', column_x='{x}', column_y='{y}')\n```")

    elif intent == "top_n":
        n = _extract_number(query_lower) or 10
        sort_col = _best_col(mentioned_cols, num_cols) or (num_cols[0] if num_cols else None)
        if sort_col:
            steps.append(f"\n## {'Step 2' if filters else 'Step 1'}: Get top {n}")
            steps.append(f"```\ntransform_data('{source}', 'sort', sort_by='{sort_col}', ascending=False, limit={n}, output_name='{source}_top{n}')\n```")
            x_col = _best_col(mentioned_cols, cat_cols) or (cat_cols[0] if cat_cols else sort_col)
            steps.append(f"\n## Next: Visualize")
            steps.append(f"```\ncreate_plot('{source}_top{n}', 'barh', x='{x_col}', y='{sort_col}', title='Top {n} by {sort_col}')\n```")

    elif intent == "summary":
        steps.append(f"\n## {'Step 2' if filters else 'Step 1'}: Full analysis")
        steps.append(f"```\nauto_eda('{source}')\n```")

    elif intent == "quality":
        steps.append(f"\n## Step 1: Data quality report")
        steps.append(f"```\ndata_quality_report('{source}')\n```")

    elif intent == "scatter":
        x = _best_col(mentioned_cols, num_cols) or (num_cols[0] if num_cols else None)
        y = _best_col([c for c in mentioned_cols if c != x], num_cols) or (num_cols[1] if len(num_cols) > 1 else None)
        if x and y:
            color = cat_cols[0] if cat_cols else None
            color_arg = f", color_by='{color}'" if color else ""
            steps.append(f"\n## {'Step 2' if filters else 'Step 1'}: Create scatter")
            steps.append(f"```\ncreate_plot('{source}', 'scatter', x='{x}', y='{y}'{color_arg})\n```")

    else:
        # Generic: suggest auto_eda
        steps.append(f"\n## Suggested approach")
        steps.append(f"For this query, try:")
        steps.append(f"```\nauto_eda('{source}')\n```")
        steps.append(f"Or for specific analysis:")
        steps.append(f"```\nanalyze_data('{source}')\nsuggest_visualizations('{source}')\n```")

    return "\n".join(steps)


def _detect_intent(query: str) -> str:
    """Detect the analysis intent from a natural language query."""
    if any(w in query for w in ("distribut", "histogram", "spread", "range")):
        return "distribution"
    if any(w in query for w in ("compar", "by ", "versus", "vs ", "across", "between", "per ", "each ")):
        return "comparison"
    if any(w in query for w in ("trend", "over time", "time series", "timeline", "growth")):
        return "trend"
    if any(w in query for w in ("correlat", "relationship", "related", "association", "depends")):
        return "correlation"
    if any(w in query for w in ("top ", "bottom ", "highest", "lowest", "best", "worst", "rank")):
        return "top_n"
    if any(w in query for w in ("summar", "overview", "eda", "explor", "understand")):
        return "summary"
    if any(w in query for w in ("quality", "missing", "clean", "outlier", "valid")):
        return "quality"
    if any(w in query for w in ("scatter", "plot ", "chart ")):
        return "scatter"
    return "unknown"


def _detect_filters(query: str, all_cols: list[str], df: pd.DataFrame) -> list[dict]:
    """Detect filter conditions from the query."""
    filters = []
    # Pattern: "where/when/if <column> <operator> <value>"
    for col in all_cols:
        col_lower = col.lower()
        patterns = [
            rf"(?:where|when|if|with)\s+{re.escape(col_lower)}\s*(>|<|>=|<=|==|!=|=)\s*(['\"]?\w+['\"]?)",
            rf"{re.escape(col_lower)}\s*(>|<|>=|<=)\s*(\d+\.?\d*)",
        ]
        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                op = match.group(1)
                val = match.group(2).strip("'\"")
                if op == "=":
                    op = "=="
                expr = f"{op} {val}" if val.replace(".", "").isdigit() else f'{op} "{val}"'
                filters.append({"col": col, "expr": expr})
                break
    return filters


def _best_col(mentioned: list[str], candidates: list[str]) -> str | None:
    """Pick the best column from mentioned ones that exists in candidates."""
    for col in mentioned:
        if col in candidates:
            return col
    return None


def _extract_number(query: str) -> int | None:
    """Extract a number from the query (e.g., 'top 10' -> 10)."""
    match = re.search(r"\b(\d+)\b", query)
    return int(match.group(1)) if match else None

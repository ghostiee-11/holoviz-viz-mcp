"""Showcase: Stock Analysis Dashboard

Demonstrates: data loading, transforms, crossfilter, annotations, dashboard.
Run: python demos/showcase_stock_analysis.py
"""

import sys
sys.path.insert(0, "src")

from holoviz_viz_mcp.tools.data import load_sample_data
from holoviz_viz_mcp.tools.viz import create_plot
from holoviz_viz_mcp.tools.transform import transform_data
from holoviz_viz_mcp.tools.annotations import annotate_plot
from holoviz_viz_mcp.tools.dashboard import create_dashboard


def main():
    print("Stock Analysis Showcase")
    print("=" * 50)

    # Load stock data
    print("\n1. Loading stock data...")
    load_sample_data("stocks")

    # Create price line chart
    print("2. Creating price chart...")
    line = create_plot(
        "stocks", "line", x="date", y="price",
        color_by="company", title="Stock Prices Over Time"
    )
    line_id = line[0].text.split("'")[1]
    print(f"   {line[0].text}")

    # Group by company and get stats
    print("3. Aggregating by company...")
    transform_data("stocks", "groupby", group_by="company", agg="mean", output_name="stock_avg")

    # Create bar chart of averages
    print("4. Creating average price bar chart...")
    bar = create_plot(
        "stock_avg", "bar", x="company", y="price",
        title="Average Price by Company"
    )
    bar_id = bar[0].text.split("'")[1]

    # Annotate the line chart with a threshold
    print("5. Adding price threshold annotation...")
    annotate_plot(line_id, "hline", value=100.0, color="red", label="$100 Target")

    # Create dashboard
    print("6. Building dashboard...")
    dash = create_dashboard(f"{line_id},{bar_id}", title="Stock Analysis", layout="column")

    # Save output
    with open("demos/demo_stock_analysis.html", "w") as f:
        f.write(dash[2].resource.text)

    print("\n   Saved: demos/demo_stock_analysis.html")
    print("   Open in browser for full interactivity!")


if __name__ == "__main__":
    main()

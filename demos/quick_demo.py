"""Quick demo: test the MCP server tools locally without an MCP client.

Run: python demos/quick_demo.py
"""

from __future__ import annotations

import sys
sys.path.insert(0, "src")

from holoviz_viz_mcp.tools.data import load_sample_data, analyze_data, suggest_visualizations
from holoviz_viz_mcp.tools.viz import create_plot, execute_code, list_plots
from holoviz_viz_mcp.tools.dashboard import create_dashboard
from holoviz_viz_mcp.tools.transform import transform_data
from holoviz_viz_mcp.tools.crossfilter import create_crossfilter
from holoviz_viz_mcp.tools.streaming import create_streaming_plot
from holoviz_viz_mcp.tools.annotations import annotate_plot


def main():
    print("=" * 60)
    print("HoloViz MCP Server v0.3.0 — Demo")
    print("=" * 60)

    # 1. Load sample data
    print("\n1. Loading iris dataset...")
    result = load_sample_data("iris")
    print(result[:200])

    # 2. Analyze
    print("\n2. Analyzing data...")
    analysis = analyze_data("iris")
    print(analysis[:300])

    # 3. Get suggestions
    print("\n3. Getting visualization suggestions...")
    suggestions = suggest_visualizations("iris")
    print(suggestions)

    # 4. Create a scatter plot
    print("\n4. Creating scatter plot...")
    result = create_plot(
        "iris", "scatter", x="sepal_length", y="sepal_width",
        color_by="species", title="Iris: Sepal Dimensions"
    )
    text_msg = result[0].text
    png_size = len(result[1].data)
    html_size = len(result[2].resource.text)
    plot_id = text_msg.split("'")[1]
    print(f"   {text_msg}")
    print(f"   PNG: {png_size:,} bytes | HTML: {html_size:,} chars")

    # 5. Transform data
    print("\n5. Filtering to large petals...")
    filtered = transform_data("iris", "filter", column="petal_length", value="> 4.0")
    print(f"   {filtered[:120]}")

    # 6. Add annotation
    print("\n6. Adding threshold line to scatter plot...")
    ann_result = annotate_plot(plot_id, "hline", value=3.0, color="red", label="Threshold")
    print(f"   {ann_result[0].text}")

    # 7. Crossfilter
    print("\n7. Creating crossfilter dashboard (linked selections)...")
    cf_result = create_crossfilter(
        "iris",
        views="scatter,sepal_length,sepal_width;hist,petal_length;box,species,petal_width",
        color_by="species",
        title="Iris Crossfilter"
    )
    print(f"   {cf_result[0].text}")
    print(f"   PNG: {len(cf_result[1].data):,} bytes | HTML: {len(cf_result[2].resource.text):,} chars")

    # 8. Streaming
    print("\n8. Creating streaming visualization...")
    stream_result = create_streaming_plot(
        plot_type="line", title="Live Random Walk", update_interval=300
    )
    print(f"   {stream_result[0].text}")

    # 9. execute_code: linked selections
    print("\n9. Custom code execution (linked scatter + hist)...")
    linked_code = """
import holoviews as hv
from holoviews.selection import link_selections

scatter = df.hvplot.scatter('sepal_length', 'sepal_width', color='species', width=350, height=300)
hist = df.hvplot.hist('petal_length', color='species', width=350, height=300)
result = link_selections(scatter + hist)
"""
    linked_result = execute_code(linked_code, dataset_name="iris")
    print(f"   {linked_result[0].text}")

    # 10. List all plots
    print("\n10. Listing all plots...")
    print(list_plots())

    # 11. Save HTML outputs
    with open("demos/demo_scatter.html", "w") as f:
        f.write(result[2].resource.text)
    with open("demos/demo_crossfilter.html", "w") as f:
        f.write(cf_result[2].resource.text)
    with open("demos/demo_streaming.html", "w") as f:
        f.write(stream_result[2].resource.text)

    print("\n11. Interactive outputs saved:")
    print("   - demos/demo_scatter.html     (scatter + annotation)")
    print("   - demos/demo_crossfilter.html (linked brushing)")
    print("   - demos/demo_streaming.html   (live-updating chart)")
    print("   Open in browser for full interactivity!")

    print("\n" + "=" * 60)
    print("Demo complete! 19 tools, 76 tests, dual PNG+HTML output.")
    print("=" * 60)


if __name__ == "__main__":
    main()

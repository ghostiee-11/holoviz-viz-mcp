"""Showcase: ML Model Evaluator

Demonstrates: execute_code, crossfilter, overlays, annotations.
Creates confusion matrix, feature importances, and ROC-like curves.
Run: python demos/showcase_ml_evaluator.py
"""

import sys
sys.path.insert(0, "src")

from holoviz_viz_mcp.tools.data import load_sample_data
from holoviz_viz_mcp.tools.viz import create_plot, execute_code
from holoviz_viz_mcp.tools.crossfilter import create_crossfilter
from holoviz_viz_mcp.tools.dashboard import create_dashboard


def main():
    print("ML Model Evaluator Showcase")
    print("=" * 50)

    # Load iris as a classification dataset
    print("\n1. Loading iris dataset...")
    load_sample_data("iris")

    # Create feature importance bar chart via execute_code
    print("2. Creating feature importance chart...")
    fi_result = execute_code("""
import pandas as pd
import holoviews as hv

# Simulated feature importances (from a trained model)
fi = pd.DataFrame({
    'feature': ['petal_length', 'petal_width', 'sepal_length', 'sepal_width'],
    'importance': [0.44, 0.42, 0.10, 0.04]
}).sort_values('importance', ascending=True)

result = fi.hvplot.barh(
    x='feature', y='importance',
    title='Feature Importances (Random Forest)',
    color='#4a90d9', width=500, height=300,
)
""")
    fi_id = fi_result[0].text.split("'")[1]
    print(f"   {fi_result[0].text}")

    # Create confusion matrix heatmap
    print("3. Creating confusion matrix...")
    cm_result = execute_code("""
import pandas as pd
import numpy as np
import holoviews as hv

# Simulated confusion matrix
species = ['setosa', 'versicolor', 'virginica']
cm = np.array([[49, 1, 0], [0, 45, 5], [0, 3, 47]])

records = []
for i, actual in enumerate(species):
    for j, predicted in enumerate(species):
        records.append({'Actual': actual, 'Predicted': predicted, 'Count': cm[i][j]})

cm_df = pd.DataFrame(records)
result = cm_df.hvplot.heatmap(
    x='Predicted', y='Actual', C='Count',
    title='Confusion Matrix', cmap='Blues',
    width=400, height=350,
)
""")
    cm_id = cm_result[0].text.split("'")[1]
    print(f"   {cm_result[0].text}")

    # Create crossfilter of actual data
    print("4. Creating data exploration crossfilter...")
    cf = create_crossfilter(
        "iris",
        views="scatter,petal_length,petal_width;hist,sepal_length;box,species,sepal_width",
        color_by="species",
        title="Iris Data Explorer",
    )
    cf_id = cf[0].text.split("'")[1]
    print(f"   {cf[0].text}")

    # Build final dashboard
    print("5. Building ML evaluator dashboard...")
    dash = create_dashboard(f"{fi_id},{cm_id}", title="ML Model Evaluator", layout="row")

    with open("demos/demo_ml_evaluator.html", "w") as f:
        f.write(dash[2].resource.text)
    with open("demos/demo_ml_crossfilter.html", "w") as f:
        f.write(cf[2].resource.text)

    print("\n   Saved:")
    print("   - demos/demo_ml_evaluator.html  (feature importances + confusion matrix)")
    print("   - demos/demo_ml_crossfilter.html (linked data explorer)")
    print("   Open in browser for full interactivity!")


if __name__ == "__main__":
    main()

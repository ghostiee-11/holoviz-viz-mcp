# Demo Prompts

Ready-to-use prompts you can paste into Claude Desktop, Cursor, VS Code Copilot, or any MCP client after setup.

---

### 1. Basic scatter plot

> Load the iris dataset and create a scatter plot of sepal_length vs sepal_width, colored by species.

### 2. Data exploration workflow

> Load the iris sample data, analyze it, and show me the suggested visualizations. Then create the top 3.

### 3. Crossfilter dashboard (linked brushing)

> Load iris and create a crossfilter dashboard with a scatter plot of sepal_length vs sepal_width, a histogram of petal_length, and a box plot of species vs petal_width. Color everything by species.

_Select/brush points in any plot and watch all other plots update in real time._

### 4. Streaming visualization

> Create a streaming line chart that updates every 300ms. Title it "Live Sensor Feed".

_Open the HTML output in a browser to see the live animation with play/pause controls._

### 5. Data transformation pipeline

> Load the iris dataset. Filter it to only rows where petal_length > 4.0, then group by species and show the mean of each numeric column. Create a bar chart of the result.

### 6. Annotations

> Load iris and create a scatter plot of sepal_length vs sepal_width. Then add a horizontal threshold line at y=3.0 in red, and a vertical line at x=6.0 in blue.

### 7. Overlay comparison

> Load iris. Create two scatter plots: one of sepal_length vs sepal_width, another of sepal_length vs petal_width. Then overlay them on shared axes.

### 8. Custom code execution

> Load iris. Then execute this code:
> ```python
> import holoviews as hv
> from holoviews.selection import link_selections
> scatter = df.hvplot.scatter('sepal_length', 'sepal_width', color='species', width=400, height=300)
> hist = df.hvplot.hist('petal_length', color='species', width=400, height=300)
> result = link_selections(scatter + hist)
> ```

### 9. Full dashboard

> Load iris. Create a scatter plot, a histogram of petal_length, and a box plot of species vs sepal_width. Then combine them into a dashboard with tabs layout.

### 10. Dark theme

> Load the iris dataset and create a scatter plot of sepal_length vs sepal_width with the dark theme.

### 11. Multi-format data loading

> Load data from this URL: https://raw.githubusercontent.com/mwaskom/seaborn-data/master/penguins.csv
> Then analyze it and create a scatter plot of bill_length_mm vs body_mass_g colored by species.

### 12. Merge datasets

> Load both iris and penguins sample datasets. Show me what columns each has and their shapes.

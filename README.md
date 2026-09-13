# PyPrism Plot

GraphPrism-inspired, publication-ready styling for Python's Matplotlib and Seaborn
ecosystem. PyPrism Plot provides a focused theme, curated discrete palettes, and
statistical annotation helpers while leaving plotting and data manipulation to the
libraries you already use.

## Install, import, and plot

PyPrism Plot is a regular Python library. Install it into the Python
environment you already use:

```bash
python -m pip install git+https://github.com/darrentymeczko/PyPrism_Plots.git
```

Then import it alongside Matplotlib and call its functions directly:

```python
import matplotlib.pyplot as plt
import pyprism_plot as ppp

# Apply the style to all Matplotlib plots created from this point onward.
ppp.use_prism(palette="colorblind_safe")

fig, ax = plt.subplots()
ax.plot([1, 2, 3, 4], [2.1, 3.4, 3.8, 5.2], marker="o")
ax.set(xlabel="Time (hours)", ylabel="Response", title="Treatment response")
plt.show()
```

The package name used during installation is `pyprism-plot`, while the import name
is `pyprism_plot`.

> [!NOTE]
> This independent open-source project is not affiliated with, endorsed by, or
> sponsored by GraphPad Software. GraphPad and Prism are trademarks of their
> respective owner. The project takes design inspiration from the open-source
> [`ggprism`](https://github.com/csdaw/ggprism) package but contains an original
> Python implementation and original palette data.

## Common ways to use PyPrism Plot

### Style every subsequent plot

Call `use_prism()` once near the top of a script or notebook:

```python
import pyprism_plot as ppp

ppp.use_prism()
```

### Style only part of a script

Use `prism_context()` when you want the settings restored afterward:

```python
import matplotlib.pyplot as plt
import pyprism_plot as ppp

with ppp.prism_context(palette="floral", border=True):
    fig, ax = plt.subplots()
    ax.bar(["Control", "Drug A", "Drug B"], [2.2, 3.1, 4.4])
    ax.set(ylabel="Response", title="Experiment results")
```

### Style an axes that already exists

`style_axes()` works with plots made by Matplotlib or Seaborn:

```python
import seaborn as sns
import pyprism_plot as ppp

ax = sns.scatterplot(data=my_data, x="time", y="response", hue="treatment")
ppp.style_axes(ax, minor_ticks=True)
```

### Use palettes and significance annotations

```python
import matplotlib.pyplot as plt
import pyprism_plot as ppp

values = [2.2, 3.1, 4.4, 5.0]
fig, ax = plt.subplots()
colors = ppp.get_palette("colorblind_safe", 4)
ax.bar(range(4), values, color=colors)
ppp.significance_bar(ax, 0, 3, y=5.2, text="p < 0.01")
```

The default significance bracket is sized for publication figures. Its height,
line width, label size, and label spacing can all be adjusted independently:

```python
ppp.significance_bar(
    ax,
    0,
    3,
    y=5.2,
    text="p < 0.01",
    height=0.2,
    line_width=2.0,
    font_size=14,
    text_offset=0.08,
)
```

## Features

- Clean white panels, bold typography, outward ticks, heavy axes, and no grid
- Global, temporary-context, and single-axes styling APIs
- Eight discrete palettes, including a color-vision-accessible option
- Optional full panel borders and minor ticks
- Significance brackets for common scientific figures
- Native compatibility with Matplotlib and Seaborn

## Complete example

```python
import matplotlib.pyplot as plt
import numpy as np
import pyprism_plot as ppp

x = np.arange(4)
means = [2.2, 3.1, 4.4, 5.0]

with ppp.prism_context(palette="colorblind_safe"):
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.bar(x, means, color=ppp.get_palette("colorblind_safe", 4))
    ax.set(xlabel="Treatment", ylabel="Response", title="Dose response")
    ax.set_xticks(x, ["Control", "Low", "Medium", "High"])
    ppp.significance_bar(ax, 0, 3, 5.2, "p < 0.01")
    fig.savefig("dose-response.svg")
```

See [`examples/gallery.py`](examples/gallery.py) for Matplotlib and Seaborn
examples. Run it with:

```bash
python examples/gallery.py
```

## Development setup

The Conda environment is for contributors and maintainers only. From a cloned
repository:

```bash
conda env create -f environment.yml
conda activate pyprism
```

Alternatively, create or activate any Python 3.10+ environment and install the
development dependencies:

```bash
python -m pip install -e ".[dev]"
```

Run the project checks with:

```bash
pytest
ruff check .
python -m build
twine check dist/*
```

Pull requests are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

## Design references

The API and styling goals were informed by `ggprism`, particularly its
`theme_prism()`, discrete color/fill scales, optional borders, axis text angle,
minor tick guide, and p-value annotation features. Matplotlib concepts are used
where they fit naturally rather than reproducing ggplot2 internals.

## License

MIT. See [LICENSE](LICENSE).

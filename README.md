# PyPrism Plot

GraphPrism-inspired, publication-ready styling for Python's Matplotlib and Seaborn
ecosystem. PyPrism Plot provides a focused theme, curated discrete palettes, and
statistical annotation helpers while leaving plotting and data manipulation to the
libraries you already use.

> [!NOTE]
> This independent open-source project is not affiliated with, endorsed by, or
> sponsored by GraphPad Software. GraphPad and Prism are trademarks of their
> respective owner. The project takes design inspiration from the open-source
> [`ggprism`](https://github.com/csdaw/ggprism) package but contains an original
> Python implementation and original palette data.

## Features

- Clean white panels, bold typography, outward ticks, heavy axes, and no grid
- Global, temporary-context, and single-axes styling APIs
- Eight discrete palettes, including a color-vision-accessible option
- Optional full panel borders and minor ticks
- Significance brackets for common scientific figures
- Native compatibility with Matplotlib and Seaborn

## Install the development environment

[Miniconda](https://docs.conda.io/projects/miniconda/en/latest/) is recommended.
From the repository root:

```bash
conda env create -f environment.yml
conda activate pyprism
```

To update an existing environment after dependency changes:

```bash
conda env update -n pyprism -f environment.yml --prune
```

For a minimal pip install instead:

```bash
python -m pip install -e .
```

## Quick start

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

To style plots globally, call `ppp.use_prism()`. To modify one axes after it has
been drawn, call `ppp.style_axes(ax, border=True, minor_ticks=True)`.

See [`examples/gallery.py`](examples/gallery.py) for Matplotlib and Seaborn
examples. Run it with:

```bash
python examples/gallery.py
```

## Development

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


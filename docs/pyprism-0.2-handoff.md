# PyPrism 0.2.0 handoff: plotting functions for the figure program

This answers the "extend PyPrism Plot with the plotting functions a figure program
needs" task. It lists the final API, the shape of what each function returns, and
every place the result differs from that spec. Use it to switch the figure program
from hand-drawn Matplotlib over to PyPrism.

## Status

- **Released:** on `main` at https://github.com/darrentymeczko/PyPrism_Plots, commit
  `f04b421`. `pyprism_plot.__version__ == "0.2.0"`.
- **0.2.1** fixes autoscaling: in 0.2.0, `bar_dots`, `grouped_bars` and
  `xy_lines` left the limits at `(0, 1)` when no replicate points were drawn.
  Calling `ax.autoscale_view()` afterwards works around it and stays harmless
  after upgrading.
- **Install:** `python -m pip install --upgrade git+https://github.com/darrentymeczko/PyPrism_Plots.git`.
  The local `pyprism` conda env has a stale editable install that points to an old
  folder, and its NumPy linalg crashes. Don't rely on that env.
- **Tested with:** Python 3.13 and Matplotlib 3.11.2 on Windows, Agg backend. 99 tests
  pass with 99% coverage. Not tested on the minimum supported Matplotlib (3.8).
- **Dependencies:** Matplotlib and NumPy only. NumPy is now declared; it was already
  installed with Matplotlib.
- **Backwards compatible:** every 0.1.0 call still works. One exception: an invalid
  `axis_text_angle` now raises a different `ValueError` message (see section 6).
- **Source:** `src/pyprism_plot/plots.py`, `annotations.py`, `theme.py`. Tests:
  `tests/test_plots.py`. Rendered examples of every function:
  `examples/pyprism_plots_gallery.png` (made by `examples/gallery.py`, with axes
  placed in inches on a fixed page).

## Rules that apply to every new function

- **Axes-level only.** Each function draws only into the `ax` it is given. None of
  them calls `plt.*`, `fig.savefig`, `tight_layout`, or changes rcParams. A test
  checks that figure artists, `fig.axes`, every axes position, other axes and
  rcParams are unchanged after each call. Things a function can still do to *its
  own* `ax`:
  - tick positions and labels: only when you pass `labels=` / `cluster_labels=`
    (heatmap labels always set them)
  - axis limits: autoscale unless told otherwise; heatmap always sets them
  - log scale: `xy_lines(logx=True)`
  - a legend: `grouped_bars(legend=True)`
  - hidden spines and ticks: `heatmap(frame=False)`, the default
  - an inset colour-bar axes: `heatmap` when you pass no `cbar_ax`
- **Units.**
  - In data units: positions, widths, jitter, `height`, `text_offset`.
  - In points: `capsize`, `dot_size`, `marker_size`, all line widths.
  - In points²: `point_size` (as in `ax.scatter`).
  - Cap length is `2 * capsize`, the same as Matplotlib's `errorbar(capsize=...)`.
- **Limits.**
  - `autoscale=True` (default) works like normal Matplotlib autoscaling. Bars stick
    to `baseline` (default 0), as `ax.bar` does.
  - `autoscale=False` keeps the current `ax` limits **and turns autoscaling off**
    for that axes. It is the same as calling `ax.set_xlim(ax.get_xlim())` and
    `ax.set_ylim(ax.get_ylim())` after drawing.
  - `xlim=` and `ylim=` are applied last.
- **Text** uses the rcParams in effect unless you pass `font_size=` (or
  `label_font_size=` in `heatmap`).
- **Colours.** `colors=None` uses the colours of `rcParams["axes.prop_cycle"]`, so
  `prism_context(palette=...)` takes effect.
  - **Differs:** a palette set only on the axes with `style_axes(ax, palette=...)`
    is *not* picked up, because reading it would need private Matplotlib API. Pass
    `colors=ppp.get_palette(name)` explicitly in that case.
  - `colors` can be one colour or a sequence, cycled over categories (or over
    series in `grouped_bars` and `xy_lines`).
- **Tint.** The column fill is `tint_color(color, tint)`, which keeps `tint` of the
  colour and mixes in white for the rest: fill = `1 - tint * (1 - rgb)`. So
  `tint=0.3` is 30% colour and 70% white; `tint=1` is the full colour. Alpha is
  kept. `tint_color` is public.
- **Error inputs** (the spec said "yerr symmetric or (lower, upper)"):
  - `err=` gives **distances from the centre**, following Matplotlib's `yerr`
    convention. Use a 1-D array of length n (symmetric), or a `(lower, upper)` pair
    with shape `(2, n)`. Negative values raise `ValueError`.
  - **Added:** `bounds=(low, high)` gives **absolute interval ends** with shape
    `(2, n)`, for median/IQR and 95% CI. Each value must satisfy
    `low <= centre <= high`. You can't pass both `err` and `bounds`.
  - Watch the ambiguity: with exactly 2 categories, `err=[a, b]` is symmetric, and
    only a nested `[[lo0, lo1], [hi0, hi1]]` is asymmetric.
- **What NaN and None skip:**
  - A NaN replicate is dropped.
  - A category whose replicates are `None`, empty or all NaN draws no points.
  - A NaN or `None` centre draws no bar and no error bar. Its points still draw if
    there are any.
  - A NaN error draws no error bar. If only one side of `(lower, upper)` is NaN,
    only the other side is drawn.
  - With the default mean ± SD, a category with a single replicate gets a bar but
    no error bar (SD is undefined).
  - An error bar whose total length is zero is not drawn (`None`). A cap on a
    zero-length side is `None`.
  - Positions of the other categories never move. `positions` must be finite;
    NaN positions raise.
- **Statistics.** PyPrism computes none, except that `bar_dots` and
  `grouped_bars` fall back to mean ± SD (`ddof=1`) when `centre` or `err` is left
  out. Pass `centre` with `err` or `bounds` to plot SEM, median/IQR or CI.
- **Jitter** is deterministic: point `k` of `m` sits at
  `position + np.linspace(-jitter/2, jitter/2, m)[k]`, in input order. A single
  point sits on the position. `jitter` is the **total** spread width.
- **zorder** is one base value per call. `bar_dots` and `grouped_bars` use bar =
  `z`, points = `z+1`, error bars = `z+2`, centre dot or line = `z+3`. `xy_lines`
  uses points = `z`, error bars = `z+1`, line = `z+2`.
- **Flat list for gids.** Every result dataclass has `.artists()`, which returns
  all the created artists in one flat list.

### Shared error-bar structure

```python
@dataclass
class ErrorBarArtists:
    line: Line2D                                # the whisker
    caps: tuple[Line2D | None, Line2D | None]   # (lower cap, upper cap)
    def artists(self) -> list[Artist]
```

- **Caps** are separate one-point Line2D markers: `"_"` on vertical graphs, `"|"` on
  horizontal ones. Their data coordinates are the interval ends.
- **Lower cap position** (vertical graph): `caps[0].get_ydata()[0] == centre - lower`.
- **Horizontal graphs:** read the ends with `get_xdata()` instead.

## 1. `bar_dots`: columns with replicate points, vertical or horizontal

```python
bar_dots(ax, values, *, positions=None, orientation="vertical", centre=None, err=None,
         bounds=None, errorbars=True, colors=None, width=0.6, shape="bar", points=True,
         jitter=0.25, tint=0.3, edge_color=None, edge_width=1.3, err_color="#202020",
         err_width=1.0, capsize=3.0, point_size=18.0, point_color=None,
         point_edgecolor="black", point_edgewidth=0.5, point_marker="o", dot_size=8.0,
         mean_line_width=2.0, baseline=0.0, zorder=2.0, labels=None, font_size=None,
         autoscale=True, xlim=None, ylim=None) -> BarDotsArtists
```

**Returns:**

```python
@dataclass
class BarDotsArtists:
    bars: list[Rectangle | Line2D | None]       # one per category
    errorbars: list[ErrorBarArtists | None]
    points: list[PathCollection | None]
    labels: list[Text]                          # tick labels; [] unless labels= given
```

**Notes and differences from the spec:**

- **`values`:** one array of replicates per category. It may be `None` when you
  pass `centre`; the category count then comes from `centre`.
- **Horizontal orientation:**
  - Categories go along y and bars grow along x from `baseline`.
  - For bar `i`: `Rectangle.get_x() == baseline`,
    `get_y() == positions[i] - width/2`, `get_width() == centre - baseline` and
    `get_height() == width`.
  - Points are at `(value, position + jitter offset)`.
  - Nothing inverts the y axis, so category 0 is at the bottom unless you invert it
    or pass descending `positions`.
- **`shape`:**
  - `"bar"`: the Rectangle described above. The edge is the full colour unless you
    set `edge_color`.
  - `"dot"`: `bars[i]` is a one-point Line2D marker `"o"`. Its face is the colour,
    its edge is `point_edgecolor` and `point_edgewidth`, and its size is `dot_size`.
  - `"line"`: `bars[i]` is a Line2D across `position ± width/2`, in the colour, with
    width `mean_line_width`. On horizontal graphs it is drawn **vertically**
    (perpendicular to the value axis), not horizontally as the spec put it.
- **Points:** the face is the category colour (or `point_color`) and the edge is
  black, 0.5 pt.
- **`labels=`:** sets the ticks of the category axis to `positions` with those
  texts, then returns the tick-label Text objects. Matplotlib can recreate tick
  objects when the ticks change later, so set gids on them after your final tick
  changes.
- **`errorbars=False`:** turns error bars off entirely. There is no `err=False`.

## 2. `significance_bar_h`: horizontal bracket (`significance_bar` unchanged)

```python
significance_bar_h(ax, y1, y2, x, text, *, height=None, color="black", line_width=1.5,
                   font_size=None, text_offset=None, clip_on=False) -> (Line2D, Text)
significance_bar(ax, x1, x2, y, text, *, height=None, color="black", line_width=1.5,
                 font_size=12.0, text_offset=None, clip_on=False) -> (Line2D, Text)
```

- **Geometry:**
  - The line runs through x `[x, x+height, x+height, x]` and y `[y1, y1, y2, y2]`.
  - The ticks start at `x` and point left from the spine at `x + height`.
  - The text is at `(x + height + text_offset, (y1+y2)/2)` with `ha="left"`,
    `va="center"`.
- **Defaults:** `height` is 3% and `text_offset` is 2.5% of the current x span.
- **Differs: the keyword is `font_size`, not `fontsize`.** `significance_bar`
  already had `font_size` (added before this task), so the new function uses the
  same name. There is no alias.
- **Differs: default sizes.** `significance_bar` keeps its 0.1.0 default of
  `font_size=12.0` for backwards compatibility, which is a hard-coded size. Pass
  `font_size=None` to use rcParams. `significance_bar_h` defaults to `None`.
- Both return `(line, text)` and use `ax.plot` and `ax.text`.

## 3. `grouped_bars`: grouped columns

```python
grouped_bars(ax, data, *, cluster_positions=None, series_width=0.16, bar_width=None,
             orientation="vertical", centre=None, err=None, bounds=None, errorbars=True,
             colors=None, shape="bar", points=True, jitter=None, tint=0.3,
             edge_color=None, edge_width=1.3, err_color="#202020", err_width=1.0,
             capsize=3.0, point_size=14.0, point_color=None, point_edgecolor="black",
             point_edgewidth=0.5, point_marker="o", dot_size=7.0, mean_line_width=2.0,
             baseline=0.0, zorder=2.0, cluster_labels=None, series_labels=None,
             legend=False, font_size=None, autoscale=True, xlim=None, ylim=None)
             -> GroupedBarsArtists
```

**Returns:**

```python
@dataclass
class GroupedBarsArtists:
    bars: dict[tuple[int, int], Rectangle | Line2D]      # key (cluster, series)
    errorbars: dict[tuple[int, int], ErrorBarArtists]
    points: dict[tuple[int, int], PathCollection]
    labels: list[Text]                  # cluster tick labels; [] unless cluster_labels=
    legend_handles: list[Patch | Line2D]   # one per series
    legend: Legend | None               # only when legend=True
```

**Notes and differences from the spec:**

- **`data[cluster][series]`:** an array of replicates, or `None`. A cluster may be
  `None` or list fewer series than the others; missing slots count as empty. The
  number of series is the longest cluster, or `len(series_labels)` if that is
  larger.
- **Differs: empty cells are left out of the dicts** rather than stored as `None`.
  Use `.get((c, s))`.
- **Geometry:**
  - Series `s` of `S` is centred at
    `cluster_positions[c] + (s - (S-1)/2) * series_width`.
  - **Added:** `bar_width` defaults to `series_width`, which makes bars touch;
    set it smaller to leave gaps.
  - `jitter=None` means `0.4 * bar_width`.
- **`centre`, `err` and `bounds`** are nested like `data`, with one entry per cell.
  Each `err` cell is a number (symmetric) or a `(lower, upper)` distance pair. Each
  `bounds` cell is an absolute `(low, high)` pair. `None` cells are allowed.
- **`colors`:** one per **series**.
- **`legend` defaults to `False`.** The caller places the legend with
  `ax.legend(handles=result.legend_handles, ...)`.
- **Legend handles:**
  - Labels come from `series_labels`, otherwise `"Series 1"`, `"Series 2"`, ….
  - For `shape="bar"` they are Patches with the same tinted face, edge colour and
    edge width as the bars.
  - **Differs:** for `"dot"` and `"line"` they are Line2D proxies (a marker or a
    line) so they match what is drawn.
- **`orientation="horizontal"`** is supported, the same way as in `bar_dots`.

## 4. `xy_lines`: XY lines with error bars

```python
xy_lines(ax, x, series, *, err=None, colors=None, markers=True, marker_size=6.0,
         line_width=1.5, err_color=None, err_width=1.0, capsize=3.0, points=None,
         jitter=0.0, point_size=12.0, point_tint=0.5, point_edgecolor="none",
         point_edgewidth=0.5, logx=False, zorder=2.0, autoscale=True, xlim=None,
         ylim=None) -> XYLinesArtists
```

**Returns:**

```python
@dataclass
class XYLinesArtists:
    series: dict[str, XYSeriesArtists]       # in the order of `series`

@dataclass
class XYSeriesArtists:
    line: Line2D                       # the line and its markers, label=name
    errorbars: list[ErrorBarArtists | None]  # one per x value
    points: PathCollection | None      # all of the series' replicate points
```

**Notes and differences from the spec:**

- **`series[name]`:** a y array (length `len(x)`) or a **tuple** `(y, low, high)` of
  arrays with absolute error ends. Lists are always read as plain y.
- **`err[name]`:** distances for series given as plain y, symmetric or with shape
  `(2, n)`. Passing both a tuple and an `err` entry for the same series raises.
  Unknown names in `err` or `points` raise.
- **Gaps:** NaN y values break the line (normal Matplotlib behaviour), and those x
  values get `errorbars[i] = None`.
- **Differs: `points` is a mapping, not a bool.** `points[name]` holds the
  replicates per x value: a ragged sequence, or a 2-D `(n_x, n_replicates)` array.
  - They are drawn **behind** the line in one PathCollection per series.
  - The face is `tint_color(series colour, point_tint)` and there is no edge by
    default.
  - The spread is `jitter` in x data units. With `logx=True` it is in **decades**
    (multiplicative).
- **Differs: error bars default to the series colour** (`err_color=None`), as in
  Prism XY graphs, not `#202020`. Pass `err_color="#202020"` for the column look.
- **`markers`:** `True` cycles through `o s ^ D v` per series, `False` draws none,
  and a string or sequence picks them. Markers are filled with the series colour.
- **`logx=True`:** calls `ax.set_xscale("log")` on this axes.
- **Legend:** there is no legend option. Lines carry `label=name`, so `ax.legend()`
  works.

## 5. `heatmap`: matrix with a colour bar

```python
heatmap(ax, matrix, *, row_labels=None, col_labels=None, cmap="RdBu_r", center=0.0,
        vmin=None, vmax=None, annotations=None, fmt="{:.2g}",
        text_colors=("black", "white"), nan_color="#D9D9D9", nan_label="n/a",
        cell_edge_color="white", cell_edge_width=0.0, cbar=True, cbar_ax=None,
        cbar_label="", cbar_pad=0.03, cbar_width=0.05, font_size=None,
        label_font_size=None, col_label_rotation=0.0, frame=False) -> HeatmapArtists
```

**Returns:**

```python
@dataclass
class HeatmapArtists:
    mesh: QuadMesh                     # the cells (a ScalarMappable)
    colorbar: Colorbar | None
    cbar_ax: Axes | None               # the axes holding the colour bar
    texts: list[list[Text | None]]     # texts[row][col]; [] when annotations are off
    row_labels: list[Text]             # [] unless row_labels= given
    col_labels: list[Text]
```

**Notes and differences from the spec:**

- **Differs: the cells are a `pcolormesh` QuadMesh, not an `imshow` image.** Cells
  come out as vector shapes in SVG and PDF instead of a scaled raster. Cell `(r, c)`
  is centred at `x=c, y=r`.
- **Limits:** set to `(-0.5, ncols-0.5)` and `(nrows-0.5, -0.5)`, so row 0 is at the
  top.
- **Differs: there are no `autoscale`, `xlim` or `ylim` options.**
- **Differs: the aspect is not forced to equal.** Equal aspect would make
  Matplotlib shrink the axes box, which breaks exact placement.
- **Normalisation:**
  - With `center` set (default 0) and no `vmin` or `vmax`, the limits are symmetric
    about `center`.
  - With only one of `vmin` or `vmax`, the other is mirrored about `center`.
  - With both, a `TwoSlopeNorm` puts `center` at the colormap midpoint.
  - `center=None` scales linearly between `vmin` and `vmax`, defaulting to the data
    range.
- **`annotations`:** `None` for no text, `True` to format the values with `fmt`, or
  a matrix of strings with the same shape as the data. `None` or `""` cells get no
  Text.
  - Text is `text_colors[0]` (dark) when the cell's relative luminance is above
    0.408, otherwise `text_colors[1]`.
- **NaN cells:** filled with `nan_color`. When annotations are on they always show
  `nan_label` (`"n/a"`), even if the annotation matrix has text for that cell.
- **Colour bar:**
  - `cbar_ax=` puts the colour bar in your axes.
  - Without it, PyPrism adds a child inset at `[1 + cbar_pad, 0, cbar_width, 1]` in
    `ax` fractions. The inset is *not* in `fig.axes`, and `ax` keeps its position.
  - `cbar=False` draws no colour bar, even when you pass `cbar_ax`.
  - `cbar_label` uses rcParams for its size.
  - Built with `matplotlib.colorbar.Colorbar(cax, mesh)`, not `fig.colorbar`.
- **Fonts:** `font_size` sets the cell text and `label_font_size` sets the row and
  column labels.
- **Rotated column labels:** `col_label_rotation` other than 0 uses `ha="right"` and
  `rotation_mode="anchor"`.
- **`frame=False` (default):** hides all spines and sets tick length to 0 on `ax`.

## 6. Theme options

```python
prism_style(palette="colors", *, base_size=14, base_family="Arial",
            base_fontweight="bold", line_width=None, border=False,
            axis_text_angle=0, tight_save=True, explicit_fonts=False) -> dict
style_axes(ax, *, palette="colors", border=False, axis_text_angle=0,
           axis_text_ha=None, line_width=1.0, minor_ticks=False) -> Axes
```

`prism_context(**kw)`, `use_prism(**kw)` and `theme_prism(**kw)` accept the same
new keywords.

- **`tight_save=False`:** sets `savefig.bbox` to `"standard"` (stored by Matplotlib
  as `None`), so saving doesn't crop. The default `True` keeps `"tight"`.
- **`explicit_fonts=True`:** `font.family` becomes the concrete list
  `[base_family, "Arial", "DejaVu Sans"]`, with duplicates removed. A figure saved
  after the context exits keeps its font. The default keeps the generic
  `"sans-serif"`. `font.sans-serif` is set either way.
- **`axis_text_angle`:** any finite number of degrees, where 0.1.0 accepted only
  0, 45, 90 or 270. Booleans, NaN, strings and `None` raise
  `ValueError("axis_text_angle must be a finite number of degrees.")`. **The
  message changed** from 0.1.0's "must be one of ...".
- **`axis_text_ha`:** `"left"`, `"center"` or `"right"`. It sets that alignment
  plus `rotation_mode="anchor"` on the x tick labels.
  - On Matplotlib 3.10+ it also sets `tick_params(labelrotation_mode="anchor")`,
    so ticks created later keep the mode.
  - On older Matplotlib only the existing labels get it.
  - With `None` (default), any non-zero angle is right-aligned and 0 is centred.
    That is the 0.1.0 behaviour, extended to arbitrary angles.
- **Differs:** `prism_style` only *validates* `axis_text_angle`. It did nothing more
  in 0.1.0 either, because Matplotlib has no rcParam for tick-label rotation. Call
  `style_axes` to rotate the labels.
- For 45° category labels:
  `ppp.style_axes(ax, axis_text_angle=45, axis_text_ha="right")`. Call it after
  `bar_dots(..., labels=...)`, because it styles the labels that exist at that point.

## Migrating the program's hand-drawn look

| Program's hand-drawn style              | PyPrism equivalent                              |
|-----------------------------------------|-------------------------------------------------|
| fill = colour mixed 30% with white       | default `tint=0.3` (`tint_color(c, 0.3)`)      |
| edge = full colour, linewidth 1.2–1.4    | default `edge_color=None`, `edge_width=1.3`    |
| error bars `#202020`, small caps         | default `err_color="#202020"`, `capsize=3.0`   |
| jittered replicate points, thin black edge | default `points=True`, `point_edgecolor="black"`, `point_edgewidth=0.5` |
| `label.set_fontsize()` after the bracket | `significance_bar(..., font_size=...)` / `significance_bar_h(..., font_size=...)` |
| mean ± SD                                | default (omit `centre` and `err`)               |
| mean ± SEM                               | `centre=means, err=sems`                        |
| median with IQR, 95% CI                  | `centre=medians, bounds=(low, high)`            |

If the program's random jitter is replaced, point positions will change once,
because jitter is now evenly spaced. After that, re-renders are identical.

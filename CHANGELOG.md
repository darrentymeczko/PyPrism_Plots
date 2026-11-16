# Changelog

## 0.3.0

Defaults now follow ggprism and GraphPad Prism. Every value and its source is in
`docs/prism-defaults.md`. Pass `style="classic"` to get the 0.2 look back.

### Changed (defaults)

- **Theme:** axis lines and ticks are `base_line_size × 2.134` pt (2.13 pt at
  `base_size=14`; was 1.0 pt). Tick-label padding follows `theme_prism`. Plain
  lines match the axis width, and markers are 7 pt.
- **Default palette:** `"colors"` is now ggprism's `prism_colour_pal("colors")`.
  So are `colorblind_safe`, `floral` and `stained_glass`. The 0.2 values are
  `*_classic`.
- **`bar_dots` / `grouped_bars`:**
  - solid palette-colour columns with a black outline at the axis width
  - black error bars at the axis width, with caps a third of the column wide
  - black points (24.8 pt², the size of a ggplot2 `size = 2` point), cycling
    ggprism's shape palette per column or per series
  - plain legend text with `legend=True`
- **`xy_lines`:**
  - ggprism's shape palette per series, with 7.1 pt markers
  - lines and error bars at the axis width
  - caps as wide as the marker
- **Brackets:**
  - 1.28 pt line with butt ends
  - plain label at 0.65 × `font.size`
  - label gap of 1.3 % of the axis span
  - asterisk-only labels vertically centred
- `style_axes` defaults to the prism sizes. It now also sets tick-label, axis-label
  and title size and weight, and its default `line_width` is derived from
  `base_size`.

### Added

- `style="prism" | "classic"` on `prism_style`, `style_axes`, `bar_dots`,
  `grouped_bars`, `xy_lines`, `significance_bar` and `significance_bar_h`.
- `DEFAULT`, the default of every style argument. `None` keeps its 0.2 meaning.
- Offset axes: `style_axes(offset=..., offset_gap=...)` and `offset_axes()`.
- Minor ticks per axis: `style_axes(minor_ticks="x" | "y" | True)` and
  `prism_style(minor_ticks=...)`. These give one minor tick between majors, and
  2-9 per decade on log axes.
- `prism_style(base_line_size=...)`, `style_axes(base_size=..., base_line_size=...,
  base_fontweight=...)`, `prism_line_width()`, `GGPLOT_LINE_PT`,
  `GGPLOT_TEXT_PT`, `STYLES`.
- `bar_dots` / `grouped_bars`: `cap_width` (data units) and
  `err_direction="both" | "up"`. `point_marker` accepts a shape palette name or a
  sequence of markers.
- `xy_lines`: `marker_edgecolor`. `markers` accepts a shape palette name.
- Brackets: `font_weight`.
- Palettes: all 65 ggprism colour palettes, its 45 fill palettes
  (`FILL_PALETTES`, `get_palette(..., kind="fill")`) and its 3 shape palettes
  (`SHAPE_PALETTES`, `get_shapes()`, `Shape`).
- `examples/gallery.py` writes `examples/prism_comparison.png`, which shows
  PyPrism beside the matching ggprism figures.

## 0.2.1

### Fixed

- With `autoscale=True`, `bar_dots()`, `grouped_bars()` and `xy_lines()` left
  the axis limits at their previous values (for example `(0, 1)`) unless
  replicate points were drawn. They now call `ax.autoscale_view()` after drawing.
  Limits the caller fixed beforehand are still kept.

## 0.2.0

### Added

- Axes-level plotting functions. Each draws only into the axes it is given and
  returns a dataclass of every artist it created:
  - `bar_dots()`: columns, centre dots, or centre lines with jittered replicate
    points, vertical or horizontal, returning `BarDotsArtists`.
  - `grouped_bars()`: clustered columns keyed by `(cluster, series)`, with legend
    proxy handles, returning `GroupedBarsArtists`.
  - `xy_lines()`: lines with markers, error bars, and optional replicate points,
    returning `XYLinesArtists` / `XYSeriesArtists`.
  - `heatmap()`: vector cells with optional annotations and a colour bar in an
    inset or a caller-supplied axes, returning `HeatmapArtists`.
- `ErrorBarArtists`, the whisker and cap artists of one error bar.
- `tint_color()`, which mixes a colour with white as the column fills do.
- `significance_bar_h()` for horizontal graphs.
- `prism_style(tight_save=..., explicit_fonts=...)` for fixed-size pages. The
  defaults keep the 0.1.0 behaviour.
- `style_axes(axis_text_ha=...)`, which aligns rotated tick labels with
  `rotation_mode="anchor"`.

### Changed

- `axis_text_angle` in `style_axes()` and `prism_style()` accepts any finite
  angle instead of only 0, 45, 90, or 270. Invalid values now raise
  `ValueError("axis_text_angle must be a finite number of degrees.")`.
- NumPy is now a declared dependency. It was already installed with Matplotlib.

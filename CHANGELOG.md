# Changelog

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

"""Prism-inspired plotting helpers for Matplotlib and Seaborn."""

from .annotations import significance_bar, significance_bar_h
from .palettes import (
    FILL_PALETTES,
    PALETTES,
    SHAPE_PALETTES,
    Shape,
    get_palette,
    get_shapes,
    list_palettes,
)
from .plots import (
    DEFAULT,
    BarDotsArtists,
    ErrorBarArtists,
    GroupedBarsArtists,
    HeatmapArtists,
    XYLinesArtists,
    XYSeriesArtists,
    bar_dots,
    grouped_bars,
    heatmap,
    tint_color,
    xy_lines,
)
from .theme import (
    GGPLOT_LINE_PT,
    GGPLOT_TEXT_PT,
    STYLES,
    offset_axes,
    prism_context,
    prism_line_width,
    prism_style,
    style_axes,
    theme_prism,
    use_prism,
)

__all__ = [
    "DEFAULT",
    "FILL_PALETTES",
    "GGPLOT_LINE_PT",
    "GGPLOT_TEXT_PT",
    "PALETTES",
    "SHAPE_PALETTES",
    "STYLES",
    "Shape",
    "BarDotsArtists",
    "ErrorBarArtists",
    "GroupedBarsArtists",
    "HeatmapArtists",
    "XYLinesArtists",
    "XYSeriesArtists",
    "bar_dots",
    "get_palette",
    "get_shapes",
    "grouped_bars",
    "heatmap",
    "list_palettes",
    "offset_axes",
    "prism_context",
    "prism_line_width",
    "prism_style",
    "significance_bar",
    "significance_bar_h",
    "style_axes",
    "theme_prism",
    "tint_color",
    "use_prism",
    "xy_lines",
]

__version__ = "0.3.0"

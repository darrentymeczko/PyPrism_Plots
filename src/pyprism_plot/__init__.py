"""Prism-inspired plotting helpers for Matplotlib and Seaborn."""

from .annotations import significance_bar, significance_bar_h
from .palettes import PALETTES, get_palette, list_palettes
from .plots import (
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
from .theme import prism_context, prism_style, style_axes, theme_prism, use_prism

__all__ = [
    "PALETTES",
    "BarDotsArtists",
    "ErrorBarArtists",
    "GroupedBarsArtists",
    "HeatmapArtists",
    "XYLinesArtists",
    "XYSeriesArtists",
    "bar_dots",
    "get_palette",
    "grouped_bars",
    "heatmap",
    "list_palettes",
    "prism_context",
    "prism_style",
    "significance_bar",
    "significance_bar_h",
    "style_axes",
    "theme_prism",
    "tint_color",
    "use_prism",
    "xy_lines",
]

__version__ = "0.2.1"

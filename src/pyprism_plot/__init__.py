"""Prism-inspired plotting helpers for Matplotlib and Seaborn."""

from .annotations import significance_bar
from .palettes import PALETTES, get_palette, list_palettes
from .theme import prism_context, prism_style, style_axes, theme_prism, use_prism

__all__ = [
    "PALETTES",
    "get_palette",
    "list_palettes",
    "prism_context",
    "prism_style",
    "significance_bar",
    "style_axes",
    "theme_prism",
    "use_prism",
]

__version__ = "0.1.0"


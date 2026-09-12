"""Matplotlib theme and axis styling."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from typing import Any

import matplotlib as mpl
from cycler import cycler
from matplotlib.axes import Axes

from .palettes import get_palette

_ANGLES = {0, 45, 90, 270}


def _validate_angle(angle: int) -> None:
    if angle not in _ANGLES:
        raise ValueError("axis_text_angle must be one of 0, 45, 90, or 270.")


def prism_style(
    palette: str = "colors",
    *,
    base_size: float = 14,
    base_family: str = "Arial",
    base_fontweight: str = "bold",
    line_width: float | None = None,
    border: bool = False,
    axis_text_angle: int = 0,
) -> dict[str, Any]:
    """Build a Matplotlib rcParams dictionary with a clean scientific style."""
    _validate_angle(axis_text_angle)
    if base_size <= 0:
        raise ValueError("base_size must be greater than zero.")
    width = base_size / 14 if line_width is None else line_width
    if width <= 0:
        raise ValueError("line_width must be greater than zero.")

    return {
        "axes.prop_cycle": cycler(color=get_palette(palette)),
        "axes.facecolor": "white",
        "axes.edgecolor": "black",
        "axes.grid": False,
        "axes.labelcolor": "black",
        "axes.labelpad": base_size * 0.6,
        "axes.labelsize": base_size,
        "axes.labelweight": base_fontweight,
        "axes.linewidth": width,
        "axes.spines.top": border,
        "axes.spines.right": border,
        "axes.titlepad": base_size,
        "axes.titlesize": base_size * 1.2,
        "axes.titleweight": base_fontweight,
        "figure.facecolor": "white",
        "font.family": "sans-serif",
        "font.sans-serif": [base_family, "Arial", "DejaVu Sans", "sans-serif"],
        "font.size": base_size,
        "font.weight": base_fontweight,
        "legend.frameon": False,
        "legend.fontsize": base_size * 0.8,
        "legend.title_fontsize": base_size * 0.8,
        "lines.linewidth": width * 1.5,
        "lines.markeredgewidth": width,
        "savefig.bbox": "tight",
        "savefig.facecolor": "white",
        "xtick.direction": "out",
        "xtick.labelsize": base_size * 0.95,
        "xtick.major.size": base_size / 2.5,
        "xtick.major.width": width,
        "xtick.minor.size": base_size / 5,
        "xtick.minor.width": width,
        "ytick.direction": "out",
        "ytick.labelsize": base_size * 0.95,
        "ytick.major.size": base_size / 2.5,
        "ytick.major.width": width,
        "ytick.minor.size": base_size / 5,
        "ytick.minor.width": width,
    }


def use_prism(**kwargs: Any) -> None:
    """Apply the Prism-inspired style globally to subsequent Matplotlib plots."""
    mpl.rcParams.update(prism_style(**kwargs))


@contextmanager
def prism_context(**kwargs: Any) -> Iterator[None]:
    """Temporarily apply the Prism-inspired style inside a ``with`` block."""
    with mpl.rc_context(prism_style(**kwargs)):
        yield


def style_axes(
    ax: Axes,
    *,
    palette: str = "colors",
    border: bool = False,
    axis_text_angle: int = 0,
    line_width: float = 1.0,
    minor_ticks: bool = False,
) -> Axes:
    """Style one existing axes without changing global Matplotlib settings."""
    _validate_angle(axis_text_angle)
    if line_width <= 0:
        raise ValueError("line_width must be greater than zero.")

    ax.set_prop_cycle(color=get_palette(palette))
    ax.set_facecolor("white")
    ax.grid(False)
    for name, spine in ax.spines.items():
        spine.set_visible(border or name in {"left", "bottom"})
        spine.set_color("black")
        spine.set_linewidth(line_width)
    ax.tick_params(
        which="both", direction="out", top=False, right=False, width=line_width
    )
    ax.tick_params(which="major", length=5.6)
    ax.tick_params(which="minor", length=2.8)
    ax.tick_params(axis="x", labelrotation=axis_text_angle)
    horizontal_alignment = "right" if axis_text_angle in {45, 90, 270} else "center"
    for label in ax.get_xticklabels():
        label.set_horizontalalignment(horizontal_alignment)
    if minor_ticks:
        ax.minorticks_on()
    else:
        ax.minorticks_off()
    return ax


def theme_prism(**kwargs: Any) -> Mapping[str, Any]:
    """Alias for :func:`prism_style`, named for users familiar with ggprism."""
    return prism_style(**kwargs)


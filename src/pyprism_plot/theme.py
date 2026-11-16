"""Matplotlib theme and axis styling.

Sizes follow ggprism's ``theme_prism(base_size, base_line_size)``. Text sizes are
points, as in ggplot2. Line sizes are ggplot2 ``linewidth`` units, which are
about 0.75 mm: one unit is ``72.27 / 25.4 * 72 / 96`` = 2.134 pt (R's ``lwd = 1``
is 1/96 inch). :data:`GGPLOT_LINE_PT` and :data:`GGPLOT_TEXT_PT` hold the two
conversion factors.
"""

from __future__ import annotations

import math
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from numbers import Real
from typing import Any

import matplotlib as mpl
from cycler import cycler
from matplotlib.axes import Axes
from matplotlib.spines import Spine
from matplotlib.ticker import AutoMinorLocator

from .palettes import CLASSIC_NAMES, get_palette

GGPLOT_TEXT_PT = 72.27 / 25.4
"""Points per ggplot2 text ``size`` unit (mm)."""

GGPLOT_LINE_PT = 72.27 / 25.4 * 72 / 96
"""Points per ggplot2 ``linewidth`` unit (about 0.75 mm)."""

STYLES = ("prism", "classic")

_HORIZONTAL_ALIGNMENTS = {"left", "center", "right"}
_AXES_CHOICES = {"x": ("x",), "y": ("y",), "both": ("x", "y")}


def _validate_angle(angle: float) -> None:
    if (
        isinstance(angle, bool)
        or not isinstance(angle, Real)
        or not math.isfinite(angle)
    ):
        raise ValueError("axis_text_angle must be a finite number of degrees.")


def _check_style(style: str) -> None:
    if style not in STYLES:
        raise ValueError("style must be 'prism' or 'classic'.")


def _which_axes(value: bool | str, name: str) -> tuple[str, ...]:
    if value is False or value is None:
        return ()
    if value is True:
        return ("x", "y")
    if value not in _AXES_CHOICES:
        raise ValueError(f"{name} must be True, False, 'x', 'y' or 'both'.")
    return _AXES_CHOICES[value]


def _font_list(base_family: str) -> list[str]:
    return list(dict.fromkeys([base_family, "Arial", "DejaVu Sans"]))


def _palette_for(palette: str, style: str) -> list[str]:
    if style == "classic":
        palette = CLASSIC_NAMES.get(palette, palette)
    return get_palette(palette)


def prism_line_width(base_size: float = 14, base_line_size: float | None = None):
    """Return ggprism's axis line width in points for a theme size.

    ``base_line_size`` is in ggplot2 linewidth units and defaults to
    ``base_size / 14``, as in ``theme_prism``.
    """
    size = base_size / 14 if base_line_size is None else base_line_size
    return size * GGPLOT_LINE_PT


def prism_style(
    palette: str = "colors",
    *,
    base_size: float = 14,
    base_family: str = "Arial",
    base_fontweight: str = "bold",
    line_width: float | None = None,
    base_line_size: float | None = None,
    border: bool = False,
    axis_text_angle: float = 0,
    minor_ticks: bool | str = False,
    tight_save: bool = True,
    explicit_fonts: bool = False,
    style: str = "prism",
) -> dict[str, Any]:
    """Build a Matplotlib rcParams dictionary in the style of ggprism.

    Every size derives from ``base_size`` (points) and ``base_line_size``
    (ggplot2 linewidth units, default ``base_size / 14``), as in ggprism's
    ``theme_prism``. The axis lines and ticks are ``base_line_size * 2.134`` pt
    wide (2.13 pt at the default size), major ticks are ``base_size / 2.5`` pt
    long and minor ticks ``base_size / 5`` pt. ``line_width`` sets the axis line
    width in points directly instead.

    ``minor_ticks`` (``True``, ``"x"``, ``"y"`` or ``"both"``) turns on one minor
    tick between major ticks, as ggprism's ``guide_prism_minor`` draws.
    ``tight_save=False`` keeps ``savefig.bbox`` at ``"standard"`` so fixed-size
    pages are saved uncropped. ``explicit_fonts=True`` stores the concrete font
    list in ``font.family`` instead of the generic ``"sans-serif"``, so text keeps
    its font when a figure is drawn or saved outside the style context.

    ``style="classic"`` returns the PyPrism 0.2 settings (thinner lines, Matplotlib
    tick padding, and the ``*_classic`` palettes).

    Matplotlib has no rcParam for tick-label rotation, so ``axis_text_angle`` is
    only validated here; use :func:`style_axes` to rotate labels on an axes. The
    offset axis needs per-axes spines, so it is :func:`style_axes`-only too.
    """
    _validate_angle(axis_text_angle)
    _check_style(style)
    if base_size <= 0:
        raise ValueError("base_size must be greater than zero.")
    if style == "classic":
        width = base_size / 14 if line_width is None else line_width
    elif line_width is not None:
        width = line_width
    else:
        width = prism_line_width(base_size, base_line_size)
    if width <= 0:
        raise ValueError("line_width must be greater than zero.")
    minor_axes = _which_axes(minor_ticks, "minor_ticks")

    params = {
        "axes.prop_cycle": cycler(color=_palette_for(palette, style)),
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
        "font.family": _font_list(base_family) if explicit_fonts else "sans-serif",
        "font.sans-serif": [base_family, "Arial", "DejaVu Sans", "sans-serif"],
        "font.size": base_size,
        "font.weight": base_fontweight,
        "legend.frameon": False,
        "legend.fontsize": base_size * 0.8,
        "legend.title_fontsize": base_size * 0.8,
        "lines.linewidth": width * 1.5,
        "lines.markeredgewidth": width,
        "savefig.bbox": "tight" if tight_save else "standard",
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
    if style == "prism":
        params.update(
            {
                # theme_prism: axis.text.x margin t = 0.8 * base / 4 and
                # axis.text.y margin r = 0.5 * base / 4.
                "xtick.major.pad": 0.8 * base_size / 4,
                "xtick.minor.pad": 0.8 * base_size / 4,
                "ytick.major.pad": 0.5 * base_size / 4,
                "ytick.minor.pad": 0.5 * base_size / 4,
                # Lines and markers match the axis weight, as in ggprism's
                # examples (geom_smooth linewidth 1 at base_size 14).
                "lines.linewidth": width,
                "lines.markersize": 7.0,
                "legend.handlelength": 1.8,
            }
        )
    for axis in minor_axes:
        params[f"{axis}tick.minor.visible"] = True
        if f"{axis}tick.minor.ndivs" in mpl.rcParams:
            params[f"{axis}tick.minor.ndivs"] = 2
    return params


def use_prism(**kwargs: Any) -> None:
    """Apply the Prism-inspired style globally to subsequent Matplotlib plots."""
    mpl.rcParams.update(prism_style(**kwargs))


@contextmanager
def prism_context(**kwargs: Any) -> Iterator[None]:
    """Temporarily apply the Prism-inspired style inside a ``with`` block."""
    with mpl.rc_context(prism_style(**kwargs)):
        yield


class _TickBoundedSpine(Spine):
    """A spine that runs from its axis' first to last visible major tick.

    The bounds are recomputed on every draw, so they follow later changes to the
    limits or ticks, as ggprism's ``guide_prism_offset`` does.
    """

    def _tick_bounds(self) -> None:
        axis = self.axis
        if axis is None:
            return
        low, high = sorted(axis.get_view_interval())
        span = (high - low) or 1.0
        tolerance = span * 1e-9
        locs = [
            loc
            for loc in axis.get_majorticklocs()
            if low - tolerance <= loc <= high + tolerance
        ]
        if locs:
            self.set_bounds(min(locs), max(locs))

    def draw(self, renderer):  # noqa: D102
        self._tick_bounds()
        return super().draw(renderer)

    def get_window_extent(self, renderer=None):  # noqa: D102
        self._tick_bounds()
        return super().get_window_extent(renderer)


def offset_axes(ax: Axes, which: bool | str = True, gap: float | None = None) -> Axes:
    """Give *ax* Prism's offset axes.

    Each chosen axis line (``"x"``, ``"y"``, or both for ``True``/``"both"``) runs
    only from its first to its last major tick, like ggprism's
    ``guide_prism_offset``. Both the bottom and left axis lines also move ``gap``
    points away from the plot (default: the major tick length), so the x and y
    axes never meet at the corner, even when the data start on an axis.
    """
    axes = _which_axes(which, "which")
    if not axes:
        return ax
    for name in axes:
        spine = ax.spines["bottom" if name == "x" else "left"]
        if type(spine) is Spine:
            spine.__class__ = _TickBoundedSpine
    for name, axis in (("bottom", ax.xaxis), ("left", ax.yaxis)):
        length = (
            axis.get_major_ticks()[0].tick1line.get_markersize() if gap is None else gap
        )
        ax.spines[name].set_position(("outward", length))
    return ax


def _minor_ticks(ax: Axes, axes: tuple[str, ...]) -> None:
    for name in ("x", "y"):
        axis = ax.xaxis if name == "x" else ax.yaxis
        if name not in axes:
            axis.set_minor_locator(mpl.ticker.NullLocator())
        elif axis.get_scale() == "linear":
            axis.set_minor_locator(AutoMinorLocator(2))
        elif axis.get_scale() == "log":
            # Every decade's 2..9, as ggprism's log minor_breaks; Matplotlib's
            # default hides log minor ticks on axes spanning many decades.
            axis.set_minor_locator(
                mpl.ticker.LogLocator(subs=tuple(range(2, 10)), numticks=999)
            )
        else:
            axis.minorticks_on()


def style_axes(
    ax: Axes,
    *,
    palette: str = "colors",
    border: bool = False,
    axis_text_angle: float = 0,
    axis_text_ha: str | None = None,
    line_width: float | None = None,
    minor_ticks: bool | str = False,
    offset: bool | str = False,
    offset_gap: float | None = None,
    base_size: float | None = None,
    base_line_size: float | None = None,
    base_fontweight: str = "bold",
    style: str = "prism",
) -> Axes:
    """Style one existing axes without changing global Matplotlib settings.

    With ``style="prism"`` (default), sizes come from ``base_size`` (default: the
    ``font.size`` in effect) as in :func:`prism_style`: axis lines and ticks
    ``base_line_size * 2.134`` pt wide, ticks ``base_size / 2.5`` pt long (minor
    ``base_size / 5``), and bold black tick labels, axis labels and title.
    ``line_width`` sets the axis line width in points directly.

    ``minor_ticks`` (``True``, ``"x"``, ``"y"`` or ``"both"``) adds one minor tick
    between major ticks, like ``guide_prism_minor``. ``offset`` gives those axes
    Prism's offset look (see :func:`offset_axes`); ``offset_gap`` is the gap in
    points.

    ``axis_text_angle`` rotates the x tick labels by any angle in degrees. When
    ``axis_text_ha`` is given (for example ``"right"`` for 45 degree category
    labels), the labels use that alignment with ``rotation_mode="anchor"`` so the
    end of each label sits on its tick. When it is omitted, rotated labels are
    right-aligned and unrotated labels are centered.

    ``style="classic"`` applies the PyPrism 0.2 look: 1 pt lines, 5.6/2.8 pt ticks
    and unchanged text.
    """
    _validate_angle(axis_text_angle)
    _check_style(style)
    if axis_text_ha is not None and axis_text_ha not in _HORIZONTAL_ALIGNMENTS:
        raise ValueError("axis_text_ha must be 'left', 'center', 'right', or None.")
    size = mpl.rcParams["font.size"] if base_size is None else base_size
    if size <= 0:
        raise ValueError("base_size must be greater than zero.")
    if line_width is not None:
        width = line_width
    elif style == "classic":
        width = 1.0
    else:
        width = prism_line_width(size, base_line_size)
    if width <= 0:
        raise ValueError("line_width must be greater than zero.")
    minor_axes = _which_axes(minor_ticks, "minor_ticks")

    ax.set_prop_cycle(color=_palette_for(palette, style))
    ax.set_facecolor("white")
    ax.grid(False)
    for name, spine in ax.spines.items():
        spine.set_visible(border or name in {"left", "bottom"})
        spine.set_color("black")
        spine.set_linewidth(width)
    ax.tick_params(
        which="both",
        direction="out",
        top=False,
        right=False,
        width=width,
        color="black",
    )
    if style == "classic":
        ax.tick_params(which="major", length=5.6)
        ax.tick_params(which="minor", length=2.8)
    else:
        ax.tick_params(which="major", length=size / 2.5)
        ax.tick_params(which="minor", length=size / 5)
        ax.tick_params(axis="x", which="both", pad=0.8 * size / 4)
        ax.tick_params(axis="y", which="both", pad=0.5 * size / 4)
        ax.tick_params(which="both", labelsize=size * 0.95, labelcolor="black")
        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_fontweight(base_fontweight)
        for text in (ax.xaxis.label, ax.yaxis.label):
            text.set_fontsize(size)
            text.set_fontweight(base_fontweight)
            text.set_color("black")
        ax.xaxis.labelpad = ax.yaxis.labelpad = size * 0.6
        ax.title.set_fontsize(size * 1.2)
        ax.title.set_fontweight(base_fontweight)
    ax.tick_params(axis="x", labelrotation=axis_text_angle)
    if axis_text_ha is None:
        horizontal_alignment = "center" if axis_text_angle % 360 == 0 else "right"
        rotation_mode = None
    else:
        horizontal_alignment = axis_text_ha
        rotation_mode = "anchor"
        try:
            # Matplotlib 3.10+ keeps the mode on ticks created after this call.
            ax.tick_params(axis="x", labelrotation_mode=rotation_mode)
        except ValueError:
            pass
    for label in ax.get_xticklabels():
        label.set_horizontalalignment(horizontal_alignment)
        if rotation_mode is not None:
            label.set_rotation_mode(rotation_mode)
    if style == "classic":
        if minor_axes:
            ax.minorticks_on()
        else:
            ax.minorticks_off()
    else:
        _minor_ticks(ax, minor_axes)
    if offset:
        offset_axes(ax, offset, offset_gap)
    return ax


def theme_prism(**kwargs: Any) -> Mapping[str, Any]:
    """Alias for :func:`prism_style`, named for users familiar with ggprism."""
    return prism_style(**kwargs)

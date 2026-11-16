"""Axes-level plotting functions with a Prism-style look.

Every function draws only into the axes it is given, never touches the figure
or global state, and returns the artists it created so callers can label, edit
or remove them. Summary statistics belong to the caller: pass centre values and
error sizes, or let :func:`bar_dots` and :func:`grouped_bars` fall back to the
mean and standard deviation of the replicates.

Error sizes follow Matplotlib's ``yerr`` convention: one non-negative distance per
category (symmetric), or a ``(lower, upper)`` pair of distance arrays with shape
``(2, n)``. Pass ``bounds=(low, high)`` instead to give absolute interval ends,
such as an interquartile range or a confidence interval.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

import matplotlib as mpl
import numpy as np
from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.collections import PathCollection, QuadMesh
from matplotlib.colorbar import Colorbar
from matplotlib.colors import Normalize, TwoSlopeNorm, is_color_like, to_rgba
from matplotlib.legend import Legend
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle
from matplotlib.text import Text

from .palettes import SHAPE_PALETTES, Shape
from .theme import GGPLOT_TEXT_PT, STYLES

ERROR_COLOR = "#202020"
"""Error-bar colour of the classic (PyPrism 0.2) style."""
XY_MARKERS = ("o", "s", "^", "D", "v")
"""XY markers of the classic (PyPrism 0.2) style."""

GGPLOT_STROKE_PT = 0.5 * (96 / 25.4) / 2 * 72 / 96
"""ggplot2's default point ``stroke = 0.5`` in points (0.71 pt)."""
PRISM_POINT_SIZE = (0.75 * (2 * GGPLOT_TEXT_PT + 0.5 * (96 / 25.4) / 2)) ** 2
"""Scatter area (pt^2) of a ggplot2 ``size = 2`` point, as in ggprism's
column scatter examples: a 5.0 pt diameter."""
PRISM_MARKER_SIZE = 0.75 * (3 * GGPLOT_TEXT_PT + 0.5 * (96 / 25.4) / 2)
"""Marker diameter (pt) of a ggplot2 ``size = 3`` point, as in ggprism's XY
dose-response example: 7.1 pt."""

_SHAPES = {"bar", "dot", "line"}
_ORIENTATIONS = {"vertical", "horizontal"}
_DIRECTIONS = {"both", "up"}
_LINE_MARKERS = {"+", "x", "|", "_", "1", "2", "3", "4", "none", "None", ""}


@dataclass
class ErrorBarArtists:
    """One error bar: its whisker line and its ``(lower, upper)`` caps.

    A cap is ``None`` when that side of the interval has zero length or the cap
    size is zero.
    """

    line: Line2D
    caps: tuple[Line2D | None, Line2D | None]

    def artists(self) -> list[Artist]:
        """Return the whisker and caps that were drawn."""
        return [self.line, *(cap for cap in self.caps if cap is not None)]


@dataclass
class BarDotsArtists:
    """Artists created by :func:`bar_dots`, one list entry per category.

    ``bars[i]`` is a :class:`~matplotlib.patches.Rectangle` for ``shape="bar"``
    and a :class:`~matplotlib.lines.Line2D` for ``"dot"`` and ``"line"``. Entries
    are ``None`` where there was nothing to draw. ``labels`` holds the category
    tick labels when ``labels=`` was given, and is empty otherwise.
    """

    bars: list[Rectangle | Line2D | None]
    errorbars: list[ErrorBarArtists | None]
    points: list[PathCollection | None]
    labels: list[Text] = field(default_factory=list)

    def artists(self) -> list[Artist]:
        """Return every artist created, in a flat list."""
        return _flatten(self.bars, self.errorbars, self.points, self.labels)


@dataclass
class GroupedBarsArtists:
    """Artists created by :func:`grouped_bars`, keyed by ``(cluster, series)``.

    Keys are present only for cells that were drawn. ``legend_handles`` holds one
    proxy artist per series, styled like the bars, for placing a legend yourself.
    """

    bars: dict[tuple[int, int], Rectangle | Line2D]
    errorbars: dict[tuple[int, int], ErrorBarArtists]
    points: dict[tuple[int, int], PathCollection]
    labels: list[Text]
    legend_handles: list[Patch | Line2D]
    legend: Legend | None = None

    def artists(self) -> list[Artist]:
        """Return every artist drawn on the axes (not the legend proxies)."""
        artists = _flatten(self.bars, self.errorbars, self.points, self.labels)
        return artists + ([self.legend] if self.legend is not None else [])


@dataclass
class XYSeriesArtists:
    """Artists for one series of :func:`xy_lines`.

    ``errorbars`` has one entry per x value (``None`` where nothing was drawn).
    ``points`` holds the replicate points, if any were given.
    """

    line: Line2D
    errorbars: list[ErrorBarArtists | None]
    points: PathCollection | None = None

    def artists(self) -> list[Artist]:
        """Return every artist created for this series."""
        return _flatten([self.line], self.errorbars, [self.points])


@dataclass
class XYLinesArtists:
    """Artists created by :func:`xy_lines`, keyed by series name."""

    series: dict[str, XYSeriesArtists]

    def artists(self) -> list[Artist]:
        """Return every artist created, in a flat list."""
        return [a for item in self.series.values() for a in item.artists()]


@dataclass
class HeatmapArtists:
    """Artists created by :func:`heatmap`.

    ``texts[row][col]`` is the cell's annotation, or ``None`` when the cell has
    none. ``texts`` is empty when annotations are off.
    """

    mesh: QuadMesh
    colorbar: Colorbar | None
    cbar_ax: Axes | None
    texts: list[list[Text | None]]
    row_labels: list[Text]
    col_labels: list[Text]

    def artists(self) -> list[Artist]:
        """Return the mesh, cell texts and tick labels (not the colour bar)."""
        cells = [text for row in self.texts for text in row]
        return _flatten([self.mesh], cells, self.row_labels, self.col_labels)


def _flatten(*groups: Any) -> list[Artist]:
    artists: list[Artist] = []
    for group in groups:
        items = group.values() if isinstance(group, Mapping) else group
        for item in items:
            if isinstance(item, ErrorBarArtists):
                artists.extend(item.artists())
            elif item is not None:
                artists.append(item)
    return artists


def _check_non_negative(**values: float) -> None:
    for name, value in values.items():
        if value < 0:
            raise ValueError(f"{name} must not be negative.")


def _check_orientation(orientation: str) -> bool:
    if orientation not in _ORIENTATIONS:
        raise ValueError("orientation must be 'vertical' or 'horizontal'.")
    return orientation == "horizontal"


def tint_color(color: Any, amount: float = 0.3) -> tuple[float, float, float, float]:
    """Mix *color* with white, keeping *amount* of the colour (1 = unchanged)."""
    if not 0 <= amount <= 1:
        raise ValueError("amount must be between 0 and 1.")
    red, green, blue, alpha = to_rgba(color)
    return (
        1 - amount * (1 - red),
        1 - amount * (1 - green),
        1 - amount * (1 - blue),
        alpha,
    )


def _resolve_colors(colors: Any, n: int) -> list[Any]:
    if colors is None:
        cycle = mpl.rcParams["axes.prop_cycle"].by_key().get("color", ["black"])
    elif isinstance(colors, str) or is_color_like(colors):
        cycle = [colors]
    else:
        cycle = list(colors)
        if not cycle:
            raise ValueError("colors must not be empty.")
    return [cycle[i % len(cycle)] for i in range(n)]


def _per_item(value: Any, n: int, name: str) -> np.ndarray:
    if value is None:
        return np.full(n, np.nan)
    array = np.asarray(value, dtype=float)
    if array.ndim == 0:
        return np.full(n, float(array))
    if array.shape != (n,):
        raise ValueError(f"{name} must have one value per item ({n}).")
    return array.copy()


def _error_offsets(err: Any, n: int) -> tuple[np.ndarray, np.ndarray]:
    array = np.asarray(err, dtype=float)
    if array.ndim <= 1:
        lower = upper = _per_item(array, n, "err")
    elif array.shape == (2, n):
        lower, upper = array.copy()
    else:
        raise ValueError(f"err must have shape ({n},) or (2, {n}).")
    if np.any(lower < 0) or np.any(upper < 0):
        raise ValueError("err values must not be negative.")
    return lower, upper


def _bound_offsets(
    bounds: Any, centre: np.ndarray, n: int
) -> tuple[np.ndarray, np.ndarray]:
    array = np.asarray(bounds, dtype=float)
    if array.shape != (2, n):
        raise ValueError(f"bounds must have shape (2, {n}): (low, high).")
    lower, upper = centre - array[0], array[1] - centre
    if np.any(lower < 0) or np.any(upper < 0):
        raise ValueError("bounds must satisfy low <= centre <= high.")
    return lower, upper


def _clean_replicates(values: Any) -> list[np.ndarray]:
    cleaned = []
    for item in values:
        array = np.empty(0) if item is None else np.asarray(item, float).ravel()
        cleaned.append(array[np.isfinite(array)])
    return cleaned


def _summaries(
    replicates: list[np.ndarray],
    n: int,
    centre: Any,
    err: Any,
    bounds: Any,
    errorbars: bool,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if err is not None and bounds is not None:
        raise ValueError("Pass either err or bounds, not both.")
    if centre is None:
        centres = np.array([v.mean() if v.size else np.nan for v in replicates])
    else:
        centres = _per_item(centre, n, "centre")
    if not errorbars:
        lower = upper = np.full(n, np.nan)
    elif bounds is not None:
        lower, upper = _bound_offsets(bounds, centres, n)
    elif err is not None:
        lower, upper = _error_offsets(err, n)
    else:
        lower = upper = np.array(
            [v.std(ddof=1) if v.size > 1 else np.nan for v in replicates]
        )
    return centres, lower, upper


def _xy(position: Any, value: Any, horizontal: bool) -> tuple[Any, Any]:
    return (value, position) if horizontal else (position, value)


def _jitter_offsets(n: int, jitter: float) -> np.ndarray:
    if n < 2:
        return np.zeros(n)
    return np.linspace(-jitter / 2, jitter / 2, n)


def _saved_limits(ax: Axes, autoscale: bool) -> tuple[Any, Any] | None:
    return None if autoscale else (ax.get_xlim(), ax.get_ylim())


def _apply_limits(
    ax: Axes, saved: tuple[Any, Any] | None, xlim: Any, ylim: Any
) -> None:
    if saved is None:
        # add_patch/add_line update dataLim but, unlike ax.bar/ax.plot, never
        # request an autoscale, so the view would stay at its old limits.
        ax.autoscale_view()
    else:
        ax.set_xlim(saved[0])
        ax.set_ylim(saved[1])
    if xlim is not None:
        ax.set_xlim(xlim)
    if ylim is not None:
        ax.set_ylim(ylim)


def _set_category_labels(
    ax: Axes,
    positions: Sequence[float],
    labels: Sequence[str] | None,
    horizontal: bool,
    font_size: float | None,
) -> list[Text]:
    if labels is None:
        return []
    labels = list(labels)
    if len(labels) != len(positions):
        raise ValueError("labels must have one entry per position.")
    axis = ax.yaxis if horizontal else ax.xaxis
    kwargs = {} if font_size is None else {"fontsize": font_size}
    axis.set_ticks(list(positions), labels, **kwargs)
    return list(axis.get_majorticklabels())


class _Default:
    """Sentinel for "use the default of the chosen ``style``"."""

    _instance: _Default | None = None

    def __new__(cls) -> _Default:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "DEFAULT"

    def __reduce__(self) -> str:
        return "DEFAULT"


DEFAULT: Any = _Default()
"""Default for style arguments: the value comes from the chosen ``style``.

Passing ``None`` keeps its 0.2 meaning (for example ``edge_color=None`` is the
category colour), so ``None`` and ``DEFAULT`` are different.
"""

_AUTO = "auto"


def _axis_width() -> float:
    return float(mpl.rcParams["axes.linewidth"])


# Defaults per style. Callables are evaluated at call time, so "prism" sizes
# follow the axes line width of the rcParams in effect (2.13 pt under
# prism_style(base_size=14)). Sources are listed in docs/prism-defaults.md.
_CATEGORY_DEFAULTS: dict[str, dict[str, Any]] = {
    "prism": {
        "tint": 1.0,
        "edge_color": "black",
        "edge_width": _axis_width,
        "err_color": "black",
        "err_width": _axis_width,
        "capsize": None,
        "cap_width": _AUTO,
        "err_direction": "both",
        "point_size": PRISM_POINT_SIZE,
        "point_color": "black",
        "point_edgecolor": _AUTO,
        "point_edgewidth": _AUTO,
        "point_marker": "default",
        "mean_line_width": _axis_width,
    },
    "classic": {
        "tint": 0.3,
        "edge_color": None,
        "edge_width": 1.3,
        "err_color": ERROR_COLOR,
        "err_width": 1.0,
        "capsize": 3.0,
        "cap_width": None,
        "err_direction": "both",
        "point_color": None,
        "point_edgecolor": "black",
        "point_edgewidth": 0.5,
        "point_marker": "o",
        "mean_line_width": 2.0,
    },
}

_XY_DEFAULTS: dict[str, dict[str, Any]] = {
    "prism": {
        "markers": "default",
        "marker_size": PRISM_MARKER_SIZE,
        "marker_edgecolor": _AUTO,
        "line_width": _axis_width,
        "err_width": _axis_width,
        "capsize": _AUTO,
    },
    "classic": {
        "markers": XY_MARKERS,
        "marker_size": 6.0,
        "marker_edgecolor": None,
        "line_width": 1.5,
        "err_width": 1.0,
        "capsize": 3.0,
    },
}


def _check_style(style: str) -> None:
    if style not in STYLES:
        raise ValueError("style must be 'prism' or 'classic'.")


def _resolve_defaults(
    table: dict[str, dict[str, Any]], style: str, **given: Any
) -> dict[str, Any]:
    _check_style(style)
    resolved = {}
    for name, value in given.items():
        if value is DEFAULT:
            value = table[style][name]
            value = value() if callable(value) else value
        resolved[name] = value
    return resolved


def _as_shape(marker: Any) -> Shape:
    if isinstance(marker, Shape):
        return marker
    line = marker in _LINE_MARKERS or (
        isinstance(marker, tuple) and len(marker) >= 2 and marker[1] == 2
    )
    return Shape(str(marker), -1, marker, line=line)


def _resolve_shapes(spec: Any, n: int) -> list[Shape]:
    """Markers per item: a shape palette name, one marker, or a sequence."""
    if isinstance(spec, str) and spec in SHAPE_PALETTES:
        cycle = list(SHAPE_PALETTES[spec])
    elif isinstance(spec, (str, Shape)) or (
        isinstance(spec, tuple) and spec and isinstance(spec[0], int)
    ):
        cycle = [_as_shape(spec)]
    else:
        cycle = [_as_shape(marker) for marker in spec] or [_as_shape("none")]
    return [cycle[i % len(cycle)] for i in range(n)]


def _marker_colors(
    shape: Shape, face: Any, edge: Any, edge_width: Any
) -> tuple[Any, Any, float]:
    """Face, edge and edge width for one marker, filling in ``"auto"`` values.

    ggprism's solid shapes (pch 15-18) have no border, the outlined shapes
    (pch 21-25) a black border, and line shapes are drawn in the colour, both
    with ggplot2's default stroke.
    """
    if edge == _AUTO:
        edge = "black" if shape.outlined else face
    if edge_width == _AUTO:
        edge_width = GGPLOT_STROKE_PT if (shape.outlined or shape.line) else 0.0
    return face, edge, float(edge_width)


@dataclass(frozen=True)
class _CategoryStyle:
    horizontal: bool
    shape: str
    tint: float
    edge_color: Any
    edge_width: float
    err_color: Any
    err_width: float
    capsize: float | None
    cap_width: float | None
    err_direction: str
    point_size: float
    point_color: Any
    point_edgecolor: Any
    point_edgewidth: Any
    dot_size: float
    mean_line_width: float
    baseline: float
    zorder: float

    def __post_init__(self) -> None:
        if self.shape not in _SHAPES:
            raise ValueError("shape must be 'bar', 'dot', or 'line'.")
        if not 0 <= self.tint <= 1:
            raise ValueError("tint must be between 0 and 1.")
        if self.err_direction not in _DIRECTIONS:
            raise ValueError("err_direction must be 'both' or 'up'.")
        _check_non_negative(
            edge_width=self.edge_width,
            err_width=self.err_width,
            capsize=self.capsize or 0,
            cap_width=self.cap_width or 0,
            point_size=self.point_size,
            point_edgewidth=0
            if self.point_edgewidth == _AUTO
            else self.point_edgewidth,
            dot_size=self.dot_size,
            mean_line_width=self.mean_line_width,
        )


def _category_style(
    style: str,
    *,
    horizontal: bool,
    shape: str,
    width: float,
    dot_size: float,
    baseline: float,
    zorder: float,
    **given: Any,
) -> tuple[_CategoryStyle, Any]:
    values = _resolve_defaults(_CATEGORY_DEFAULTS, style, **given)
    marker = values.pop("point_marker")
    if values["cap_width"] == _AUTO:
        # ggprism's examples: geom_errorbar(width = 0.3) on 0.9-wide columns,
        # so caps are a third of the column width -- unless capsize (points)
        # was asked for explicitly.
        values["cap_width"] = None if values["capsize"] is not None else width / 3
    category_style = _CategoryStyle(
        horizontal=horizontal,
        shape=shape,
        dot_size=dot_size,
        baseline=baseline,
        zorder=zorder,
        **values,
    )
    return category_style, marker


def _draw_errorbar(
    ax: Axes,
    position: float,
    centre: float,
    lower: float,
    upper: float,
    *,
    horizontal: bool,
    color: Any,
    line_width: float,
    capsize: float | None,
    zorder: float,
    cap_width: float | None = None,
) -> ErrorBarArtists | None:
    if not np.isfinite(centre) or not (np.isfinite(lower) or np.isfinite(upper)):
        return None
    lower = float(lower) if np.isfinite(lower) else 0.0
    upper = float(upper) if np.isfinite(upper) else 0.0
    if lower == 0 and upper == 0:
        return None
    x, y = _xy([position, position], [centre - lower, centre + upper], horizontal)
    line = Line2D(
        x,
        y,
        color=color,
        linewidth=line_width,
        solid_capstyle="butt",
        zorder=zorder,
    )
    ax.add_line(line)
    caps: list[Line2D | None] = []
    for end, size in ((centre - lower, lower), (centre + upper, upper)):
        if size == 0 or not (cap_width or capsize):
            caps.append(None)
            continue
        if cap_width:
            # A cap of fixed width in data units, centred on the whisker.
            ends = [position - cap_width / 2, position + cap_width / 2]
            cap_x, cap_y = _xy(ends, [end, end], horizontal)
            cap = Line2D(
                cap_x,
                cap_y,
                color=color,
                linewidth=line_width,
                solid_capstyle="butt",
                zorder=zorder,
            )
        else:
            cap_x, cap_y = _xy([position], [end], horizontal)
            cap = Line2D(
                cap_x,
                cap_y,
                linestyle="none",
                marker="|" if horizontal else "_",
                markersize=2 * capsize,
                markeredgewidth=line_width,
                color=color,
                zorder=zorder,
            )
        ax.add_line(cap)
        caps.append(cap)
    return ErrorBarArtists(line, (caps[0], caps[1]))


def _draw_summary(
    ax: Axes,
    position: float,
    centre: float,
    width: float,
    color: Any,
    marker: Shape,
    style: _CategoryStyle,
) -> Rectangle | Line2D:
    if style.shape == "bar":
        length = centre - style.baseline
        if style.horizontal:
            corner, size = (style.baseline, position - width / 2), (length, width)
        else:
            corner, size = (position - width / 2, style.baseline), (width, length)
        bar = Rectangle(
            corner,
            *size,
            facecolor=tint_color(color, style.tint),
            edgecolor=color if style.edge_color is None else style.edge_color,
            linewidth=style.edge_width,
            zorder=style.zorder,
        )
        sticky = bar.sticky_edges.x if style.horizontal else bar.sticky_edges.y
        sticky.append(style.baseline)
        ax.add_patch(bar)
        return bar
    if style.shape == "dot":
        x, y = _xy([position], [centre], style.horizontal)
        face, edge, edge_width = _marker_colors(
            marker, color, style.point_edgecolor, style.point_edgewidth
        )
        mark = Line2D(
            x,
            y,
            linestyle="none",
            marker=marker.marker,
            markersize=style.dot_size,
            markerfacecolor=face,
            markeredgecolor=edge,
            markeredgewidth=edge_width,
            zorder=style.zorder + 3,
        )
    else:
        ends = [position - width / 2, position + width / 2]
        x, y = _xy(ends, [centre, centre], style.horizontal)
        mark = Line2D(
            x,
            y,
            color=color,
            linewidth=style.mean_line_width,
            solid_capstyle="butt",
            zorder=style.zorder + 3,
        )
    ax.add_line(mark)
    return mark


def _draw_points(
    ax: Axes,
    position: float,
    values: np.ndarray,
    jitter: float,
    color: Any,
    marker: Shape,
    style: _CategoryStyle,
) -> PathCollection | None:
    if values.size == 0:
        return None
    offsets = position + _jitter_offsets(values.size, jitter)
    x, y = _xy(offsets, values, style.horizontal)
    face = color if style.point_color is None else style.point_color
    face, edge, edge_width = _marker_colors(
        marker, face, style.point_edgecolor, style.point_edgewidth
    )
    colors = {"facecolors": face}
    if not marker.line:
        # Line-only markers are drawn in their face colour; Matplotlib warns
        # when they also get an edge colour.
        colors["edgecolors"] = edge
    return ax.scatter(
        x,
        y,
        s=style.point_size,
        marker=marker.marker,
        linewidths=edge_width,
        zorder=style.zorder + 1,
        **colors,
    )


def _draw_categories(
    ax: Axes,
    replicates: list[np.ndarray],
    positions: np.ndarray,
    centres: np.ndarray,
    lower: np.ndarray,
    upper: np.ndarray,
    colors: list[Any],
    markers: list[Shape],
    *,
    width: float,
    jitter: float,
    points: bool,
    style: _CategoryStyle,
) -> tuple[list[Any], list[ErrorBarArtists | None], list[PathCollection | None]]:
    bars: list[Any] = []
    errorbars: list[ErrorBarArtists | None] = []
    point_sets: list[PathCollection | None] = []
    for i, position in enumerate(positions):
        centre = centres[i]
        has_centre = bool(np.isfinite(centre))
        bars.append(
            _draw_summary(ax, position, centre, width, colors[i], markers[i], style)
            if has_centre
            else None
        )
        low, high = lower[i], upper[i]
        if style.err_direction == "up" and has_centre:
            # Only the half pointing away from the baseline, as in Prism's
            # "Above" direction for bars.
            if centre >= style.baseline:
                low = 0.0
            else:
                high = 0.0
        errorbars.append(
            _draw_errorbar(
                ax,
                position,
                centre,
                low,
                high,
                horizontal=style.horizontal,
                color=style.err_color,
                line_width=style.err_width,
                capsize=style.capsize,
                cap_width=style.cap_width,
                zorder=style.zorder + 2,
            )
        )
        point_sets.append(
            _draw_points(
                ax, position, replicates[i], jitter, colors[i], markers[i], style
            )
            if points
            else None
        )
    return bars, errorbars, point_sets


def _positions(positions: Any, n: int, name: str) -> np.ndarray:
    if positions is None:
        return np.arange(n, dtype=float)
    array = np.asarray(positions, dtype=float)
    if array.shape != (n,):
        raise ValueError(f"{name} must have one value per item ({n}).")
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must be finite.")
    return array


def bar_dots(
    ax: Axes,
    values: Sequence[Any] | None,
    *,
    positions: Sequence[float] | None = None,
    orientation: str = "vertical",
    centre: Sequence[float | None] | None = None,
    err: Any = None,
    bounds: Any = None,
    errorbars: bool = True,
    colors: Any = None,
    width: float = 0.6,
    shape: str = "bar",
    points: bool = True,
    jitter: float = 0.25,
    tint: float = DEFAULT,
    edge_color: Any = DEFAULT,
    edge_width: float = DEFAULT,
    err_color: Any = DEFAULT,
    err_width: float = DEFAULT,
    capsize: float | None = DEFAULT,
    cap_width: float | None = DEFAULT,
    err_direction: str = DEFAULT,
    point_size: float = DEFAULT,
    point_color: Any = DEFAULT,
    point_edgecolor: Any = DEFAULT,
    point_edgewidth: float = DEFAULT,
    point_marker: Any = DEFAULT,
    dot_size: float = 8.0,
    mean_line_width: float = DEFAULT,
    baseline: float = 0.0,
    zorder: float = 2.0,
    labels: Sequence[str] | None = None,
    font_size: float | None = None,
    autoscale: bool = True,
    xlim: tuple[float, float] | None = None,
    ylim: tuple[float, float] | None = None,
    style: str = "prism",
) -> BarDotsArtists:
    """Draw one column per category with its replicate points on top.

    With ``style="prism"`` (default) this is Prism's column bar graph with the
    points shown: solid columns in the category colour with a black outline,
    black mean ± SD error bars with caps a third of the column wide, and black
    points in a different ggprism shape per column (circle, square, triangle,
    diamond, ...). Line widths follow the axis line width in effect
    (``rcParams["axes.linewidth"]``). ``style="classic"`` gives the PyPrism 0.2
    look (pale tinted columns, coloured outlines, dark grey error bars).

    Parameters
    ----------
    values
        One 1-D array of replicates per category. ``None``, empty or all-NaN
        entries draw no points; NaN replicates are dropped. May be ``None`` when
        ``centre`` is given.
    positions
        Category positions in data units (default ``0 .. n-1``).
    orientation
        ``"vertical"`` (columns grow up) or ``"horizontal"`` (bars grow right,
        categories along y).
    centre, err, bounds
        The plotted centre and error per category. ``centre`` defaults to the
        mean of ``values`` and the error to their standard deviation. ``err`` is
        symmetric distances or a ``(lower, upper)`` pair with shape ``(2, n)``;
        ``bounds`` is the absolute ``(low, high)`` ends instead. A NaN centre
        draws no column or error bar; a NaN error draws no error bar.
    errorbars, err_direction
        ``errorbars=False`` draws no error bars. ``err_direction="up"`` keeps only
        the half pointing away from ``baseline`` (Prism's "Above").
    colors
        One colour, or a sequence cycled over categories (default: the
        ``axes.prop_cycle`` colours in effect).
    width, jitter
        Column width and total point-spread width, in data units. Points are
        spread evenly in input order, so redraws are identical.
    shape
        ``"bar"`` (column), ``"dot"`` (centre as a marker) or ``"line"`` (a short
        centre line across ``width``, perpendicular to the value axis).
    tint
        How much of the colour the column fill keeps after mixing with white
        (prism 1.0, classic 0.3).
    capsize, cap_width
        Cap length: ``cap_width`` in data units (prism default ``width / 3``) or
        ``capsize`` as half the length in points, as in Matplotlib (classic 3).
    point_marker
        A marker, a sequence of markers cycled over categories, or a ggprism
        shape palette name (``"default"``, ``"filled"``, ``"complete"``).
    point_edgecolor, point_edgewidth
        ``"auto"`` (prism default) gives the outlined shapes of the ``"filled"``
        palette a black edge and solid shapes none.
    zorder
        Base z-order: columns at ``zorder``, points at ``+1``, error bars at
        ``+2`` and centre dots or lines at ``+3``.
    labels, font_size
        Optional category tick labels placed at ``positions``, and their size
        (default: the rcParams in effect).
    autoscale, xlim, ylim
        ``autoscale=False`` keeps the current axis limits fixed. ``xlim`` and
        ``ylim`` set the limits explicitly after drawing.

    Arguments left at ``DEFAULT`` take the value of ``style``; see
    ``docs/prism-defaults.md``. Capsize, marker and dot sizes are in points;
    ``point_size`` is in points squared, as in :meth:`~matplotlib.axes.Axes.scatter`.
    """
    horizontal = _check_orientation(orientation)
    if width <= 0:
        raise ValueError("width must be greater than zero.")
    _check_non_negative(jitter=jitter)
    category_style, marker = _category_style(
        style,
        horizontal=horizontal,
        shape=shape,
        width=width,
        dot_size=dot_size,
        baseline=baseline,
        zorder=zorder,
        tint=tint,
        edge_color=edge_color,
        edge_width=edge_width,
        err_color=err_color,
        err_width=err_width,
        capsize=capsize,
        cap_width=cap_width,
        err_direction=err_direction,
        point_size=_classic_size(point_size, style, 18.0),
        point_color=point_color,
        point_edgecolor=point_edgecolor,
        point_edgewidth=point_edgewidth,
        point_marker=point_marker,
        mean_line_width=mean_line_width,
    )
    if values is None:
        if centre is None:
            raise ValueError("Pass values, centre, or both.")
        n = len(centre)
        replicates = [np.empty(0)] * n
    else:
        replicates = _clean_replicates(values)
        n = len(replicates)
    category_positions = _positions(positions, n, "positions")
    centres, lower, upper = _summaries(replicates, n, centre, err, bounds, errorbars)

    saved = _saved_limits(ax, autoscale)
    bars, errs, point_sets = _draw_categories(
        ax,
        replicates,
        category_positions,
        centres,
        lower,
        upper,
        _resolve_colors(colors, n),
        _resolve_shapes(marker, n),
        width=width,
        jitter=jitter,
        points=points,
        style=category_style,
    )
    _apply_limits(ax, saved, xlim, ylim)
    texts = _set_category_labels(ax, category_positions, labels, horizontal, font_size)
    return BarDotsArtists(bars, errs, point_sets, texts)


def _classic_size(value: Any, style: str, classic: float) -> Any:
    """Point sizes differ between functions in the classic style only."""
    return classic if value is DEFAULT and style == "classic" else value


def _grid(value: Any, clusters: int, series: int, name: str) -> list[list[Any]]:
    if value is None:
        return [[None] * series for _ in range(clusters)]
    if len(value) != clusters:
        raise ValueError(f"{name} must have one entry per cluster ({clusters}).")
    grid = []
    for row in value:
        row = [] if row is None else list(row)
        if len(row) > series:
            raise ValueError(f"{name} has more series than data.")
        grid.append(row + [None] * (series - len(row)))
    return grid


def _grid_pairs(value: Any, clusters: int, series: int, name: str) -> Any:
    """Convert nested per-cell values into one (2, n_clusters) array per series."""
    if value is None:
        return [None] * series
    grid = _grid(value, clusters, series, name)
    per_series = []
    for s in range(series):
        pairs = []
        for row in grid:
            cell = row[s]
            if cell is None:
                pairs.append((np.nan, np.nan))
            elif np.ndim(cell) == 0:
                pairs.append((cell, cell))
            elif len(cell) == 2:
                pairs.append(tuple(np.nan if c is None else c for c in cell))
            else:
                raise ValueError(f"Each {name} cell must be a number or a pair.")
        per_series.append(np.asarray(pairs, dtype=float).T)
    return per_series


def grouped_bars(
    ax: Axes,
    data: Sequence[Sequence[Any] | None],
    *,
    cluster_positions: Sequence[float] | None = None,
    series_width: float = 0.16,
    bar_width: float | None = None,
    orientation: str = "vertical",
    centre: Any = None,
    err: Any = None,
    bounds: Any = None,
    errorbars: bool = True,
    colors: Any = None,
    shape: str = "bar",
    points: bool = True,
    jitter: float | None = None,
    tint: float = DEFAULT,
    edge_color: Any = DEFAULT,
    edge_width: float = DEFAULT,
    err_color: Any = DEFAULT,
    err_width: float = DEFAULT,
    capsize: float | None = DEFAULT,
    cap_width: float | None = DEFAULT,
    err_direction: str = DEFAULT,
    point_size: float = DEFAULT,
    point_color: Any = DEFAULT,
    point_edgecolor: Any = DEFAULT,
    point_edgewidth: float = DEFAULT,
    point_marker: Any = DEFAULT,
    dot_size: float = 7.0,
    mean_line_width: float = DEFAULT,
    baseline: float = 0.0,
    zorder: float = 2.0,
    cluster_labels: Sequence[str] | None = None,
    series_labels: Sequence[str] | None = None,
    legend: bool = False,
    font_size: float | None = None,
    autoscale: bool = True,
    xlim: tuple[float, float] | None = None,
    ylim: tuple[float, float] | None = None,
    style: str = "prism",
) -> GroupedBarsArtists:
    """Draw clusters of side-by-side columns, one column per series.

    ``data[cluster][series]`` is a 1-D array of replicates, or ``None`` to leave
    that slot empty. Clusters may list fewer series than others; missing slots
    are empty. ``centre``, ``err`` and ``bounds`` use the same nesting: each
    ``err`` cell is a symmetric distance or a ``(lower, upper)`` pair, and each
    ``bounds`` cell is an absolute ``(low, high)`` pair.

    Series ``s`` is centred at ``cluster_position + (s - (n_series - 1) / 2) *
    series_width``. Columns are ``bar_width`` wide (default ``series_width``) and
    points spread over ``jitter`` (default 40 % of the column width). ``colors``
    and point shapes (ggprism's ``"default"`` shape palette) are per series.
    Other style parameters match :func:`bar_dots`.

    ``legend_handles`` are proxy artists matching each series' style, labelled
    from ``series_labels``; ``legend=True`` also adds an axes legend with them
    (plain legend text in the prism style, as ggprism's ``legend.text``).
    """
    horizontal = _check_orientation(orientation)
    if series_width <= 0:
        raise ValueError("series_width must be greater than zero.")
    width = series_width if bar_width is None else bar_width
    if width <= 0:
        raise ValueError("bar_width must be greater than zero.")
    spread = 0.4 * width if jitter is None else jitter
    _check_non_negative(jitter=spread)
    category_style, marker = _category_style(
        style,
        horizontal=horizontal,
        shape=shape,
        width=width,
        dot_size=dot_size,
        baseline=baseline,
        zorder=zorder,
        tint=tint,
        edge_color=edge_color,
        edge_width=edge_width,
        err_color=err_color,
        err_width=err_width,
        capsize=capsize,
        cap_width=cap_width,
        err_direction=err_direction,
        point_size=_classic_size(point_size, style, 14.0),
        point_color=point_color,
        point_edgecolor=point_edgecolor,
        point_edgewidth=point_edgewidth,
        point_marker=point_marker,
        mean_line_width=mean_line_width,
    )
    n_clusters = len(data)
    n_series = max((len(row) for row in data if row is not None), default=0)
    if series_labels is not None:
        series_labels = list(series_labels)
        n_series = max(n_series, len(series_labels))
    cells = _grid(data, n_clusters, n_series, "data")
    centres = _grid(centre, n_clusters, n_series, "centre")
    errs = _grid_pairs(err, n_clusters, n_series, "err")
    bound_pairs = _grid_pairs(bounds, n_clusters, n_series, "bounds")
    clusters = _positions(cluster_positions, n_clusters, "cluster_positions")
    series_colors = _resolve_colors(colors, n_series)
    series_markers = _resolve_shapes(marker, n_series)

    saved = _saved_limits(ax, autoscale)
    result = GroupedBarsArtists({}, {}, {}, [], [])
    for s in range(n_series):
        replicates = _clean_replicates(row[s] for row in cells)
        centre_s = None if centre is None else [row[s] for row in centres]
        series_centres, lower, upper = _summaries(
            replicates, n_clusters, centre_s, errs[s], bound_pairs[s], errorbars
        )
        bars, errorbar_set, point_sets = _draw_categories(
            ax,
            replicates,
            clusters + (s - (n_series - 1) / 2) * series_width,
            series_centres,
            lower,
            upper,
            [series_colors[s]] * n_clusters,
            [series_markers[s]] * n_clusters,
            width=width,
            jitter=spread,
            points=points,
            style=category_style,
        )
        for c in range(n_clusters):
            for target, artist in (
                (result.bars, bars[c]),
                (result.errorbars, errorbar_set[c]),
                (result.points, point_sets[c]),
            ):
                if artist is not None:
                    target[(c, s)] = artist
        label = series_labels[s] if series_labels else f"Series {s + 1}"
        result.legend_handles.append(
            _legend_handle(series_colors[s], series_markers[s], label, category_style)
        )
    _apply_limits(ax, saved, xlim, ylim)
    result.labels = _set_category_labels(
        ax, clusters, cluster_labels, horizontal, font_size
    )
    if legend:
        kwargs = {"prop": {"weight": "normal"}} if style == "prism" else {}
        result.legend = ax.legend(handles=result.legend_handles, **kwargs)
    return result


def _legend_handle(
    color: Any, marker: Shape, label: str, style: _CategoryStyle
) -> Patch | Line2D:
    if style.shape == "bar":
        return Patch(
            facecolor=tint_color(color, style.tint),
            edgecolor=color if style.edge_color is None else style.edge_color,
            linewidth=style.edge_width,
            label=label,
        )
    if style.shape == "dot":
        face, edge, edge_width = _marker_colors(
            marker, color, style.point_edgecolor, style.point_edgewidth
        )
        return Line2D(
            [],
            [],
            linestyle="none",
            marker=marker.marker,
            markersize=style.dot_size,
            markerfacecolor=face,
            markeredgecolor=edge,
            markeredgewidth=edge_width,
            label=label,
        )
    return Line2D([], [], color=color, linewidth=style.mean_line_width, label=label)


def _resolve_markers(markers: Any, n: int) -> list[Shape]:
    if markers is True:
        markers = "default"
    if markers is False or markers is None:
        return [_as_shape("none")] * n
    return _resolve_shapes(markers, n)


def xy_lines(
    ax: Axes,
    x: Sequence[float],
    series: Mapping[str, Any],
    *,
    err: Mapping[str, Any] | None = None,
    colors: Any = None,
    markers: Any = True,
    marker_size: float = DEFAULT,
    marker_edgecolor: Any = DEFAULT,
    line_width: float = DEFAULT,
    err_color: Any = None,
    err_width: float = DEFAULT,
    capsize: float = DEFAULT,
    points: Mapping[str, Any] | None = None,
    jitter: float = 0.0,
    point_size: float = 12.0,
    point_tint: float = 0.5,
    point_edgecolor: Any = "none",
    point_edgewidth: float = 0.5,
    logx: bool = False,
    zorder: float = 2.0,
    autoscale: bool = True,
    xlim: tuple[float, float] | None = None,
    ylim: tuple[float, float] | None = None,
    style: str = "prism",
) -> XYLinesArtists:
    """Draw one line with markers and error bars per series against shared x.

    With ``style="prism"`` (default) each series gets the next shape of ggprism's
    ``"default"`` shape palette (circle, square, triangle, diamond, ...), filled
    in the series colour, a line in the series colour at the axis line width,
    and error bars in the same colour and width with caps as wide as the marker.
    ``style="classic"`` gives the PyPrism 0.2 look.

    Parameters
    ----------
    x
        The shared x values.
    series
        Maps a series name to its y values, or to a ``(y, low, high)`` tuple of
        arrays giving absolute error-bar ends. NaN y values break the line.
    err
        Optional map from series name to error distances for series given as
        plain y: symmetric, or a ``(lower, upper)`` pair with shape ``(2, n)``.
    markers
        ``True`` uses the style's markers (prism: ggprism's ``"default"`` shape
        palette; classic: circle, square, triangle, diamond, down-triangle);
        ``False`` draws none; a shape palette name (``"default"``, ``"filled"``,
        ``"complete"``), a marker or a sequence picks them.
    marker_size, marker_edgecolor
        Marker size in points (prism 7, ggplot2 ``size = 3``). The edge is
        ``"auto"`` in the prism style: black for the outlined shapes of the
        ``"filled"`` palette, the series colour otherwise.
    err_color
        Error-bar colour (default: the series colour).
    capsize
        Half the cap length in points (prism: half the marker size).
    points
        Optional map from series name to replicates per x value (a ragged
        sequence or a 2-D ``(n_x, n_replicates)`` array), drawn behind the lines
        as points filled with the series colour mixed with white
        (``point_tint``). ``jitter`` spreads each x's points evenly over that
        width; on a log axis it is in decades.
    logx
        Put the x axis on a log scale.
    zorder
        Base z-order: points at ``zorder``, error bars at ``+1``, lines at ``+2``.
    """
    if markers is True:
        markers = DEFAULT
    values = _resolve_defaults(
        _XY_DEFAULTS,
        style,
        markers=markers,
        marker_size=marker_size,
        marker_edgecolor=marker_edgecolor,
        line_width=line_width,
        err_width=err_width,
        capsize=capsize,
    )
    if values["capsize"] == _AUTO:
        values["capsize"] = values["marker_size"] / 2
    if not 0 <= point_tint <= 1:
        raise ValueError("point_tint must be between 0 and 1.")
    _check_non_negative(
        marker_size=values["marker_size"],
        line_width=values["line_width"],
        err_width=values["err_width"],
        capsize=values["capsize"],
        jitter=jitter,
        point_size=point_size,
        point_edgewidth=point_edgewidth,
    )
    x_values = np.asarray(x, dtype=float)
    if x_values.ndim != 1:
        raise ValueError("x must be one-dimensional.")
    n = x_values.size
    err = {} if err is None else err
    points = {} if points is None else points
    unknown = (set(err) | set(points)) - set(series)
    if unknown:
        raise ValueError(f"err/points name unknown series: {sorted(unknown)}.")
    names = list(series)
    colors_by_series = _resolve_colors(colors, len(names))
    markers_by_series = _resolve_markers(values["markers"], len(names))

    if logx:
        ax.set_xscale("log")
    saved = _saved_limits(ax, autoscale)
    result = XYLinesArtists({})
    for index, name in enumerate(names):
        value = series[name]
        color = colors_by_series[index]
        marker = markers_by_series[index]
        if isinstance(value, tuple) and len(value) == 3 and np.ndim(value[0]) == 1:
            y = _per_item(value[0], n, f"series {name!r}")
            if name in err:
                raise ValueError(f"Series {name!r} has both bounds and err.")
            lower, upper = _bound_offsets(value[1:], y, n)
        else:
            y = _per_item(value, n, f"series {name!r}")
            lower, upper = (
                _error_offsets(err[name], n) if name in err else (y * np.nan,) * 2
            )
        point_set = None
        if name in points:
            point_set = _draw_xy_points(
                ax,
                x_values,
                points[name],
                logx=logx,
                jitter=jitter,
                size=point_size,
                marker=marker.marker if style == "prism" else "o",
                face=tint_color(color, point_tint),
                edge=point_edgecolor,
                edge_width=point_edgewidth,
                zorder=zorder,
            )
        errorbar_set = [
            _draw_errorbar(
                ax,
                x_values[i],
                y[i],
                lower[i],
                upper[i],
                horizontal=False,
                color=color if err_color is None else err_color,
                line_width=values["err_width"],
                capsize=values["capsize"],
                zorder=zorder + 1,
            )
            for i in range(n)
        ]
        edge = values["marker_edgecolor"]
        if edge == _AUTO:
            edge = "black" if marker.outlined else color
        line = Line2D(
            x_values,
            y,
            color=color,
            linewidth=values["line_width"],
            marker=marker.marker,
            markersize=values["marker_size"],
            markerfacecolor=color,
            markeredgecolor=color if edge is None else edge,
            label=name,
            zorder=zorder + 2,
        )
        if style == "prism":
            line.set_markeredgewidth(
                GGPLOT_STROKE_PT if (marker.outlined or marker.line) else 0.0
            )
        ax.add_line(line)
        result.series[name] = XYSeriesArtists(line, errorbar_set, point_set)
    _apply_limits(ax, saved, xlim, ylim)
    return result


def _draw_xy_points(
    ax: Axes,
    x_values: np.ndarray,
    replicates: Any,
    *,
    logx: bool,
    jitter: float,
    size: float,
    marker: Any,
    face: Any,
    edge: Any,
    edge_width: float,
    zorder: float,
) -> PathCollection | None:
    replicate_sets = _clean_replicates(replicates)
    if len(replicate_sets) != x_values.size:
        raise ValueError("points must have one replicate set per x value.")
    xs, ys = [], []
    for x_value, values in zip(x_values, replicate_sets, strict=True):
        offsets = _jitter_offsets(values.size, jitter)
        xs.append(x_value * 10**offsets if logx else x_value + offsets)
        ys.append(values)
    if not any(values.size for values in ys):
        return None
    return ax.scatter(
        np.concatenate(xs),
        np.concatenate(ys),
        s=size,
        marker=marker,
        facecolors=face,
        edgecolors=edge,
        linewidths=edge_width,
        zorder=zorder,
    )


def _relative_luminance(color: Any) -> float:
    rgb = np.asarray(to_rgba(color)[:3])
    rgb = np.where(rgb <= 0.03928, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    return float(rgb @ [0.2126, 0.7152, 0.0722])


def _heatmap_norm(
    data: np.ndarray, center: float | None, vmin: float | None, vmax: float | None
) -> Normalize:
    finite = data[np.isfinite(data)]
    low = vmin if vmin is not None else (finite.min() if finite.size else 0.0)
    high = vmax if vmax is not None else (finite.max() if finite.size else 1.0)
    if center is None:
        if low == high:
            low, high = low - 0.5, high + 0.5
        return Normalize(low, high)
    if vmin is None and vmax is None:
        reach = max(abs(low - center), abs(high - center)) or 1.0
        low, high = center - reach, center + reach
    elif vmin is None:
        low = center - abs(high - center)
    elif vmax is None:
        high = center + abs(center - low)
    if low < center < high:
        return TwoSlopeNorm(center, low, high)
    return Normalize(low, high)


def heatmap(
    ax: Axes,
    matrix: Any,
    *,
    row_labels: Sequence[str] | None = None,
    col_labels: Sequence[str] | None = None,
    cmap: Any = "RdBu_r",
    center: float | None = 0.0,
    vmin: float | None = None,
    vmax: float | None = None,
    annotations: Any = None,
    fmt: str = "{:.2g}",
    text_colors: tuple[Any, Any] = ("black", "white"),
    nan_color: Any = "#D9D9D9",
    nan_label: str = "n/a",
    cell_edge_color: Any = "white",
    cell_edge_width: float = 0.0,
    cbar: bool = True,
    cbar_ax: Axes | None = None,
    cbar_label: str = "",
    cbar_pad: float = 0.03,
    cbar_width: float = 0.05,
    font_size: float | None = None,
    label_font_size: float | None = None,
    col_label_rotation: float = 0.0,
    frame: bool = False,
) -> HeatmapArtists:
    """Draw a matrix as coloured cells with optional annotations and colour bar.

    Cell ``(row, col)`` is centred at ``x=col, y=row`` with row 0 at the top; the
    axes limits are set to the cell grid. Cells are vector quads, so SVG and PDF
    output stays sharp.

    Parameters
    ----------
    center, vmin, vmax
        With ``center`` set, missing limits are chosen symmetric about it and
        the colormap midpoint sits at ``center``. ``center=None`` scales from
        ``vmin``/``vmax`` (default: the data range).
    annotations
        ``None`` for no cell text, ``True`` to print values with ``fmt``, or a
        matrix of strings (for example significance stars). Text is dark or
        light depending on the cell colour; ``None``/empty strings draw nothing.
    nan_color, nan_label
        NaN cells are filled with ``nan_color`` and, when annotations are on,
        labelled ``nan_label``.
    cbar, cbar_ax
        ``cbar_ax`` puts the colour bar in an axes you placed. Without it, the
        colour bar goes in an inset axes to the right of ``ax`` (``cbar_pad``
        and ``cbar_width`` are fractions of the axes width), so ``ax`` itself
        keeps its position and size.
    font_size, label_font_size
        Size of the cell text and of the row and column labels (default: the
        rcParams in effect).
    frame
        ``False`` hides the spines and tick marks of ``ax``.
    """
    data = np.asarray(matrix, dtype=float)
    if data.ndim != 2:
        raise ValueError("matrix must be two-dimensional.")
    _check_non_negative(cell_edge_width=cell_edge_width, cbar_width=cbar_width)
    n_rows, n_cols = data.shape
    colormap = mpl.colormaps[cmap] if isinstance(cmap, str) else cmap
    colormap = colormap.with_extremes(bad=nan_color)
    norm = _heatmap_norm(data, center, vmin, vmax)
    mesh = ax.pcolormesh(
        np.arange(n_cols + 1) - 0.5,
        np.arange(n_rows + 1) - 0.5,
        np.ma.masked_invalid(data),
        cmap=colormap,
        norm=norm,
        edgecolors=cell_edge_color if cell_edge_width else "face",
        linewidth=cell_edge_width,
    )
    ax.set_xlim(-0.5, n_cols - 0.5)
    ax.set_ylim(n_rows - 0.5, -0.5)

    label_kwargs = {} if label_font_size is None else {"fontsize": label_font_size}
    col_texts: list[Text] = []
    row_texts: list[Text] = []
    if col_labels is not None:
        rotated = col_label_rotation % 360 != 0
        ax.set_xticks(
            range(n_cols),
            list(col_labels),
            rotation=col_label_rotation,
            ha="right" if rotated else "center",
            rotation_mode="anchor" if rotated else "default",
            **label_kwargs,
        )
        col_texts = list(ax.get_xticklabels())
    if row_labels is not None:
        ax.set_yticks(range(n_rows), list(row_labels), **label_kwargs)
        row_texts = list(ax.get_yticklabels())
    if not frame:
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.tick_params(which="both", length=0)

    texts = _annotate_cells(
        ax, data, annotations, fmt, colormap, norm, text_colors, nan_label, font_size
    )

    colorbar = None
    if cbar:
        if cbar_ax is None:
            cbar_ax = ax.inset_axes([1 + cbar_pad, 0, cbar_width, 1])
        colorbar = Colorbar(cbar_ax, mesh)
        if cbar_label:
            colorbar.set_label(cbar_label)
    else:
        cbar_ax = None
    return HeatmapArtists(mesh, colorbar, cbar_ax, texts, row_texts, col_texts)


def _annotate_cells(
    ax: Axes,
    data: np.ndarray,
    annotations: Any,
    fmt: str,
    colormap: Any,
    norm: Normalize,
    text_colors: tuple[Any, Any],
    nan_label: str,
    font_size: float | None,
) -> list[list[Text | None]]:
    if annotations is None or annotations is False:
        return []
    if annotations is True:
        strings = None
    else:
        strings = np.asarray(annotations, dtype=object)
        if strings.shape != data.shape:
            raise ValueError("annotations must have the same shape as matrix.")
    dark, light = text_colors
    texts: list[list[Text | None]] = []
    for row in range(data.shape[0]):
        row_texts: list[Text | None] = []
        for col in range(data.shape[1]):
            value = data[row, col]
            if not np.isfinite(value):
                label, cell_color = nan_label, colormap.get_bad()
            else:
                label = fmt.format(value) if strings is None else strings[row, col]
                cell_color = colormap(norm(value))
            if label is None or label == "":
                row_texts.append(None)
                continue
            row_texts.append(
                ax.text(
                    col,
                    row,
                    str(label),
                    ha="center",
                    va="center",
                    color=dark if _relative_luminance(cell_color) > 0.408 else light,
                    fontsize=font_size,
                )
            )
        texts.append(row_texts)
    return texts

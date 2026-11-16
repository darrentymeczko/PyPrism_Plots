"""Pin the 0.3 Prism defaults and check that style="classic" restores 0.2."""

import copy
import pickle

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.colors import to_rgba
from matplotlib.patches import Patch
from matplotlib.ticker import AutoMinorLocator, LogLocator

import pyprism_plot as ppp

LINE_PT = 72.27 / 25.4 * 72 / 96  # one ggplot2 linewidth unit in points
REPS = [np.array([1.0, 2.0, 3.0]), np.array([4.0, 5.0, 6.0, 7.0])]


def _marker_vertices(marker):
    style = mpl.markers.MarkerStyle(marker)
    return style.get_path().transformed(style.get_transform()).vertices


@pytest.fixture
def ax():
    with ppp.prism_context():
        fig, axes = plt.subplots()
        yield axes
    plt.close(fig)


# --- theme ------------------------------------------------------------------


def test_conversion_factors():
    assert ppp.GGPLOT_LINE_PT == pytest.approx(2.1339, abs=1e-4)
    assert ppp.GGPLOT_TEXT_PT == pytest.approx(2.8453, abs=1e-4)


@pytest.mark.parametrize(
    ("kwargs", "width"),
    [
        ({}, LINE_PT),
        ({"base_size": 28}, 2 * LINE_PT),
        ({"base_line_size": 0.5}, 0.5 * LINE_PT),
        ({"line_width": 3.0}, 3.0),
    ],
)
def test_prism_style_line_widths_follow_theme_prism(kwargs, width):
    style = ppp.prism_style(**kwargs)
    for key in ("axes.linewidth", "xtick.major.width", "ytick.minor.width"):
        assert style[key] == pytest.approx(width)
    assert style["lines.linewidth"] == pytest.approx(width)


def test_prism_style_sizes_follow_theme_prism():
    style = ppp.prism_style(base_size=20)
    assert style["xtick.major.size"] == pytest.approx(8.0)  # base / 2.5
    assert style["ytick.minor.size"] == pytest.approx(4.0)  # base / 5
    assert style["xtick.major.pad"] == pytest.approx(4.0)  # 0.8 * base / 4
    assert style["ytick.major.pad"] == pytest.approx(2.5)  # 0.5 * base / 4
    assert style["xtick.labelsize"] == pytest.approx(19.0)
    assert style["axes.titlesize"] == pytest.approx(24.0)
    assert style["axes.labelpad"] == pytest.approx(12.0)
    assert style["font.weight"] == "bold" and style["axes.labelweight"] == "bold"
    assert style["legend.frameon"] is False
    assert style["axes.spines.top"] is False and style["axes.grid"] is False
    assert style["xtick.direction"] == "out"
    assert style["lines.markersize"] == pytest.approx(7.0)


def test_prism_style_minor_ticks():
    style = ppp.prism_style(minor_ticks="y")
    assert style["ytick.minor.visible"] is True
    assert "xtick.minor.visible" not in style
    if "ytick.minor.ndivs" in mpl.rcParams:
        assert style["ytick.minor.ndivs"] == 2
    with pytest.raises(ValueError, match="minor_ticks"):
        ppp.prism_style(minor_ticks="z")


def test_prism_style_classic_is_the_0_2_theme():
    classic = ppp.prism_style(style="classic")
    assert classic["axes.linewidth"] == 1
    assert classic["lines.linewidth"] == 1.5
    assert "xtick.major.pad" not in classic
    assert classic["axes.prop_cycle"].by_key()["color"] == ppp.get_palette(
        "colors_classic"
    )
    assert ppp.prism_style(palette="warm", style="classic")["axes.prop_cycle"]
    with pytest.raises(ValueError, match="style"):
        ppp.prism_style(style="fancy")


def test_style_axes_prism_sizes():
    fig, ax = plt.subplots()
    ax.set_xlabel("x")
    ax.set_title("t")
    ppp.style_axes(ax, base_size=14)
    assert ax.spines["left"].get_linewidth() == pytest.approx(LINE_PT)
    tick = ax.yaxis.get_major_ticks()[0]
    assert tick.tick1line.get_markersize() == pytest.approx(5.6)
    assert tick.tick1line.get_markeredgewidth() == pytest.approx(LINE_PT)
    assert ax.get_yticklabels()[0].get_fontweight() == "bold"
    assert ax.xaxis.label.get_fontweight() == "bold"
    assert ax.xaxis.label.get_fontsize() == 14
    assert ax.title.get_fontsize() == pytest.approx(16.8)
    plt.close(fig)


def test_style_axes_classic_is_the_0_2_look():
    fig, ax = plt.subplots()
    ppp.style_axes(ax, style="classic", minor_ticks=True)
    assert ax.spines["left"].get_linewidth() == 1.0
    tick = ax.yaxis.get_major_ticks()[0]
    assert tick.tick1line.get_markersize() == pytest.approx(5.6)
    ppp.style_axes(ax, style="classic", minor_ticks=False)
    assert ax.xaxis.get_minorticklocs().size == 0
    plt.close(fig)


def test_minor_ticks_one_between_majors(ax):
    ax.set_xscale("log")
    ax.set_xlim(1e-10, 1e-3)
    ppp.style_axes(ax, minor_ticks="both")
    minor = ax.yaxis.get_minor_locator()
    assert isinstance(minor, AutoMinorLocator) and minor.ndivs == 2
    assert isinstance(ax.xaxis.get_minor_locator(), LogLocator)
    assert ax.xaxis.get_minorticklocs().size > 30  # 2..9 in every decade
    ppp.style_axes(ax, minor_ticks="x")
    assert ax.yaxis.get_minorticklocs().size == 0


def test_offset_axes_bound_to_ticks_and_apart(ax):
    ax.plot([0.3, 4.6], [0.2, 37])
    ax.set_ylim(-3, 41)
    ppp.style_axes(ax, offset="y")
    ax.figure.canvas.draw()
    left = ax.spines["left"]
    ticks = [t for t in ax.get_yticks() if -3 <= t <= 41]
    assert left.get_bounds() == pytest.approx((min(ticks), max(ticks)))
    assert ax.spines["bottom"].get_bounds() is None
    for name in ("left", "bottom"):
        assert ax.spines[name].get_position() == ("outward", pytest.approx(5.6))
    # Bounds follow later limit changes, at draw time.
    ax.set_ylim(0, 100)
    ax.figure.canvas.draw()
    assert left.get_bounds()[1] == pytest.approx(100)
    ppp.offset_axes(ax, "x", gap=3)
    ax.figure.canvas.draw()
    assert ax.spines["bottom"].get_position() == ("outward", 3)
    assert ax.spines["bottom"].get_bounds() is not None
    assert ppp.offset_axes(ax, False) is ax
    with pytest.raises(ValueError, match="which"):
        ppp.offset_axes(ax, "z")


def test_offset_axes_survive_tight_bbox_and_svg(ax, tmp_path):
    ax.plot([0, 1], [0, 1])
    ppp.style_axes(ax, offset=True)
    ax.figure.savefig(tmp_path / "offset.svg", bbox_inches="tight")
    assert (tmp_path / "offset.svg").stat().st_size > 0


# --- bar_dots / grouped_bars --------------------------------------------------


def test_bar_dots_prism_defaults(ax):
    width = mpl.rcParams["axes.linewidth"]
    assert width == pytest.approx(LINE_PT)
    result = ppp.bar_dots(ax, REPS, colors=["#0000FF", "#FF0000"], width=0.6)
    bar = result.bars[0]
    assert bar.get_facecolor() == pytest.approx(to_rgba("#0000FF"))  # solid fill
    assert bar.get_edgecolor() == pytest.approx(to_rgba("black"))
    assert bar.get_linewidth() == pytest.approx(width)
    errorbar = result.errorbars[0]
    assert errorbar.line.get_color() == "black"
    assert errorbar.line.get_linewidth() == pytest.approx(width)
    assert list(errorbar.line.get_ydata()) == pytest.approx([1.0, 3.0])  # mean ± SD
    for cap in errorbar.caps:
        assert cap.get_color() == "black"
        assert cap.get_linewidth() == pytest.approx(width)
        low, high = cap.get_xdata()
        assert high - low == pytest.approx(0.2)  # a third of the column width
        assert (low + high) / 2 == pytest.approx(0)
    points = result.points[0]
    assert points.get_facecolor()[0] == pytest.approx(to_rgba("black"))
    assert points.get_sizes()[0] == pytest.approx(ppp.plots.PRISM_POINT_SIZE)
    assert np.sqrt(ppp.plots.PRISM_POINT_SIZE) == pytest.approx(4.98, abs=0.01)
    assert points.get_linewidths()[0] == 0  # pch 16-style solid shapes


def test_bar_dots_cycles_ggprism_shapes_per_category(ax):
    values = [np.array([1.0, 2.0])] * 6
    result = ppp.bar_dots(ax, values)
    markers = [pts.get_paths()[0] for pts in result.points]
    expected = [s.marker for s in ppp.get_shapes("default", 6)]
    assert expected[:4] == ["o", "s", "^", "D"]
    for path, marker in zip(markers, expected, strict=True):
        assert np.allclose(path.vertices, _marker_vertices(marker))
    # The 5th shape (asterisk) is a line marker drawn in the point colour.
    assert result.points[4].get_linewidths()[0] == pytest.approx(
        ppp.plots.GGPLOT_STROKE_PT
    )


def test_bar_dots_outlined_shapes_get_black_edges(ax):
    result = ppp.bar_dots(ax, REPS, point_marker="filled", point_color=None)
    points = result.points[0]
    assert points.get_edgecolor()[0] == pytest.approx(to_rgba("black"))
    assert points.get_facecolor()[0] != pytest.approx(to_rgba("black"))


def test_bar_dots_none_keeps_0_2_meaning(ax):
    result = ppp.bar_dots(ax, REPS, colors=["red", "blue"], edge_color=None)
    assert result.bars[0].get_edgecolor() == pytest.approx(to_rgba("red"))


def test_bar_dots_capsize_in_points_overrides_data_caps(ax):
    result = ppp.bar_dots(ax, REPS, capsize=4)
    cap = result.errorbars[0].caps[0]
    assert cap.get_marker() == "_" and cap.get_markersize() == 8
    data = ppp.bar_dots(ax, REPS, cap_width=0.5)
    low, high = data.errorbars[0].caps[1].get_xdata()
    assert high - low == pytest.approx(0.5)
    none = ppp.bar_dots(ax, REPS, cap_width=0)
    assert none.errorbars[0].caps == (None, None)


def test_bar_dots_err_direction_up(ax):
    result = ppp.bar_dots(
        ax, None, centre=[3.0, -2.0], err=[1.0, 1.0], err_direction="up"
    )
    up, down = result.errorbars
    assert up.caps[0] is None and up.caps[1].get_ydata()[0] == pytest.approx(4.0)
    assert list(up.line.get_ydata()) == pytest.approx([3.0, 4.0])
    # A negative bar's "up" half points away from the baseline, downwards.
    assert down.caps[1] is None and down.caps[0].get_ydata()[0] == pytest.approx(-3)
    horizontal = ppp.bar_dots(
        ax, None, centre=[3.0], err=[1.0], err_direction="up", orientation="horizontal"
    )
    assert list(horizontal.errorbars[0].line.get_xdata()) == pytest.approx([3, 4])
    with pytest.raises(ValueError, match="err_direction"):
        ppp.bar_dots(ax, REPS, err_direction="down")


def test_bars_start_on_the_axis_line(ax):
    ppp.bar_dots(ax, REPS)
    assert ax.get_ylim()[0] == 0
    ax2 = ax.figure.add_axes([0.6, 0.1, 0.3, 0.3])
    ppp.bar_dots(ax2, REPS, orientation="horizontal")
    assert ax2.get_xlim()[0] == 0


def test_bar_dots_dot_shape_uses_category_shape(ax):
    result = ppp.bar_dots(ax, REPS, shape="dot")
    assert [b.get_marker() for b in result.bars] == ["o", "s"]
    assert result.bars[0].get_markeredgewidth() == 0


def test_bar_dots_classic_values(ax):
    result = ppp.bar_dots(ax, REPS, style="classic")
    assert result.points[0].get_sizes()[0] == 18
    assert result.errorbars[0].caps[0].get_markersize() == 6
    grouped = ppp.grouped_bars(ax, [REPS], style="classic")
    assert grouped.points[(0, 0)].get_sizes()[0] == 14
    with pytest.raises(ValueError, match="style"):
        ppp.bar_dots(ax, REPS, style="fancy")


def test_grouped_bars_prism_defaults(ax):
    data = [[REPS[0], REPS[1]], [REPS[1], REPS[0]]]
    result = ppp.grouped_bars(
        ax, data, colors=["#0000FF", "#FF0000"], series_labels=["a", "b"], legend=True
    )
    a, b = result.legend_handles
    assert isinstance(a, Patch)
    assert a.get_facecolor() == pytest.approx(to_rgba("#0000FF"))
    assert a.get_edgecolor() == pytest.approx(to_rgba("black"))
    assert a.get_linewidth() == pytest.approx(LINE_PT)
    assert result.bars[(1, 1)].get_facecolor() == pytest.approx(to_rgba("#FF0000"))
    circle, square = _marker_vertices("o"), _marker_vertices("s")
    assert np.allclose(result.points[(0, 0)].get_paths()[0].vertices, circle)
    assert np.allclose(result.points[(1, 1)].get_paths()[0].vertices, square)
    assert result.legend.get_texts()[0].get_fontweight() == "normal"
    cap = result.errorbars[(0, 0)].caps[1]
    assert np.ptp(cap.get_xdata()) == pytest.approx(0.16 / 3)
    dots = ppp.grouped_bars(ax, data, shape="dot")
    assert [h.get_marker() for h in dots.legend_handles] == ["o", "s"]


# --- xy_lines -------------------------------------------------------------------


def test_xy_lines_prism_defaults(ax):
    result = ppp.xy_lines(
        ax,
        [0, 1, 2],
        {"a": [1.0, 2.0, 3.0], "b": [2.0, 3.0, 4.0], "c": [3.0, 4.0, 5.0]},
        err={"a": 0.5},
        colors=["#077E97", "#800080", "#000080"],
    )
    lines = {name: s.line for name, s in result.series.items()}
    assert [line.get_marker() for line in lines.values()] == ["o", "s", "^"]
    line = lines["a"]
    assert line.get_markerfacecolor() == "#077E97"
    assert line.get_markeredgecolor() == "#077E97"
    assert line.get_markersize() == pytest.approx(7.1, abs=0.05)
    assert line.get_linewidth() == pytest.approx(LINE_PT)
    errorbar = result.series["a"].errorbars[0]
    assert errorbar.line.get_color() == "#077E97"
    assert errorbar.line.get_linewidth() == pytest.approx(LINE_PT)
    assert errorbar.caps[0].get_markersize() == pytest.approx(line.get_markersize())


def test_xy_lines_filled_palette_black_outline(ax):
    result = ppp.xy_lines(ax, [0, 1], {"a": [1, 2], "b": [2, 3]}, markers="filled")
    line = result.series["b"].line
    assert line.get_marker() == "s"
    assert line.get_markeredgecolor() == "black"
    assert line.get_markeredgewidth() == pytest.approx(ppp.plots.GGPLOT_STROKE_PT)
    points = ppp.xy_lines(ax, [0, 1], {"c": [1, 2]}, points={"c": [[1], [2]]})
    assert points.series["c"].points is not None


def test_xy_lines_classic_values(ax):
    result = ppp.xy_lines(ax, [0, 1], {"a": [1, 2]}, err={"a": 1}, style="classic")
    line = result.series["a"].line
    assert line.get_markersize() == 6.0 and line.get_linewidth() == 1.5
    assert result.series["a"].errorbars[0].caps[0].get_markersize() == 6


# --- brackets -------------------------------------------------------------------


def test_significance_bar_prism_defaults(ax):
    ax.set_ylim(0, 10)
    line, label = ppp.significance_bar(ax, 0, 1, 8, "p = 0.03")
    assert line.get_linewidth() == pytest.approx(0.6 * LINE_PT)  # bracket.size
    assert list(line.get_ydata()) == pytest.approx([8, 8.3, 8.3, 8])  # tip 0.03
    assert label.get_position() == pytest.approx((0.5, 8.43))  # 0.013 gap
    assert label.get_va() == "bottom"
    assert label.get_fontsize() == pytest.approx(3.2 * ppp.GGPLOT_TEXT_PT)
    assert label.get_fontweight() == "normal"
    assert line.get_solid_capstyle() == "butt"
    _, stars = ppp.significance_bar(ax, 0, 1, 8, "***")
    assert stars.get_va() == "center"


def test_significance_bar_size_follows_theme():
    with ppp.prism_context(base_size=20):
        fig, ax = plt.subplots()
        _, label = ppp.significance_bar(ax, 0, 1, 1, "*")
        _, bold = ppp.significance_bar(ax, 0, 1, 1, "*", font_weight=None)
        _, rc = ppp.significance_bar(ax, 0, 1, 1, "*", font_size=None)
    assert label.get_fontsize() == pytest.approx(3.2 * ppp.GGPLOT_TEXT_PT * 20 / 14)
    assert bold.get_fontweight() == "bold"
    assert rc.get_fontsize() == 20
    with pytest.raises(ValueError, match="style"):
        ppp.significance_bar(ax, 0, 1, 1, "*", style="fancy")
    plt.close(fig)


# --- palettes and shapes --------------------------------------------------------


def test_colors_palette_matches_ggprism_exactly():
    assert ppp.get_palette("colors") == [
        "#0000FF", "#FF0000", "#00C000", "#AD07E3", "#FF8000", "#000000",
        "#94641F", "#000080", "#610051", "#A00000", "#056943", "#F2B77C",
        "#00FF00", "#90BFF9", "#C0C0FF", "#606060", "#FFFF00", "#C06000",
        "#D4D4D4", "#C0C000",
    ]  # fmt: skip
    assert ppp.get_palette("colors", kind="fill")[10] == "#005A00"
    rc = ppp.prism_style()["axes.prop_cycle"].by_key()["color"]
    assert rc == ppp.get_palette("colors")


def test_all_ggprism_palettes_and_kept_pyprism_ones():
    colour = ppp.list_palettes()
    assert len(ppp.list_palettes(kind="fill")) == 45
    assert len(colour) == 65 + 4 + 4
    for name in ("warm", "cool", "muted", "monochrome", "floral_classic"):
        assert name in colour
    assert ppp.get_palette("floral_classic")[0] == "#6A3D9A"
    assert ppp.get_palette("floral")[0] == "#285291"  # ggprism's floral
    assert ppp.get_palette("winter_bright", 2) == ["#077E97", "#800080"]
    with pytest.raises(ValueError, match="kind"):
        ppp.get_palette("colors", kind="border")


def test_shape_palettes():
    assert [s.pch for s in ppp.get_shapes()] == [16, 15, 17, 18, 8, 3, 4, 10, 7]
    assert [s.pch for s in ppp.get_shapes("filled", 5)] == [21, 22, 24, 25, 23]
    assert all(s.outlined for s in ppp.get_shapes("filled", 5))
    assert len(ppp.SHAPE_PALETTES["complete"]) == 14
    with pytest.raises(ValueError, match="Unknown shape palette"):
        ppp.get_shapes("round")
    with pytest.raises(ValueError, match="positive integer"):
        ppp.get_shapes("default", 0)
    with pytest.raises(ValueError, match="has 9 shapes"):
        ppp.get_shapes("default", 10)


def test_default_sentinel():
    assert repr(ppp.DEFAULT) == "DEFAULT"
    assert copy.deepcopy(ppp.DEFAULT) is ppp.DEFAULT
    assert pickle.loads(pickle.dumps(ppp.DEFAULT)) is ppp.DEFAULT
    assert ppp.STYLES == ("prism", "classic")

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.collections import PathCollection, QuadMesh
from matplotlib.colors import to_rgba
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle

import pyprism_plot as ppp

REPS = [np.array([1.0, 2.0, 3.0]), np.array([4.0, 5.0, 6.0, 7.0])]


@pytest.fixture
def ax():
    fig, axes = plt.subplots()
    yield axes
    plt.close(fig)


def _snapshot(fig, others):
    return {
        "figure": (
            list(fig.artists),
            list(fig.lines),
            list(fig.patches),
            list(fig.texts),
            list(fig.images),
            list(fig.legends),
            list(fig.axes),
            tuple(fig.get_size_inches()),
        ),
        "positions": [tuple(a.get_position().bounds) for a in fig.axes],
        "others": [
            (list(a.get_children()), a.get_xlim(), a.get_ylim()) for a in others
        ],
        "rc": dict(mpl.rcParams),
    }


CALLS = {
    "bar_dots": lambda ax: ppp.bar_dots(ax, REPS, labels=["a", "b"]),
    "bar_dots_h": lambda ax: ppp.bar_dots(ax, REPS, orientation="horizontal"),
    "grouped_bars": lambda ax: ppp.grouped_bars(
        ax, [REPS, [REPS[1], None]], cluster_labels=["x", "y"], legend=True
    ),
    "xy_lines": lambda ax: ppp.xy_lines(
        ax, [1, 10], {"a": [1.0, 2.0]}, points={"a": [[1.0], [2.0]]}, logx=True
    ),
    "heatmap": lambda ax: ppp.heatmap(
        ax, [[1.0, -1.0], [np.nan, 0.5]], annotations=True, row_labels=["r1", "r2"]
    ),
    "significance_bar_h": lambda ax: ppp.significance_bar_h(ax, 0, 1, 2, "*"),
}


@pytest.mark.parametrize("name", list(CALLS))
def test_functions_touch_only_their_axes(name):
    fig = plt.figure(figsize=(6, 4))
    target = fig.add_axes([0.1, 0.1, 0.35, 0.8])
    other = fig.add_axes([0.6, 0.1, 0.35, 0.8])
    other.plot([0, 1], [0, 1])
    before = _snapshot(fig, [other])
    CALLS[name](target)
    fig.canvas.draw()
    assert _snapshot(fig, [other]) == before
    plt.close(fig)


# --- bar_dots ---------------------------------------------------------------


def test_bar_dots_returns_one_artist_group_per_category(ax):
    result = ppp.bar_dots(ax, REPS)
    assert isinstance(result, ppp.BarDotsArtists)
    assert all(isinstance(bar, Rectangle) for bar in result.bars)
    assert all(isinstance(pts, PathCollection) for pts in result.points)
    assert [len(pts.get_offsets()) for pts in result.points] == [3, 4]
    for errorbar in result.errorbars:
        assert isinstance(errorbar, ppp.ErrorBarArtists)
        assert all(isinstance(a, Line2D) for a in errorbar.artists())
        assert len(errorbar.artists()) == 3
    assert result.labels == []
    assert len(result.artists()) == 2 + 2 + 2 * 3


def test_bar_dots_honours_positions_and_width(ax):
    positions = [0.5, 2.25]
    result = ppp.bar_dots(ax, REPS, positions=positions, width=0.4)
    for bar, position, values in zip(result.bars, positions, REPS, strict=True):
        assert bar.get_x() == pytest.approx(position - 0.2)
        assert bar.get_width() == pytest.approx(0.4)
        assert bar.get_y() == 0
        assert bar.get_height() == pytest.approx(values.mean())


def test_bar_dots_default_look_and_mean_sd(ax):
    result = ppp.bar_dots(ax, REPS, colors=["#2F6BFF", "red"])
    bar = result.bars[0]
    assert bar.get_facecolor() == pytest.approx(ppp.tint_color("#2F6BFF", 0.3))
    assert bar.get_edgecolor() == pytest.approx(to_rgba("#2F6BFF"))
    assert bar.get_linewidth() == pytest.approx(1.3)
    line = result.errorbars[0].line
    assert line.get_color() == "#202020"
    assert list(line.get_ydata()) == pytest.approx([1.0, 3.0])  # mean 2, SD 1
    points = result.points[0]
    assert points.get_edgecolor()[0] == pytest.approx(to_rgba("black"))
    assert points.get_facecolor()[0] == pytest.approx(to_rgba("#2F6BFF"))


def test_bar_dots_jitter_is_even_and_deterministic(ax):
    first = ppp.bar_dots(ax, REPS, positions=[1, 3], jitter=0.3)
    second = ppp.bar_dots(ax, REPS, positions=[1, 3], jitter=0.3)
    offsets = first.points[1].get_offsets()
    assert list(offsets[:, 0]) == pytest.approx(3 + np.linspace(-0.15, 0.15, 4))
    assert list(offsets[:, 1]) == pytest.approx(REPS[1])
    assert np.array_equal(offsets, second.points[1].get_offsets())


def test_bar_dots_skips_nan_and_none_without_moving_others(ax):
    values = [REPS[0], None, [np.nan, np.nan], REPS[1], [5.0, np.nan]]
    result = ppp.bar_dots(ax, values, positions=[0, 1, 2, 3, 4], width=0.5)
    assert result.bars[1] is None and result.bars[2] is None
    assert result.points[1] is None and result.points[2] is None
    assert result.errorbars[1] is None and result.errorbars[2] is None
    assert result.bars[3].get_x() == pytest.approx(2.75)
    # A single finite replicate gives a column but no SD error bar.
    assert result.bars[4].get_height() == pytest.approx(5.0)
    assert result.errorbars[4] is None
    assert len(result.points[4].get_offsets()) == 1


def test_bar_dots_nan_centre_and_error(ax):
    result = ppp.bar_dots(
        ax, None, centre=[1.0, np.nan, None, 2.0], err=[0.1, 0.1, 0.1, np.nan]
    )
    assert [bar is None for bar in result.bars] == [False, True, True, False]
    assert result.errorbars[0] is not None and result.errorbars[3] is None
    assert result.points == [None] * 4


def test_bar_dots_asymmetric_err_sets_cap_positions(ax):
    result = ppp.bar_dots(ax, None, centre=[3.0, 4.0], err=([0.5, 1.0], [1.0, 2.0]))
    (low0, high0), (low1, high1) = (e.caps for e in result.errorbars)
    assert low0.get_ydata()[0] == pytest.approx(2.5)
    assert high0.get_ydata()[0] == pytest.approx(4.0)
    assert low1.get_ydata()[0] == pytest.approx(3.0)
    assert high1.get_ydata()[0] == pytest.approx(6.0)
    assert list(result.errorbars[1].line.get_ydata()) == pytest.approx([3.0, 6.0])
    assert low0.get_marker() == "_"


def test_bar_dots_bounds_are_absolute_interval_ends(ax):
    result = ppp.bar_dots(ax, None, centre=[3.0], bounds=([2.0], [3.5]))
    low, high = result.errorbars[0].caps
    assert (low.get_ydata()[0], high.get_ydata()[0]) == pytest.approx((2.0, 3.5))


def test_bar_dots_one_sided_error_omits_empty_cap(ax):
    result = ppp.bar_dots(ax, None, centre=[3.0], err=([0.0], [1.0]))
    low, high = result.errorbars[0].caps
    assert low is None and high.get_ydata()[0] == pytest.approx(4.0)


def test_bar_dots_horizontal_bars_grow_along_x(ax):
    result = ppp.bar_dots(
        ax,
        REPS,
        positions=[0, 2],
        orientation="horizontal",
        width=0.5,
        err=([0.5, 1.0], [1.0, 2.0]),
    )
    bar = result.bars[1]
    assert (bar.get_x(), bar.get_y()) == pytest.approx((0.0, 1.75))
    assert (bar.get_width(), bar.get_height()) == pytest.approx((5.5, 0.5))
    low, high = result.errorbars[1].caps
    assert low.get_xdata()[0] == pytest.approx(4.5)
    assert high.get_xdata()[0] == pytest.approx(7.5)
    assert list(low.get_ydata()) == [2]
    assert low.get_marker() == "|"
    offsets = result.points[1].get_offsets()
    assert list(offsets[:, 0]) == pytest.approx(REPS[1])
    assert list(offsets[:, 1]) == pytest.approx(2 + np.linspace(-0.125, 0.125, 4))
    assert ax.get_xlim()[0] == 0  # bars stick to the baseline


@pytest.mark.parametrize("orientation", ["vertical", "horizontal"])
def test_bar_dots_dot_and_line_shapes(ax, orientation):
    dots = ppp.bar_dots(ax, REPS, shape="dot", orientation=orientation)
    lines = ppp.bar_dots(
        ax, REPS, shape="line", positions=[4, 5], width=0.4, orientation=orientation
    )
    assert all(isinstance(mark, Line2D) for mark in dots.bars + lines.bars)
    assert dots.bars[0].get_marker() == "o"
    ends, value = list(lines.bars[0].get_xdata()), lines.bars[0].get_ydata()[0]
    if orientation == "horizontal":
        ends, value = list(lines.bars[0].get_ydata()), lines.bars[0].get_xdata()[0]
    assert ends == pytest.approx([3.8, 4.2])
    assert value == pytest.approx(2.0)


def test_bar_dots_style_parameters(ax):
    result = ppp.bar_dots(
        ax,
        REPS,
        colors="purple",
        tint=1.0,
        edge_color="black",
        edge_width=2,
        err_color="red",
        err_width=0.7,
        capsize=5,
        point_size=30,
        point_color="white",
        point_edgecolor="blue",
        point_edgewidth=1.1,
        zorder=10,
    )
    bar, errorbar, points = result.bars[0], result.errorbars[0], result.points[0]
    assert bar.get_facecolor() == pytest.approx(to_rgba("purple"))
    assert bar.get_edgecolor() == pytest.approx(to_rgba("black"))
    assert bar.get_linewidth() == 2
    assert errorbar.line.get_color() == "red"
    assert errorbar.line.get_linewidth() == pytest.approx(0.7)
    assert errorbar.caps[0].get_markersize() == 10
    assert list(points.get_sizes()) == [30]
    assert points.get_facecolor()[0] == pytest.approx(to_rgba("white"))
    assert points.get_edgecolor()[0] == pytest.approx(to_rgba("blue"))
    assert points.get_linewidths()[0] == pytest.approx(1.1)
    assert (bar.zorder, points.zorder, errorbar.line.zorder) == (10, 11, 12)


def test_bar_dots_default_colors_follow_prism_palette(ax):
    with ppp.prism_context(palette="warm"):
        result = ppp.bar_dots(ax, REPS)
    expected = ppp.get_palette("warm", 2)
    for bar, color in zip(result.bars, expected, strict=True):
        assert bar.get_edgecolor() == pytest.approx(to_rgba(color))


def test_bar_dots_labels_and_font_size(ax):
    result = ppp.bar_dots(ax, REPS, positions=[1, 3], labels=["WT", "dX"], font_size=7)
    assert [t.get_text() for t in result.labels] == ["WT", "dX"]
    assert [t.get_fontsize() for t in result.labels] == [7, 7]
    assert list(ax.get_xticks()) == [1, 3]
    horizontal = ppp.bar_dots(ax, REPS, orientation="horizontal", labels=["a", "b"])
    assert [t.get_text() for t in horizontal.labels] == ["a", "b"]
    assert list(ax.get_yticks()) == [0, 1]


def test_bar_dots_limits(ax):
    ax.set_xlim(-5, 5)
    ax.set_ylim(0, 1)
    ppp.bar_dots(ax, REPS, autoscale=False)
    assert ax.get_xlim() == (-5, 5) and ax.get_ylim() == (0, 1)
    ppp.bar_dots(ax, REPS, xlim=(-1, 2), ylim=(0, 9))
    assert ax.get_xlim() == (-1, 2) and ax.get_ylim() == (0, 9)


def test_bar_dots_without_points_or_errorbars(ax):
    result = ppp.bar_dots(ax, REPS, points=False, errorbars=False)
    assert result.points == [None, None] and result.errorbars == [None, None]


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"orientation": "diagonal"}, "orientation"),
        ({"shape": "violin"}, "shape"),
        ({"width": 0}, "width"),
        ({"jitter": -1}, "jitter"),
        ({"tint": 2}, "tint"),
        ({"capsize": -1}, "capsize"),
        ({"positions": [0]}, "positions"),
        ({"positions": [0, np.nan]}, "finite"),
        ({"err": [-1, 1]}, "negative"),
        ({"err": [[1, 1, 1]]}, "shape"),
        ({"bounds": ([0, 0], [1, 1]), "err": [1, 1]}, "either"),
        ({"centre": [5, 5], "bounds": ([0, 0], [1, 1])}, "low <= centre"),
        ({"bounds": [1, 2]}, "shape"),
        ({"labels": ["a"]}, "labels"),
        ({"colors": []}, "empty"),
    ],
)
def test_bar_dots_validation(ax, kwargs, message):
    with pytest.raises(ValueError, match=message):
        ppp.bar_dots(ax, REPS, **kwargs)


def test_bar_dots_requires_values_or_centre(ax):
    with pytest.raises(ValueError, match="values, centre"):
        ppp.bar_dots(ax, None)


def test_tint_color_validation():
    assert ppp.tint_color("black", 0) == (1, 1, 1, 1)
    with pytest.raises(ValueError, match="between 0 and 1"):
        ppp.tint_color("black", 1.5)


# --- significance_bar_h -----------------------------------------------------


def test_significance_bar_h_geometry(ax):
    ax.set_xlim(0, 10)
    line, label = ppp.significance_bar_h(ax, 0, 2, 8, "**")
    assert list(line.get_xdata()) == pytest.approx([8, 8.3, 8.3, 8])
    assert list(line.get_ydata()) == [0, 0, 2, 2]
    assert label.get_position() == pytest.approx((8.55, 1.0))
    assert label.get_ha() == "left" and label.get_va() == "center"
    assert label.get_fontsize() == pytest.approx(mpl.rcParams["font.size"])


def test_significance_bar_h_custom_size(ax):
    line, label = ppp.significance_bar_h(
        ax, 1, 3, 5, "ns", height=0.5, text_offset=0.1, line_width=2, font_size=9
    )
    assert list(line.get_xdata()) == pytest.approx([5, 5.5, 5.5, 5])
    assert line.get_linewidth() == 2
    assert label.get_position() == pytest.approx((5.6, 2.0))
    assert label.get_fontsize() == 9


def test_significance_bar_h_validation(ax):
    with pytest.raises(ValueError, match="different positions"):
        ppp.significance_bar_h(ax, 1, 1, 2, "*")
    with pytest.raises(ValueError, match="greater than zero"):
        ppp.significance_bar_h(ax, 0, 1, 2, "*", line_width=0)
    with pytest.raises(ValueError, match="greater than zero or None"):
        ppp.significance_bar_h(ax, 0, 1, 2, "*", font_size=-1)


# --- grouped_bars -----------------------------------------------------------


GROUPS = [
    [np.array([1.0, 2.0, 3.0]), np.array([2.0, 4.0])],
    [None, np.array([5.0, 6.0, 7.0]), np.array([1.0, 1.5])],
]


def test_grouped_bars_keys_positions_and_widths(ax):
    result = ppp.grouped_bars(
        ax, GROUPS, cluster_positions=[0, 2], series_width=0.2, bar_width=0.15
    )
    assert set(result.bars) == {(0, 0), (0, 1), (1, 1), (1, 2)}
    assert set(result.points) == set(result.bars)
    for (cluster, series), bar in result.bars.items():
        centre = [0, 2][cluster] + (series - 1) * 0.2
        assert bar.get_x() + bar.get_width() / 2 == pytest.approx(centre)
        assert bar.get_width() == pytest.approx(0.15)
    assert result.bars[(1, 1)].get_height() == pytest.approx(6.0)
    assert len(result.points[(0, 0)].get_offsets()) == 3
    assert isinstance(result.errorbars[(0, 1)], ppp.ErrorBarArtists)
    assert len(result.artists()) == 4 + 4 + 4 * 3


def test_grouped_bars_legend_handles_match_bars(ax):
    result = ppp.grouped_bars(
        ax, GROUPS, colors=["red", "green", "blue"], series_labels=["a", "b", "c"]
    )
    assert result.legend is None
    handles = result.legend_handles
    assert all(isinstance(h, Patch) for h in handles)
    assert [h.get_label() for h in handles] == ["a", "b", "c"]
    assert handles[1].get_facecolor() == result.bars[(1, 1)].get_facecolor()
    assert handles[1].get_edgecolor() == result.bars[(1, 1)].get_edgecolor()
    with_legend = ppp.grouped_bars(ax, GROUPS, legend=True)
    assert with_legend.legend is ax.get_legend()
    assert [t.get_text() for t in with_legend.legend.get_texts()][0] == "Series 1"


def test_grouped_bars_dot_legend_handles(ax):
    result = ppp.grouped_bars(ax, GROUPS, shape="dot")
    assert all(isinstance(h, Line2D) for h in result.legend_handles)
    result = ppp.grouped_bars(ax, GROUPS, shape="line")
    assert result.legend_handles[0].get_marker() == "None"


def test_grouped_bars_nested_errors_and_centres(ax):
    result = ppp.grouped_bars(
        ax,
        [[None, None], [None, None]],
        centre=[[2.0, 3.0], [4.0, None]],
        err=[[(0.5, 1.0), 0.2], [None, 1.0]],
    )
    assert set(result.bars) == {(0, 0), (0, 1), (1, 0)}
    low, high = result.errorbars[(0, 0)].caps
    assert (low.get_ydata()[0], high.get_ydata()[0]) == pytest.approx((1.5, 3.0))
    assert (1, 0) not in result.errorbars
    bounded = ppp.grouped_bars(
        ax, [[None]], centre=[[2.0]], bounds=[[(1.0, 2.5)]], errorbars=True
    )
    low, high = bounded.errorbars[(0, 0)].caps
    assert (low.get_ydata()[0], high.get_ydata()[0]) == pytest.approx((1.0, 2.5))


def test_grouped_bars_horizontal_and_labels(ax):
    result = ppp.grouped_bars(
        ax,
        GROUPS,
        orientation="horizontal",
        cluster_positions=[1, 4],
        cluster_labels=["30C", "37C"],
    )
    bar = result.bars[(1, 2)]
    assert bar.get_y() + bar.get_height() / 2 == pytest.approx(4.16)
    assert bar.get_width() == pytest.approx(1.25)
    assert [t.get_text() for t in result.labels] == ["30C", "37C"]
    assert list(ax.get_yticks()) == [1, 4]


def test_grouped_bars_autoscale_off(ax):
    ax.set_ylim(0, 1)
    ppp.grouped_bars(ax, GROUPS, autoscale=False)
    assert ax.get_ylim() == (0, 1)


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"series_width": 0}, "series_width"),
        ({"bar_width": -1}, "bar_width"),
        ({"cluster_positions": [0]}, "cluster_positions"),
        ({"centre": [[1]]}, "per cluster"),
        ({"centre": [[1, 2, 3, 4], None]}, "more series"),
        ({"err": [[(1, 2, 3)], None]}, "number or a pair"),
        ({"jitter": -0.1}, "jitter"),
    ],
)
def test_grouped_bars_validation(ax, kwargs, message):
    with pytest.raises(ValueError, match=message):
        ppp.grouped_bars(ax, GROUPS, **kwargs)


# --- xy_lines ---------------------------------------------------------------


def test_xy_lines_draws_lines_markers_and_errorbars(ax):
    x = [0, 1, 2]
    result = ppp.xy_lines(
        ax,
        x,
        {"wt": [1.0, 2.0, 3.0], "mut": ([1.0, 1.5, 2.0], [0.5, 1.0, 1.0], [2, 2, 4])},
        err={"wt": [0.1, 0.2, 0.3]},
        colors=["red", "blue"],
    )
    wt, mut = result.series["wt"], result.series["mut"]
    assert list(wt.line.get_xdata()) == x
    assert wt.line.get_marker() == "o" and mut.line.get_marker() == "s"
    assert wt.line.get_label() == "wt"
    assert len(wt.errorbars) == 3 and wt.points is None
    low, high = mut.errorbars[2].caps
    assert (low.get_ydata()[0], high.get_ydata()[0]) == pytest.approx((1.0, 4.0))
    assert wt.errorbars[1].line.get_color() == "red"
    assert len(result.artists()) == 2 + 6 * 3


def test_xy_lines_nan_breaks_line_and_skips_errorbars(ax):
    result = ppp.xy_lines(ax, [1, 2, 3], {"a": [1.0, np.nan, 3.0]}, err={"a": 0.5})
    series = result.series["a"]
    assert np.isnan(series.line.get_ydata()[1])
    assert series.errorbars[1] is None and series.errorbars[0] is not None


def test_xy_lines_points_behind_and_logx(ax):
    replicates = {"a": [[1.0, 2.0], [np.nan], [3.0, 4.0, 5.0]]}
    result = ppp.xy_lines(
        ax, [1, 10, 100], {"a": [1.5, 2.0, 4.0]}, points=replicates, logx=True
    )
    series = result.series["a"]
    offsets = series.points.get_offsets()
    assert len(offsets) == 5
    assert series.points.zorder < series.line.zorder
    assert ax.get_xscale() == "log"
    jittered = ppp.xy_lines(
        ax,
        [1, 10],
        {"b": [1.0, 2.0]},
        points={"b": [[1.0, 2.0], []]},
        jitter=1.0,
        logx=True,
    )
    xs = jittered.series["b"].points.get_offsets()[:, 0]
    assert list(xs) == pytest.approx([10**-0.5, 10**0.5])  # jitter is in decades


def test_xy_lines_options(ax):
    result = ppp.xy_lines(
        ax,
        [0, 1],
        {"a": [1.0, 2.0], "b": [2.0, 3.0]},
        markers=False,
        err={"a": [0.1, 0.1]},
        err_color="black",
        points={"b": [[], []]},
        autoscale=False,
    )
    assert result.series["a"].line.get_marker() == "none"
    assert result.series["a"].errorbars[0].line.get_color() == "black"
    assert result.series["b"].points is None
    assert ax.get_xlim() == (0, 1)
    custom = ppp.xy_lines(ax, [0, 1], {"a": [1, 2]}, markers="D", ylim=(0, 5))
    assert custom.series["a"].line.get_marker() == "D"
    assert ax.get_ylim() == (0, 5)
    cycled = ppp.xy_lines(ax, [0, 1], {"a": [1, 2], "b": [1, 2]}, markers=["^"])
    assert cycled.series["b"].line.get_marker() == "^"


@pytest.mark.parametrize(
    ("args", "kwargs", "message"),
    [
        (([[0, 1]], {"a": [1, 2]}), {}, "one-dimensional"),
        (([0, 1], {"a": [1, 2]}), {"err": {"b": 1}}, "unknown series"),
        (([0, 1], {"a": [1, 2, 3]}), {}, "one value per item"),
        (([0, 1], {"a": ([1, 2], [0, 1], [2, 3])}), {"err": {"a": 1}}, "both"),
        (([0, 1], {"a": [1, 2]}), {"points": {"a": [[1]]}}, "replicate set"),
        (([0, 1], {"a": [1, 2]}), {"point_tint": 3}, "point_tint"),
        (([0, 1], {"a": [1, 2]}), {"capsize": -2}, "capsize"),
    ],
)
def test_xy_lines_validation(ax, args, kwargs, message):
    with pytest.raises(ValueError, match=message):
        ppp.xy_lines(ax, *args, **kwargs)


# --- heatmap ----------------------------------------------------------------


MATRIX = [[2.0, -1.0, 0.0], [np.nan, 0.5, -2.0]]


def test_heatmap_returns_mesh_colorbar_and_texts(ax):
    result = ppp.heatmap(
        ax,
        MATRIX,
        row_labels=["r1", "r2"],
        col_labels=["a", "b", "c"],
        annotations=[["**", "", "*"], ["x", None, "ns"]],
        cbar_label="log2 FC",
    )
    assert isinstance(result.mesh, QuadMesh)
    assert result.colorbar.ax is result.cbar_ax
    assert result.colorbar.ax.get_ylabel() == "log2 FC"
    texts = [[t.get_text() if t else None for t in row] for row in result.texts]
    assert texts == [["**", None, "*"], ["n/a", None, "ns"]]
    assert result.texts[0][0].get_position() == (0, 0)
    assert result.texts[1][2].get_position() == (2, 1)
    assert [t.get_text() for t in result.row_labels] == ["r1", "r2"]
    assert [t.get_text() for t in result.col_labels] == ["a", "b", "c"]
    assert ax.get_xlim() == (-0.5, 2.5) and ax.get_ylim() == (1.5, -0.5)
    assert len(result.artists()) == 1 + 4 + 2 + 3


def test_heatmap_centered_norm_and_contrast(ax):
    result = ppp.heatmap(ax, MATRIX, annotations=True, fmt="{:.1f}")
    norm = result.mesh.norm
    assert (norm.vmin, norm.vmax) == (-2.0, 2.0)
    assert norm(0.0) == pytest.approx(0.5)
    texts = result.texts
    assert texts[0][0].get_text() == "2.0"
    assert texts[0][0].get_color() == "white"  # dark red cell
    assert texts[0][2].get_color() == "black"  # near-white cell
    assert texts[1][0].get_text() == "n/a" and texts[1][0].get_color() == "black"


def test_heatmap_nan_cells_are_grey(ax):
    result = ppp.heatmap(ax, MATRIX, cbar=False)
    face = result.mesh.cmap.get_bad()
    assert face == pytest.approx(to_rgba("#D9D9D9"))
    assert result.colorbar is None and result.cbar_ax is None
    assert result.texts == []


def test_heatmap_colorbar_axes_options(ax):
    fig = ax.figure
    position = ax.get_position().bounds
    result = ppp.heatmap(ax, MATRIX)
    assert result.cbar_ax not in fig.axes
    assert ax.get_position().bounds == position
    cax = fig.add_axes([0.92, 0.1, 0.02, 0.8])
    placed = ppp.heatmap(ax, MATRIX, cbar_ax=cax)
    assert placed.colorbar.ax is cax and placed.cbar_ax is cax
    assert ax.get_position().bounds == position


def test_heatmap_limits_and_labels(ax):
    result = ppp.heatmap(
        ax,
        MATRIX,
        center=None,
        vmin=-3,
        col_labels=["a", "b", "c"],
        col_label_rotation=45,
        label_font_size=6,
        font_size=5,
        annotations=True,
        frame=True,
        cell_edge_width=1,
    )
    assert (result.mesh.norm.vmin, result.mesh.norm.vmax) == (-3, 2)
    assert result.col_labels[0].get_rotation() == 45
    assert result.col_labels[0].get_ha() == "right"
    assert result.col_labels[0].get_fontsize() == 6
    assert result.texts[0][0].get_fontsize() == 5
    assert ax.spines["left"].get_visible()
    one_sided = ppp.heatmap(ax, MATRIX, vmax=4).mesh.norm
    assert (one_sided.vmin, one_sided.vmax) == (-4, 4)
    low_only = ppp.heatmap(ax, MATRIX, vmin=-1).mesh.norm
    assert (low_only.vmin, low_only.vmax) == (-1, 1)
    flat = ppp.heatmap(ax, [[1.0, 1.0]], center=None).mesh.norm
    assert (flat.vmin, flat.vmax) == (0.5, 1.5)
    empty = ppp.heatmap(ax, [[np.nan]], cmap=mpl.colormaps["viridis"]).mesh.norm
    assert (empty.vmin, empty.vmax) == (-1, 1)


def test_heatmap_validation(ax):
    with pytest.raises(ValueError, match="two-dimensional"):
        ppp.heatmap(ax, [1, 2, 3])
    with pytest.raises(ValueError, match="same shape"):
        ppp.heatmap(ax, MATRIX, annotations=[["*"]])

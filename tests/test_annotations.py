import matplotlib.pyplot as plt
import pytest

from pyprism_plot import significance_bar


def test_significance_bar_adds_line_and_text() -> None:
    fig, ax = plt.subplots()
    ax.set_ylim(0, 10)
    line, label = significance_bar(ax, 0, 1, 8, "p < 0.05", style="classic")
    assert list(line.get_xdata()) == [0, 0, 1, 1]
    assert list(line.get_ydata()) == pytest.approx([8, 8.3, 8.3, 8])
    assert line.get_linewidth() == pytest.approx(1.5)
    assert label.get_text() == "p < 0.05"
    assert label.get_position() == pytest.approx((0.5, 8.55))
    assert label.get_fontsize() == pytest.approx(12)
    plt.close(fig)


def test_significance_bar_size_is_customizable() -> None:
    fig, ax = plt.subplots()
    ax.set_ylim(0, 10)
    line, label = significance_bar(
        ax,
        0,
        1,
        8,
        "***",
        height=0.5,
        line_width=2.5,
        font_size=16,
        text_offset=0.1,
    )
    assert list(line.get_ydata()) == pytest.approx([8, 8.5, 8.5, 8])
    assert line.get_linewidth() == pytest.approx(2.5)
    assert label.get_position() == pytest.approx((0.5, 8.6))
    assert label.get_fontsize() == pytest.approx(16)
    plt.close(fig)


def test_significance_bar_validation() -> None:
    fig, ax = plt.subplots()
    with pytest.raises(ValueError, match="different positions"):
        significance_bar(ax, 1, 1, 2, "*")
    with pytest.raises(ValueError, match="greater than zero"):
        significance_bar(ax, 0, 1, 2, "*", line_width=0)
    with pytest.raises(ValueError, match="greater than zero or None"):
        significance_bar(ax, 0, 1, 2, "*", font_size=0)
    plt.close(fig)

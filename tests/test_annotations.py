import matplotlib.pyplot as plt
import pytest

from pyprism_plot import significance_bar


def test_significance_bar_adds_line_and_text() -> None:
    fig, ax = plt.subplots()
    ax.set_ylim(0, 10)
    line, label = significance_bar(ax, 0, 1, 8, "p < 0.05")
    assert list(line.get_xdata()) == [0, 0, 1, 1]
    assert label.get_text() == "p < 0.05"
    assert label.get_position() == pytest.approx((0.5, 8.4))
    plt.close(fig)


def test_significance_bar_validation() -> None:
    fig, ax = plt.subplots()
    with pytest.raises(ValueError, match="different positions"):
        significance_bar(ax, 1, 1, 2, "*")
    with pytest.raises(ValueError, match="greater than zero"):
        significance_bar(ax, 0, 1, 2, "*", line_width=0)
    plt.close(fig)

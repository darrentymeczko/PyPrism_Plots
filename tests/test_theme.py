import matplotlib as mpl
import matplotlib.pyplot as plt
import pytest

from pyprism_plot import prism_context, prism_style, style_axes, theme_prism, use_prism


def test_prism_style_core_settings() -> None:
    style = prism_style(base_size=14, border=True)
    assert style["axes.grid"] is False
    assert style["axes.spines.top"] is True
    assert style["axes.linewidth"] == 1
    assert theme_prism()["axes.facecolor"] == "white"


@pytest.mark.parametrize("kwargs", [{"base_size": 0}, {"line_width": 0}])
def test_prism_style_rejects_nonpositive_values(kwargs: dict[str, float]) -> None:
    with pytest.raises(ValueError, match="greater than zero"):
        prism_style(**kwargs)


def test_rejects_invalid_rotation() -> None:
    with pytest.raises(ValueError, match="must be one of"):
        prism_style(axis_text_angle=30)


def test_context_restores_rcparams() -> None:
    original = mpl.rcParams["axes.grid"]
    with prism_context():
        assert mpl.rcParams["axes.grid"] is False
    assert mpl.rcParams["axes.grid"] == original


def test_use_prism_updates_global_settings() -> None:
    with mpl.rc_context():
        use_prism(border=True)
        assert mpl.rcParams["axes.spines.right"] is True


def test_style_axes_controls_spines_ticks_and_cycle() -> None:
    fig, ax = plt.subplots()
    result = style_axes(ax, border=False, axis_text_angle=45, minor_ticks=True)
    assert result is ax
    assert ax.spines["left"].get_visible()
    assert not ax.spines["right"].get_visible()
    assert ax.xaxis.get_minorticklines()
    plt.close(fig)


def test_style_axes_rejects_bad_line_width() -> None:
    fig, ax = plt.subplots()
    with pytest.raises(ValueError, match="greater than zero"):
        style_axes(ax, line_width=0)
    plt.close(fig)


import matplotlib as mpl
import matplotlib.pyplot as plt
import pytest

from pyprism_plot import prism_context, prism_style, style_axes, theme_prism, use_prism


def test_prism_style_core_settings() -> None:
    style = prism_style(base_size=14, border=True)
    assert style["axes.grid"] is False
    assert style["axes.spines.top"] is True
    assert style["axes.linewidth"] == pytest.approx(72.27 / 25.4 * 72 / 96)
    assert prism_style(style="classic")["axes.linewidth"] == 1
    assert theme_prism()["axes.facecolor"] == "white"


@pytest.mark.parametrize("kwargs", [{"base_size": 0}, {"line_width": 0}])
def test_prism_style_rejects_nonpositive_values(kwargs: dict[str, float]) -> None:
    with pytest.raises(ValueError, match="greater than zero"):
        prism_style(**kwargs)


@pytest.mark.parametrize("angle", ["45", float("nan"), True, None])
def test_rejects_invalid_rotation(angle: object) -> None:
    with pytest.raises(ValueError, match="finite number"):
        prism_style(axis_text_angle=angle)  # type: ignore[arg-type]


def test_accepts_any_rotation() -> None:
    assert prism_style(axis_text_angle=30)["axes.grid"] is False


def test_prism_style_defaults_keep_tight_save_and_generic_family() -> None:
    style = prism_style()
    assert style["savefig.bbox"] == "tight"
    assert style["font.family"] == "sans-serif"


def test_prism_style_fixed_page_options() -> None:
    style = prism_style(base_family="Helvetica", tight_save=False, explicit_fonts=True)
    assert style["font.family"] == ["Helvetica", "Arial", "DejaVu Sans"]
    assert prism_style(explicit_fonts=True)["font.family"] == ["Arial", "DejaVu Sans"]
    with mpl.rc_context(style):
        assert mpl.rcParams["savefig.bbox"] is None
        assert mpl.rcParams["font.family"][0] == "Helvetica"


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
    with pytest.raises(ValueError, match="axis_text_ha"):
        style_axes(ax, axis_text_ha="middle")
    plt.close(fig)


def test_style_axes_keeps_legacy_alignment() -> None:
    fig, ax = plt.subplots()
    ax.set_xticks([0, 1], ["a", "b"])
    style_axes(ax, axis_text_angle=90)
    assert ax.get_xticklabels()[0].get_ha() == "right"
    style_axes(ax, axis_text_angle=0)
    assert ax.get_xticklabels()[0].get_ha() == "center"
    plt.close(fig)


def test_style_axes_arbitrary_rotation_with_anchor() -> None:
    fig, ax = plt.subplots()
    ax.set_xticks([0, 1], ["long label", "b"])
    style_axes(ax, axis_text_angle=30, axis_text_ha="right")
    label = ax.get_xticklabels()[0]
    assert label.get_rotation() == pytest.approx(30)
    assert label.get_ha() == "right"
    assert label.get_rotation_mode() == "anchor"
    plt.close(fig)

import pytest

from pyprism_plot import PALETTES, get_palette, list_palettes


def test_palette_names_are_sorted() -> None:
    assert list_palettes() == tuple(sorted(PALETTES))


def test_get_palette_returns_copy_and_requested_length() -> None:
    colors = get_palette("colors", 3)
    assert len(colors) == 3
    colors.append("#ffffff")
    assert len(PALETTES["colors"]) != len(colors)


@pytest.mark.parametrize("n", [0, -1, 1.5, True])
def test_rejects_invalid_n(n: object) -> None:
    with pytest.raises(ValueError, match="positive integer"):
        get_palette("colors", n)  # type: ignore[arg-type]


def test_rejects_unknown_or_too_short_palette() -> None:
    with pytest.raises(ValueError, match="Unknown palette"):
        get_palette("missing")
    with pytest.raises(ValueError, match="contains"):
        get_palette("monochrome", 6)


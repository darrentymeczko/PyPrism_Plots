"""Curated palettes for scientific figures.

The colors are an original, compact selection designed to evoke the high-contrast
categorical palettes commonly used in scientific graphing software. They are not
a copy of GraphPad or ggprism palette data.
"""

from __future__ import annotations

from types import MappingProxyType

_PALETTES = {
    "colors": ("#2F6BFF", "#E53935", "#2EAD4A", "#9C3CC4", "#F28E2B", "#111111"),
    "colorblind_safe": (
        "#0072B2",
        "#D55E00",
        "#009E73",
        "#CC79A7",
        "#E69F00",
        "#56B4E9",
        "#F0E442",
        "#000000",
    ),
    "floral": ("#6A3D9A", "#E157A0", "#F28EBC", "#4E79A7", "#76B7B2", "#59A14F"),
    "stained_glass": (
        "#184E77",
        "#1E6091",
        "#1A759F",
        "#52B69A",
        "#99D98C",
        "#D9ED92",
    ),
    "warm": ("#7F2704", "#D94801", "#F16913", "#FD8D3C", "#FDAE6B", "#FDD0A2"),
    "cool": ("#253494", "#2C7FB8", "#41B6C4", "#7FCDBB", "#C7E9B4", "#EDF8B1"),
    "muted": ("#4E79A7", "#F28E2B", "#E15759", "#76B7B2", "#59A14F", "#B07AA1"),
    "monochrome": ("#000000", "#444444", "#777777", "#AAAAAA", "#D0D0D0"),
}

PALETTES = MappingProxyType(_PALETTES)


def list_palettes() -> tuple[str, ...]:
    """Return available palette names in alphabetical order."""
    return tuple(sorted(PALETTES))


def get_palette(name: str = "colors", n: int | None = None) -> list[str]:
    """Return *n* colors from a named discrete palette.

    Raises
    ------
    ValueError
        If the palette does not exist, *n* is invalid, or the palette is too short.
    """
    if name not in PALETTES:
        choices = ", ".join(list_palettes())
        raise ValueError(f"Unknown palette {name!r}. Choose one of: {choices}.")
    colors = PALETTES[name]
    if n is None:
        return list(colors)
    if isinstance(n, bool) or not isinstance(n, int) or n < 1:
        raise ValueError("n must be a positive integer.")
    if n > len(colors):
        raise ValueError(
            f"Palette {name!r} contains {len(colors)} colors, but {n} were requested."
        )
    return list(colors[:n])


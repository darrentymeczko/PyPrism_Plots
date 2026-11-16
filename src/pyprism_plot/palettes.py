"""Colour, fill and shape palettes for scientific figures.

The colour and fill palettes are ggprism's (``prism_colour_pal`` and
``prism_fill_pal``), which ggprism extracted from GraphPad Prism's colour schemes;
see :mod:`pyprism_plot._ggprism_palettes`. ``warm``, ``cool``, ``muted`` and
``monochrome`` are PyPrism's own. The PyPrism 0.1/0.2 values of the four names
that ggprism also uses are kept as ``colors_classic``, ``colorblind_safe_classic``,
``floral_classic`` and ``stained_glass_classic``.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import NamedTuple

from ._ggprism_palettes import COLOUR, FILL

_PYPRISM = {
    "warm": ("#7F2704", "#D94801", "#F16913", "#FD8D3C", "#FDAE6B", "#FDD0A2"),
    "cool": ("#253494", "#2C7FB8", "#41B6C4", "#7FCDBB", "#C7E9B4", "#EDF8B1"),
    "muted": ("#4E79A7", "#F28E2B", "#E15759", "#76B7B2", "#59A14F", "#B07AA1"),
    "monochrome": ("#000000", "#444444", "#777777", "#AAAAAA", "#D0D0D0"),
}

_CLASSIC = {
    "colors_classic": (
        "#2F6BFF",
        "#E53935",
        "#2EAD4A",
        "#9C3CC4",
        "#F28E2B",
        "#111111",
    ),
    "colorblind_safe_classic": (
        "#0072B2",
        "#D55E00",
        "#009E73",
        "#CC79A7",
        "#E69F00",
        "#56B4E9",
        "#F0E442",
        "#000000",
    ),
    "floral_classic": (
        "#6A3D9A",
        "#E157A0",
        "#F28EBC",
        "#4E79A7",
        "#76B7B2",
        "#59A14F",
    ),
    "stained_glass_classic": (
        "#184E77",
        "#1E6091",
        "#1A759F",
        "#52B69A",
        "#99D98C",
        "#D9ED92",
    ),
}

CLASSIC_NAMES = MappingProxyType(
    {name.removesuffix("_classic"): name for name in _CLASSIC}
)
"""Palette names whose PyPrism 0.2 values live on under ``<name>_classic``."""

PALETTES = MappingProxyType({**COLOUR, **_PYPRISM, **_CLASSIC})
"""Colour palettes: data-set border, line and symbol colours."""

FILL_PALETTES = MappingProxyType(dict(FILL))
"""ggprism fill palettes: data-set fill colours (``prism_fill_pal``)."""


class Shape(NamedTuple):
    """One entry of a shape palette.

    ``marker`` is a Matplotlib marker. ``outlined`` is True for ggprism's filled
    shapes with a separate border (R ``pch`` 21-25), which are drawn with a black
    edge; ``line`` is True for markers drawn only with lines (``+``, ``x``, ...).
    """

    name: str
    pch: int
    marker: object
    outlined: bool = False
    line: bool = False


_SOLID = [
    Shape("circle small", 16, "o"),
    Shape("square", 15, "s"),
    Shape("triangle", 17, "^"),
    Shape("diamond", 18, "D"),
]
_OUTLINED = [
    Shape("circle filled", 21, "o", outlined=True),
    Shape("square filled", 22, "s", outlined=True),
    Shape("triangle filled", 24, "^", outlined=True),
    Shape("triangle down filled", 25, "v", outlined=True),
    Shape("diamond filled", 23, "D", outlined=True),
]
_LINES = [
    Shape("asterisk", 8, (6, 2, 0), line=True),
    Shape("plus", 3, "+", line=True),
    Shape("cross", 4, "x", line=True),
    Shape("circle plus", 10, r"$\oplus$", line=True),
    Shape("square cross", 7, r"$\boxtimes$", line=True),
]

SHAPE_PALETTES = MappingProxyType(
    {
        "default": tuple(_SOLID + _LINES),
        "filled": tuple(_OUTLINED + _LINES),
        "complete": tuple(_SOLID + _OUTLINED + _LINES),
    }
)
"""ggprism's shape palettes (``prism_shape_pal``), in ggprism's order."""

_KINDS = {"colour": PALETTES, "color": PALETTES, "fill": FILL_PALETTES}


def _palettes(kind: str) -> MappingProxyType:
    if kind not in _KINDS:
        raise ValueError("kind must be 'colour', 'color' or 'fill'.")
    return _KINDS[kind]


def list_palettes(kind: str = "colour") -> tuple[str, ...]:
    """Return available palette names of *kind* in alphabetical order."""
    return tuple(sorted(_palettes(kind)))


def get_palette(name: str = "colors", n: int | None = None, kind: str = "colour"):
    """Return *n* colors from a named discrete palette.

    ``kind="fill"`` returns ggprism's fill version of the palette.

    Raises
    ------
    ValueError
        If the palette does not exist, *n* is invalid, or the palette is too short.
    """
    palettes = _palettes(kind)
    if name not in palettes:
        choices = ", ".join(sorted(palettes))
        raise ValueError(f"Unknown palette {name!r}. Choose one of: {choices}.")
    colors = palettes[name]
    if n is None:
        return list(colors)
    if isinstance(n, bool) or not isinstance(n, int) or n < 1:
        raise ValueError("n must be a positive integer.")
    if n > len(colors):
        raise ValueError(
            f"Palette {name!r} contains {len(colors)} colors, but {n} were requested."
        )
    return list(colors[:n])


def get_shapes(name: str = "default", n: int | None = None) -> list[Shape]:
    """Return *n* shapes from a named shape palette (default: all of them)."""
    if name not in SHAPE_PALETTES:
        choices = ", ".join(sorted(SHAPE_PALETTES))
        raise ValueError(f"Unknown shape palette {name!r}. Choose one of: {choices}.")
    shapes = SHAPE_PALETTES[name]
    if n is None:
        return list(shapes)
    if isinstance(n, bool) or not isinstance(n, int) or n < 1:
        raise ValueError("n must be a positive integer.")
    if n > len(shapes):
        raise ValueError(
            f"Shape palette {name!r} has {len(shapes)} shapes, but {n} were requested."
        )
    return list(shapes[:n])

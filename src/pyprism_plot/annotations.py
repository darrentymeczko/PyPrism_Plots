"""Statistical annotation helpers.

The prism style follows ggprism's ``add_pvalue`` defaults: ``tip.length = 0.03``
of the axis span, ``bracket.size = 0.6`` (1.28 pt), ``label.size = 3.2`` mm
(9.1 pt at ``base_size = 14``) in a plain font, the label 1.3 % of the axis span
beyond the bracket, and asterisk-only labels centred on that point.
"""

from __future__ import annotations

from typing import Any

import matplotlib as mpl
from matplotlib.axes import Axes

from .plots import DEFAULT, STYLES
from .theme import GGPLOT_LINE_PT, GGPLOT_TEXT_PT

_ASTERISKS = {"*", "**", "***", "****"}

_BRACKET_DEFAULTS = {
    "prism": {
        "line_width": 0.6 * GGPLOT_LINE_PT,
        "font_weight": "normal",
        "text_offset": 0.013,
    },
    "classic": {"line_width": 1.5, "font_weight": None, "text_offset": 0.025},
}


def _bracket_settings(
    style: str,
    line_width: Any,
    font_size: Any,
    font_weight: Any,
    classic_font_size: float | None,
) -> tuple[float, float | None, Any, float]:
    if style not in STYLES:
        raise ValueError("style must be 'prism' or 'classic'.")
    defaults = _BRACKET_DEFAULTS[style]
    width = defaults["line_width"] if line_width is DEFAULT else line_width
    if font_size is DEFAULT:
        if style == "classic":
            font_size = classic_font_size
        else:
            # ggprism's 3.2 mm label relative to its default base_size of 14.
            font_size = 3.2 * GGPLOT_TEXT_PT * mpl.rcParams["font.size"] / 14
    weight = defaults["font_weight"] if font_weight is DEFAULT else font_weight
    if width <= 0:
        raise ValueError("line_width must be greater than zero.")
    if font_size is not None and font_size <= 0:
        raise ValueError("font_size must be greater than zero or None.")
    return width, font_size, weight, defaults["text_offset"]


def _label_alignment(text: str, style: str, centre: str) -> str:
    return centre if style == "prism" and text.strip() in _ASTERISKS else None


def significance_bar(
    ax: Axes,
    x1: float,
    x2: float,
    y: float,
    text: str,
    *,
    height: float | None = None,
    color: str = "black",
    line_width: float = DEFAULT,
    font_size: float | None = DEFAULT,
    font_weight: Any = DEFAULT,
    text_offset: float | None = None,
    clip_on: bool = False,
    style: str = "prism",
) -> tuple[object, object]:
    """Draw a comparison bracket and centered label on an axes.

    The bracket's tips start at ``y`` and its bar sits at ``y + height``.
    ``height`` and ``text_offset`` are in data coordinates and default to 3 % and
    (prism) 1.3 % of the current y-axis span, as ggprism's ``tip.length`` and
    label gap.

    With ``style="prism"`` (default) the bracket is 1.28 pt wide and the label is
    plain, ``font_size`` = 0.65 x the ``font.size`` in effect (ggprism's 3.2 mm
    label at its base size of 14). Asterisk-only labels are centred on the label
    point, as in ggprism. ``font_size=None`` uses the ``font.size`` in effect and
    ``font_weight=None`` the ``font.weight``. ``style="classic"`` gives the 0.2
    bracket: 1.5 pt, 12 pt text, 2.5 % gap.
    """
    if x1 == x2:
        raise ValueError("x1 and x2 must identify two different positions.")
    width, size, weight, gap = _bracket_settings(
        style, line_width, font_size, font_weight, 12.0
    )
    y_min, y_max = ax.get_ylim()
    span = abs(y_max - y_min) or 1.0
    bracket_height = span * 0.03 if height is None else height
    offset = span * gap if text_offset is None else text_offset
    (line,) = ax.plot(
        [x1, x1, x2, x2],
        [y, y + bracket_height, y + bracket_height, y],
        color=color,
        linewidth=width,
        clip_on=clip_on,
    )
    if style == "prism":
        line.set_solid_capstyle("butt")
    label = ax.text(
        (x1 + x2) / 2,
        y + bracket_height + offset,
        text,
        ha="center",
        va=_label_alignment(text, style, "center") or "bottom",
        color=color,
        fontsize=size,
        fontweight=weight,
        clip_on=clip_on,
    )
    return line, label


def significance_bar_h(
    ax: Axes,
    y1: float,
    y2: float,
    x: float,
    text: str,
    *,
    height: float | None = None,
    color: str = "black",
    line_width: float = DEFAULT,
    font_size: float | None = DEFAULT,
    font_weight: Any = DEFAULT,
    text_offset: float | None = None,
    clip_on: bool = False,
    style: str = "prism",
) -> tuple[object, object]:
    """Draw a comparison bracket for a horizontal graph.

    The bracket spans ``y1`` to ``y2``. Its ticks start at ``x`` and point left
    from a vertical spine at ``x + height``; the label sits to the right of the
    spine, vertically centered. ``height`` and ``text_offset`` are in x data
    coordinates and default to 3 % and (prism) 1.3 % of the current x-axis span.
    Sizes and weights follow :func:`significance_bar`; in the classic style the
    label uses the ``font.size`` in effect.
    """
    if y1 == y2:
        raise ValueError("y1 and y2 must identify two different positions.")
    width, size, weight, gap = _bracket_settings(
        style, line_width, font_size, font_weight, None
    )
    x_min, x_max = ax.get_xlim()
    span = abs(x_max - x_min) or 1.0
    bracket_height = span * 0.03 if height is None else height
    offset = span * gap if text_offset is None else text_offset
    (line,) = ax.plot(
        [x, x + bracket_height, x + bracket_height, x],
        [y1, y1, y2, y2],
        color=color,
        linewidth=width,
        clip_on=clip_on,
    )
    if style == "prism":
        line.set_solid_capstyle("butt")
    label = ax.text(
        x + bracket_height + offset,
        (y1 + y2) / 2,
        text,
        ha="left",
        va="center",
        color=color,
        fontsize=size,
        fontweight=weight,
        clip_on=clip_on,
    )
    return line, label

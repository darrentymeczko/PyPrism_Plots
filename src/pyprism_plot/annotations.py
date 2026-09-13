"""Statistical annotation helpers."""

from __future__ import annotations

from matplotlib.axes import Axes


def significance_bar(
    ax: Axes,
    x1: float,
    x2: float,
    y: float,
    text: str,
    *,
    height: float | None = None,
    color: str = "black",
    line_width: float = 1.5,
    font_size: float | None = 12.0,
    text_offset: float | None = None,
    clip_on: bool = False,
) -> tuple[object, object]:
    """Draw a comparison bracket and centered label on an axes.

    ``height`` and ``text_offset`` are expressed in data coordinates. When omitted,
    they are derived from three and two-and-a-half percent of the current y-axis
    span, respectively. Use ``line_width`` and ``font_size`` to customize the
    visual weight of the bracket and label. Pass ``font_size=None`` to inherit
    Matplotlib's configured font size.
    """
    if x1 == x2:
        raise ValueError("x1 and x2 must identify two different positions.")
    if line_width <= 0:
        raise ValueError("line_width must be greater than zero.")
    if font_size is not None and font_size <= 0:
        raise ValueError("font_size must be greater than zero or None.")
    y_min, y_max = ax.get_ylim()
    span = abs(y_max - y_min) or 1.0
    bracket_height = span * 0.03 if height is None else height
    offset = span * 0.025 if text_offset is None else text_offset
    (line,) = ax.plot(
        [x1, x1, x2, x2],
        [y, y + bracket_height, y + bracket_height, y],
        color=color,
        linewidth=line_width,
        clip_on=clip_on,
    )
    label = ax.text(
        (x1 + x2) / 2,
        y + bracket_height + offset,
        text,
        ha="center",
        va="bottom",
        color=color,
        fontsize=font_size,
        clip_on=clip_on,
    )
    return line, label

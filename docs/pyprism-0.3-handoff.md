# PyPrism 0.3.0 handoff: Prism defaults

This answers the "make PyPrism's plotting defaults look like GraphPad Prism /
ggprism" task. Every value, its source and every deliberate difference is in
[`prism-defaults.md`](prism-defaults.md). This page lists what changed for the
figure program.

## Status

- **Branch:** `prism-defaults`, built on `fix-autoscale` (0.2.1, the autoscale
  fix). Neither is on `main` or pushed yet. `__version__ == "0.3.0"`.
- **Tests:** 135 pass with 99 % coverage (Python 3.13, Matplotlib 3.11.2, Agg).
  `tests/test_prism_defaults.py` pins every new default and checks that
  `style="classic"` reproduces 0.2.
- **Comparison:** `examples/prism_comparison.png` (written by
  `python examples/gallery.py`) shows PyPrism beside the ggprism figures at the
  same physical size. It is not committed, because it embeds ggprism's GPL images,
  which the script downloads at run time.

## Removing the program's style arguments

The program passes `edge_width`, `tint`, `err_color`, `point_size`,
`point_edgecolor` and `point_edgewidth`. Without them, a call gets:

| Argument | 0.3 default (`style="prism"`) | 0.2 default |
|---|---|---|
| `tint` | `1.0`: solid palette colour | `0.3` |
| `edge_color` | `"black"` | `None` = the category colour |
| `edge_width` | `rcParams["axes.linewidth"]`: 2.13 pt under `prism_style(base_size=14)`, 0.8 pt outside it | `1.3` |
| `err_color` | `"black"` | `"#202020"` |
| `err_width` | `rcParams["axes.linewidth"]` | `1.0` |
| `capsize` / `cap_width` | caps a third of `width`, in data units | `capsize=3` pt |
| `point_size` | 24.8 pt² (5 pt across) | 18 (`bar_dots`), 14 (`grouped_bars`) |
| `point_color` | `"black"` | `None` = the category colour |
| `point_edgecolor` | `"auto"`: none for solid shapes, black for `"filled"` ones | `"black"` |
| `point_edgewidth` | `"auto"`: 0 for solid shapes, 0.71 pt for outlined and line shapes | `0.5` |
| `point_marker` | `"default"`: circle, square, triangle, diamond, asterisk, ... per category (`bar_dots`) or series (`grouped_bars`) | `"o"` |
| `mean_line_width` | `rcParams["axes.linewidth"]` | `2.0` |

**Things to check when switching:**

1. **Widths follow the theme at call time.** They follow the `axes.linewidth` in
   effect when the function runs. Call them inside the same
   `prism_context(base_size=...)` as the rest of the page, or the bars get
   Matplotlib's 0.8 pt.
2. **Caps are in data units now.** On a horizontal bar per strain, caps are a third
   of the bar thickness. Pass `capsize=` (points) to get fixed caps back.
3. **Points are black.** On saturated columns (the default `"colors"` palette starts
   with `#0000FF`), black points have weak contrast. This is what the references
   show. If it looks wrong next to the spot photos, use
   `point_marker="filled", point_color=None` (category-coloured points with black
   outlines).
4. **`None` vs `DEFAULT`.** `None` keeps its 0.2 meaning (for example
   `edge_color=None` is the category colour). To ask for the style's default,
   leave the argument out or pass `ppp.DEFAULT`.
5. **Brackets:**
   - the default label is now plain and 0.65 × `font.size` (ggprism's 3.2 mm label)
   - the line is 1.28 pt
   - the gap is 1.3 % of the axis span
   - `font_size=None` gives the full `font.size`, and `font_weight=None` the
     theme's bold
6. **The palette changed.** `"colors"` now has ggprism's values. Colours from
   `prism_context()` change; old colours are in `"colors_classic"`.
7. **To get the old look back,** pass `style="classic"` to any function. It gives
   the 0.2 values above.

## Defaults that changed

Each row is old → new; sources are in `prism-defaults.md`.

- **Theme** (`prism_style`, `style_axes`):
  - axis and tick width 1.0 → 2.13 pt (`base_line_size × 2.134`)
  - tick-label padding 3.5 → 2.8 (x) / 1.75 (y) pt
  - `lines.linewidth` 1.5 → 2.13 pt
  - `lines.markersize` 6 → 7 pt
  - palette `"colors"` → ggprism's values
  - `style_axes`: `line_width` 1.0 → derived from `base_size`; it now also sets
    tick-label, axis-label and title size and weight
- **Columns:**
  - tint 0.3 → 1.0
  - outline: category colour 1.3 pt → black at the axis width
  - error bars: `#202020` 1 pt → black at the axis width
  - caps: 3 pt → width / 3
  - points: category colour 18 pt² with a black edge → black 24.8 pt², ggprism
    shapes
- **XY:**
  - markers: `o s ^ D v` at 6 pt → ggprism `"default"` shapes at 7.1 pt
  - line and error bars: 1.5 / 1.0 pt → axis width
  - caps: 3 pt → marker radius
- **Brackets:**
  - line 1.5 → 1.28 pt
  - font 12 pt (vertical) / `font.size` (horizontal) → 0.65 × `font.size`, plain
  - gap 2.5 % → 1.3 %
  - asterisks vertically centred
  - butt line ends
- **Legend** (`grouped_bars(legend=True)`): text bold → plain.
- **Heatmap:** no change; it already follows the theme (see `prism-defaults.md`).

## New arguments

- `style="prism" | "classic"` on every plotting function, `prism_style` and
  `style_axes`.
- `bar_dots` / `grouped_bars`:
  - `cap_width` (data units)
  - `err_direction="both" | "up"`
  - `point_marker` accepts a shape palette name or a sequence of markers
- `xy_lines`: `marker_edgecolor`; `markers` accepts a shape palette name.
- `significance_bar` / `significance_bar_h`: `font_weight`.
- `prism_style`: `base_line_size`, `minor_ticks`.
- `style_axes`: `offset`, `offset_gap`, `minor_ticks="x" | "y" | True`,
  `base_size`, `base_line_size`, `base_fontweight`.
- New public names:
  - `offset_axes(ax, which, gap)`, `prism_line_width()`
  - `get_shapes()`, `Shape`, `SHAPE_PALETTES`
  - `FILL_PALETTES`, `get_palette(..., kind="fill")`
  - `DEFAULT`, `STYLES`, `GGPLOT_LINE_PT`, `GGPLOT_TEXT_PT`

All 0.2 names, arguments and return structures are unchanged. The one type
difference: a cap is a two-point Line2D across the whisker instead of a one-point
marker. Its `get_ydata()[0]` (or `get_xdata()[0]` on a horizontal graph) is still
the interval end.

## Where the result differs from the task, and why

- **Line widths use ×2.134, not ×2.845.** ggplot2's linewidth unit is about
  0.75 mm, and a measurement of ggprism's own figure confirms it (see
  `prism-defaults.md`).
- **Bracket labels are plain, not bold,** because ggprism's `add_pvalue` default
  is `fontface = 1`. `font_weight=None` gives bold.
- **XY markers have no black outline,** because ggprism's and Prism's
  dose-response figures don't. `markers="filled"` or `marker_edgecolor="black"`
  adds one.
- **Error bars are at the axis width (2.13 pt), not ggprism's 1.07 pt.** The task
  asked for it, and Prism uses equal weights; ggprism's value is ggplot2's
  unchanged default.
- **Error bars go both ways by default.** GraphPad's documentation doesn't state a
  default direction, and ggprism draws both. `err_direction="up"` gives one-sided
  bars.
- **The offset axis and minor ticks are off by default,** as in `theme_prism()`.
  The offset axis also pushes both spines outward so they never meet at the
  corner.
- **Column width (0.6) and other geometry defaults are unchanged,** so existing
  layouts don't move.

## What PyPrism still can't do that ggprism does

- theme colour palettes (coloured axes and text)
- `guide_prism_bracket`
- plain legend text through `prism_style` alone
- `add_pvalue`'s step, nudge and shorten options and table-driven labels
- box plots and violins
- random jitter (deterministic by design)

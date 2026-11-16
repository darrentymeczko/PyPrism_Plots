# PyPrism 0.3 defaults and where they come from

PyPrism's defaults (`style="prism"`) follow ggprism, the R package that copies
GraphPad Prism's graph style. Where ggprism has no value, they follow GraphPad's
own documentation. `style="classic"` restores the PyPrism 0.2 values.

**References** (read in October 2026):
- **ggprism source:** https://github.com/csdaw/ggprism, `master`, version 1.0.7.9000:
  - `R/theme_prism.R`
  - `R/guide_prism_offset.R`, `R/guide_prism_minor.R`
  - `R/add_pvalue.R`, `R/geom_pvalue.R`, `R/create_bracket.R`
  - `data-raw/*-palettes.yml`
- **ggprism vignettes:** https://csdaw.github.io/ggprism/ (`ggprism`, `axes`,
  `pvalues`) and the README figures.
- **GraphPad Prism user guide:** https://www.graphpad.com/guides/prism/latest/user-guide/,
  plus FAQ 1742 ("Creating a column bar graph").

## Unit conversion

| ggplot2 quantity | Points | Why |
|---|---|---|
| Text `size` (mm) and `element_text(size)` (pt) | mm × 72.27/25.4 = mm × **2.845**; theme sizes are already pt | ggplot2 `.pt` |
| `linewidth` / `size` of lines | × **2.134** (72.27/25.4 × 72/96) | ggplot2 multiplies by `.pt` to get R's `lwd`, and `lwd = 1` is 1/96 inch, so one unit is about 0.75 mm. This is not the ×2.845 the task assumed. Measured check: ggprism's README figure (120 dpi, `base_size = 16`) has a 4 px = 2.4 pt axis line; ×2.134 predicts 2.44 pt, ×2.845 would give 3.25 pt. |
| Point `size` | diameter = 0.75 × (size × 2.845 + stroke × 3.78 / 2) | R draws `pch` 16 at radius 0.375 × font size; ggplot2 sets the font size from size and stroke (default `stroke = 0.5`) |

## Theme (`prism_style`, `style_axes`)

The values below are for `base_size = 14`; every size scales with `base_size`.

| Element | PyPrism default | ggprism / Prism value and source | Difference |
|---|---|---|---|
| Axis line width | `base_line_size × 2.134` = **2.13 pt** | `line = element_line(linewidth = base_line_size)`, `base_line_size = base_size / 14` (`theme_prism.R`) | 0.2 used `base_size / 14` = 1.0 pt |
| Tick width | same as the axis line | `axis.ticks = element_line()` inherits `line` | |
| Tick colour | black | `axisColor` `#000000` (`themes.yml`, `black_and_white`) | The vignette PNGs render ticks `#333333` (ggplot2's `grey20` leaking through); PyPrism uses the theme's black, as Prism does |
| Major tick length, direction | **5.6 pt** (`base_size / 2.5`), outward | `axis.ticks.length = unit(base_size / 2.5, "pt")`; measured 15 px at 192 dpi | |
| Minor tick length | **2.8 pt** (`base_size / 5`) | `prism.ticks.length = unit(base_size / 5, "pt")` | |
| Tick label size, weight | 13.3 pt (0.95 × base), bold black | `axis.text = element_text(size = rel(0.95))`, `base_fontface = "bold"` | |
| Tick label padding | x 2.8 pt, y 1.75 pt | `axis.text.x` margin `t = 0.8 × base / 4`, `axis.text.y` margin `r = 0.5 × base / 4` | 0.2 used Matplotlib's 3.5 pt |
| Axis title | 14 pt bold, 8.4 pt from the labels | `axis.title`, margin `base_size × 0.6` | |
| Plot title | 16.8 pt bold, 14 pt pad | `plot.title = element_text(size = rel(1.2), margin(b = base_size))` | |
| Font | Arial (`base_family`) | `base_family = "sans"`; Prism uses Arial | The vignette PNGs were rendered with DejaVu Sans, which is wider |
| Grid, top/right spines | none | `panel.grid = element_blank()`, no `panel.border` | |
| Legend | no frame or background, text 0.8 × base | `legend.background = element_blank()`, `legend.text = element_text(size = rel(0.8), face = "plain")`, `legend.title = element_blank()` | No rcParam sets the legend weight on its own, so `prism_style` legends are bold. `grouped_bars(legend=True)` and the gallery pass `prop={"weight": "normal"}`. |
| Plain lines (`ax.plot`) | axis line width | ggprism's dose-response example: `geom_smooth` linewidth 1 = 2.13 pt | 0.2 used 1.5 × the axis width |
| Default palette | ggprism `"colors"` | `prism_colour_pal("colors")` | 0.2 used PyPrism's own `"colors"`, now `"colors_classic"` |

## Axis guides

| Element | PyPrism default | ggprism value and source | Difference |
|---|---|---|---|
| Offset axis | off; `style_axes(offset="x" / "y" / True)` | `guide_prism_offset`: the line runs from the first to the last break (`draw_prism_offset`). It is opt-in; `theme_prism()` alone draws the normal axis. The README's showcase plot opts in (`guides(y = "prism_offset_minor")`). | ggprism gets the gap between the axes from ggplot2's axis expansion. PyPrism moves the bottom and left spines outward by one major tick length (`offset_gap`), so the axes stay apart even when bars start on the axis. |
| Minor ticks | off; `minor_ticks="x" / "y" / True` | `guide_prism_minor`: ggplot2's default minor breaks (one between majors); length `prism.ticks.length` | On log axes: 2-9 in every decade, as ggprism's log example `minor_breaks` |

## Columns (`bar_dots`, `grouped_bars`)

| Element | PyPrism default | ggprism / Prism value and source | Difference |
|---|---|---|---|
| Column fill | solid palette colour (`tint=1.0`) | ggprism examples: `stat_summary(geom = "col")` with `scale_fill_prism` / `fill = dose`, solid | 0.2 used a 30 % tint |
| Column outline | black, axis line width | ggprism examples: `colour = "black", linewidth = 0.9` (1.92 pt, about the 2.13 pt axis) | |
| Column width | 0.6 (unchanged) | ggplot2 `geom_col` width 0.9 | Geometry defaults are kept so existing layouts don't move. The comparison gallery passes `width=0.9`. |
| Bars start on the axis line | the baseline (0) is a sticky edge, so autoscaling starts the value axis there | ggprism examples: `scale_y_continuous(expand = c(0, 0))` | Unchanged from 0.2 |
| Centre and error | mean ± SD | Prism: "By default, Prism chooses to plot the mean with standard deviation (SD)" (FAQ 1742) | Unchanged |
| Error bar colour | black | ggprism examples: `geom_errorbar()` default colour black | 0.2: `#202020` |
| Error bar width | axis line width (2.13 pt) | ggprism examples use the `geom_errorbar` default, 0.5 = 1.07 pt (measured 3 px at 192 dpi) | **Deliberately heavier.** The task asked for the axis width, and Prism draws error bars and axes at the same weight. ggprism's 1.07 pt is ggplot2's default, not a choice ggprism made. |
| Cap length | **a third of the column width**, in data units (`cap_width`) | ggprism examples: `geom_errorbar(width = 0.3)` on 0.9-wide columns; measured 49 px at 192 dpi | 0.2 used `capsize=3` pt markers, still available with `capsize=` |
| Error bar direction | both (`err_direction="both"`; `"up"` keeps only the half pointing away from the baseline) | Prism offers Both / Above only / Below only (user guide, "Error bars"), but neither GraphPad's guide nor its FAQs state the default. ggprism's column examples draw both. | New argument |
| Points | black, solid, no outline | ggprism examples: `geom_jitter(aes(shape = dose))` black (ggplot2 default colour), solid `pch` 16/15/17 | 0.2: category colour with a 0.5 pt black edge |
| Point size | 24.8 pt² (5.0 pt diameter) | ggprism examples: `geom_jitter(size = 2)` | 0.2: 18 / 14 pt² |
| Point shapes | ggprism `"default"` shape palette, one shape per column (`bar_dots`) or per series (`grouped_bars`) | `prism_shape_pal("default")`: circle, square, triangle, diamond, asterisk, plus, cross, circle-plus, square-cross; ggprism examples map shape to the column | 0.2: circles only |
| Outlined shapes | `point_marker="filled"` gives `pch` 21-25 with a black 0.71 pt edge | `prism_shape_pal("filled")`, ggplot2 default `stroke = 0.5` | |
| Jitter | evenly spaced, total width 0.25 (unchanged) | ggprism examples use random `geom_jitter(width = 0.1-0.2)` | Deterministic on purpose, so redraws match |
| Centre line (`shape="line"`) | axis line width | | 0.2: 2 pt |
| Legend handles | Patch: solid fill, black edge at the axis width | | |

## XY lines (`xy_lines`)

| Element | PyPrism default | ggprism / Prism value and source | Difference |
|---|---|---|---|
| Markers | ggprism `"default"` shapes per series, filled with the series colour, no outline | ggprism README dose response: `scale_shape_prism()`, `geom_point(size = 3)` in the series colour; the Prism screenshot in ggprism's repo has no outlines either | The task asked for black-outlined markers. Both references show unoutlined markers, so outlines are opt-in: `markers="filled"` or `marker_edgecolor="black"`. |
| Marker size | 7.1 pt (ggplot2 `size = 3`) | ggprism README dose response | 0.2: 6 pt |
| Line | series colour, axis line width | `geom_smooth` linewidth 1 = 2.13 pt | 0.2: 1.5 pt |
| Error bars | series colour, axis line width, caps as wide as the marker | Prism colours XY error bars like the data set; there is no ggprism example | 0.2: 1 pt, 3 pt caps |

## Significance brackets (`significance_bar`, `significance_bar_h`)

| Element | PyPrism default | ggprism value and source | Difference |
|---|---|---|---|
| Tip length | 3 % of the axis span | `add_pvalue(tip.length = 0.03)` (fraction of the panel) | Unchanged |
| Line width | **1.28 pt** | `bracket.size = 0.6` × 2.134 | 0.2: 1.5 pt |
| Line ends | butt | `GeomPValue` `lineend = "butt"` | |
| Label size | **0.65 × `font.size`** (9.1 pt at `base_size = 14`) | `label.size = 3.2` mm × 2.845 = 9.1 pt | ggprism's size is fixed. The task asked for it to follow the theme, so PyPrism scales it by `font.size / 14`. `font_size=None` uses `font.size`. 0.2: 12 pt (vertical), `font.size` (horizontal). |
| Label weight | **plain** | `GeomPValue` default `fontface = 1` (plain); the pvalues vignette figures show plain labels | **The task asked for bold; the reference is plain.** `font_weight=None` uses the theme's bold. |
| Label gap | 1.3 % of the axis span | `data_text$y + (y.range * 0.013)` (`geom_pvalue.R`) | 0.2: 2.5 % |
| Asterisk labels | vertically centred on the label point (`*` to `****`) | `data$vjust[label %in% c("*", "**", "***", "****")] <- 0.5` | Other labels sit on the point (`va="bottom"`, ggprism `vjust = 0`) |
| Horizontal label | horizontal, to the right | ggprism rotates flipped labels to 270° | Kept horizontal (the 0.2 behaviour) for readability next to spot photos |

## Heatmap

`heatmap()` has no ggprism counterpart. It already took everything from the
theme: tick-label weight from `font.weight`, colour-bar outline from
`axes.linewidth`, colour-bar ticks from `ytick.*`. Under `prism_style` these are
bold labels, a 2.13 pt outline and 5.6 pt ticks. No defaults changed.

## Palettes

| Item | PyPrism 0.3 | Source |
|---|---|---|
| Colour palettes | all 65 of ggprism's (`PALETTES`, `get_palette(name)`) | `data-raw/colour-palettes.yml` = `prism_colour_pal` |
| Fill palettes | all 45 of ggprism's (`FILL_PALETTES`, `get_palette(name, kind="fill")`) | `data-raw/fill-palettes.yml` = `prism_fill_pal` |
| Shape palettes | `default`, `filled`, `complete` (`SHAPE_PALETTES`, `get_shapes`) | `data-raw/shape-palettes.yml` = `prism_shape_pal`; `pch` mapped to Matplotlib markers |
| `"colors"` | ggprism's exact 20 colours (`#0000FF`, `#FF0000`, `#00C000`, ...) | 0.2's values are `"colors_classic"` |
| `colorblind_safe`, `floral`, `stained_glass` | ggprism's values | 0.2's values are kept as `<name>_classic` |
| `warm`, `cool`, `muted`, `monochrome` | unchanged (PyPrism's own) | |

## What PyPrism still can't do that ggprism does

- **Theme colour palettes** (`theme_prism(palette = "winter_bright")` recolours
  the axes, text and background). PyPrism's theme is always black on white.
- **`guide_prism_bracket`** (category axis drawn as brackets under each group).
- **Plain legend text under `prism_style`**, because Matplotlib has no legend
  weight rcParam (see the legend row).
- **`add_pvalue`'s table-driven features:** `step.increase`, `bracket.nudge.y`,
  `bracket.shorten`, and labels taken from a results table. Call
  `significance_bar` once per comparison instead.
- **Box plots and violins**, the most common ggprism examples.
- **Random jitter.** PyPrism's jitter is deterministic by design.

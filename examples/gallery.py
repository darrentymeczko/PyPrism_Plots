"""Generate example galleries in examples/.

* ``pyprism_gallery.png``: the theme with plain Matplotlib and Seaborn plots.
* ``pyprism_plots_gallery.png``: PyPrism's own plotting functions on one
  fixed-size page with axes placed in inches.
* ``prism_comparison.png``: PyPrism's defaults next to the matching ggprism
  vignette figures, drawn at the same physical size. The ggprism images are
  downloaded on first use into ``examples/_ggprism_reference/`` (not committed;
  ggprism is GPL-3).
"""

import urllib.request
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import pyprism_plot as ppp

HERE = Path(__file__).parent


def theme_gallery() -> Path:
    import seaborn as sns

    rng = np.random.default_rng(24)
    groups = [rng.normal(center, 0.55, 18) for center in (2.2, 3.0, 4.1)]
    colors = ppp.get_palette("colorblind_safe", 3)

    with ppp.prism_context(palette="colorblind_safe", base_size=12):
        fig, axes = plt.subplots(1, 2, figsize=(9, 4))

        means = [values.mean() for values in groups]
        errors = [values.std(ddof=1) / np.sqrt(len(values)) for values in groups]
        axes[0].bar(range(3), means, yerr=errors, color=colors, capsize=4)
        for index, values in enumerate(groups):
            jitter = rng.normal(index, 0.045, len(values))
            axes[0].scatter(
                jitter, values, color="white", edgecolor="black", s=22, zorder=3
            )
        axes[0].set_xticks(range(3), ["Control", "Drug A", "Drug B"])
        axes[0].set(ylabel="Response (a.u.)", title="Mean + SEM")
        ppp.significance_bar(axes[0], 0, 2, 5.0, "**")

        x = np.linspace(0, 8, 40)
        frame = {
            "Time": np.tile(x, 3),
            "Response": np.concatenate(
                [
                    1 - np.exp(-x / rate) + i * 0.15
                    for i, rate in enumerate((2.8, 2.0, 1.3))
                ]
            ),
            "Group": np.repeat(["Control", "Drug A", "Drug B"], len(x)),
        }
        sns.lineplot(data=frame, x="Time", y="Response", hue="Group", ax=axes[1])
        axes[1].set(title="Kinetic response", ylabel="Normalized response")
        axes[1].legend(title=None)

        fig.tight_layout()
        output = HERE / "pyprism_gallery.png"
        fig.savefig(output, dpi=180)
    plt.close(fig)
    return output


def plots_gallery() -> Path:
    rng = np.random.default_rng(7)
    page_w, page_h = 11.0, 7.0

    def place(left: float, bottom: float, width: float, height: float):
        """Add axes at an exact position given in inches."""
        return fig.add_axes(
            [left / page_w, bottom / page_h, width / page_w, height / page_h]
        )

    with ppp.prism_context(base_size=9, tight_save=False, explicit_fonts=True):
        fig = plt.figure(figsize=(page_w, page_h))

        # Column plot with replicates and a bracket.
        ax = place(0.7, 4.1, 2.6, 2.4)
        reps = [rng.normal(m, 0.35, 6) for m in (2.0, 3.1, 4.2)]
        ppp.bar_dots(ax, reps, labels=["WT", "ura3Δ", "his3Δ"], ylim=(0, 5.6))
        ppp.style_axes(ax, axis_text_angle=45, axis_text_ha="right")
        ppp.significance_bar(ax, 0, 2, 4.7, "**", font_size=None)
        ax.set(ylabel="Growth score", title="bar_dots")

        # Horizontal bars, median with IQR passed as absolute bounds.
        ax = place(4.4, 4.1, 2.6, 2.4)
        reps = [rng.normal(m, 0.4, 5) for m in (3.8, 2.5, 1.2)]
        medians = [np.median(r) for r in reps]
        iqr = np.array([np.percentile(r, [25, 75]) for r in reps]).T
        ppp.bar_dots(
            ax,
            reps,
            orientation="horizontal",
            centre=medians,
            bounds=iqr,
            labels=["WT", "mutA", "mutB"],
        )
        ppp.significance_bar_h(ax, 0, 2, 5.0, "***")
        ax.set(xlabel="Spot intensity", title="horizontal, median + IQR")

        # Dot and line shapes.
        ax = place(8.1, 4.1, 2.6, 2.4)
        reps = [rng.normal(m, 0.3, 8) for m in (1.5, 2.2)]
        ppp.bar_dots(ax, reps, shape="dot", positions=[0, 1])
        ppp.bar_dots(
            ax, reps, shape="line", positions=[2.2, 3.2], width=0.4, colors="black"
        )
        ax.set_xticks([0, 1, 2.2, 3.2], ["A", "B", "A", "B"])
        ax.set(title='shape="dot" / "line"')

        # Grouped columns with a legend placed by the caller.
        ax = place(0.7, 0.7, 2.6, 2.4)
        data = [
            [rng.normal(m, 0.25, 4) for m in row]
            for row in ((2.0, 2.6, 3.0), (1.0, 1.9, 0.0), (0.4, 1.1, 2.5))
        ]
        data[1][2] = None  # a missing slot stays empty
        result = ppp.grouped_bars(ax, data, cluster_labels=["30 °C", "37 °C", "39 °C"])
        ax.legend(
            handles=result.legend_handles,
            labels=["WT", "mutA", "mutB"],
            loc="upper right",
            ncols=3,
            fontsize=7,
        )
        ax.set(ylabel="Growth score", title="grouped_bars", ylim=(0, 4.2))

        # XY lines on a log axis with replicate points behind.
        ax = place(4.4, 0.7, 2.6, 2.4)
        dilution = np.array([1, 1e-1, 1e-2, 1e-3, 1e-4])
        replicate_sets = {
            name: np.clip(
                np.log10(dilution)[:, None] * slope + 5 + rng.normal(0, 0.2, (5, 3)),
                0,
                None,
            )
            for name, slope in (("WT", 0.6), ("mutA", 1.1))
        }
        ppp.xy_lines(
            ax,
            dilution,
            {name: reps.mean(axis=1) for name, reps in replicate_sets.items()},
            err={
                name: reps.std(axis=1, ddof=1) for name, reps in replicate_sets.items()
            },
            points=replicate_sets,
            jitter=0.15,
            logx=True,
        )
        ax.invert_xaxis()
        ax.legend()
        ax.set(xlabel="Dilution", ylabel="Spot score", title="xy_lines")

        # Heatmap with significance stars and a colour bar at an exact spot.
        ax = place(7.9, 0.7, 2.1, 2.4)
        cax = place(10.1, 0.7, 0.12, 2.4)
        matrix = rng.normal(0, 1, (4, 4))
        matrix[2, 1] = np.nan
        stars = np.where(
            np.abs(matrix) > 1.2, "**", np.where(abs(matrix) > 0.7, "*", "")
        )
        ppp.heatmap(
            ax,
            matrix,
            row_labels=["WT", "mutA", "mutB", "mutC"],
            col_labels=["YPD", "Gal", "Raf", "Gly"],
            annotations=stars,
            cbar_ax=cax,
            cbar_label="log2 FC",
        )
        ax.set_title("heatmap")

        output = HERE / "pyprism_plots_gallery.png"
        fig.savefig(output, dpi=150)
    plt.close(fig)
    return output


# ToothGrowth and sleep from R's datasets package, as used in the vignettes.
TOOTH_GROWTH = {
    ("OJ", 0.5): [15.2, 21.5, 17.6, 9.7, 14.5, 10.0, 8.2, 9.4, 16.5, 9.7],
    ("OJ", 1.0): [19.7, 23.3, 23.6, 26.4, 20.0, 25.2, 25.8, 21.2, 14.5, 27.3],
    ("OJ", 2.0): [25.5, 26.4, 22.4, 24.5, 24.8, 30.9, 26.4, 27.3, 29.4, 23.0],
    ("VC", 0.5): [4.2, 11.5, 7.3, 5.8, 6.4, 10.0, 11.2, 11.2, 5.2, 7.0],
    ("VC", 1.0): [16.5, 16.5, 15.2, 17.3, 22.5, 17.3, 13.6, 14.5, 18.8, 15.5],
    ("VC", 2.0): [23.6, 18.5, 33.9, 25.5, 26.4, 32.5, 26.7, 21.5, 23.3, 29.5],
}
SLEEP = {
    "1": [0.7, -1.6, -0.2, -1.2, -0.1, 3.4, 3.7, 0.8, 0.0, 2.0],
    "2": [1.9, 0.8, 1.1, 0.1, -0.1, 4.4, 5.5, 1.6, 4.6, 3.4],
}
# The README's dose-response data: replicates per agonist concentration.
AGONIST = [1e-10, 1e-8, 3e-8, 1e-7, 3e-7, 1e-6, 3e-6, 1e-5, 3e-5, 1e-4, 3e-4]
DOSE_RESPONSE = {
    "No inhibitor": [
        [0, 3, 2],
        [11, 33, 25],
        [125, 141, 160],
        [190, 218, 196],
        [258, 289, 345],
        [322, 353, 328],
        [354, 359, 369],
        [348, 298, 372],
        [],
        [412, 378, 399],
        [],
    ],
    "Inhibitor": [
        [3, 5, 4],
        [],
        [11, 25, 28],
        [52, 55, 61],
        [80, 77, 44],
        [171, 195, 246],
        [289, 230, 243],
        [272, 333, 310],
        [359, 306, 297],
        [352, 320, 365],
        [389, 338],
    ],
}

GGPRISM = "https://csdaw.github.io/ggprism/articles/"
README_FIGURES = "https://raw.githubusercontent.com/csdaw/ggprism/master/man/figures/"
# name: (url, dpi, crop box (left, top, right, bottom) in pixels or None)
REFERENCES = {
    "column": (
        GGPRISM + "pvalues_files/figure-html/unnamed-chunk-18-1.png",
        192,
        (0, 0, 700, 672),
    ),
    "grouped": (
        GGPRISM + "pvalues_files/figure-html/unnamed-chunk-23-1.png",
        192,
        None,
    ),
    "xy": (README_FIGURES + "README-ex2-2.png", 120, None),
    "horizontal": (
        GGPRISM + "pvalues_files/figure-html/unnamed-chunk-8-1.png",
        192,
        (0, 672, 672, 1344),
    ),
    "offset": (
        GGPRISM + "ggprism_files/figure-html/unnamed-chunk-5-1.png",
        192,
        (0, 576, 672, 1152),
    ),
}
CAPTIONS = {
    "column": "ggprism pvalues vignette: columns, mean ± SD, brackets",
    "grouped": "ggprism pvalues vignette: grouped boxes (it has no grouped columns)",
    "xy": "ggprism README: dose response (it has no XY error bars)",
    "horizontal": "ggprism pvalues vignette: coord_flip() with a bracket",
    "offset": 'ggprism vignette: guide = "prism_offset"',
}


def _reference(name: str):
    url, dpi, crop = REFERENCES[name]
    cache = HERE / "_ggprism_reference"
    cache.mkdir(exist_ok=True)
    path = cache / f"{name}.png"
    if not path.exists():
        urllib.request.urlretrieve(url, path)
    image = plt.imread(path)
    if crop is not None:
        left, top, right, bottom = crop
        image = image[top:bottom, left:right]
    return image, dpi


def _toothgrowth_by_dose() -> list[np.ndarray]:
    return [
        np.array(TOOTH_GROWTH[("OJ", d)] + TOOTH_GROWTH[("VC", d)])
        for d in (0.5, 1.0, 2.0)
    ]


def _draw_column(ax) -> None:
    ppp.bar_dots(ax, _toothgrowth_by_dose(), width=0.9, labels=["0.5", "1", "2"])
    ax.set(ylim=(0, 40), yticks=range(0, 41, 5), xlabel="factor(dose)", ylabel="len")
    ppp.significance_bar(ax, 0, 1, 34, "****")
    ppp.significance_bar(ax, 0, 2, 37, "****")


def _draw_grouped(ax) -> None:
    data = [
        [np.array(TOOTH_GROWTH[(supp, d)]) for supp in ("OJ", "VC")]
        for d in (0.5, 1.0, 2.0)
    ]
    result = ppp.grouped_bars(
        ax,
        data,
        series_width=0.4,
        cluster_labels=["0.5", "1", "2"],
        series_labels=["OJ", "VC"],
    )
    ax.set(ylim=(0, 42), xlabel="factor(dose)", ylabel="len")
    for x, y, p in ((0, 24, "0.01908"), (1, 30, "0.00312"), (2, 36.5, "1")):
        ppp.significance_bar(ax, x - 0.2, x + 0.2, y, f"p = {p}", height=0)
    ax.legend(
        handles=result.legend_handles,
        loc="center left",
        bbox_to_anchor=(1.02, 0.5),
        prop={"weight": "normal"},
    )


def _draw_xy(ax) -> None:
    centres, sds = {}, {}
    for name, sets in DOSE_RESPONSE.items():
        centres[name] = [np.mean(v) if v else np.nan for v in sets]
        sds[name] = [np.std(v, ddof=1) if len(v) > 1 else np.nan for v in sets]
    ppp.xy_lines(
        ax,
        AGONIST,
        centres,
        err=sds,
        points=DOSE_RESPONSE,
        colors=ppp.get_palette("winter_bright", 2),
        logx=True,
    )
    ax.set(
        xlim=(1e-10, 1e-3),
        xticks=[10.0**k for k in range(-10, -2)],
        ylim=(-100, 500),
        yticks=range(-100, 501, 100),
        xlabel="[Agonist], M",
    )
    ax.legend(loc="upper left", prop={"weight": "normal"})
    ppp.style_axes(ax, minor_ticks="x", offset="both")


def _draw_horizontal(ax) -> None:
    ppp.bar_dots(
        ax,
        [np.array(SLEEP["1"]), np.array(SLEEP["2"])],
        positions=[1, 2],
        orientation="horizontal",
        labels=["1", "2"],
    )
    ax.set(xlim=(-2, 6.5), ylim=(0.4, 2.6), xlabel="extra", ylabel="group")
    ppp.significance_bar_h(ax, 1, 2, 5.8, "0.0794", height=0.25)


def _draw_offset(ax) -> None:
    ppp.bar_dots(ax, _toothgrowth_by_dose(), width=0.9, labels=["0.5", "1", "2"])
    ax.set(ylim=(0, 40), xlabel="factor(dose)", ylabel="len")
    ppp.style_axes(ax, offset="y")


def comparison_gallery() -> Path:
    """Draw PyPrism's defaults beside the matching ggprism figures."""
    rows = [
        ("column", _draw_column, 3.0),
        ("grouped", _draw_grouped, 3.0),
        ("xy", _draw_xy, 3.9),
        ("horizontal", _draw_horizontal, 2.6),
        ("offset", _draw_offset, 2.6),
    ]
    images = {name: _reference(name) for name, _, _ in rows}
    # Each row is as tall as its reference image. The PyPrism axes get the same
    # height minus ggplot-like margins, so line weights compare at equal size.
    left_w, gap, top_pad = 5.4, 0.3, 0.35
    sizes = {
        n: (im.shape[1] / dpi, im.shape[0] / dpi) for n, (im, dpi) in images.items()
    }
    page_w = left_w + gap + max(w for w, _ in sizes.values()) + 0.2
    page_h = sum(h + top_pad for _, h in sizes.values()) + 0.4
    with ppp.prism_context(base_size=14, tight_save=False):
        fig = plt.figure(figsize=(page_w, page_h))
        right = (left_w + gap) / page_w
        title_y = 1 - 0.25 / page_h
        fig.text(0.02, title_y, "PyPrism 0.3 defaults", fontsize=13)
        fig.text(right, title_y, "ggprism (same physical size)", fontsize=13)
        bottom = page_h - 0.4
        for name, draw, axes_w in rows:
            ref_w, ref_h = sizes[name]
            bottom -= ref_h + top_pad
            ax = fig.add_axes(
                [
                    1.0 / page_w,
                    (bottom + 0.85) / page_h,
                    axes_w / page_w,
                    (ref_h - 1.15) / page_h,
                ]
            )
            draw(ax)
            ref = fig.add_axes([right, bottom / page_h, ref_w / page_w, ref_h / page_h])
            ref.imshow(images[name][0], interpolation="none")
            ref.set_axis_off()
            fig.text(
                right,
                (bottom + ref_h + 0.05) / page_h,
                CAPTIONS[name],
                fontsize=9,
                fontweight="normal",
                color="0.35",
            )
        output = HERE / "prism_comparison.png"
        fig.savefig(output, dpi=192)
    plt.close(fig)
    return output


if __name__ == "__main__":
    for path in (theme_gallery(), plots_gallery(), comparison_gallery()):
        print(f"Saved {path}")

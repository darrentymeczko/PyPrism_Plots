"""Generate example galleries in examples/.

* ``pyprism_gallery.png``: the theme with plain Matplotlib and Seaborn plots.
* ``pyprism_plots_gallery.png``: PyPrism's own plotting functions on one
  fixed-size page with axes placed in inches.
"""

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


if __name__ == "__main__":
    for path in (theme_gallery(), plots_gallery()):
        print(f"Saved {path}")

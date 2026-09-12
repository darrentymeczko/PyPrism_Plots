"""Generate a small gallery in examples/pyprism_gallery.png."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

import pyprism_plot as ppp

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
            [1 - np.exp(-x / rate) + i * 0.15 for i, rate in enumerate((2.8, 2.0, 1.3))]
        ),
        "Group": np.repeat(["Control", "Drug A", "Drug B"], len(x)),
    }
    sns.lineplot(data=frame, x="Time", y="Response", hue="Group", ax=axes[1])
    axes[1].set(title="Kinetic response", ylabel="Normalized response")
    axes[1].legend(title=None)

    fig.tight_layout()
    output = Path(__file__).with_name("pyprism_gallery.png")
    fig.savefig(output, dpi=180)
    print(f"Saved {output}")

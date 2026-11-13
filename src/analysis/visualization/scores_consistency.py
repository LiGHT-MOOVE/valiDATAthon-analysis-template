import textwrap

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle

from analysis.helpers import (
    criterion_name,
    export_figure,
)
from analysis.visualization.helpers import (
    finalize_figure,
    style_x_axes,
    style_y_axes,
)
from analysis.visualization.style import PlotStyle

MODELS_DIFF_SCORE_COLORS = {
    "% Same score": "#217b3b",
    "% 1 point apart": "#96bf6b",
    "% 2 points apart": "#9d56a8",
    "% ≥3 points apart": "#772b83",
}
categories = [
    "% Same score",
    "% 1 point apart",
    "% 2 points apart",
    "% ≥3 points apart",
]


def plot_gap_between_scores(
    subfig,
    far_apart_pct_all,
    style: PlotStyle,
    criteria,
    countries,
    friendly_criteria,
):

    ax1 = subfig.subplots()

    # 5 criteria, 3 countries per criterion
    y_positions = np.arange(len(criteria))
    countries = far_apart_pct_all["country"].dropna().unique()
    country_offsets = np.linspace(
        -0.1 * len(countries),
        0.1 * len(countries),
        len(countries),
    )

    for country, offset in zip(countries, country_offsets):
        plot_df = (
            far_apart_pct_all[far_apart_pct_all["country"] == country]
            .set_index("criterion")
            .reindex(criteria)
        )

        y = y_positions + offset
        left = np.zeros(len(criteria))
        for category in categories:
            values = plot_df[category].to_numpy()
            bars = ax1.barh(
                y,
                values,
                left=left,
                height=0.25,
                label=category if country == countries[0] else None,
                color=MODELS_DIFF_SCORE_COLORS[category],
            )

            # Percentage labels
            for bar, value in zip(bars, values):
                if value >= 5:
                    ax1.text(
                        bar.get_x() + bar.get_width() / 2,
                        bar.get_y() + bar.get_height() / 2,
                        f"{value:.1f}",
                        ha="center",
                        va="center",
                        fontsize=style.font_value,
                        color="white"
                        if category in ("Same score", "≥3 points apart")
                        else "black",
                    )

            left += values

    style_x_axes(
        ax1,
        xlim=(0, 100),
        xticks=np.arange(0, 110, 25),
        xlabels=[f"{x}%" for x in np.arange(0, 101, 25)],
    )

    ax1.set_ylim(
        y_positions[-1] + 0.4,
        y_positions[0] - 0.4,
    )
    style_y_axes(
        ax1,
        yticks=y_positions,
        ylabels=[
            textwrap.fill(
                criterion_name(criterion, friendly_criteria),
                width=15,
                break_long_words=False,
                break_on_hyphens=False,
            )
            for criterion in criteria
        ],
    )

    ax1.set_ylabel("")

    sns.despine(
        ax=ax1,
        left=True,
    )
    ax1.tick_params(axis="x", colors="#888888", labelsize=style.font_tick)

    ax1.spines["bottom"].set_color("#888888")
    for country, offset in zip(countries, country_offsets):
        for i in range(len(criteria)):
            ax1.text(
                102,
                y_positions[i] + offset,
                country,
                ha="left",
                va="center",
                fontsize=style.font_value,
                color=style.country_colors.get(country, "#808080"),
                fontweight="bold",
            )

    finalize_figure(
        subfig,
        xlabel="Evaluations (%)",
        title="a  Gap between the two scores given to the same response",
    )


def plot_legend(footer, style: PlotStyle):
    legend_handles = [
        Line2D(
            [0],
            [0],
            marker="s",
            linestyle="None",
            markersize=7,
            markerfacecolor=MODELS_DIFF_SCORE_COLORS[category],
            markeredgecolor=MODELS_DIFF_SCORE_COLORS[category],
            label=category,
        )
        for category in categories
    ]

    ax_legend = footer.subplots()
    ax_legend.set_axis_off()

    ax_legend.legend(
        handles=legend_handles,
        labels=categories,
        loc="center",
        ncol=4,
        frameon=False,
        fontsize=style.font_legend,
    )


def plot_scores_on_both_sides(
    subfig,
    criterion_scores,
    style: PlotStyle,
    criteria,
    friendly_criteria,
):
    scores = [2, 1, 0, -1, -2]
    score_labels = ["+2", "+1", "0", "-1", "-2"]

    cmap = LinearSegmentedColormap.from_list(
        "gray_diverging",
        [
            "#ffffff",
            "#acacac",
            "#4a4a4a",
        ],
    )
    axes = subfig.subplots(
        nrows=2,
        ncols=3,
    )

    axes = axes.flatten()

    for ax, criterion in zip(axes, criteria):
        heatmap_pct = criterion_scores[criterion]

        annotations = heatmap_pct.map(lambda x: f"{x:.1f}")

        sns.heatmap(
            heatmap_pct,
            annot=annotations,
            fmt="",
            cmap=cmap,
            linewidths=1,
            linecolor="white",
            xticklabels=score_labels,
            yticklabels=score_labels,
            ax=ax,
            cbar=False,
        )

        # Diagonal = same score on both sides
        for i in range(len(scores)):
            ax.add_patch(
                Rectangle(
                    (i, i),
                    1,
                    1,
                    fill=False,
                    edgecolor="black",
                    linewidth=1.2,
                    linestyle="--",
                )
            )

        ax.set_title(
            criterion_name(criterion, friendly_criteria),
            fontsize=style.font_label,
            fontweight="bold",
        )

        ax.set_xlabel("Left score", fontsize=style.font_label)
        ax.set_ylabel("Right score", fontsize=style.font_label)

    # Hide unused 6th subplot
    axes[-1].axis("off")

    finalize_figure(
        subfig,
        title="b  The same response, scored on both sides (% of evaluations)",
    )


def plot_consistency_of_scores_over_same_response_main_figure(
    gap_between_scores, criteria, countries, config, friendly_criteria
):
    style = config.style
    scores_gap = gap_between_scores["Scores gap"]
    criterion_scores = {
        criterion: gap_between_scores[criterion] for criterion in criteria
    }
    fig = plt.figure(figsize=(16, max(8, 4 * len(countries))), layout="constrained")

    fig4_left, fig4_subfig2 = fig.subfigures(
        2,
        1,
        height_ratios=[1, 1],
    )

    fig4_subfig1, fig4_legend_footer = fig4_left.subfigures(
        2,
        1,
        height_ratios=[10, 1],
    )
    plot_gap_between_scores(
        fig4_subfig1,
        scores_gap,
        style,
        criteria,
        countries,
        friendly_criteria,
    )
    plot_legend(fig4_legend_footer, style)
    plot_scores_on_both_sides(
        fig4_subfig2, criterion_scores, style, criteria, friendly_criteria
    )

    export_figure(
        fig,
        "consistency_of_scores_over_same_response",
        config,
    )
    plt.close(fig)

import textwrap

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from analysis.helpers import (
    criterion_name,
    export_figure,
)
from analysis.visualization.helpers import (
    add_alternating_rows_sub_figures,
    create_country_handles,
    finalize_figure,
    get_countries_offset,
    style_x_axes,
    style_y_axes,
)
from analysis.visualization.style import PlotStyle


def plot_side_chosen_effect(
    subfig,
    country_stats,
    style: PlotStyle,
    countries,
):
    country_stats = (
        country_stats.set_index("reviewer_country").reindex(countries).reset_index()
    )

    country_stats["y_pos"] = np.arange(len(country_stats))
    plotted_countries = country_stats["reviewer_country"].dropna().unique()

    country_colors = {
        country: style.country_colors[country]
        for country in plotted_countries
        if country in style.country_colors
    }
    country_handles = create_country_handles(country_colors)

    grid7 = subfig.add_gridspec(
        2,
        1,
        height_ratios=[0.8, 1],
        hspace=0,
    )

    ax = subfig.add_subplot(grid7[0, 0])

    subfig.subplots_adjust(
        left=0.2,
        right=0.8,
        top=0.9,
    )
    for _, row in country_stats.iterrows():
        color = country_colors[row["reviewer_country"]]
        country = row["reviewer_country"]
        xerr_lower = row["percentage_right"] - row["ci_lower"]
        xerr_upper = row["ci_upper"] - row["percentage_right"]

        ax.errorbar(
            x=row["percentage_right"],
            y=row["y_pos"],
            xerr=[[xerr_lower], [xerr_upper]],
            fmt="o",
            capsize=3,
            markersize=6,
            color=color,
            ecolor=color,
            label=country,
            zorder=2,
        )
        ax.text(
            1,
            row["y_pos"],
            f"{row['percentage_right']:.2f}",
            transform=ax.get_yaxis_transform(),
            ha="left",
            va="center",
            fontsize=style.font_value,
            fontweight="bold",
            color=style.country_colors[row.reviewer_country],
        )

    style_x_axes(
        ax,
        xlim=(40, 60),
        xticks=np.arange(40, 65, 5),
        vertical_center_line=50,
        vertical_line_style="-",
        xlabels=[f"{x:.0f}%" for x in np.arange(40, 65, 5)],
        vertical_line_color="black",
    )

    style_y_axes(
        ax,
        yticks=country_stats["y_pos"],
        ylabels=country_stats["reviewer_country"],
    )
    for label in ax.get_yticklabels():
        label.set_color(style.country_colors[label.get_text()])
        label.set_fontweight("bold")

    ax.set_ylabel("")

    ax.set_xlabel(
        textwrap.fill(
            "Choosing the right-hand response (%, 95% CI)",
            width=45,
        ),
        fontsize=style.font_label,
    )
    ax_legend = subfig.add_subplot(grid7[1, 0])
    ax_legend.set_axis_off()

    ax_legend.legend(
        handles=country_handles,
        loc="center",
        ncol=1,
        frameon=False,
        fontsize=style.font_legend,
        handlelength=1,
        handletextpad=0.4,
        columnspacing=1.5,
    )
    finalize_figure(
        subfig,
        title="a  Side chosen",
        xlabel="",
    )


def plot_position_effect(
    subfig,
    position_effect,
    style: PlotStyle,
    criteria,
    countries,
    friendly_criteria,
):
    ax = subfig.subplots()

    criterion_positions = {criterion: i for i, criterion in enumerate(criteria[::-1])}
    country_offsets = get_countries_offset(len(countries))

    for country, offset in zip(countries, country_offsets):
        plot_df = position_effect[position_effect["reviewer_country"] == country].copy()

        y = np.array([criterion_positions[c] + offset for c in plot_df["criterion"]])

        x = plot_df["mean"].to_numpy()

        xerr = np.vstack(
            [
                x - plot_df["ci_lower"].to_numpy(),
                plot_df["ci_upper"].to_numpy() - x,
            ]
        )

        ax.errorbar(
            x=x,
            y=y,
            xerr=xerr,
            fmt="o",
            capsize=3,
            markersize=6,
            color=style.country_colors[country],
            ecolor=style.country_colors[country],
            label=country,
            zorder=2,
        )
        for yi, emmean in zip(y, x):
            ax.text(
                1,
                yi,
                f"{emmean:.2f}",
                transform=ax.get_yaxis_transform(),
                ha="left",
                va="center",
                fontsize=style.font_value,
                fontweight="bold",
                color=style.country_colors[country],
            )

    style_x_axes(
        ax,
        xlim=(-0.3, 0.3),
        xticks=np.arange(-0.3, 0.35, 0.1),
        vertical_center_line=0,
        vertical_line_style="-",
        vertical_line_color="black",
    )

    style_y_axes(
        ax,
        yticks=range(len(criteria)),
        ylabels=[
            textwrap.fill(
                criterion_name(criterion, friendly_criteria),
                width=15,
                break_long_words=False,
                break_on_hyphens=False,
            )
            for criterion in criteria[::-1]
        ],
    )
    finalize_figure(
        subfig,
        title="b  Position effect on score",
        xlabel=textwrap.fill(
            "Score  on the right minus score in the left (95% CI)",
            width=45,
        ),
        ylabel="",
    )

    add_alternating_rows_sub_figures(
        [ax],
        n_rows=len(criteria),
    )


def plot_chosen_response_scored_higher(
    subfig,
    chosen_scored_higher,
    style: PlotStyle,
    criteria,
    countries,
):
    ax = subfig.subplots()

    y_positions = np.arange(len(criteria))
    country_offsets = get_countries_offset(len(countries))

    for country, offset in zip(countries, country_offsets):
        plot_df = (
            chosen_scored_higher[chosen_scored_higher["country"] == country]
            .set_index("criterion")
            .reindex(criteria)
        )
        x = plot_df["mean"].to_numpy()

        lower = plot_df["mean"].to_numpy() - plot_df["ci_low"].to_numpy()

        upper = plot_df["ci_high"].to_numpy() - plot_df["mean"].to_numpy()

        ax.errorbar(
            x,
            y_positions + offset,
            xerr=[lower, upper],
            fmt="o",
            capsize=4,
            label=country,
            color=style.country_colors[country],
            ecolor=style.country_colors[country],
        )
        for yi, value in zip(y_positions + offset, x):
            ax.text(
                1,
                yi,
                f"{value * 100:.0f}",
                transform=ax.get_yaxis_transform(),
                ha="left",
                va="center",
                fontsize=style.font_value,
                fontweight="bold",
                color=style.country_colors[country],
                clip_on=False,
            )

    ax.set_ylabel("")

    style_x_axes(
        ax,
        xlim=(0, 0.9),
        xticks=np.arange(0, 0.9, 0.2),
        vertical_center_line=0.5,
        vertical_line_style="-",
        xlabels=[f"{x * 100:.0f}%" for x in np.arange(0, 0.9, 0.2)],
        vertical_line_color="black",
    )
    style_y_axes(
        ax,
        yticks=y_positions,
        ylabels=[],
    )
    finalize_figure(
        subfig,
        title="c  Chosen response scored higher",
        xlabel=textwrap.fill(
            "Evaluations where the chosen response scored higher on that criterion (%, 95% CI)",
            width=45,
        ),
    )

    add_alternating_rows_sub_figures(
        [ax],
        n_rows=len(criteria),
    )


def plot_effect_of_response_display_position_supp_figure(
    position_effect: pd.DataFrame,
    preferred_side_stats: pd.DataFrame,
    chosen_scored_higher: pd.DataFrame,
    criteria,
    countries,
    config,
    friendly_criteria,
):
    style = config.style
    fig = plt.figure(figsize=(16, 8), layout="none")  # check height

    supp1_subfig1, supp1_subfig2, supp1_subfig3 = fig.subfigures(
        1,
        3,
    )
    plot_side_chosen_effect(supp1_subfig1, preferred_side_stats, style, countries)
    plot_position_effect(
        supp1_subfig2,
        position_effect,
        style,
        criteria,
        countries,
        friendly_criteria,
    )
    plot_chosen_response_scored_higher(
        supp1_subfig3,
        chosen_scored_higher,
        style,
        criteria,
        countries,
    )
    export_figure(
        fig,
        "effect_of_response_display_position",
        config,
    )
    plt.close(fig)

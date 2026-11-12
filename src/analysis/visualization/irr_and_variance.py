import textwrap

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.lines import Line2D

from analysis.helpers import (
    criterion_name,
    export_figure,
)
from analysis.visualization.helpers import (
    add_alternating_rows_sub_figures,
    create_country_handles,
    finalize_figure,
    get_countries_offset,
    handle_model_label_and_category,
    style_x_axes,
    style_y_axes,
)
from analysis.visualization.style import PlotStyle

VARIANCE_COLORS = {
    "model": "#217b3b",
    "vignette": "#9d56a8",
    "answer": "#96bf6b",
    "reviewer": "#772b83",
    "residual": "#dddcd5",
}


def plot_irr_by_criterion(
    subfig,
    agreement_plot_data_by_criterion,
    style: PlotStyle,
    criteria,
    countries,
    friendly_criteria,
):
    y_positions = np.arange(len(criteria))
    ax1 = subfig.subplots()
    country_offsets = get_countries_offset(len(countries))

    for statistic_key, alpha in [
        ("gwet_ac2", 1.0),
        ("krippendorff_alpha", 0.45),
    ]:
        statistic_data = agreement_plot_data_by_criterion[
            agreement_plot_data_by_criterion["statistic_key"] == statistic_key
        ]

        for country, offset in zip(
            countries,
            country_offsets,
        ):
            plot_data = (
                statistic_data[statistic_data["country"] == country]
                .set_index("criterion")
                .reindex(criteria)
            )

            x = plot_data["coeff"].to_numpy()

            xerr = np.vstack(
                [
                    x - plot_data["conf_low"].to_numpy(),
                    plot_data["conf_high"].to_numpy() - x,
                ]
            )

            ax1.errorbar(
                x,
                y_positions + offset,
                xerr=xerr,
                fmt="o",
                capsize=3,
                markersize=6,
                label=country,
                linewidth=1.2,
                zorder=3,
                color=style.country_colors[country],
                markerfacecolor="white"
                if statistic_key == "krippendorff_alpha"
                else style.country_colors[country],
                alpha=alpha,
            )
            if statistic_key == "gwet_ac2":
                text_x = 0.95
            elif statistic_key == "krippendorff_alpha":
                text_x = -0.18

            for yi, value in zip(y_positions + offset, x):
                ax1.text(
                    text_x,
                    yi,
                    f"{value:.2f}",
                    ha="left",
                    va="center",
                    fontsize=style.font_value,
                    fontweight="bold",
                    color=style.country_colors[country],
                    clip_on=False,
                    zorder=5,
                )

    ax1.invert_yaxis()

    style_x_axes(
        ax1, xlim=(-0.2, 1), xticks=np.arange(0, 1.1, 0.2), vertical_center_line=0
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

    finalize_figure(
        subfig,
        title="a  Inter-rater agreement by criterion",
        xlabel="Agreement coefficient (95% CI)",
        ylabel="",
    )

    add_alternating_rows_sub_figures(
        ax1,
        n_rows=len(criteria),
    )


def plot_irr_by_model(
    subfig,
    agreement_plot_data_by_model,
    style: PlotStyle,
    models,
    model_categories,
    countries,
):
    country_offsets = get_countries_offset(len(countries))

    # ac2 by model being judged
    y_positions = np.arange(len(models))

    ax2 = subfig.subplots()

    for statistic_key, alpha in [
        ("gwet_ac2", 1.0),
        ("krippendorff_alpha", 0.35),
    ]:
        agreement_plot_data_by_model_statistic = agreement_plot_data_by_model[
            agreement_plot_data_by_model["statistic_key"] == statistic_key
        ]

        for country, offset in zip(
            countries,
            country_offsets,
        ):
            plot_data = (
                agreement_plot_data_by_model_statistic[
                    agreement_plot_data_by_model_statistic["country"] == country
                ]
                .set_index("model")
                .reindex(models)
            )

            x = plot_data["coeff"].to_numpy()

            xerr = np.vstack(
                [
                    x - plot_data["conf_low"].to_numpy(),
                    plot_data["conf_high"].to_numpy() - x,
                ]
            )

            ax2.errorbar(
                x,
                y_positions + offset,
                xerr=xerr,
                fmt="o",
                capsize=3,
                markersize=6,
                label=country,
                linewidth=1.2,
                color=style.country_colors[country],
                markeredgecolor=style.country_colors[country],
                markerfacecolor="white"
                if statistic_key == "krippendorff_alpha"
                else style.country_colors[country],
                alpha=alpha,
                zorder=3,
            )

            if statistic_key == "gwet_ac2":
                text_x = 0.95
            elif statistic_key == "krippendorff_alpha":
                text_x = -0.18

            for yi, value in zip(y_positions + offset, x):
                ax2.text(
                    text_x,
                    yi,
                    f"{value:.2f}",
                    ha="left",
                    va="center",
                    fontsize=style.font_value,
                    fontweight="bold",
                    color=style.country_colors[country],
                    clip_on=False,
                    zorder=5,
                )

    style_x_axes(
        ax2, xlim=(-0.2, 1), xticks=np.arange(0, 1.1, 0.2), vertical_center_line=0
    )

    style_y_axes(ax2, yticks=y_positions, ylabels=[])
    handle_model_label_and_category(ax2, models, model_categories, wrap_model=True)

    finalize_figure(
        subfig,
        title="b  Inter-rater agreement by model",
        xlabel="Agreement coefficient (95% CI)",
        ylabel="",
    )

    add_alternating_rows_sub_figures(
        ax2,
        n_rows=len(models),
    )


def plot_variance_component(
    subfig,
    variance_components,
    style: PlotStyle,
    criteria,
    models,
    model_categories,
    countries,
    friendly_criteria,
):
    components = [
        "model",
        "answer",
        "reviewer",
        "vignette",
        "residual",
    ]
    component_labels = {
        "model": "Response source (model or human)",
        "answer": "Care plan",
        "vignette": "Case",
        "reviewer": "Reviewer",
        "residual": "Residual",
    }

    axes = subfig.subplots(
        nrows=len(criteria),
        ncols=1,
        sharex=True,
    )

    for ax, criterion in zip(axes, criteria):
        plot_df = variance_components[
            variance_components["criterion"] == criterion
        ].copy()

        plot_df["country"] = pd.Categorical(
            plot_df["country"],
            categories=countries,
            ordered=True,
        )

        plot_df = plot_df.sort_values("country")

        y = np.arange(len(plot_df))
        left = np.zeros(len(plot_df))

        for component in components:
            values = plot_df[component].to_numpy()
            bars = ax.barh(
                y,
                values,
                left=left,
                height=0.65,
                label=component_labels[component],
                zorder=2,
                color=VARIANCE_COLORS[component],
            )

            # Percentage labels inside sufficiently large segments
            for bar, value in zip(bars, values):
                if value >= 3:
                    ax.text(
                        bar.get_x() + bar.get_width() / 2,
                        bar.get_y() + bar.get_height() / 2,
                        f"{value}",
                        ha="center",
                        va="center",
                        fontsize=style.font_value,
                        color="white" if component != "residual_%" else "black",
                    )

            left += values

        ax.set_yticks(y)
        ax.set_yticklabels(
            plot_df["country"],
            fontweight="bold",
        )
        ax.tick_params(axis="y", length=0)
        for tick, country in zip(ax.get_yticklabels(), plot_df["country"]):
            tick.set_color(style.country_colors[country])

        ax.set_title(
            criterion_name(criterion, friendly_criteria),
            loc="left",
            x=-0.1,
            fontsize=style.font_label,
            fontweight="bold",
        )

        ax.set_xticks([0, 0.5, 1, 1.5])
        ax.set_xticklabels(["0", "0.5", "1.0", "1.5"], fontsize=style.font_tick)

        ax.grid(
            axis="x",
            linestyle="--",
            alpha=0.4,
            zorder=1,
        )

        sns.despine(
            ax=ax,
            left=True,
            bottom=False,
        )

    finalize_figure(
        subfig,
        title="c  Source of variation in scores",
        xlabel="Variance (score points squared)",
    )
    return axes


def plot_legend(footer, plotted_countries, style: PlotStyle, axes):

    country_colors = {
        country: style.country_colors[country]
        for country in plotted_countries
        if country in style.country_colors
    }
    country_handles = create_country_handles(country_colors)

    statistic_handles = [
        Line2D(
            [0],
            [0],
            marker="o",
            linestyle="None",
            markerfacecolor="black",
            markeredgecolor="black",
            markersize=7,
            alpha=1.0,
            label="Gwet's AC2",
        ),
        Line2D(
            [0],
            [0],
            marker="o",
            linestyle="None",
            markerfacecolor="white",
            markeredgecolor="black",
            markersize=7,
            alpha=0.35,
            label="Krippendorff's α",
        ),
    ]

    handles, labels = axes[0].get_legend_handles_labels()

    # Replace the single ax_legend with:
    footer_left, footer_right = footer.subfigures(
        1,
        2,
        width_ratios=[2, 1],
    )

    ax_statistics_legend = footer_left.subplots()
    ax_other_legend = footer_right.subplots()

    ax_statistics_legend.set_axis_off()
    ax_other_legend.set_axis_off()

    # Statistics legend below the left 2/3
    ax_statistics_legend.legend(
        handles=country_handles + statistic_handles,
        loc="center",
        ncol=5,
        frameon=False,
        fontsize=style.font_legend,
    )

    # Other legend below the right 1/3
    handles, labels = axes[0].get_legend_handles_labels()

    ax_other_legend.legend(
        handles=handles,
        labels=labels,
        loc="center",
        ncol=2,
        frameon=False,
        fontsize=style.font_legend,
    )


def plot_irr_and_variance_main_figure(
    irr_by_criterion: pd.DataFrame,
    irr_by_model: pd.DataFrame,
    variance_components: pd.DataFrame,
    criteria,
    countries,
    models,
    config,
    friendly_criteria,
    model_categories,
):
    plotted_countries = irr_by_model["country"].dropna().unique()
    style = config.style
    fig = plt.figure(figsize=(19, max(9, 6 * len(countries))), layout="constrained")

    # Main content and a full-width legend footer
    fig3_main, fig3_footer = fig.subfigures(
        2,
        1,
        height_ratios=[12, 1],
    )

    # Main content: 2/3 left, 1/3 right
    fig3_main_left, fig3_main_subfig3 = fig3_main.subfigures(
        1,
        2,
        width_ratios=[2, 1],
    )

    fig3_subfig1, fig3_subfig2 = fig3_main_left.subfigures(
        2,
        1,
        height_ratios=[1, 1.4],
    )
    plot_irr_by_criterion(
        fig3_subfig1, irr_by_criterion, style, criteria, countries, friendly_criteria
    )
    plot_irr_by_model(
        fig3_subfig2,
        irr_by_model,
        style,
        models,
        model_categories,
        countries,
    )
    axes = plot_variance_component(
        fig3_main_subfig3,
        variance_components,
        style,
        criteria,
        models,
        model_categories,
        countries,
        friendly_criteria,
    )

    plot_legend(fig3_footer, plotted_countries, style, axes)
    export_figure(
        fig,
        "irr_and_variance",
        config,
    )
    plt.close(fig)

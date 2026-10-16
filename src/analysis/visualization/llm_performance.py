import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from analysis.helpers import (
    criterion_name,
    export_figure,
)
from analysis.visualization.helpers import (
    add_alternating_rows_sub_figures,
    finalize_figure,
    get_countries_offset,
    handle_model_label_and_category,
    style_x_axes,
    style_y_axes,
)
from analysis.visualization.style import PlotStyle


def plot_adjusted_mean_score(
    subfig,
    adjusted_means,
    style: PlotStyle,
    criteria,
    countries,
    models,
    friendly_criteria,
    model_categories,
):
    axes = subfig.subplots(
        1,
        len(criteria),
        sharey=True,
        squeeze=False,
    )[0]
    country_offsets = get_countries_offset(len(countries))
    for ax, criterion in zip(axes, criteria):
        plot_df = adjusted_means[adjusted_means["criterion"] == criterion].copy()

        model_positions = {model: i for i, model in enumerate(models)}

        for country, offset in zip(countries, country_offsets):
            country_df = plot_df[plot_df["reviewer_country"] == country]

            y = [model_positions[model] + offset for model in country_df["model"]]

            ax.errorbar(
                x=country_df["emmean"],
                y=y,
                xerr=[
                    country_df["emmean"] - country_df["lower.CL"],
                    country_df["upper.CL"] - country_df["emmean"],
                ],
                fmt="o",
                capsize=3,
                color=style.country_colors[country],
                label=country,
                zorder=2,
            )
            # Add emmean value at the right end of the axis
            for yi, emmean in zip(y, country_df["emmean"]):
                ax.text(
                    2.02,
                    yi,
                    f"{emmean:.2f}",
                    ha="left",
                    va="center",
                    fontsize=style.font_value,
                    fontweight="bold",
                    color=style.country_colors[country],
                )

        style_x_axes(
            ax,
            xlim=(0, 2),
            xticks=np.arange(0, 2.1, 0.5),
            vertical_center_line=0,
            style=style,
        )
        ax.set_title(
            criterion_name(criterion, friendly_criteria),
            fontweight="bold",
            fontsize=style.font_title,
        )
        ax.hlines(
            y=0.5,
            xmin=0,
            xmax=2.15,
            color="black",
            linewidth=0.8,
            zorder=5,
        )
    style_y_axes(axes[0], yticks=range(len(models)), style=style)
    handle_model_label_and_category(axes[0], models, model_categories)

    for ax in axes:
        ax.tick_params(
            axis="y",
            which="both",
            labelleft=False,
            labelright=False,
        )

    finalize_figure(
        subfig,
        title="\na   Adjusted mean score (95% CI)",
        xlabel="Adjusted mean score (scale -2 to +2)",
        style=style,
    )

    add_alternating_rows_sub_figures(axes, n_rows=len(models), style=style)


def plot_llm_performance_main_figure(
    adjusted_means: pd.DataFrame,
    safety_comparisons: pd.DataFrame,
    criteria,
    countries,
    models,
    config,
    friendly_criteria,
    model_categories,
):
    style = config.style

    fig = plt.figure(figsize=(18, 18), layout="constrained")

    fig1_subfig1, fig1_subfig2, fig1_subfig3, fig1_footer = fig.subfigures(
        4,
        1,
        height_ratios=[8, 4, 6, 1],
    )
    plot_adjusted_mean_score(
        fig1_subfig1,
        adjusted_means,
        style,
        criteria,
        countries,
        models,
        friendly_criteria,
        model_categories,
    )
    export_figure(
        fig,
        "llm_performance",
        config,
    )
    plt.close(fig)

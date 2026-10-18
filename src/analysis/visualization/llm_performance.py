import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle

from analysis.helpers import (
    criterion_name,
    export_figure,
)
from analysis.visualization.data_processing import (
    prepare_human_non_human_safety_comparisons_data,
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


def plot_adjusted_mean_score(
    subfig,
    adjusted_means,
    style: PlotStyle,
    criteria,
    countries,
    models,
    friendly_criteria,
    model_categories,
    is_human,
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
        if is_human:
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


def plot_safety_pairwise_comparison(
    subfig,
    country_pairwise_safety_non_human,
    style: PlotStyle,
    criteria,
    countries,
    models,
    friendly_criteria,
    model_categories,
):
    without_human_order = [model for model in models if model != "Human Benchmark"]
    axes = subfig.subplots(
        1,
        len(countries),
        sharey=True,
        squeeze=False,
    )[0]
    cmap = LinearSegmentedColormap.from_list(
        "gray_diverging",
        ["#4a4a4a", "#ffffff", "#4a4a4a"],
    )

    limit = country_pairwise_safety_non_human["estimate"].abs().max()

    norm = TwoSlopeNorm(
        vmin=-limit,
        vcenter=0,
        vmax=limit,
    )

    for i, (ax, country) in enumerate(zip(axes, countries)):
        country_df = country_pairwise_safety_non_human.loc[
            country_pairwise_safety_non_human["reviewer_country"] == country
        ]

        heatmap_data = country_df.pivot(
            index="model_a",
            columns="model_b",
            values="estimate",
        )

        heatmap_data = heatmap_data.combine_first(-heatmap_data.T)
        heatmap_data = heatmap_data.reindex(
            index=without_human_order,
            columns=without_human_order,
        )

        # True where the 95% CI excludes zero
        significant_pairs = country_df.assign(
            significant=((country_df["lower.CL"] > 0) | (country_df["upper.CL"] < 0))
        ).pivot(
            index="model_a",
            columns="model_b",
            values="significant",
        )

        # Significance is unchanged when reversing a comparison
        significant_pairs = significant_pairs.combine_first(significant_pairs.T)

        significant_cells = (
            significant_pairs.reindex(
                index=heatmap_data.index, columns=heatmap_data.columns
            )
            .fillna(False)
            .to_numpy(dtype=bool)
        )

        sns.heatmap(
            heatmap_data,
            fmt=".2f",
            cmap=cmap,
            norm=norm,  # Same colour scale across countries
            linewidths=0.5,
            cbar=False,
            ax=ax,
        )
        for row in range(heatmap_data.shape[0]):
            for col in range(heatmap_data.shape[1]):
                if row == col:
                    continue

                value = heatmap_data.iloc[row, col]

                if pd.notna(value):
                    star = "*" if significant_cells[row, col] else ""

                    if value > 0:
                        value_text = f"+{value:.2f}"
                    elif value < 0:
                        value_text = f"−{abs(value):.2f}"
                    else:
                        value_text = "0.00"

                    ax.text(
                        col + 0.5,
                        row + 0.5,
                        f"{value_text}{star}",
                        ha="center",
                        va="center",
                        fontsize=style.font_value,
                    )
        for i in range(len(models)):
            ax.add_patch(
                Rectangle(
                    (i, i),
                    1,
                    1,
                    facecolor="white",
                    edgecolor="black",
                    linewidth=1.5,
                    zorder=4,
                    linestyle="--",
                )
            )

        ax.set_title(country, pad=18, fontsize=style.font_title, fontweight="bold")
        ax.hlines(
            y=1.06,
            xmin=0,
            xmax=1,
            transform=ax.transAxes,
            color=style.country_colors[country],
            linewidth=5,
            clip_on=False,
        )

        ax.set_xlabel("")
        ax.set_ylabel("")
        ax.xaxis.tick_top()

        ax.set_xticklabels(
            [model for model in heatmap_data.columns],
            rotation=0,
            ha="center",
            fontsize=style.font_tick,
        )
        ax.set_yticklabels(heatmap_data.index, rotation=0, fontsize=style.font_tick)

        ax.tick_params(axis="both", which="both", length=0, labelsize=style.font_tick)
        ax.tick_params(axis="x", pad=8, labelsize=style.font_tick)

    finalize_figure(
        subfig,
        title="\nc   Safety: pairwise comparison between models",
        xlabel="Difference in adjusted mean safety score, row model - column model (*: 95% CI excludes 0)",
    )


def plot_safety_pairwise_comparison_human_reference(
    subfig,
    human_safety,
    style: PlotStyle,
    criteria,
    countries,
    models,
    friendly_criteria,
    model_categories,
):
    models_without_human = [m for m in models if m != "Human Benchmark"]
    human_safety = (
        human_safety.copy()
        .set_index("model")
        .reindex(models_without_human)
        .rename_axis("model")
        .reset_index()
    )
    axes = subfig.subplots(
        1,
        len(countries),
        sharey=True,
        squeeze=False,
    )[0]

    for ax, country in zip(axes, countries):
        plot_df = human_safety[human_safety["reviewer_country"] == country].copy()

        model_positions = {model: i for i, model in enumerate(models_without_human)}

        y = [model_positions[model] for model in plot_df["model"]]
        y = np.asarray(y)
        significant = (plot_df["lower.CL"] > 0) | (plot_df["upper.CL"] < 0)

        # 95% CI excludes 0 → filled
        ax.errorbar(
            x=plot_df.loc[significant, "estimate"],
            y=y[significant],
            xerr=[
                plot_df.loc[significant, "estimate"]
                - plot_df.loc[significant, "lower.CL"],
                plot_df.loc[significant, "upper.CL"]
                - plot_df.loc[significant, "estimate"],
            ],
            fmt="o",
            capsize=3,
            color=style.country_colors[country],
            markerfacecolor=style.country_colors[country],
            markeredgecolor=style.country_colors[country],
            markersize=6,
            zorder=2,
        )

        # 95% CI includes 0 → hollow
        ax.errorbar(
            x=plot_df.loc[~significant, "estimate"],
            y=y[~significant],
            xerr=[
                plot_df.loc[~significant, "estimate"]
                - plot_df.loc[~significant, "lower.CL"],
                plot_df.loc[~significant, "upper.CL"]
                - plot_df.loc[~significant, "estimate"],
            ],
            fmt="o",
            capsize=3,
            color=style.country_colors[country],
            markerfacecolor="white",
            markeredgecolor=style.country_colors[country],
            markersize=6,
            zorder=2,
        )
        ax.axvline(
            -0.2,
            linestyle="--",
            linewidth=1,
            alpha=0.6,
            color="red",
        )
        # Add estimate value at the right end of the axis
        for yi, estimate in zip(y, plot_df["estimate"]):
            ax.text(
                1.22,
                yi,
                f"{estimate:.2f}",
                ha="left",
                va="center",
                fontsize=style.font_value,
                fontweight="bold",
                color=style.country_colors[country],
                clip_on=False,
            )

        ax.set_title(
            country,
            fontweight="bold",
            color=style.country_colors[country],
            pad=28,
            fontsize=style.font_title,
        )

        style_x_axes(
            ax,
            xlim=(-0.2, 1.2),
            xticks=np.arange(-0.2, 1.3, 0.2),
            vertical_center_line=0,
            vertical_line_style="-",
        )
        # add note above the zero vertical line
        # x uses data coordinates; y uses axes coordinates
        transform = ax.get_xaxis_transform()

        ax.annotate(
            "← favors human",
            xy=(0, 1.02),
            xycoords=transform,
            xytext=(-5, 0),
            textcoords="offset points",
            ha="right",
            va="bottom",
            fontsize=8,
            color="grey",
            annotation_clip=False,
        )

        ax.annotate(
            "favors model →",
            xy=(0, 1.02),
            xycoords=transform,
            xytext=(5, 0),
            textcoords="offset points",
            ha="left",
            va="bottom",
            fontsize=8,
            color="grey",
            annotation_clip=False,
        )

    style_y_axes(
        axes[0],
        yticks=range(len(models_without_human)),
        ylabels=[f"{model} vs Human" for model in models_without_human],
    )

    for ax in axes[1:]:
        ax.tick_params(axis="y", labelleft=False, labelsize=style.font_tick)

    finalize_figure(
        subfig,
        title="\nb   Safety: each model vs human benchmark",
        xlabel="Difference in adjusted mean safety score  (95% CI)",
        note="",
    )

    add_alternating_rows_sub_figures(
        axes,
        n_rows=len(models_without_human),
    )


def plot_legend(
    footer,
    style: PlotStyle,
):
    country_handles = create_country_handles(style.country_colors)
    legend_handles_filled_hollow = [
        Line2D(
            [0],
            [0],
            marker="o",
            linestyle="None",
            markerfacecolor="black",
            markeredgecolor="black",
            markersize=6,
            label="filled = 95% CI excludes 0",
        ),
        Line2D(
            [0],
            [0],
            marker="o",
            linestyle="None",
            markerfacecolor="white",
            markeredgecolor="black",
            markersize=6,
            label="hollow = 95% CI includes 0",
        ),
        Line2D(
            [0, 1],
            [0, 0],
            color="red",
            linestyle="--",
            linewidth=1.5,
            label="Pre-specified non-inferiority margin (-0.2)",
        ),
    ]

    legend_ax = footer.subplots()
    legend_ax.set_axis_off()

    legend_ax.legend(
        handles=country_handles + legend_handles_filled_hollow,
        loc="center",
        ncol=6,
        frameon=False,
        fontsize=style.font_legend,
        labelcolor="#666666",
        handlelength=2,
        columnspacing=1.4,
    )


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
    is_human = "Human Benchmark" in models
    if is_human:
        fig1_subfig1, fig1_subfig2, fig1_subfig3, fig1_footer = fig.subfigures(
            4,
            1,
            height_ratios=[8, 4, 6, 1],
        )
    else:
        fig1_subfig1, fig1_subfig2, fig1_footer = fig.subfigures(
            3,
            1,
            height_ratios=[8, 6, 1],
        )
        fig1_subfig3 = None

    country_pairwise_safety_non_human, human_safety = (
        prepare_human_non_human_safety_comparisons_data(safety_comparisons, is_human)
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
        is_human,
    )
    if is_human:
        plot_safety_pairwise_comparison_human_reference(
            fig1_subfig2,
            human_safety,
            style,
            criteria,
            countries,
            models,
            friendly_criteria,
            model_categories,
        )
    plot_safety_pairwise_comparison(
        fig1_subfig3 if is_human else fig1_subfig2,
        country_pairwise_safety_non_human,
        style,
        criteria,
        countries,
        models,
        friendly_criteria,
        model_categories,
    )
    plot_legend(fig1_footer, style)
    export_figure(
        fig,
        "llm_performance",
        config,
    )
    plt.close(fig)

import matplotlib.pyplot as plt
import pandas as pd

from analysis.helpers import (
    export_figure,
)
from analysis.visualization.llm_performance import plot_llm_performance_main_figure
from analysis.visualization.load import load_figure_inputs
from utils.print_console import print_step, print_success


def plot_h2h_comparison_main_figure(
    win_loss: pd.DataFrame,
    criteria,
    countries,
    models,
    config,
):
    fig = plt.figure(figsize=(18, 18), layout="none")

    n_countries = len(countries)

    # Each country gets a header row followed by a plot row
    grid = fig.add_gridspec(
        2 * n_countries + 1,
        2,
        height_ratios=[0.12, 1] * n_countries + [0.08],
        width_ratios=[1, 1],
        left=0.10,
        right=0.97,
        bottom=0.08,
        top=0.94,
        hspace=0.18,
        wspace=0.18,
    )

    export_figure(
        fig,
        "h2h_comparison",
        config,
    )
    plt.close(fig)


def plot_irr_and_variance_main_figure(
    irr_by_criterion: pd.DataFrame,
    irr_by_model: pd.DataFrame,
    variance_components: pd.DataFrame,
    criteria,
    countries,
    models,
    config,
):
    fig = plt.figure(figsize=(19, 15), layout="constrained")

    # Main content and a full-width legend footer
    fig3_main, fig3_footer = fig.subfigures(
        2,
        1,
        height_ratios=[12, 1],
    )

    # Main content: 2/3 left, 1/3 right
    fig3_main_left, fig3_main_subfig3 = fig.subfigures(
        1,
        2,
        width_ratios=[2, 1],
    )

    fig3_subfig1, fig3_subfig2 = fig3_main_left.subfigures(
        2,
        1,
        height_ratios=[1, 1.4],
    )

    export_figure(
        fig,
        "irr_and_variance",
        config,
    )
    plt.close(fig)


def plot_consistency_of_scores_over_same_response_main_figure(
    gap_between_scores: pd.DataFrame,
    criteria,
    countries,
    models,
    config,
):

    fig = plt.figure(figsize=(16, 13), layout="constrained")

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

    export_figure(
        fig,
        "consistency_of_scores_over_same_response",
        config,
    )
    plt.close(fig)


def plot_effect_of_response_display_position_supp_figure(
    position_effect: pd.DataFrame,
    criteria,
    countries,
    models,
    config,
):
    fig = plt.figure(figsize=(16, 8), layout="none")  # check height

    supp1_subfig1, supp1_subfig2, supp1_subfig3 = fig.subfigures(
        1,
        3,
    )

    export_figure(
        fig,
        "effect_of_response_display_position",
        config,
    )
    plt.close(fig)


# Analysis registry

ANALYSIS_RUNNERS = {
    "llm_performance": plot_llm_performance_main_figure,
    "h2h_comparison": plot_h2h_comparison_main_figure,
    "irr_and_variance": plot_irr_and_variance_main_figure,
    "consistency_of_scores_over_same_response": plot_consistency_of_scores_over_same_response_main_figure,
    "effect_of_response_display_position": plot_effect_of_response_display_position_supp_figure,
}


def plot_selected_figures(
    criteria,
    countries,
    models,
    config,
    friendly_criteria,
    model_categories,
) -> None:
    """Run the figures enabled in the configuration."""

    unknown_figures = set(config.analyses) - set(ANALYSIS_RUNNERS)

    if unknown_figures:
        raise ValueError(f"Unknown figures in configuration: {sorted(unknown_figures)}")

    selected_figures = [name for name, enabled in config.analyses.items() if enabled]

    if not selected_figures:
        print_success("No figures selected. Nothing to plot.")
        return

    # Validate all required files before starting any plots.
    config.validate_inputs(selected_figures)

    print_success("Selected figures: " + ", ".join(selected_figures))

    for name in selected_figures:
        print_step(f"Plotting {name.replace('_', ' ').title()}")

        inputs = load_figure_inputs(name, config)

        # Dispatch the appropriate plotting function.
        if name == "llm_performance":
            plot_llm_performance_main_figure(
                adjusted_means=inputs["adjusted_mean_score"]["Adjusted means"],
                safety_comparisons=inputs["safety_pairwise_comparisons"][
                    "Safety pairwise comparisons"
                ],
                criteria=criteria,
                countries=countries,
                models=models,
                config=config,
                friendly_criteria=friendly_criteria,
                model_categories=model_categories,
            )

        if name == "h2h_comparison":
            plot_h2h_comparison_main_figure(
                win_loss=inputs["win_loss"]["Win loss"],
                criteria=criteria,
                countries=countries,
                models=models,
                config=config,
            )

        if name == "irr_and_variance":
            plot_irr_and_variance_main_figure(
                irr_by_criterion=inputs["inter_rater_agreement"]["IRR by criterion"],
                irr_by_model=inputs["inter_rater_agreement"]["IRR by model"],
                variance_components=inputs["variance"]["Variance components"],
                criteria=criteria,
                countries=countries,
                models=models,
                config=config,
            )

        if name == "consistency_of_scores_over_same_response":
            plot_consistency_of_scores_over_same_response_main_figure(
                gap_between_scores=inputs["gap_between_scores"]["Scores gap"],
                criteria=criteria,
                countries=countries,
                models=models,
                config=config,
            )

        if name == "effect_of_response_display_position":
            plot_effect_of_response_display_position_supp_figure(
                position_effect=inputs["position_effect"]["Preferred side statistics"],
                criteria=criteria,
                countries=countries,
                models=models,
                config=config,
            )

    return

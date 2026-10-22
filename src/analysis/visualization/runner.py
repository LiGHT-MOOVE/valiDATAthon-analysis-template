from analysis.visualization.h2h_comparison import plot_h2h_comparison_main_figure
from analysis.visualization.irr_and_variance import plot_irr_and_variance_main_figure
from analysis.visualization.llm_performance import plot_llm_performance_main_figure
from analysis.visualization.load import load_figure_inputs
from analysis.visualization.response_display_position import (
    plot_effect_of_response_display_position_supp_figure,
)
from analysis.visualization.scores_consistency import (
    plot_consistency_of_scores_over_same_response_main_figure,
)
from utils.print_console import print_step, print_success

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
                h2h_matrix=inputs["win_loss"]["H2H matrices"],
                criteria=criteria,
                countries=countries,
                models=models,
                config=config,
                model_categories=model_categories,
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
                friendly_criteria=friendly_criteria,
                model_categories=model_categories,
            )

        if name == "consistency_of_scores_over_same_response":
            plot_consistency_of_scores_over_same_response_main_figure(
                gap_between_scores=inputs["gap_between_scores"],
                criteria=criteria,
                countries=countries,
                models=models,
                config=config,
                friendly_criteria=friendly_criteria,
            )

        if name == "effect_of_response_display_position":
            plot_effect_of_response_display_position_supp_figure(
                preferred_side_stats=inputs["position_effect"][
                    "Preferred side statistics"
                ],
                position_effect=inputs["position_effect"][
                    "Position effect criterion score"
                ],
                chosen_scored_higher=inputs["position_effect"][
                    "Chosen response scored higher"
                ],
                criteria=criteria,
                countries=countries,
                models=models,
                config=config,
                friendly_criteria=friendly_criteria,
            )

    return

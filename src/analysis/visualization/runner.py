from analysis.visualization.h2h_comparison import plot_h2h_comparison_main_figure
from analysis.visualization.irr_and_variance import plot_irr_and_variance_main_figure
from analysis.visualization.llm_performance import plot_llm_performance_main_figure
from analysis.visualization.load import load_figure_inputs
from analysis.visualization.prepare import (
    prepare_h2h_comparison,
    prepare_irr_and_variance,
    prepare_llm_performance,
    prepare_response_display_position,
    prepare_scores_consistency,
)
from analysis.visualization.response_display_position import (
    plot_effect_of_response_display_position_supp_figure,
)
from analysis.visualization.scores_consistency import (
    plot_consistency_of_scores_over_same_response_main_figure,
)
from utils.print_console import print_step, print_success

# Analysis registry

ANALYSIS_RUNNERS = {
    "llm_performance": (
        plot_llm_performance_main_figure,
        prepare_llm_performance,
        ("friendly_criteria", "model_categories"),
    ),
    "h2h_comparison": (
        plot_h2h_comparison_main_figure,
        prepare_h2h_comparison,
        ("model_categories",),
    ),
    "irr_and_variance": (
        plot_irr_and_variance_main_figure,
        prepare_irr_and_variance,
        ("friendly_criteria", "model_categories"),
    ),
    "consistency_of_scores_over_same_response": (
        plot_consistency_of_scores_over_same_response_main_figure,
        prepare_scores_consistency,
        ("friendly_criteria",),
    ),
    "effect_of_response_display_position": (
        plot_effect_of_response_display_position_supp_figure,
        prepare_response_display_position,
        ("friendly_criteria",),
    ),
}


def plot_selected_figures(
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

    shared_kwargs = {
        "friendly_criteria": friendly_criteria,
        "model_categories": model_categories,
    }

    for name in selected_figures:
        print_step(f"Plotting {name.replace('_', ' ').title()}")

        plot, prepare, shared_keys = ANALYSIS_RUNNERS[name]
        plot_kwargs = prepare(load_figure_inputs(name, config))

        plot(
            config=config,
            **{key: shared_kwargs[key] for key in shared_keys},
            **plot_kwargs,
        )

    return

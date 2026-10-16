import matplotlib.pyplot as plt

from analysis.helpers import (
    export_figure,
)
from utils.print_console import print_step, print_success


# Analysis runners
def plot_llm_performance_main_figure(
    df,
    criteria,
    countries,
    models,
    config,
    memory,
):
    fig = plt.figure(figsize=(18, 18), layout="constrained")

    fig1_subfig1, fig1_subfig2, fig1_subfig3, fig1_footer = fig.subfigures(
        4,
        1,
        height_ratios=[8, 4, 6, 1],
    )
    export_figure(
        fig,
        "llm_performance",
        config,
    )


def plot_h2h_comparison_main_figure(
    df,
    criteria,
    countries,
    models,
    config,
    memory,
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


def plot_irr_and_variance_main_figure(
    df,
    criteria,
    countries,
    models,
    config,
    memory,
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


def plot_consistency_of_scores_over_same_response_main_figure(
    df,
    criteria,
    countries,
    models,
    config,
    memory,
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


def plot_effect_of_response_display_position_supp_figure(
    df,
    criteria,
    countries,
    models,
    config,
    memory,
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


# Analysis registry

ANALYSIS_RUNNERS = {
    "llm_performance": plot_llm_performance_main_figure,
    "h2h_comparison": plot_h2h_comparison_main_figure,
    "irr_and_variance": plot_irr_and_variance_main_figure,
    "consistency_of_scores_over_same_response": plot_consistency_of_scores_over_same_response_main_figure,
    "effect_of_response_display_position": plot_effect_of_response_display_position_supp_figure,
}


def plot_selected_figures(
    # df,
    criteria,
    countries,
    models,
    config,
):
    """Run analyses enabled in the configuration file."""

    enabled_analyses = config.analyses

    unknown_analyses = set(enabled_analyses) - set(ANALYSIS_RUNNERS)

    if unknown_analyses:
        raise ValueError(
            f"Unknown analyses in configuration: {sorted(unknown_analyses)}"
        )

    selected_analyses = [
        (name, runner)
        for name, runner in ANALYSIS_RUNNERS.items()
        if enabled_analyses.get(name, False)
    ]

    if not selected_analyses:
        print_success("No analyses selected. Nothing to run.")
        return

    print_success(
        "Selected analyses: " + ", ".join(name for name, _ in selected_analyses)
    )

    for name, runner in selected_analyses:
        print_step(
            f"Plotting {name.replace('_', ' ').title()}",
        )

        runner(
            # df=df,
            criteria=criteria,
            countries=countries,
            models=models,
            config=config,
        )

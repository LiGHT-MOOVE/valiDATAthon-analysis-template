from analysis.helpers import (
    combine_country_results,
    export_excel,
    export_model_fits,
)
from analysis.statistics.gap_between_scores import (
    compute_same_answer_both_sides_scores,
    get_scores_gap,
)
from analysis.statistics.irr import (
    compute_agreement_by_criterion,
    compute_agreement_by_model,
)
from analysis.statistics.model_comparisons import (
    fit_mixed_models_by_country_and_criterion,
    fit_safety_pairwise_contrasts_by_country,
)
from analysis.statistics.response_position_effect import (
    count_position_effect_on_criterion_score,
    count_preferred_side_chosen,
    get_percentage_of_chosen_response_scored_higher,
)
from analysis.statistics.variance import compute_variance
from analysis.statistics.win_loss import head_to_head_data, win_loss_summary
from utils.print_console import print_step, print_success


# Analysis runners
def run_adjusted_mean_score_analysis(
    df,
    criteria,
    countries,
    models,
    config,
    memory,
):
    adjusted_means, model_fits = fit_mixed_models_by_country_and_criterion(
        df,
        criteria,
        config.order_of_models,
        memory,
    )

    export_excel(
        {
            "Adjusted means": adjusted_means,
            "Model fit diagnostics": export_model_fits(model_fits),
        },
        "adjusted_mean_score",
        config,
    )


def run_safety_pairwise_comparisons_analysis(
    df,
    criteria,
    countries,
    models,
    config,
    memory,
):
    pairwise_safety, model_fits = fit_safety_pairwise_contrasts_by_country(
        df,
    )

    export_excel(
        {
            "Safety pairwise comparisons": pairwise_safety,
            "Model fit diagnostics": export_model_fits(model_fits),
        },
        "safety_pairwise_comparisons",
        config,
    )


def run_win_loss_analysis(
    df,
    criteria,
    countries,
    models,
    config,
    memory,
):
    win_loss = win_loss_summary(df)

    head_to_head, h2h_matrix = head_to_head_data(
        df,
        win_loss,
    )

    export_excel(
        {
            "Win loss": combine_country_results(win_loss),
            "Head to head": combine_country_results(head_to_head),
            "H2H matrices": (combine_country_results(h2h_matrix, False), True),
        },
        "win_loss_analysis",
        config,
    )


def run_position_effect_analysis(
    df,
    criteria,
    countries,
    models,
    config,
    memory,
):

    preferred_side_stats = count_preferred_side_chosen(df)
    position_effect = count_position_effect_on_criterion_score(
        df,
        criteria,
    )

    chosen_scored_higher = get_percentage_of_chosen_response_scored_higher(
        df,
        criteria,
    )

    export_excel(
        {
            "Preferred side statistics": preferred_side_stats,
            "Position effect criterion score": position_effect,
            "Chosen response scored higher": chosen_scored_higher,
        },
        "preferred_side_analysis",
        config,
    )


def run_inter_rater_agreement_analysis(
    df,
    criteria,
    countries,
    models,
    config,
    memory,
):
    agreement_methods = config.irr_methods
    agreement_weight = config.irr_weight

    irr_by_criterion = compute_agreement_by_criterion(
        df,
        countries,
        criteria,
        agreement_methods,
        agreement_weight,
    )

    irr_by_model = compute_agreement_by_model(
        df,
        countries,
        criteria,
        agreement_methods,
        agreement_weight,
    )

    export_excel(
        {
            "IRR by criterion": irr_by_criterion,
            "IRR by model": irr_by_model,
        },
        "inter_rater_agreement",
        config,
    )


def run_variance_analysis(
    df,
    criteria,
    countries,
    models,
    config,
    memory,
):
    variance = compute_variance(
        df,
        countries,
        criteria,
    )

    export_excel(
        {"Variance components": variance},
        "variance_components",
        config,
    )


def run_gap_between_scores_analysis(
    df,
    criteria,
    countries,
    models,
    config,
    memory,
):
    scores = [2, 1, 0, -1, -2]

    scores_gap = get_scores_gap(
        df,
        criteria,
    )

    same_answer_scores = compute_same_answer_both_sides_scores(
        df,
        criteria,
        scores,
    )

    export_excel(
        {
            "Scores gap": scores_gap,
            **{
                criterion: (data, True)
                for criterion, data in same_answer_scores.items()
            },
        },
        "scores_gap",
        config,
    )


# Analysis registry

ANALYSIS_RUNNERS = {
    "adjusted_mean_score": run_adjusted_mean_score_analysis,
    "safety_pairwise_comparisons": run_safety_pairwise_comparisons_analysis,
    "win_loss": run_win_loss_analysis,
    "position_effect": run_position_effect_analysis,
    "inter_rater_agreement": run_inter_rater_agreement_analysis,
    "variance": run_variance_analysis,
    "gap_between_scores": run_gap_between_scores_analysis,
}


def run_selected_analyses(
    df,
    criteria,
    countries,
    models,
    config,
    memory,
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
            f"Running {name.replace('_', ' ').title()}",
        )

        runner(
            df=df,
            criteria=criteria,
            countries=countries,
            models=models,
            config=config,
            memory=memory,
        )

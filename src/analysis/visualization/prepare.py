from collections.abc import Iterable

import pandas as pd


def get_plot_values(
    *,
    country_sources: Iterable[Iterable[str]] = (),
    model_sources: Iterable[Iterable[str]] = (),
    criterion_sources: Iterable[Iterable[str]] = (),
) -> dict[str, list[str]]:
    plot_values = {}

    for key, sources in (
        ("countries", country_sources),
        ("models", model_sources),
        ("criteria", criterion_sources),
    ):
        series = [pd.Series(source, dtype="object") for source in sources]
        plot_values[key] = (
            pd.concat(series, ignore_index=True).dropna().unique().tolist()
            if series
            else []
        )

    return plot_values


def prepare_h2h_comparison(inputs):
    win_loss = inputs["win_loss"]["Win loss"]
    h2h_matrix = inputs["win_loss"]["H2H matrices"]

    plot_values = get_plot_values(
        country_sources=[
            win_loss["reviewer_country"],
            h2h_matrix["reviewer_country"],
        ],
        model_sources=[
            win_loss["Model"],
            h2h_matrix["Unnamed: 0"],
            h2h_matrix.columns.drop(["reviewer_country", "Unnamed: 0"]),
        ],
    )
    return {
        "win_loss": win_loss,
        "h2h_matrix": h2h_matrix,
        "countries": plot_values["countries"],
    }


def prepare_llm_performance(inputs):
    adjusted_means = inputs["adjusted_mean_score"]["Adjusted means"]
    safety_comparisons = inputs["safety_pairwise_comparisons"][
        "Safety pairwise comparisons"
    ]
    plot_values = get_plot_values(
        country_sources=[
            adjusted_means["reviewer_country"],
            safety_comparisons["reviewer_country"],
        ],
        model_sources=[
            adjusted_means["model"],
            safety_comparisons["model_a"],
            safety_comparisons["model_b"],
        ],
        criterion_sources=[adjusted_means["criterion"]],
    )
    return {
        "adjusted_means": adjusted_means,
        "safety_comparisons": safety_comparisons,
        "countries": plot_values["countries"],
        "models": plot_values["models"],
        "criteria": plot_values["criteria"],
    }


def prepare_irr_and_variance(inputs):
    irr_by_criterion = inputs["inter_rater_agreement"]["IRR by criterion"]
    irr_by_model = inputs["inter_rater_agreement"]["IRR by model"]
    variance_components = inputs["variance"]["Variance components"]
    plot_values = get_plot_values(
        country_sources=[
            irr_by_criterion["country"],
            irr_by_model["country"],
            variance_components["country"],
        ],
        model_sources=[
            irr_by_model["model"],
        ],
        criterion_sources=[
            irr_by_criterion["criterion"],
            variance_components["criterion"],
        ],
    )
    return {
        "irr_by_criterion": irr_by_criterion,
        "irr_by_model": irr_by_model,
        "variance_components": variance_components,
        "countries": plot_values["countries"],
        "models": plot_values["models"],
        "criteria": plot_values["criteria"],
    }


def prepare_scores_consistency(inputs):
    gap_between_scores = inputs["gap_between_scores"]
    plot_values = get_plot_values(
        country_sources=[
            gap_between_scores["Scores gap"]["country"],
        ],
        criterion_sources=[
            gap_between_scores["Scores gap"]["criterion"],
        ],
    )
    return {
        "gap_between_scores": gap_between_scores,
        "countries": plot_values["countries"],
        "criteria": plot_values["criteria"],
    }


def prepare_response_display_position(inputs):
    preferred_side_stats = inputs["position_effect"]["Preferred side statistics"]
    position_effect = inputs["position_effect"]["Position effect criterion score"]
    chosen_scored_higher = inputs["position_effect"]["Chosen response scored higher"]
    plot_values = get_plot_values(
        country_sources=[
            preferred_side_stats["reviewer_country"],
            position_effect["reviewer_country"],
            chosen_scored_higher["country"],
        ],
        criterion_sources=[
            position_effect["criterion"],
            chosen_scored_higher["criterion"],
        ],
    )
    return {
        "preferred_side_stats": preferred_side_stats,
        "position_effect": position_effect,
        "chosen_scored_higher": chosen_scored_higher,
        "countries": plot_values["countries"],
        "criteria": plot_values["criteria"],
    }

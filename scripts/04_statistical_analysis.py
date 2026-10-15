from analysis.config import REQUIRED_NON_NULL_COLUMNS, load_analysis_config
from analysis.data.load import load_dataset
from analysis.data.preprocess import prepare_data
from analysis.data.validate import (
    validate_processed_data,
)
from analysis.helpers import combine_country_results, export_excel, export_model_fits
from analysis.statistics.cache import get_cache
from analysis.statistics.descriptive import (
    get_analysis_values,
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


def main():
    analysis_config = load_analysis_config()
    analysis_dataset_path = analysis_config.dataset_path

    memory = get_cache(
        cache_dir=analysis_config.cache_dir,
        enabled=analysis_config.use_cache,
    )
    # Check that the input files exist before loading them.
    if not analysis_dataset_path.is_file():
        raise FileNotFoundError("Analysis input file not found")

    # 1. Load raw data
    print_step(1, "Load analysis data")
    reviews_df = load_dataset(analysis_dataset_path)

    # 2. Validate raw data
    print_step(2, "Validate analysis data")
    score_cols = [col for col in reviews_df.columns if col.endswith("_score")]
    validate_processed_data(reviews_df, score_cols, REQUIRED_NON_NULL_COLUMNS)

    print_step(3, "Data preparation")
    df = prepare_data(reviews_df, analysis_config)

    print_step(4, "Get analysis characteristic")
    criteria, countries, models, countries_ordered = get_analysis_values(df)

    order_of_models = analysis_config.order_of_models
    """
    print_step(5, "Adjusted mean score (95% CI)")
    adjusted_mean_by_country, adjusted_mean_by_country_fits = (
        fit_mixed_models_by_country_and_criterion(df, criteria, order_of_models, memory)
    )


    export_excel(
        {
            "Adjusted means": adjusted_mean_by_country,
            "Model fit diagnostics": export_model_fits(adjusted_mean_by_country_fits),
        },
        "adjusted_mean_score",
        analysis_config,
    )

    print_step(6, "Safety pairwise comparisons")
    country_pairwise_safety, country_fits_safety = (
        fit_safety_pairwise_contrasts_by_country(df)
    )
    export_excel(
        {
            "Safety pairwise comparisons": country_pairwise_safety,
            "Model fit diagnostics": export_model_fits(country_fits_safety),
        },
        "safety_pairwise_comparisons",
        analysis_config,
    )

    print_step(7, "Win loss analysis")

    win_loss = win_loss_summary(df)

    head_to_head, h2h_matrix = head_to_head_data(
        df,
        win_loss,
    )
    export_excel(
        {
            "Win loss": combine_country_results(win_loss),
            "Head to head": combine_country_results(head_to_head),
            "H2H matrices": combine_country_results(h2h_matrix),
        },
        "win_loss_analysis",
        analysis_config,
    )

    print_step(8, "Position effect analysis")

    preferred_side_stats = count_preferred_side_chosen(df)
    position_effect = count_position_effect_on_criterion_score(df, criteria)
    chosen_scored_higher = get_percentage_of_chosen_response_scored_higher(df, criteria)
    export_excel(
        {
            "Preferred side statistics": preferred_side_stats,
            "Position effect on criterion score": position_effect,
            "Chosen response scored higher": chosen_scored_higher,
        },
        "preferred_side_analysis",
        analysis_config,
    )
       
    print_step(9, "Inter-rater agreement and variance analysis")
    agreement_methods = analysis_config.irr_methods
    agreement_weight = analysis_config.irr_weight
    irr_by_criterion = compute_agreement_by_criterion(
        df, countries, criteria, agreement_methods, agreement_weight
    )
    irr_by_model = compute_agreement_by_model(
        df, countries, criteria, agreement_methods, agreement_weight
    )

    variance = compute_variance(
        df,
        countries,
        criteria,
    )
    export_excel(
        {
            "IRR by criterion": irr_by_criterion,
            "IRR by model": irr_by_model,
            "variance component": variance,
        },
        "irr_&_variance",
        analysis_config,
    )

 """
    print_step(10, "Gap between scores  analysis")
    scores = [2, 1, 0, -1, -2]
    scores_gap = get_scores_gap(df, criteria)
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
        analysis_config,
    )
    print_success(
        f"Dataset characteristic and missing values save to: {analysis_config.output_dir}/docs"
    )


if __name__ == "__main__":
    main()

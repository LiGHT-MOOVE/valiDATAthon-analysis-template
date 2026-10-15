from analysis.config import REQUIRED_NON_NULL_COLUMNS, load_analysis_config
from analysis.data.load import load_dataset
from analysis.data.preprocess import prepare_data
from analysis.data.validate import (
    validate_processed_data,
)
from analysis.helpers import export_dataframe, export_excel, export_model_fits
from analysis.statistics.cache import get_cache
from analysis.statistics.descriptive import (
    get_analysis_values,
)
from analysis.statistics.model_comparisons import (
    fit_mixed_models_by_country_and_criterion,
    fit_safety_pairwise_contrasts_by_country,
)
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
    print_step(4, "Adjusted mean score (95% CI)")
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
    """
    print_step(5, "Safety pairwise comparisons")
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
    """
    print_success(
        f"Dataset characteristic and missing values save to: {analysis_config.output_dir}/docs"
    )


if __name__ == "__main__":
    main()

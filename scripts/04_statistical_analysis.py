from analysis.data.load import load_dataset
from analysis.data.preprocess import prepare_data
from analysis.data.validate import validate_processed_data
from analysis.statistics.cache import get_cache
from analysis.statistics.config import (
    REQUIRED_NON_NULL_COLUMNS,
    load_analysis_config,
)
from analysis.statistics.descriptive import get_analysis_values
from analysis.statistics.runner import ANALYSIS_RUNNERS, run_selected_analyses
from utils.print_console import print_step, print_success


def main():
    """Load, validate, prepare, and analyse the dataset."""

    config = load_analysis_config()
    analysis_dataset_path = config.dataset_path

    # Validate analysis selection before loading the dataset.
    unknown_analyses = set(config.analyses) - set(ANALYSIS_RUNNERS)

    if unknown_analyses:
        raise ValueError(
            f"Unknown analyses in configuration: {sorted(unknown_analyses)}"
        )

    selected_analyses = [
        name for name in ANALYSIS_RUNNERS if config.analyses.get(name, False)
    ]

    if not selected_analyses:
        print_success("No analyses selected. Nothing to run.")
        return

    if not analysis_dataset_path.is_file():
        raise FileNotFoundError(
            f"Analysis input file not found: {analysis_dataset_path}"
        )

    memory = get_cache(
        cache_dir=config.cache_dir,
        enabled=config.use_cache,
    )

    print_step(1, "Load analysis data")
    reviews_df = load_dataset(analysis_dataset_path)

    print_step(2, "Validate analysis data")

    score_cols = [column for column in reviews_df.columns if column.endswith("_score")]

    validate_processed_data(
        reviews_df,
        score_cols,
        REQUIRED_NON_NULL_COLUMNS,
    )

    print_step(3, "Data preparation")
    df = prepare_data(
        reviews_df,
        config,
    )

    print_step(4, "Get analysis characteristics")
    criteria, countries, models, countries_ordered = get_analysis_values(df)

    run_selected_analyses(
        df=df,
        criteria=criteria,
        countries=countries,
        models=models,
        config=config,
        memory=memory,
    )

    print_success(f"Analysis results saved to: {config.docs_dir}")


if __name__ == "__main__":
    main()

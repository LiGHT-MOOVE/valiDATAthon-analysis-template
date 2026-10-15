from analysis.config import REQUIRED_NON_NULL_COLUMNS, load_analysis_config
from analysis.data.load import load_dataset
from analysis.data.preprocess import prepare_data
from analysis.data.validate import (
    validate_processed_data,
)
from analysis.helpers import export_dataframe
from analysis.statistics.descriptive import (
    calculate_missingness,
    create_study_characteristics_table,
)
from utils.print_console import print_step, print_success


def main():
    analysis_config = load_analysis_config()
    analysis_dataset_path = analysis_config.dataset_path
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

    print_step(4, "Calculate missing values")
    missing_values = calculate_missingness(df)
    export_dataframe(missing_values, "missing_values", analysis_config, save_index=True)

    print_step(5, "Dataset characteristic")
    study_characteristic = create_study_characteristics_table(df)
    export_dataframe(study_characteristic, "dataset_characteristic", analysis_config)

    print_success(
        f"Dataset characteristic and missing values save to: {analysis_config.output_dir}/docs"
    )


if __name__ == "__main__":
    main()

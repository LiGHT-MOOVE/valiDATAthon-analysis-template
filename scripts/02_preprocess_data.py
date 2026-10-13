import argparse
from pathlib import Path

from analysis.data.load import check_input_files, load_dataset
from analysis.data.preprocess import (
    calculate_duplicate_diagnostics,
    create_analytic_dataset,
    remove_duplicate_reviews,
)
from analysis.data.validate import (
    validate_processed_data,
    validate_raw_data,
)
from config import ROOT, get_country_config, load_config, validate_config
from utils.general import parse_args
from utils.print_console import print_step

CONFIG_PATH = ROOT / "configs/config.yaml"

config = load_config(CONFIG_PATH)
validate_config(config)


def main():
    args = parse_args()

    country_config = get_country_config(
        config,
        args.country,
    )

    raw_data_path = ROOT / config["paths"]["raw_data"]
    answers_path = raw_data_path / country_config["answers"]
    reviews_path = raw_data_path / country_config["reviews"]

    processed_data_path = ROOT / config["paths"]["processed_data"]
    diagnostics_path = processed_data_path / "diagnostics"

    # Check that the input files exist before loading them.

    for path in [answers_path, reviews_path]:
        if not path.is_file():
            raise FileNotFoundError(f"Input file not found: {path}")

    # Create output directories.

    # create folders
    processed_data_path.mkdir(parents=True, exist_ok=True)
    diagnostics_path.mkdir(parents=True, exist_ok=True)

    # check input files
    check_input_files(answers_path, reviews_path)
    # 1. Load raw data
    print_step(1, "Load raw data")
    answers_raw = load_dataset(answers_path)
    reviews_raw = load_dataset(reviews_path)

    # 2. Validate raw data
    print_step(2, "Validate raw data")
    answers_raw_validated, reviews_raw_validated = validate_raw_data(
        answers_raw, reviews_raw
    )

    # 3. Preprocess reviews
    print_step(3, "Preprocess reviews")
    reviews_reshaped = create_analytic_dataset(
        reviews_raw_validated, answers_raw_validated, country_config["name"]
    )
    duplicate_reviews, diagnostics_summary = calculate_duplicate_diagnostics(
        reviews_reshaped
    )
    clean_reviews = remove_duplicate_reviews(reviews_reshaped)

    # 4. Validate processed data
    print_step(4, " Validate processed data")
    score_cols = [col for col in clean_reviews.columns if col.endswith("_score")]
    non_null_cols = [
        col
        for col in clean_reviews.columns
        if not col.endswith("_score") and col != "comments"
    ]
    print(non_null_cols)
    validate_processed_data(clean_reviews, score_cols, non_null_cols)

    # 5. Save outputs
    print_step(5, " Save outputs")
    # Preserve your existing filenames and formats.
    clean_reviews.to_csv(
        processed_data_path / f"{country_config['name']}_preprocessed_reviews.csv",
        index=False,
        na_rep="",
    )
    duplicate_reviews.to_csv(
        processed_data_path / f"{country_config['name']}_reviews_duplicates.csv",
        index=False,
        na_rep="",
    )

    # 6. Print summary
    print_step(6, "Print summary")
    # Preserve your existing summary information.
    with open(
        diagnostics_path / f"{country_config['name']}_diagnostics_summary.txt",
        "w",
        encoding="utf-8",
    ) as f:
        f.write(diagnostics_summary)

    print("=" * 70)
    print("MOOVE preprocessing completed successfully")
    print("=" * 70)

    print(f"Raw answers:       {len(answers_raw):,}")
    print(f"Raw reviews:       {len(reviews_raw):,}")
    print(f"Clean reviews:     {len(clean_reviews):,}")
    print(f"Unique battles:    {clean_reviews['battle_id'].nunique():,}")
    print(f"Unique reviewers:  {clean_reviews['reviewer_id'].nunique():,}")
    print(f"Unique answers:    {clean_reviews['answer_id'].nunique():,}")

    print()
    print(f"Processed data saved to: {processed_data_path}")
    print("=" * 70)


if __name__ == "__main__":
    main()

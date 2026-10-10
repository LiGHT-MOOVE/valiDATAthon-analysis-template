from pathlib import Path

from analysis.data.load import load_dataset
from analysis.data.preprocess import (
    calculate_duplicate_diagnostics,
    create_analytic_dataset,
    remove_duplicate_reviews,
)
from analysis.data.validate import (
    validate_processed_data,
    validate_raw_data,
)
from config import load_config
from utils.print_console import print_step

ROOT = Path(__file__).resolve().parents[1]

config = load_config()
RAW_DATA_PATH = config["paths"]["raw_data"]
PROCESSED_DATA_PATH = config["paths"]["processed_data"]

ANSWERS_DATA = config["data"]["answers"]
REVIEWS_DATA = config["data"]["reviews"]

PATH_TO_ANSWERS = ROOT / RAW_DATA_PATH / ANSWERS_DATA
PATH_TO_REVIEWS = ROOT / RAW_DATA_PATH / REVIEWS_DATA
PATH_TO_PROCESSED_DATA_FOLDER = ROOT / PROCESSED_DATA_PATH
DIAGNOSTICS_FOLDER = PATH_TO_PROCESSED_DATA_FOLDER / "diagnostics"


def main():
    # create folders
    PATH_TO_PROCESSED_DATA_FOLDER.mkdir(parents=True, exist_ok=True)
    DIAGNOSTICS_FOLDER.mkdir(parents=True, exist_ok=True)

    # 1. Load raw data
    print_step(1, "Load raw data")
    answers_raw = load_dataset(PATH_TO_ANSWERS)
    reviews_raw = load_dataset(PATH_TO_REVIEWS)

    # 2. Validate raw data
    print_step(2, "Validate raw data")
    answers_raw_validated, reviews_raw_validated = validate_raw_data(
        answers_raw, reviews_raw
    )

    # 3. Preprocess reviews
    print_step(3, "Preprocess reviews")
    reviews_reshaped = create_analytic_dataset(
        reviews_raw_validated, answers_raw_validated
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
    validate_processed_data(clean_reviews, score_cols, non_null_cols)

    # 5. Save outputs
    print_step(5, " Save outputs")
    # Preserve your existing filenames and formats.
    clean_reviews.to_csv(
        PATH_TO_PROCESSED_DATA_FOLDER / "malawi_phc_preprocessed_reviews.csv",
        index=False,
        na_rep="",
    )
    duplicate_reviews.to_csv(
        PATH_TO_PROCESSED_DATA_FOLDER
        / "malawi_phc_preprocessed_reviews_duplicates.csv",
        index=False,
        na_rep="",
    )

    # 6. Print summary
    print_step(6, "Print summary")
    # Preserve your existing summary information.
    with open(
        DIAGNOSTICS_FOLDER / "malawi_phc_diagnostics_summary.txt",
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
    print(f"Processed data saved to: {PATH_TO_PROCESSED_DATA_FOLDER}")
    print("=" * 70)


if __name__ == "__main__":
    main()

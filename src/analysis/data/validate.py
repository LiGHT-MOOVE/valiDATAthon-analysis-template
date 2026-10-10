valid_votes = {"left", "right", "equal"}
valid_scores = {-2, -1, 0, 1, 2}
required_review_columns = [
    "ID",
    "Left answer ID",
    "Right answer ID",
    "User ID",
    "Creation timestamp",
]


required_answer_columns = [
    "Model",
    "Question ID",
    "ID",
]

valid_preferred = {"yes", "no", "equal"}
valid_placement = {"left", "right"}


def validate_raw_data(answers_raw, reviews_raw):
    # Your existing raw-data validation code goes here.
    # Keep the existing validation logic unchanged.

    # -------------------------------------------------------------------------
    # Reviews validation
    # -------------------------------------------------------------------------

    score_cols = [
        col
        for col in reviews_raw.columns
        if col.startswith(("Left evaluations:", "Right evaluations:"))
    ]
    # Remove duplicate review IDs
    reviews_raw_validated = reviews_raw.drop_duplicates(subset=["ID"]).copy()

    # Validate Vote
    invalid_votes = reviews_raw_validated["Vote"].notna() & ~reviews_raw_validated[
        "Vote"
    ].isin(valid_votes)

    if invalid_votes.any():
        raise ValueError(
            f"Invalid Vote values found: "
            f"{reviews_raw_validated.loc[invalid_votes, 'Vote'].unique()}"
        )

    # Validate score columns
    for col in score_cols:
        invalid_scores = reviews_raw_validated[col].notna() & ~reviews_raw_validated[
            col
        ].isin(valid_scores)

        if invalid_scores.any():
            raise ValueError(
                f"Invalid values found in '{col}': "
                f"{reviews_raw_validated.loc[invalid_scores, col].unique()}"
            )

    # Required non-null columns
    missing_values = reviews_raw_validated[required_review_columns].isna()

    if missing_values.any().any():
        missing_summary = missing_values.sum()
        missing_summary = missing_summary[missing_summary > 0]

        raise ValueError(
            f"Required values are missing in reviews data:\n{missing_summary}"
        )
    # -------------------------------------------------------------------------
    # Answers validation
    # -------------------------------------------------------------------------

    missing_values = answers_raw[required_answer_columns].isna()

    if missing_values.any().any():
        missing_summary = missing_values.sum()
        missing_summary = missing_summary[missing_summary > 0]

        raise ValueError(
            f"Required values are missing in answers data:\n{missing_summary}"
        )

    # Remove duplicate answer IDs
    answers_raw_validated = answers_raw.drop_duplicates(subset=["ID"]).copy()

    return answers_raw_validated, reviews_raw_validated


def validate_processed_data(clean_reviews, score_cols, non_null_cols):
    # Your existing final-validation code goes here.
    # Keep the existing validation logic unchanged.
    required_final_columns = score_cols + non_null_cols + ["comments"]
    missing_columns = [
        col for col in required_final_columns if col not in clean_reviews.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing expected columns in final dataset: {missing_columns}"
        )

    # review_id must be unique
    if clean_reviews["review_id"].duplicated().any():
        raise ValueError("Duplicate review_id values found.")

    # battle_id + placement must be unique
    if clean_reviews.duplicated(subset=["battle_id", "placement"]).any():
        raise ValueError("Duplicate battle_id + placement combinations found.")

    # reviewer + answer + opposing answer must be unique
    if clean_reviews.duplicated(
        subset=[
            "reviewer_id",
            "answer_id",
            "opposing_answer_id",
        ]
    ).any():
        raise ValueError(
            "Duplicate reviewer/answer/opposing-answer combinations found."
        )
    # Validate preferred
    invalid_preferred = clean_reviews["preferred"].notna() & ~clean_reviews[
        "preferred"
    ].isin(valid_preferred)

    if invalid_preferred.any():
        raise ValueError(
            "Invalid values found in 'preferred': "
            f"{clean_reviews.loc[invalid_preferred, 'preferred'].unique()}"
        )

    # Validate placement
    if not clean_reviews["placement"].isin(valid_placement).all():
        raise ValueError("Invalid placement values found.")

    # Validate score columns
    for col in score_cols:
        invalid_scores = clean_reviews[col].notna() & ~clean_reviews[col].isin(
            valid_scores
        )

        if invalid_scores.any():
            raise ValueError(
                f"Invalid values found in '{col}': "
                f"{clean_reviews.loc[invalid_scores, col].unique()}"
            )

    # Validate non-null columns
    missing_required_values = clean_reviews[non_null_cols].isna().any()

    missing_required_values = missing_required_values[missing_required_values]

    if len(missing_required_values) > 0:
        raise ValueError(
            f"Missing required values in final dataset:\n{missing_required_values}"
        )

    # print("Done your processed data validated successfully!")

import pandas as pd

from analysis.config import AnalysisConfig


# Helper functions
def calculate_preferred(row):
    vote = row["vote"]
    placement = row["placement"]

    if pd.isna(vote):
        return vote

    if vote == "equal":
        return "equal"

    if vote == placement:
        return "yes"

    return "no"


def clean_column_name(column):
    column = column.strip().lower()
    column = column.replace("&", "and")
    column = column.replace("%", "percent")
    column = column.replace("/", "_")
    column = column.replace("-", "_")
    column = column.replace(" ", "_")
    column = column.replace("(", "")
    column = column.replace(")", "")
    column = column.replace(".", "")
    return column


# Transformation functions
def reshape_reviews(reviews_validated):
    # Select the columns corresponding to the Left and Right evaluations
    left_right_columns = [
        col for col in reviews_validated.columns if col.startswith(("Left", "Right"))
    ]
    reviews_selected = reviews_validated[
        [
            "ID",
            "Creation timestamp",
            "User ID",
            "Vote",
            "Working group name",
        ]
        + left_right_columns
    ].copy()

    # Rename core columns
    reviews_selected = reviews_selected.rename(
        columns={
            "ID": "battle_id",
            "Creation timestamp": "review_timestamp",
            "User ID": "reviewer_id",
            "Vote": "vote",
            "Working group name": "working_group",
        }
    )

    # Create opposing answer IDs
    # -------------------------------------------------------------------------
    reviews_selected["Left opposing_answer_id"] = reviews_selected["Right answer ID"]
    reviews_selected["Right opposing_answer_id"] = reviews_selected["Left answer ID"]

    # Reshape Left / Right into one row per reviewed answer
    common_columns = [
        "battle_id",
        "review_timestamp",
        "reviewer_id",
        "vote",
        "working_group",
    ]

    left_columns = [col for col in reviews_selected.columns if col.startswith("Left ")]
    right_columns = [
        col for col in reviews_selected.columns if col.startswith("Right ")
    ]

    left_df = reviews_selected[common_columns + left_columns].copy()
    right_df = reviews_selected[common_columns + right_columns].copy()

    # Remove "Left " / "Right " prefixes
    left_df.columns = [
        col.replace("Left ", "", 1) if col.startswith("Left ") else col
        for col in left_df.columns
    ]
    right_df.columns = [
        col.replace("Right ", "", 1) if col.startswith("Right ") else col
        for col in right_df.columns
    ]

    left_df["placement"] = "left"
    right_df["placement"] = "right"

    # Combine the two sides
    reviews_reshaped = pd.concat(
        [left_df, right_df],
        ignore_index=True,
    )

    return reviews_reshaped


def join_answer_metadata(reviews_reshaped, answers_validated):
    answer_metadata = answers_validated[["Question ID", "Model", "ID"]].rename(
        columns={
            "Question ID": "vignette_id",
            "Model": "model",
            "ID": "answer ID",
        }
    )

    reviews_reshaped = reviews_reshaped.merge(
        answer_metadata,
        how="left",
        on="answer ID",
    )

    # Join opposing model
    opposing_model_metadata = answers_validated[["ID", "Model"]].rename(
        columns={
            "ID": "opposing_answer_id",
            "Model": "opposing_model",
        }
    )

    reviews_reshaped = reviews_reshaped.merge(
        opposing_model_metadata,
        how="left",
        on="opposing_answer_id",
    )
    reviews_reshaped["placement"] = reviews_reshaped["placement"].str.lower()

    return reviews_reshaped


# Main preprocessing function
def create_analytic_dataset(reviews_validated, answers_validated, country_name):

    reviews_reshaped = reshape_reviews(reviews_validated)
    reviews_answers_reshaped = join_answer_metadata(reviews_reshaped, answers_validated)

    # Calculate preferred
    reviews_answers_reshaped["preferred"] = reviews_answers_reshaped.apply(
        calculate_preferred,
        axis=1,
    )

    # Select final columns
    evaluation_columns = [
        col
        for col in reviews_answers_reshaped.columns
        if col.startswith("evaluations: ")
    ]

    final_columns = [
        "battle_id",
        "reviewer_id",
        "working_group",
        "placement",
        "review_timestamp",
        "vignette_id",
        "answer ID",
        "model",
        "preferred",
        "opposing_answer_id",
        "opposing_model",
    ] + evaluation_columns

    # Add comment if it exists
    if "comment" in reviews_answers_reshaped.columns:
        final_columns.append("comment")

    reviews_answers_reshaped = reviews_answers_reshaped[final_columns].copy()

    # Rename answer ID
    reviews_answers_reshaped = reviews_answers_reshaped.rename(
        columns={
            "answer ID": "answer_id",
            "comment": "comments",
        }
    )

    # Rename evaluation columns
    rename_evaluation_columns = {}

    for col in evaluation_columns:
        new_name = col.replace("evaluations: ", "", 1) + " Score"

        rename_evaluation_columns[col] = new_name

    reviews_answers_reshaped = reviews_answers_reshaped.rename(
        columns=rename_evaluation_columns
    )

    # Arrange and clean names
    reviews_answers_reshaped = reviews_answers_reshaped.sort_values(
        by=[
            "review_timestamp",
            "battle_id",
            "placement",
        ]
    ).reset_index(drop=True)

    # Equivalent to rowid_to_column()
    reviews_answers_reshaped.insert(
        0,
        "review_id",
        range(1, len(reviews_answers_reshaped) + 1),
    )
    reviews_answers_reshaped["reviewer_country"] = country_name
    reviews_answers_reshaped.columns = [
        clean_column_name(col) for col in reviews_answers_reshaped.columns
    ]

    return reviews_answers_reshaped


def calculate_duplicate_diagnostics(reviews_reshaped):
    # Duplicate reviews of the same answer by the same reviewer
    duplicate_reviews = (
        reviews_reshaped.groupby(["reviewer_id", "answer_id"], dropna=False)
        .filter(lambda x: len(x) > 1)
        .sort_values(
            [
                "reviewer_id",
                "vignette_id",
                "answer_id",
                "opposing_answer_id",
                "review_timestamp",
            ]
        )
    )

    # Create paired review key
    reviews_reshaped["paired_review_key"] = reviews_reshaped[
        ["answer_id", "opposing_answer_id"]
    ].apply(
        lambda row: "*".join(
            sorted(
                [
                    str(row["answer_id"]),
                    str(row["opposing_answer_id"]),
                ]
            )
        ),
        axis=1,
    )

    # Duplicate paired reviews
    duplicate_paired_reviews = (
        reviews_reshaped.groupby(["reviewer_id", "paired_review_key"], dropna=False)
        .size()
        .reset_index(name="n")
    )

    # Each paired review produces two rows
    duplicate_paired_reviews["n"] = duplicate_paired_reviews["n"] / 2

    duplicate_paired_reviews = duplicate_paired_reviews[
        duplicate_paired_reviews["n"] > 1
    ]

    n_users_with_duplicate_paired_reviews = duplicate_paired_reviews[
        "reviewer_id"
    ].nunique()

    n_duplicate_paired_reviews = len(duplicate_paired_reviews)

    n_duplicate_paired_review_submissions = duplicate_paired_reviews["n"].sum()

    # Duplicate non-paired reviews

    duplicate_nonpaired_reviews = (
        reviews_reshaped.groupby(["reviewer_id", "paired_review_key"], dropna=False)
        .filter(lambda x: len(x) == 2)
        .groupby(["reviewer_id", "answer_id"], dropna=False)
        .size()
        .reset_index(name="n")
    )

    duplicate_nonpaired_reviews = duplicate_nonpaired_reviews[
        duplicate_nonpaired_reviews["n"] > 1
    ]

    n_duplicate_nonpaired_reviews = len(duplicate_nonpaired_reviews)

    diagnostics_summary = (
        f"There were {n_duplicate_paired_reviews} paired reviews "
        f"with duplicate submissions "
        f"(these reviews were submitted a total of "
        f"{n_duplicate_paired_review_submissions} times by "
        f"{n_users_with_duplicate_paired_reviews} reviewers). "
        f"In addition, there were "
        f"{n_duplicate_nonpaired_reviews} answers scored multiple times "
        f"by the same reviewer across distinct paired reviews."
    )

    return duplicate_reviews, diagnostics_summary


def remove_duplicate_reviews(reviews_reshaped):
    # Remove duplicate reviews
    clean_reviews = reviews_reshaped.drop_duplicates(
        subset=[
            "reviewer_id",
            "answer_id",
            "opposing_answer_id",
        ],
        keep="first",
    ).copy()

    # Remove diagnostic key from final dataset
    clean_reviews = clean_reviews.drop(columns=["paired_review_key"])

    # Convert timestamp
    clean_reviews["review_timestamp"] = pd.to_datetime(
        clean_reviews["review_timestamp"],
        errors="coerce",
        utc=True,
    )

    return clean_reviews


def prepare_data(df: pd.DataFrame, config: AnalysisConfig) -> pd.DataFrame:
    """Normalize model names first, then assign model categories."""

    data = df.copy()
    data["model_raw"] = data["model"]
    data["model"] = data["model"].replace(config.friendly_models)
    if "opposing_model" in data:
        data["opposing_model_raw"] = data["opposing_model"]
        data["opposing_model"] = data["opposing_model"].replace(config.friendly_models)

    # Allow category mappings keyed by either raw or friendly model name.
    category = data["model"].map(config.model_categories)
    category = category.fillna(data["model_raw"].map(config.model_categories))
    data["model_category"] = category
    data["review_timestamp"] = pd.to_datetime(data["review_timestamp"])
    return data

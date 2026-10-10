"""
Script: Pre-process raw data exported directly from the MOOVE platform.

Builds a single, readable, clean analytic dataset with one row per review
(i.e., two rows per paired review). Used as an input to downstream modeling
and analytic work.

THIS CODE WAS MIGRATION FROM R-CODE (SAM/Ariadne Labs)
Equivalent Python implementation of:
    hypmoove_preprocess_data_STC.R
"""

from pathlib import Path

import pandas as pd

# =============================================================================
# Paths
# =============================================================================

# Update these paths as needed
PATH_TO_ANSWERS = Path("data/raw/Malawi PHC - Answers.csv")
PATH_TO_REVIEWS = Path("data/raw/Malawi PHC - fixed-Reviews.csv")

PATH_TO_PROCESSED_DATA_FOLDER = Path("data/processed")


# Create output directories if they do not exist
PATH_TO_PROCESSED_DATA_FOLDER.mkdir(parents=True, exist_ok=True)

DIAGNOSTICS_FOLDER = PATH_TO_PROCESSED_DATA_FOLDER / "diagnostics"
DIAGNOSTICS_FOLDER.mkdir(parents=True, exist_ok=True)


# =============================================================================
# Load raw data
# =============================================================================

answers_raw = pd.read_csv(PATH_TO_ANSWERS)
reviews_raw = pd.read_csv(PATH_TO_REVIEWS)


# =============================================================================
# Quality checks on raw data
# =============================================================================

# Identify score columns:
# Left evaluations: ...
# Right evaluations: ...
score_cols = [
    col
    for col in reviews_raw.columns
    if col.startswith(("Left evaluations:", "Right evaluations:"))
]


# -------------------------------------------------------------------------
# Reviews validation
# -------------------------------------------------------------------------

# Remove duplicate review IDs
reviews_raw_validated = reviews_raw.drop_duplicates(subset=["ID"]).copy()


# Validate Vote
valid_votes = {"left", "right", "equal"}

invalid_votes = reviews_raw_validated["Vote"].notna() & ~reviews_raw_validated[
    "Vote"
].isin(valid_votes)

if invalid_votes.any():
    raise ValueError(
        f"Invalid Vote values found: "
        f"{reviews_raw_validated.loc[invalid_votes, 'Vote'].unique()}"
    )


# Validate score columns
valid_scores = {-2, -1, 0, 1, 2}

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
required_review_columns = [
    "ID",
    "Left answer ID",
    "Right answer ID",
    "User ID",
    "Creation timestamp",
]

missing_values = reviews_raw_validated[required_review_columns].isna()

if missing_values.any().any():
    missing_summary = missing_values.sum()
    missing_summary = missing_summary[missing_summary > 0]

    raise ValueError(f"Required values are missing in reviews data:\n{missing_summary}")


# -------------------------------------------------------------------------
# Answers validation
# -------------------------------------------------------------------------

required_answer_columns = [
    "Model",
    "Question ID",
    "ID",
]

missing_values = answers_raw[required_answer_columns].isna()

if missing_values.any().any():
    missing_summary = missing_values.sum()
    missing_summary = missing_summary[missing_summary > 0]

    raise ValueError(f"Required values are missing in answers data:\n{missing_summary}")


# Remove duplicate answer IDs
answers_raw_validated = answers_raw.drop_duplicates(subset=["ID"]).copy()


# =============================================================================
# Build reviews analytic dataset
# =============================================================================

# Select the columns corresponding to the Left and Right evaluations
left_right_columns = [
    col for col in reviews_raw_validated.columns if col.startswith(("Left", "Right"))
]

reviews_selected = reviews_raw_validated[
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


# -------------------------------------------------------------------------
# Create opposing answer IDs
# -------------------------------------------------------------------------

reviews_selected["Left opposing_answer_id"] = reviews_selected["Right answer ID"]

reviews_selected["Right opposing_answer_id"] = reviews_selected["Left answer ID"]


# -------------------------------------------------------------------------
# Reshape Left / Right into one row per reviewed answer
# -------------------------------------------------------------------------

# Convert:
#
# Left answer ID
# Left opposing_answer_id
# Left evaluations: ...
#
# Right answer ID
# Right opposing_answer_id
# Right evaluations: ...
#
# into:
#
# placement | answer ID | opposing_answer_id | evaluations...
#
# We first create separate left and right dataframes because this is
# easier to control in pandas than reproducing tidyr::pivot_longer()
# exactly.

common_columns = [
    "battle_id",
    "review_timestamp",
    "reviewer_id",
    "vote",
    "working_group",
]

left_columns = [col for col in reviews_selected.columns if col.startswith("Left ")]

right_columns = [col for col in reviews_selected.columns if col.startswith("Right ")]


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


# -------------------------------------------------------------------------
# Join answer metadata
# -------------------------------------------------------------------------

answer_metadata = answers_raw_validated[["Question ID", "Model", "ID"]].rename(
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
opposing_model_metadata = answers_raw_validated[["ID", "Model"]].rename(
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


# =============================================================================
# Calculate preferred
# =============================================================================

reviews_reshaped["placement"] = reviews_reshaped["placement"].str.lower()


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


reviews_reshaped["preferred"] = reviews_reshaped.apply(
    calculate_preferred,
    axis=1,
)


# =============================================================================
# Select final columns
# =============================================================================

evaluation_columns = [
    col for col in reviews_reshaped.columns if col.startswith("evaluations: ")
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
if "comment" in reviews_reshaped.columns:
    final_columns.append("comment")


reviews_reshaped = reviews_reshaped[final_columns].copy()


# Rename answer ID
reviews_reshaped = reviews_reshaped.rename(
    columns={
        "answer ID": "answer_id",
        "comment": "comments",
    }
)


# =============================================================================
# Rename evaluation columns
# =============================================================================

rename_evaluation_columns = {}

for col in evaluation_columns:
    new_name = col.replace("evaluations: ", "", 1) + " Score"

    rename_evaluation_columns[col] = new_name


reviews_reshaped = reviews_reshaped.rename(columns=rename_evaluation_columns)


# =============================================================================
# Arrange and clean names
# =============================================================================

reviews_reshaped = reviews_reshaped.sort_values(
    by=[
        "review_timestamp",
        "battle_id",
        "placement",
    ]
).reset_index(drop=True)


# Equivalent to rowid_to_column()
reviews_reshaped.insert(
    0,
    "review_id",
    range(1, len(reviews_reshaped) + 1),
)


# Equivalent to janitor::clean_names()
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


reviews_reshaped.columns = [clean_column_name(col) for col in reviews_reshaped.columns]


# =============================================================================
# Duplicate Reviews Diagnostics
# =============================================================================

# -------------------------------------------------------------------------
# Duplicate reviews of the same answer by the same reviewer
# -------------------------------------------------------------------------

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


# -------------------------------------------------------------------------
# Create paired review key
# -------------------------------------------------------------------------

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


# -------------------------------------------------------------------------
# Duplicate paired reviews
# -------------------------------------------------------------------------

duplicate_paired_reviews = (
    reviews_reshaped.groupby(["reviewer_id", "paired_review_key"], dropna=False)
    .size()
    .reset_index(name="n")
)


# Each paired review produces two rows
duplicate_paired_reviews["n"] = duplicate_paired_reviews["n"] / 2


duplicate_paired_reviews = duplicate_paired_reviews[duplicate_paired_reviews["n"] > 1]


n_users_with_duplicate_paired_reviews = duplicate_paired_reviews[
    "reviewer_id"
].nunique()


n_duplicate_paired_reviews = len(duplicate_paired_reviews)


n_duplicate_paired_review_submissions = duplicate_paired_reviews["n"].sum()


# -------------------------------------------------------------------------
# Duplicate non-paired reviews
# -------------------------------------------------------------------------

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


# =============================================================================
# Diagnostics summary
# =============================================================================

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


# =============================================================================
# Remove duplicate reviews
# =============================================================================

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


# =============================================================================
# Convert timestamp
# =============================================================================

clean_reviews["review_timestamp"] = pd.to_datetime(
    clean_reviews["review_timestamp"],
    errors="coerce",
    utc=True,
)


# =============================================================================
# Identify score and non-score columns
# =============================================================================

score_cols = [col for col in clean_reviews.columns if col.endswith("_score")]


non_null_cols = [
    col
    for col in clean_reviews.columns
    if not col.endswith("_score") and col != "comments"
]


# =============================================================================
# Final validation
# =============================================================================

# Required columns must exist
required_final_columns = score_cols + non_null_cols + ["comments"]

missing_columns = [
    col for col in required_final_columns if col not in clean_reviews.columns
]


if missing_columns:
    raise ValueError(f"Missing expected columns in final dataset: {missing_columns}")


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
    raise ValueError("Duplicate reviewer/answer/opposing-answer combinations found.")


# Validate preferred
valid_preferred = {"yes", "no", "equal"}

invalid_preferred = clean_reviews["preferred"].notna() & ~clean_reviews[
    "preferred"
].isin(valid_preferred)

if invalid_preferred.any():
    raise ValueError(
        "Invalid values found in 'preferred': "
        f"{clean_reviews.loc[invalid_preferred, 'preferred'].unique()}"
    )


# Validate placement
valid_placement = {"left", "right"}

if not clean_reviews["placement"].isin(valid_placement).all():
    raise ValueError("Invalid placement values found.")


# Validate score columns
for col in score_cols:
    invalid_scores = clean_reviews[col].notna() & ~clean_reviews[col].isin(valid_scores)

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


# =============================================================================
# Save outputs
# =============================================================================

# -------------------------------------------------------------------------
# Clean analytic dataset
# -------------------------------------------------------------------------

# Recommended Python format
"""
clean_reviews.to_parquet(
    PATH_TO_PROCESSED_DATA_FOLDER
    / "preprocessed_reviews.parquet",
    index=False,
)
"""

# Also save CSV for easy inspection / sharing
clean_reviews.to_csv(
    PATH_TO_PROCESSED_DATA_FOLDER / "malawi_phc_preprocessed_reviews.csv",
    index=False,
    na_rep="",
)


# -------------------------------------------------------------------------
# Duplicate review diagnostics
# -------------------------------------------------------------------------

duplicate_reviews.to_csv(
    PATH_TO_PROCESSED_DATA_FOLDER / "malawi_phc_preprocessed_reviews_duplicates.csv",
    index=False,
    na_rep="",
)


# -------------------------------------------------------------------------
# Diagnostics summary
# -------------------------------------------------------------------------

with open(
    DIAGNOSTICS_FOLDER / "malawi_phc_diagnostics_summary.txt",
    "w",
    encoding="utf-8",
) as f:
    f.write(diagnostics_summary)


# =============================================================================
# Print summary
# =============================================================================

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
print("Duplicate diagnostics:")
print(f"  Duplicate paired reviews: {n_duplicate_paired_reviews}")
print(f"  Duplicate paired submissions: {n_duplicate_paired_review_submissions}")
print(
    f"  Reviewers with duplicate paired reviews: "
    f"{n_users_with_duplicate_paired_reviews}"
)
print(f"  Duplicate non-paired reviews: {n_duplicate_nonpaired_reviews}")

print()
print(f"Processed data saved to: {PATH_TO_PROCESSED_DATA_FOLDER}")
print("=" * 70)

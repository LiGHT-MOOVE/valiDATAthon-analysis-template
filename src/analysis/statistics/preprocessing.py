from collections.abc import Sequence

import pandas as pd


def prepare_criterion_data(
    df: pd.DataFrame,
    criterion: str,
) -> pd.DataFrame:

    return df.dropna(
        subset=[
            criterion,
            "model",
            "reviewer_id",
            "vignette_id",
            "answer_id",
        ]
    )


def long_ratings(df: pd.DataFrame, criteria: Sequence[str]) -> pd.DataFrame:
    # keep most recent review
    unique = df.sort_values("review_timestamp").drop_duplicates(
        ["answer_id", "reviewer_id"],
        keep="last",
    )
    return (
        unique[["answer_id", "reviewer_id", "model", "review_timestamp", *criteria]]
        .melt(
            id_vars=["answer_id", "reviewer_id", "model", "review_timestamp"],
            value_vars=criteria,
            var_name="criterion",
            value_name="score",
        )
        .dropna(subset=["score"])
        .sort_values(["answer_id", "criterion", "review_timestamp"])
        .reset_index(drop=True)
    )


def paired_ratings(long: pd.DataFrame) -> pd.DataFrame:
    selected = long.assign(
        iter=lambda x: x.groupby(["answer_id", "criterion"]).cumcount() + 1,
        n=lambda x: x.groupby(["answer_id", "criterion"])["score"].transform("size"),
    ).query("iter <= 2 and n >= 2")
    return (
        selected.pivot(
            index=["answer_id", "model", "criterion"], columns="iter", values="score"
        )
        .rename(columns={1: "rater_1", 2: "rater_2"})
        .reset_index()
    )

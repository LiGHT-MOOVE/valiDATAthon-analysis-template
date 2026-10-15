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

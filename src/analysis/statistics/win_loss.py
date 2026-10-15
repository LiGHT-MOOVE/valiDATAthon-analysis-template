#| label: load-packages
from __future__ import annotations

import numpy as np
import pandas as pd


# ______________________________
# analysis
def win_loss_summary(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Calculate win/loss summaries for each country."""

    results = {}

    for country, df_country in df.groupby(
        "reviewer_country",
        observed=True,
        sort=False,
    ):
        counts = (
            df_country.groupby(["model", "preferred"], observed=True)
            .size()
            .unstack(fill_value=0)
            .reindex(columns=["yes", "no", "equal"], fill_value=0)
            .rename(columns={"yes": "Wins", "no": "Losses", "equal": "Ties"})
            .reset_index()
            .rename(columns={"model": "Model"})
        )
        total = counts[["Wins", "Losses", "Ties"]].sum(axis=1)
        # win counts as total and ties as half => w + 0.5t / total
        counts["Winning Percentage"] = (2 * counts["Wins"] + counts["Ties"]) / (
            2 * total
        )
        counts = counts.sort_values("Winning Percentage", ascending=False).reset_index(
            drop=True
        )
        counts.insert(0, "Rank", np.arange(1, len(counts) + 1))
        results[country] = counts
    return results


def head_to_head_data(
    df: pd.DataFrame, rankings: pd.DataFrame
) -> tuple[dict[str, pd.DataFrame], dict[str, pd.DataFrame]]:
    results = {}
    matrices = {}
    for country, df_country in df.groupby(
        "reviewer_country",
        observed=True,
        sort=False,
    ):
        counts = (
            df_country.groupby(["model", "opposing_model", "preferred"], observed=True)
            .size()
            .rename("n")
            .reset_index()
            .pivot_table(
                index=["model", "opposing_model"],
                columns="preferred",
                values="n",
                fill_value=0,
                aggfunc="sum",
            )
            .reindex(columns=["yes", "no", "equal"], fill_value=0)
            .rename(columns={"yes": "wins", "no": "losses", "equal": "ties"})
            .reset_index()
        )
        total = counts[["wins", "losses", "ties"]].sum(axis=1)
        counts["points_pct"] = np.where(
            total > 0, (2 * counts["wins"] + counts["ties"]) / (2 * total), np.nan
        )
        country_rankings = rankings.get(country)
        if country_rankings is None:
            continue
        order = country_rankings.sort_values("Rank", ascending=False)["Model"].tolist()
        matrix = counts.pivot(
            index="model", columns="opposing_model", values="points_pct"
        ).reindex(index=order, columns=order)
        results[country] = counts
        matrices[country] = matrix

    return results, matrices

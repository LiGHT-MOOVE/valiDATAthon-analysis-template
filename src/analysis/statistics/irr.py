#| label: load-packages
from __future__ import annotations

import warnings
from collections.abc import Sequence

import pandas as pd
from irrCAC.raw import CAC

from analysis.statistics.preprocessing import long_ratings

# ______________________________
# Agreement


def agreement_results_by_model(
    long: pd.DataFrame,
    irr_methods,
    irr_weight,
    categories: Sequence[int] = (-2, -1, 0, 1, 2),
    confidence_level=0.95,
) -> pd.DataFrame:
    rows = []

    for model in long["model"].dropna().unique():
        long_model = long[long["model"].eq(model)].copy()

        long_model["rating_unit"] = (
            long_model["answer_id"].astype(str)
            + "_"
            + long_model["criterion"].astype(str)
        )

        ratings = long_model.pivot(
            index="rating_unit",
            columns="reviewer_id",
            values="score",
        )

        ratings = ratings.loc[ratings.notna().sum(axis=1) >= 2].dropna(
            axis=1,
            how="all",
        )

        if ratings.empty or ratings.shape[1] < 2:
            warnings.warn(f"Skipping {model}: fewer than two usable reviewers.")
            continue
        for key, method in irr_methods.items():
            cac = CAC(
                ratings=ratings,
                weights=irr_weight,
                categories=list(categories),
                confidence_level=confidence_level,
                digits=8,
            )
            estimate = getattr(cac, method)()["est"]
            low, high = estimate["confidence_interval"]
            rows.append(
                {
                    "model": model,
                    "statistic_key": key,
                    "coeff.name": estimate["coefficient_name"],
                    "coeff": estimate["coefficient_value"],
                    "conf_low": low,
                    "conf_high": high,
                    "stderr": estimate["se"],
                    "test_statistic": estimate["z"],
                    "p.value": estimate["p_value"],
                    "pa": estimate["pa"],
                    "pe": estimate["pe"],
                }
            )
    return pd.DataFrame(rows)


# agreement by criterion
def agreement_results(
    long: pd.DataFrame,
    criteria: Sequence[str],
    irr_methods,
    irr_weight,
    categories: Sequence[int] = (-2, -1, 0, 1, 2),
    confidence_level=0.95,
) -> pd.DataFrame:
    rows = []
    for criterion in criteria:
        ratings = long.loc[long["criterion"].eq(criterion)].pivot(
            index="answer_id", columns="reviewer_id", values="score"
        )
        ratings = ratings.loc[ratings.notna().sum(axis=1) >= 2].dropna(
            axis=1, how="all"
        )
        if ratings.empty or ratings.shape[1] < 2:
            warnings.warn(f"Skipping {criterion}: fewer than two usable ratings.")
            continue
        for key, method in irr_methods.items():
            cac = CAC(
                ratings=ratings,
                weights=irr_weight,
                categories=list(categories),
                confidence_level=confidence_level,
                digits=8,
            )
            estimate = getattr(cac, method)()["est"]
            low, high = estimate["confidence_interval"]
            rows.append(
                {
                    "criterion": criterion,
                    "statistic_key": key,
                    "coeff.name": estimate["coefficient_name"],
                    "coeff": estimate["coefficient_value"],
                    "conf_low": low,
                    "conf_high": high,
                    "stderr": estimate["se"],
                    "test_statistic": estimate["z"],
                    "p.value": estimate["p_value"],
                    "pa": estimate["pa"],
                    "pe": estimate["pe"],
                }
            )
    return pd.DataFrame(rows)


def compute_agreement_by_criterion(
    df, countries, criteria, irr_methods, irr_weight, confidence_level
):
    agreement_all = []

    for country in countries:
        df_country = df[df["reviewer_country"] == country]
        ratings_long = long_ratings(df_country, criteria)

        agreement_output = agreement_results(
            ratings_long,
            criteria,
            irr_methods,
            irr_weight,
            confidence_level=confidence_level,
        )

        agreement_output["country"] = country

        agreement_all.append(agreement_output)

    agreement_plot_data_by_criterion = pd.concat(
        agreement_all,
        ignore_index=True,
    )
    return agreement_plot_data_by_criterion


def compute_agreement_by_model(
    df, countries, criteria, irr_methods, irr_weight, confidence_level
):
    agreement_all_by_model = []
    for country in countries:
        df_country = df[df["reviewer_country"] == country]
        ratings_long = long_ratings(df_country, criteria)
        agreement_output = agreement_results_by_model(
            ratings_long, irr_methods, irr_weight, confidence_level=confidence_level
        )

        agreement_output["country"] = country

        agreement_all_by_model.append(agreement_output)

    agreement_plot_data_by_model = pd.concat(
        agreement_all_by_model,
        ignore_index=True,
    )

    return agreement_plot_data_by_model

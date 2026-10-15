import numpy as np
import pandas as pd


def count_preferred_side_chosen(df):
    """This function get the percentage of RIGHT chosen over the preferred vignettes only (YES/NO) votes"""
    df_win = df[df["preferred"].isin(["yes"])]
    country_stats_preferred_position = (
        df_win.groupby("reviewer_country")["placement"]
        .agg(
            percentage_right=lambda x: (x == "right").mean() * 100,
            percentage_left=lambda x: (x == "left").mean() * 100,
            std=lambda x: (x == "right").std(),
            n=lambda x: (x == "right").count(),
        )
        .reset_index()
    )
    country_stats_preferred_position["SE"] = country_stats_preferred_position[
        "std"
    ] / np.sqrt(country_stats_preferred_position["n"])

    country_stats_preferred_position["ci_lower"] = (
        country_stats_preferred_position["percentage_right"]
        - 1.96 * country_stats_preferred_position["SE"] * 100
    )

    country_stats_preferred_position["ci_upper"] = (
        country_stats_preferred_position["percentage_right"]
        + 1.96 * country_stats_preferred_position["SE"] * 100
    )
    return country_stats_preferred_position


def count_position_effect_on_criterion_score(df, criteria):
    # Position effect on criterion scores
    position_effect = (
        df.groupby(
            ["battle_id", "reviewer_country"],
            observed=True,
        )
        .apply(
            lambda g: pd.Series(
                {
                    criterion: (
                        g.loc[g["placement"] == "right", criterion].iloc[0]
                        - g.loc[g["placement"] == "left", criterion].iloc[0]
                    )
                    for criterion in criteria
                }
            ),
            include_groups=False,
        )
        .reset_index()
    )

    position_effect_long = position_effect.melt(
        id_vars=[
            "battle_id",
            "reviewer_country",
        ],
        value_vars=criteria,
        var_name="criterion",
        value_name="difference",
    )
    position_summary = (
        position_effect_long.groupby(
            ["reviewer_country", "criterion"],
            observed=True,
        )["difference"]
        .agg(["count", "mean", "median", "std", "min", "max"])
        .reset_index()
    )

    position_summary["se"] = position_summary["std"] / np.sqrt(
        position_summary["count"]
    )

    position_summary["ci_lower"] = (
        position_summary["mean"] - 1.96 * position_summary["se"]
    )

    position_summary["ci_upper"] = (
        position_summary["mean"] + 1.96 * position_summary["se"]
    )

    return position_summary


def get_percentage_of_chosen_response_scored_higher(df, criteria):
    # Does the chosen response also score higher for that criterion?
    df_not_equal = df[df["preferred"] != "equal"].copy()

    results = []

    for (country, battle_id), group in df_not_equal.groupby(
        ["reviewer_country", "battle_id"]
    ):
        if len(group) != 2:
            continue

        preferred = group["preferred"].iloc[0]

        for criterion in criteria:
            first_score = group.iloc[0][criterion]
            second_score = group.iloc[1][criterion]

            if preferred == "yes":
                preferred_score = first_score
                nonpreferred_score = second_score

            elif preferred == "no":
                preferred_score = second_score
                nonpreferred_score = first_score

            else:
                continue

            results.append(
                {
                    "country": country,
                    "battle_id": battle_id,
                    "criterion": criterion,
                    "preferred_higher": preferred_score > nonpreferred_score,
                    "far_apart": abs(preferred_score - nonpreferred_score),
                }
            )

    preferred_results = pd.DataFrame(results)
    summary_preferred_results = (
        preferred_results.groupby(["country", "criterion"])["preferred_higher"]
        .agg(
            mean="mean",
            n="count",
            sd="std",
        )
        .reset_index()
    )

    summary_preferred_results["se"] = summary_preferred_results["sd"] / np.sqrt(
        summary_preferred_results["n"]
    )

    summary_preferred_results["ci_low"] = (
        summary_preferred_results["mean"] - 1.96 * summary_preferred_results["se"]
    )

    summary_preferred_results["ci_high"] = (
        summary_preferred_results["mean"] + 1.96 * summary_preferred_results["se"]
    )

    summary_preferred_results["ci_low"] = summary_preferred_results["ci_low"].clip(0, 1)
    summary_preferred_results["ci_high"] = summary_preferred_results["ci_high"].clip(
        0, 1
    )
    return summary_preferred_results

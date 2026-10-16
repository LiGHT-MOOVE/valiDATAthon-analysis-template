import pandas as pd
import numpy as np


def prepare_human_non_human_safety_comparisons_data(
    country_pairwise_safety,
    is_human,
):
    human_safety = pd.DataFrame()

    if is_human:
        human_safety = country_pairwise_safety[
            (country_pairwise_safety["model_a"] == "Human Benchmark")
            | (country_pairwise_safety["model_b"] == "Human Benchmark")
        ].copy()

        human_is_a = human_safety["model_a"] == "Human Benchmark"

        human_safety["model"] = np.where(
            human_is_a,
            human_safety["model_b"],
            human_safety["model_a"],
        )

        # Flip contrast to always be Model - Human
        human_safety.loc[
            human_is_a,
            ["estimate", "lower.CL", "upper.CL"],
        ] *= -1

        # Swap CI bounds after flipping
        human_safety.loc[
            human_is_a,
            ["lower.CL", "upper.CL"],
        ] = human_safety.loc[
            human_is_a,
            ["upper.CL", "lower.CL"],
        ].values

    country_pairwise_safety_non_human = country_pairwise_safety[
        (country_pairwise_safety["model_a"] != "Human Benchmark")
        & (country_pairwise_safety["model_b"] != "Human Benchmark")
    ].copy()

    country_pairwise_safety_non_human["pair_1"] = country_pairwise_safety_non_human[
        ["model_a", "model_b"]
    ].min(axis=1)

    country_pairwise_safety_non_human["pair_2"] = country_pairwise_safety_non_human[
        ["model_a", "model_b"]
    ].max(axis=1)

    # Identify rows where the contrast direction must be reversed
    reverse = (
        country_pairwise_safety_non_human["model_a"]
        != country_pairwise_safety_non_human["pair_1"]
    )

    old_lower = country_pairwise_safety_non_human.loc[reverse, "lower.CL"].copy()

    old_upper = country_pairwise_safety_non_human.loc[reverse, "upper.CL"].copy()

    country_pairwise_safety_non_human.loc[reverse, "estimate"] *= -1

    country_pairwise_safety_non_human.loc[reverse, "lower.CL"] = -old_upper
    country_pairwise_safety_non_human.loc[reverse, "upper.CL"] = -old_lower

    country_pairwise_safety_non_human["model_a"] = country_pairwise_safety_non_human[
        "pair_1"
    ]
    country_pairwise_safety_non_human["model_b"] = country_pairwise_safety_non_human[
        "pair_2"
    ]

    country_pairwise_safety_non_human["contrast"] = (
        country_pairwise_safety_non_human["model_a"]
        + " - "
        + country_pairwise_safety_non_human["model_b"]
    )

    country_pairwise_safety_non_human = country_pairwise_safety_non_human.drop(
        columns=["pair_1", "pair_2"]
    )

    return country_pairwise_safety_non_human, human_safety

import pandas as pd


def get_scores_gap(
    df,
    criteria,
):
    results = []

    for (country, battle_id), group in df.groupby(["reviewer_country", "battle_id"]):
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
                preferred_score = second_score
                nonpreferred_score = first_score

            results.append(
                {
                    "country": country,
                    "battle_id": battle_id,
                    "criterion": criterion,
                    "preferred_higher": preferred_score > nonpreferred_score,
                    "far_apart": abs(preferred_score - nonpreferred_score),
                }
            )

    preferred_results_all = pd.DataFrame(results)
    far_apart_results_all = (
        preferred_results_all.groupby(["country", "criterion"])["far_apart"]
        .value_counts()
        .unstack(fill_value=0)
        .reset_index()
    )
    far_apart_results_all["≥3 points apart"] = (
        far_apart_results_all[3] + far_apart_results_all[4]
    )

    far_apart_results_all = far_apart_results_all.drop(columns=[3, 4])
    far_apart_results_all = far_apart_results_all.rename(
        columns={
            0: "Same score",
            1: "1 point apart",
            2: "2 points apart",
        }
    )
    # Rename categories
    far_apart_pct_all = far_apart_results_all.rename(
        columns={
            0: "Same score",
            1: "1 point apart",
            2: "2 points apart",
        }
    )
    categories = [
        "Same score",
        "1 point apart",
        "2 points apart",
        "≥3 points apart",
    ]

    categories_pct = [
        "% Same score",
        "% 1 point apart",
        "% 2 points apart",
        "% ≥3 points apart",
    ]

    # Convert counts to percentages
    far_apart_pct_all[categories_pct] = (
        far_apart_pct_all[categories].div(
            far_apart_pct_all[categories].sum(axis=1),
            axis=0,
        )
        * 100
    )
    return far_apart_pct_all


def compute_same_answer_both_sides_scores(df, criteria, scores):
    results = {}
    for criterion in criteria:
        df_battle = (
            df.groupby("battle_id")[criterion]
            .agg(["first", "last"])
            .rename(
                columns={
                    "first": "left",
                    "last": "right",
                }
            )
        )

        heatmap_data = pd.crosstab(
            df_battle["right"],
            df_battle["left"],
        ).reindex(
            index=scores,
            columns=scores,
            fill_value=0,
        )

        heatmap_pct = heatmap_data / heatmap_data.values.sum() * 100
        results[criterion] = heatmap_pct

    return results

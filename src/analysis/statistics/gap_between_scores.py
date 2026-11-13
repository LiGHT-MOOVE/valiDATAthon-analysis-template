import pandas as pd


def get_scores_gap(df, criteria):
    gap_labels = {
        0: "Same score",
        1: "1 point apart",
        2: "2 points apart",
        3: "≥3 points apart",
    }
    categories = list(gap_labels.values())
    percentage_columns = [f"% {category}" for category in categories]
    output_columns = ["country", "criterion", *categories, *percentage_columns]
    results = []

    for (country, _battle_id), group in df.groupby(["reviewer_country", "battle_id"]):
        if len(group) != 2:
            continue

        for criterion in criteria:
            first_score, second_score = group[criterion]

            if pd.isna(first_score) or pd.isna(second_score):
                continue

            gap = abs(float(first_score) - float(second_score))
            results.append((country, criterion, min(gap, 3)))

    if not results:
        return pd.DataFrame(columns=output_columns)

    gaps = pd.DataFrame(results, columns=["country", "criterion", "gap"])
    counts = (
        gaps.groupby(["country", "criterion", "gap"])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=list(gap_labels), fill_value=0)
        .rename(columns=gap_labels)
    )

    percentages = counts.div(counts.sum(axis=1), axis=0).mul(100)
    percentages.columns = percentage_columns

    return counts.join(percentages).rename_axis(columns=None).reset_index()


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

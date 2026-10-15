import pandas as pd


def calculate_missingness(df):
    missingness = pd.DataFrame(
        {
            "n_missing": df.isna().sum(),
            "pct_missing": df.isna().mean() * 100,
        }
    )

    return missingness


def calculate_date_ranges(df):
    date_ranges = (
        df.groupby("reviewer_country")["review_timestamp"]
        .agg(date_min="min", date_max="max")
        .reset_index()
    )

    date_ranges["date_range"] = (
        date_ranges["date_min"].dt.strftime("%d %b")
        + " – "
        + date_ranges["date_max"].dt.strftime("%d %b %Y")
    )

    return date_ranges


def calculate_country_statistics(df):
    country_stats = (
        df.groupby("reviewer_country")
        .agg(
            clinical_vignettes=("vignette_id", "nunique"),
            pairwise_reviews=("battle_id", "nunique"),
            participants=("reviewer_id", "nunique"),
        )
        .reset_index()
    )

    return country_stats


def calculate_reviews_per_participant(df):
    reviews_per_participant = (
        df.groupby(["reviewer_country", "reviewer_id"])["battle_id"]
        .nunique()
        .groupby("reviewer_country")
        .agg(
            mean="mean",
            q25=lambda x: x.quantile(0.25),
            q75=lambda x: x.quantile(0.75),
        )
        .reset_index()
    )

    return reviews_per_participant


def create_study_characteristics_table(df):
    """Create a study characteristics table by country and overall."""

    date_ranges = calculate_date_ranges(df).set_index("reviewer_country")

    country_stats = calculate_country_statistics(df).set_index("reviewer_country")

    reviews_per_participant = calculate_reviews_per_participant(df).set_index(
        "reviewer_country"
    )

    countries = country_stats.index.tolist()

    summary_data = {
        "Characteristic": [
            "Date range",
            "Clinical vignettes, n",
            "Pairwise reviews, n",
            "Participants, n",
            "Pairwise reviews per participant, mean (IQR)",
        ]
    }

    for country in countries:
        reviews = reviews_per_participant.loc[country]

        summary_data[country] = [
            date_ranges.loc[country, "date_range"],
            country_stats.loc[country, "clinical_vignettes"],
            country_stats.loc[country, "pairwise_reviews"],
            country_stats.loc[country, "participants"],
            (f"{reviews['mean']:.1f} ({reviews['q25']:.0f}–{reviews['q75']:.0f})"),
        ]

    # overall
    overall_reviews_per_participant = df.groupby(["reviewer_country", "reviewer_id"])[
        "battle_id"
    ].nunique()

    overall_date_range = (
        f"{df['review_timestamp'].min():%d %b} – "
        f"{df['review_timestamp'].max():%d %b %Y}"
    )

    summary_data["Overall"] = [
        overall_date_range,
        df["vignette_id"].nunique(),
        df[["reviewer_country", "battle_id"]].drop_duplicates().shape[0],
        df[["reviewer_country", "reviewer_id"]].drop_duplicates().shape[0],
        (
            f"{overall_reviews_per_participant.mean():.1f} "
            f"({overall_reviews_per_participant.quantile(0.25):.0f}–"
            f"{overall_reviews_per_participant.quantile(0.75):.0f})"
        ),
    ]

    return pd.DataFrame(summary_data)


def get_analysis_values(df):
    criteria = [column for column in df.columns if column.endswith("_score")]

    countries = sorted(df["reviewer_country"].dropna().unique())

    models = df["model"].dropna().drop_duplicates().tolist()

    countries_ordered = sorted(countries)

    return (
        criteria,
        countries,
        models,
        countries_ordered,
    )

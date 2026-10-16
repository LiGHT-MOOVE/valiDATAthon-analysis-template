#| label: load-packages
from __future__ import annotations

import importlib
from collections.abc import Sequence

import pandas as pd
from joblib import Memory

import config
from analysis.statistics.config import MixedModelResult
from analysis.statistics.mixed_models import (
    estimated_marginal_means,
    fit_crossed_mixed_model,
    pairwise_model_contrasts,
)
from analysis.statistics.preprocessing import prepare_criterion_data

importlib.reload(config)


def _fit_model(
    analysis_df: pd.DataFrame,
    criterion: str,
    memory: Memory | None = None,
) -> MixedModelResult:
    """Fit a mixed-effects model, using the cache when available."""

    if memory is None:
        return fit_crossed_mixed_model(analysis_df, criterion)

    cached_fit = memory.cache(fit_crossed_mixed_model)
    return cached_fit(analysis_df, criterion)


def fit_mixed_models_by_country_and_criterion(
    df: pd.DataFrame,
    criteria: Sequence[str],
    models_ordered: Sequence[str],
    memory: Memory | None = None,
) -> tuple[pd.DataFrame, dict[tuple[str, str], MixedModelResult]]:
    """Fit one mixed model for each country and criterion."""

    summaries = []
    fits = {}

    for country, country_df in df.groupby(
        "reviewer_country",
        observed=True,
        sort=False,
    ):
        if pd.isna(country):
            continue

        categories = country_df[["model", "model_category"]].drop_duplicates()

        for criterion in criteria:
            analysis_df = prepare_criterion_data(
                country_df,
                criterion,
            )

            models = [
                model
                for model in models_ordered
                if model in analysis_df["model"].unique()
            ]

            if len(models) < 2:
                print(
                    f"Skipping {country} / {criterion}: fewer than two observed models."
                )
                continue

            print(f"Fitting {country} / {criterion}...")

            try:
                fit = _fit_model(
                    analysis_df,
                    criterion,
                    memory=memory,
                )
            except Exception as exc:  # noqa: BLE001
                print(f"Failed {country} / {criterion}: {type(exc).__name__}: {exc}")
                continue

            fits[(str(country), criterion)] = fit

            summary = estimated_marginal_means(
                fit,
                models,
                criterion,
            )

            summary["reviewer_country"] = country

            summary = summary.merge(
                categories,
                on="model",
                how="left",
                validate="many_to_one",
            )

            summaries.append(summary)

    if not summaries:
        return pd.DataFrame(), fits

    combined_summary = pd.concat(
        summaries,
        ignore_index=True,
    )

    return combined_summary, fits


# for safety
def fit_safety_pairwise_contrasts_by_country(
    df: pd.DataFrame,
):
    """Fit one mixed model per reviewer country using safety scores only."""

    pairwise_results = []
    fits = {}

    for country, country_df in df.groupby(
        "reviewer_country",
        observed=True,
        sort=False,
    ):
        if pd.isna(country):
            continue

        categories = country_df[["model", "model_category"]].drop_duplicates()

        analysis_df = (
            country_df[
                [
                    "model",
                    "model_category",
                    "reviewer_id",
                    "vignette_id",
                    "answer_id",
                    "safety_score",
                ]
            ]
            .dropna(
                subset=[
                    "safety_score",
                    "model",
                    "reviewer_id",
                    "vignette_id",
                    "answer_id",
                ]
            )
            .copy()
        )

        models = analysis_df["model"].drop_duplicates().tolist()

        if len(models) < 2:
            print(f"Skipping {country}: fewer than two observed models.")
            continue

        print(f"Fitting {country} / safety...")

        try:
            fit = fit_crossed_mixed_model(
                analysis_df,
                "safety_score",
                fixed_formula="C(model)",
            )
        except Exception as exc:  # noqa: BLE001
            print(f"Failed {country}: {type(exc).__name__}: {exc}")
            continue

        fits[str(country)] = fit

        # Calculate all pairwise model comparisons.
        country_results = pairwise_model_contrasts(
            fit,
            models,
            criterion="Safety",
        )

        country_results["reviewer_country"] = country

        model_a_categories = categories.rename(
            columns={
                "model": "model_a",
                "model_category": "model_a_category",
            }
        )

        country_results = country_results.merge(
            model_a_categories,
            on="model_a",
            how="left",
            validate="many_to_one",
        )

        model_b_categories = categories.rename(
            columns={
                "model": "model_b",
                "model_category": "model_b_category",
            }
        )

        country_results = country_results.merge(
            model_b_categories,
            on="model_b",
            how="left",
            validate="many_to_one",
        )

        pairwise_results.append(country_results)

    if pairwise_results:
        combined_results = pd.concat(
            pairwise_results,
            ignore_index=True,
        )
    else:
        combined_results = pd.DataFrame()

    return combined_results, fits

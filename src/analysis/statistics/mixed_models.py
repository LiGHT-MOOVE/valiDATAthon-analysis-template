#| label: load-packages
from __future__ import annotations

import importlib
import math
from collections.abc import Sequence
from itertools import combinations

import numpy as np
import pandas as pd
import patsy

import config
from analysis.config import MixedModelResult

importlib.reload(config)

import statsmodels.formula.api as smf
from scipy import stats

RANDOM_EFFECTS = (
    "reviewer_id",
    "vignette_id",
    "answer_id",
)


def model_design_vector(result: MixedModelResult, model: str) -> np.ndarray:
    new_data = pd.DataFrame({"model": [model]})

    design_matrix = patsy.build_design_matrices(
        [result.design_info],
        new_data,
        return_type="dataframe",
    )[0]

    return design_matrix.iloc[0].to_numpy()


def linear_estimate(
    result: MixedModelResult,
    contrast: np.ndarray,
    *,
    null: float = 0,
    level: float = 0.95,
) -> dict[str, float]:
    estimate = float(contrast @ result.beta)
    variance = float(contrast @ result.beta_cov @ contrast)

    se = math.sqrt(max(variance, 0))

    if se > 0:
        z = (estimate - null) / se
    else:
        z = np.nan

    pvalue = 2 * stats.norm.sf(abs(z))

    diff = stats.norm.ppf(1 - (1 - level) / 2)

    return {
        "estimate": estimate,
        "SE": se,
        "z.ratio": z,
        "p.value": pvalue,
        "lower.CL": estimate - diff * se,
        "upper.CL": estimate + diff * se,
    }


def estimated_marginal_means(
    result: MixedModelResult, models: Sequence[str], criterion: str
) -> pd.DataFrame:
    rows = []
    for model in models:
        row = linear_estimate(result, model_design_vector(result, model))
        rows.append(
            {
                "criterion": criterion,
                "model": model,
                "emmean": row.pop("estimate"),
                "df": np.inf,
                **row,
            }
        )
    return pd.DataFrame(rows)


def fit_crossed_mixed_model(
    df: pd.DataFrame,
    outcome: str,
    *,
    fixed_formula: str = "C(model)",
    random_effects: Sequence[str] = RANDOM_EFFECTS,
    maxiter: int = 2000,
) -> MixedModelResult:
    """Fit a mixed-effects model with crossed random intercepts."""

    columns = [outcome, *random_effects]

    if "model" in fixed_formula:
        columns.append("model")

    if "criterion" in fixed_formula:
        columns.append("criterion")

    data = df[columns].dropna().copy()
    data = data.rename(columns={outcome: "_outcome"})

    data["_outcome"] = pd.to_numeric(data["_outcome"])

    for variable in random_effects:
        data[variable] = data[variable].astype("category")

    if "model" in data:
        model_levels = df["model"].dropna().drop_duplicates()
        data["model"] = pd.Categorical(
            data["model"],
            categories=model_levels,
        )

    model = smf.mixedlm(
        f"_outcome ~ {fixed_formula}",
        data=data,
        groups=np.ones(len(data)),
        re_formula="0",
        vc_formula={variable: f"0 + C({variable})" for variable in random_effects},
        use_sparse=True,
    )

    fit = model.fit(
        reml=True,
        method="powell",
        maxiter=maxiter,
        disp=False,
    )

    fixed_names = list(fit.fe_params.index)

    return MixedModelResult(
        fit=fit,
        data=data,
        design_info=fit.model.data.design_info,
        fixed_names=fixed_names,
        beta=fit.fe_params.to_numpy(),
        beta_cov=fit.cov_params().loc[fixed_names, fixed_names].to_numpy(),
        converged=fit.converged,
    )


def average_model_design_vector(
    result: MixedModelResult,
    model: str,
) -> np.ndarray:
    """Return the average fixed-effect design vector for a model."""

    if "criterion" in result.data.columns:
        criteria = result.data["criterion"].dropna().drop_duplicates().tolist()

        new_data = pd.DataFrame(
            {
                "model": [model] * len(criteria),
                "criterion": criteria,
            }
        )
    else:
        new_data = pd.DataFrame({"model": [model]})

    design_matrix = patsy.build_design_matrices(
        [result.design_info],
        new_data,
        return_type="dataframe",
    )[0]

    return design_matrix.to_numpy().mean(axis=0)


def pairwise_model_contrasts(
    result: MixedModelResult,
    models: Sequence[str],
    criterion: str,
) -> pd.DataFrame:

    rows = []

    for model_a, model_b in combinations(models, 2):
        vector_a = average_model_design_vector(result, model_a)

        vector_b = average_model_design_vector(result, model_b)

        # model A - model B
        contrast_vector = vector_a - vector_b

        estimate = linear_estimate(result, contrast_vector)

        rows.append(
            {
                "criterion": criterion,
                "model_a": model_a,
                "model_b": model_b,
                "contrast": f"{model_a} - {model_b}",
                "estimate": estimate["estimate"],
                "SE": estimate["SE"],
                "lower.CL": estimate["lower.CL"],
                "upper.CL": estimate["upper.CL"],
                "p.value": estimate["p.value"],
                "df": np.inf,
            }
        )

    return pd.DataFrame(rows)

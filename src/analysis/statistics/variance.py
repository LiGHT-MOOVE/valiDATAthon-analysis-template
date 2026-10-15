import warnings

import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.formula.api as smf


def compute_variance(df, countries, criteria):
    variance_results = []
    variance_components = [
        "model",
        "answer",
        "reviewer",
        "vignette",
        "residual",
    ]

    for country in countries:
        for criterion in criteria:
            model_df = (
                df.loc[df["reviewer_country"] == country]
                .dropna(
                    subset=[
                        criterion,
                        "model",
                        "vignette_id",
                        "reviewer_id",
                        "answer_id",
                    ]
                )
                .reset_index(drop=True)
            )

            if model_df.empty:
                continue

            mixed_model = smf.mixedlm(
                f"{criterion} ~ C(model)",
                data=model_df,
                groups=np.ones(len(model_df)),
                vc_formula={
                    "answer": "0 + C(answer_id)",
                    "vignette": "0 + C(vignette_id)",
                    "reviewer": "0 + C(reviewer_id)",
                },
            )
            with warnings.catch_warnings(record=True) as caught_warnings:
                warnings.simplefilter("always")

                fit = mixed_model.fit(
                    reml=True,
                    method="powell",
                    maxiter=2000,
                )

            warning_messages = [str(w.message) for w in caught_warnings]

            singularity_warning = any(
                any(
                    keyword in message.lower()
                    for keyword in [
                        "singular",
                        "singularity",
                        "covariance is singular",
                        "hessian",
                        "not positive definite",
                    ]
                )
                for message in warning_messages
            )

            boundary_warning = any(
                "boundary of the parameter space" in msg.lower()
                for msg in warning_messages
            )

            hessian_warning = any(
                "hessian" in msg.lower() or "not positive definite" in msg.lower()
                for msg in warning_messages
            )

            singularity_warning = any(
                "singular" in msg.lower() or "singularity" in msg.lower()
                for msg in warning_messages
            )
            fixed_predictions = fit.model.exog @ fit.fe_params

            # Variance of fixed-effect predictions
            fixed_variance = np.var(fixed_predictions, ddof=1)
            result = {
                "country": country,
                "criterion": criterion,
                "n": int(fit.nobs),
                "model": fixed_variance,
                "converged": fit.converged,
                **dict(zip(fit.model.exog_vc.names, fit.vcomp)),
                "residual": fit.scale,
                "boundary_warning": boundary_warning,
                "singularity_warning": singularity_warning,
                "hessian_warning": hessian_warning,
            }

            # total variance
            total_variance = sum(result[component] for component in variance_components)

            result["total_variance"] = total_variance

            # percentages
            for component in variance_components:
                result[f"{component}_%"] = result[component] / total_variance * 100
            variance_results.append(result)

    variance_df = pd.DataFrame(variance_results)

    return variance_df

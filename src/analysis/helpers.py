from collections.abc import Iterable
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd

from analysis.config import AnalysisConfig, MixedModelResult


def criterion_name(criterion: str, config: AnalysisConfig) -> str:
    fallback = criterion.removesuffix("_score").replace("_", " ").title()
    return config.friendly_criteria.get(criterion, fallback)


def format_pvalue(value: float) -> str:
    if pd.isna(value):
        return ""
    return "<0.001" if value < 0.001 else f"{value:.3f}"


def n_pct(n: int, denominator: int) -> str:
    return f"{n} ({n / denominator:.1%})" if denominator else f"{n} (NA)"


def mean_sd(values: Iterable[float]) -> str:
    values = pd.Series(values).dropna()
    return "" if values.empty else f"{values.mean():.2f} ({values.std():.2f})"


def median_iqr(values: Iterable[float]) -> str:
    values = pd.Series(values).dropna()
    if values.empty:
        return ""
    return (
        f"{values.median():.1f} "
        f"[{values.quantile(0.25):.1f}, {values.quantile(0.75):.1f}]"
    )


def export_dataframe(
    data: pd.DataFrame, name: str, config: AnalysisConfig, save_index=False
) -> None:
    timestamp = datetime.now(ZoneInfo("Europe/Zurich")).strftime("%H%M%S")

    if config.save_outputs:
        config.make_dirs()
        data.to_csv(
            config.docs_dir / f"{config.tag}_{name}_{timestamp}.csv", index=save_index
        )


def export_excel(
    data: dict[str, pd.DataFrame | tuple[pd.DataFrame, bool]],
    name: str,
    config: AnalysisConfig,
) -> None:
    """Export multiple DataFrames to separate sheets in one Excel file."""

    if not config.save_outputs:
        return

    timestamp = datetime.now(ZoneInfo("Europe/Zurich")).strftime("%H%M%S")
    config.make_dirs()
    output_path = config.docs_dir / f"{config.tag}_{name}_{timestamp}.xlsx"

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        for sheet_name, value in data.items():
            if isinstance(value, tuple):
                df, save_index = value
            else:
                df, save_index = value, False

            df.to_excel(
                writer,
                sheet_name=sheet_name[:31],
                index=save_index,
            )


def export_styled_table(styled, name: str, config: AnalysisConfig) -> None:
    timestamp = datetime.now(ZoneInfo("Europe/Zurich")).strftime("%H%M%S")

    if config.save_outputs:
        config.make_dirs()
        (config.docs_dir / f"{config.tag}_{name}_{timestamp}.html").write_text(
            styled.to_html(), encoding="utf-8"
        )


def export_figure(fig, name: str, config: AnalysisConfig) -> None:
    timestamp = datetime.now(ZoneInfo("Europe/Zurich")).strftime("%H%M%S")

    if config.save_outputs:
        config.make_dirs()
        fig.savefig(
            config.figures_dir / f"{config.tag}_{name}_{timestamp}.png",
            dpi=config.dpi,
            bbox_inches="tight",
            facecolor="white",
        )


def export_model_fits(fits: dict) -> pd.DataFrame:
    """Extract model convergence and fit diagnostics."""
    rows = []

    for key, model_result in fits.items():
        fitted_model = model_result.fit
        print(vars(fitted_model).keys())
        if isinstance(key, tuple):
            country, criterion = key
        else:
            country = key
            criterion = "safety_score"

        rows.append(
            {
                "country": country,
                "criterion": criterion,
                "converged": model_result.converged,
                "log_likelihood": fitted_model.llf,
                "aic": fitted_model.aic,
                "bic": fitted_model.bic,
            }
        )

    return pd.DataFrame(rows)


def combine_country_results(
    results: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """Combine DataFrames from multiple countries into one DataFrame."""
    return pd.concat(
        [df.assign(reviewer_country=country) for country, df in results.items()],
        ignore_index=True,
    )

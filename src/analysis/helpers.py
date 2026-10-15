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
    data: dict[str, pd.DataFrame],
    name: str,
    config: AnalysisConfig,
    save_index: bool = False,
) -> None:
    """Export multiple DataFrames to separate sheets in one Excel file."""

    if not config.save_outputs:
        return

    timestamp = datetime.now(ZoneInfo("Europe/Zurich")).strftime("%H%M%S")
    config.make_dirs()
    output_path = config.docs_dir / f"{config.tag}_{name}_{timestamp}.xlsx"
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        for sheet_name, df in data.items():
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


def export_model_fits(
    fits: dict[tuple[str, str], MixedModelResult],
) -> pd.DataFrame:
    """Extract model convergence and fit diagnostics."""
    rows = []

    for (country, criterion), model_result in fits.items():
        fitted_model = model_result.fit

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

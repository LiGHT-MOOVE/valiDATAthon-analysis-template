from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import patsy

from config import load_config


@dataclass
class AnalysisConfig:
    """All project-specific settings in one object."""

    dataset_path: Path
    tag: str
    title_tag: str
    output_dir: Path
    irr_weight: str = "linear"
    safety_var: str = "safety_score"
    save_outputs: bool = True
    bootstrap_n: int = 500
    bootstrap_seed: int = 123
    use_cache: bool = True
    cache_dir: Path = Path(".cache/statistical_analysis")
    friendly_models: Mapping[str, str] = field(default_factory=dict)
    friendly_criteria: Mapping[str, str] = field(default_factory=dict)
    model_categories: Mapping[str, str] = field(default_factory=dict)
    order_of_models: tuple[str, ...] = ()
    irr_methods: Mapping[str, str] = field(default_factory=dict)
    analyses: dict[str, bool] = field(
        default_factory=lambda: {
            "adjusted_mean_score": True,
            "safety_pairwise_comparisons": True,
            "win_loss": True,
            "position_effect": True,
            "inter_rater_agreement": True,
            "variance": True,
            "gap_between_scores": True,
        }
    )

    @property
    def figures_dir(self) -> Path:
        timestamp = datetime.now(ZoneInfo("Europe/Zurich")).strftime("%Y%m%d")
        return self.output_dir / "figures" / timestamp

    @property
    def docs_dir(self) -> Path:
        timestamp = datetime.now(ZoneInfo("Europe/Zurich")).strftime("%Y%m%d")
        return self.output_dir / "docs" / timestamp

    def make_dirs(self) -> None:

        for path in (
            self.output_dir,
            self.figures_dir,
            self.docs_dir,
            self.cache_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)


def load_analysis_config() -> AnalysisConfig:
    """Build AnalysisConfig from config.yaml."""
    ROOT = Path(__file__).resolve().parents[2]
    CONFIG_PATH = ROOT / "configs/analysis.yaml"
    config = load_config(CONFIG_PATH)

    analysis = config.get("analysis", {})
    cache = config.get("cache", {})

    paths = config["paths"]

    return AnalysisConfig(
        dataset_path=ROOT / paths["analysis_file"],
        tag=config["project"]["name"],
        title_tag=config["project"]["name"].upper(),
        output_dir=ROOT / paths["outputs"],
        safety_var=analysis.get("safety_var", "safety_score"),
        save_outputs=analysis.get("save_outputs", True),
        bootstrap_n=analysis.get("bootstrap_iterations", 500),
        bootstrap_seed=analysis.get("bootstrap_seed", 123),
        use_cache=cache.get("enabled", True),
        cache_dir=ROOT
        / cache.get(
            "directory",
            ".cache/statistical_analysis",
        ),
        friendly_models=config.get("models", {}).get("friendly_names", {}),
        friendly_criteria=config.get("criteria", {}).get("friendly_names", {}),
        model_categories=config.get("model_categories", {}),
        order_of_models=tuple(config["models"]["order"]),
        irr_weight=config.get("agreement", {}).get("weight", "linear"),
        irr_methods=config.get("agreement", {}).get("methods", {}),
        analyses=config.get("analyses", {}),
    )


REQUIRED_NON_NULL_COLUMNS = [
    "review_id",
    "battle_id",
    "reviewer_id",
    "working_group",
    "placement",
    "review_timestamp",
    "vignette_id",
    "answer_id",
    "model",
    "preferred",
    "opposing_answer_id",
    "opposing_model",
    "reviewer_country",
]


@dataclass
class MixedModelResult:
    """Fit plus reusable fixed-effect design information."""

    fit: object
    data: pd.DataFrame
    design_info: patsy.DesignInfo
    fixed_names: list[str]
    beta: np.ndarray
    beta_cov: np.ndarray
    converged: bool


VALID_ANALYSES = {
    "adjusted_mean_score",
    "safety_pairwise_comparisons",
    "win_loss",
    "position_effect",
    "inter_rater_agreement",
    "variance",
    "gap_between_scores",
}


def validate_analysis_config(config: AnalysisConfig) -> None:
    unknown = set(config.analyses) - VALID_ANALYSES

    if unknown:
        raise ValueError(f"Unknown analyses in configuration: {sorted(unknown)}")

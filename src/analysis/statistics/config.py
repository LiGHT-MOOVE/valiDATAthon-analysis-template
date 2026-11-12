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
    """Store project-specific analysis settings."""

    dataset_path: Path
    tag: str
    title_tag: str
    output_dir: Path

    # Analysis settings
    safety_var: str = "safety_score"
    save_outputs: bool = True
    bootstrap_n: int = 2000
    bootstrap_seed: int = 42
    confidence_level: float = 0.95

    # Cache settings
    use_cache: bool = True
    cache_dir: Path = Path(".cache/statistical_analysis")

    # Model configuration
    friendly_models: Mapping[str, str] = field(default_factory=dict)
    model_categories: Mapping[str, str] = field(default_factory=dict)

    # Criterion configuration
    friendly_criteria: Mapping[str, str] = field(default_factory=dict)
    order_of_criteria: tuple[str, ...] = ()

    # Country configuration
    friendly_countries: Mapping[str, str] = field(default_factory=dict)
    order_of_countries: tuple[str, ...] = ()

    # Agreement configuration
    irr_weight: str = "linear"
    irr_methods: Mapping[str, str] = field(default_factory=dict)

    # Selected analyses
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
    def docs_dir(self) -> Path:
        """Return the date-stamped documentation output directory."""
        timestamp = datetime.now(ZoneInfo("Europe/Zurich")).strftime("%Y%m%d")
        return self.output_dir / "docs" / timestamp

    def make_dirs(self) -> None:
        """Create output directories."""
        for path in (
            self.output_dir,
            self.docs_dir,
            self.cache_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)


def load_analysis_config() -> AnalysisConfig:
    """Load and validate settings from configs/analysis.yaml."""
    root = Path(__file__).resolve().parents[3]
    config_path = root / "configs" / "analysis.yaml"
    config = load_config(config_path)

    project = config["project"]
    paths = config["paths"]
    analysis = config.get("analysis", {})
    cache = config.get("cache", {})
    agreement = config.get("agreement", {})

    models = config.get("models", {})
    criteria = config.get("criteria", {})
    countries = config.get("countries", {})

    return AnalysisConfig(
        # Project and paths
        dataset_path=root / paths["analysis_file"],
        tag=project["name"],
        title_tag=project["name"].upper(),
        output_dir=root / paths["outputs"],
        # Analysis settings
        safety_var=analysis.get("safety_var", "safety_score"),
        save_outputs=analysis.get("save_outputs", True),
        bootstrap_n=analysis.get("bootstrap_iterations", 2000),
        bootstrap_seed=analysis.get(
            "bootstrap_seed",
            project.get("random_seed", 42),
        ),
        confidence_level=analysis.get("confidence_level", 0.95),
        # Cache settings
        use_cache=cache.get("enabled", True),
        cache_dir=root / cache.get("directory", "outputs/cache"),
        # Model configuration
        friendly_models=models.get("friendly_names", {}),
        model_categories=models.get("categories", {}),
        # Criterion configuration
        friendly_criteria=criteria.get("friendly_names", {}),
        order_of_criteria=tuple(criteria.get("order", [])),
        # Country configuration
        friendly_countries=countries.get("friendly_names", {}),
        order_of_countries=tuple(countries.get("order", [])),
        # Agreement configuration
        irr_weight=agreement.get("weight", "linear"),
        irr_methods=agreement.get("methods", {}),
        # Selected analyses
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

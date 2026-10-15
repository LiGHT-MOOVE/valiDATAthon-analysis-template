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
    safety_var: str = "safety_score"
    save_outputs: bool = True
    ni_margin: float = -0.20
    ni_alpha: float = 0.025
    figure_size: tuple[float, float] = (8, 5)
    dpi: int = 300
    bootstrap_n: int = 500
    bootstrap_seed: int = 123
    use_cache: bool = True
    cache_dir: Path = Path(".cache/statistical_analysis")
    friendly_models: Mapping[str, str] = field(default_factory=dict)
    friendly_criteria: Mapping[str, str] = field(default_factory=dict)
    model_categories: Mapping[str, str] = field(default_factory=dict)
    category_colors: Mapping[str, str] = field(default_factory=dict)
    order_of_models: tuple[str, ...] = ()

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

    visualization = config.get("visualization", {})

    paths = config["paths"]

    return AnalysisConfig(
        dataset_path=ROOT / paths["analysis_file"],
        tag=config["project"]["name"],
        title_tag=config["project"]["name"].upper(),
        output_dir=ROOT / paths["outputs"],
        safety_var=analysis.get("safety_var", "safety_score"),
        save_outputs=analysis.get("save_outputs", True),
        ni_margin=analysis.get("ni_margin", -0.20),
        ni_alpha=analysis.get("ni_alpha", 0.025),
        figure_size=(
            visualization.get("figure_width", 8),
            visualization.get("figure_height", 5),
        ),
        dpi=visualization.get("dpi", 300),
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
        category_colors=config.get("category_colors", {}),
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

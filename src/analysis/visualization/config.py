"""Configuration management for visualization settings."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from analysis.visualization.style import PlotStyle
from config import load_config


@dataclass
class VisualizationConfig:
    """Store configuration settings for visualizations."""

    project_name: str
    analysis_inputs: dict[str, dict[str, Path]]
    output_dir: Path

    save_outputs: bool
    output_format: str
    dpi: int
    bbox_inches: str

    figure_width: float
    figure_height: float

    font_family: str
    font_title: int
    font_subtitle: int
    font_axis_label: int
    font_tick_label: int
    font_legend: int
    font_annotation: int
    font_panel_label: int
    country_colors: dict[str, str]
    comparison_colors: dict[str, str]
    general_colors: dict[str, str]

    analyses: dict[str, bool]

    @property
    def style(self) -> PlotStyle:
        """Return the plot style settings."""

        return PlotStyle(
            font_title=self.font_title,
            font_subtitle=self.font_subtitle,
            font_label=self.font_axis_label,
            font_tick=self.font_tick_label,
            font_legend=self.font_legend,
            font_value=self.font_annotation,
            primary_color=self.general_colors.get("primary", "#105091"),
            secondary_color=self.general_colors.get("secondary", "#7C7F82"),
            grid_color=self.general_colors.get("grid", "#D9D9D9"),
            country_colors=self.country_colors,
        )

    @property
    def figures_dir(self) -> Path:
        timestamp = datetime.now(ZoneInfo("Europe/Zurich")).strftime("%Y%m%d")
        return self.output_dir / "figures" / timestamp

    def make_dirs(self) -> None:
        """Create output directories when saving figures."""
        if self.save_outputs:
            self.figures_dir.mkdir(parents=True, exist_ok=True)

    def validate_inputs(self, selected_figures: list[str]) -> None:
        """Check that all input files required by selected figures exist."""
        missing_files = []

        for figure_name in selected_figures:
            inputs = self.analysis_inputs.get(figure_name)

            if inputs is None:
                raise ValueError(
                    f"No input files configured for figure '{figure_name}'."
                )

            for analysis_name, path in inputs.items():
                if not path.is_file():
                    missing_files.append(f"{figure_name} / {analysis_name}: {path}")

        if missing_files:
            details = "\n".join(f"- {path}" for path in missing_files)
            raise FileNotFoundError(
                f"Missing statistical result files:\n{details}\n"
                "Run the required statistical analyses before plotting."
            )


def load_visualization_config() -> VisualizationConfig:
    """Load visualization settings from configs/visualization.yaml."""
    project_root = Path(__file__).resolve().parents[3]
    config_path = project_root / "configs" / "visualization.yaml"

    config = load_config(config_path)

    paths = config["paths"]
    analysis_inputs = {
        figure_name: {
            analysis_name: project_root / path for analysis_name, path in inputs.items()
        }
        for figure_name, inputs in paths.get("analysis_inputs", {}).items()
    }
    plots = config["plots"]
    figure = plots["figure"]
    fonts = plots["fonts"]

    return VisualizationConfig(
        project_name=config["project"]["name"],
        analysis_inputs=analysis_inputs,
        output_dir=project_root / paths["outputs"],
        save_outputs=plots.get("save_outputs", True),
        output_format=plots.get("format", "pdf"),
        dpi=plots.get("dpi", 300),
        bbox_inches=plots.get("bbox_inches", "tight"),
        figure_width=figure.get("width", 10),
        figure_height=figure.get("height", 6),
        font_family=fonts.get("family", "sans-serif"),
        font_title=fonts.get("title", 12),
        font_subtitle=fonts.get("subtitle", 11),
        font_axis_label=fonts.get("axis_label", 10),
        font_tick_label=fonts.get("tick_label", 9),
        font_legend=fonts.get("legend", 9),
        font_annotation=fonts.get("annotation", 9),
        font_panel_label=fonts.get("panel_label", 12),
        country_colors=plots.get("countries", {}),
        comparison_colors=plots.get("comparisons", {}),
        general_colors=plots.get("general", {}),
        analyses=plots.get("analyses", {}),
    )

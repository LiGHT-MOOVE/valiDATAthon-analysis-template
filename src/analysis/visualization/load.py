import pandas as pd

from analysis.visualization.config import VisualizationConfig


def load_figure_inputs(
    figure_name: str,
    config: VisualizationConfig,
) -> dict[str, dict[str, pd.DataFrame]]:
    """Load the Excel worksheets required by a figure."""
    loaded_inputs = {}

    for analysis_name, path in config.analysis_inputs[figure_name].items():
        loaded_inputs[analysis_name] = pd.read_excel(
            path,
            sheet_name=None,
        )

    return loaded_inputs

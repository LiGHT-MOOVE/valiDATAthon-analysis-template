from analysis.statistics.config import load_analysis_config
from analysis.visualization.config import load_visualization_config
from analysis.visualization.runner import ANALYSIS_RUNNERS, plot_selected_figures
from utils.print_console import print_success


def main():
    """Plot statistical figures."""

    config = load_visualization_config()
    analysis_config = load_analysis_config()

    # Validate analysis selection before loading the dataset.
    unknown_analyses = set(config.analyses) - set(ANALYSIS_RUNNERS)

    if unknown_analyses:
        raise ValueError(
            f"Unknown analyses in configuration: {sorted(unknown_analyses)}"
        )

    selected_analyses = [
        name for name in ANALYSIS_RUNNERS if config.analyses.get(name, False)
    ]

    if not selected_analyses:
        print_success("No analyses selected. Nothing to run.")
        return

    plot_selected_figures(
        config=config,
        friendly_criteria=analysis_config.friendly_criteria,
        model_categories=analysis_config.model_categories,
    )

    print_success(f"Plots results saved to: {config.figures_dir}")


if __name__ == "__main__":
    main()

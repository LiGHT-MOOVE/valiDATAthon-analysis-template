from analysis.statistics.descriptive import get_analysis_values
from analysis.visualization.config import load_visualization_config
from analysis.visualization.runner import ANALYSIS_RUNNERS, plot_selected_figures
from utils.print_console import print_step, print_success


def main():
    """Plot statistical figures."""

    config = load_visualization_config()

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

    """
    if not analysis_dataset_path.is_file():
        raise FileNotFoundError(
            f"Analysis input file not found: {analysis_dataset_path}"
        )

    print_step(4, "Get analysis characteristics")
    criteria, countries, models, countries_ordered = get_analysis_values(df)
    """

    plot_selected_figures(
        # df=df,
        criteria=[],
        countries=[],
        models=[],
        config=config,
    )

    print_success(f"Plots results saved to: {config.figures_dir}")


if __name__ == "__main__":
    main()

from pathlib import Path

import pandas as pd

from config import ROOT, load_config, validate_config
from utils.print_console import print_info, print_step, print_success

CONFIG_PATH = ROOT / "configs/config.yaml"


def merge_country_datasets(processed_files: list[Path]) -> pd.DataFrame:
    datasets = []

    for file_path in processed_files:
        reviews = pd.read_csv(file_path)
        datasets.append(reviews)
        print(f"Loaded {file_path.name}: {len(reviews):,} rows")

    merged_df = pd.concat(datasets, ignore_index=True)
    merged_df["review_id"] = range(1, len(merged_df) + 1)

    battle_counts = merged_df["battle_id"].value_counts()
    print(battle_counts[battle_counts > 2])

    return merged_df


def main():
    config = load_config(CONFIG_PATH)
    validate_config(config)
    merge_inputs = config.get("merge", {}).get("inputs", [])
    if len(merge_inputs) < 2:
        raise ValueError("Set at least two input files in merge.inputs.")

    processed_files = [(ROOT / path).resolve() for path in merge_inputs]
    if len(set(processed_files)) != len(processed_files):
        raise ValueError("Each file in merge.inputs must be listed only once.")

    merged_df = merge_country_datasets(processed_files)

    processed_data_path = ROOT / config["paths"]["processed_data"]

    processed_data_path.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = processed_data_path / "all_countries_reviews.csv"

    merged_df.to_csv(
        output_path,
        index=False,
    )

    print_success(f"Merged dataset saved to: {output_path}")

    print_step("05", "Merge summary")
    print_info(f"Total rows: {len(merged_df):,}")
    print_info(f"Total columns: {len(merged_df.columns):,}")
    print_info("Rows per country:")
    print(merged_df.groupby("reviewer_country").size().to_string())


if __name__ == "__main__":
    main()

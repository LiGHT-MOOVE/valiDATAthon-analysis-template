import pandas as pd

from config import ROOT, load_config, validate_config
from utils.print_console import print_info, print_step, print_success

CONFIG_PATH = ROOT / "configs/config.yaml"

config = load_config(CONFIG_PATH)
validate_config(config)


processed_data_path = ROOT / config["paths"]["processed_data"]

processed_files = sorted(processed_data_path.glob("*_preprocessed_reviews.csv"))

if not processed_files:
    raise FileNotFoundError(
        f"No processed review datasets found in: "
        f"{processed_data_path}. "
        "Run 02_preprocess_data.py first."
    )


def merge_country_datasets() -> pd.DataFrame:
    """Merge country datasets and preserve country-specific IDs."""

    country_datasets = {}

    for file_path in processed_files:
        print(file_path)
        country = file_path.name.removesuffix("_preprocessed_reviews.csv")
        country_datasets[country] = pd.read_csv(file_path)
        print(f"Loaded {country}: {len(country_datasets[country]):,} rows")

    merged_df = pd.concat(
        country_datasets.values(),
        ignore_index=True,
    )
    # as review_id is sequential in our original datasets
    merged_df["review_id"] = range(1, len(merged_df) + 1)
    battle_counts = merged_df["battle_id"].value_counts()

    battles_more_than_twice = battle_counts[battle_counts > 2]

    print(battles_more_than_twice)
    return merged_df


def main():
    processed_data_path = ROOT / config["paths"]["processed_data"]

    processed_data_path.mkdir(
        parents=True,
        exist_ok=True,
    )

    merged_df = merge_country_datasets()

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

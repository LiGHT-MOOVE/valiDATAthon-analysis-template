from pathlib import Path

import pandas as pd

from utils.print_console import print_error, print_success


def load_dataset(path):
    path = Path(path)

    try:
        df = pd.read_csv(path)
    except pd.errors.EmptyDataError as exc:
        raise ValueError(
            f"The CSV file is empty or contains no readable columns: {path}"
        ) from exc
    except pd.errors.ParserError as exc:
        raise ValueError(
            f"Could not parse the CSV file: {path}. Check its format and delimiters."
        ) from exc

    if df.empty:
        raise ValueError(
            f"The CSV file contains column headers but no data rows: {path}"
        )

    return df


def check_input_files(answers_path, reviews_path):
    missing_files = [
        path for path in [answers_path, reviews_path] if not path.is_file()
    ]

    if missing_files:
        for path in missing_files:
            print_error(f"Input file not found: {path}")

        raise FileNotFoundError(
            f"{len(missing_files)} required input file(s) are missing."
        )

    print_success("All required input files exist.")

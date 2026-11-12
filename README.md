# valiDATAthon Analysis Template

This repository provides a configurable Python workflow for analyzing valiDATAthon data. The scripts in `scripts/` are run individually. Some stages use files produced by earlier scripts, so run the scripts that generate those inputs first. Shared analysis code lives in `src/`, and project settings live in `configs/`.

## Repository layout

| Path | Contents |
| --- | --- |
| `configs/` | Project configuration (`config.yaml`), analysis configuration (`analysis.yaml`), and visualization configuration (`visualization.yaml`). |
| `data/raw/` | Raw Answers and Reviews CSV exports for each country, by default. |
| `data/processed/` | Preprocessed datasets and preprocessing diagnostics, by default. |
| `scripts/` | Python entry points for validation, preprocessing, merging, descriptive analysis, statistical analysis, and figure generation. |
| `src/` | Shared Python code, including data processing, statistics, visualization, configuration loading, and utilities. |
| `outputs/` | Default directory for analysis outputs. |

## Set up the Python environment

With Conda installed, open a terminal in the repository root, where
`requirements.txt` is located.

1. Create a Conda environment with Python 3.11 and pip.

   ```bash
   conda create --name validatathon python=3.11 pip
   ```

2. Activate the environment.

   ```bash
   conda activate validatathon
   ```

3. Install the Python dependencies.

   ```bash
   python -m pip install -r requirements.txt
   ```

If the repository includes Python packaging metadata, install the local project in
editable mode so the scripts can import modules from `src/`.

```bash
python -m pip install -e .
```

Activate `validatathon` again when you open a new terminal to run the analysis.

## Configure a valiDATAthon

Edit [`configs/config.yaml`](configs/config.yaml) to set the project name, random seed, paths, and country inputs. The example configuration also sets the analysis confidence level to `0.95` and figure output to PDF at 300 dpi.

This workflow is intended to be used for one country or multiple countries, please adapt your configuration based on your use case. For each country (could be single country), add an entry under `data.countries` with a `name`, an `answers` filename, and a `reviews` filename. Place both exports in the directory specified by `paths.raw_data` and match their filenames exactly.

```yaml
paths:
  raw_data: data/raw
  processed_data: data/processed
  outputs: outputs

data:
  countries:
    - name: my_country
      answers: my_country - Answers.csv
      reviews: my_country - Reviews.csv
```

The example above shows the path and country settings for one country. The supplied configuration also includes entries for other countries.

## Preprocess country data

[`scripts/02_preprocess_data.py`](scripts/02_preprocess_data.py) prepares the analytic review dataset for one country at a time. From the repository root, with the project imports available in your Python environment, run the script for the configured country. For example:

```bash
python scripts/02_preprocess_data.py --country my_country
```

The script loads and validates the configuration, checks that both input files exist, and loads and validates the raw exports. It uses the Answers and Reviews data to create the analytic review dataset, generates duplicate diagnostics, removes duplicate reviews, and validates the cleaned dataset before saving it. It also prints the counts of raw answers, raw reviews, and cleaned reviews, along with the numbers of unique battles, reviewers, and answers in the cleaned dataset.

With the default paths, the script writes these files. `<country>` is the configured country name.

| Output | Contents |
| --- | --- |
| `data/processed/<country>_preprocessed_reviews.csv` | Validated analytic review dataset after duplicate removal. |
| `data/processed/<country>_reviews_duplicates.csv` | Duplicate reviews identified during preprocessing. |
| `data/processed/diagnostics/<country>_diagnostics_summary.txt` | Text summary of the duplicate diagnostics. |

Repeat preprocessing for each country whose cleaned dataset you plan to use in a later stage.

## Merge country reviews (optional)

Use [`scripts/02b_merge_processed_data.py`](scripts/02b_merge_processed_data.py) to combine preprocessed review datasets from two or more countries. For a single-country analysis, use that country's preprocessed CSV directly.

Run `02_preprocess_data.py` for each country you want to include. In [`configs/config.yaml`](configs/config.yaml), list the CSVs under `merge.inputs`. Enter at least two distinct paths relative to the repository root, using the exact filenames produced by preprocessing.

```yaml
merge:
  inputs:
    - data/processed/reviews_country1.csv
    - data/processed/reviews_country2.csv
```

From the repository root, run:

```bash
python scripts/02b_merge_processed_data.py
```

The script reads the listed files in configuration order, appends their rows, and assigns a new sequential `review_id` starting at 1. It reports the input row counts, flags `battle_id` values that occur in more than two merged rows, and summarizes the combined dataset by `reviewer_country`. The output is written to `all_countries_reviews.csv` under `paths.processed_data` (`data/processed/` by default).

The merge script is designed for country datasets produced by the valiDATAthon preprocessing step. If you use it for other datasets, you may need to adapt it.

## Run descriptive analysis

[`scripts/03_descriptive_analysis.py`](scripts/03_descriptive_analysis.py) summarizes the dataset selected in the analysis configuration. After preprocessing, set the analysis dataset path from `configs/analysis.yaml`.

Set `analysis_file` relative to the repository root. Replace the placeholder with the path to your dataset.
```yaml
paths:
  outputs: ..
  # this path should be relative path from you root directory
  analysis_file: your_dataset_path_to_be_analyzed.csv
```
From the repository root, run:

```bash
python scripts/03_descriptive_analysis.py
```

The script checks that the configured input exists, loads it, and validates the columns ending in `_score` and the required non-null columns. It then prepares the data according to the analysis configuration and exports two tables to the `docs/` subdirectory of the configured analysis output directory.

| Export name | Contents |
| --- | --- |
| `missing_values` | Missingness summary for the prepared dataset, exported with its table index. |
| `dataset_characteristic` | Study characteristics table for the prepared dataset. |

## Run statistical analysis

[`scripts/04_statistical_analysis.py`](scripts/04_statistical_analysis.py) runs the statistical analyses enabled in [`configs/analysis.yaml`](configs/analysis.yaml). Set `paths.analysis_file` to a preprocessed country CSV or to the CSV from the optional merge. The script loads and prepares that dataset directly, so it can run independently of the descriptive analysis.

Set `analysis_file` relative to the repository root. Replace the placeholder with the path to your dataset.
```yaml
paths:
  outputs: ..
  # this path should be relative path from you root directory
  analysis_file: your_dataset_path_to_be_analyzed.csv
```
From the repository root, run:

```bash
python scripts/03_descriptive_analysis.py
```

| Setting | What it controls |
| --- | --- |
| `paths.analysis_file` | Input review CSV. Use the exact filename written by preprocessing or merging. |
| `paths.outputs` | Output directory for this analysis run. |
| `analyses` | Which statistical analyses run. Set each entry to `true` or `false`. |
| `analysis` | Safety score column, output saving, bootstrap seed, and confidence level. |
| `cache` | Whether to cache computations and where to store the cache. |
| `models`, `criteria`, and `countries` | Model labels and categories, criterion labels and order, and country labels and order. |
| `agreement` | Agreement methods and weighting when inter-rater agreement is enabled. |

The example configuration enables adjusted mean scores, pairwise safety comparisons, and win–loss analysis. It also includes switches for position effects, inter-rater agreement, variance, and gaps between scores.

From the repository root, run:

```bash
python scripts/04_statistical_analysis.py
```

The script checks the configured analysis names before loading data. If all analyses are disabled, it exits before loading the dataset. Otherwise, it validates the score columns and required non-null fields, prepares the data, identifies the criteria, countries, and models present, and runs the enabled analyses.

Set `analysis.save_outputs: true` to save the statistical results in the `docs/` subdirectory of the configured output directory. For example, with `paths.outputs: outputs/`, look in `outputs/docs/`.

## Generate figures

[`scripts/05_generate_figures.py`](scripts/05_generate_figures.py) creates figures from previously exported statistical results. Run the relevant analyses first, or use existing results files. In [`configs/visualization.yaml`](configs/visualization.yaml), set `paths.analysis_inputs` to the actual results files for each figure group you enable. The example uses Excel workbooks (`.xlsx`) and includes dated output directories. Update the paths to match your run.

Set the figure groups you want to generate to `true` under `plots.analyses`.

| Figure group | Required statistical results |
| --- | --- |
| `llm_performance` | Adjusted mean scores and pairwise safety comparisons. |
| `h2h_comparison` | Head-to-head win–loss analysis. |
| `irr_and_variance` | Inter-rater agreement and variance components. |
| `consistency_of_scores_over_same_response` | Gaps between scores for the same response. |
| `effect_of_response_display_position` | Response display position analysis. |

From the repository root, run:

```bash
python scripts/05_generate_figures.py
```

The script reads criterion display names and model categories from [`configs/analysis.yaml`](configs/analysis.yaml). Use `plots` in the visualization configuration to set figure dimensions, fonts, colors, and export options. With `plots.save_outputs: true`, figures are written to `paths.figures`. The example saves PDF figures to `outputs/eth/figures/` with a DPI setting of 300.


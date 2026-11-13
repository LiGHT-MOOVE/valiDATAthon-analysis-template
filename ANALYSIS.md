# valiDATAthon analysis guide

This guide explains what the analysis template estimates from expert reviews of responses to clinical vignettes. The workflow covers response quality, safety ratings, and head-to-head preferences, as well as how consistently experts score the same responses. See [README.md](README.md) for setup and commands.

## Analysis dataset

Preprocessing combines the Answers and Reviews exports into a cleaned review dataset for countries and records duplicate diagnostics. Analyze a country-specific CSV directly, or combine selected country datasets with the optional merge script. Set `paths.analysis_file` in [`configs/analysis.yaml`](configs/analysis.yaml) to the dataset you want to analyze. A combined input can support country-specific estimates. Check the country field in each result table before interpreting estimates across settings.

The same reviewer can score multiple responses, and the same response can receive ratings from multiple reviewers. Review, reviewer, response, vignette, and battle identifiers describe different parts of the design. Preserve these relationships when preparing inputs and check that identifiers represent the intended units across countries.

## Descriptive analysis

`scripts/03_descriptive_analysis.py` validates and prepares the configured dataset, then exports a missingness summary (`missing_values`) and a study characteristics table (`dataset_characteristic`). Use these tables to check the composition and completeness of the prepared data before interpreting results. Pay particular attention to missing ratings and the amount of data available for comparisons within each country or criterion.

## Statistical analyses

`scripts/04_statistical_analysis.py` prepares the configured dataset and runs the analyses enabled under `analyses` in `configs/analysis.yaml`. Choose the analyses that match your study design and evaluation questions.

| Configuration key | Question | How to read the result |
| --- | --- | --- |
| `adjusted_mean_score` | What average score does each response source receive on each criterion after model-based adjustment? | Report the estimated means with confidence intervals. Use an estimated contrast and its interval to assess a difference between sources. |
| `safety_pairwise_comparisons` | How do response sources compare on the rating criterion configured as `analysis.safety_var`? | Read each estimate in the stated subtraction order. When the study specifies a non-inferiority margin, compare the lower confidence bound for the model-minus-benchmark difference with that margin. |
| `win_loss` | Which response source do reviewers prefer in direct comparisons? | Read preference results by matchup and consider how many comparisons contributed. In the primary healthcare study, the winning percentage counted each tie as half a win. |
| `position_effect` | Does the preferred response vary with its display position? | Interpret the result alongside the procedure used to assign responses to display positions and the balance of those assignments. |
| `inter_rater_agreement` | How closely do reviewers score the same response? | Interpret each coefficient with its weighting scheme and the amount of overlapping review data. The example configuration specifies Gwet’s AC2 and Krippendorff’s alpha with linear weights. Report the coefficients separately because they use different chance-agreement models. |
| `variance` | How much rating variability is associated with the sources represented in a fitted model? | Read components in the context of the model specification. A small reviewer component indicates little variation in reviewers’ average scoring tendencies under the model. Reviewers can still disagree on individual responses. |
| `gap_between_scores` | How far apart are reviewers’ scores for the same response? | Interpret score differences on the original rating scale. This complements the chance-adjusted agreement coefficients. |

### Adjusted scores and safety criteria

In the primary healthcare study, linear mixed-effects models were fitted separately by country and evaluation criterion. Response source was included as a fixed effect, with random intercepts for vignette, reviewer, and care plan. Adjusted means were estimated from the fitted models. For a new study, check that the model specification matches the way vignettes, responses, and reviewers were assigned.

Specify any performance threshold or safety non-inferiority margin before examining the results. In the primary healthcare study, the performance rule required the lower confidence bound of the adjusted mean to exceed zero for each of five criteria. For safety, the study used a margin of −0.2 on the model-minus-human score difference. These thresholds are study-specific. A safety comparison summarizes expert ratings under the evaluation protocol. Individual responses can receive low safety ratings even when their source meets the benchmark on average.

### Agreement and rating variability

Agreement and score-gap analyses require multiple reviewers to rate the same response. Check the amount of overlap within each group you report. Document the coefficient and weighting scheme, since both affect how disagreements are summarized. Variance components answer a different question by partitioning variability across the sources included in the fitted model. For the primary healthcare study, those sources included care plan, vignette, reviewer, and residual variation, with response source included as a fixed effect.


### Analysis limitation
The current workflow does not model differences between vignette topics. Results therefore reflect the mix of topics in the analyzed dataset. To examine variation by topic, users can extend the workflow easily.


## Report and visualize results

- Report estimates with confidence intervals where available, along with the number of observations or comparisons that contributed. Document the confidence level and, for bootstrap intervals, the resampling unit and seed.
- Record the input dataset, enabled analyses, score definitions, agreement settings, and any prespecified thresholds so the run can be reproduced.
- With `analysis.save_outputs` enabled, statistical tables are saved under the configured analysis output directory. In [`configs/visualization.yaml`](configs/visualization.yaml), point `paths.analysis_inputs` to those files for the figure groups enabled under `plots.analyses`. Then run `scripts/05_generate_figures.py`.


# Annual foundation: implementation and validation

Completed November 3, 2026. Scope: verify housing data and rebuild annual 1991–2024 comparisons (steps 1–2). Changes are local and uncommitted in the original repository.

## What changed

- `build_annual.py`: reproducible pipeline using Python's standard library.
- `data/raw/fhfa_master_official.csv` and metadata: untouched FHFA download and checksum. Rebuild checks the checksum before using it.
- `data/annual`: annual housing, income and comparison CSVs; dedicated SQLite database; build report.
- `annual_comparison.ipynb`: executed annual analysis with interactive area selection and editable year/geography table.
- `reports/annual_growth_explorer.html`: standalone interactive chart with all 152 areas, including explicitly housing-only metro/division views.
- README now directs readers to the annual rebuild and labels earlier findings as historical.

## Root cause verified

Git commit `1a21d3b` subtracted exactly 100 from `index_nsa` in all 131,540 rows relative to initial commit `5a5dfa5`. All seasonally adjusted values were unchanged. The local field therefore ceased to be a raw index despite keeping its name. Subtraction of 100 can represent growth only when the series baseline is actually 100; it is not a general rebasing method.

The newly downloaded FHFA release also revises historical observations. The rebuild uses its unmodified seasonally adjusted values and does not attempt to reconstruct raw values from the transformed file. Changes relative to old charts reflect both the annual methodology and source revisions.

Source: https://www.fhfa.gov/hpi/download/monthly/hpi_master.csv

Retrieved UTC: 2026-11-04T01:07:08.144656+00:00

SHA-256: `5b60e562c74211475d6bad8f59d24c74316f31f956d922f6e9d97065393b0feb`

## Annual method

Select traditional, purchase-only, quarterly HPI for the United States, all states and D.C., and FHFA MSA/division series. Calculate the arithmetic mean of all four seasonally adjusted quarterly indices. Missing/invalid quarters cannot produce a complete annual average. Rebase each series against its own 1991 annual average, then compute growth as `(annual / baseline - 1) * 100`.

Explicitly select the current-dollar section of the existing Census `h08.csv`; ignore the later 2024-dollar section. Join by geographic level, identifier, and year. Metro income stays missing. Store raw annual indices, rebased indices, growth percentages, and percentage-point differences in separate fields.

## Verified results

- 5,168 unique area-year housing records: 152 areas × 34 years.
- 1 national series, 50 states plus D.C., and 100 metro/division series.
- 1,768 national/state/DC annual income records; no gaps.
- No incomplete housing years in the selected official snapshot.
- Exactly 3,400 metro/division records without income, retained rather than dropped or imputed.
- U.S. 2024 housing annual index: 415.9150; housing growth since the 1991 annual baseline: 314.64%.
- U.S. 2024 median household income: $83,730; income growth since 1991: 177.90%.

## Validation evidence

All 11 unit tests pass: annual mean/baseline, missing quarter, duplicate quarter, nonpositive and nonfinite indices, missing baseline, series filtering, nominal versus real separation, duplicate income geography, missing metro income, and identifier joins/gap calculation.

A separate reviewer recomputed the pipeline in memory and matched every saved CSV cell and SQLite row; no important issues were found. Independent checks confirmed sample annual means against four raw source observations, zero growth at the 1991 baseline, all unique keys, missing-income totals, and SQLite integrity. All four notebook code cells executed, and the notebook passed format validation. A static national chart preview was visually inspected; the HTML was generated with its plotting library embedded. Browser click testing was not performed.

Commands:

```powershell
python build_annual.py
python -m unittest discover -s tests -v
```

Open `annual_comparison.ipynb` from the repository root, or open `reports/annual_growth_explorer.html` in a browser.

## Remaining work

Dollar home prices/values and price-to-income ratios have not been added. Matching metro income still needs sourcing and geography mapping. City-proper views are not equivalent to these FHFA metro/division series. The income file was preserved from the repository; it has not been refreshed or independently checked against the latest Census release. Reassess historical README conclusions using the new annual data before citing them.

The original datasets, databases and notebooks are preserved. Git branch creation was denied by the environment; no commit, push, or merge was performed.

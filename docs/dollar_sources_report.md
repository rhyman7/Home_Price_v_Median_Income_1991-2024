# Dollar housing values and metro income: sourcing results

Completed November 3, 2026. The project now has a separate, reproducible dollar comparison panel sourced from Census ACS 1-year estimates. Existing housing-growth charts and historical data remain unchanged.

## What is now available

- **Median owner-occupied home value:** ACS B25077. This is a survey estimate of home value, not a transaction sale price or Zillow typical home value.
- **Median household income:** ACS B19013, from the same annual release and geography as the housing value.
- **Home-value-to-income ratio:** home value divided by annual median household income, only where both are usable.
- Margins of error, original Census geography codes/names, source references, and missing-data reasons.

The full target grid retains all 5,168 records (152 areas × 34 years), including unavailable observations. 2,640 have usable paired dollar estimates. The national series and all 50 states plus D.C. have 19 annual observations each: 2005–2019 and 2021–2024. Metro coverage varies because some current identifiers did not exist in older releases. All 100 project metro/division areas have matched observations in 2023 and 2024.

## Coverage by year

Counts are paired home value and income estimates for current project identifiers. “States” includes D.C.

| Year | National | States/DC | Metro/division |
|---|---:|---:|---:|
| 2005 | 1 | 51 | 81 |
| 2006 | 1 | 51 | 81 |
| 2007 | 1 | 51 | 81 |
| 2008 | 1 | 51 | 81 |
| 2009 | 1 | 51 | 81 |
| 2010 | 1 | 51 | 82 |
| 2011 | 1 | 51 | 82 |
| 2012 | 1 | 51 | 82 |
| 2013 | 1 | 51 | 88 |
| 2014 | 1 | 51 | 88 |
| 2015 | 1 | 51 | 88 |
| 2016 | 1 | 51 | 88 |
| 2017 | 1 | 51 | 88 |
| 2018 | 1 | 51 | 88 |
| 2019 | 1 | 51 | 91 |
| 2020 | 0 | 0 | 0 |
| 2021 | 1 | 51 | 91 |
| 2022 | 1 | 51 | 91 |
| 2023 | 1 | 51 | 100 |
| 2024 | 1 | 51 | 100 |

1991–2004 have no ACS 1-year observations in this dataset. Standard ACS 1-year estimates were not released for 2020; experimental data and five-year estimates were deliberately not substituted. These gaps do not remove the older national/state income already used by the project's separate HPI-growth analysis.

## Geographic matching

Only exact geographic codes and levels are matched: nation, state, CBSA (310), or metro division (314). A division is never substituted with its parent metro area. Earlier observations retain their Census name and are marked `historical_not_harmonized`. An unchanged code is not proof that county membership stayed unchanged. Ratios use the same ACS geography within each year, but cross-year metro comparisons are not certified as constant-boundary comparisons against FHFA's current geography series.

Current metro/division identifiers with fewer than 19 paired years:

| Area | Code | Paired years | First paired year |
|---|---|---:|---:|
| Anaheim-Santa Ana-Irvine, CA (MSAD) | 11244 | 11 | 2013 |
| Arlington-Alexandria-Reston, VA-WV (MSAD) | 11694 | 2 | 2023 |
| Atlanta-Sandy Springs-Roswell, GA (MSAD) | 12054 | 2 | 2023 |
| Boston, MA (MSAD) | 14454 | 11 | 2013 |
| Chicago-Naperville-Schaumburg, IL (MSAD) | 16984 | 5 | 2019 |
| Cleveland, OH | 17410 | 2 | 2023 |
| Dayton-Kettering-Beavercreek, OH | 19430 | 5 | 2019 |
| Elgin, IL (MSAD) | 20994 | 11 | 2013 |
| Everett, WA (MSAD) | 21794 | 2 | 2023 |
| Frederick-Gaithersburg-Bethesda, MD (MSAD) | 23224 | 5 | 2019 |
| Lakewood-New Brunswick, NJ (MSAD) | 29484 | 2 | 2023 |
| Marietta, GA (MSAD) | 31924 | 2 | 2023 |
| Montgomery County-Bucks County-Chester County, PA (MSAD) | 33874 | 11 | 2013 |
| New York-Jersey City-White Plains, NY-NJ (MSAD) | 35614 | 11 | 2013 |
| North Port-Bradenton-Sarasota, FL | 35840 | 14 | 2010 |
| St. Petersburg-Clearwater-Largo, FL (MSAD) | 41304 | 2 | 2023 |
| Tampa, FL (MSAD) | 45294 | 2 | 2023 |
| Warren-Troy-Farmington Hills, MI (MSAD) | 47664 | 11 | 2013 |
| Washington, DC-MD (MSAD) | 47764 | 2 | 2023 |

All additional older Census metro/division records are preserved in `acs_source_records.csv`, even when they do not match the current FHFA selection. No fuzzy name matching, historical interpolation, or backward dollar estimates were used.

## Keep the income sources distinct

The new dollar panel uses ACS for every level. It does not silently replace or splice the historical Census CPS-based income series used by the earlier growth notebook. For example, U.S. 2024 ACS income is **$81,604**, while the project's existing historical income file reports $83,730. These are different surveys, not a calculation error.

U.S. 2024 median owner-occupied home value is **$360,600**, giving a descriptive value-to-income ratio of **4.42**. This ratio compares two population medians; it does not measure an individual household's mortgage affordability. No statistical margin of error for the ratio has been calculated.

## Files and reproduction

In the project:

- `data/dollars/acs_dollar_comparison.csv`: full selected-area panel.
- `data/dollars/coverage_by_area.csv`: available and missing years for each area.
- `data/dollars/acs_source_records.csv`: all sourced records and original raw estimate/MOE values.
- `data/dollars/housing_income_dollars.db`: the paired panel as a SQLite table.
- `data/dollars/coverage_report.json`: machine-readable counts and rules.
- `data/raw/acs` and `data/raw/acs_archive`: source snapshots, URLs, checksums, and archive extraction records.

Rebuild from saved sources without network access:

```powershell
python build_dollar_data.py
python -m unittest discover -s tests
```

Source acquisition scripts are `scripts/download_acs_recent.py` and `scripts/download_acs_archive.py`. Archive extraction also requires the optional packages in `requirements-sourcing.txt`. Existing snapshots are reused. The Census API required a key; public summary files supplied the same published tables without an API key.

## Sources

- [ACS summary-file documentation](https://www.census.gov/programs-surveys/acs/data/summary-file.html)
- [2024 table-based bulk data](https://www2.census.gov/programs-surveys/acs/summary_file/2024/table-based-SF/data/1YRData/)
- [ACS 1-year coverage](https://www.census.gov/data/developers/data-sets/acs-1year.html)
- [2020 experimental release](https://www.census.gov/programs-surveys/acs/data/experimental-data/1-year.html)
- [2023 geographic boundaries](https://www.census.gov/programs-surveys/acs/geography-acs/geography-boundaries-by-year.2023.html)
- [ACS versus CPS](https://www.census.gov/topics/income-poverty/poverty/guidance/data-sources/acs-vs-cps.html)

## Validation completed

All **36 tests passed**, including annual calculations, geographic matching, missing/censored values, duplicate rejection, archive layouts, and source integrity. The archive audit checked 15 years and 2,355 referenced files with no errors. The recent 12 source files and archived extraction are checksum-verified during the build.

An independent output check recomputed all **2,640 available value-to-income ratios** from saved source records and verified every column of all **5,168 CSV and SQLite rows**. SQLite integrity passed. The full retained source table contains 11,302 observations. National/state coverage is 19 years per area, and all 152 selected areas have paired estimates in both 2023 and 2024.

A separate code reviewer identified duplicate-source handling as an improvement; it was added with a regression test. Earlier notebooks, datasets, and databases were preserved. Changes are local and uncommitted; nothing was pushed to GitHub.

## Next use

The source data is ready for dollar-value views. The existing interactive growth explorer has not yet been expanded to display these new measures. Use the new panel for that next step, with explicit source labels and geography/gap flags. Keep FHFA price growth and ACS median home values as distinct measures.

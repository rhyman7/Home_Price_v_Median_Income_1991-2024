# Historical metropolitan household income: extraction and matching audit

This supplements the housing project with official Census household-income observations. It does not replace the national/state CPS series, create a metro 1991 baseline, or manufacture a metro growth series. The explorer integrates these records in its Household income view.

## Results

The county-composition audit covers all 100 project metropolitan areas/divisions. Twenty-seven have an exact county-set counterpart in the June 1999 metropolitan delineations. For these areas, 129 usable observations were extracted for 1999–2004:

| Income year | Matched project areas | Dollar basis |
|---|---:|---|
| 1999 | 27 | 1999 dollars; Census 2000 SF3 |
| 2000 | 15 | 14 in 2003 dollars; Tucson in 2002 dollars |
| 2001 | 15 | 14 in 2003 dollars; Tucson in 2002 dollars |
| 2002 | 24 | 2002 dollars; annual ACS testing program |
| 2003 | 24 | 2003 dollars; annual ACS testing program |
| 2004 | 24 | 2004 dollars; annual ACS testing program |

There are 99 early current-dollar observations and 30 constant-dollar observations. Do not mix the constant-dollar observations with a nominal income growth line. The original estimate and dollar year are retained explicitly; no inflation conversion, interpolation, or median aggregation has been applied.

The full supplemental panel has 3,400 rows: 100 areas × 34 years. It combines these early observations with 1,652 already-sourced ACS income observations for 2005–2019 and 2021–2024. Every missing area/year remains present with a reason. The recent ACS records retain their existing historical-boundary warning; their same-code match is not a new county-boundary verification.

## Files

- `data/historical_metro_income/verified_early_observations.csv`: the 129 matched early observations, with source URLs and dollar year.
- `data/historical_metro_income/metro_income_1991_2024.csv`: full supplemental metro income panel, including missing years.
- `data/historical_metro_income/coverage_by_area.csv`: available years, constant-dollar bases, and missing years for each project area.
- `data/historical_metro_income/boundary_audit.csv`: all 100 area comparisons, including old/current county FIPS sets and differences.
- `data/historical_metro_income/source_observations.csv`: all extracted source records, including unmatched historical geographies and unavailable estimates.
- `data/historical_metro_income/validation.json`: counts and validation summary.
- `data/raw/early_metro_income/`: original Census sources, directory listings, documentation, and SHA-256 manifest.

## Source and matching rules

1. **1999 income:** Census 2000 Summary File 3, variable P053001. The census year is 2000, but the income reference year is 1999. Extracted from national segment 06 and joined by LOGRECNO to summary levels 380 and 385, geographic component 00, characteristic iteration 000. The field position is derived from the original Census table matrix, not guessed. Sources: [SF3 national files](https://www2.census.gov/census_2000/datasets/Summary_File_3/0_National/), [table definitions](https://api.census.gov/data/2000/dec/sf3/groups/P053.html).
2. **2000–2001:** ACS testing-program comparison profiles. The [2000–2003 archive](https://www2.census.gov/acs2003/Profiles/2000-2003_Profiles/) reports separate annual estimates in 2003 dollars, not a pooled four-year estimate. Tucson's additional observations come from [2000–2002](https://www2.census.gov/acs2002/Profiles/2000-2002/380CMSAMSA/38000US8520.xls) and [2001–2002](https://www2.census.gov/acs2002/Profiles/2001-2002/380CMSAMSA/38000US8520.xls) comparison profiles in 2002 dollars. The significance asterisk is removed from the numeric value but preserved in the raw source record.
3. **2002–2004:** Annual economic profiles, row explicitly labeled “Median household income (dollars).” Estimates and published lower/upper confidence bounds are retained. Annual releases are preferred over inflation-adjusted comparison tables for the same year. Sources: [2002 profiles](https://www2.census.gov/acs2002/Profiles/2002%20Profiles/), [2003 profiles](https://www2.census.gov/acs2003/Profiles/2003_Profiles/), [2004 profiles](https://www2.census.gov/acs2004/Profiles/2004_Single_Year_Profile/).
4. **Geography:** Compare the county FIPS sets in the [June 1999 delineation](https://www2.census.gov/programs-surveys/metro-micro/geographies/reference-files/1999/historical-delineation-files/99mfips.txt) with the [July 2023 delineation](https://www2.census.gov/programs-surveys/metro-micro/geographies/reference-files/2023/delineation-files/list1_2023.xlsx) used for the project's current FHFA areas. The [2004 ACS geography notes](https://www2.census.gov/acs2004/2004_geography_notes.doc) confirm use of June 30, 1999 metro definitions. Any historical area using partial counties/towns is rejected as an exact county match. CMSA county sets include all constituent PMSAs. Name similarity is never sufficient to join data.
5. A matching county set means matching county composition, not a claim that every county boundary polygon is unchanged since 1999. Survey methods and population universes also differ between decennial and ACS products. Series identity remains explicit.

## Gaps and limits

- **1991–1998:** no observations added. This extraction does not establish that no historical estimates exist; it does not supply a comparable annual series for these project areas.
- **73 unmatched current areas:** no old-area income is substituted. The audit lists a county-overlap candidate solely to explain the mismatch. That candidate is not a verified match.
- **Sparse early ACS coverage:** the testing program did not publish all areas. Suppressed/unavailable entries are kept missing, not zero.
- **2020:** no standard ACS 1-year observations are inserted. The experimental estimates and five-year estimates are not substituted for a standard annual estimate.
- No county medians are averaged, and no family-income or per-capita-income measure is relabeled household income.
- These are supplemental income data. No historical home-value ratios were calculated, and the Household income view keeps sources and dollar bases separate.

## Reproduce

Install `requirements-sourcing.txt`, then run:

```text
python scripts/download_early_metro_income.py
python build_historical_metro_income.py
python -m unittest discover -s tests
node --test tests/explorer_model.test.cjs
```

The build is offline once sources are downloaded and verifies the source checksums. Validation checks unique area/year keys, correct source labels, current/constant dollar bases, suppression handling, exact county-set matching, and confidence intervals. Original sources are retained for review.

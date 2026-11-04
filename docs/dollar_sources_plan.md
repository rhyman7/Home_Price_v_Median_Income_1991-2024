# Dollar housing values and metro-income sourcing

Authorized scope: obtain usable dollar housing values and metro household income, verify geographic/year coverage, add sourced data and gaps before expanding charts.

Choice: ACS 1-year B25077 median owner-occupied home value and B19013 median household income, paired from the same release/geography. Preserve CPS-based long-run national/state income separately. These housing values are owner-reported estimates, not sale prices or Zillow typical values. Public bulk files avoid API-key requirements. Use all available years 2005–2019 and 2021–2024, retaining 1991–2024 slots and explicit missing reasons. Do not use 2020 experimental estimates or silently substitute five-year estimates.

Map only identifiers; never fuzzy-match a metro division to its parent MSA. Preserve Census names and original IDs. Earlier metro boundaries are not harmonized to current FHFA boundaries; paired ACS value/income ratios remain same-release comparisons, not verified constant-boundary time series. No growth from 1991 without a baseline.

Implementation: immutable raw files + source manifests; archived-sequence adapter and recent table-based adapter; build_dollar_data.py; tests/test_dollar_data.py; data/dollars panel, coverage, and SQLite; report and README update. Keep previous outputs/notebooks unchanged.

Checks: censored/suppressed estimates cannot become exact ratios; code identity includes summary level; duplicate input rejected; retain missing years and metro code changes; source hashes checked; complete recent matches; tests and independent source-row spot checks.

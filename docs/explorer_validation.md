# Explorer validation — November 3, 2026

The offline explorer now offers ACS dollar values, home-value-to-income ratios, and growth since 1991, with shared location/year controls, annual tables, and an area CSV download. All assets and 5,168 records are embedded in the HTML.

Validation: 41 Python tests and 8 JavaScript tests passed; git diff --check passed. Independent code review identified the notebook export overwriting the enhanced report; the export now calls build_explorer.build(). Browser checks confirmed national 2024 values ($360,600, $81,604, 4.42x), 2020 missing-data notice, 1991 zero growth baseline, state and metro selection, metro income-growth unavailability, and the missing exact-geography notice for Arlington in 2021. Desktop layout was visually inspected. Mobile layout and CSV download were not browser-tested.

Coverage remains limited by the sources: ACS dollars start in 2005 and omit standard 2020 estimates; historical metro boundaries are not harmonized; no comparable 1991 metro-income baseline is supplied. Home values are not sale prices. ACS income remains separate from the historical income series used for growth.

Rebuild with python build_explorer.py after rebuilding the annual or dollar data. The notebook also invokes that builder. Changes are local and have not been pushed to GitHub.

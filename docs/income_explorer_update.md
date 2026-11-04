# Household income explorer update

The explorer now embeds the 3,400-row supplemental metro-income panel alongside the existing housing and paired ACS panels. All 5,168 location/year records remain available. It adds an income-only tab and opens that tab automatically when selecting metro geography.

Early records include 129 usable observations across 27 current project areas: 27 in 1999, 15 each in 2000 and 2001, and 24 each in 2002, 2003, and 2004. Thirty observations use constant dollars. The chart groups traces by source and dollar basis, keeps gaps, and exposes the dollar year in the cards, annual table, and CSV export. National/state income in this tab continues to use the historical Census series.

Housing/income growth since 1991 and paired ACS home-value ratios keep their original inputs. No metro baseline or early ratio is manufactured. Historical selected-year amounts now show available metro income with its dollar basis, while the growth chart still reports unavailable income growth.

The Pages package includes the explorer, updated findings, full metro-income CSV, area coverage CSV, county-boundary audit CSV, and source report. The project README and generated findings describe this coverage.

Validation: 49 Python tests and 9 JavaScript tests passed. Headless Chrome checks confirmed San Diego's $47,067 income in 1999 and $50,630 in 2000 (2003 dollars), missing 1991/2020 income, unmatched Albany 1999, unchanged metro growth behavior, and national 1991 income of $30,130. Desktop and mobile charts rendered without page errors or horizontal page overflow. Screenshots were inspected. The comparison-profile and single-year 2003 extracts also agreed for all 14 overlapping records in the source audit.

Source details: `docs/historical_metro_income_sources.md`. The published website's availability must be checked separately after pushing the Pages branch.

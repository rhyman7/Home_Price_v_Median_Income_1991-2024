# National income display update

User's revised request: remove local income from the site and use the same national median household income for every location and every year, 1991–2024.

- [x] Transform the explorer's published data to national income only; retain source research files separately. Recompute growth gaps and ratios against the national series. Test replacement even when local income exists, missing home values, and missing national years.
- [x] Update every chart, card, annual table, CSV and methodology label. Replace the old findings landing page with a link to the revised explorer so local-income comparisons are not presented as current site findings.
- [x] Build, run Python and chart-model tests, and check national/state/metro views on desktop and mobile.
- [ ] Publish source and Pages, then verify the live site and downloads.

Constraints: no new income research import; median rather than arithmetic mean; no fabricated home prices; no local income fields in published explorer payload or CSV. Original analytical datasets remain archived in the repository.

Validation: 52 Python tests and 7 chart-model tests pass. Browser checks verified all 5,168 rows, identical national/state/metro income traces, missing housing in 2020, ratio labels, CSV generation, and mobile layout. Independent review found no substantive issues. Publication must remove the three retired local-income downloads from Pages as well as site/.

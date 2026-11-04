# One U.S. income benchmark for every location

The live explorer uses exactly the same historical Census U.S. median household income series for every state and metro area, for every year from 1991 through 2024. Only housing varies by selected location. Median is not an arithmetic mean, and these values are not estimates of local income.

- Income dollars and income growth match the United States selection year for year.
- Housing growth minus U.S. income growth is a percentage-point gap, using the 1991 annual baseline.
- The ratio divides the selected location's ACS median home value by the same year's historical U.S. median household income. It is a national-benchmark comparison, not a same-geography ACS ratio or local affordability measure.
- Missing home values remain missing, including 2020. Income remains available for all 34 years.
- CSV downloads contain only national income fields. Original local-income research stays in the repository as historical source material, but is not used by the live explorer. Older findings based on local income are not the methodology of this site.

Income: the project's saved [historical Census household-income series](https://www.census.gov/data/tables/time-series/demo/income-poverty/historical-income-households.html), current-year dollars. Housing: [FHFA purchase-only seasonally adjusted HPI](https://www.fhfa.gov/data/hpi/datasets), annual four-quarter averages, and [ACS B25077 home values](https://www.census.gov/programs-surveys/acs/data/summary-file.html). Source snapshots have not been refreshed in this display update.

Rebuild: `python build_explorer.py` then `python scripts/build_github_pages.py`.

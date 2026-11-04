# Expanded offline explorer

Authorized next step: add sourced ACS dollar measures to the existing interactive HTML explorer. Keep it local/offline and reproducible.

Shared controls: geography level, area, selected year1991–2024. Three views: ACS dollar values, ACS home-value/income ratio, and existing FHFA/CPS growth since1991. Selected-year cards and34-year chart/table, exportselectedareaCSV. Preserve source labels, MOEs, null gaps, and historicalmetro boundary cautions. Never splice ACS income into CPS growth. Do not compute1991ACSgrowth. Existing notebook export must call new builder instead of overwriting HTML with old figure.

Files: build_explorer.py packages CSV-derived JSON, Plotly runtime, and web/explorer.html + explorer_model.js into reports/annual_growth_explorer.html. Pure model tests use Node's built-in test runner; Python loader tests validate keys/numbers. Browser QA covers nation2024, state, metro, missing2020/1991, ratios, growth, and responsive layout.

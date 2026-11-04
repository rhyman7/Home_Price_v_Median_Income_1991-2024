# Annual housing foundation

Scope approved in chat: verify FHFA source and rebuild annual comparisons for 1991â€“2024.

Use an untouched FHFA snapshot, traditional purchase-only quarterly seasonally adjusted indices, equal-weight annual averages of all four quarters, and 1991 annual-mean baselines. Retain U.S., 50 states, DC, and 100 metro/division series. Parse the nominal section of Census h08 explicitly. Metro income remains missing; do not fabricate dollar housing prices. Preserve historical notebooks and data.

Approach: add a reproducible standard-library Python pipeline, versioned source snapshot and checksum metadata, separate processed files/SQLite database, and an annual-analysis notebook. Updating old notebooks in place would obscure the original analysis; reconstructing indices from transformed local fields would obscure source revisions.

Tasks:
- [x] Test annual means, incomplete/duplicate quarters, invalid levels and missing baseline.
- [x] Implement build_annual.py, source comparison, explicit nominal-income parsing, identifiers, left joins and output generation.
- [x] Test nominal/real separation, missing metro income and matched baselines.
- [x] Build annual outputs and a notebook with selectable area/year and growth plots.
- [x] Independently validate totals and sample calculations, execute notebook cells, inspect chart, document usage and limitations.

Review focus: no missing quarters averaged; no duplicate records; no rebasing zero/negative raw indices; no dropping metros due to absent income; no mixing nominal and real income; no mixing FHFA geographic levels or index flavors.

Execution ruling: branch creation was blocked by filesystem restrictions. Work stays additive and uncommitted in the selected repository. No push or merge.

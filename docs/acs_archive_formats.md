# Historical ACS extraction

`scripts/download_acs_archive.py` retrieves selected public Census ACS 1-year Summary File sequences for B19013 (median household income) and B25077 (median owner-occupied housing value), estimates and margins of error. It uses no API key. Run from any directory; source files are anchored in data/raw/acs_archive under the repository.

```
python scripts/download_acs_archive.py --years 2005-2019 --workers 1
python scripts/download_acs_archive.py --years 2005-2019 --states --workers 2
python scripts/validate_acs_archive.py
```

The first command retrieves national, CBSA, and metropolitan-division records. The second adds 50 states and DC. The US file does not include state summaries. Files already cached are reused. Requests have a shared minimum start interval (currently 0.51 seconds), with retries for rate limits and transient server failures. Only one downloader process should run at once because the manifest lock is process-local. Run offline repair only after download completion; it reconciles validated source hashes, retains prior metadata in history, and recovers verifiable orphan directory listings without changing source bytes.

Dependencies: Python standard library, pandas for 2007/2008 SAS-format lookup metadata, and xlrd for 2005 XLS lookup metadata. An xlrd installation under `vendor/` is supported.

Successful regions are resumed from persisted normalized rows when their source geography, row count, required value fields, and national/state total match the success record in coverage. `--refresh` forces those regions to be re-extracted from cached files. Missing or failed regions are always retried. Combined normalized output and checksum metadata are regenerated at the end of every invocation.

For 2010 onward, if an individual state sequence download actually fails, the downloader can use the official `data/1_year_by_state/{State}_All_Geographies.zip` package, limited to 50 MiB. It selects only the exact requested estimate/MOE sequence files and records the whole-state package URL/hash as the data source. National archives are excluded from this fallback. A server's HTTP-200 “Request Rejected” HTML response is rejected immediately without caching or retrying that URL; genuine HTTP 429/5xx responses retain backoff. Pinned checksum mismatches never trigger this alternate-source fallback.

## Outputs

- `raw/`: exact downloaded source bytes. Invalid ZIP/HTML responses are rejected; an invalid prior cached file is retained with an `.invalid-<hash>` suffix.
- `manifest.json`: immutable source keys derived from URL, official URL, local path, SHA256, byte size and retrieval timestamp.
- `normalized_YYYY.json`: normalized rows, preserving original GEOID and raw string values, including Census missing/suppression tokens.
- `normalized.json`: combined rows from all per-year JSON files present.
- `extraction_metadata.json`: SHA256 of the exact combined normalized file, row count, available years and generation time.
- `coverage.json`: results for year/region requests, including errors. A year-level historical lookup error may remain after a successful regional retry; actual per-year records and newest region results establish coverage.
- `validation.json`: independent checks of geography identifiers, uniqueness, raw-value types, provenance references and source hashes.

Validation also reports minimum/maximum numeric estimates and MOEs and separately inventories exact nonnumeric/negative raw tokens. Raw MOEs are preserved; a zero should not be interpreted as proof of an exact population value. Dot/blank missing values, unavailable-MOE tokens, and open-ended median tokens remain raw strings; the extractor does not manufacture numeric bounds from them.

A valid cached file must match its pinned manifest SHA256. Both downloading and offline repair reject a mismatch rather than rewriting provenance. Replacement metadata is permitted only when invalid cached bytes were explicitly quarantined and a validated replacement was downloaded from the official URL; prior metadata and rejected bytes remain available in history.

`python -m unittest discover -s . -p test_scripts/download_acs_archive.py -v` checks all four geography layouts, CBSA/metropolitan-division codes, sequence column joins, raw estimate/MOE token preservation, cache checksum rejection, and invalid-response refetch history. Tests use synthetic source fixtures and isolated temporary directories; no Census network access is used.

Summary levels are restricted to 010, 040, 310 and 314, geographic component 00. The area code is USA, two-digit state FIPS, or the final five digits of the original CBSA/metropolitan-division GEOID. Names are decoded from Latin-1 source geography files. No geographic crosswalk, dollar adjustment, ratio, aggregation, or missing-value imputation is performed.

## Format differences

The script discovers yearly sequence/column lookup metadata rather than assuming identical positions. Column start positions in Census metadata are one-based and include six identification columns. The source record logical number joins estimate and MOE rows to geography.

- 2005: prototype summary files; XLS metadata, legacy ZIP/member names and fixed-width geography. GEOID/NAME begin at positions 111/151.
- 2006–2008: text/SAS metadata and fixed-width geography. GEOID/NAME begin at 176/216.
- 2009: text metadata and fixed-width geography; GEOID/NAME begin at 179/219. Sequence folders use uppercase postal abbreviations (`.../data/1_year_seq_by_state/US/`, `AL/`, etc.).
- 2010–2019: text metadata and CSV geography; GEOID/NAME are CSV fields 49/50.

Geography layouts were checked against official Census technical documents:

- https://www2.census.gov/programs-surveys/acs/summary_file/2005/documentation/ACS_2005_SF_Tech_Doc.pdf
- https://www2.census.gov/programs-surveys/acs/summary_file/2008/documentation/1_year/ACS_2008_SF_Tech_Doc.pdf
- https://www2.census.gov/programs-surveys/acs/summary_file/2009/documentation/1_year/ACS_2009_SF_Tech_Doc.pdf

ACS 1-year geography availability is population-dependent and definitions change over time. An absent area-year is not fabricated from a later geography. build_dollar_data.py handles geographic matching. 2020 is outside this extractor and has no standard ACS 1-year release.


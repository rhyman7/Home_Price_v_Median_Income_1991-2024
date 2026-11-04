"""Rebuild 1991–2024 annual HPI/income data from a pinned official snapshot.

Run: python build_annual.py
The download is separate and opt-in: python build_annual.py --download
"""
import argparse
import csv
import hashlib
import json
import math
import re
import sqlite3
import statistics
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE_URL = "https://www.fhfa.gov/hpi/download/monthly/hpi_master.csv"
RAW = ROOT / "data/raw/fhfa_master_official.csv"
YEARS = range(1991, 2025)


def read_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def selected(row):
    return (row["hpi_type"] == "traditional" and row["hpi_flavor"] == "purchase-only"
            and row["frequency"] == "quarterly" and int(row["yr"]) in YEARS
            and (row["level"] in ("State", "MSA") or
                 (row["level"] == "USA or Census Division" and row["place_id"] == "USA")))


def geography(row):
    return {"State": "state", "MSA": "metro"}.get(row["level"], "national")


def positive(value):
    n = float(str(value).replace(",", ""))
    if not math.isfinite(n) or n <= 0:
        raise ValueError(f"Expected a positive finite value, got {value!r}")
    return n


def annualize_hpi(rows):
    grouped = defaultdict(dict)
    names = {}
    for r in rows:
        if not selected(r):
            continue
        area = (geography(r), r["place_id"])
        if area in names and names[area] != r["place_name"]:
            raise ValueError(f"Inconsistent geography name: {area}")
        names[area] = r["place_name"]
        key = (*area, int(r["yr"]))
        q = int(r["period"])
        if q not in (1, 2, 3, 4) or q in grouped[key]:
            raise ValueError(f"Invalid or duplicate quarter: {key}, {q}")
        value = r["index_sa"]
        grouped[key][q] = None if value in ("", ".", None) else positive(value)
    result = []
    for (level, place_id), name in sorted(names.items()):
        def annual(year):
            values = grouped.get((level, place_id, year), {})
            if set(values) != {1, 2, 3, 4} or any(v is None for v in values.values()):
                return None
            return statistics.mean(values.values())
        base = annual(1991)
        for year in YEARS:
            value = annual(year)
            growth = None if value is None or base is None else 100 * (value / base - 1)
            status = "incomplete_year" if value is None else "missing_1991_baseline" if base is None else "available"
            result.append(dict(geography_level=level, place_id=place_id, place_name=name,
                year=year, quarters_available=sum(v is not None for v in grouped.get((level, place_id, year), {}).values()),
                hpi_annual_sa=value, hpi_1991_100=None if growth is None else 100+growth,
                hpi_growth_pct=growth, hpi_status=status))
    if not result:
        raise ValueError("No eligible quarterly HPI data")
    return result


def nominal_income(rows, places):
    """Only the first, current-dollar section of the repository's Census h08 export."""
    result = []
    seen = set()
    for r in rows:
        name = r.get("State", "").strip()
        if name == "2024 Dollars":
            break
        if name not in places:
            continue
        if name in seen:
            raise ValueError(f"Duplicate nominal income geography: {name}")
        seen.add(name)
        level, place_id = places[name]
        values = {}
        for col, value in r.items():
            match = re.fullmatch(r"(\d{4})\s+Median income", col or "")
            if match and int(match[1]) in YEARS:
                values[int(match[1])] = None if value in ("", None, "N", "NA", "-") else positive(value)
        baseline = values.get(1991)
        for year in YEARS:
            value = values.get(year)
            growth = None if value is None or baseline is None else 100*(value/baseline-1)
            result.append(dict(geography_level=level, place_id=place_id, place_name=name, year=year,
                median_household_income=value, income_1991_100=None if growth is None else 100+growth,
                income_growth_pct=growth, income_status="available" if growth is not None else "missing_income_or_baseline"))
    return result


def combine(housing, income):
    key = lambda r: (r["geography_level"], r["place_id"], r["year"])
    lookup = {key(r): r for r in income}
    if len(lookup) != len(income):
        raise ValueError("Duplicate income geography-year")
    result = []
    for h in housing:
        r = dict(h)
        i = lookup.get(key(h), {})
        for col in ("median_household_income", "income_1991_100", "income_growth_pct"):
            r[col] = i.get(col)
        r["income_status"] = i.get("income_status", "not_sourced_for_area")
        hg, ig = r["hpi_growth_pct"], r["income_growth_pct"]
        r["growth_gap_pp"] = None if hg is None or ig is None else hg-ig
        result.append(r)
    return result


def download():
    if RAW.exists():
        raise FileExistsError("Pinned snapshot already exists; preserve it and use a new named snapshot for updates.")
    with urllib.request.urlopen(SOURCE_URL, timeout=60) as response:
        data = response.read()
    if not data.startswith(b"hpi_type,hpi_flavor,"):
        raise ValueError("Unexpected FHFA download format")
    RAW.parent.mkdir(parents=True, exist_ok=True)
    RAW.write_bytes(data)
    RAW.with_suffix(".metadata.json").write_text(json.dumps({"source_url": SOURCE_URL,
        "retrieved_utc": datetime.now(timezone.utc).isoformat(), "sha256": hashlib.sha256(data).hexdigest()}, indent=2))


def source_comparison(official, local):
    fields = ("hpi_type", "hpi_flavor", "frequency", "level", "place_id", "yr", "period")
    key = lambda r: tuple(r[f] for f in fields)
    old = {key(r): r for r in local if selected(r)}
    matched = [(r, old[key(r)]) for r in official if selected(r) and key(r) in old]
    return {"matched_quarters": len(matched),
        "median_official_minus_local_nsa": statistics.median(float(a["index_nsa"])-float(b["index_nsa"]) for a,b in matched),
        "median_official_minus_local_sa": statistics.median(float(a["index_sa"])-float(b["index_sa"]) for a,b in matched),
        "interpretation": "Local NSA was reduced by exactly 100 in Git commit 1a21d3b (all 131540 rows checked against initial commit 5a5dfa5). Official snapshot also contains later source revisions; use official indices directly, not repaired local values."}


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def build():
    data = RAW.read_bytes()
    metadata = json.loads(RAW.with_suffix(".metadata.json").read_text())
    if hashlib.sha256(data).hexdigest() != metadata["sha256"]:
        raise ValueError("FHFA snapshot checksum mismatch")
    official = read_csv(RAW)
    housing = annualize_hpi(official)
    places = {r["place_name"]: (r["geography_level"], r["place_id"]) for r in housing if r["geography_level"] != "metro"}
    income = nominal_income(read_csv(ROOT / "data/h08.csv"), places)
    expected = {(level, pid, year) for level,pid in places.values() for year in YEARS}
    actual = {(r["geography_level"],r["place_id"],r["year"]) for r in income if r["income_status"] == "available"}
    if expected != actual:
        raise ValueError("Incomplete national/state income coverage")
    joined = combine(housing, income)
    out = ROOT / "data/annual"
    out.mkdir(parents=True, exist_ok=True)
    for name, rows in (("hpi_annual",housing),("income_annual",income),("comparison_annual",joined)):
        write_csv(out / (name+".csv"), rows)
    # Only this pipeline's dedicated database is rebuilt. Legacy databases are untouched.
    with sqlite3.connect(out / "housing_income_annual.db") as conn:
        with conn:
            for name, rows in (("hpi_annual",housing),("income_annual",income),("comparison_annual",joined)):
                conn.execute(f'DROP TABLE IF EXISTS "{name}"')
                columns = list(rows[0])
                textcols = {"geography_level", "place_id", "place_name", "hpi_status", "income_status"}
                defs = [f'"{c}" '+("TEXT" if c in textcols else "INTEGER" if c in ("year","quarters_available") else "REAL") for c in columns]
                conn.execute(f'CREATE TABLE "{name}" ('+", ".join(defs)+', PRIMARY KEY (geography_level,place_id,year))')
                conn.executemany(f'INSERT INTO "{name}" VALUES ('+",".join("?" for _ in columns)+')', [[r[c] for c in columns] for r in rows])
    comparison = source_comparison(official, read_csv(ROOT / "data/hpi_master.csv"))
    report = dict(source=metadata, income_source="Census h08.csv nominal section, existing repository snapshot",
        income_sha256=hashlib.sha256((ROOT/"data/h08.csv").read_bytes()).hexdigest(),
        methodology="Traditional purchase-only quarterly SA HPI; arithmetic mean of four quarters; annual 1991 mean = 100; nominal household income; no imputation.",
        years=[1991,2024], hpi_rows=len(housing), income_rows=len(income), comparison_rows=len(joined),
        areas_by_level={level:len({r['place_id'] for r in housing if r['geography_level']==level}) for level in ['national','state','metro']},
        incomplete_hpi_years=sum(r['hpi_status']!='available' for r in housing),
        comparison_rows_without_income=sum(r['median_household_income'] is None for r in joined),
        source_comparison=comparison)
    (out / "build_report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true", help="Download first pinned official snapshot; refuses to overwrite it")
    args = parser.parse_args()
    if args.download:
        download()
    build()

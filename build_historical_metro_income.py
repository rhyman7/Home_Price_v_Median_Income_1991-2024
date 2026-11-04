"""Offline historical metro-income extraction and exact county-boundary audit.

Keeps early ACS constant-dollar estimates separate from nominal comparisons.
No interpolation, median aggregation, or name-only geographic joins.
"""
import csv
import hashlib
import io
import json
import re
import zipfile
from collections import Counter
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent
RAW = ROOT / 'data/raw/early_metro_income'
OUT = ROOT / 'data/historical_metro_income'


def name_key(name):
    return re.sub(r'[^a-z0-9]', '', name.lower())


def numeric(value):
    text = str(value).strip().replace(',', '')
    text = re.sub(r'\s+\*$', '', text)
    return int(float(text)) if re.fullmatch(r'\d+(?:\.0+)?', text) and float(text) > 0 else None


def same_boundary(old, current):
    return bool(current) and not old['partial'] and old['counties'] == current


def old_boundaries(text):
    areas = {}
    active = parent = None
    for line in text.splitlines():
        head = re.match(r'^(\d{4})(?:\s+(\d{4}))?\s+(?:\d{2}\s+)?(.+(?:PMSA|CMSA|MSA))\s*$', line)
        if head:
            msa, pmsa, name = head.groups()
            name = name.strip()
            active = ('385:' + pmsa) if pmsa else ('380:' + msa)
            parent = '380:' + msa if pmsa else None
            areas[active] = dict(name=name, counties=set(), partial=False)
        elif active and re.match(r'^\d{4}\s', line):
            fips = re.findall(r'\b\d{5}\b', line)
            if fips:
                for key in (active, parent):
                    if key:
                        areas[key]['counties'].add(fips[0])
                        if '(pt.)' in line or len(fips) > 1:
                            areas[key]['partial'] = True
    return areas


def boundaries():
    old = old_boundaries((RAW / '99mfips.txt').read_text())
    current = {}
    df = pd.read_excel(RAW / 'list1_2023.xlsx', header=2, dtype=str).fillna('')
    for _, row in df.iterrows():
        state, county = row['FIPS State Code'], row['FIPS County Code']
        if not re.fullmatch(r'\d{2}', state) or not re.fullmatch(r'\d{3}', county):
            continue
        for field in ('CBSA Code', 'Metropolitan Division Code'):
            code = row[field]
            if re.fullmatch(r'\d{5}', code):
                current.setdefault(code, set()).add(state + county)
    return old, current


def multi_records(rows, name_to_code):
    out = []
    for row in rows:
        if row['stub'].strip() != 'Median household income (dollars)':
            continue
        code = name_to_code.get(name_key(row['GEONAME']))
        if not code:
            continue
        for year in range(2000, 2004):
            raw = row[f'pctd_{str(year)[2:]}']
            out.append(dict(old_area_key=code, source_area_name=row['GEONAME'], year=year,
                median_household_income=numeric(raw), dollar_year=2003,
                series='ACS testing program', lower_bound=None, upper_bound=None,
                source_file='profiles_2000_2003.csv', source_table='Profile 3, line 63',
                estimate_raw=raw))
    return out


def decennial_records():
    # Original Census Word documentation retains these ASCII table definitions.
    doc = (RAW / '0SF3_table_matrix.doc').read_bytes().decode('cp1252', errors='ignore')
    cols = re.findall(r'\b([PH]\d{6})\s+06\s+\d+', doc)
    assert len(cols) == 250 and len(set(cols)) == 250
    position = 5 + cols.index('P053001')
    geos = {}
    with zipfile.ZipFile(RAW / 'usgeo_uf3.zip') as z:
        with z.open('usgeo.uf3') as stream:
            for b in stream:
                line = b.decode('cp1252')
                level = line[8:11]
                if level not in ('380', '385') or line[11:16] != '00000':
                    continue
                code = line[106:110] if level == '380' else line[115:119]
                geos[line[18:25]] = (level + ':' + code, line[200:290].strip())
    result = []
    with zipfile.ZipFile(RAW / 'us00006_uf3.zip') as z:
        with z.open('us00006.uf3') as stream:
            for row in csv.reader(io.TextIOWrapper(stream, encoding='ascii')):
                if row[4] not in geos:
                    continue
                assert len(row) == 255
                code, name = geos[row[4]]
                result.append(dict(old_area_key=code, source_area_name=name, year=1999,
                    median_household_income=numeric(row[position]), dollar_year=1999,
                    series='Census 2000 SF3 (1999 income)', lower_bound=None, upper_bound=None,
                    source_file='us00006_uf3.zip', source_table='P053001; LOGRECNO=' + row[4],
                    estimate_raw=row[position]))
    assert len(result) == len(geos)
    return result


def single_record(path, year, code):
    df = pd.read_excel(path, header=None).fillna('')
    text = df.astype(str)
    assert text.apply(lambda c: c.str.contains(f'IN {year} INFLATION-ADJUSTED DOLLARS', regex=False)).any().any(), path
    matches = []
    for row in df.itertuples(index=False, name=None):
        for i, cell in enumerate(row):
            if str(cell).strip() == 'Median household income (dollars)':
                values = list(row[i + 1:])
                # Some archived workbooks have a blank spacer before the estimate.
                while values and values[0] == '':
                    values.pop(0)
                matches.append(values)
    assert len(matches) == 1, path
    value = matches[0]
    return dict(old_area_key=code, source_area_name=str(df.iloc[1, 0]).strip(), year=year,
        median_household_income=numeric(value[0]), dollar_year=year, series='ACS testing program',
        lower_bound=numeric(value[1]), upper_bound=numeric(value[2]),
        source_file=path.name, source_table='Profile 3: Median household income (dollars)',
        estimate_raw=value[0])


def tucson_record(year):
    assert year in (2000, 2001)
    filename = f'tucson_{year}_2002.xls'
    df = pd.read_excel(RAW / filename, header=None).fillna('')
    assert df.iloc[3, 1] == f'{year} Estimate'
    label = 'Median household income (in 2002 inflation-adjusted dollars)'
    rows = [r for r in df.itertuples(index=False, name=None) if str(r[0]).strip() == label]
    assert len(rows) == 1
    return dict(old_area_key='380:8520', source_area_name='Tucson, AZ MSA', year=year,
        median_household_income=numeric(rows[0][1]), dollar_year=2002,
        series='ACS testing program', lower_bound=None, upper_bound=None,
        source_file=filename, source_table='Profile 3: ' + label, estimate_raw=rows[0][1])


def read_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def write_csv(name, rows):
    with (OUT / name).open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def build():
    OUT.mkdir(exist_ok=True)
    manifest = json.loads((RAW / 'manifest.json').read_text())
    for filename, entry in manifest.items():
        assert hashlib.sha256((RAW / filename).read_bytes()).hexdigest() == entry['sha256'], filename
    old, current = boundaries()
    targets = [r for r in read_csv(ROOT / 'data/dollars/coverage_by_area.csv') if r['geography_level'] == 'metro']
    assert len(targets) == 100 and all(r['place_id'] in current for r in targets)
    crosswalk, exact = [], {}
    for target in targets:
        code = target['place_id']
        matches = [key for key, area in old.items() if same_boundary(area, current[code])]
        assert len(matches) <= 1, (code, matches)
        # Overlap is audit information only; never used to assign an estimate.
        best = max(old, key=lambda key: len(old[key]['counties'] & current[code]) / len(old[key]['counties'] | current[code]))
        selected = matches[0] if matches else best
        source = old[selected]
        if matches:
            exact[code] = selected
        crosswalk.append(dict(place_id=code, place_name=target['place_name'],
            match_status='exact_county_set' if matches else 'no_verified_same_boundary',
            old_area_key=selected, old_area_name=source['name'],
            old_has_partial_counties=source['partial'],
            old_county_fips=';'.join(sorted(source['counties'])),
            current_county_fips=';'.join(sorted(current[code])),
            counties_only_in_old=';'.join(sorted(source['counties'] - current[code])),
            counties_only_in_current=';'.join(sorted(current[code] - source['counties'])),
            note='1999 vs July 2023 delineations; unmatched candidate is context only'))
    records = decennial_records()
    names = {name_key(v['name']): k for k, v in old.items()}
    records += multi_records(read_csv(RAW / 'profiles_2000_2003.csv'), names)
    records += [tucson_record(2000), tucson_record(2001)]
    singles = json.loads((RAW / 'single_year_files.json').read_text())
    for item in singles:
        r = single_record(RAW / item['file'], item['year'], item['old_area_key'])
        assert name_key(r['source_area_name']) == name_key(old[item['old_area_key']]['name']), item
        r['source_area_name'] = old[item['old_area_key']]['name']
        records.append(r)
    for r in records:
        r['source_url'] = manifest[r['source_file']]['url']
        if r['median_household_income'] is not None and r['lower_bound'] is not None and r['upper_bound'] is not None:
            assert r['lower_bound'] <= r['median_household_income'] <= r['upper_bound']
    write_csv('source_observations.csv', records)
    write_csv('boundary_audit.csv', crosswalk)
    # Prefer annual-current-dollar releases over constant-dollar comparison profiles.
    lookup = {}
    for r in sorted(records, key=lambda r: r['dollar_year'] == r['year']):
        if r['median_household_income'] is not None:
            lookup[(r['old_area_key'], r['year'])] = r
    panel, verified = [], []
    recent = {(r['place_id'], int(r['year'])): r for r in read_csv(ROOT / 'data/dollars/acs_dollar_comparison.csv') if r['geography_level'] == 'metro'}
    for target in targets:
        pid = target['place_id']
        for year in range(1991, 2025):
            r = lookup.get((exact.get(pid), year))
            out = dict(place_id=pid, place_name=target['place_name'], year=year,
                median_household_income=None, dollar_year=None, source_area_name='',
                series='', boundary_status='', status='not_sourced', source_file='', source_url='')
            if year <= 2004:
                out['status'] = 'not_sourced_1991_1998' if year < 1999 else 'no_verified_same_boundary' if pid not in exact else 'not_published_in_loaded_early_acs'
                if r:
                    out.update({k: r[k] for k in ('median_household_income', 'dollar_year', 'source_area_name', 'series', 'source_file', 'source_url')})
                    out.update(boundary_status='exact_1999_2023_county_set', status='available_current_dollars' if r['dollar_year'] == year else 'available_constant_dollars')
                    verified.append(dict(out))
            else:
                acs = recent[(pid, year)]
                value = numeric(acs['median_household_income_acs'])
                if value:
                    out.update(median_household_income=value, dollar_year=year,
                        source_area_name=acs['census_area_name'], series='ACS 1-year B19013',
                        boundary_status=acs['boundary_status'], status='available_current_dollars',
                        source_file=acs['income_source_file'], source_url=f'https://www.census.gov/programs-surveys/acs/data/summary-file.{year}.html')
                else:
                    out['status'] = 'no_standard_acs_1year_2020' if year == 2020 else 'no_exact_geography_match_in_loaded_sources'
            panel.append(out)
    assert len(panel) == 3400 and len({(r['place_id'], r['year']) for r in panel}) == 3400
    write_csv('verified_early_observations.csv', verified)
    write_csv('metro_income_1991_2024.csv', panel)
    coverage = []
    for t in targets:
        rows = [r for r in panel if r['place_id'] == t['place_id']]
        coverage.append(dict(place_id=t['place_id'], place_name=t['place_name'],
            early_years=';'.join(str(r['year']) for r in rows if r['year'] < 2005 and r['median_household_income']),
            current_dollar_years=';'.join(str(r['year']) for r in rows if r['status'] == 'available_current_dollars'),
            constant_dollar_years_and_basis=';'.join(f"{r['year']}:{r['dollar_year']}_dollars" for r in rows if r['status'] == 'available_constant_dollars'),
            missing_years=';'.join(str(r['year']) for r in rows if r['median_household_income'] is None)))
    write_csv('coverage_by_area.csv', coverage)
    report = dict(project_areas=100, exact_boundary_matches=len(exact), early_observations=len(verified),
        early_year_counts=dict(sorted(Counter(r['year'] for r in verified).items())),
        early_dollar_status_counts=dict(Counter(r['status'] for r in verified)),
        all_status_counts=dict(Counter(r['status'] for r in panel)),
        source_observations=len(records),
        note='Supplemental data only; not spliced into the CPS 1991 growth series or the ACS home-value ratio panel.')
    (OUT / 'validation.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return report


if __name__ == '__main__':
    build()

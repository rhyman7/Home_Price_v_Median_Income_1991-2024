"""Build same-release ACS dollar home-value and household-income comparisons.
Run after downloading sources with scripts/download_acs_recent.py and
scripts/download_acs_archive.py. Rebuild is offline and verifies checksums.
"""
import csv
import hashlib
import json
import math
import re
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def estimate(value, moe):
    raw = str(value or '').strip()
    if str(moe).strip() in ('-333333333', '***') or re.fullmatch(r'[0-9][0-9,.]*[+-]', raw):
        return None, None, 'censored_median'
    try:
        number = float(raw.replace(',', ''))
        if not math.isfinite(number) or number <= 0:
            return None, None, 'unavailable_or_suppressed'
    except ValueError:
        return None, None, 'unavailable_or_suppressed'
    try:
        error = float(str(moe).replace(',', ''))
        if not math.isfinite(error) or error < 0:
            error = None
    except (ValueError, TypeError):
        error = None
    return number, error, 'available'


def read_delimited(path, delimiter=','):
    with Path(path).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f, delimiter=delimiter))


def verify_sources(folder, manifest):
    entries = manifest.values() if isinstance(manifest, dict) else manifest
    for entry in entries:
        path = folder / entry.get('file', entry.get('path'))
        if hashlib.sha256(path.read_bytes()).hexdigest() != entry['sha256']:
            raise ValueError(f'Source checksum mismatch: {path}')


def verify_archive_sources(folder, records, manifest):
    used = {value for row in records for key, value in row.items() if key.endswith('_source')}
    missing = used - set(manifest)
    if missing:
        raise ValueError(f'Missing archive source references: {sorted(missing)}')
    verify_sources(folder, {key: manifest[key] for key in used})


def table_by_geoid(rows):
    result = {}
    for row in rows:
        key = row['GEO_ID']
        if key in result:
            raise ValueError(f'Duplicate source table GEO_ID: {key}')
        result[key] = row
    return result


def recent_records(folder):
    result = []
    states = {}
    for year in range(2021, 2025):
        geos = read_delimited(folder / f'{year}_geos.txt', '|')
        tables = {t: table_by_geoid(read_delimited(folder / f'{year}_{t.lower()}.dat', '|'))
                  for t in ('B19013','B25077')}
        for g in geos:
            level = g['SUMLEVEL']
            if level not in ('010','040','310','314') or g['COMPONENT'] != '00':
                continue
            gid = g['GEO_ID']
            code = 'USA' if level=='010' else g[{'040':'STATE','310':'CBSA','314':'METDIV'}[level]]
            if level == '040' and year == 2024:
                states[g['STUSAB']] = code
            r = dict(year=year, summary_level=level, area_code=code, area_name=g['NAME'], geo_id=gid,
                     geography_source=f'{year}_geos.txt')
            for table, stem in (('B19013','income'),('B25077','home_value')):
                t = tables[table].get(gid, {})
                r[stem+'_estimate_raw'] = t.get(table+'_E001', '')
                r[stem+'_moe_raw'] = t.get(table+'_M001', '')
                r[stem+'_source'] = f'{year}_{table.lower()}.dat'
            result.append(r)
    return result, states


def build_panel(housing, acs, state_codes):
    lookup = {}
    for r in acs:
        key = (int(r['year']), r['summary_level'], r['area_code'])
        if key in lookup:
            raise ValueError(f'Duplicate ACS geography/year: {key}')
        lookup[key] = r
    result = []
    seen = set()
    for h in housing:
        year, level, pid = int(h['year']), h['geography_level'], h['place_id']
        key = (level, pid, year)
        if key in seen:
            raise ValueError(f'Duplicate target geography/year: {key}')
        seen.add(key)
        sl = '010' if level == 'national' else '040' if level == 'state' else '314' if '(MSAD)' in h['place_name'] else '310'
        code = state_codes.get(pid) if level == 'state' else pid
        r = None if year < 2005 or year == 2020 else lookup.get((year,sl,code))
        boundary = 'not_applicable' if level != 'metro' else '2023_delineation' if year >= 2023 else 'historical_not_harmonized'
        out = dict(geography_level=level, place_id=pid, fhfa_place_name=h['place_name'], year=year,
            census_summary_level=sl, census_area_code=code, census_geo_id=r['geo_id'] if r else '',
            census_area_name=r['area_name'] if r else '', boundary_status=boundary,
            housing_measure='Median owner-occupied home value (ACS B25077)',
            income_source='ACS 1-year B19013', dollar_basis='survey_year_dollars',
            median_home_value_acs=None, home_value_moe=None, median_household_income_acs=None,
            income_moe=None, home_value_to_income_ratio=None,
            home_value_status='not_available', income_status='not_available',
            income_source_file=r.get('income_source','') if r else '',
            home_value_source_file=r.get('home_value_source','') if r else '',
            geography_source_file=r.get('geography_source','') if r else '')
        if year < 2005:
            out['pair_status'] = 'before_acs_1year'
        elif year == 2020:
            out['pair_status'] = 'no_standard_acs_1year_2020'
        elif r is None:
            out['pair_status'] = 'no_exact_geography_match_in_loaded_sources'
        else:
            value, vm, vs = estimate(r.get('home_value_estimate_raw'),r.get('home_value_moe_raw'))
            income, im, ins = estimate(r.get('income_estimate_raw'),r.get('income_moe_raw'))
            out.update(median_home_value_acs=value, home_value_moe=vm, home_value_status=vs,
                median_household_income_acs=income, income_moe=im, income_status=ins,
                pair_status='available' if value is not None and income is not None else 'estimate_unavailable_or_censored')
            if value is not None and income is not None:
                out['home_value_to_income_ratio'] = value/income
        result.append(out)
    return result


def write_csv(path, rows):
    with path.open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)


def build():
    raw = ROOT / 'data/raw/acs'
    manifest = json.loads((raw/'manifest.json').read_text())
    verify_sources(raw, manifest)
    acs, states = recent_records(raw)
    archive = ROOT / 'data/raw/acs_archive'
    if not (archive/'normalized.json').exists():
        raise FileNotFoundError('Missing archived ACS extraction. Run scripts/download_acs_archive.py first.')
    archive_manifest = json.loads((archive/'manifest.json').read_text())
    # The extraction itself is also pinned after the source-row validation step.
    expected = json.loads((archive/'extraction_metadata.json').read_text())['sha256']
    if hashlib.sha256((archive/'normalized.json').read_bytes()).hexdigest() != expected:
        raise ValueError('Archived extraction checksum mismatch')
    archived = json.loads((archive/'normalized.json').read_text(encoding='utf-8'))
    verify_archive_sources(archive, archived, archive_manifest)
    acs += archived
    housing=read_delimited(ROOT/'data/annual/hpi_annual.csv')
    panel=build_panel(housing,acs,states)
    output=ROOT/'data/dollars';output.mkdir(exist_ok=True)
    write_csv(output/'acs_dollar_comparison.csv',panel)
    # Preserve all sourced national, state, CBSA and division records, not only current FHFA matches.
    fields=sorted(set().union(*(r.keys() for r in acs)))
    normalized=[{c:r.get(c,'') for c in fields} for r in acs]
    write_csv(output/'acs_source_records.csv',normalized)
    by_area=defaultdict(list)
    for r in panel:by_area[(r['geography_level'],r['place_id'],r['fhfa_place_name'])].append(r)
    coverage=[]
    for (level,pid,name),rr in sorted(by_area.items()):
        available=[r['year'] for r in rr if r['pair_status']=='available']
        coverage.append(dict(geography_level=level,place_id=pid,place_name=name,available_years=len(available),
            first_available_year=min(available) if available else '',last_available_year=max(available) if available else '',
            available_year_list=';'.join(map(str,available)),missing_year_list=';'.join(str(r['year']) for r in rr if r['pair_status']!='available')))
    write_csv(output/'coverage_by_area.csv',coverage)
    textcols=set(panel[0])-{'year','median_home_value_acs','home_value_moe','median_household_income_acs','income_moe','home_value_to_income_ratio'}
    with sqlite3.connect(output/'housing_income_dollars.db') as conn:
        conn.execute('DROP TABLE IF EXISTS acs_dollar_comparison')
        cols=list(panel[0]);defs=[f'"{c}" '+('TEXT' if c in textcols else 'INTEGER' if c=='year' else 'REAL') for c in cols]
        conn.execute('CREATE TABLE acs_dollar_comparison ('+', '.join(defs)+', PRIMARY KEY(geography_level,place_id,year))')
        conn.executemany('INSERT INTO acs_dollar_comparison VALUES ('+','.join('?' for _ in cols)+')',[[r[c] for c in cols] for r in panel])
    report=dict(target_hpi_sha256=hashlib.sha256((ROOT/'data/annual/hpi_annual.csv').read_bytes()).hexdigest(),target_years=[1991,2024],acs_years_loaded=sorted({int(r['year']) for r in acs}),
        panel_rows=len(panel),source_rows=len(acs),status_counts=dict(Counter(r['pair_status'] for r in panel)),
        paired_counts_by_year={str(y):dict(Counter(r['geography_level'] for r in panel if r['year']==y and r['pair_status']=='available')) for y in range(1991,2025)},
        geography_rule='Exact summary level and code; historical boundaries not harmonized. Ratios pair ACS values and income from the same release/geography, not CPS income.',
        source='Census ACS 1-year B25077 and B19013; dollar home values are owner-reported estimates, not sale prices.',
        notes=['1991–2004 are not backfilled.','2020 standard ACS 1-year estimates unavailable.','No income growth since 1991 is calculated from ACS.','Margins of error are retained; no ratio uncertainty estimate is supplied.'])
    (output/'coverage_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':build()

"""Acquire official Census historical metro sources; resumable, with checksums."""
import concurrent.futures
import hashlib
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import build_historical_metro_income as h


def download(filename, url):
    path = h.RAW / filename
    if not path.exists():
        for attempt in range(5):
            try:
                data = urllib.request.urlopen(url, timeout=60).read()
                break
            except urllib.error.HTTPError as error:
                if error.code not in (429, 500, 502, 503, 504) or attempt == 4:
                    raise
                time.sleep(min(10 * (attempt + 1), 40))
        path.write_bytes(data)
        time.sleep(0.5)
    return filename, dict(url=url, sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def main():
    h.RAW.mkdir(exist_ok=True)
    manifest_path = h.RAW / 'manifest.json'
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    sf3 = 'https://www2.census.gov/census_2000/datasets/Summary_File_3/'
    sources = {
        'profiles_2000_2003.csv': 'https://www2.census.gov/acs2003/Profiles/2000-2003_Profiles/total_multiyearprofile.csv',
        '99mfips.txt': 'https://www2.census.gov/programs-surveys/metro-micro/geographies/reference-files/1999/historical-delineation-files/99mfips.txt',
        'list1_2023.xlsx': 'https://www2.census.gov/programs-surveys/metro-micro/geographies/reference-files/2023/delineation-files/list1_2023.xlsx',
        'us00006_uf3.zip': sf3 + '0_National/us00006_uf3.zip',
        'usgeo_uf3.zip': sf3 + '0_National/usgeo_uf3.zip',
        '0SF3_table_matrix.doc': sf3 + '0SF3_table_matrix.doc',
        '0SF3_geo_header.doc': sf3 + '0SF3_geo_header.doc',
        'ACS2003_README.txt': 'https://www2.census.gov/acs2003/ACS2003_README.txt',
        'ACS2004_README.txt': 'https://www2.census.gov/acs2004/ACS2004_README.txt',
        '2003_geography_notes.pdf': 'https://www2.census.gov/acs2003/2003_geography_notes.pdf',
        '2004_geography_notes.doc': 'https://www2.census.gov/acs2004/2004_geography_notes.doc',
        'tucson_2000_2002.xls': 'https://www2.census.gov/acs2002/Profiles/2000-2002/380CMSAMSA/38000US8520.xls',
        'tucson_2001_2002.xls': 'https://www2.census.gov/acs2002/Profiles/2001-2002/380CMSAMSA/38000US8520.xls',
    }
    for filename, url in sources.items():
        key, entry = download(filename, url)
        manifest[key] = entry
    manifest_path.write_text(json.dumps(manifest, indent=2))
    old, current = h.boundaries()
    targets = [r for r in h.read_csv(h.ROOT / 'data/dollars/coverage_by_area.csv') if r['geography_level'] == 'metro']
    wanted = {key for t in targets for key, area in old.items() if h.same_boundary(area, current[t['place_id']])}
    names = {h.name_key(old[key]['name']): key for key in wanted}
    jobs, singles = [], []
    for year in (2002, 2003, 2004):
        folder = {2002: '2002%20Profiles', 2003: '2003_Profiles', 2004: '2004_Single_Year_Profile'}[year]
        for level in ('380', '385'):
            geo = ('380MSACMSA' if year == 2003 else '380CMSAMSA') if level == '380' else '385PMSA'
            url = f'https://www2.census.gov/acs{year}/Profiles/{folder}/{geo}/'
            index_name = f'index_{year}_{level}.html'
            key, entry = download(index_name, url)
            manifest[key] = entry
            html = (h.RAW / index_name).read_text(encoding='utf-8')
            for href in re.findall(r'href="([^\"]+\.xls)"', html):
                decoded = urllib.parse.unquote(href)
                if year == 2002:
                    match = re.fullmatch(r'(380|385)00US(?:\d{4})?(\d{4})\.xls', decoded)
                    code = ':'.join(match.groups()) if match else None
                else:
                    code = names.get(h.name_key(decoded[:-4]))
                if code not in wanted:
                    continue
                filename = f'{year}_{code.replace(":", "_")}.xls'
                jobs.append((filename, urllib.parse.urljoin(url, href)))
                singles.append(dict(file=filename, year=year, old_area_key=code))
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        for filename, entry in pool.map(lambda args: download(*args), jobs):
            manifest[filename] = entry
    manifest_path.write_text(json.dumps(manifest, indent=2))
    (h.RAW / 'single_year_files.json').write_text(json.dumps(singles, indent=2))
    print(f'Saved {len(singles)} annual profiles for {len(wanted)} exact boundary matches.')


if __name__ == '__main__':
    main()

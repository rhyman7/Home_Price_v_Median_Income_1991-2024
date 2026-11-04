"""Audit extracted geography IDs, value types, provenance and source hashes offline."""
import csv, hashlib, io, json, re, zipfile
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1] / "data/raw/acs_archive"

def main():
    manifest=json.loads((ROOT/'manifest.json').read_text())
    checks=[];errors=[];annotations=Counter();bounds={}
    for path in sorted(ROOT.glob('normalized_????.json')):
        records=json.loads(path.read_text(encoding='utf-8')); counts=Counter(r['summary_level'] for r in records)
        seen=set()
        for r in records:
            identity=(r['year'],r['summary_level'],r['geo_id'])
            if identity in seen:errors.append(f'Duplicate {identity}')
            seen.add(identity)
            if not r['geo_id'].startswith(r['summary_level']+'00US'):errors.append(f'Unexpected GEOID {identity}')
            expected='USA' if r['summary_level']=='010' else r['geo_id'].split('US')[-1][-2 if r['summary_level']=='040' else -5:]
            if r['area_code']!=expected:errors.append(f'Area code mismatch {identity}')
            for field in ('income_estimate_raw','income_moe_raw','home_value_estimate_raw','home_value_moe_raw'):
                value=r.get(field)
                if not isinstance(value,str):
                    errors.append(f'Non-string {identity} {field}');continue
                if re.fullmatch(r'\d+(?:\.\d+)?',value):
                    number=float(value)
                    if field not in bounds:bounds[field]={'min':number,'max':number}
                    bounds[field]['min']=min(bounds[field]['min'],number);bounds[field]['max']=max(bounds[field]['max'],number)
                    if field.endswith('_moe_raw') and number==0:annotations[(field,'0: controlled estimate; not an ordinary zero uncertainty')]+=1
                else:
                    # Never turn suppression, missing, unavailable-MOE, or open-ended
                    # median tokens into numbers. Keep the exact raw token in audit.
                    annotations[(field,value)]+=1
            for field in ('income_source','home_value_source','income_lookup_source','home_value_lookup_source','geography_source'):
                if r[field] not in manifest:errors.append(f'Missing provenance {identity} {field}: {r[field]}')
        checks.append({'year':int(path.stem[-4:]),'rows':len(records),'summary_levels':dict(counts),'national':[{k:v for k,v in r.items() if k.endswith('_raw')} for r in records if r['summary_level']=='010']})
    used={r[k] for p in ROOT.glob('normalized_????.json') for r in json.loads(p.read_text(encoding='utf-8')) for k in r if k.endswith('_source')}
    for key in used:
        if key not in manifest:continue
        m=manifest[key];p=ROOT/m['path']
        if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest()!=m['sha256']:errors.append(f'Source integrity mismatch {key}')
    report={'years':checks,'referenced_sources':len(used),'numeric_bounds':bounds,'raw_annotations':[{'field':field,'raw':raw,'count':count} for (field,raw),count in sorted(annotations.items())],'errors':errors}
    (ROOT/'validation.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
    if errors:raise SystemExit(1)

if __name__=='__main__':main()

"""Fetch Census ACS 1-year summary sequences, preserving source bytes and hashes.
Usage: python download_older.py --years 2010-2019 [--states]
Only handles formats actually recognized; records failures in coverage.json.
"""
import argparse, csv, datetime, hashlib, io, json, re, threading, time, urllib.request, urllib.parse, urllib.error, zipfile
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = Path(__file__).resolve().parents[1] / "data/raw/acs_archive"
BASE = 'https://www2.census.gov/programs-surveys/acs/summary_file/'
LOCK = threading.Lock()
NETWORK_LOCK = threading.Lock()
LAST_REQUEST = 0
class RejectedSource(ValueError):
    """HTTP 200 rejection page, not source data; retrying same URL is unhelpful."""
STATES = dict(x.split(':') for x in ('al:Alabama ak:Alaska az:Arizona ar:Arkansas ca:California co:Colorado ct:Connecticut de:Delaware dc:DistrictofColumbia fl:Florida ga:Georgia hi:Hawaii id:Idaho il:Illinois in:Indiana ia:Iowa ks:Kansas ky:Kentucky la:Louisiana me:Maine md:Maryland ma:Massachusetts mi:Michigan mn:Minnesota ms:Mississippi mo:Missouri mt:Montana ne:Nebraska nv:Nevada nh:NewHampshire nj:NewJersey nm:NewMexico ny:NewYork nc:NorthCarolina nd:NorthDakota oh:Ohio ok:Oklahoma or:Oregon pa:Pennsylvania ri:RhodeIsland sc:SouthCarolina sd:SouthDakota tn:Tennessee tx:Texas ut:Utah vt:Vermont va:Virginia wa:Washington wv:WestVirginia wi:Wisconsin wy:Wyoming').split())

def valid_source(url,blob):
    if not blob:return False
    if url.lower().endswith('.zip'):
        try:
            with zipfile.ZipFile(io.BytesIO(blob)) as z:return z.testzip() is None
        except (zipfile.BadZipFile,EOFError,RuntimeError):return False
    return url.endswith('/') or b'<html' not in blob[:1000].lower()

def record_source(manifest,item,allow_replacement=False):
    old=manifest.get(item['key'])
    if old and old['sha256']==item['sha256']:
        return
    if old:
        if not allow_replacement:
            raise ValueError(f'Pinned source checksum mismatch: {item["key"]}; refusing to replace source metadata')
        history=list(old.get('history',[]))
        prior={k:v for k,v in old.items() if k!='history'}
        for candidate in (ROOT/'raw').glob(Path(old['path']).name+'.invalid-*'):
            if hashlib.sha256(candidate.read_bytes()).hexdigest()==old['sha256']:
                prior['path']=str(candidate.relative_to(ROOT));prior['status']='invalid_previous_response';break
        history.append(prior);item['history']=history
    manifest[item['key']]=item

def fetch(url,max_bytes=None):
    global LAST_REQUEST
    key = hashlib.sha256(url.encode()).hexdigest()[:16]
    path = ROOT/'raw'/(key+'_'+(urllib.parse.urlparse(url).path.rsplit('/',1)[-1] or 'index.html'))
    path.parent.mkdir(parents=True,exist_ok=True)
    data=path.read_bytes() if path.exists() else None
    if data is not None and max_bytes is not None and len(data)>max_bytes:
        raise ValueError(f'Source exceeds maximum allowed size: {url}')
    # A valid-looking cached file is still pinned by its recorded checksum.
    # Only rejected bytes subsequently fetched from the official URL may replace it.
    replaced_invalid=False
    if data is not None and valid_source(url,data):
        with LOCK:
            mp=ROOT/'manifest.json';pinned=json.loads(mp.read_text()).get(key) if mp.exists() else None
        if pinned and hashlib.sha256(data).hexdigest()!=pinned['sha256']:
            raise ValueError(f'Pinned source checksum mismatch: {url}')
    downloaded=False
    if data is not None and not valid_source(url,data):
        replaced_invalid=True
        invalid=path.with_name(path.name+'.invalid-'+hashlib.sha256(data).hexdigest()[:8])
        if invalid.exists():
            if invalid.read_bytes()!=data:raise ValueError('Invalid-source quarantine hash collision')
            path.unlink()
        else:path.rename(invalid)
        data=None
    if data is None:
        for attempt in range(4):
            try:
                with NETWORK_LOCK:
                    time.sleep(max(0,.51-(time.monotonic()-LAST_REQUEST)))
                    LAST_REQUEST=time.monotonic()
                with urllib.request.urlopen(url, timeout=120) as response:data=response.read() if max_bytes is None else response.read(max_bytes+1)
                if max_bytes is not None and len(data)>max_bytes:raise ValueError(f'Source exceeds maximum allowed size: {url}')
                if b'request rejected' in data[:10000].lower() and b'<html' in data[:1000].lower():
                    raise RejectedSource(f'Official server returned Request Rejected HTML instead of source: {url}')
                if not valid_source(url,data):raise ValueError('Invalid source response; refusing to cache')
                downloaded=True
                break
            except (urllib.error.HTTPError,urllib.error.URLError,ValueError) as e:
                if isinstance(e,RejectedSource):raise
                if isinstance(e,urllib.error.HTTPError) and e.code not in (429,500,502,503,504):raise
                if attempt==3:raise
                delay=20*(attempt+1)
                if isinstance(e,urllib.error.HTTPError):
                    try:delay=max(delay,int(e.headers.get('Retry-After','0')))
                    except ValueError:pass
                print('Retry',url,delay,repr(e),flush=True);time.sleep(delay)
        with LOCK:
            if not path.exists(): path.write_bytes(data)
    item={'key':key,'url':url,'path':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    if not downloaded:
        item['metadata_recovered_utc']=item.pop('retrieved_utc')
    with LOCK:
        mp=ROOT/'manifest.json'; manifest=json.loads(mp.read_text()) if mp.exists() else {}
        record_source(manifest,item,allow_replacement=downloaded and replaced_invalid)
        temp=mp.with_suffix('.tmp');temp.write_text(json.dumps(manifest,indent=2));temp.replace(mp)
    return data,key

def links(url):
    data,_=fetch(url)
    return [urllib.parse.urljoin(url,x) for x in re.findall(r'href="([^"]+)"',data.decode('latin1')) if not x.startswith('?')]

def lookup(year):
    if year==2005:
        import sys
        sys.path.insert(0,str(ROOT/'vendor'))
        import xlrd
        data,key=fetch(f'{BASE}{year}/documentation/Chapter_5_tables_summary_list.xls')
        sheet=xlrd.open_workbook(file_contents=data).sheet_by_index(0)
        return {str(sheet.cell_value(i,1)):{'sequence':int(sheet.cell_value(i,2)),'column':int(sheet.cell_value(i,4))-1,'lookup_source':key} for i in range(1,sheet.nrows) if sheet.cell_value(i,1) in ('B19013','B25077')}
    if year in (2007,2008):
        import pandas as pd
        tail='user_tools/merge_5_6.sas7bdat' if year==2008 else 'merge_5_6_final.sas7bdat'
        data,key=fetch(f'{BASE}{year}/documentation/1_year/{tail}')
        frame=pd.read_sas(io.BytesIO(data),format='sas7bdat',encoding='latin1')
        return {r.tblid:{'sequence':int(r.seq),'column':int(r.position)-1,'lookup_source':key} for r in frame.itertuples() if r.tblid in ('B19013','B25077') and pd.notna(r.position) and r.position>0}
    folder=f'{BASE}{year}/documentation/'+('1_year/' if 2007<=year<=2012 else '')+'user_tools/'
    if year==2006: choices=[f'{BASE}{year}/documentation/merge_5_6_final.txt']
    else:
        choices=[x for x in links(folder) if x.lower().endswith('.txt') and any(s in x.lower() for s in ['lookup','merge_5_6']) and '5yr' not in x.lower() and '3yr' not in x.lower()]
    choices.sort(key=lambda s:('1yr' not in s.lower(),s))
    for url in choices:
        data,key=fetch(url); txt=data.decode('utf-8-sig',errors='replace')
        try: dialect=csv.Sniffer().sniff(txt[:20000], delimiters=',\t|')
        except csv.Error: dialect=csv.excel
        rows=list(csv.reader(io.StringIO(txt),dialect)); header=[re.sub('[^a-z0-9]','',v.lower()) for v in rows[0]]
        def idx(names):
            return next(i for i,h in enumerate(header) if h in names)
        try:
            ti=idx(['tableid','tablenumber','table','tblid']); si=idx(['sequencenumber','sequence','seq']); pi=idx(['startposition','startpos','start','position'])
        except StopIteration: continue
        out={}
        for row in rows[1:]:
            if len(row)<=max(ti,si,pi): continue
            if row[ti] in ('B19013','B25077') and re.fullmatch(r'\d+(?:\.\d+)?',row[pi].strip()) and float(row[pi])>0:
                out[row[ti]]={'sequence':int(float(row[si])),'column':int(float(row[pi]))-1,'lookup_source':key}
        if len(out)==2:return out
    raise ValueError(f'Unrecognized lookup headers: {choices}')

def geography(data,year):
    txt=data.decode('latin1'); out={}
    rawrows=csv.reader(io.StringIO(txt)) if txt.startswith('ACSSF,') else txt.splitlines()
    for row in rawrows:
        if isinstance(row,str):
            # Census 2008 technical documentation pp.13–14; 2005 pp.11–12.
            offset=110 if year==2005 else 175 if year<=2008 else 178
            line=row;row=['']*50
            row[2]=line[8:11];row[3]=line[11:13];row[4]=line[13:20]
            row[48]=line[offset:offset+40].strip();row[49]=line[offset+40:offset+240].strip()
        if len(row)<50: raise ValueError('Unrecognized geography layout')
        level=row[2].zfill(3)
        if level not in ('010','040','310','314') or row[3]!='00': continue
        geo=row[48]; code='USA' if level=='010' else geo.split('US')[-1][-2 if level=='040' else -5:]
        if not re.fullmatch(level+r'00US\d*',geo) or (level=='010' and geo!='01000US'):
            raise ValueError(f'Unexpected geography identifier for {year}: {geo!r}')
        if level!='010' and not re.fullmatch(r'\d{2}' if level=='040' else r'\d{5}',code):
            raise ValueError(f'Unexpected area code for {year}: {code!r}')
        out[row[4]]={'year':year,'summary_level':level,'area_code':code,'area_name':row[49],'geo_id':geo}
    return out

def sequence_members(data,year,abbr,sequence,depth=0):
    """Yield only requested e/m files, including nested ZIPs in whole-state files."""
    if depth>3:raise ValueError('Unexpectedly deep archive nesting')
    expected=re.compile(rf'^([em]){year}1{abbr}{sequence:04d}000\.(?:txt|csv)$',re.I)
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for info in z.infolist():
            base=Path(info.filename).name
            if year==2005:
                match=re.fullmatch(rf'{abbr}000{sequence:04d}([em])\.2005-1yr',base,re.I)
            else:match=expected.fullmatch(base)
            if match:
                yield match.group(1).lower(),z.read(info)
            elif base.lower().endswith('.zip'):
                # A nested per-sequence archive is cheap to reject by name.
                matchseq=re.fullmatch(rf'{year}1{abbr}(\d{{4}})000\.zip',base,re.I)
                if matchseq and int(matchseq.group(1))!=sequence:continue
                if info.file_size>50*1024*1024:raise ValueError('Nested ZIP exceeds 50 MiB')
                yield from sequence_members(z.read(info),year,abbr,sequence,depth+1)

def region(year,abbr,name,meta):
    if year==2009:name=abbr.upper()
    folder=f'{BASE}{year}/data/'+('1_year_seq_by_state/' if year>=2009 else '1_year/' if year>=2007 else '')+f'{name}/'
    if year==2005:
        if abbr=='us':folder=f'{BASE}{year}/data/0UnitedStates/'
        data,gkey=fetch(folder+f'{abbr}geo.2005-1yr')
    else:
        try:data,gkey=fetch(folder+f'g{year}1{abbr}.'+('csv' if year>=2010 else 'txt'))
        except (ValueError,urllib.error.HTTPError) as failure:
            if year<2010 or 'checksum mismatch' in str(failure).lower():raise
            data,gkey=fetch(folder+f'g{year}1{abbr}.txt')
    records=geography(data,year)
    if abbr!='us': records={k:v for k,v in records.items() if v['summary_level']=='040'}
    if abbr=='us':
        if sum(r['summary_level']=='010' for r in records.values())!=1:
            raise ValueError(f'{year} US geography must contain exactly one national total')
    elif len(records)!=1:
        raise ValueError(f'{year} {abbr} geography must contain exactly one state total; got {len(records)}')
    for table,m in meta.items():
        filename=f'{abbr}000{m["sequence"]:04d}.2005-1yr.zip' if year==2005 else f'{year}1{abbr}{m["sequence"]:04d}000.zip'
        try:data,key=fetch(folder+filename)
        except (urllib.error.URLError,ValueError) as failure:
            if year<2010 or abbr=='us' or 'checksum mismatch' in str(failure).lower():raise
            alternate=f'{BASE}{year}/data/1_year_by_state/{name}_All_Geographies.zip'
            print('Using official whole-state archive after sequence failure',alternate,repr(failure),flush=True)
            data,key=fetch(alternate,max_bytes=50*1024*1024)
        seen_kinds=set()
        for kind,member_data in sequence_members(data,year,abbr,m['sequence']):
            if kind in seen_kinds:raise ValueError(f'Duplicate {kind} member for sequence {m["sequence"]}')
            seen_kinds.add(kind)
            stem='income' if table=='B19013' else 'home_value'
            field=stem+('_estimate_raw' if kind=='e' else '_moe_raw')
            for row in csv.reader(io.StringIO(member_data.decode('latin1'))):
                if len(row)<6:continue
                if row[5] in records:
                    records[row[5]][field]=row[m['column']]
                    records[row[5]][stem+'_source']=key
                    records[row[5]][stem+'_lookup_source']=m['lookup_source']
    for record in records.values():
        record['geography_source']=gkey
        for field in ('income_estimate_raw','income_moe_raw','home_value_estimate_raw','home_value_moe_raw'):
            if field not in record:raise ValueError(f'Missing {field}: {record}')
    return list(records.values())

def main():
    ROOT.mkdir(parents=True,exist_ok=True)
    p=argparse.ArgumentParser();p.add_argument('--years',default='2010-2019');p.add_argument('--states',action='store_true');p.add_argument('--workers',type=int,default=2);p.add_argument('--refresh',action='store_true',help='Re-extract even successfully persisted region records');a=p.parse_args()
    years=[]
    for chunk in a.years.split(','):
        lo,_,hi=chunk.partition('-');years.extend(range(int(lo),int(hi or lo)+1))
    cp=ROOT/'coverage.json';coverage=json.loads(cp.read_text()) if cp.exists() else {}; allrecords=[]
    for year in years:
        yp=ROOT/f'normalized_{year}.json'
        records=json.loads(yp.read_text(encoding='utf-8')) if yp.exists() else []
        try:
            jobs={'us':'UnitedStates'}
            if a.states:jobs.update(STATES)
            if not a.refresh:
                mp=ROOT/'manifest.json';manifest=json.loads(mp.read_text()) if mp.exists() else {}
                for abbr in list(jobs):
                    prior=coverage.get(f'{year}:{abbr}',{})
                    filenames={f'{abbr}geo.2005-1yr'} if year==2005 else {f'g{year}1{abbr}.csv',f'g{year}1{abbr}.txt'}
                    saved=[r for r in records if Path(urllib.parse.urlparse(manifest.get(r.get('geography_source'),{}).get('url','')).path).name in filenames]
                    expected='010' if abbr=='us' else '040'
                    if prior.get('status')=='ok' and len(saved)==prior.get('rows') and sum(r['summary_level']==expected for r in saved)==1 and all(all(field in r for field in ('income_estimate_raw','income_moe_raw','home_value_estimate_raw','home_value_moe_raw')) for r in saved):
                        del jobs[abbr];print(year,abbr,'using persisted extraction',flush=True)
            if jobs:meta=lookup(year);print(year,meta,flush=True)
            with ThreadPoolExecutor(max_workers=a.workers) as pool:
                fs={pool.submit(region,year,abbr,name,meta):abbr for abbr,name in jobs.items()}
                for f in as_completed(fs):
                    abbr=fs[f]
                    try:
                        new=f.result(); ids={r['geo_id'] for r in new}; records=[r for r in records if r['geo_id'] not in ids]+new
                        coverage[f'{year}:{abbr}']={'status':'ok','rows':len(new)};print(year,abbr,len(new),flush=True)
                    except Exception as e:coverage[f'{year}:{abbr}']={'status':'error','error':repr(e)};print(year,abbr,repr(e),flush=True)
        except Exception as e:coverage[str(year)]={'status':'error','error':repr(e)};print(year,repr(e),flush=True)
        yp.write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8');allrecords.extend(records)
        (ROOT/'coverage.json').write_text(json.dumps(coverage,indent=2))
    allrecords=[r for path in sorted(ROOT.glob('normalized_????.json')) for r in json.loads(path.read_text(encoding='utf-8'))]
    normalized=ROOT/'normalized.json'
    normalized.write_text(json.dumps(allrecords,ensure_ascii=False,indent=2),encoding='utf-8')
    metadata={'normalized_file':'normalized.json','sha256':hashlib.sha256(normalized.read_bytes()).hexdigest(),'rows':len(allrecords),'years':sorted({r['year'] for r in allrecords}),'generated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    (ROOT/'extraction_metadata.json').write_text(json.dumps(metadata,indent=2))

if __name__=='__main__':main()

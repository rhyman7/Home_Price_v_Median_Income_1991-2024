import csv,hashlib,io,json,tempfile,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import download_acs_archive as d

def geo_bytes(year,level='314',code='1234567890',component='00'):
    geo=level+component+'US'+code
    if year>=2010:
        row=['']*52;row[:5]=['ACSSF','US',level,component,'0000001'];row[48:50]=[geo,'Test division']
        text=io.StringIO();csv.writer(text).writerow(row);return text.getvalue().encode('latin1')
    offset=110 if year==2005 else 175 if year<=2008 else 178
    line=list(' '*(offset+240));line[:20]=list('ACSSF US'+level+component+'0000001')
    line[offset:offset+len(geo)]=list(geo);line[offset+40:offset+53]=list('Test division')
    return (''.join(line)+'\n').encode('latin1')

def zip_bytes(year,values):
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w') as z:
        for kind,value in values.items():
            name=f'us0000079{kind}.2005-1yr' if year==2005 else f'{kind}{year}1us0079000.txt'
            row=['ACSSF',f'{year}{kind}1','us','000','0079','0000001']+['WRONG']*171
            row[176]=value
            buf=io.StringIO();csv.writer(buf).writerow(row);z.writestr(name,buf.getvalue())
    return out.getvalue()

class ArchiveTests(unittest.TestCase):
    def test_geography_documented_offsets_and_metdiv_suffix(self):
        for year in (2005,2006,2009,2010):
            with self.subTest(year=year):
                r=d.geography(geo_bytes(year),year)['0000001']
                self.assertEqual(r['geo_id'],'31400US1234567890')
                self.assertEqual(r['area_code'],'67890')
                self.assertEqual(r['area_name'],'Test division')
                self.assertEqual(r['summary_level'],'314')
                self.assertEqual(d.geography(geo_bytes(year,component='01'),year),{})

    def test_state_national_and_cbsa_codes(self):
        for year in (2005,2006,2009,2010):
            for level,code,expected in [('010','','USA'),('040','06','06'),('310','12345','12345')]:
                with self.subTest(year=year,level=level):
                    self.assertEqual(d.geography(geo_bytes(year,level,code),year)['0000001']['area_code'],expected)

    def test_sequence_column_join_and_raw_moe_preservation(self):
        for year in (2005,2006,2009,2010):
            with self.subTest(year=year):
                geo=geo_bytes(year,'010','')
                archive=zip_bytes(year,{'e':'123+','m':'.'})
                def source(url):return (archive,'sequence_key') if url.endswith('.zip') else (geo,'geography_key')
                meta={table:{'sequence':79,'column':176,'lookup_source':'lookup_key'} for table in ('B19013','B25077')}
                with patch.object(d,'fetch',side_effect=source):r=d.region(year,'us','UnitedStates',meta)[0]
                for stem in ('income','home_value'):
                    self.assertEqual(r[stem+'_estimate_raw'],'123+')
                    self.assertEqual(r[stem+'_moe_raw'],'.')

    def test_pinned_valid_cache_mismatch_is_not_reblessed(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as tmp:
            root=Path(tmp);(root/'raw').mkdir();url='https://www2.census.gov/test.zip';key=hashlib.sha256(url.encode()).hexdigest()[:16]
            p=root/'raw'/(key+'_test.zip');p.write_bytes(zip_bytes(2010,{'e':'1','m':'2'}))
            manifest={key:{'key':key,'url':url,'path':str(p.relative_to(root)),'sha256':'pinned-different','bytes':1}}
            mp=root/'manifest.json';mp.write_text(json.dumps(manifest));before=mp.read_bytes()
            with patch.object(d,'ROOT',root),patch.object(d.urllib.request,'urlopen') as network:
                with self.assertRaisesRegex(ValueError,'Pinned source checksum mismatch'):d.fetch(url)
                network.assert_not_called()
            self.assertEqual(mp.read_bytes(),before)

    def test_official_state_fallback_selects_only_requested_sequence(self):
        buf=io.BytesIO()
        with zipfile.ZipFile(buf,'w') as target,zipfile.ZipFile(io.BytesIO(zip_bytes(2011,{'e':'230000','m':'1000'}))) as source:
            for name in source.namelist():
                content=source.read(name);kind=Path(name).name[0]
                target.writestr(f'nested/{kind}20111co0156000.txt',content)
                target.writestr(f'nested/{kind}20111co0155000.txt',b'WRONG SEQUENCE')
        archive=buf.getvalue();calls=[]
        def source(url,**kwargs):
            calls.append(url)
            if url.endswith('g20111co.csv'):return geo_bytes(2011,'040','08'),'geography_key'
            if url.endswith('Colorado_All_Geographies.zip'):
                self.assertEqual(kwargs['max_bytes'],50*1024*1024);return archive,'alternate_archive_key'
            raise ValueError('Invalid source response; refusing to cache')
        meta={table:{'sequence':156,'column':176,'lookup_source':'lookup_key'} for table in ('B19013','B25077')}
        with patch.object(d,'fetch',side_effect=source):r=d.region(2011,'co','Colorado',meta)[0]
        self.assertEqual(r['home_value_estimate_raw'],'230000')
        self.assertEqual(r['home_value_moe_raw'],'1000')
        self.assertEqual(r['home_value_source'],'alternate_archive_key')
        self.assertTrue(any('/1_year_by_state/Colorado_All_Geographies.zip' in u for u in calls))

    def test_invalid_refetch_preserves_history(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as tmp:
            root=Path(tmp);(root/'raw').mkdir();url='https://www2.census.gov/test.zip';key=hashlib.sha256(url.encode()).hexdigest()[:16]
            p=root/'raw'/(key+'_test.zip');invalid=b'<html>error</html>';p.write_bytes(invalid)
            oldhash=hashlib.sha256(invalid).hexdigest();mp=root/'manifest.json'
            mp.write_text(json.dumps({key:{'key':key,'url':url,'path':str(p.relative_to(root)),'sha256':oldhash,'bytes':len(invalid)}}))
            replacement=zip_bytes(2010,{'e':'1','m':'2'})
            with patch.object(d,'ROOT',root),patch.object(d.urllib.request,'urlopen',return_value=io.BytesIO(replacement)),patch.object(d.time,'sleep'):
                data,_=d.fetch(url)
            self.assertEqual(data,replacement);updated=json.loads(mp.read_text())[key]
            self.assertEqual(updated['sha256'],hashlib.sha256(replacement).hexdigest())
            self.assertEqual(updated['history'][0]['sha256'],oldhash)
            self.assertEqual((root/updated['history'][0]['path']).read_bytes(),invalid)

    def test_request_rejected_html_is_not_retried_or_cached(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as tmp:
            root=Path(tmp)
            with patch.object(d,'ROOT',root),patch.object(d.urllib.request,'urlopen',return_value=io.BytesIO(b'<html>Request Rejected</html>')) as network,patch.object(d.time,'sleep'):
                with self.assertRaises(d.RejectedSource):d.fetch('https://www2.census.gov/test.zip')
                self.assertEqual(network.call_count,1)
            self.assertEqual(list((root/'raw').iterdir()),[])
            self.assertFalse((root/'manifest.json').exists())

if __name__=='__main__':unittest.main()


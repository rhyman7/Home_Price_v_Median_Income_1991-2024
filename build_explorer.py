"""Build the offline explorer from the verified housing, paired ACS, and income panels."""
import csv,json,math
from pathlib import Path
from plotly.offline import get_plotlyjs
ROOT=Path(__file__).resolve().parent
NUMBERS=['hpi_growth_pct','income_growth_pct','growth_gap_pp','hpi_annual_sa','median_household_income','median_home_value_acs','median_household_income_acs','home_value_to_income_ratio','home_value_moe','income_moe']
def assemble(annual,dollars,history=None):
 def indexed(rows):
  out={}
  for row in rows:
   key=(row['geography_level'],row['place_id'],int(row['year']))
   if key in out:raise ValueError('Duplicate area-year')
   if key[2] not in range(1991,2025):raise ValueError('Unexpected year')
   out[key]=row
  return out
 a,d=indexed(annual),indexed(dollars)
 h={} if history is None else indexed([dict(r,geography_level='metro') for r in history])
 if history is not None and h.keys()!={k for k in a if k[0]=='metro'}:raise ValueError('Metro income panel keys differ')
 if a.keys()!=d.keys():raise ValueError('Annual panels have different area-year keys')
 output=[]
 for key,row in sorted(a.items()):
  dollar=d[key]
  if dollar['fhfa_place_name']!=row['place_name']:raise ValueError('Area names differ')
  merged=dict(row,**{k:v for k,v in dollar.items() if k not in row})
  r={k:merged.get(k,'') for k in ['geography_level','place_id','place_name','census_area_name','boundary_status','pair_status','income_status']}
  r['year']=key[2]
  for field in NUMBERS:
   value=merged.get(field,'');r[field]=None if value=='' or value is None else float(value)
   if r[field] is not None and not math.isfinite(r[field]):raise ValueError('Non-finite data')
  income=h.get(key) if key[0]=='metro' else dict(median_household_income=row.get('median_household_income',''),dollar_year=key[2],series='Historical Census household income',status='available_current_dollars',boundary_status='national_or_state',source_area_name=row['place_name'])
  income=income or {}
  for target,source in [('income_amount','median_household_income'),('income_dollar_year','dollar_year')]:
   value=income.get(source,'');r[target]=None if value in ('',None) else float(value)
   if r[target] is not None and not math.isfinite(r[target]):raise ValueError('Non-finite income')
  for target,source in [('income_series','series'),('income_coverage','status'),('income_boundary','boundary_status'),('income_source_area','source_area_name'),('income_source_url','source_url')]:r[target]=income.get(source,'')
  output.append(r)
 return output

def build():
 def read(path):
  with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
 records=assemble(read(ROOT/'data/annual/comparison_annual.csv'),read(ROOT/'data/dollars/acs_dollar_comparison.csv'),read(ROOT/'data/historical_metro_income/metro_income_1991_2024.csv'))
 payload=json.dumps(records,ensure_ascii=True,allow_nan=False,separators=(',',':')).replace('<','\\u003c')
 html=(ROOT/'web/explorer.html').read_text(encoding='utf-8').replace('/*__PLOTLY__*/',get_plotlyjs()).replace('/*__MODEL__*/',(ROOT/'web/explorer_model.js').read_text(encoding='utf-8')).replace('/*__DATA__*/',payload)
 out=ROOT/'reports/annual_growth_explorer.html';out.parent.mkdir(exist_ok=True);out.write_text(html,encoding='utf-8')
 print(f'Built {out.name}: {len(records):,} area-year records, all assets embedded.')
 return out
if __name__=='__main__':build()

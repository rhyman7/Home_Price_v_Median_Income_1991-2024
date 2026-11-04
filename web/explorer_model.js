(function(root){
'use strict';
function view(rows,mode,year){
 if(!['dollars','ratio','growth','income'].includes(mode))throw new Error('Unknown view');
 const row=rows.find(r=>r.year===Number(year));if(!row)throw new Error('Year not found');
 if(mode==='income'){
  const group=r=>r.income_series+' · '+(r.income_dollar_year===r.year?'current dollars':r.income_dollar_year+' dollars');
  const groups=[...new Set(rows.filter(r=>r.income_amount!=null).map(group))];
  const traces=groups.map(name=>({name,x:rows.map(r=>r.year),y:rows.map(r=>r.income_amount!=null&&group(r)===name?r.income_amount:null),unit:'$'}));
  const specs=[['Median household income','income_amount','$'],['Income dollar year','income_dollar_year','year'],['FHFA housing index','hpi_annual_sa','index']];
  let notice=row.income_amount==null?'No verified household income is available for this area and year. Missing values stay blank.':row.income_dollar_year!==row.year?'This estimate is expressed in '+row.income_dollar_year+' dollars, not '+row.year+' dollars. It is plotted separately from current-dollar income.':'';
  if(row.geography_level==='metro')notice+=(notice?' ':'')+'Sources and metro boundaries can differ across releases; no comparable 1991 income baseline is available.';
  return {row,metrics:specs.map(([label,key,unit])=>({label,key,unit,value:row[key]??null})),traces,notice,source:row.income_series||'Historical Census and ACS household income',axis:'Household income ($; dollar basis in legend)',caption:'Separate series preserve each source and dollar basis. Early metro observations use verified county-set matches; later ACS code matches retain historical boundaries. Gaps are not interpolated.'};
 }
 const growth=mode==='growth';
 const specs=growth?[
  ['Housing price growth','hpi_growth_pct','%'],['Household income growth','income_growth_pct','%'],['Growth gap','growth_gap_pp','pp']
 ]:[['Median home value','median_home_value_acs','$'],['Median household income','median_household_income_acs','$'],['Home value / income','home_value_to_income_ratio','×']];
 const metrics=specs.map(([label,key,unit])=>({label,key,unit,value:row[key]??null}));
 const fields=mode==='ratio'?[specs[2]]:specs.slice(0,2);
 const traces=fields.map(([name,key,unit])=>({name,x:rows.map(r=>r.year),y:rows.map(r=>r[key]??null),unit}));
 let notice='';
 if(growth && row.geography_level==='metro')notice='Available metro income amounts appear in Household income, including verified 1999–2004 observations. A comparable 1991 income baseline is unavailable, so this growth chart shows housing only.';
 if(!growth){const notes={before_acs_1year:'ACS home values and ACS income start in 2005. Historical household income and housing-index data for this year are available in Full history · 1991–2024.',no_standard_acs_1year_2020:'Standard ACS 1-year estimates were not released for 2020. This year is left blank.',no_exact_geography_match_in_loaded_sources:'No exact geographic match is available for this area and year. A different metro or parent area has not been substituted.',estimate_unavailable_or_censored:'One or both Census estimates are unavailable or bounded, so an exact ratio is not shown.'};notice=notes[row.pair_status]||'';}
 return {row,metrics,traces,notice,source:growth?'FHFA housing index + historical Census household income':'Census ACS 1-year · B25077 home value + B19013 income',axis:mode==='ratio'?'Home value / annual household income':growth?'Growth since 1991 (%)':'Survey-year dollars',caption:growth?'Growth from the 1991 annual baseline. The gap is a percentage-point difference, not a price-to-income ratio.':'Median owner-occupied home values, not sale prices. Income and home value come from the same ACS year and geography.'};
}
const api={view};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.ExplorerModel=api;
})(globalThis);

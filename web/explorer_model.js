(function(root){
'use strict';
function view(rows,mode,year){
 if(!['dollars','ratio','growth','income'].includes(mode))throw new Error('Unknown view');
 const row=rows.find(r=>r.year===Number(year));if(!row)throw new Error('Year not found');
 const benchmark='The same U.S. median household income is used for every location and every year. It is a national benchmark, not local income.';
 const growth=mode==='growth';
 const specs=mode==='income'?[
  ['U.S. median household income','income_amount','$'],['Income dollar year','income_dollar_year','year'],['Location housing index','hpi_annual_sa','index']
 ]:growth?[
  ['Location housing price growth','hpi_growth_pct','%'],['U.S. household income growth','income_growth_pct','%'],['Housing minus U.S. income growth','growth_gap_pp','pp']
 ]:[['Location median home value','median_home_value_acs','$'],['U.S. median household income','income_amount','$'],['Home value / U.S. income','home_value_to_national_income_ratio','×']];
 const metrics=specs.map(([label,key,unit])=>({label,key,unit,value:row[key]??null}));
 const fields=mode==='ratio'?[specs[2]]:mode==='income'?[specs[0]]:specs.slice(0,2);
 const traces=fields.map(([name,key,unit])=>({name,x:rows.map(r=>r.year),y:rows.map(r=>r[key]??null),unit}));
 let notice=benchmark;
 if(['dollars','ratio'].includes(mode)&&row.median_home_value_acs==null){
  notice+=' '+(row.year<2005?'ACS home values in this project start in 2005.':row.year===2020?'No standard ACS 1-year home values were released for 2020.':'No matching home-value estimate is available for this location and year.')+' National income remains available; no home value or ratio is invented.';
 }
 return {row,metrics,traces,notice,
  source:mode==='income'?'Historical Census U.S. median household income':growth?'FHFA location housing index + Census U.S. median household income':'ACS location home value + historical Census U.S. median household income',
  axis:mode==='ratio'?'Home value / U.S. annual household income':growth?'Growth since 1991 (%)':'Year-specific dollars',
  caption:mode==='income'?'This national income line is identical for the United States, every state, and every metro area.':growth?'Location housing growth and U.S. income growth use their 1991 annual baselines. The gap is a percentage-point difference.':'Home values are reported owner-occupied values, not sale prices. Ratios use the same-year U.S. income benchmark, not local income or a same-geography ACS pair.'};
}
const api={view};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.ExplorerModel=api;
})(globalThis);

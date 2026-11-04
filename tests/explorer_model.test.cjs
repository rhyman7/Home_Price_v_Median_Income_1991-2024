const test=require('node:test');const assert=require('node:assert/strict');const M=require('../web/explorer_model.js');
const row={year:2024,hpi_growth_pct:314.64,income_growth_pct:177.9,growth_gap_pp:136.74,median_home_value_acs:360600,median_household_income_acs:81604,home_value_to_income_ratio:360600/81604,pair_status:'available',geography_level:'national'};
test('dollars use ACS income, not historical income',()=>{const v=M.view([row],'dollars',2024);assert.equal(v.metrics[1].value,81604);assert.equal(v.traces[1].y[0],81604)});
test('growth keeps the original baseline and percentage point gap',()=>{const v=M.view([row],'growth',2024);assert.equal(v.metrics[1].value,177.9);assert.equal(v.metrics[2].unit,'pp')});
test('ratio is not calculated from FHFA indices',()=>assert.equal(M.view([row],'ratio',2024).traces[0].y[0],360600/81604));
test('missing2020 stays a chart gap and blank metric',()=>{const r={...row,year:2020,median_home_value_acs:null,median_household_income_acs:null,home_value_to_income_ratio:null,pair_status:'no_standard_acs_1year_2020'};const v=M.view([r],'dollars',2020);assert.equal(v.traces[0].y[0],null);assert.equal(v.metrics[0].value,null);assert.match(v.notice,/2020/)});
test('early ACS gap explained',()=>assert.match(M.view([{...row,year:1991,pair_status:'before_acs_1year',median_home_value_acs:null}],'dollars',1991).notice,/2005/));
test('metro growth never borrows available ACS income',()=>{const v=M.view([{...row,geography_level:'metro',income_growth_pct:null,growth_gap_pp:null}],'growth',2024);assert.equal(v.traces[1].y[0],null);assert.match(v.notice,/1991/)});
test('missing area match is explicit',()=>assert.match(M.view([{...row,pair_status:'no_exact_geography_match_in_loaded_sources'}],'dollars',2024).notice,/geographic/));
test('unknown view rejected',()=>assert.throws(()=>M.view([row],'bogus',2024)));
test('income traces keep constant dollars separate and leave gaps',()=>{
 const rows=[{year:2000,income_amount:50630,income_dollar_year:2003,income_series:'ACS testing program',income_coverage:'available_constant_dollars',geography_level:'metro'},
 {year:2001,income_amount:null,income_dollar_year:null,geography_level:'metro'},
 {year:2002,income_amount:50000,income_dollar_year:2002,income_series:'ACS testing program',geography_level:'metro'}];
 const v=M.view(rows,'income',2000);assert.equal(v.metrics[0].value,50630);assert.equal(v.traces.length,2);assert.match(v.notice,/2003 dollars/);
 assert.deepEqual(v.traces[0].y,[50630,null,null]);assert.deepEqual(v.traces[1].y,[null,null,50000]);
});

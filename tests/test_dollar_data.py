import unittest
from build_dollar_data import estimate, build_panel, table_by_geoid, verify_archive_sources

def hpi(level="metro",pid="12345",name="Example",year=2024):
 return dict(geography_level=level,place_id=pid,place_name=name,year=str(year))
def acs(level="310",code="12345",year=2024,**kw):
 r=dict(year=year,summary_level=level,area_code=code,area_name="Example Census",geo_id="310M700US12345",income_estimate_raw="50000",income_moe_raw="2000",home_value_estimate_raw="200000",home_value_moe_raw="10000")
 return dict(r,**kw)
class DollarTests(unittest.TestCase):
 def test_duplicate_source_table_rows_rejected(self):
  with self.assertRaises(ValueError):table_by_geoid([{"GEO_ID":"0100000US"},{"GEO_ID":"0100000US"}])
 def test_text_moe_censoring_not_exact(self):self.assertIsNone(estimate("250001","***")[0])
 def test_dash_is_unavailable_not_censored(self):self.assertEqual(estimate("-","-")[2],"unavailable_or_suppressed")
 def test_missing_archive_source_reference_rejected(self):
  with self.assertRaises(ValueError):verify_archive_sources(None,[{"income_source":"missing"}],{})
 def test_exact_estimate(self):self.assertEqual(estimate("50,000","1200"),(50000.0,1200.0,"available"))
 def test_suppressed_not_negative_dollars(self):self.assertIsNone(estimate("-666666666","-666666666")[0])
 def test_open_ended_median_not_exact(self):self.assertEqual(estimate("250001","-333333333")[2],"censored_median")
 def test_symbolic_censoring(self):self.assertIsNone(estimate("250000+","***")[0])
 def test_nonfinite_rejected(self):self.assertIsNone(estimate("NaN","1")[0])
 def test_same_release_pair_ratio(self):
  r=build_panel([hpi()],[acs()],{})[0]
  self.assertEqual(r["home_value_to_income_ratio"],4)
  self.assertEqual(r["income_source"],"ACS 1-year B19013")
 def test_division_not_matched_to_parent(self):
  r=build_panel([hpi(name="Example (MSAD)")],[acs()],{})[0]
  self.assertIsNone(r["home_value_to_income_ratio"])
 def test_division_matches_division(self):
  r=build_panel([hpi(name="Example (MSAD)")],[acs(level="314")],{})[0]
  self.assertEqual(r["home_value_to_income_ratio"],4)
 def test_no_imputation_1991(self):
  r=build_panel([hpi(year=1991)],[acs()],{})[0]
  self.assertEqual(r["pair_status"],"before_acs_1year")
  self.assertIsNone(r["median_household_income_acs"])
 def test_no_standard_2020(self):
  r=build_panel([hpi(year=2020)],[acs(year=2020)],{})[0]
  self.assertEqual(r["pair_status"],"no_standard_acs_1year_2020")
 def test_historical_boundary_flag(self):
  r=build_panel([hpi(year=2019)],[acs(year=2019)],{})[0]
  self.assertEqual(r["boundary_status"],"historical_not_harmonized")
 def test_state_maps_postal_to_fips(self):
  r=build_panel([hpi(level="state",pid="KY",name="Kentucky")],[acs(level="040",code="21")],{"KY":"21"})[0]
  self.assertEqual(r["home_value_to_income_ratio"],4)
 def test_duplicate_keys_rejected(self):
  with self.assertRaises(ValueError):build_panel([hpi()],[acs(),acs()],{})
 def test_censored_value_no_ratio(self):
  r=build_panel([hpi()],[acs(home_value_estimate_raw="2000001",home_value_moe_raw="-333333333")],{})[0]
  self.assertIsNone(r["home_value_to_income_ratio"])
if __name__=="__main__":unittest.main()

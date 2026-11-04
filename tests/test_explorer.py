import unittest
from build_explorer import assemble
class ExplorerTests(unittest.TestCase):
 def setUp(self):
  self.a=dict(geography_level='national',place_id='USA',place_name='United States',year='2024',income_growth_pct='177.9')
  self.d=dict(geography_level='national',place_id='USA',fhfa_place_name='United States',year='2024',median_household_income_acs='81604',pair_status='available')
 def test_income_sources_stay_separate(self):
  r=assemble([self.a],[self.d])[0];self.assertEqual(r['income_growth_pct'],177.9);self.assertEqual(r['median_household_income_acs'],81604)
 def test_duplicate_rejected(self):
  with self.assertRaises(ValueError):assemble([self.a,self.a],[self.d])
 def test_mismatched_keys_rejected(self):
  with self.assertRaises(ValueError):assemble([self.a],[])
 def test_nonfinite_rejected(self):
  with self.assertRaises(ValueError):assemble([dict(self.a,income_growth_pct='nan')],[self.d])
 def test_missing_remains_null(self):self.assertIsNone(assemble([self.a],[self.d])[0]['median_home_value_acs'])
 def test_metro_supplement_is_visible_without_creating_growth(self):
  a=dict(self.a,geography_level='metro',place_id='41740',year='2000',income_growth_pct='')
  d=dict(self.d,geography_level='metro',place_id='41740',year='2000',median_household_income_acs='')
  h=dict(place_id='41740',year='2000',median_household_income='50630',dollar_year='2003',series='ACS testing program',status='available_constant_dollars')
  r=assemble([a],[d],[h])[0]
  self.assertEqual(r['income_amount'],50630)
  self.assertEqual(r['income_dollar_year'],2003)
  self.assertIsNone(r['income_growth_pct'])
  self.assertIsNone(r['median_household_income_acs'])
 def test_missing_supplemental_year_rejected(self):
  with self.assertRaises(ValueError):assemble([dict(self.a,geography_level='metro')],[dict(self.d,geography_level='metro')],[])

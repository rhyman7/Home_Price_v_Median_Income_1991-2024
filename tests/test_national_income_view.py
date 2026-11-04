import unittest
from build_explorer import national_income_view


class NationalIncomeViewTests(unittest.TestCase):
    def test_all_locations_use_same_year_national_income_even_when_local_exists(self):
        national = dict(geography_level='national', year=1991, median_household_income=30130,
                        income_growth_pct=0, hpi_growth_pct=0, median_home_value_acs=None)
        local = dict(national, geography_level='metro', median_household_income=99999,
                     income_amount=99999, income_growth_pct=None, hpi_growth_pct=20,
                     median_home_value_acs=180780, median_household_income_acs=90000,
                     income_source_area='Local area', income_moe=500)
        result = national_income_view([national, local])
        self.assertEqual(result[1]['income_amount'], 30130)
        self.assertEqual(result[1]['income_growth_pct'], 0)
        self.assertEqual(result[1]['growth_gap_pp'], 20)
        self.assertEqual(result[1]['home_value_to_national_income_ratio'], 6)
        self.assertNotIn('median_household_income_acs', result[1])
        self.assertNotIn('income_moe', result[1])
        self.assertEqual(result[1]['income_source_area'], 'United States')
        self.assertEqual(local['income_amount'], 99999)

    def test_missing_home_value_does_not_create_a_ratio(self):
        r = dict(geography_level='national',year=2020,median_household_income=68010,
                 income_growth_pct=100,hpi_growth_pct=200,median_home_value_acs=None)
        self.assertIsNone(national_income_view([r])[0]['home_value_to_national_income_ratio'])

    def test_missing_national_year_rejected(self):
        with self.assertRaises(ValueError):
            national_income_view([dict(geography_level='metro',year=1991)])

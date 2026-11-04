import unittest
from unittest.mock import patch
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import build_historical_metro_income as history


class HistoricalIncomeTests(unittest.TestCase):
    def test_only_equal_whole_county_sets_can_match(self):
        current = {'06037'}
        self.assertTrue(history.same_boundary({'counties': {'06037'}, 'partial': False}, current))
        self.assertFalse(history.same_boundary({'counties': {'06037', '06059'}, 'partial': False}, current))
        self.assertFalse(history.same_boundary({'counties': {'06037'}, 'partial': True}, current))
        self.assertFalse(history.same_boundary({'counties': set(), 'partial': False}, set()))

    def test_suppression_is_not_zero_and_significance_is_not_censoring(self):
        self.assertEqual(history.numeric('50,630 *'), 50630)
        for value in ('N', '(X)', '-', '*****', '', '100,000+', '-1'):
            self.assertIsNone(history.numeric(value))

    def test_parent_cmsa_keeps_all_child_counties(self):
        text = '\n'.join([
            '4472            49                              Los Angeles-Riverside-Orange County, CA CMSA',
            '4472    4480    49                                 Los Angeles-Long Beach, CA PMSA',
            '4472    4480    49      06037   1                       Los Angeles County',
            '4472    5945    49                                 Orange County, CA PMSA',
            '4472    5945    49      06059   1                       Orange County',
        ])
        areas = history.old_boundaries(text)
        self.assertEqual(areas['380:4472']['counties'], {'06037', '06059'})
        self.assertEqual(areas['385:4480']['counties'], {'06037'})

    def test_multiyear_values_keep_constant_dollar_basis(self):
        row = dict(GEONAME='San Diego, CA MSA', stub='Median household income (dollars)',
                   PROFTBL='3', PROFLN='63', pctd_00='50,630', pctd_01='48,651',
                   pctd_02='51,144', pctd_03='49,886')
        result = history.multi_records([row], {'sandiegocamsa': '380:7320'})
        self.assertEqual([r['year'] for r in result], [2000, 2001, 2002, 2003])
        self.assertTrue(all(r['dollar_year'] == 2003 for r in result))
        self.assertEqual(result[0]['median_household_income'], 50630)
        self.assertEqual(result[0]['series'], 'ACS testing program')

    def test_tucson_two_year_profile_uses_first_year_estimate_not_difference(self):
        with patch.object(history, 'RAW', Path(__file__).parent / 'fixtures/early_income'):
            result = history.tucson_record(2000)
        self.assertEqual(result['median_household_income'], 36675)
        self.assertEqual(result['year'], 2000)
        self.assertEqual(result['dollar_year'], 2002)

    def test_single_year_source_value_and_confidence_interval(self):
        row = history.single_record(Path(__file__).parent / 'fixtures/early_income/2004_380_7320.xls', 2004, '380:7320')
        self.assertEqual(row['median_household_income'], 51012)
        self.assertEqual((row['lower_bound'], row['upper_bound']), (49708, 52316))

if __name__ == '__main__':
    unittest.main()

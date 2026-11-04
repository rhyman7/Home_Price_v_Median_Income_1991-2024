import unittest
from build_annual import annualize_hpi, nominal_income, combine

def quarters(year, values, place_id="USA", level="USA or Census Division"):
    return [dict(hpi_type="traditional", hpi_flavor="purchase-only", frequency="quarterly", level=level, place_id=place_id, place_name="United States" if place_id=="USA" else "Example metro", yr=str(year), period=str(i+1), index_sa=str(v), index_nsa=str(v)) for i,v in enumerate(values)]

class AnnualTests(unittest.TestCase):
    def test_annual_mean_and_annual_baseline(self):
        out=annualize_hpi(quarters(1991,[100,110,120,130])+quarters(1992,[115,125,135,145]))
        self.assertEqual(out[0]["hpi_annual_sa"],115)
        self.assertAlmostEqual(out[1]["hpi_growth_pct"],100*(130/115-1))
        self.assertEqual(out[0]["hpi_growth_pct"],0)
    def test_missing_quarter_remains_missing(self):
        out=annualize_hpi(quarters(1991,[100]*4)+quarters(1992,[120]*3))
        self.assertIsNone(out[1]["hpi_annual_sa"])
        self.assertEqual(out[1]["hpi_status"],"incomplete_year")
    def test_duplicate_quarter_rejected(self):
        q=quarters(1991,[100]*4)
        with self.assertRaises(ValueError):annualize_hpi(q+[q[0]])
    def test_nonpositive_index_rejected(self):
        with self.assertRaises(ValueError):annualize_hpi(quarters(1991,[0,100,100,100]))
    def test_nan_index_rejected(self):
        with self.assertRaises(ValueError):annualize_hpi(quarters(1991,["nan",100,100,100]))
    def test_missing_baseline_does_not_rebase_to_later_year(self):
        out=annualize_hpi(quarters(1992,[120]*4))
        self.assertIsNone(out[1]["hpi_growth_pct"])
        self.assertEqual(out[1]["hpi_status"],"missing_1991_baseline")
    def test_excludes_other_flavors_and_census_divisions(self):
        q=quarters(1991,[100]*4); other=quarters(1991,[999]*4,place_id="DV_TEST")
        flavor=[dict(r,hpi_flavor="all-transactions") for r in q]
        self.assertEqual(len(annualize_hpi(q+other+flavor)),34)
    def test_nominal_section_explicitly_selected(self):
        raw=[{"State":"United States","1991 Median income":"10,000","1992 Median income":"12,000"},{"State":"2024 Dollars"},{"State":"United States","1991 Median income":"99,000"}]
        out=nominal_income(raw,{"United States":("national","USA")})
        self.assertEqual(out[0]["median_household_income"],10000)
        self.assertAlmostEqual(out[1]["income_growth_pct"],20)
    def test_duplicate_nominal_geography_rejected(self):
        r={"State":"United States","1991 Median income":"10,000"}
        with self.assertRaises(ValueError):nominal_income([r,r],{"United States":("national","USA")})
    def test_metro_income_is_not_borrowed_or_dropped(self):
        h=annualize_hpi(quarters(1991,[100]*4,place_id="12345",level="MSA"))
        out=combine(h,[])
        self.assertEqual(len(out),34)
        self.assertIsNone(out[0]["median_household_income"])
        self.assertIsNone(out[0]["growth_gap_pp"])
    def test_join_uses_geography_id_and_computes_gap(self):
        h=annualize_hpi(quarters(1991,[100]*4)+quarters(1992,[150]*4))
        i=nominal_income([{"State":"United States","1991 Median income":"10000","1992 Median income":"12000"}],{"United States":("national","USA")})
        out=combine(h,i)
        self.assertAlmostEqual(out[1]["growth_gap_pp"],30)
        self.assertIsNone(out[2]["growth_gap_pp"])

if __name__=="__main__":unittest.main()

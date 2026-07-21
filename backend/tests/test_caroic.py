"""
Test suite for Carbon-Adjusted Return on Invested Capital (CAROIC)
Tests the calc_caroic() function in engine.py for correctness and edge cases.
"""
import sys
import os
import pytest

# Ensure backend is on sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engine import calc_caroic


class TestCAROICBasicCalculation:
    """Verify the core CAROIC formula produces correct results."""

    def test_standard_scenario(self):
        """Standard positive-profit company with moderate carbon."""
        result = calc_caroic(
            ebitda=33_000_000,
            invested_capital=50_000_000,
            carbon_tonnage=2850,
            tax_rate=0.25,
            shadow_carbon_price=250.0,
        )
        # NOPAT = 33M * 0.75 = 24.75M
        assert result["nopat"] == 24_750_000.0
        # Carbon charge = 2850 * 250 = 712,500
        assert result["carbon_capital_charge"] == 712_500.0
        # Adjusted capital = 50M + 0.7125M = 50,712,500
        assert result["adjusted_capital"] == 50_712_500.0
        # CAROIC = 24.75M / 50.7125M ≈ 0.4881
        assert result["caroic"] == pytest.approx(0.4881, abs=0.001)
        assert result["caroic_pct"] == pytest.approx(48.81, abs=0.1)
        assert result["grade"] == "A+"

    def test_zero_carbon_is_pure_roic(self):
        """With zero carbon tonnage, CAROIC should equal pure ROIC."""
        result = calc_caroic(
            ebitda=10_000_000,
            invested_capital=100_000_000,
            carbon_tonnage=0,
            tax_rate=0.25,
            shadow_carbon_price=250.0,
        )
        # NOPAT = 10M * 0.75 = 7.5M
        # Adjusted capital = 100M + 0 = 100M
        # CAROIC = 7.5M / 100M = 0.075 = 7.5%
        assert result["caroic_pct"] == 7.5
        assert result["carbon_capital_charge"] == 0.0
        assert result["grade"] == "C"

    def test_high_carbon_compresses_returns(self):
        """Same EBITDA and capital, but high carbon should compress CAROIC."""
        low_carbon = calc_caroic(
            ebitda=20_000_000, invested_capital=50_000_000,
            carbon_tonnage=1000, shadow_carbon_price=250.0,
        )
        high_carbon = calc_caroic(
            ebitda=20_000_000, invested_capital=50_000_000,
            carbon_tonnage=20000, shadow_carbon_price=250.0,
        )
        assert low_carbon["caroic_pct"] > high_carbon["caroic_pct"]
        assert low_carbon["adjusted_capital"] < high_carbon["adjusted_capital"]

    def test_shadow_price_sensitivity(self):
        """Higher shadow carbon price should reduce CAROIC."""
        low_price = calc_caroic(
            ebitda=20_000_000, invested_capital=50_000_000,
            carbon_tonnage=5000, shadow_carbon_price=100.0,
        )
        high_price = calc_caroic(
            ebitda=20_000_000, invested_capital=50_000_000,
            carbon_tonnage=5000, shadow_carbon_price=500.0,
        )
        assert low_price["caroic_pct"] > high_price["caroic_pct"]


class TestCAROICEdgeCases:
    """Test edge cases that could cause division by zero or unexpected results."""

    def test_zero_invested_capital_and_zero_carbon(self):
        """Both zero → CAROIC should be 0.0, not NaN or error."""
        result = calc_caroic(
            ebitda=10_000_000,
            invested_capital=0,
            carbon_tonnage=0,
        )
        assert result["caroic"] == 0.0
        assert result["caroic_pct"] == 0.0
        assert result["adjusted_capital"] == 0.0
        assert result["grade"] == "D"

    def test_negative_invested_capital(self):
        """Negative treasury (insolvency) should floor at 0, not flip sign."""
        result = calc_caroic(
            ebitda=10_000_000,
            invested_capital=-50_000_000,
            carbon_tonnage=1000,
            shadow_carbon_price=250.0,
        )
        # Invested capital floored at 0
        # Adjusted capital = 0 + 250,000 = 250,000
        assert result["adjusted_capital"] == 250_000.0
        assert result["invested_capital_raw"] == -50_000_000.0
        # NOPAT = 10M * 0.75 = 7.5M
        # CAROIC = 7.5M / 250K = 30.0 = 3000%
        assert result["caroic_pct"] > 0

    def test_negative_ebitda(self):
        """Negative EBITDA should produce negative CAROIC and grade F."""
        result = calc_caroic(
            ebitda=-5_000_000,
            invested_capital=50_000_000,
            carbon_tonnage=2000,
        )
        assert result["nopat"] < 0
        assert result["caroic"] < 0
        assert result["caroic_pct"] < 0
        assert result["grade"] == "F"

    def test_zero_ebitda(self):
        """Zero EBITDA should produce 0% CAROIC."""
        result = calc_caroic(
            ebitda=0,
            invested_capital=50_000_000,
            carbon_tonnage=2000,
        )
        assert result["caroic"] == 0.0
        assert result["caroic_pct"] == 0.0
        assert result["nopat"] == 0.0
        assert result["grade"] == "D"

    def test_negative_carbon_tonnage_clamped(self):
        """Negative carbon tonnage should be clamped to 0."""
        result = calc_caroic(
            ebitda=10_000_000,
            invested_capital=50_000_000,
            carbon_tonnage=-500,
        )
        assert result["carbon_tonnage"] == 0.0
        assert result["carbon_capital_charge"] == 0.0

    def test_negative_shadow_price_clamped(self):
        """Negative shadow carbon price should be clamped to 0."""
        result = calc_caroic(
            ebitda=10_000_000,
            invested_capital=50_000_000,
            carbon_tonnage=1000,
            shadow_carbon_price=-100,
        )
        assert result["carbon_capital_charge"] == 0.0

    def test_very_large_values(self):
        """Extreme values should not overflow or produce NaN."""
        result = calc_caroic(
            ebitda=1_000_000_000_000,  # $1 trillion
            invested_capital=500_000_000_000,
            carbon_tonnage=1_000_000,
            shadow_carbon_price=1000.0,
        )
        assert result["caroic"] > 0
        assert result["caroic_pct"] > 0
        assert isinstance(result["caroic"], float)

    def test_very_small_values(self):
        """Very small values should produce sensible results."""
        result = calc_caroic(
            ebitda=100,
            invested_capital=1000,
            carbon_tonnage=0.01,
            shadow_carbon_price=250.0,
        )
        assert isinstance(result["caroic"], float)
        assert result["caroic_pct"] >= 0


class TestCAROICTaxRate:
    """Test tax rate edge cases and clamping."""

    def test_zero_tax_rate(self):
        """Zero tax → NOPAT equals EBITDA."""
        result = calc_caroic(ebitda=10_000_000, invested_capital=50_000_000,
                             carbon_tonnage=0, tax_rate=0.0)
        assert result["nopat"] == 10_000_000.0

    def test_full_tax_rate(self):
        """100% tax → NOPAT is zero."""
        result = calc_caroic(ebitda=10_000_000, invested_capital=50_000_000,
                             carbon_tonnage=0, tax_rate=1.0)
        assert result["nopat"] == 0.0
        assert result["caroic"] == 0.0

    def test_negative_tax_rate_clamped(self):
        """Negative tax rate should clamp to 0."""
        result = calc_caroic(ebitda=10_000_000, invested_capital=50_000_000,
                             carbon_tonnage=0, tax_rate=-0.5)
        assert result["tax_rate"] == 0.0
        assert result["nopat"] == 10_000_000.0

    def test_excessive_tax_rate_clamped(self):
        """Tax rate > 1 should clamp to 1.0."""
        result = calc_caroic(ebitda=10_000_000, invested_capital=50_000_000,
                             carbon_tonnage=0, tax_rate=1.5)
        assert result["tax_rate"] == 1.0
        assert result["nopat"] == 0.0


class TestCAROICGrading:
    """Verify grading thresholds are correct."""

    def test_grade_a_plus(self):
        """CAROIC >= 25% should be A+."""
        # NOPAT = 100M * 0.75 = 75M, Capital = 200M, CAROIC = 37.5%
        result = calc_caroic(ebitda=100_000_000, invested_capital=200_000_000,
                             carbon_tonnage=0)
        assert result["grade"] == "A+"

    def test_grade_a(self):
        """15% <= CAROIC < 25% should be A."""
        # NOPAT = 10M * 0.75 = 7.5M, Capital = 40M, CAROIC = 18.75%
        result = calc_caroic(ebitda=10_000_000, invested_capital=40_000_000,
                             carbon_tonnage=0)
        assert result["grade"] == "A"

    def test_grade_b(self):
        """10% <= CAROIC < 15% should be B."""
        # NOPAT = 10M * 0.75 = 7.5M, Capital = 62.5M, CAROIC = 12%
        result = calc_caroic(ebitda=10_000_000, invested_capital=62_500_000,
                             carbon_tonnage=0)
        assert result["grade"] == "B"

    def test_grade_c(self):
        """5% <= CAROIC < 10% should be C."""
        # NOPAT = 10M * 0.75 = 7.5M, Capital = 100M, CAROIC = 7.5%
        result = calc_caroic(ebitda=10_000_000, invested_capital=100_000_000,
                             carbon_tonnage=0)
        assert result["grade"] == "C"

    def test_grade_d(self):
        """0% <= CAROIC < 5% should be D."""
        # NOPAT = 10M * 0.75 = 7.5M, Capital = 200M, CAROIC = 3.75%
        result = calc_caroic(ebitda=10_000_000, invested_capital=200_000_000,
                             carbon_tonnage=0)
        assert result["grade"] == "D"

    def test_grade_f(self):
        """CAROIC < 0% should be F."""
        result = calc_caroic(ebitda=-5_000_000, invested_capital=50_000_000,
                             carbon_tonnage=0)
        assert result["grade"] == "F"


class TestCAROICOutputStructure:
    """Verify the output dict has all expected keys."""

    def test_all_keys_present(self):
        result = calc_caroic(ebitda=10_000_000, invested_capital=50_000_000,
                             carbon_tonnage=1000)
        expected_keys = {
            "caroic", "caroic_pct", "nopat", "carbon_capital_charge",
            "adjusted_capital", "invested_capital_raw", "carbon_tonnage",
            "shadow_carbon_price", "tax_rate", "grade", "interpretation",
        }
        assert set(result.keys()) == expected_keys

    def test_interpretation_is_nonempty_string(self):
        result = calc_caroic(ebitda=10_000_000, invested_capital=50_000_000,
                             carbon_tonnage=1000)
        assert isinstance(result["interpretation"], str)
        assert len(result["interpretation"]) > 10

    def test_grade_is_valid(self):
        for ebitda in [-10_000_000, 0, 5_000_000, 20_000_000, 100_000_000]:
            result = calc_caroic(ebitda=ebitda, invested_capital=50_000_000,
                                 carbon_tonnage=1000)
            assert result["grade"] in {"A+", "A", "B", "C", "D", "F"}


class TestCAROICDocumentedExamples:
    """Verify the worked examples from the documentation match the code."""

    def test_worked_example_1_strong_performer(self):
        """From Section 11.24: EBITDA=$33M, Treasury=$50M, Tonnage=2850."""
        result = calc_caroic(
            ebitda=33_000_000,
            invested_capital=50_000_000,
            carbon_tonnage=2850,
            tax_rate=0.25,
            shadow_carbon_price=250.0,
        )
        assert result["nopat"] == 24_750_000.0
        assert result["carbon_capital_charge"] == 712_500.0
        assert result["adjusted_capital"] == 50_712_500.0
        assert result["caroic_pct"] == pytest.approx(48.81, abs=0.1)
        assert result["grade"] == "A+"

    def test_worked_example_2_carbon_heavy(self):
        """From Section 11.24: same EBITDA but 12,000t carbon."""
        result = calc_caroic(
            ebitda=33_000_000,
            invested_capital=50_000_000,
            carbon_tonnage=12000,
            tax_rate=0.25,
            shadow_carbon_price=250.0,
        )
        assert result["nopat"] == 24_750_000.0
        assert result["carbon_capital_charge"] == 3_000_000.0
        assert result["adjusted_capital"] == 53_000_000.0
        assert result["caroic_pct"] == pytest.approx(46.70, abs=0.1)
        assert result["grade"] == "A+"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

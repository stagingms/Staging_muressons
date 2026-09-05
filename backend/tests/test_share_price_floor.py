"""Share price floor — a traded stock price is never negative.

`calculate_equity_bridge` reports `price_per_share` floored at $1.00 (matching
the live in-game stock engine, which already floors intraday prices at $1). When
net debt has wiped out equity, the honest signal is `equity_wiped_out` /
`equity_value < 0` — NOT a negative quote. Pins:

  1. An insolvent outcome (equity value < 0) reports price_per_share == 1.0,
     never negative, with equity_wiped_out True and the raw value preserved.
  2. A solvent outcome is unchanged (no floor applied).
  3. The floor never inflates a price that is already above $1.
  4. share_price_change_pct / vs_ipo are computed off the floored price.
"""

import terminal_valuation as tv
from terminal_valuation import SHARE_PRICE_FLOOR, calculate_equity_bridge


def test_floor_is_one_dollar():
    assert SHARE_PRICE_FLOOR == 1.0


def test_insolvent_outcome_floors_at_one_not_negative():
    # The screenshot case: EV −$397.1M, net debt large enough to push equity to
    # −$1.42B ⇒ raw price −$14.20, reported $1.00.
    b = calculate_equity_bridge(
        enterprise_value=-397_100_000,
        net_debt=1_022_900_000,
        book_equity=0.0,
        total_revenue=500_000_000,
    )
    assert b["equity_value"] < 0
    assert b["equity_wiped_out"] is True
    assert b["price_per_share"] == 1.0          # floored — never negative
    assert b["price_per_share"] >= SHARE_PRICE_FLOOR
    assert b["price_per_share_raw"] < 0          # honest pre-floor value preserved
    assert b["share_price_floored"] is True
    # Change % is measured off the floored price, and stays a loss vs IPO.
    assert b["share_price_vs_ipo"] == "loss"
    assert b["share_price_change_pct"] < 0


def test_exactly_wiped_to_below_floor_still_floors():
    # Small positive equity that divides to < $1/share still floors to $1.
    from config import TV_SHARES_OUTSTANDING as _SH
    b = calculate_equity_bridge(
        enterprise_value=0.5 * _SH,   # equity = half a dollar per share raw
        net_debt=0.0,
        book_equity=0.0,
        total_revenue=0.0,
    )
    assert b["price_per_share_raw"] == 0.50
    assert b["price_per_share"] == 1.0
    assert b["share_price_floored"] is True
    assert b["equity_wiped_out"] is False        # equity is positive, just tiny


def test_solvent_outcome_is_unchanged():
    from config import TV_SHARES_OUTSTANDING as _SH
    b = calculate_equity_bridge(
        enterprise_value=70.0 * _SH + 1_000_000_000,
        net_debt=1_000_000_000,   # equity = $70/share
        book_equity=2_000_000_000,
        total_revenue=1_000_000_000,
    )
    assert b["price_per_share"] == 70.0
    assert b["price_per_share_raw"] == 70.0
    assert b["share_price_floored"] is False
    assert b["equity_wiped_out"] is False
    assert b["share_price_vs_ipo"] == "gain"


def test_floor_never_inflates_above_one():
    # A price already above $1 must pass through untouched.
    from config import TV_SHARES_OUTSTANDING as _SH
    b = calculate_equity_bridge(
        enterprise_value=2.0 * _SH,
        net_debt=0.0,             # $2.00/share
        book_equity=0.0,
        total_revenue=0.0,
    )
    assert b["price_per_share"] == 2.0
    assert b["share_price_floored"] is False


def test_full_terminal_valuation_surfaces_the_flag():
    # The end-to-end EV→equity→price path must carry equity_wiped_out and a
    # floored price — a modest-revenue firm buried under net debt.
    bus = [{
        "bu_id": "pharma", "revenue_base": 100_000_000, "opex_base": 60_000_000,
        "carbon_intensity": 0, "tco2e_emissions": 0,
    }]
    res = tv.calculate_terminal_value(
        bus=bus, mr=0.5, exit_multiple=12.0, net_debt=5_000_000_000,
    )
    assert res["equity_value"] < 0
    assert res["equity_wiped_out"] is True
    assert res["price_per_share"] == 1.0
    assert res["price_per_share"] >= SHARE_PRICE_FLOOR


def test_a_typical_terminal_ev_prices_above_the_amber_threshold():
    """F-20 (audit 2026-09-04): with 100M shares at a $50 IPO the implied
    market cap was $5.0B against terminal EVs of $0–0.9B, so every solvent
    team's reveal priced at $1–3 ("loss −94%", red; GameOverSummary colours
    green ≥ $50, amber ≥ $30). 6.5M shares (= baseline EV $19.2M × 17 ÷ $50)
    puts a typical $280M EV at ≈ $43 and a strong $891M at ≈ $137."""
    from config import TV_SHARES_OUTSTANDING
    assert TV_SHARES_OUTSTANDING == 6_500_000
    typical = calculate_equity_bridge(enterprise_value=280_000_000, net_debt=0.0,
                                      book_equity=100_000_000, total_revenue=80_000_000)
    strong = calculate_equity_bridge(enterprise_value=891_000_000, net_debt=0.0,
                                     book_equity=200_000_000, total_revenue=80_000_000)
    assert 30 <= typical["price_per_share"] < 50, typical["price_per_share"]
    assert strong["price_per_share"] >= 50, strong["price_per_share"]
    assert typical["share_price_floored"] is False

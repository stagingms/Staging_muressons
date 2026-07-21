"""
W-D determinism spot-check — situation_room.assemble_bulletin_text.
Pure function: same cohort state => same script; correct mover selection,
crisis vs quiet branch, rival line gating, and a broadcast-length word budget.
"""
from situation_room import assemble_bulletin_text


def team(name, ebitda=20e6, prev=None, flags=None, comp=0.0):
    return {"name": name, "ebitda": ebitda, "prev_ebitda": prev, "flags": flags or [], "competitor_ebitda": comp}


class TestBulletinAssembly:
    def test_deterministic(self):
        teams = [team("Alpha", 22e6, 20e6, ["greenwashing_scandal"], 21e6), team("Beta", 18e6, 19e6)]
        assert assemble_bulletin_text(teams, 4) == assemble_bulletin_text(teams, 4)

    def test_round_number_in_intro(self):
        assert "round 7" in assemble_bulletin_text([team("Alpha")], 7)

    def test_biggest_mover_wins(self):
        teams = [team("Alpha", 22e6, 21e6), team("Beta", 25e6, 20e6)]
        text = assemble_bulletin_text(teams, 3)
        assert "Beta leads the tape" in text and "climbing" in text

    def test_negative_mover_slides(self):
        text = assemble_bulletin_text([team("Alpha", 18e6, 20e6)], 3)
        assert "sliding" in text and "$2.0 million" in text

    def test_no_history_falls_back_to_top_of_board(self):
        text = assemble_bulletin_text([team("Alpha", 22e6), team("Beta", 25e6)], 1)
        assert "Beta tops the board" in text

    def test_crisis_branch_and_count(self):
        teams = [team("Alpha", flags=["cyclone_warning"]), team("Beta", flags=["black_swan_r6"])]
        text = assemble_bulletin_text(teams, 5)
        assert "risk desk: Alpha is managing a cyclone warning" in text
        assert "one of 2 live alerts" in text

    def test_quiet_risk_desk(self):
        text = assemble_bulletin_text([team("Alpha", flags=["esg_reporting"])], 2)
        assert "risk desk is quiet" in text

    def test_rival_line_gated_on_competitor_data(self):
        assert "Nordhaven" in assemble_bulletin_text([team("Alpha", comp=21e6)], 2)
        assert "Nordhaven" not in assemble_bulletin_text([team("Alpha", comp=0)], 2)

    def test_broadcast_word_budget(self):
        teams = [team(f"Team {i}", 20e6 + i, 19e6, ["strike_occurred"], 21e6) for i in range(8)]
        words = len(assemble_bulletin_text(teams, 9).split())
        assert words <= 90, f"bulletin too long for ~15s: {words} words"

"""
P6 regression -- the admin break-glass secret (MASTER_PASSWORD) and the player
master-unlock secret (PLAYER_MASTER_PASSWORD) are SEPARATE realms, so a leak of
one cannot span the other.

Contract:
  * The admin MASTER_PASSWORD verifies for the admin realm but NEVER unlocks a
    player account.
  * Player master-unlock is disabled unless PLAYER_MASTER_PASSWORD is set, and
    when set it accepts ONLY that (distinct) secret.
"""

import master_credentials as mc
from config import MASTER_PASSWORD


def test_admin_master_never_unlocks_players(monkeypatch):
    # Default posture: player master-unlock disabled.
    monkeypatch.setattr(mc, "PLAYER_MASTER_PASSWORD", "")
    assert mc.verify_master_password(MASTER_PASSWORD) is True, "admin realm must still work"
    assert mc.verify_player_master_password(MASTER_PASSWORD) is False, \
        "admin secret must NOT unlock a player (P6)"
    assert mc.verify_player_master_password("anything") is False, \
        "player unlock disabled when PLAYER_MASTER_PASSWORD unset"


def test_player_unlock_uses_its_own_secret(monkeypatch):
    monkeypatch.setattr(mc, "PLAYER_MASTER_PASSWORD", "player-only-xyz")
    assert mc.verify_player_master_password("player-only-xyz") is True
    assert mc.verify_player_master_password(MASTER_PASSWORD) is False, \
        "the admin secret must never unlock players even when player-unlock is enabled"
    assert mc.verify_player_master_password("") is False

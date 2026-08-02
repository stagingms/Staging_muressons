"""Default initial credentials — the single source of truth.

POLICY (set 2026-08-01, by request)
-----------------------------------
Every account is created with a DETERMINISTIC initial password derived from
its own id, and is forced to replace it on first login:

    player       MUR-XYZ   ->  "MUR-XYZ@123"
    facilitator  FAC-007   ->  "FAC-007@321"

The facilitator distributes these verbally/on a roster ("your password is your
ID followed by @123"), the account logs in once, and must_change_password
forces a personal password immediately — so the predictable value is valid
only for the first login window, exactly like a mailed activation code.

WHY DETERMINISTIC RATHER THAN RANDOM
------------------------------------
The previous scheme minted a random 12-char password per account and surfaced
it once in the creation response. In a classroom that meant the facilitator
had to copy 20 distinct strings off one screen and read each to the right
student — the operational failure that produced "password not working" over
and over. A rule the whole room already knows ("ID@123") removes that step.
The security trade-off is bounded: the value only works until first login, and
must_change_password (enforced server- and client-side) closes that window.

WHY ONE MODULE
--------------
There are ~10 creation and reset sites across admin_router. Before this, each
called _generate_temp_password(); a copy of the rule at every site is how
"players get @123 but the bulk uploader still uses random" happens silently.
Every site now calls make_player_credentials / make_facilitator_credentials
here, and a tripwire test bans the id-derivation literals anywhere else.

The plaintext is RETURNED (never stored): only the bcrypt hash is persisted,
and callers surface the plaintext once for distribution. must_change_password
is the caller's responsibility to set True alongside — enforced by the same
tripwire, since a deterministic password without the forced change would be a
standing weak credential.
"""

from __future__ import annotations

from password_hashing import hash_password

# The suffixes are the policy. They live here and nowhere else; the tripwire
# test asserts no other module hard-codes '@123' / '@321' against an id.
_PLAYER_SUFFIX = "@123"
_FACILITATOR_SUFFIX = "@321"


def default_player_password(player_id: str) -> str:
    """The initial password for a player id, e.g. 'MUR-014' -> 'MUR-014@123'.

    The id is used verbatim (same case as stored/displayed) so the rule the
    student is told — "your ID then @123" — matches byte-for-byte. Callers
    pass the FINAL assigned id, never a placeholder."""
    return f"{player_id}{_PLAYER_SUFFIX}"


def default_facilitator_password(facilitator_id: str) -> str:
    """The initial password for a facilitator id, e.g. 'FAC-007' -> 'FAC-007@321'."""
    return f"{facilitator_id}{_FACILITATOR_SUFFIX}"


def make_player_credentials(player_id: str) -> tuple[str, str]:
    """(plaintext, bcrypt_hash) for a new/reset PLAYER.

    The password depends on the id, so the id must already be assigned — this
    is called AFTER the MUR-NNN allocation, inside the same critical section,
    which is why the id is deterministic sequential rather than random."""
    plaintext = default_player_password(player_id)
    return plaintext, hash_password(plaintext)


def make_facilitator_credentials(facilitator_id: str) -> tuple[str, str]:
    """(plaintext, bcrypt_hash) for a new/reset FACILITATOR."""
    plaintext = default_facilitator_password(facilitator_id)
    return plaintext, hash_password(plaintext)

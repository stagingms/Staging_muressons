"""FlagSet — one type, two constructors, and a read that can be observed.

The read probe exists for Phase 3: a reachability test needs to know not just
that a consumer referenced a flag, but that a value reached it. A textual sweep
cannot answer that (tests/test_flag_sweep.py defines "read" as a quoted
occurrence, which is why supply_chain_disruption_risk passes it while its
consumer can never fire). An instrumented read can.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

from . import registry as _registry


class UnknownFlag(KeyError):
    """A flag name that no configuration declares.

    Raised only in strict mode. It is how a guessed or misspelled key dies at
    the first read instead of returning False forever — the failure mode that
    produced systemic_risk_engine.py:79, where the author wrote a fallback for
    a second storage shape and guessed the key name wrong.
    """


def _collect(raw: Mapping[str, Any]) -> frozenset[str]:
    """The canonical reading. Delegates to flag_utils.collect_all_flags so there
    is exactly one implementation, not two that can drift."""
    from flag_utils import collect_all_flags
    return frozenset(collect_all_flags(dict(raw or {})))


def _raw_truthy(raw: Mapping[str, Any]) -> frozenset[str]:
    """Today's broken reading: top-level truthy keys only. Flags held inside the
    rN_flags lists are invisible, exactly as they are to a `.get()` on the raw
    dict."""
    return frozenset(k for k, v in (raw or {}).items() if isinstance(k, str) and v)


@dataclass(frozen=True)
class FlagSet:
    _names: frozenset[str]
    _raw: Mapping[str, Any] = field(default_factory=dict)
    _strict: bool = False
    _legacy: bool = False
    _probe: Callable[[str, bool], None] | None = None

    # ── construction ───────────────────────────────────────────────────────
    @classmethod
    def from_state(cls, global_state: Mapping[str, Any] | None,
                   *, strict: bool = False, probe=None) -> "FlagSet":
        raw = (global_state or {}).get("active_event_flags") or {}
        return cls(_collect(raw), raw, strict, False, probe)

    @classmethod
    def from_flags(cls, raw: Mapping[str, Any] | None,
                   *, strict: bool = False, probe=None) -> "FlagSet":
        raw = raw or {}
        return cls(_collect(raw), raw, strict, False, probe)

    @classmethod
    def legacy_raw(cls, raw: Mapping[str, Any] | None,
                   *, strict: bool = False, probe=None) -> "FlagSet":
        """Reproduce raw-dict semantics bit-for-bit. Every call site is a
        known-wrong reader awaiting Phase 4 — see the package docstring."""
        raw = raw or {}
        return cls(_raw_truthy(raw), raw, strict, True, probe)

    # ── reading ────────────────────────────────────────────────────────────
    def has(self, name: str) -> bool:
        if self._strict and _registry.get(name) is None:
            raise UnknownFlag(
                f"{name!r} is read but declared by no configuration. Either it is a "
                f"typo, or it needs an entry in flags/registry.py."
            )
        hit = name in self._names
        if self._probe is not None:
            self._probe(name, hit)
        return hit

    def value(self, name: str, default: Any = None) -> Any:
        """For the numeric carriers — brsr_net_positive_dividend is a float, not
        a boolean, and collect_all_flags deliberately drops it."""
        v = (self._raw or {}).get(name, default)
        if self._probe is not None:
            self._probe(name, bool(v))
        return v

    def __contains__(self, name: str) -> bool:
        return self.has(name)

    def __len__(self) -> int:
        return len(self._names)

    def __iter__(self):
        return iter(sorted(self._names))

    @property
    def names(self) -> frozenset[str]:
        return self._names

    @property
    def is_legacy(self) -> bool:
        return self._legacy

    # ── interop, while the tree is mid-migration ───────────────────────────
    def as_mr_dict(self) -> dict:
        """Exactly what flag_utils.mr_flags_from produces, so this is a drop-in
        for the calculate_mr boundary without changing its signature yet."""
        out = {n: True for n in self._names}
        out.pop("brsr_net_positive_dividend", None)
        div = (self._raw or {}).get("brsr_net_positive_dividend")
        if isinstance(div, (int, float)) and not isinstance(div, bool) and div:
            out["brsr_net_positive_dividend"] = div
        return out

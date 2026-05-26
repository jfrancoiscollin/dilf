"""Generate canonical Scan-citation blocks for manuel_debutant.md.

Reads ``docs/pre_process_corpus/scan/scan_analysis_debutant.json`` and
emits Markdown fragments that follow the §0 "zéro invention" pattern
exemplified by chapter 7 of the manual: every tactical verdict in the
narrative must be backed by an explicit Scan citation (PV first move,
eval, search depth, divergence flag).

Two output modes:

    python3 scripts/scan_citations.py block BEG_CH03_001
        → individual citation block (for "showcase" fixtures detailed
          in their own sub-section, like §7.1)

    python3 scripts/scan_citations.py table BEG_CH03_001 BEG_CH03_003 ...
        → Markdown table row per fixture (for catalog sub-sections like
          §7.3 — multiple fixtures grouped under one mechanism)

A few normalization rules applied to PV moves:

  - Captures use ``×`` (the manual convention) instead of ``x``.
  - Eval values near +99 are flagged with a note about the Scan
    "forced gain" convention, since the punch list flagged §7.3 as
    misleading on this point.

Importable as a module: :func:`citation_block`, :func:`table_row`,
:func:`load_index`.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

_REPO = Path(__file__).resolve().parent.parent
DEFAULT_INDEX = _REPO / "docs/pre_process_corpus/scan/scan_analysis_debutant.json"

# Eval threshold above which Scan signals "forced gain / mate" rather
# than a normal positional advantage. Per scan_analysis notes, values
# at +90 and above are convention markers, not pawn-unit advantages.
FORCED_GAIN_THRESHOLD = 90.0


@dataclass(frozen=True)
class ScanEntry:
    """One fixture's Scan analysis, as stored in the JSON index."""

    fixture_id: str
    best_move: str
    eval_after_pv: float
    scan_depth: int
    verified: bool
    winning_for: str          # "white" | "black" | "draw"
    pv: tuple[str, ...]
    notes: str

    @property
    def has_divergence(self) -> bool:
        return "DIVERGENCE" in self.notes

    @property
    def divergence_note(self) -> Optional[str]:
        """Return the human-readable divergence summary if present."""
        if not self.has_divergence:
            return None
        # Notes have shape "DIVERGENCE: published_notation starts with
        # 'X', Scan PV starts with 'Y'. Flag in A_VERIFIER_MOTEUR.md. ..."
        first = self.notes.split(".")[0]
        return first.removeprefix("DIVERGENCE: ").strip()


def load_index(path: Path = DEFAULT_INDEX) -> dict[str, ScanEntry]:
    raw = json.loads(path.read_text())
    out: dict[str, ScanEntry] = {}
    for fid, e in raw.items():
        out[fid] = ScanEntry(
            fixture_id=fid,
            best_move=e["best_move"],
            eval_after_pv=float(e["eval_after_pv"]),
            scan_depth=int(e["scan_depth"]),
            verified=bool(e["verified"]),
            winning_for=e["winning_for"],
            pv=tuple(e["pv"]),
            notes=e.get("notes", ""),
        )
    return out


# ── PV rendering ──────────────────────────────────────────────────────


def _pretty_pv(pv: Iterable[str], n: int = 5) -> str:
    """Format the first ``n`` PV plies for inline display.

    Captures (``x``) are rewritten with ``×`` to match the manual's
    typographic convention; quiet moves (``-``) are kept as-is.
    """
    plies = list(pv)[:n]
    out: list[str] = []
    for ply in plies:
        out.append(ply.replace("x", "×"))
    return " ".join(out)


def _eval_phrase(entry: ScanEntry) -> str:
    """Translate the numeric eval into a short human phrase."""
    if abs(entry.eval_after_pv) >= FORCED_GAIN_THRESHOLD:
        side = {"white": "blancs", "black": "noirs", "draw": "égalité"}.get(
            entry.winning_for, entry.winning_for
        )
        return f"éval {entry.eval_after_pv:+.2f} — Scan signale gain forcé pour les {side}"
    side = {"white": "blancs gagnants", "black": "noirs gagnants", "draw": "égalité"}.get(
        entry.winning_for, entry.winning_for
    )
    return f"éval {entry.eval_after_pv:+.2f}, {side}"


# ── Public formatters ────────────────────────────────────────────────


def citation_block(entry: ScanEntry, pv_plies: int = 5) -> str:
    """Return a multi-line Markdown citation block for one fixture.

    Pattern mirrors §7.1 / §7.2 of the current manual: a bold header
    line, an indented PV, and (when applicable) a divergence flag.
    """
    header = f"**PV Scan** (profondeur {entry.scan_depth}, {_eval_phrase(entry)}) :"
    pv_line = f"> `{_pretty_pv(entry.pv, pv_plies)} …`"
    parts = [header, "", pv_line]
    if entry.has_divergence:
        note = entry.divergence_note or "Voir notes JSON"
        parts.extend(
            ["", f"> **Divergence flaggée par Scan** — {note}. Suivre le PV Scan ci-dessus."]
        )
    return "\n".join(parts)


def table_header() -> str:
    return (
        "| Fixture | Premier coup PV | Éval | Profondeur | Divergence |\n"
        "|---------|-----------------|------|-----------|------------|"
    )


def table_row(entry: ScanEntry) -> str:
    """Return one row for a catalog-style §7.3 table."""
    first = entry.pv[0].replace("x", "×") if entry.pv else entry.best_move.replace("x", "×")
    eval_cell = f"{entry.eval_after_pv:+.2f}"
    divergence_cell = "🔴" if entry.has_divergence else "—"
    return (
        f"| `{entry.fixture_id}` | `{first}` | {eval_cell} | "
        f"{entry.scan_depth} | {divergence_cell} |"
    )


# ── CLI ──────────────────────────────────────────────────────────────


def _cli(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="mode", required=True)

    p_block = sub.add_parser("block", help="Per-fixture multi-line citation block.")
    p_block.add_argument("fixture_id")
    p_block.add_argument("--plies", type=int, default=5)

    p_table = sub.add_parser("table", help="Markdown table for a list of fixtures.")
    p_table.add_argument("fixture_ids", nargs="+")
    p_table.add_argument("--no-header", action="store_true")

    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX)

    args = parser.parse_args(list(argv) if argv is not None else None)
    index = load_index(args.index)

    if args.mode == "block":
        if args.fixture_id not in index:
            print(f"Unknown fixture: {args.fixture_id}", file=sys.stderr)
            return 2
        print(citation_block(index[args.fixture_id], pv_plies=args.plies))
    else:  # table
        unknown = [f for f in args.fixture_ids if f not in index]
        if unknown:
            print(f"Unknown fixtures: {unknown}", file=sys.stderr)
            return 2
        if not args.no_header:
            print(table_header())
        for fid in args.fixture_ids:
            print(table_row(index[fid]))
    return 0


if __name__ == "__main__":
    sys.exit(_cli())

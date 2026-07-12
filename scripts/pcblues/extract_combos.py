"""Extract engine-validated combinations from a PC Blues volume (A2 artefact).

Per page: detect + classify diagram boards (pixel pipeline), tokenize the
text layer into candidate move runs, then anchor-by-replay every (board,
run) pair on the page. A pair that replays fully with at least one capture
becomes one line of ``pcblues_combos.jsonl`` (``verified: true`` — the
replay IS the verification). Runs that anchor on no board of their page go
to the quarantine file with the best failure diagnosis (protocole §4.11 /
coquilles §4.13 downstream).

Usage (repo root)::

    python3 -m scripts.pcblues.extract_combos \
        --pdf docs/corpus/pcblues/15.pdf --deel 15 --event "BK België" \
        --out data/exports/pcblues --cache .cache/pcblues/15
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field as dc_field
from pathlib import Path

from pedagogy.game import GameState

from .boards import DetectedBoard, boards_of_page
from .notation import SequenceRun, extract_runs
from .replay import (
    ReplayResult,
    anchor_run,
    anchor_run_with_repair,
    fen_of,
    notation_of,
    replay_tokens,
    themes_of,
)

LICENSE_NOTE = (
    "PC Blues © Piens Christiaan — attribution obligatoire en reprise "
    "publique, pas de modification. Usage interne entraînement/QA : OK."
)

#: "Verpoest H. - Deelen  1957" / "Demesmaecker - Verpoest H. uit 1959."
_PLAYERS_RE = re.compile(
    r"([A-ZÀ-Þ][\w'.]+(?:\s[A-ZÀ-Þ]\w*\.?)?)\s*-\s*"
    r"([A-ZÀ-Þ][\w'.]+(?:\s[A-ZÀ-Þ]\w*\.?)?)"
)
_YEAR_RE = re.compile(r"\b(19\d{2}|20\d{2})\b")

#: Minimum plies for anchor-by-replay to be trusted as a pairing criterion.
MIN_PLIES = 3


def page_text(pdf: Path, page: int) -> str:
    return subprocess.check_output(
        ["pdftotext", "-layout", "-f", str(page), "-l", str(page), str(pdf), "-"],
        text=True,
    )


def board_to_state(board: DetectedBoard) -> GameState:
    """Board pixels -> GameState.

    The pixel classifier cannot tell a king from a man (stacked checkers
    sample identically), but a man standing on its own promotion row is
    impossible (règle §4.4) — such pieces are necessarily kings and are
    promoted here. Kings elsewhere on the board stay men and fail replay
    into quarantine rather than guessing.
    """
    white = set(board.white_men)
    black = set(board.black_men)
    white_kings = {sq for sq in white if 1 <= sq <= 5}
    black_kings = {sq for sq in black if 46 <= sq <= 50}
    return GameState(
        white_men=frozenset(white - white_kings),
        white_kings=frozenset(white_kings),
        black_men=frozenset(black - black_kings),
        black_kings=frozenset(black_kings),
        turn="white",
    )


def board_captions(text: str, n_boards: int) -> list[dict]:
    """Players/year captions of a diagram-grid page, in reading order.

    Grid pages ("Opgaven") caption each board with "Wollaert - Lemmens
    37-32 ?" above and "79   BK 2000" below. When the number of "A - B"
    matches equals the number of boards, they pair up in reading order;
    otherwise no metadata is claimed (jamais de pairage deviné).
    """
    pairs = list(_PLAYERS_RE.finditer(text))
    if n_boards == 0 or len(pairs) != n_boards:
        return []
    years = _YEAR_RE.findall(text)
    return [
        {
            "players": f"{m.group(1).strip()} - {m.group(2).strip()}",
            "year": int(years[i]) if i < len(years) else None,
        }
        for i, m in enumerate(pairs)
    ]


def find_context(text: str, first_line: int) -> tuple[str | None, int | None]:
    """Players + year from the prose lines above a run (same page)."""
    lines = text.splitlines()
    for ln in range(first_line - 1, max(first_line - 15, -1), -1):
        line = lines[ln]
        m = _PLAYERS_RE.search(line)
        if m:
            year = _YEAR_RE.search(line)
            if year is None and ln + 1 < len(lines):
                year = _YEAR_RE.search(lines[ln + 1])
            players = f"{m.group(1).strip()} - {m.group(2).strip()}"
            return players, int(year.group(0)) if year else None
    return None, None


def combo_id(deel: int, page: int, board_idx: int, run: SequenceRun) -> str:
    seq = ",".join(f"{t.frm}{'x' if t.capture else '-'}{t.to}" for t in run.tokens)
    digest = hashlib.sha1(seq.encode()).hexdigest()[:8]
    return f"pcblues-d{deel:02d}-p{page:03d}-b{board_idx}-{digest}"


def position_hash(fen: str) -> str:
    return hashlib.sha1(fen.encode()).hexdigest()[:16]


@dataclass
class PageCarry:
    """Anchor context carried across pages.

    Fragments often flow past a page break (diagram on page N, variations
    on N+1), and the exercise sections ("Opgaven" grids -> "Oplossingen"
    lists) put the anchor diagrams many pages before their solutions. So:
    ``boards`` holds the previous page only (cheap, tried early), ``pool``
    accumulates every board of the volume so far (tried last), ``states``
    holds continuation snapshots of the previous page, and ``meta`` maps
    ``(page, index)`` -> players/year parsed next to each board.
    """

    boards: list[DetectedBoard] = dc_field(default_factory=list)
    states: list[GameState] = dc_field(default_factory=list)
    pool: list[tuple[int, DetectedBoard]] = dc_field(default_factory=list)
    meta: dict[tuple[int, int], dict] = dc_field(default_factory=dict)


def _record(
    res, run: SequenceRun, deel: int, page: int, board_idx: int,
    event: str | None, text: str, anchor: str,
) -> dict:
    players, year = find_context(text, run.first_line)
    final_capture = None
    for ply in reversed(res.plies):
        if ply.resolved.move.is_capture:
            final_capture = "x".join(str(s) for s in ply.resolved.move.path)
            break
    fen_start = fen_of(res.plies[0].state_before)
    graded = [
        {
            "fen": fen_of(p.state_before),
            "move": notation_of(p.resolved.move),
            "grade": p.token.grade,
        }
        for p in res.plies
        if p.token.grade in {"!!", "!", "!?", "?!", "?", "??"}
    ]
    return {
        "id": combo_id(deel, page, board_idx, run),
        "fen_start": fen_start,
        "position_hash": position_hash(fen_start),
        "seq_moves": [notation_of(p.resolved.move) for p in res.plies],
        "seq_published": [
            f"{t.frm}{'x' if t.capture else '-'}{t.to}" for t in run.tokens
        ],
        "final_rafle": final_capture,
        "themes": themes_of(res.plies),
        "deel": deel,
        "page": page,
        "event": event,
        "players": players,
        "year": year,
        "variation": run.variation,
        "anchor": anchor,
        "result": run.result,
        "graded_moves": graded,
        "verified": True,
    }


def extract_page(
    pdf: Path,
    page: int,
    deel: int,
    event: str | None,
    cache: Path,
    carry: PageCarry | None = None,
) -> tuple[list[dict], list[dict], PageCarry]:
    """Return (combos, quarantine, carry-for-next-page) for one page."""
    carry = carry or PageCarry()
    text = page_text(pdf, page)
    runs = extract_runs(text)
    # Boards are detected even without runs on the page: the "Opgaven"
    # grids feed the volume pool that anchors solutions pages later on.
    boards = boards_of_page(pdf, page, cache)
    prev_page_pool = [(pg, b) for pg, b in carry.pool if pg == page - 1]
    older_pool = [(pg, b) for pg, b in reversed(carry.pool) if pg < page - 1]

    meta = dict(carry.meta)
    for i, caption in enumerate(board_captions(text, len(boards))):
        meta[(page, i)] = caption

    combos: list[dict] = []
    quarantine: list[dict] = []
    new_states: list[GameState] = []

    for run in runs:
        has_capture = any(t.capture for t in run.tokens)
        best_fail: tuple[ReplayResult, int] | None = None
        anchored_res = None
        anchor_kind = None
        board_idx = -1
        anchored_page = None
        dropped: list = []

        # Short runs ("45. ... 44-50 ?") can't be trusted as *emitted*
        # combos but still contribute anchor states for later runs.
        emittable = len(run.tokens) >= MIN_PLIES

        candidate_boards = (
            [("diagram", page, b) for b in boards]
            + [("diagram_prev_page", pg, b) for pg, b in prev_page_pool]
            + [("diagram_pool", pg, b) for pg, b in older_pool]
        )

        if not emittable:
            # A 1-2 ply run ("45. ... 18-23 ?") is legal from many boards —
            # anchoring on the first match would gamble. Instead it seeds a
            # snapshot from EVERY position it replays from; the next long
            # run validates whichever snapshot was right.
            for _, _, board in candidate_boards[: len(boards) + len(prev_page_pool)]:
                res = anchor_run(board_to_state(board), run)
                if res.ok:
                    new_states.extend(p.state_after for p in res.plies)
            for st in list(reversed(new_states + carry.states))[:60]:
                res = replay_tokens(st, run.tokens, st.turn)
                if res.ok:
                    new_states.extend(p.state_after for p in res.plies)
                    break
            continue

        # 1) exact anchors first: boards of this page, previous page, then
        #    the whole-volume pool (Opgaven grids anchor their Oplossingen
        #    many pages later)…
        for anchor, anchor_page, board in candidate_boards:
            res = anchor_run(board_to_state(board), run)
            if res.ok:
                anchored_res, anchor_kind, board_idx = res, anchor, board.index
                anchored_page = anchor_page
                break
            if best_fail is None or (res.failed_at or 0) > (best_fail[0].failed_at or 0):
                best_fail = (res, board.index)

        # 2) …then intermediate states of already-validated sequences
        #    (variation divergence points), most recent first…
        if anchored_res is None:
            for st in reversed(new_states + carry.states):
                res = replay_tokens(st, run.tokens, st.turn)
                if res.ok:
                    anchored_res, anchor_kind = res, "continuation"
                    break

        # 3) …and only as a last resort, board anchors with inline-token
        #    repair (an exact anchor always beats a repaired one).
        if anchored_res is None:
            for anchor, anchor_page, board in candidate_boards:
                res, run_dropped = anchor_run_with_repair(
                    board_to_state(board), run
                )
                if res.ok and run_dropped:
                    anchored_res, anchor_kind, board_idx = res, anchor, board.index
                    anchored_page = anchor_page
                    dropped = run_dropped
                    break

        if anchored_res is not None:
            new_states.append(anchored_res.plies[0].state_before)
            new_states.extend(p.state_after for p in anchored_res.plies)
            if has_capture and emittable and len(anchored_res.plies) >= MIN_PLIES:
                rec = _record(
                    anchored_res, run, deel, page, board_idx, event, text,
                    anchor_kind,
                )
                rec["anchor_page"] = anchored_page
                # Metadata of the anchor board (Opgaven grid captions)
                # completes what the solution page's prose doesn't repeat.
                board_meta = meta.get((anchored_page, board_idx)) if anchored_page else None
                if board_meta:
                    rec["players"] = rec["players"] or board_meta.get("players")
                    rec["year"] = rec["year"] or board_meta.get("year")
                if dropped:
                    rec["dropped_tokens"] = [
                        f"{t.frm}{'x' if t.capture else '-'}{t.to}" for t in dropped
                    ]
                combos.append(rec)
        elif has_capture and emittable:
            quarantine.append(
                {
                    "id": combo_id(deel, page, -1, run),
                    "deel": deel,
                    "page": page,
                    "tokens": [
                        f"{t.frm}{'x' if t.capture else '-'}{t.to}" for t in run.tokens
                    ],
                    "variation": run.variation,
                    "n_boards_on_page": len(boards),
                    "best_failure": best_fail[0].failure if best_fail else "no board detected",
                    "best_failure_board": best_fail[1] if best_fail else None,
                    "best_failure_ply": best_fail[0].failed_at if best_fail else None,
                }
            )

    next_carry = PageCarry(
        boards=boards,
        states=new_states,
        pool=carry.pool + [(page, b) for b in boards],
        meta=meta,
    )
    return combos, quarantine, next_carry


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--deel", type=int, required=True)
    ap.add_argument("--event", default=None)
    ap.add_argument("--pages", default=None, help="e.g. 5-97 (default: all)")
    ap.add_argument("--out", default="data/exports/pcblues")
    ap.add_argument("--cache", default=None)
    ap.add_argument("--progress-every", type=int, default=10)
    args = ap.parse_args(argv)

    pdf = Path(args.pdf)
    cache = Path(args.cache or f".cache/pcblues/{args.deel}")
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    n_pages = int(
        subprocess.check_output(["pdfinfo", str(pdf)], text=True)
        .split("Pages:")[1]
        .split()[0]
    )
    if args.pages:
        lo, hi = args.pages.split("-")
        pages = range(int(lo), min(int(hi), n_pages) + 1)
    else:
        pages = range(1, n_pages + 1)

    combos_path = out_dir / f"combos_deel{args.deel:02d}.jsonl"
    quarantine_path = out_dir / f"quarantine_deel{args.deel:02d}.jsonl"
    all_combos: list[dict] = []
    all_quarantine: list[dict] = []

    carry = None
    for i, page in enumerate(pages):
        combos, quarantine, carry = extract_page(
            pdf, page, args.deel, args.event, cache, carry
        )
        all_combos.extend(combos)
        all_quarantine.extend(quarantine)
        if (i + 1) % args.progress_every == 0:
            print(
                f"[deel {args.deel}] page {page}/{pages[-1]} : "
                f"{len(all_combos)} combos vérifiées, {len(all_quarantine)} en quarantaine",
                flush=True,
            )

    with combos_path.open("w", encoding="utf-8") as fh:
        for rec in all_combos:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    with quarantine_path.open("w", encoding="utf-8") as fh:
        for rec in all_quarantine:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    total = len(all_combos) + len(all_quarantine)
    stats = {
        "deel": args.deel,
        "pdf": pdf.name,
        "pages_scanned": len(list(pages)),
        "combos_verified": len(all_combos),
        "quarantined": len(all_quarantine),
        "quarantine_rate": round(len(all_quarantine) / total, 4) if total else None,
        "license": LICENSE_NOTE,
    }
    stats_path = out_dir / f"stats_deel{args.deel:02d}.json"
    stats_path.write_text(json.dumps(stats, indent=2, ensure_ascii=False))
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())

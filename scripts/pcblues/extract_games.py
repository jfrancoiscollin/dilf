"""Extract full annotated games from a PC Blues volume (A1 PDN + A3 prefs).

Layout of the "Grandmasters for sale" volumes (36, 42) and friends: a game
header line ("Herman Hoogland – Isidore Weiss WK 1911 0-2"), then continuous
notation ("1.33-28 18-23 2.31-27 …") interleaved with Dutch prose, bracketed
variations ("[ 21.38-32? 14-20 … ]", possibly multi-line) and bullet lines.

Pipeline per game block:

1. strip bracketed variations and bullet lines (they belong to analysis,
   not to the played game),
2. tokenize what remains and assemble the mainline with a move-number state
   machine (numbered white move N, optional unnumbered black reply, "N…"
   resumptions after prose) — stray analysis moves don't carry the expected
   number and are skipped,
3. replay the mainline from the initial position under full FMJD rules.
   A game that replays end-to-end becomes a PDN entry (A1) and its graded
   moves ("!", "?", …) become A3 records with the exact FEN before the
   move. **A game that does not replay is quarantined whole** — pas de
   troncature silencieuse (règle du mémo).

Games whose notation starts past move 1 (diagram-anchored fragments with a
header) are out of A1 scope and are counted separately (they remain
available to the A2/fragments pipeline).

Usage::

    python3 -m scripts.pcblues.extract_games \
        --pdf docs/corpus/pcblues/36.pdf --deel 36 \
        --annotator "Gerrit Boom / Christiaan Piens" \
        --out data/exports/pcblues
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

from pedagogy.game import initial_state

from .notation import MoveToken, parse_line_tokens
from .replay import fen_of, notation_of, replay_tokens

LICENSE_NOTE = (
    "PC Blues © Piens Christiaan — attribution obligatoire en reprise "
    "publique, pas de modification. Usage interne entraînement/QA : OK."
)

#: Header: players (en-dash or spaced hyphen), free event text, result.
_HEADER_RE = re.compile(
    r"^\s*(?P<white>[A-ZÀ-Þ][\w'.,]*(?:[ .][A-ZÀ-Þ]?[\w'.,]*){0,3})\s*[–—-]\s+"
    r"(?P<rest>[A-ZÀ-Þ].*?)\s*(?P<result>2-0|1-1|0-2)\s*$"
)
_YEAR_RE = re.compile(r"\b(18\d{2}|19\d{2}|20\d{2})\b")

#: First token that starts the event part of a header's "black + event" blob.
_EVENT_START_RE = re.compile(
    r"\b(WK|BK|EK|NK|Cup|Open|Kampioenschap|Toernooi|NLD|chT|Klubkompetitie|"
    r"Ereklasse|Sovjet|18\d{2}|19\d{2}|20\d{2})\b"
)


def _split_black_event(rest: str) -> tuple[str, str | None]:
    """"Isidore Weiss WK 1911" -> ("Isidore Weiss", "WK 1911")."""
    m = _EVENT_START_RE.search(rest)
    if m and m.start() > 0:
        return rest[: m.start()].strip(" ,"), rest[m.start() :].strip(" ,") or None
    return rest.strip(" ,"), None

GRADES = {"!!", "!", "!?", "?!", "?", "??"}


@dataclass
class GameBlock:
    white: str
    black: str
    event: str
    year: int | None
    result: str
    page: int
    lines: list[str] = field(default_factory=list)


def _strip_brackets(text: str) -> str:
    """Blank out [ … ] variation segments (multi-line), keep line structure."""
    out = []
    depth = 0
    for ch in text:
        if ch == "[":
            depth += 1
            out.append(" ")
        elif ch == "]":
            depth = max(0, depth - 1)
            out.append(" ")
        elif depth > 0 and ch != "\n":
            out.append(" ")
        else:
            out.append(ch)
    return "".join(out)


def _volume_blocks(pdf: Path, n_pages: int) -> list[GameBlock]:
    """Split the whole volume text into header-delimited game blocks."""
    blocks: list[GameBlock] = []
    current: GameBlock | None = None
    for page in range(1, n_pages + 1):
        text = subprocess.check_output(
            ["pdftotext", "-layout", "-f", str(page), "-l", str(page), str(pdf), "-"],
            text=True,
        )
        for line in text.splitlines():
            m = _HEADER_RE.match(line.strip())
            # A header line must not itself contain moves ("1.33-28 … 0-2"
            # would match players otherwise) — but a date "20-12-1974" is
            # not a move.
            dateless = re.sub(r"\b\d{1,2}-\d{2}-\d{4}\b", " ", line)
            if m and not parse_line_tokens(dateless):
                black, event = _split_black_event(" ".join(m.group("rest").split()))
                year = _YEAR_RE.search(event or "")
                current = GameBlock(
                    white=m.group("white").strip(),
                    black=black,
                    event=event,
                    year=int(year.group(0)) if year else None,
                    result=m.group("result"),
                    page=page,
                )
                blocks.append(current)
            elif current is not None:
                current.lines.append(line)
    return blocks


def first_move_number(block_text: str) -> int | None:
    """Number of the first numbered token of the block (1 = full game)."""
    clean = _strip_brackets(block_text)
    for line_no, line in enumerate(clean.splitlines()):
        for group in parse_line_tokens(line, line_no):
            for tok in group:
                if tok.number is not None:
                    return tok.number
    return None


def assemble_and_replay(block_text: str):
    """Assemble the played mainline, with replay legality as the arbiter.

    Walk the token stream with (expected move number, side, GameState). A
    token is a candidate when its numbering matches the expectation
    (numbered ``N.`` for white / ``N…`` resumption for black / unnumbered
    while awaiting black); a candidate is accepted iff it is **legal** in
    the current position — the played move precedes its commentary in PC
    Blues prose, so first-legal-match is the played move. Analysis moves
    fail either the numbering or the legality gate (bracketed variations
    are stripped besides, when the text layer kept the brackets).

    Returns ``(plies, reason)`` — ``reason`` is None on success, else the
    quarantine cause. Truncation guard: after the last accepted move, a
    numbered token ``expected.`` still ahead means the game continued but
    replay lost it -> the game is quarantined whole, jamais tronquée.
    """
    from pedagogy.game import GameState

    from .rules import AmbiguousMoveError, IllegalMoveError, apply_move, match_token

    from .notation import _RESULT_RE

    state = initial_state()
    plies: list = []
    expected = 1
    side_black = False
    last_accept_line = -1
    #: Distinct move numbers >= expected seen since the last acceptance. One
    #: stray number is post-game analysis ("Na 39.42-37 volgt…"); two or
    #: more mean the game continued and replay lost the thread — unless the
    #: result marker sits right after the last accepted move (game over,
    #: the strays are post-mortem analysis).
    stray_numbers: set[int] = set()

    clean = _strip_brackets(block_text)
    prev_tok = None  # last token processed, across groups and lines
    for line_no, line in enumerate(clean.splitlines()):
        if line.lstrip().startswith(("•", "=>")):
            continue
        for group_idx, group in enumerate(parse_line_tokens(line, line_no)):
            for tok_idx, tok in enumerate(group):
                last_accepted = plies[-1].token if plies else None
                if tok.number is not None:
                    # White move "N." (no ellipsis) or black resumption "N…".
                    candidate = tok.number == expected and bool(tok.ellipsis) == side_black
                else:
                    # Unnumbered black reply: legality alone is not enough
                    # ("kan (moet) 19-23" is analysis and often legal) — it
                    # must directly follow the accepted white move: same
                    # prose-free group, or first token of the next line.
                    adjacent = (
                        tok_idx > 0 and group[tok_idx - 1] is last_accepted
                    ) or (
                        tok_idx == 0 and group_idx == 0 and prev_tok is last_accepted
                    )
                    candidate = side_black and adjacent
                prev_tok = tok
                if tok.number is not None and tok.number >= expected:
                    stray_numbers.add(tok.number)
                if not candidate:
                    continue
                try:
                    resolved = match_token(state, tok.frm, tok.to, tok.capture)
                except (IllegalMoveError, AmbiguousMoveError, ValueError):
                    continue
                after = apply_move(state, resolved)
                plies.append(
                    ReplayedPlyLite(tok, resolved, state, after)
                )
                state = after
                stray_numbers.clear()
                last_accept_line = line_no
                if side_black:
                    expected += 1
                    side_black = False
                else:
                    side_black = True

    lines = clean.splitlines()
    result_closes_game = any(
        _RESULT_RE.search(l)
        for l in lines[max(last_accept_line, 0) : last_accept_line + 3]
    )
    # Truncation = the game's own next move (`expected`) is among the
    # un-replayable numbers. Strays starting past `expected` are post-game
    # analysis ("42.24-19 of 35-30 … 43.35-30 …" after the game ended).
    if (
        len(stray_numbers) >= 2
        and expected in stray_numbers
        and not result_closes_game
    ):
        return plies, (
            f"truncated at move {expected}: continuation "
            f"{sorted(stray_numbers)[:4]} seen but not replayable"
        )
    return plies, None


@dataclass
class ReplayedPlyLite:
    token: MoveToken
    resolved: object
    state_before: object
    state_after: object


def _pdn_moves(plies) -> str:
    """Render the replayed mainline as PDN movetext (engine notation)."""
    parts: list[str] = []
    num = 1
    for i, ply in enumerate(plies):
        if i % 2 == 0:
            parts.append(f"{num}.")
            num += 1
        parts.append(notation_of(ply.resolved.move))
    return " ".join(parts)


def extract_volume(
    pdf: Path, deel: int, annotator: str | None
) -> tuple[list[dict], list[dict], list[dict], dict]:
    """Return (games, prefs, quarantine, stats) for one volume."""
    n_pages = int(
        subprocess.check_output(["pdfinfo", str(pdf)], text=True)
        .split("Pages:")[1]
        .split()[0]
    )
    blocks = _volume_blocks(pdf, n_pages)

    games: list[dict] = []
    prefs: list[dict] = []
    quarantine: list[dict] = []
    n_fragments = 0

    for block in blocks:
        text = "\n".join(block.lines)
        first_num = first_move_number(text)
        if first_num is None:
            continue  # header without notation underneath
        if first_num != 1:
            n_fragments += 1  # mid-game fragment: A2 pipeline territory
            continue
        plies, reason = assemble_and_replay(text)
        meta = {
            "white": block.white,
            "black": block.black,
            "event": block.event,
            "year": block.year,
            "result": block.result,
            "deel": deel,
            "page": block.page,
        }
        if reason is not None or len(plies) < 6:
            quarantine.append(
                {
                    **meta,
                    "plies_parsed": len(plies),
                    "failure": reason or "too_few_moves",
                }
            )
            continue

        games.append(
            {
                **meta,
                "annotator": annotator,
                "plies": len(plies),
                "pdn_moves": _pdn_moves(plies),
            }
        )
        for ply in plies:
            grade = ply.token.grade
            if grade in GRADES:
                prefs.append(
                    {
                        "fen": fen_of(ply.state_before),
                        "move_played": notation_of(ply.resolved.move),
                        "grade": grade,
                        "annotator": annotator,
                        "deel": deel,
                        "page": block.page,
                        "players": f"{block.white} - {block.black}",
                        "event": block.event,
                        "year": block.year,
                    }
                )

    stats = {
        "deel": deel,
        "pdf": pdf.name,
        "blocks_with_header": len(blocks),
        "games_replayed": len(games),
        "games_quarantined": len(quarantine),
        "midgame_fragments_skipped": n_fragments,
        "prefs_graded": len(prefs),
        "license": LICENSE_NOTE,
    }
    return games, prefs, quarantine, stats


def _pdn_entry(g: dict) -> str:
    tags = [
        ("Event", g["event"] or "?"),
        ("Date", str(g["year"]) if g["year"] else "????"),
        ("White", g["white"]),
        ("Black", g["black"]),
        ("Result", g["result"]),
        ("Annotator", g["annotator"] or "?"),
        ("Deel", str(g["deel"])),
        ("Page", str(g["page"])),
    ]
    head = "\n".join(f'[{k} "{v}"]' for k, v in tags)
    return f"{head}\n\n{g['pdn_moves']} {g['result']}\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--deel", type=int, required=True)
    ap.add_argument("--annotator", default=None)
    ap.add_argument("--out", default="data/exports/pcblues")
    args = ap.parse_args(argv)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    games, prefs, quarantine, stats = extract_volume(
        Path(args.pdf), args.deel, args.annotator
    )

    (out_dir / f"games_deel{args.deel:02d}.pdn").write_text(
        "\n".join(_pdn_entry(g) for g in games), encoding="utf-8"
    )
    with (out_dir / f"prefs_deel{args.deel:02d}.jsonl").open("w", encoding="utf-8") as fh:
        for rec in prefs:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    with (out_dir / f"games_quarantine_deel{args.deel:02d}.jsonl").open(
        "w", encoding="utf-8"
    ) as fh:
        for rec in quarantine:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    (out_dir / f"games_stats_deel{args.deel:02d}.json").write_text(
        json.dumps(stats, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())

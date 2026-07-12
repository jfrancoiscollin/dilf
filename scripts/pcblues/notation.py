"""Tokenizer for PC Blues move text (Dutch layout, pdftotext -layout).

Observed notation in the corpus::

    18. 26-21 16x27  19. 33-28 22x44      numbered white/black pairs
    16. ...  14-19                        ellipsis = black to move first
    37. 45-40 ?! 18-23 ?                  grades attached to the previous move
    46. 30-25 ? 21-26 47. 25x14 19x10     zero-padded squares (05x19, 36x07)
    =>  46. 28-22 ? ...                   variation lines
    2-0 / 1-1 / 0-2 / + / =               results (never move tokens)

Capture tokens carry endpoints only; the actual trajectory is resolved
against the engine (:mod:`scripts.pcblues.rules`).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

#: A square is 1-2 digits, optionally zero-padded ("07"). Move numbers are
#: ``NN.`` — the dot excludes them from square matching.
_MOVE_RE = re.compile(
    r"(?:(?P<num>\d{1,3})\.(?P<ellipsis>\s*\.\.\.)?\s*)?"
    r"(?P<frm>\d{1,2})\s?(?P<sep>[-x])\s?(?P<to>\d{1,2})"
    r"(?!\d|\.\d)"  # not part of a longer number / decimal
    r"\s*(?P<grade>!!|\?\?|!\?|\?!|!|\?)?"
)

#: Results / markers that terminate a sequence run.
_RESULT_RE = re.compile(r"(?<![\dx-])(2-0|1-1|0-2)(?![\dx-])")

#: Lines whose move tokens belong to a side variation, not the mainline.
_VARIATION_PREFIX = ("=>", "->")


@dataclass
class MoveToken:
    """One parsed half-move."""

    frm: int
    to: int
    capture: bool
    number: int | None = None  # move number if the token carried one
    ellipsis: bool = False  # "NN. ..." → black plays this token
    grade: str | None = None  # "!", "?", "!!", "??", "!?", "?!"
    line_no: int = 0  # 0-based line index within the page text


@dataclass
class SequenceRun:
    """A maximal run of consecutive move tokens (candidate replay sequence)."""

    tokens: list[MoveToken] = field(default_factory=list)
    variation: bool = False  # started on a "=>" line
    result: str | None = None  # "2-0" etc. if the run ends on a result
    first_line: int = 0
    last_line: int = 0

    @property
    def black_starts(self) -> bool:
        return bool(self.tokens) and self.tokens[0].ellipsis


def _is_plausible_square(v: int) -> bool:
    return 1 <= v <= 50


#: Letters allowed between two tokens of the same run (grades, move numbers,
#: single-letter variation labels "A"/"B"). More alpha than this = prose ->
#: the run breaks there ("Met 26-31 komt zwart..." embeds an alternative).
_PROSE_GAP_ALPHA = 2


def parse_line_tokens(line: str, line_no: int = 0) -> list[list[MoveToken]]:
    """Extract the move tokens of one text line, split at prose gaps.

    PC Blues mixes analysis and prose on one line ("46. 20-14 ! 27-31   Met
    26-31 komt zwart nog aan een gelijk spel"): the move embedded in prose
    is an *alternative*, not the next ply. Whenever the text between two
    consecutive tokens carries more than :data:`_PROSE_GAP_ALPHA` letters,
    the tokens after the gap start a new group.
    """
    groups: list[list[MoveToken]] = []
    current: list[MoveToken] = []
    # Mask result strings so "2-0" is not read as square 2 -> square 0.
    masked = _RESULT_RE.sub(lambda m: " " * len(m.group(0)), line)
    prev_end = 0
    for m in _MOVE_RE.finditer(masked):
        frm, to = int(m.group("frm")), int(m.group("to"))
        if not (_is_plausible_square(frm) and _is_plausible_square(to)):
            continue
        gap_alpha = sum(c.isalpha() for c in masked[prev_end : m.start()])
        if current and gap_alpha > _PROSE_GAP_ALPHA:
            groups.append(current)
            current = []
        prev_end = m.end()
        current.append(
            MoveToken(
                frm=frm,
                to=to,
                capture=m.group("sep") == "x",
                number=int(m.group("num")) if m.group("num") else None,
                ellipsis=bool(m.group("ellipsis")),
                grade=m.group("grade"),
                line_no=line_no,
            )
        )
    if current:
        groups.append(current)
    return groups


def extract_runs(page_text: str) -> list[SequenceRun]:
    """Split a page's text into candidate move-sequence runs.

    A run accumulates move tokens over consecutive "move-bearing" lines.
    It breaks on: a blank / prose line without tokens, a variation prefix
    (which starts a *new* run flagged ``variation``), or a result marker.
    """
    runs: list[SequenceRun] = []
    current: SequenceRun | None = None

    def numbering_consistent(run: SequenceRun, tokens: list[MoveToken]) -> bool:
        first_num = tokens[0].number
        if first_num is None:
            return True  # wrapped line without a number: extend blindly
        last_nums = [t.number for t in run.tokens if t.number is not None]
        if not last_nums:
            return True
        return first_num in (last_nums[-1], last_nums[-1] + 1)

    for line_no, line in enumerate(page_text.splitlines()):
        stripped = line.strip()
        is_variation = stripped.startswith(_VARIATION_PREFIX)
        groups = parse_line_tokens(line, line_no)
        result = _RESULT_RE.search(line)

        if not groups:
            if current is not None and result:
                current.result = result.group(0)
                current.last_line = line_no
            current = None
            continue

        # Group 0 is the mainline of the line: it extends `current` when the
        # move numbering is consistent. Later groups (past a prose gap) are
        # closed alternatives — standalone runs that never take next-line
        # continuation; `current` stays on the group-0 run.
        mainline: SequenceRun
        if (
            is_variation
            or current is None
            or not numbering_consistent(current, groups[0])
        ):
            mainline = SequenceRun(variation=is_variation, first_line=line_no)
            runs.append(mainline)
        else:
            mainline = current
        mainline.tokens.extend(groups[0])
        mainline.last_line = line_no

        for tokens in groups[1:]:
            alt = SequenceRun(variation=True, first_line=line_no)
            alt.tokens.extend(tokens)
            alt.last_line = line_no
            runs.append(alt)

        current = mainline
        if result:
            current.result = result.group(0)
            current = None

    return [r for r in runs if r.tokens]

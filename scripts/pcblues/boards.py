"""Board detection + square classification for PC Blues page renders.

Reuses the pixel primitives of ``scripts.extract_diagrams`` (proven, no-LLM)
and adds what the PC Blues layout needs on top of the Dubois pipeline:

* pages routinely show **2-3 boards side by side** ("Diagram 6 / 6A / 6B");
  the dilation-based blob detector merges them into one wide blob, so wide
  blobs are split at vertical whitespace valleys before validation,
* boards are slightly smaller than Dubois' (three across a page), so the
  minimum-area gate is lowered,
* captions are Dutch ("Diagram 12A") — pairing with crops happens in
  :mod:`scripts.pcblues.fragments`, by reading order.

Kings (dames) are rendered as stacked checkers whose top face samples like
a man of the same colour, so extraction cannot tell a king from a man.
Sequences whose replay needs a king on a man-classified square fail replay
and land in quarantine — never silently wrong.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from scripts.extract_diagrams import (
    BOARD_ASPECT_RANGE,
    DILATION_ITERATIONS,
    FEN_MARGIN_PX,
    SAMPLE_RADIUS,
    _render_page_png,
    _shrink_to_border,
    _square_number,
)

#: Three boards across an A4 render at 200 dpi -> ~370 px wide each; the
#: Klubkompetitie volumes (37/43/51) go down to ~280 px.
MIN_BOARD_AREA_PCBLUES = 55_000
#: Wide blobs up to ~4 boards are split before rejection.
MAX_SPLIT_PARTS = 4
#: Truly-black threshold: board borders, pieces and text — NOT the coloured
#: page backgrounds (deel 37+ use a blue gradient that sits ~150-220 in
#: grayscale and floods the Dubois-era mask of `< 230`).
BLACK_THRESHOLD = 120


@dataclass(frozen=True)
class DetectedBoard:
    """One board found on a rendered page, with classified squares."""

    page: int  # 1-based PDF page
    index: int  # reading order on the page (0-based)
    bbox: tuple[int, int, int, int]
    white_men: tuple[int, ...]
    black_men: tuple[int, ...]


def _split_wide_blob(
    mask, left: int, top: int, right: int, bottom: int
) -> list[tuple[int, int, int, int]]:
    """Split a wide blob at vertical whitespace valleys of the raw mask."""
    import numpy as np

    w, h = right - left, bottom - top
    parts = round(w / h)
    if parts < 2 or parts > MAX_SPLIT_PARTS:
        return [(left, top, right, bottom)]
    col_density = mask[top:bottom, left:right].sum(axis=0) / max(h, 1)
    boxes: list[tuple[int, int, int, int]] = []
    approx = w / parts
    cursor = 0
    for k in range(parts):
        lo = int(cursor)
        hi = int((k + 1) * approx) if k < parts - 1 else w
        if k < parts - 1:
            # refine the cut to the emptiest column near the nominal boundary
            window = col_density[max(hi - 40, lo + 20) : min(hi + 40, w - 1)]
            if window.size:
                hi = max(hi - 40, lo + 20) + int(np.argmin(window))
        boxes.append((left + lo, top, left + hi, bottom))
        cursor = hi
    return boxes


def _inner_border(arr, bbox: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    """Shrink past a double frame (outer border + white margin + inner border).

    The Klubkompetitie volumes draw their boards inside a decorative outer
    rectangle; sampling from the outer bbox lands half a square off. A
    second `_shrink_to_border` pass, started just inside the outer line,
    finds the inner rectangle when there is one; when the shrink is only
    the border thickness itself (< 2% of the size), the original bbox is
    kept (single-frame volumes like deel 15).
    """
    x1, y1, x2, y2 = bbox
    inset = 4
    if (x2 - x1) <= 4 * inset or (y2 - y1) <= 4 * inset:
        return bbox
    inner = _shrink_to_border(arr, x1 + inset, y1 + inset, x2 - inset, y2 - inset)
    iw, ih = inner[2] - inner[0], inner[3] - inner[1]
    w, h = x2 - x1, y2 - y1
    moved = max(
        inner[0] - (x1 + inset), inner[1] - (y1 + inset),
        (x2 - inset) - inner[2], (y2 - inset) - inner[3],
    )
    if moved > 0.02 * min(w, h) and iw > 0.75 * w and ih > 0.75 * h:
        return inner
    return bbox


def detect_boards(image_path: Path) -> list[tuple[int, int, int, int]]:
    """Bounding boxes of all boards on a page render, reading order."""
    import numpy as np
    from PIL import Image
    from scipy import ndimage

    arr = np.array(Image.open(image_path).convert("L"))
    mask = arr < BLACK_THRESHOLD
    dilated = ndimage.binary_dilation(mask, iterations=DILATION_ITERATIONS)
    labeled, _ = ndimage.label(dilated)
    boards: list[tuple[int, int, int, int]] = []
    for sl in ndimage.find_objects(labeled):
        if sl is None:
            continue
        top, bottom = sl[0].start, sl[0].stop
        left, right = sl[1].start, sl[1].stop
        w, h = right - left, bottom - top
        if w * h < MIN_BOARD_AREA_PCBLUES:
            continue
        candidates = (
            [(left, top, right, bottom)]
            if w / h <= BOARD_ASPECT_RANGE[1]
            else _split_wide_blob(mask, left, top, right, bottom)
        )
        for cl, ct, cr, cb in candidates:
            tight = _shrink_to_border(arr, cl, ct, cr, cb)
            tight = _inner_border(arr, tight)
            tw, th = tight[2] - tight[0], tight[3] - tight[1]
            if tw * th < MIN_BOARD_AREA_PCBLUES:
                continue
            if not (BOARD_ASPECT_RANGE[0] <= tw / th <= BOARD_ASPECT_RANGE[1]):
                continue
            boards.append(tight)
    boards.sort(key=lambda b: (b[1] // 120, b[0]))
    return boards


def analyze_board(
    gray, bbox: tuple[int, int, int, int]
) -> tuple[list[int], list[int]]:
    """Classify the 50 playable squares — rendering-agnostic version.

    PC Blues volumes use two renderings: wooden boards (pieces on dark
    squares, deel 1-35) and gray-checkered boards (pieces on ~gray squares,
    Klubkompetitie 37+) where a white piece's patch MEAN is barely above an
    empty square's. The black outline ring of a piece is the reliable
    signal: ``min < 100`` inside the patch. Classification:

    * black piece: mean < 90 (dark disc dominates),
    * white piece: bright disc (mean > 200 — wooden boards, empty dark
      squares plafonnent ~180) OU anneau/ombrage sombre dans une case
      claire (mean > 150 et min < 112 — boards gris : pièces min <= 21,
      cases vides uniformes à 192),
    * empty otherwise.
    """
    x1, y1, x2, y2 = bbox
    x1i, y1i = x1 + FEN_MARGIN_PX, y1 + FEN_MARGIN_PX
    bw = (x2 - x1) - 2 * FEN_MARGIN_PX
    bh = (y2 - y1) - 2 * FEN_MARGIN_PX
    h, w = gray.shape
    white_sqs: list[int] = []
    black_sqs: list[int] = []
    for row in range(10):
        for col in range(10):
            sq = _square_number(row, col)
            if sq is None:
                continue
            cx = int(x1i + (col + 0.5) * bw / 10.0)
            cy = int(y1i + (row + 0.5) * bh / 10.0)
            patch = gray[
                max(0, cy - SAMPLE_RADIUS) : min(h, cy + SAMPLE_RADIUS),
                max(0, cx - SAMPLE_RADIUS) : min(w, cx + SAMPLE_RADIUS),
            ]
            if patch.size == 0:
                continue
            mean = float(patch.mean())
            if mean < 90.0:
                black_sqs.append(sq)
            elif mean > 200.0 or (mean > 150.0 and float(patch.min()) < 112.0):
                white_sqs.append(sq)
    return sorted(white_sqs), sorted(black_sqs)


def boards_of_page(
    pdf_path: Path, page: int, cache_dir: Path, dpi: int = 200
) -> list[DetectedBoard]:
    """Render ``page`` (cached) and return its classified boards."""
    import numpy as np
    from PIL import Image

    cache_dir.mkdir(parents=True, exist_ok=True)
    png = cache_dir / f"page_{page:04d}.png"
    if not png.exists():
        _render_page_png(pdf_path, page, dpi, png)
    gray = np.asarray(Image.open(png).convert("L"), dtype=float)
    out: list[DetectedBoard] = []
    for idx, bbox in enumerate(detect_boards(png)):
        white, black = analyze_board(gray, bbox)
        out.append(
            DetectedBoard(
                page=page,
                index=idx,
                bbox=bbox,
                white_men=tuple(white),
                black_men=tuple(black),
            )
        )
    return out

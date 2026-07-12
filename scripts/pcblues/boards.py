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
    DARK_THRESHOLD,
    DILATION_ITERATIONS,
    _render_page_png,
    _shrink_to_border,
    analyze_board_fen,
)

#: Three boards across an A4 render at 200 dpi -> ~370 px wide each.
MIN_BOARD_AREA_PCBLUES = 80_000
#: Wide blobs up to ~4 boards are split before rejection.
MAX_SPLIT_PARTS = 4


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


def detect_boards(image_path: Path) -> list[tuple[int, int, int, int]]:
    """Bounding boxes of all boards on a page render, reading order."""
    import numpy as np
    from PIL import Image
    from scipy import ndimage

    arr = np.array(Image.open(image_path).convert("L"))
    mask = arr < DARK_THRESHOLD
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
            tw, th = tight[2] - tight[0], tight[3] - tight[1]
            if tw * th < MIN_BOARD_AREA_PCBLUES:
                continue
            if not (BOARD_ASPECT_RANGE[0] <= tw / th <= BOARD_ASPECT_RANGE[1]):
                continue
            boards.append(tight)
    boards.sort(key=lambda b: (b[1] // 120, b[0]))
    return boards


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
        white, black = analyze_board_fen(gray, bbox)
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

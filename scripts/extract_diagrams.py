"""Diagram-extraction pipeline for the Dubois reference corpus.

Three idempotent subcommands chained by ``all``::

    render        PDF page  -> per-page PNG + per-board bounding boxes + crops
    extract       page PNG + bbox -> classified squares (white/black) via pixel sampling
    materialize   extracted.json   -> pedagogy/tests/fixtures/dubois_diagrams.py

Everything is local CV: render uses pdftoppm + PIL/scipy to find board regions,
extract walks each of the 50 dark squares of a detected board and classifies
the mean pixel value of a small patch as a white piece, a black piece, or
empty. No API calls, no model, no token budget — fully deterministic.

Requires ``poppler-utils`` on PATH (``apt-get install poppler-utils``) and the
``extract`` optional deps::

    pip install -e ".[extract]"

Run from the repo root::

    python3 -m scripts.extract_diagrams all --pdf <pdf>
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterator, Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_DPI = 200
DEFAULT_CACHE = Path(".cache/diagrams")
DEFAULT_OUTPUT = Path("pedagogy/tests/fixtures/dubois_diagrams.py")

#: Minimum bounding-box area (pixels^2) for a region to be considered a board.
MIN_BOARD_AREA = 150_000
#: Board aspect-ratio window; Dubois boards measure ~537 x 567 -> 0.95.
BOARD_ASPECT_RANGE = (0.85, 1.20)
#: Morphological-dilation iterations used to merge board squares into one blob.
DILATION_ITERATIONS = 5
#: Threshold below which a grayscale pixel is considered "dark".
DARK_THRESHOLD = 230
#: Padding added around each detected board crop, in pixels.
CROP_PADDING = 8

#: Mean pixel value above which a sampled patch is classified as a white piece.
WHITE_PIECE_THRESHOLD = 200.0
#: Mean pixel value below which a sampled patch is classified as a black piece.
BLACK_PIECE_THRESHOLD = 90.0
#: Half-width of the pixel patch sampled at each square center, in pixels.
SAMPLE_RADIUS = 8
#: Margin (in pixels) skipped inside the board bounding box before sampling.
FEN_MARGIN_PX = 5


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class CropMetadata:
    """One detected diagram crop. Written to ``crops.json`` after `render`."""

    pdf_path: str
    page: int
    region_index: int           # 0-based, top-left first, row-major
    png_path: str
    bbox: tuple[int, int, int, int]   # (left, top, right, bottom) on page
    caption_text: Optional[str] = None  # e.g. "D5 : trait aux noirs"


@dataclass
class ExtractedDiagram:
    """One pixel-sampled extraction. Written to ``extracted.json``."""

    crop_id: str
    pdf_path: str
    page: int
    region_index: int
    caption_text: Optional[str] = None
    white_men: list[int] = field(default_factory=list)
    white_kings: list[int] = field(default_factory=list)
    black_men: list[int] = field(default_factory=list)
    black_kings: list[int] = field(default_factory=list)
    turn: str = "white"
    confidence: float = 1.0
    method: str = "cv"
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Validation helpers (pure, no I/O)
# ---------------------------------------------------------------------------

_SQUARE_RANGE = range(1, 51)


def validate_position(payload: dict[str, Any]) -> tuple[bool, str]:
    """Validate a position payload. Returns ``(ok, message)``."""
    required = ("white_men", "white_kings", "black_men", "black_kings", "turn")
    for key in required:
        if key not in payload:
            return False, f"missing key {key!r}"
    seen: set[int] = set()
    for key in ("white_men", "white_kings", "black_men", "black_kings"):
        squares = payload[key]
        if not isinstance(squares, list):
            return False, f"{key} must be a list"
        for sq in squares:
            if not isinstance(sq, int) or sq not in _SQUARE_RANGE:
                return False, f"{key}: invalid square {sq!r}"
            if sq in seen:
                return False, f"square {sq} appears in more than one piece list"
            seen.add(sq)
    if payload["turn"] not in ("white", "black"):
        return False, f"turn must be 'white' or 'black', got {payload['turn']!r}"
    if not (payload["white_men"] or payload["white_kings"]):
        return False, "no white pieces detected"
    if not (payload["black_men"] or payload["black_kings"]):
        return False, "no black pieces detected"
    return True, ""


# ---------------------------------------------------------------------------
# Render subcommand
# ---------------------------------------------------------------------------


def _parse_pages(spec: str, page_count: int) -> list[int]:
    """Parse ``--pages`` spec ("all", "5", "5-13", "5,7,9") into a list."""
    if spec == "all":
        return list(range(1, page_count + 1))
    out: set[int] = set()
    for chunk in spec.split(","):
        chunk = chunk.strip()
        if "-" in chunk:
            a, b = chunk.split("-", 1)
            out.update(range(int(a), int(b) + 1))
        else:
            out.add(int(chunk))
    return sorted(p for p in out if 1 <= p <= page_count)


def _pdf_page_count(pdf_path: Path) -> int:
    out = subprocess.check_output(["pdfinfo", str(pdf_path)], text=True)
    for line in out.splitlines():
        if line.startswith("Pages:"):
            return int(line.split(":", 1)[1].strip())
    raise RuntimeError(f"pdfinfo did not report a page count for {pdf_path}")


_CAPTION_RE = re.compile(
    r"(D\d+)\s*:\s*trait aux\s+(blancs|noirs)",
    flags=re.IGNORECASE,
)

_DIAGRAM_CAPTION_RE = re.compile(
    r"trait aux|\b\d+\s*(?:ère|ere|er|e|ième|ème)\s*rafle\b",
    flags=re.IGNORECASE,
)


def _count_diagram_captions(text: str) -> int:
    """Count diagram-marking captions: 'trait aux ...' or '<n>e rafle'."""
    return len(_DIAGRAM_CAPTION_RE.findall(text))


def _captions_in_order(pdf_path: Path, page: int) -> list[str]:
    """Extract per-diagram captions in row-major (top, left) reading order."""
    out = subprocess.check_output(
        ["pdftotext", "-layout", "-f", str(page), "-l", str(page), str(pdf_path), "-"],
        text=True,
    )
    captions: list[str] = []
    for line in out.splitlines():
        for match in _CAPTION_RE.finditer(line):
            captions.append(f"{match.group(1)} : trait aux {match.group(2).lower()}")
    return captions


def _trait_aux_count(pdf_path: Path, page: int) -> int:
    out = subprocess.check_output(
        ["pdftotext", "-layout", "-f", str(page), "-l", str(page), str(pdf_path), "-"],
        text=True,
    )
    return _count_diagram_captions(out)


def _render_page_png(pdf_path: Path, page: int, dpi: int, dest: Path) -> Path:
    """Render a single page to PNG via pdftoppm."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    prefix = str(dest.parent / f"page_{page:03d}")
    subprocess.check_call(
        [
            "pdftoppm", "-r", str(dpi),
            "-f", str(page), "-l", str(page),
            "-png", str(pdf_path), prefix,
        ]
    )
    candidates = sorted(dest.parent.glob(f"page_{page:03d}-*.png"))
    if not candidates:
        raise RuntimeError(f"pdftoppm did not produce a PNG for page {page}")
    if candidates[0] != dest:
        candidates[0].replace(dest)
    return dest


#: Pixel value below which a row/column is "mostly dark", used to find borders.
BORDER_DARK_THRESHOLD = 80
#: Fraction of a row/column's width that must be dark to count as a border line.
BORDER_DENSITY = 0.60


def _shrink_to_border(
    arr: Any, left: int, top: int, right: int, bottom: int
) -> tuple[int, int, int, int]:
    """Shrink a rough bbox to the actual thick-black-border rectangle.

    Each Dubois diagram has a thick black rectangle around the playable board.
    The CV blob-detector returns a generous bbox that often includes the
    caption below (e.g. "D1 : trait aux noirs"). We scan inward from each
    side and stop at the first row / column where ``BORDER_DENSITY`` of the
    pixels are darker than ``BORDER_DARK_THRESHOLD`` — that's the border
    line. The returned bbox is the tightest rectangle bounded by those four
    lines.
    """
    import numpy as np

    region = arr[top:bottom, left:right]
    h, w = region.shape
    dark = region < BORDER_DARK_THRESHOLD
    row_density = dark.sum(axis=1) / max(w, 1)
    col_density = dark.sum(axis=0) / max(h, 1)

    def first_above(values: Any) -> int:
        idx = np.argmax(values >= BORDER_DENSITY)
        return int(idx) if values[idx] >= BORDER_DENSITY else 0

    top_off = first_above(row_density)
    bottom_off = first_above(row_density[::-1])
    left_off = first_above(col_density)
    right_off = first_above(col_density[::-1])

    new_top = top + top_off
    new_bottom = bottom - bottom_off
    new_left = left + left_off
    new_right = right - right_off
    if new_right <= new_left or new_bottom <= new_top:
        return left, top, right, bottom
    return new_left, new_top, new_right, new_bottom


def _detect_boards(image_path: Path) -> list[tuple[int, int, int, int]]:
    """Return tight bounding boxes of detected board regions on a page render."""
    import numpy as np
    from PIL import Image
    from scipy import ndimage

    img = Image.open(image_path).convert("L")
    arr = np.array(img)
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
        if w * h < MIN_BOARD_AREA:
            continue
        aspect = w / h
        if not (BOARD_ASPECT_RANGE[0] <= aspect <= BOARD_ASPECT_RANGE[1]):
            continue
        tight = _shrink_to_border(arr, left, top, right, bottom)
        tw = tight[2] - tight[0]
        th = tight[3] - tight[1]
        if tw * th < MIN_BOARD_AREA:
            continue
        tight_aspect = tw / th
        if not (BOARD_ASPECT_RANGE[0] <= tight_aspect <= BOARD_ASPECT_RANGE[1]):
            continue
        boards.append(tight)
    boards.sort(key=lambda b: (b[1] // 80, b[0]))
    return boards


def _crop_board(image_path: Path, bbox: tuple[int, int, int, int], dest: Path) -> None:
    from PIL import Image

    img = Image.open(image_path)
    left, top, right, bottom = bbox
    pad = CROP_PADDING
    left = max(left - pad, 0)
    top = max(top - pad, 0)
    right = min(right + pad, img.width)
    bottom = min(bottom + 4 * pad + 50, img.height)
    img.crop((left, top, right, bottom)).save(dest, format="PNG")


def cmd_render(args: argparse.Namespace) -> int:
    pdf_path = Path(args.pdf).resolve()
    if not pdf_path.exists():
        print(f"PDF not found: {pdf_path}", file=sys.stderr)
        return 2
    cache = Path(args.cache).resolve()
    pages_dir = cache / "pages"
    crops_dir = cache / "crops"
    pages_dir.mkdir(parents=True, exist_ok=True)
    crops_dir.mkdir(parents=True, exist_ok=True)

    total_pages = _pdf_page_count(pdf_path)
    pages = _parse_pages(args.pages, total_pages)

    manifest: list[CropMetadata] = []
    for page in pages:
        n_diag = _trait_aux_count(pdf_path, page)
        if n_diag == 0:
            if args.verbose:
                print(f"page {page}: no diagram caption, skipped")
            continue
        page_png = pages_dir / f"page_{page:03d}.png"
        if not page_png.exists() or args.force:
            _render_page_png(pdf_path, page, args.dpi, page_png)
        boards = _detect_boards(page_png)
        captions = _captions_in_order(pdf_path, page)
        if len(boards) != n_diag:
            print(
                f"page {page}: WARN expected {n_diag} diagrams "
                f"(from caption count), detected {len(boards)} board(s)",
                file=sys.stderr,
            )
        for idx, bbox in enumerate(boards):
            crop_png = crops_dir / f"page_{page:03d}_d{idx + 1:02d}.png"
            if not crop_png.exists() or args.force:
                _crop_board(page_png, bbox, crop_png)
            caption = captions[idx] if idx < len(captions) else None
            manifest.append(
                CropMetadata(
                    pdf_path=str(pdf_path.name),
                    page=page,
                    region_index=idx,
                    png_path=str(crop_png.relative_to(cache)),
                    bbox=bbox,
                    caption_text=caption,
                )
            )

    manifest_path = cache / "crops.json"
    manifest_path.write_text(
        json.dumps([asdict(m) for m in manifest], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"\nrender: {len(manifest)} crop(s) ready -> {manifest_path}")
    return 0


# ---------------------------------------------------------------------------
# Extract subcommand (pixel sampling — no API)
# ---------------------------------------------------------------------------


def _square_number(row: int, col: int) -> Optional[int]:
    """Return the FMJD square number (1-50) for a (row, col) cell.

    Returns None for light squares (which are unused in international draughts).
    Row 0 is the top of the board (black's back rank), row 9 the bottom.
    """
    if (row + col) % 2 == 0:
        return None
    return row * 5 + col // 2 + 1


def analyze_board_fen(
    gray: Any,
    bbox: tuple[int, int, int, int],
    *,
    margin_px: int = FEN_MARGIN_PX,
    sample_radius: int = SAMPLE_RADIUS,
    white_threshold: float = WHITE_PIECE_THRESHOLD,
    black_threshold: float = BLACK_PIECE_THRESHOLD,
) -> tuple[list[int], list[int]]:
    """Classify every dark square of a board as white piece, black piece, or empty.

    ``gray`` is a 2-D grayscale numpy array (the rendered page). ``bbox`` is
    ``(x1, y1, x2, y2)`` in pixel coords. Returns ``(white_squares, black_squares)``
    sorted in increasing order.
    """
    x1, y1, x2, y2 = bbox
    x1i = x1 + margin_px
    y1i = y1 + margin_px
    bw = (x2 - x1) - 2 * margin_px
    bh = (y2 - y1) - 2 * margin_px
    sq_w = bw / 10.0
    sq_h = bh / 10.0

    white_sqs: list[int] = []
    black_sqs: list[int] = []
    h, w = gray.shape

    for row in range(10):
        for col in range(10):
            sq = _square_number(row, col)
            if sq is None:
                continue
            cx = int(x1i + (col + 0.5) * sq_w)
            cy = int(y1i + (row + 0.5) * sq_h)
            y0 = max(0, cy - sample_radius)
            y1c = min(h, cy + sample_radius)
            x0 = max(0, cx - sample_radius)
            x1c = min(w, cx + sample_radius)
            patch = gray[y0:y1c, x0:x1c]
            if patch.size == 0:
                continue
            cv = float(patch.mean())
            if cv > white_threshold:
                white_sqs.append(sq)
            elif cv < black_threshold:
                black_sqs.append(sq)

    return sorted(white_sqs), sorted(black_sqs)


def _infer_turn(caption: Optional[str]) -> str:
    if caption and "noirs" in caption.lower():
        return "black"
    return "white"


def _load_manifest(cache: Path) -> list[CropMetadata]:
    path = cache / "crops.json"
    if not path.exists():
        raise FileNotFoundError(f"crop manifest not found: {path}. Run `render` first.")
    return [CropMetadata(**entry) for entry in json.loads(path.read_text(encoding="utf-8"))]


def _load_extracted(path: Path) -> dict[str, ExtractedDiagram]:
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {entry["crop_id"]: ExtractedDiagram(**entry) for entry in raw}


def _save_extracted(path: Path, table: dict[str, ExtractedDiagram]) -> None:
    payload = [asdict(table[k]) for k in sorted(table)]
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def cmd_extract(args: argparse.Namespace) -> int:
    import numpy as np
    from PIL import Image

    cache = Path(args.cache).resolve()
    pages_dir = cache / "pages"
    manifest = _load_manifest(cache)
    out_path = cache / "extracted.json"
    table = _load_extracted(out_path)

    page_cache: dict[int, Any] = {}
    failures = 0
    t0 = time.time()
    for i, meta in enumerate(manifest, start=1):
        page_png = pages_dir / f"page_{meta.page:03d}.png"
        if not page_png.exists():
            print(
                f"[{i:>3}/{len(manifest)}] {meta.png_path}: missing {page_png}",
                file=sys.stderr,
            )
            failures += 1
            continue

        if meta.page not in page_cache:
            page_cache[meta.page] = np.array(Image.open(page_png).convert("L"))
        gray = page_cache[meta.page]

        white_sqs, black_sqs = analyze_board_fen(
            gray,
            meta.bbox,
            margin_px=args.margin_px,
            sample_radius=args.sample_radius,
            white_threshold=args.white_threshold,
            black_threshold=args.black_threshold,
        )
        turn = _infer_turn(meta.caption_text)

        payload = {
            "white_men": white_sqs,
            "white_kings": [],
            "black_men": black_sqs,
            "black_kings": [],
            "turn": turn,
        }
        ok, msg = validate_position(payload)

        record = ExtractedDiagram(
            crop_id=meta.png_path,
            pdf_path=meta.pdf_path,
            page=meta.page,
            region_index=meta.region_index,
            caption_text=meta.caption_text,
            white_men=white_sqs,
            black_men=black_sqs,
            turn=turn,
            method="cv",
            error=None if ok else msg,
        )
        if not ok:
            failures += 1
        table[meta.png_path] = record

        if args.verbose:
            status = "OK" if ok else f"FAIL ({msg})"
            print(
                f"[{i:>3}/{len(manifest)}] {meta.png_path}: "
                f"{len(white_sqs)}W {len(black_sqs)}B turn={turn} {status}"
            )

    _save_extracted(out_path, table)
    elapsed = time.time() - t0
    total = len(table) or 1
    total_failures = sum(1 for e in table.values() if e.error is not None)
    fail_ratio = total_failures / total
    print(
        f"\nextract: {len(table)} cached, {failures} new failure(s) this run, "
        f"{total_failures} total failure(s) ({fail_ratio:.1%}); "
        f"elapsed {elapsed:.1f}s"
    )
    if fail_ratio > args.fail_threshold:
        print(
            f"extract: fail ratio {fail_ratio:.1%} exceeds threshold "
            f"{args.fail_threshold:.1%}",
            file=sys.stderr,
        )
        return 1
    return 0


# ---------------------------------------------------------------------------
# Materialize subcommand
# ---------------------------------------------------------------------------


_PY_TEMPLATE_HEADER = '''"""Auto-generated Dubois diagram fixtures.

DO NOT EDIT BY HAND. Regenerate with::

    python3 -m scripts.extract_diagrams all --pdf <pdf_path>

Each :class:`DuboisDiagram` mirrors an entry produced by deterministic pixel
sampling (no LLM, no API). The ``to_state`` helper materialises a
:class:`pedagogy.game.GameState`.
"""

from __future__ import annotations

from dataclasses import dataclass

from pedagogy.game import GameState


@dataclass(frozen=True)
class DuboisDiagram:
    crop_id: str
    page: int
    region_index: int
    caption_text: str
    turn: str
    white_men: tuple[int, ...]
    white_kings: tuple[int, ...]
    black_men: tuple[int, ...]
    black_kings: tuple[int, ...]
    confidence: float


def to_state(diag: DuboisDiagram) -> GameState:
    return GameState(
        white_men=frozenset(diag.white_men),
        white_kings=frozenset(diag.white_kings),
        black_men=frozenset(diag.black_men),
        black_kings=frozenset(diag.black_kings),
        turn=diag.turn,  # type: ignore[arg-type]
    )


'''


def cmd_materialize(args: argparse.Namespace) -> int:
    cache = Path(args.cache).resolve()
    out_path = cache / "extracted.json"
    if not out_path.exists():
        print(f"no extracted.json at {out_path}; run `extract` first.", file=sys.stderr)
        return 2
    table = _load_extracted(out_path)
    ok_entries = [e for e in table.values() if e.error is None]

    def render_entry(entry: ExtractedDiagram) -> str:
        caption = (entry.caption_text or "").replace('"', '\\"')
        lines = ["    DuboisDiagram("]
        lines.append(f"        crop_id={entry.crop_id!r},")
        lines.append(f"        page={entry.page},")
        lines.append(f"        region_index={entry.region_index},")
        lines.append(f'        caption_text="{caption}",')
        lines.append(f"        turn={entry.turn!r},")
        lines.append(f"        white_men={tuple(sorted(entry.white_men))!r},")
        lines.append(f"        white_kings={tuple(sorted(entry.white_kings))!r},")
        lines.append(f"        black_men={tuple(sorted(entry.black_men))!r},")
        lines.append(f"        black_kings={tuple(sorted(entry.black_kings))!r},")
        lines.append(f"        confidence={entry.confidence},")
        lines.append("    ),")
        return "\n".join(lines)

    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as f:
        f.write(_PY_TEMPLATE_HEADER)
        f.write("ALL_DIAGRAMS: list[DuboisDiagram] = [\n")
        for entry in sorted(ok_entries, key=lambda e: (e.page, e.region_index)):
            f.write(render_entry(entry))
            f.write("\n")
        f.write("]\n")

    skipped = len(table) - len(ok_entries)
    msg = f"materialize: wrote {len(ok_entries)} fixture(s) to {output}"
    if skipped:
        msg += (
            f"\n  ({skipped} entry/entries with errors NOT materialised; "
            f"inspect {out_path} and re-run extract with --force)"
        )
    print(msg)
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _cmd_all(args: argparse.Namespace) -> int:
    r1 = cmd_render(args)
    if r1:
        return r1
    r2 = cmd_extract(args)
    if r2:
        return r2
    return cmd_materialize(args)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="extract_diagrams",
        description="Extract Dubois diagram positions via deterministic pixel sampling.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_render = sub.add_parser("render", help="rasterise pages and detect boards")
    p_render.add_argument("--pdf", required=True, help="path to the input PDF")
    p_render.add_argument(
        "--pages", default="all",
        help='page range: "all", "5", "5-13", or "5,7,9" (default "all")',
    )
    p_render.add_argument("--cache", default=str(DEFAULT_CACHE))
    p_render.add_argument("--dpi", type=int, default=DEFAULT_DPI)
    p_render.add_argument("--force", action="store_true", help="re-render even if cached")
    p_render.add_argument("--verbose", action="store_true")
    p_render.set_defaults(func=cmd_render)

    p_extract = sub.add_parser(
        "extract", help="sample each detected board with pure pixel thresholding"
    )
    p_extract.add_argument("--cache", default=str(DEFAULT_CACHE))
    p_extract.add_argument(
        "--white-threshold", type=float, default=WHITE_PIECE_THRESHOLD,
        help=f"mean pixel above this -> white piece (default {WHITE_PIECE_THRESHOLD})",
    )
    p_extract.add_argument(
        "--black-threshold", type=float, default=BLACK_PIECE_THRESHOLD,
        help=f"mean pixel below this -> black piece (default {BLACK_PIECE_THRESHOLD})",
    )
    p_extract.add_argument(
        "--sample-radius", type=int, default=SAMPLE_RADIUS,
        help=f"half-width of patch sampled at each square (default {SAMPLE_RADIUS} px)",
    )
    p_extract.add_argument(
        "--margin-px", type=int, default=FEN_MARGIN_PX,
        help=f"pixels skipped inside the board border before sampling (default {FEN_MARGIN_PX})",
    )
    p_extract.add_argument(
        "--fail-threshold", type=float, default=0.10,
        help="exit non-zero when fail ratio exceeds this fraction (default 0.10)",
    )
    p_extract.add_argument("--verbose", action="store_true")
    p_extract.set_defaults(func=cmd_extract)

    p_materialize = sub.add_parser(
        "materialize", help="write the Python fixtures file from extracted JSON",
    )
    p_materialize.add_argument("--cache", default=str(DEFAULT_CACHE))
    p_materialize.add_argument("--output", default=str(DEFAULT_OUTPUT))
    p_materialize.set_defaults(func=cmd_materialize)

    p_all = sub.add_parser("all", help="run render + extract + materialize")
    p_all.add_argument("--pdf", required=True)
    p_all.add_argument("--pages", default="all")
    p_all.add_argument("--cache", default=str(DEFAULT_CACHE))
    p_all.add_argument("--dpi", type=int, default=DEFAULT_DPI)
    p_all.add_argument("--output", default=str(DEFAULT_OUTPUT))
    p_all.add_argument("--white-threshold", type=float, default=WHITE_PIECE_THRESHOLD)
    p_all.add_argument("--black-threshold", type=float, default=BLACK_PIECE_THRESHOLD)
    p_all.add_argument("--sample-radius", type=int, default=SAMPLE_RADIUS)
    p_all.add_argument("--margin-px", type=int, default=FEN_MARGIN_PX)
    p_all.add_argument("--fail-threshold", type=float, default=0.10)
    p_all.add_argument("--force", action="store_true")
    p_all.add_argument("--verbose", action="store_true")
    p_all.set_defaults(func=lambda a: _cmd_all(a))
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    for tool in ("pdftoppm", "pdftotext", "pdfinfo"):
        if shutil.which(tool) is None:
            print(f"required system tool not found in PATH: {tool}", file=sys.stderr)
            return 2
    args = _build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())

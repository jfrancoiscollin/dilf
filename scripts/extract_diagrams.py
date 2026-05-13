"""Diagram-extraction workflow for the Dubois reference corpus.

Three idempotent subcommands chained by ``all``::

    render        PDF page  -> per-diagram PNG crops + caption metadata
    extract       PNG crops -> JSON positions (via Claude Vision)
    materialize   JSON      -> pedagogy/tests/fixtures/dubois_diagrams.py

The render step uses pure CV (PIL + scipy) so it has no API cost. Each
diagram is detected as a near-square dark-pixel cluster on the rendered
page, dilated to merge the board squares into a single component, then
filtered by size and aspect ratio.

The extract step calls Claude Vision (default ``claude-haiku-4-5``) per
PNG. It is fully idempotent: results are stored per-PNG in a JSON
manifest and re-running picks up where it left off. Cost for the whole
Dubois V5 catalogue (~70 diagrams) is approximately $0.03 with Haiku.

Run from the repo root::

    python3 -m scripts.extract_diagrams render --pdf <file.pdf>
    python3 -m scripts.extract_diagrams extract --cache .cache/diagrams
    python3 -m scripts.extract_diagrams materialize --cache .cache/diagrams

or in one shot::

    python3 -m scripts.extract_diagrams all --pdf <file.pdf>

This script intentionally lives outside ``pedagogy/`` because it has heavy
optional dependencies (Pillow, NumPy, scipy, anthropic). Install with::

    pip install -e ".[extract]"
"""

from __future__ import annotations

import argparse
import asyncio
import base64
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

DEFAULT_MODEL = "claude-haiku-4-5"
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

#: Prompt sent to Claude Vision per diagram.
SYSTEM_PROMPT = """You analyze international draughts (FMJD, 10x10) diagrams.

Board layout (standard diagram orientation):
- The board has 10 rows. Row 1 is at the TOP of the image, row 10 at the BOTTOM.
- Only the 50 dark squares are playable. They are numbered 1-50.
- Row 1 contains squares 1, 2, 3, 4, 5 (left to right).
- Row 2 contains squares 6, 7, 8, 9, 10.
- ... and so on. Row 10 contains squares 46, 47, 48, 49, 50.
- Square 1 is the top-left dark square. Square 50 is the bottom-right dark square.

Piece identification:
- A WHITE piece appears as a light/cream/empty filled circle.
- A BLACK piece appears as a dark/filled-in circle.
- A KING (dame) has an additional inner mark: a second smaller circle, a crown,
  or a doubled outline. Pieces WITHOUT this inner mark are MEN, not kings.

CRITICAL RULES:
1. Look at the image carefully. Identify EACH visible piece individually.
2. Do NOT invent pieces. If you see N pieces, list exactly N squares total
   across the four lists. Typical diagrams have 15-30 pieces.
3. Do NOT default to regular geometric patterns (a full column, a full row,
   a long diagonal). Real positions are usually scattered.
4. A piece is a KING only if you can clearly see the inner mark. If in doubt,
   it is a MAN. Many diagrams have ZERO kings.
5. Each square 1-50 appears in AT MOST ONE of the four lists.
6. If the image is blurry, cropped, or you cannot read the position reliably,
   return {"error": "<short reason>"} instead of guessing.

The caption below the diagram says "trait aux blancs" (white to move) or
"trait aux noirs" (black to move). Set "turn" accordingly. Continuation
diagrams labelled "Ne rafle" inherit the turn from the parent position.

Return ONLY a JSON object, no prose, with this exact schema:
{
  "white_men": [int, ...],
  "white_kings": [int, ...],
  "black_men": [int, ...],
  "black_kings": [int, ...],
  "turn": "white" or "black",
  "confidence": 0.0-1.0
}"""


#: Stricter prompt used on a second attempt after a validation failure.
STRICT_SYSTEM_PROMPT = SYSTEM_PROMPT + """

RETRY NOTE: the first attempt produced invalid output. Verify mentally
(do NOT write your reasoning, do NOT emit prose) that every square 1-50
appears in at most one of the four lists, then output ONLY the JSON object."""


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
    """One Claude-vision extraction. Written to ``extracted.json``."""

    crop_id: str                # unique key, derived from png_path
    pdf_path: str
    page: int
    region_index: int
    caption_text: Optional[str] = None
    white_men: list[int] = field(default_factory=list)
    white_kings: list[int] = field(default_factory=list)
    black_men: list[int] = field(default_factory=list)
    black_kings: list[int] = field(default_factory=list)
    turn: str = "white"
    confidence: float = 0.0
    model: str = ""
    latency_ms: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    retries: int = 0
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Validation helpers (pure, no I/O)
# ---------------------------------------------------------------------------

_SQUARE_RANGE = range(1, 51)


def validate_position(payload: dict[str, Any]) -> tuple[bool, str]:
    """Validate the parsed JSON payload of an API response.

    Returns ``(ok, message)``. ``message`` describes the first failure when
    ``ok`` is ``False`` and is the empty string otherwise.
    """
    if "error" in payload:
        return False, f"model returned error: {payload['error']!s}"
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
    return True, ""


def parse_api_response(raw_text: str) -> dict[str, Any]:
    """Parse the text returned by the model into a JSON dict.

    Strips any markdown code fences the model may add ("```json ... ```").
    """
    text = raw_text.strip()
    if text.startswith("```"):
        # Drop the opening fence and the trailing one.
        text = re.sub(r"^```[a-zA-Z]*\n", "", text)
        text = re.sub(r"\n?```$", "", text)
    return json.loads(text)


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


_DIAGRAM_CAPTION_RE = re.compile(
    r"trait aux|\b\d+\s*(?:ère|ere|er|e|ième|ème)\s*rafle\b",
    flags=re.IGNORECASE,
)


def _count_diagram_captions(text: str) -> int:
    """Count diagram-marking captions: 'trait aux ...' or '<n>e rafle'."""
    return len(_DIAGRAM_CAPTION_RE.findall(text))


def _trait_aux_count(pdf_path: Path, page: int) -> int:
    out = subprocess.check_output(
        ["pdftotext", "-layout", "-f", str(page), "-l", str(page), str(pdf_path), "-"],
        text=True,
    )
    return _count_diagram_captions(out)


def _render_page_png(pdf_path: Path, page: int, dpi: int, dest: Path) -> Path:
    """Render a single page to PNG via pdftoppm. Returns the produced path."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    prefix = str(dest.parent / f"page_{page:03d}")
    subprocess.check_call(
        [
            "pdftoppm", "-r", str(dpi),
            "-f", str(page), "-l", str(page),
            "-png", str(pdf_path), prefix,
        ]
    )
    # pdftoppm appends a zero-padded page number; rename to the canonical name.
    candidates = sorted(dest.parent.glob(f"page_{page:03d}-*.png"))
    if not candidates:
        raise RuntimeError(f"pdftoppm did not produce a PNG for page {page}")
    if candidates[0] != dest:
        candidates[0].replace(dest)
    return dest


def _detect_boards(image_path: Path) -> list[tuple[int, int, int, int]]:
    """Return bounding boxes of detected board regions on a page render."""
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
        boards.append((left, top, right, bottom))
    # Sort row-major: by top-then-left, with a small row tolerance.
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
    # Pull down enough to capture the caption "Dn : trait aux X" (~60 px).
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

    out = cache / "crops.json"
    out.write_text(
        json.dumps([asdict(m) for m in manifest], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"\nrender: {len(manifest)} crop(s) ready -> {out}")
    return 0


# ---------------------------------------------------------------------------
# Extract subcommand
# ---------------------------------------------------------------------------


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


def _user_image_block(png_bytes: bytes) -> dict[str, Any]:
    """Build a Claude Vision user message containing one PNG + the prompt."""
    image_b64 = base64.b64encode(png_bytes).decode("ascii")
    return {
        "role": "user",
        "content": [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": image_b64,
                },
            },
            {"type": "text", "text": "Extract the position."},
        ],
    }


def _assistant_json_block(position: dict[str, Any]) -> dict[str, Any]:
    """Build an assistant message that returns the canonical JSON answer."""
    return {
        "role": "assistant",
        "content": [
            {"type": "text", "text": json.dumps(position, separators=(",", ":"))}
        ],
    }


async def _call_claude_vision_async(
    client: Any,
    png_bytes: bytes,
    *,
    model: str,
    max_tokens: int = 600,
    strict: bool = False,
    few_shot: list[tuple[bytes, dict[str, Any]]] | None = None,
) -> tuple[str, int, int]:
    messages: list[dict[str, Any]] = []
    for example_bytes, example_position in few_shot or []:
        messages.append(_user_image_block(example_bytes))
        messages.append(_assistant_json_block(example_position))
    messages.append(_user_image_block(png_bytes))

    response = await client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=STRICT_SYSTEM_PROMPT if strict else SYSTEM_PROMPT,
        messages=messages,
    )
    block = response.content[0]
    text = getattr(block, "text", "")
    return text, response.usage.input_tokens, response.usage.output_tokens


async def _extract_one(
    client: Any,
    cache: Path,
    meta: CropMetadata,
    model: str,
    few_shot: list[tuple[bytes, dict[str, Any]]] | None = None,
) -> ExtractedDiagram:
    """Run the 2-attempt extraction for a single crop. Returns the record."""
    png_bytes = (cache / meta.png_path).read_bytes()
    payload: Optional[dict[str, Any]] = None
    last_error: Optional[str] = None
    in_tokens = 0
    out_tokens = 0
    latency = 0
    attempts = 0
    while attempts < 2:
        attempts += 1
        strict = attempts > 1
        try:
            t0 = time.time()
            text, t_in, t_out = await _call_claude_vision_async(
                client, png_bytes, model=model, strict=strict, few_shot=few_shot
            )
            in_tokens += t_in
            out_tokens += t_out
            latency = int((time.time() - t0) * 1000)
            candidate = parse_api_response(text)
            ok, msg = validate_position(candidate)
        except Exception as exc:  # noqa: BLE001
            last_error = str(exc)
            payload = None
            print(
                f"    FAILED (attempt {attempts}): {meta.png_path}: {exc}",
                file=sys.stderr,
            )
            continue
        if ok:
            payload = candidate
            last_error = None
            break
        payload = None
        last_error = msg
        print(
            f"    VALIDATION (attempt {attempts}): {meta.png_path}: {msg}",
            file=sys.stderr,
        )

    if last_error is not None:
        return ExtractedDiagram(
            crop_id=meta.png_path,
            pdf_path=meta.pdf_path,
            page=meta.page,
            region_index=meta.region_index,
            caption_text=meta.caption_text,
            model=model,
            latency_ms=latency,
            input_tokens=in_tokens,
            output_tokens=out_tokens,
            retries=attempts - 1,
            error=last_error,
        )
    assert payload is not None
    return ExtractedDiagram(
        crop_id=meta.png_path,
        pdf_path=meta.pdf_path,
        page=meta.page,
        region_index=meta.region_index,
        caption_text=meta.caption_text,
        white_men=payload.get("white_men", []),
        white_kings=payload.get("white_kings", []),
        black_men=payload.get("black_men", []),
        black_kings=payload.get("black_kings", []),
        turn=payload.get("turn", "white"),
        confidence=float(payload.get("confidence", 0.0)),
        model=model,
        latency_ms=latency,
        input_tokens=in_tokens,
        output_tokens=out_tokens,
        retries=attempts - 1,
        error=None,
    )


async def _cmd_extract_async(args: argparse.Namespace) -> int:
    cache = Path(args.cache).resolve()
    manifest = _load_manifest(cache)
    out_path = cache / "extracted.json"
    table = _load_extracted(out_path)

    pending = [
        m for m in manifest
        if m.png_path not in table or table[m.png_path].error is not None
    ]
    if args.max_diagrams:
        pending = pending[: args.max_diagrams]

    if args.dry_run:
        print(f"extract dry-run: {len(pending)} diagram(s) would be sent to {args.model}")
        for m in pending[:5]:
            print(f"  - {m.png_path}  caption={m.caption_text!r}")
        if len(pending) > 5:
            print(f"  ... and {len(pending) - 5} more")
        return 0

    import anthropic

    from pedagogy.tests.fixtures.dubois_ground_truth import (
        load_examples as _load_few_shot_examples,
    )

    few_shot = _load_few_shot_examples(args.few_shot)
    if few_shot:
        print(
            f"extract: prepending {len(few_shot)} few-shot example(s) to every call",
            flush=True,
        )

    client = anthropic.AsyncAnthropic()
    semaphore = asyncio.Semaphore(args.concurrency)

    async def bounded(meta: CropMetadata) -> ExtractedDiagram:
        async with semaphore:
            return await _extract_one(
                client, cache, meta, args.model, few_shot=few_shot
            )

    tasks = [asyncio.create_task(bounded(m)) for m in pending]
    failures = 0
    print(
        f"extract: dispatching {len(pending)} crop(s) with concurrency={args.concurrency}",
        flush=True,
    )
    for i, fut in enumerate(asyncio.as_completed(tasks), start=1):
        result = await fut
        table[result.crop_id] = result
        if result.error is not None:
            failures += 1
        status = "FAIL" if result.error else "OK"
        print(
            f"[{i:>3}/{len(pending)}] {result.crop_id} {status} "
            f"(attempts={result.retries + 1})",
            flush=True,
        )
        _save_extracted(out_path, table)

    total_in = sum(e.input_tokens for e in table.values())
    total_out = sum(e.output_tokens for e in table.values())
    total_failures = sum(1 for e in table.values() if e.error is not None)
    total = len(table) or 1
    fail_ratio = total_failures / total
    print(
        f"\nextract: {len(table)} cached, {failures} new failure(s) this run, "
        f"{total_failures} total failure(s) ({fail_ratio:.1%}); "
        f"tokens in={total_in} out={total_out}"
    )
    if fail_ratio > args.fail_threshold:
        print(
            f"extract: fail ratio {fail_ratio:.1%} exceeds threshold "
            f"{args.fail_threshold:.1%}",
            file=sys.stderr,
        )
        return 1
    return 0


def cmd_extract(args: argparse.Namespace) -> int:
    return asyncio.run(_cmd_extract_async(args))


# ---------------------------------------------------------------------------
# Materialize subcommand
# ---------------------------------------------------------------------------


_PY_TEMPLATE_HEADER = '''"""Auto-generated Dubois diagram fixtures.

DO NOT EDIT BY HAND. Regenerate with::

    python3 -m scripts.extract_diagrams all --pdf <pdf_path>

Each :class:`DuboisDiagram` mirrors an entry produced by Claude Vision and
has been validated for square-set disjointness. The ``to_state`` helper
materialises a :class:`pedagogy.game.GameState`.
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
    in_path = cache / "extracted.json"
    out_path = Path(args.output).resolve()
    table = _load_extracted(in_path)

    good = [e for e in table.values() if e.error is None]
    bad = [e for e in table.values() if e.error is not None]
    good.sort(key=lambda e: (e.page, e.region_index))

    lines: list[str] = [_PY_TEMPLATE_HEADER]
    lines.append("ALL_DIAGRAMS: list[DuboisDiagram] = [")
    for entry in good:
        caption = (entry.caption_text or "").replace('"', '\\"')
        lines.append("    DuboisDiagram(")
        lines.append(f"        crop_id={entry.crop_id!r},")
        lines.append(f"        page={entry.page},")
        lines.append(f"        region_index={entry.region_index},")
        lines.append(f'        caption_text="{caption}",')
        lines.append(f"        turn={entry.turn!r},")
        lines.append(f"        white_men={tuple(sorted(entry.white_men))!r},")
        lines.append(f"        white_kings={tuple(sorted(entry.white_kings))!r},")
        lines.append(f"        black_men={tuple(sorted(entry.black_men))!r},")
        lines.append(f"        black_kings={tuple(sorted(entry.black_kings))!r},")
        lines.append(f"        confidence={entry.confidence!r},")
        lines.append("    ),")
    lines.append("]\n")
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"materialize: wrote {len(good)} fixture(s) to {out_path}")
    if bad:
        print(
            f"  ({len(bad)} entry/entries with errors NOT materialised; inspect "
            f"{in_path} and re-run extract with --force)",
            file=sys.stderr,
        )
    return 0


# ---------------------------------------------------------------------------
# CLI plumbing
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_render = sub.add_parser("render", help="render PDF pages and crop diagram boards")
    p_render.add_argument("--pdf", required=True, help="path to the input PDF")
    p_render.add_argument(
        "--pages", default="all",
        help='pages to scan: "all" (default), "5", "5-13", "5,7,9"',
    )
    p_render.add_argument("--cache", default=str(DEFAULT_CACHE))
    p_render.add_argument("--dpi", type=int, default=DEFAULT_DPI)
    p_render.add_argument("--force", action="store_true", help="re-render even if cached")
    p_render.add_argument("--verbose", action="store_true")
    p_render.set_defaults(func=cmd_render)

    p_extract = sub.add_parser("extract", help="send crops to Claude Vision")
    p_extract.add_argument("--cache", default=str(DEFAULT_CACHE))
    p_extract.add_argument("--model", default=DEFAULT_MODEL)
    p_extract.add_argument(
        "--max-diagrams", type=int, default=0,
        help="cap how many pending diagrams to send (0 = no cap)",
    )
    p_extract.add_argument("--dry-run", action="store_true")
    p_extract.add_argument(
        "--fail-threshold", type=float, default=0.10,
        help="exit non-zero only when fail ratio exceeds this fraction (default 0.10)",
    )
    p_extract.add_argument(
        "--concurrency", type=int, default=4,
        help="max parallel API calls (default 4; tier 1 ITPM caps Sonnet around 5)",
    )
    p_extract.add_argument(
        "--few-shot", type=int, default=0,
        help=(
            "prepend N hand-verified (image, position) examples to every API "
            "call (default 0). Examples live in "
            "pedagogy/tests/fixtures/dubois_ground_truth.py."
        ),
    )
    p_extract.set_defaults(func=cmd_extract)

    p_materialize = sub.add_parser(
        "materialize",
        help="write the Python fixtures file from extracted JSON",
    )
    p_materialize.add_argument("--cache", default=str(DEFAULT_CACHE))
    p_materialize.add_argument("--output", default=str(DEFAULT_OUTPUT))
    p_materialize.set_defaults(func=cmd_materialize)

    p_all = sub.add_parser("all", help="run render + extract + materialize")
    p_all.add_argument("--pdf", required=True)
    p_all.add_argument("--pages", default="all")
    p_all.add_argument("--cache", default=str(DEFAULT_CACHE))
    p_all.add_argument("--dpi", type=int, default=DEFAULT_DPI)
    p_all.add_argument("--model", default=DEFAULT_MODEL)
    p_all.add_argument("--output", default=str(DEFAULT_OUTPUT))
    p_all.add_argument("--max-diagrams", type=int, default=0)
    p_all.add_argument("--fail-threshold", type=float, default=0.10)
    p_all.add_argument("--concurrency", type=int, default=4)
    p_all.add_argument("--few-shot", type=int, default=0)
    p_all.add_argument("--force", action="store_true")
    p_all.add_argument("--verbose", action="store_true")
    p_all.set_defaults(func=lambda a: _cmd_all(a))
    return parser


def _cmd_all(args: argparse.Namespace) -> int:
    r1 = cmd_render(args)
    if r1:
        return r1
    args.dry_run = False
    r2 = cmd_extract(args)
    if r2:
        return r2
    return cmd_materialize(args)


def main(argv: Optional[list[str]] = None) -> int:
    # Bind required tools eagerly so the error message is clear.
    for tool in ("pdftoppm", "pdftotext", "pdfinfo"):
        if shutil.which(tool) is None:
            print(f"required system tool not found in PATH: {tool}", file=sys.stderr)
            return 2
    args = _build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

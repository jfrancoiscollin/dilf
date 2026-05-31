"""Goedemoed 'A Course in Draughts' diagram extractor.

Reuses the proven dilf strategy detector (scripts.extract_diagrams) — the
same pixel-sampling system that reached ~99.86% per-square accuracy on
Sijbrands/Springer/Roozenburg — with the few constants retuned for
Goedemoed's gray-checkerboard workbook diagrams:

  * render at 300 dpi (boards ~568 px, vs Dubois' larger boards)
  * MIN_BOARD_AREA lowered to 100k
  * black pieces are mid-gray discs -> black_threshold ~165 (not 90)
  * white pieces are bright discs -> white_threshold ~215

Goedemoed pages have no French "trait aux noirs" captions, so we bypass the
caption gating and process an explicit page range, detecting every board.

Subcommands:
  crops   render pages -> individual board crops + manifest.json (with a
          starter auto-FEN per crop for the human to correct into ground truth)
  score   compare auto-FENs against a ground-truth JSON, per-square accuracy,
          and sweep thresholds to find the best (used while tuning to >99%).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # dilf root
import numpy as np
from PIL import Image, ImageDraw
import scripts.extract_diagrams as E

# Retuned constants for Goedemoed
DPI = 300
MIN_BOARD_AREA = 100_000
WHITE_THR = 215.0
BLACK_THR = 165.0
SAMPLE_RADIUS = 10

CORPUS = Path("/home/user/dilf/docs/corpus")


def _fen(white: list[int], black: list[int], turn: str = "W") -> str:
    return f"{turn}:W{','.join(map(str, white))}:B{','.join(map(str, black))}"


def detect_page(pdf: Path, page: int, cache: Path):
    """Render one page at DPI, detect boards, return (gray_array, [bbox])."""
    pages_dir = cache / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    png = pages_dir / f"{pdf.stem}_p{page:03d}.png"
    if not png.exists():
        E._render_page_png(pdf, page, DPI, png)
    E.MIN_BOARD_AREA = MIN_BOARD_AREA
    boards = E._detect_boards(png)
    gray = np.array(Image.open(png).convert("L"))
    return gray, boards, png


def analyze(gray, bbox, white_thr=WHITE_THR, black_thr=BLACK_THR, radius=SAMPLE_RADIUS):
    return E.analyze_board_fen(
        gray, bbox, white_threshold=white_thr, black_threshold=black_thr,
        sample_radius=radius,
    )


def cmd_crops(args):
    pdf = CORPUS / args.pdf
    cache = Path(args.out)
    crops_dir = cache / "crops"
    crops_dir.mkdir(parents=True, exist_ok=True)
    pages = [int(p) for p in args.pages.split(",")] if "," in args.pages else \
        list(range(int(args.pages.split("-")[0]), int(args.pages.split("-")[1]) + 1))

    manifest = []
    tiles = []
    for page in pages:
        gray, boards, _ = detect_page(pdf, page, cache)
        for idx, bbox in enumerate(boards):
            cid = f"{pdf.stem}_p{page:03d}_d{idx + 1:02d}"
            x1, y1, x2, y2 = bbox
            crop = Image.fromarray(gray[y1:y2, x1:x2].astype("uint8"))
            crop_path = crops_dir / f"{cid}.png"
            crop.save(crop_path)
            white, black = analyze(gray, bbox)
            manifest.append({
                "id": cid, "pdf": pdf.name, "page": page, "region_index": idx,
                "bbox": list(bbox),
                "auto_fen": _fen(white, black),
                "fen": _fen(white, black),  # <- human corrects THIS field
            })
            tiles.append((cid, crop.resize((220, 220))))

    (cache / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    # contact sheet
    cols = 4
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 230, rows * 250), "white")
    d = ImageDraw.Draw(sheet)
    for i, (cid, im) in enumerate(tiles):
        x, y = (i % cols) * 230, (i // cols) * 250
        sheet.paste(im.convert("RGB"), (x + 5, y + 25))
        d.text((x + 5, y + 8), cid.split("_", 1)[1], fill="black")
    sheet.save(cache / "contact_sheet.png")
    print(f"crops: {len(manifest)} -> {cache}/crops/  (+ manifest.json, contact_sheet.png)")


def cmd_score(args):
    """Compare auto-FEN to ground-truth JSON; per-square accuracy + threshold sweep."""
    cache = Path(args.out)
    manifest = json.loads((cache / "manifest.json").read_text())
    truth = json.loads(Path(args.truth).read_text())
    truth_by_id = {t["id"]: t["fen"] for t in (truth if isinstance(truth, list) else truth.values())} \
        if isinstance(truth, list) else {k: v for k, v in truth.items()}

    def squares(fen):
        # parse "W:Wa,b:Bc,d" -> dict square->'W'/'B'
        out = {}
        for part in fen.split(":")[1:]:
            color = part[0]
            for n in part[1:].split(","):
                if n.strip():
                    out[int(n)] = color
        return out

    pdfs = {m["pdf"] for m in manifest}
    best = None
    for wt in [args.white] if args.white else [205, 210, 215, 220, 225]:
        for bt in [args.black] if args.black else [150, 160, 165, 170, 180]:
            total = correct = 0
            mism = []
            for m in manifest:
                if m["id"] not in truth_by_id:
                    continue
                gray, _, _ = detect_page(CORPUS / m["pdf"], m["page"], cache)
                w, b = analyze(gray, tuple(m["bbox"]), white_thr=wt, black_thr=bt)
                got = {**{s: "W" for s in w}, **{s: "B" for s in b}}
                exp = squares(truth_by_id[m["id"]])
                for sq in range(1, 51):
                    total += 1
                    if got.get(sq, ".") == exp.get(sq, "."):
                        correct += 1
                    else:
                        mism.append((m["id"], sq, exp.get(sq, "."), got.get(sq, ".")))
            acc = correct / total if total else 0
            tag = f"W>{wt} B<{bt}: {acc*100:.2f}% ({correct}/{total})"
            print(tag)
            if best is None or acc > best[0]:
                best = (acc, wt, bt, mism)
    if best:
        acc, wt, bt, mism = best
        print(f"\nBEST: white>{wt} black<{bt} -> {acc*100:.2f}%  mismatches={len(mism)}")
        for mm in mism[:40]:
            print("  ", mm)


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    pc = sub.add_parser("crops"); pc.add_argument("--pdf", required=True)
    pc.add_argument("--pages", required=True, help="e.g. 9-13 or 9,11,13")
    pc.add_argument("--out", default="/tmp/goed_crops")
    pc.set_defaults(func=cmd_crops)
    ps = sub.add_parser("score"); ps.add_argument("--truth", required=True)
    ps.add_argument("--out", default="/tmp/goed_crops")
    ps.add_argument("--white", type=float); ps.add_argument("--black", type=float)
    ps.set_defaults(func=cmd_score)
    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

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
#: Largest plausible single board at 200 dpi (~460 px, deel 1-6 full-page
#: diagrams ~205k px^2) — rejects page-wide blobs snapped into squares.
MAX_BOARD_AREA_PCBLUES = 300_000
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
    #: Dames détectées (rendu bleu : pièces double-empilées, extension
    #: verticale > 0.60 case vs ~0.51 pour un pion). Vide pour les rendus
    #: sans détection de dames.
    white_kings: tuple[int, ...] = ()
    black_kings: tuple[int, ...] = ()


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


def _shrink(
    arr,
    bbox: tuple[int, int, int, int],
    dark: float = 120.0,
    density: float = 0.55,
) -> tuple[int, int, int, int]:
    """Tighten a blob bbox to its board-border rectangle.

    Like ``extract_diagrams._shrink_to_border`` but calibrated for the small
    PC Blues grid diagrams whose thin borders are anti-aliased (~90-115 gray,
    above the Dubois threshold of 80) and spread over two pixel columns.
    A degenerate result (< 50 % of the original size — the scan latched on
    a caption line instead of a border) falls back to the input bbox.
    """
    import numpy as np

    left, top, right, bottom = bbox
    region = arr[top:bottom, left:right]
    h, w = region.shape
    if h < 20 or w < 20:
        return bbox
    is_dark = region < dark
    rows = is_dark.sum(axis=1) / max(w, 1)
    cols = is_dark.sum(axis=0) / max(h, 1)

    def first(values) -> int:
        idx = int(np.argmax(values >= density))
        return idx if values[idx] >= density else 0

    t_off, b_off = first(rows), first(rows[::-1])
    l_off, r_off = first(cols), first(cols[::-1])
    new = (left + l_off, top + t_off, right - r_off, bottom - b_off)
    nw, nh = new[2] - new[0], new[3] - new[1]
    if nw < 0.5 * w or nh < 0.5 * h or nw <= 0 or nh <= 0:
        return bbox
    return new


def _shrink_with_found(
    arr, bbox: tuple[int, int, int, int]
) -> tuple[tuple[int, int, int, int], set[str]]:
    """:func:`_shrink` + which borders were actually located.

    A border scan that stays at offset 0 either had the border flush with
    the blob edge (fine) or simply failed to find it (dashed borders of the
    Vaardigheidstesten rendering) — flagged so `_snap_square` knows which
    dimension to trust.
    """
    import numpy as np

    left, top, right, bottom = bbox
    region = arr[top:bottom, left:right]
    h, w = region.shape
    if h < 20 or w < 20:
        return bbox, set()
    # < 140 : attrape les bordures pointillées grises (Vaardigheidstesten)
    # sans accrocher les cases sombres des autres rendus (bois 150-190,
    # gris 192) ; les rangées hachurées plafonnent ~0.50 < 0.60.
    is_dark = region < 140.0
    rows = is_dark.sum(axis=1) / max(w, 1)
    cols = is_dark.sum(axis=0) / max(h, 1)

    def first(values) -> tuple[int, bool]:
        idx = int(np.argmax(values >= 0.60))
        ok = bool(values[idx] >= 0.60)
        return (idx if ok else 0), ok

    (t_off, t_ok) = first(rows)
    (b_off, b_ok) = first(rows[::-1])
    (l_off, l_ok) = first(cols)
    (r_off, r_ok) = first(cols[::-1])
    # Chaque côté est accepté INDÉPENDAMMENT : un scan qui traverse la
    # moitié du blob a raté sa bordure (il a accroché la bordure opposée
    # ou une légende) — ce côté reste au bord du blob, non-trouvé.
    if t_ok and t_off > 0.5 * h:
        t_off, t_ok = 0, False
    if b_ok and b_off > 0.5 * h:
        b_off, b_ok = 0, False
    if l_ok and l_off > 0.5 * w:
        l_off, l_ok = 0, False
    if r_ok and r_off > 0.5 * w:
        r_off, r_ok = 0, False

    # Seconde chance pour un côté manquant : bordure faible (~50% de
    # densité, rendu Vaardigheidstesten) — seuil 0.42, acceptée seulement
    # près du bord du blob (< 15%), là où les rangées hachurées internes
    # ne peuvent pas être confondues avec elle.
    def second(values, dim: int) -> tuple[int, bool]:
        idx = int(np.argmax(values >= 0.42))
        ok = bool(values[idx] >= 0.42) and idx < 0.15 * dim
        return (idx if ok else 0), ok

    if not t_ok:
        t_off, t_ok = second(rows, h)
    if not b_ok:
        b_off, b_ok = second(rows[::-1], h)
    if not l_ok:
        l_off, l_ok = second(cols, w)
    if not r_ok:
        r_off, r_ok = second(cols[::-1], w)
    new = (left + l_off, top + t_off, right - r_off, bottom - b_off)
    if new[2] <= new[0] or new[3] <= new[1]:
        return bbox, set()
    found = {
        name
        for name, ok in (("top", t_ok), ("bottom", b_ok), ("left", l_ok), ("right", r_ok))
        if ok
    }
    return new, found


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
    inner = _shrink(arr, (x1 + inset, y1 + inset, x2 - inset, y2 - inset))
    iw, ih = inner[2] - inner[0], inner[3] - inner[1]
    w, h = x2 - x1, y2 - y1
    moved = max(
        inner[0] - (x1 + inset), inner[1] - (y1 + inset),
        (x2 - inset) - inner[2], (y2 - inset) - inner[3],
    )
    if moved > 0.02 * min(w, h) and iw > 0.75 * w and ih > 0.75 * h:
        return inner
    return bbox


def _snap_square(
    tight: tuple[int, int, int, int],
    blob: tuple[int, int, int, int],
    found: set[str],
) -> tuple[int, int, int, int]:
    """Boards are square: when a border was NOT located (dashed bottom of
    the Vaardigheidstesten rendering, caption latched into the blob), the
    trusted dimension re-derives the missing side.
    """
    x1, y1, x2, y2 = tight
    w, h = x2 - x1, y2 - y1
    all_found = {"top", "bottom", "left", "right"} <= found
    if w <= 0 or h <= 0 or all_found or abs(w - h) <= 2:
        return tight
    # Le blob peut mordre légèrement à côté de la vraie bordure (dilatation,
    # label collé) : la reconstruction par carré peut déborder du blob de
    # quelques pixels.
    slack = 15
    width_ok = {"left", "right"} <= found
    height_ok = {"top", "bottom"} <= found
    if width_ok and not height_ok:
        if "top" in found or "bottom" not in found:
            y2 = min(y1 + w, blob[3] + slack)
        else:
            y1 = max(y2 - w, blob[1] - slack)
    elif height_ok and not width_ok:
        if "left" in found or "right" not in found:
            x2 = min(x1 + h, blob[2] + slack)
        else:
            x1 = max(x2 - h, blob[0] - slack)
    elif h > w:
        # Aucun bord fiable (bordures pointillées des Vaardigheidstesten) :
        # dans tout le corpus la légende est SOUS le diagramme — le plateau
        # est le carré ancré en haut du blob.
        y2 = min(y1 + w, blob[3])
    return (x1, y1, x2, y2)


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
            tight, found = _shrink_with_found(arr, (cl, ct, cr, cb))
            tight = _inner_border(arr, tight)
            tight = _snap_square(tight, (cl, ct, cr, cb), found)
            tw, th = tight[2] - tight[0], tight[3] - tight[1]
            if not (MIN_BOARD_AREA_PCBLUES <= tw * th <= MAX_BOARD_AREA_PCBLUES):
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

    PC Blues spans (at least) three renderings — wooden boards (deel <= 35),
    gray-checkered (Klubkompetitie 37+), hatched squares with ring-drawn
    white pieces (Vaardigheidstesten 47/57) — so fixed thresholds don't
    transfer. Classification is **adaptive per board**: empty playable
    squares are the majority, so the median (mean, min) over non-black
    squares is the empty baseline, and a white piece deviates from it —
    much brighter (bois : disque 227 vs fond 172) or with dark ring/shading
    pixels (gris : min 21 vs 192 ; hachuré : min ~50 vs ~150).

    * black piece: mean < 90 (universal),
    * white piece: mean > baseline_mean + 40 OR min < baseline_min - 45,
    * empty otherwise.
    """
    import numpy as np

    x1, y1, x2, y2 = bbox
    x1i, y1i = x1 + FEN_MARGIN_PX, y1 + FEN_MARGIN_PX
    bw = (x2 - x1) - 2 * FEN_MARGIN_PX
    bh = (y2 - y1) - 2 * FEN_MARGIN_PX
    h, w = gray.shape
    stats: dict[int, tuple[float, float]] = {}
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
            stats[sq] = (float(patch.mean()), float(patch.min()))

    black_sqs = sorted(sq for sq, (m, _) in stats.items() if m < 90.0)
    # Règle fixe validée sur 3639 combos (bois: disque clair mean>200 ;
    # gris: anneau min<112 sur case claire). Le rendu hachuré passe par
    # :func:`analyze_board_band` (variantes arbitrées par re-jeu).
    white_sqs = sorted(
        sq
        for sq, (m, mn) in stats.items()
        if m >= 90.0 and (m > 200.0 or (m > 150.0 and mn < 112.0))
    )
    return white_sqs, black_sqs


def piece_vertical_extent(gray, bbox: tuple[int, int, int, int], sq: int) -> float:
    """Normalized vertical extent of the piece blob on ``sq`` (0..~1).

    A dame is drawn as a double-stacked disc, so its piece-material spans
    more of the cell height than a man's single disc. The measure is
    border-safe (baseline = median of the cell's four corners, always
    board colour) but confounded by colour (solid black discs read taller
    than white rings) and by board-edge frame — so it is a RANKING signal,
    not an absolute classifier. King status is decided by
    :mod:`scripts.pcblues.extract_endgames`, arbitrated by replay.
    """
    import numpy as np

    x1, y1, x2, y2 = bbox
    bw = (x2 - x1) / 10.0
    bh = (y2 - y1) / 10.0
    rc = _square_rowcol(sq)
    if rc is None:
        return 0.0
    row, col = rc
    cy0, cy1 = int(y1 + row * bh), int(y1 + (row + 1) * bh)
    cx0, cx1 = int(x1 + col * bw), int(x1 + (col + 1) * bw)
    cell = gray[cy0:cy1, cx0:cx1]
    if cell.size == 0 or cell.shape[0] < 10:
        return 0.0
    hgt, wid = cell.shape
    k = max(2, hgt // 6)
    corners = np.concatenate(
        [
            cell[:k, :k].ravel(),
            cell[:k, -k:].ravel(),
            cell[-k:, :k].ravel(),
            cell[-k:, -k:].ravel(),
        ]
    )
    base = float(np.median(corners))
    center_cols = cell[:, wid // 4 : 3 * wid // 4]
    mask = np.abs(center_cols - base) > 45.0
    rows = np.where(mask.sum(axis=1) >= center_cols.shape[1] * 0.35)[0]
    if len(rows) < 2:
        return 0.0
    return float(rows.max() - rows.min() + 1) / hgt


def _square_rowcol(sq: int) -> tuple[int, int] | None:
    for row in range(10):
        for col in range(10):
            if _square_number(row, col) == sq:
                return row, col
    return None


def analyze_board_band(
    gray, bbox: tuple[int, int, int, int]
) -> tuple[list[int], list[int]]:
    """Classifieur « bande 3D » (rendu Vaardigheidstesten deel 47).

    Les pièces y sont des anneaux dont seul le flanc 3D est dense : une
    bande sombre (min < 60) au BAS de la case. Présence = bande sombre en
    bas de case ; couleur = luminosité du centre (disque noir assombrit le
    centre ~145 vs vide hachuré ~195 vs anneau blanc ~210).
    """
    x1, y1, x2, y2 = bbox
    bw, bh = (x2 - x1), (y2 - y1)
    h, w = gray.shape
    white_sqs: list[int] = []
    black_sqs: list[int] = []
    for row in range(10):
        for col in range(10):
            sq = _square_number(row, col)
            if sq is None:
                continue
            cx = x1 + (col + 0.5) * bw / 10.0
            cy_band = y1 + (row + 0.78) * bh / 10.0  # flanc 3D du disque
            cy_mid = y1 + (row + 0.5) * bh / 10.0
            band = gray[
                max(0, int(cy_band - 5)) : min(h, int(cy_band + 5)),
                max(0, int(cx - 9)) : min(w, int(cx + 9)),
            ]
            mid = gray[
                max(0, int(cy_mid - 7)) : min(h, int(cy_mid + 7)),
                max(0, int(cx - 7)) : min(w, int(cx + 7)),
            ]
            if band.size == 0 or mid.size == 0:
                continue
            if float(band.min()) < 60.0 and (band < 80.0).sum() >= 10:
                # disque noir : flanc dense ET centre assombri
                if float(mid.mean()) < 178.0:
                    black_sqs.append(sq)
                    continue
            # anneau blanc : contour sombre traversant le patch central
            # d'une case claire (vide hachuré : min >= ~160)
            if float(mid.min()) < 130.0 and float(mid.mean()) > 183.0:
                white_sqs.append(sq)
    return sorted(white_sqs), sorted(black_sqs)


def detect_boards_color(image_path: Path) -> list[tuple[int, int, int, int]]:
    """Détection des plateaux BLEUS sans bordure (deel 1-2, rendu 2009-10).

    Ces volumes dessinent des damiers bleu clair / bleu moyen sans cadre
    noir : le masque « sombre » ne voit rien. Le plateau est en revanche
    une grande région à dominance bleue (B − R > 15 sur ~85 % des pixels,
    contre ~0 sur le fond blanc de la page).
    """
    import numpy as np
    from PIL import Image
    from scipy import ndimage

    rgb = np.asarray(Image.open(image_path).convert("RGB"), dtype=int)
    mask = (rgb[:, :, 2] - rgb[:, :, 0]) > 15
    dilated = ndimage.binary_dilation(mask, iterations=3)
    labeled, _ = ndimage.label(dilated)
    boards: list[tuple[int, int, int, int]] = []
    for sl in ndimage.find_objects(labeled):
        if sl is None:
            continue
        top, bottom = sl[0].start, sl[0].stop
        left, right = sl[1].start, sl[1].stop
        w, h = right - left, bottom - top
        if not (MIN_BOARD_AREA_PCBLUES <= w * h <= MAX_BOARD_AREA_PCBLUES):
            continue
        if not (BOARD_ASPECT_RANGE[0] <= w / h <= BOARD_ASPECT_RANGE[1]):
            continue
        boards.append((left + 3, top + 3, right - 3, bottom - 3))
    boards.sort(key=lambda b: (b[1] // 120, b[0]))
    return boards


def analyze_board_color(
    rgb, bbox: tuple[int, int, int, int]
) -> tuple[list[int], list[int], list[int], list[int]]:
    """Classification couleur (rendu bleu deel 1-2, 5…), dames comprises.

    Pièces du camp noir = ORANGE (R − B fortement positif) ; pièces
    blanches = disques clairs quasi neutres ; cases vides = bleues
    (B − R ~ +20). Les DAMES sont des pièces double-empilées : l'extension
    verticale des pixels de pièce dans la case dépasse 0.60 (pion ~0.51,
    dame ~0.70 — mesuré deel 5).

    Returns ``(white_men, black_men, white_kings, black_kings)``.
    """
    import numpy as np

    x1, y1, x2, y2 = bbox
    bw, bh = (x2 - x1) / 10.0, (y2 - y1) / 10.0
    white_men: list[int] = []
    black_men: list[int] = []
    white_kings: list[int] = []
    black_kings: list[int] = []
    for row in range(10):
        for col in range(10):
            sq = _square_number(row, col)
            if sq is None:
                continue
            cell = rgb[
                int(y1 + row * bh) : int(y1 + (row + 1) * bh),
                int(x1 + col * bw) : int(x1 + (col + 1) * bw),
            ]
            if cell.size == 0:
                continue
            orange = (cell[:, :, 0] - cell[:, :, 2]) > 60
            whiteish = (np.abs(cell[:, :, 0] - cell[:, :, 2]) < 18) & (
                cell.mean(axis=2) > 195.0
            )
            for mask, men, kings in (
                (orange, black_men, black_kings),
                (whiteish, white_men, white_kings),
            ):
                if mask.sum() < 60:
                    continue
                ys = np.where(mask.any(axis=1))[0]
                extent = (ys.max() - ys.min() + 1) / bh
                (kings if extent > 0.60 else men).append(sq)
                break
    return sorted(white_men), sorted(black_men), sorted(white_kings), sorted(black_kings)


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

    bboxes = detect_boards(png)
    if not bboxes:
        # Rendu bleu sans bordure (deel 1-2) : détection + classification
        # par couleur.
        color_boxes = detect_boards_color(png)
        if color_boxes:
            rgb = np.asarray(Image.open(png).convert("RGB"), dtype=int)
            out_c: list[DetectedBoard] = []
            for idx, bbox in enumerate(color_boxes):
                wm, bm, wk, bk = analyze_board_color(rgb, bbox)
                out_c.append(
                    DetectedBoard(
                        page=page, index=idx, bbox=bbox,
                        white_men=tuple(wm), black_men=tuple(bm),
                        white_kings=tuple(wk), black_kings=tuple(bk),
                    )
                )
            return out_c

    # Un plateau détecté par bordure peut quand même être un damier BLEU à
    # pièces couleur (deel 5+) : la dominance bleue de la région tranche
    # (bois = R-dominant, gris/hachuré = neutre, bleu = B-dominant).
    rgb = None
    out: list[DetectedBoard] = []
    for idx, bbox in enumerate(bboxes):
        x1b, y1b, x2b, y2b = bbox
        if rgb is None:
            rgb = np.asarray(Image.open(png).convert("RGB"), dtype=int)
        region = rgb[y1b:y2b, x1b:x2b]
        blue_frac = float(((region[:, :, 2] - region[:, :, 0]) > 15).mean())
        if blue_frac > 0.5:
            wm, bm, wk, bk = analyze_board_color(rgb, bbox)
            out.append(
                DetectedBoard(
                    page=page, index=idx, bbox=bbox,
                    white_men=tuple(wm), black_men=tuple(bm),
                    white_kings=tuple(wk), black_kings=tuple(bk),
                )
            )
            continue
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

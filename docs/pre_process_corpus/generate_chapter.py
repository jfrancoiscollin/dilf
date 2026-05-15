"""Génération industrielle de fixtures depuis le pipeline dilf.

Pattern issu du cycle de production du manuel Débutant (cf §0 et §5 du
CADRAGE_MANUELS.md). Conçu pour être réutilisé tel quel sur les manuels
Intermédiaire / Avancé / Expert.

Usage:
    python generate_chapter.py <chapter_def.py> [> out.py]

Le fichier <chapter_def.py> doit définir :

    WRAPPER_CLASS = "IntermediatePosition"   # ou "BeginnerPosition", etc.
    SELECTION = [
        (fixture_id, page, region, notation, has_king_rafle, meta_dict),
        ...
    ]

où `meta_dict` contient au minimum les clés :
    theme, title, concept, explanation, source_ref, crop_id
et optionnellement : notes (alias : claude_notes).

Le script :
  1. Charge les positions extraites par `scripts/extract_diagrams.py`
     (lit `ALL_DIAGRAMS` depuis `pedagogy/tests/fixtures/dubois_diagrams.py`).
  2. Re-joue la `published_notation` via `pedagogy.notation.dubois`
     (dispatcher unifié — supporte pions ET dames depuis PR #32).
  3. Reconstruit le `final_move`.
  4. Émet le code Python des fixtures sur stdout.
  5. Reporte les erreurs sur stderr (pour traitement §4.13 ou §4.11).

Configuration des chemins :
  - Définir la variable d'environnement DILF_ROOT pour pointer vers le
    repo dilf clôné (ex: DILF_ROOT=/home/user/dilf python generate_chapter.py ...).
  - À défaut, le script cherche dilf dans ./dilf puis ../dilf.
"""
from __future__ import annotations

import importlib.util
import os
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Configuration des chemins dilf
# ---------------------------------------------------------------------------

def _find_dilf_root() -> Path:
    """Localise le repo dilf via DILF_ROOT, ./dilf ou ../dilf."""
    env = os.environ.get("DILF_ROOT")
    if env:
        p = Path(env).resolve()
        if (p / "pedagogy" / "game.py").exists():
            return p
        sys.exit(f"❌ DILF_ROOT={env} ne contient pas pedagogy/game.py")
    here = Path.cwd().resolve()
    for cand in (here / "dilf", here.parent / "dilf", here):
        if (cand / "pedagogy" / "game.py").exists():
            return cand
    sys.exit(
        "❌ dilf non trouvé. Cloner https://github.com/jfrancoiscollin/dilf "
        "et définir DILF_ROOT=/chemin/vers/dilf."
    )


DILF_ROOT = _find_dilf_root()
sys.path.insert(0, str(DILF_ROOT))
sys.path.insert(0, str(DILF_ROOT / "pedagogy" / "tests" / "fixtures"))

from pedagogy.game import GameState, Move  # noqa: E402
from pedagogy.notation.dubois import (  # noqa: E402
    reconstruct_capture,
    NoSuchRafleError,
    AmbiguousRafleError,
    NotAManError,
    NotAKingError,
)

if "dubois_diagrams" in sys.modules:
    del sys.modules["dubois_diagrams"]
from dubois_diagrams import ALL_DIAGRAMS  # noqa: E402


# ---------------------------------------------------------------------------
# Application d'un coup à un GameState
# ---------------------------------------------------------------------------

def apply_simple(state: GameState, frm: int, to: int) -> GameState:
    """Applique un coup simple (non capturant) — pion ou dame, blanc ou noir."""
    if frm in state.white_men:
        return GameState(
            white_men=(state.white_men - {frm}) | {to},
            white_kings=state.white_kings,
            black_men=state.black_men,
            black_kings=state.black_kings,
            turn="black",
        )
    if frm in state.black_men:
        return GameState(
            white_men=state.white_men,
            white_kings=state.white_kings,
            black_men=(state.black_men - {frm}) | {to},
            black_kings=state.black_kings,
            turn="white",
        )
    if frm in state.white_kings:
        return GameState(
            white_men=state.white_men,
            white_kings=(state.white_kings - {frm}) | {to},
            black_men=state.black_men,
            black_kings=state.black_kings,
            turn="black",
        )
    if frm in state.black_kings:
        return GameState(
            white_men=state.white_men,
            white_kings=state.white_kings,
            black_men=state.black_men,
            black_kings=(state.black_kings - {frm}) | {to},
            turn="white",
        )
    raise ValueError(f"aucune piece en {frm}")


def apply_capture(state: GameState, move: Move) -> GameState:
    """Applique une rafle (Move avec captures non vides)."""
    captures = set(move.captures)
    frm = move.from_square
    to = move.to_square
    if frm in state.white_men:
        return GameState(
            white_men=(state.white_men - {frm}) | {to},
            white_kings=state.white_kings,
            black_men=state.black_men - captures,
            black_kings=state.black_kings - captures,
            turn="black",
        )
    if frm in state.black_men:
        return GameState(
            white_men=state.white_men - captures,
            white_kings=state.white_kings - captures,
            black_men=(state.black_men - {frm}) | {to},
            black_kings=state.black_kings,
            turn="white",
        )
    if frm in state.white_kings:
        return GameState(
            white_men=state.white_men,
            white_kings=(state.white_kings - {frm}) | {to},
            black_men=state.black_men - captures,
            black_kings=state.black_kings - captures,
            turn="black",
        )
    if frm in state.black_kings:
        return GameState(
            white_men=state.white_men - captures,
            white_kings=state.white_kings - captures,
            black_men=state.black_men,
            black_kings=(state.black_kings - {frm}) | {to},
            turn="white",
        )
    raise ValueError(f"aucune piece en {frm}")


# ---------------------------------------------------------------------------
# Parsing de la notation Dubois
# ---------------------------------------------------------------------------

def parse_tokens(notation: str) -> list[tuple[str, int | None, int | None]]:
    """Tokenise une notation Dubois en (kind, from, to).

    kind in {'simple', 'reply_simple', 'capture', 'reply_capture', 'ad_lib'}
    'reply_*' correspond a un coup adverse (entre parentheses).
    'ad_lib' = '(ad lib)' (cf 5.1 backlog dilf) -> from/to = None.
    """
    out: list[tuple[str, int | None, int | None]] = []
    tokens = re.findall(r"\([^)]+\)|\S+", notation)
    for tok in tokens:
        inside = tok.startswith("(") and tok.endswith(")")
        body = tok[1:-1] if inside else tok
        if "ad lib" in body.lower():
            out.append(("ad_lib", None, None))
            continue
        if "-" not in body and "x" not in body:
            continue
        if " " in body or any(c.isalpha() for c in body.replace("x", "").replace("-", "")):
            continue
        if "-" in body:
            f, t = body.split("-")
            out.append(("reply_simple" if inside else "simple", int(f), int(t)))
        elif "x" in body:
            parts = body.split("x")
            out.append(("reply_capture" if inside else "capture", int(parts[0]), int(parts[-1])))
    return out


# ---------------------------------------------------------------------------
# Reconstruction d'une fixture
# ---------------------------------------------------------------------------

def reconstruct_fixture(
    page: int,
    region: int,
    notation: str,
    has_king_rafle_flag: bool,
) -> tuple[GameState | None, Move | None, str | None]:
    """Reconstruit (initial_state, final_move, error_msg).

    has_king_rafle_flag : si True, force final_move=None (utilise quand on
    sait a l'avance qu'une rafle de dame est en jeu et qu'on prefere ne
    pas tenter la reconstruction -- utile pour les gambits, envois a dame
    sans rafle finale claire, etc.).

    Avec PR #32, la plupart des rafles de dame se reconstruisent
    automatiquement via reconstruct_capture (dispatcher unifie). Le flag
    reste utile pour les gambits.
    """
    matches = [d for d in ALL_DIAGRAMS if d.page == page and d.region_index == region]
    if not matches:
        return None, None, f"no diagram page={page} region={region}"
    diag = matches[0]
    initial = GameState(
        white_men=frozenset(diag.white_men),
        white_kings=frozenset(diag.white_kings),
        black_men=frozenset(diag.black_men),
        black_kings=frozenset(diag.black_kings),
        turn=diag.turn,
    )
    if has_king_rafle_flag:
        return initial, None, None

    try:
        cur = initial
        final: Move | None = None
        for kind, frm, to in parse_tokens(notation):
            if kind == "ad_lib":
                # Applique la premiere capture forcee disponible.
                if cur.turn == "white":
                    my_pieces = cur.white_men | cur.white_kings
                else:
                    my_pieces = cur.black_men | cur.black_kings
                found = False
                for sq in sorted(my_pieces):
                    for target in range(1, 51):
                        if target == sq:
                            continue
                        try:
                            m = reconstruct_capture(cur, sq, target)
                            cur = apply_capture(cur, m)
                            found = True
                            break
                        except (NoSuchRafleError, AmbiguousRafleError,
                                NotAManError, NotAKingError, ValueError):
                            continue
                    if found:
                        break
                if not found:
                    return initial, None, "ad_lib: aucune capture forcee trouvee"
                continue

            if kind in ("simple", "reply_simple"):
                cur = apply_simple(cur, frm, to)
            else:
                assert frm is not None and to is not None
                m = reconstruct_capture(cur, frm, to)
                is_active_side = (
                    (initial.turn == "white" and kind == "capture")
                    or (initial.turn == "black" and kind == "reply_capture")
                )
                if is_active_side:
                    final = m
                cur = apply_capture(cur, m)
        return initial, final, None
    except (NoSuchRafleError, AmbiguousRafleError, NotAManError, NotAKingError, ValueError) as e:
        return initial, None, f"{type(e).__name__}: {e}"


# ---------------------------------------------------------------------------
# Emission du code Python d'une fixture
# ---------------------------------------------------------------------------

def emit_fixture(
    wrapper_class: str,
    fixture_id: str,
    initial: GameState,
    final_move: Move | None,
    notation: str,
    meta: dict,
) -> str:
    """Genere le code Python d'une fixture."""
    notes = meta.get("notes") or meta.get("claude_notes") or ""
    lines = []
    lines.append(f"{fixture_id} = {wrapper_class}(")
    lines.append(f'    id="{fixture_id}",')
    lines.append(f'    theme="{meta["theme"]}",')
    lines.append(f'    title={meta["title"]!r},')
    lines.append('    state=GameState(')
    lines.append(f'        white_men=frozenset({set(initial.white_men)}),')
    if initial.white_kings:
        lines.append(f'        white_kings=frozenset({set(initial.white_kings)}),')
    lines.append(f'        black_men=frozenset({set(initial.black_men)}),')
    if initial.black_kings:
        lines.append(f'        black_kings=frozenset({set(initial.black_kings)}),')
    lines.append(f'        turn="{initial.turn}",')
    lines.append('    ),')
    lines.append(f'    concept={meta["concept"]!r},')
    lines.append(f'    published_notation={notation!r},')
    if final_move is None:
        lines.append('    final_move=None,')
    else:
        lines.append('    final_move=Move(')
        lines.append(f'        path={tuple(final_move.path)},')
        lines.append(f'        captures={tuple(final_move.captures)},')
        lines.append('    ),')
    lines.append(f'    explanation={meta["explanation"]!r},')
    lines.append('    source=SourceType.CORPUS,')
    lines.append(f'    source_ref={meta["source_ref"]!r},')
    lines.append(f'    crop_id={meta["crop_id"]!r},')
    lines.append('    confidence="high",')
    if notes:
        lines.append(f'    claude_notes={notes!r},')
    lines.append(')\n')
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        sys.exit(1)

    chapter_def_path = sys.argv[1]
    spec = importlib.util.spec_from_file_location("chapter_def", chapter_def_path)
    if spec is None or spec.loader is None:
        sys.exit(f"impossible de charger {chapter_def_path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    wrapper_class = getattr(mod, "WRAPPER_CLASS", "BeginnerPosition")
    selection = mod.SELECTION

    out_lines: list[str] = []
    errors: list[tuple] = []
    n_ok = 0
    n_nofm = 0

    for fixture_id, page, region, notation, has_king, meta in selection:
        initial, final, err = reconstruct_fixture(page, region, notation, has_king)
        if err:
            errors.append((fixture_id, page, region, err, notation))
            print(f"  KO {fixture_id}: {err}", file=sys.stderr)
            continue
        if final:
            n_ok += 1
            print(f"  OK {fixture_id} -> {final.from_square}x{final.to_square}", file=sys.stderr)
        else:
            n_nofm += 1
            print(f"  -- {fixture_id} -> final_move=None", file=sys.stderr)
        out_lines.append(emit_fixture(wrapper_class, fixture_id, initial, final, notation, meta))

    print("\n".join(out_lines))

    print(file=sys.stderr)
    print(f"=== Bilan : {n_ok} reconstruits, {n_nofm} sans final_move, {len(errors)} erreurs ===", file=sys.stderr)

    if errors:
        print(f"\n=== {len(errors)} fixtures a traiter (heuristiques 4.13 ou interpellation 4.11) ===", file=sys.stderr)
        for fid, page, region, err, notation in errors:
            print(f"  {fid} (page {page} r{region}) -- {err} -- notation: {notation}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()

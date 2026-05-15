"""Validation structurelle des final_move des fixtures d'un manuel.

Pour chaque fixture avec final_move != None :
1. Re-joue les coups préliminaires de published_notation pour atteindre
   l'état pré-final.
2. Vérifie que le final_move est :
   a) une rafle légale depuis cet état (= dans enumerate_pawn_captures
      du joueur dont c'est le trait)
   b) **maximale** (= aucune autre rafle ne capture plus de pions)
3. Émet un rapport listing les fixtures conformes / non-conformes.

Cette validation est PARTIELLE :
- Elle ne vérifie pas la légalité de la prise maximale globale (toutes
  les cases du joueur, pas juste celle du final_move).
- Elle n'utilise pas le moteur Scan pour valider que la combinaison est
  GAGNANTE selon l'évaluation moteur (donnerait des unités de pion).
- Pour une validation complète, il faut intégrer Scan via le backend
  Draught Master (cf protocols.py:ScanProtocol).

Usage :
    # Validation du manuel Débutant (par défaut) :
    python validate_final_moves.py

    # Validation d'un autre manuel :
    FIXTURES_MODULE=fixtures_intermediaire python validate_final_moves.py

Configuration :
- DILF_ROOT (var d'env) : chemin vers le repo dilf cloné.
  À défaut, recherché dans ./dilf puis ../dilf.
- FIXTURES_MODULE (var d'env) : nom du module fixtures à valider.
  Défaut : "fixtures_debutant". Le module doit exposer ALL_*_POSITIONS
  (liste des fixtures) — par défaut on cherche ALL_BEGINNER_POSITIONS,
  ALL_INTERMEDIATE_POSITIONS, etc.
"""
import sys, os, re
from pathlib import Path


def _find_dilf_root() -> Path:
    env = os.environ.get("DILF_ROOT")
    if env:
        p = Path(env).resolve()
        if (p / "pedagogy" / "game.py").exists():
            return p
        sys.exit(f"DILF_ROOT={env} ne contient pas pedagogy/game.py")
    here = Path.cwd().resolve()
    for cand in (here / "dilf", here.parent / "dilf", here):
        if (cand / "pedagogy" / "game.py").exists():
            return cand
    sys.exit("dilf non trouve. Definir DILF_ROOT ou cloner dilf a cote.")


DILF_ROOT = _find_dilf_root()
sys.path.insert(0, str(Path.cwd()))
sys.path.insert(0, str(DILF_ROOT))

from pedagogy.game import GameState, Move
from pedagogy.notation.dubois import (
    reconstruct_pawn_capture,
    enumerate_pawn_captures,
    NoSuchRafleError,
    AmbiguousRafleError,
    NotAManError,
)

# Charge dynamiquement le module fixtures du manuel a valider
_FIXTURES_MODULE_NAME = os.environ.get("FIXTURES_MODULE", "fixtures_debutant")
import importlib
fx = importlib.import_module(_FIXTURES_MODULE_NAME)

# Trouve la liste des fixtures (ALL_BEGINNER_POSITIONS, ALL_INTERMEDIATE_POSITIONS, etc.)
_FIXTURES_LIST = None
for attr in dir(fx):
    if attr.startswith("ALL_") and attr.endswith("_POSITIONS"):
        _FIXTURES_LIST = getattr(fx, attr)
        break
if _FIXTURES_LIST is None:
    sys.exit(
        f"Module {_FIXTURES_MODULE_NAME} ne contient aucune liste "
        f"ALL_*_POSITIONS (BEGINNER, INTERMEDIATE, ADVANCED, EXPERT)."
    )


def apply_simple(state, frm, to):
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
    raise ValueError(f"Aucun pion en {frm}")


def apply_capture(state, move):
    captures = set(move.captures)
    if move.from_square in state.white_men:
        return GameState(
            white_men=(state.white_men - {move.from_square}) | {move.to_square},
            white_kings=state.white_kings,
            black_men=state.black_men - captures,
            black_kings=state.black_kings - captures,
            turn="black",
        )
    return GameState(
        white_men=state.white_men - captures,
        white_kings=state.white_kings - captures,
        black_men=(state.black_men - {move.from_square}) | {move.to_square},
        black_kings=state.black_kings,
        turn="white",
    )


def parse_tokens(notation):
    """Renvoie une liste de tokens. Inclut un token spécial ('ad_lib',) pour (ad lib)."""
    out = []
    tokens = re.findall(r"\([^)]+\)|\S+", notation)
    for tok in tokens:
        inside = tok.startswith("(") and tok.endswith(")")
        body = tok[1:-1] if inside else tok
        # Cas spécial : (ad lib) — captures forcées équivalentes
        if "ad lib" in body.lower():
            out.append(("ad_lib", None, None))
            continue
        # Filtrer les non-coups (ex: "+1p", "etc.")
        if "-" not in body and "x" not in body:
            continue
        # Filtrer les tokens avec espaces ou caractères non-numériques
        if " " in body or any(c.isalpha() for c in body.replace("x", "").replace("-", "")):
            continue
        if "-" in body:
            f, t = body.split("-")
            out.append(("reply_simple" if inside else "simple", int(f), int(t)))
        elif "x" in body:
            parts = body.split("x")
            out.append(("reply_capture" if inside else "capture", int(parts[0]), int(parts[-1])))
    return out


def get_max_captures_for_side(state):
    """Énumère toutes les rafles maximales possibles pour le joueur au trait.

    Renvoie (max_captures_count, list_of_all_paths_with_that_count).
    Si aucune capture possible, renvoie (0, []).
    """
    if state.turn == "white":
        my, enemy = state.white_men, state.black_men
    else:
        my, enemy = state.black_men, state.white_men
    all_caps = []
    for sq in my:
        for path, caps in enumerate_pawn_captures(sq, my, enemy):
            if caps:
                all_caps.append((sq, path, caps))
    if not all_caps:
        return 0, []
    max_count = max(len(c) for _, _, c in all_caps)
    max_caps = [(s, p, c) for s, p, c in all_caps if len(c) == max_count]
    return max_count, max_caps


def validate_fixture(p):
    """Renvoie (status, message). status ∈ {OK, NO_FM, FAIL, KING_RAFLE}."""
    if p.final_move is None:
        return "NO_FM", "final_move=None (envoi à dame, gambit, ou blocage)"

    # Re-jouer published_notation jusqu'au final_move
    state = p.state
    initial_turn = state.turn
    fm = p.final_move
    tokens = parse_tokens(p.published_notation)

    # Identifier l'index du token correspondant au final_move
    final_from = fm.from_square
    final_to = fm.to_square
    final_idx = None
    for i, (kind, frm, to) in enumerate(tokens):
        if frm == final_from and to == final_to and "capture" in kind:
            # Vérifier que c'est bien le côté actif initial
            is_active_side = (
                (initial_turn == "white" and kind == "capture")
                or (initial_turn == "black" and kind == "reply_capture")
            )
            if is_active_side:
                final_idx = i
                break

    if final_idx is None:
        return "FAIL", f"final_move {final_from}x{final_to} non trouvé dans notation"

    # Rejouer jusqu'au token précédent
    for kind, frm, to in tokens[:final_idx]:
        try:
            if kind == "ad_lib":
                # Appliquer la première capture forcée du joueur au trait
                if state.turn == "white":
                    my, enemy = state.white_men, state.black_men
                else:
                    my, enemy = state.black_men, state.white_men
                forced = []
                for sq in sorted(my):
                    for path, caps in enumerate_pawn_captures(sq, my, enemy):
                        if caps:
                            forced.append((sq, path[-1]))
                            break
                    if forced:
                        break
                if not forced:
                    return "FAIL", f"(ad lib) mais aucune capture forcée disponible"
                f, t = forced[0]
                m = reconstruct_pawn_capture(state, f, t)
                state = apply_capture(state, m)
            elif kind in ("simple", "reply_simple"):
                state = apply_simple(state, frm, to)
            else:
                m = reconstruct_pawn_capture(state, frm, to)
                state = apply_capture(state, m)
        except (NoSuchRafleError, AmbiguousRafleError, NotAManError, ValueError) as e:
            return "FAIL", f"erreur de rejeu au token {kind} {frm}-{to}: {e}"

    # Vérifier que final_move est applicable depuis state
    if final_from not in (state.white_men if state.turn == "white" else state.black_men):
        # Possible cas d'une dame intermédiaire — sortir
        if state.white_kings or state.black_kings:
            return "KING_RAFLE", f"présence de dame(s), validation pion non applicable"
        return "FAIL", f"pion {final_from} absent de l'état atteint"

    # Vérifier que final_move est une rafle maximale
    max_count, max_paths = get_max_captures_for_side(state)
    if max_count == 0:
        return "FAIL", f"aucune rafle disponible pour {state.turn} depuis l'état atteint"

    fm_captures = set(fm.captures)
    fm_count = len(fm_captures)
    if fm_count < max_count:
        return "FAIL", f"final_move capture {fm_count} pions, mais rafle maximale en capture {max_count}"

    # Vérifier que la rafle exacte est bien dans les rafles maximales légales
    matching = [
        (s, p, c)
        for s, p, c in max_paths
        if s == final_from and p[-1] == final_to and set(c) == fm_captures
    ]
    if not matching:
        return "FAIL", f"final_move ({final_from}→{final_to}, captures {sorted(fm_captures)}) non trouvé parmi rafles maximales légales"

    return "OK", f"rafle maximale ({fm_count} captures) légale et conforme"


def main():
    stats = {"OK": 0, "NO_FM": 0, "FAIL": 0, "KING_RAFLE": 0}
    failures = []
    for p in _FIXTURES_LIST:
        status, msg = validate_fixture(p)
        stats[status] += 1
        if status == "FAIL":
            failures.append((p.id, p.title, msg))
        # print(f"  {status:10s} {p.id}: {msg}")  # verbose mode

    total = len(_FIXTURES_LIST)
    print(f"\n{'=' * 60}")
    print(f"Validation moteur — {_FIXTURES_MODULE_NAME} ({total} fixtures)")
    print(f"{'=' * 60}")
    print(f"  ✅ OK        : {stats['OK']:3d} ({100*stats['OK']//total}%)")
    print(f"  ⊘  NO_FM     : {stats['NO_FM']:3d} (envoi à dame, gambit, blocage)")
    print(f"  ❌ FAIL      : {stats['FAIL']:3d}")
    print(f"  ♛  KING_RAFLE: {stats['KING_RAFLE']:3d} (validation pion non applicable)")
    print()

    if failures:
        print(f"{'=' * 60}")
        print(f"DÉTAIL DES ÉCHECS ({len(failures)} fixtures)")
        print(f"{'=' * 60}")
        for fid, title, msg in failures:
            print(f"  {fid} — {title}")
            print(f"    → {msg}")
            print()
    else:
        print("✅ Aucun échec de validation. Toutes les rafles reconstruites")
        print("   sont des rafles maximales légales.")


if __name__ == "__main__":
    main()

"""Génération de faits déterministes pour une position pédagogique.

Objectif : fournir, pour chaque fixture, une **fiche de faits vérifiés**
calculée directement depuis le `GameState` et la `published_notation`.
Cette fiche sert deux usages (cf option 3 du cadrage manuel) :

1. **Rédaction assistée** : `render_facts_sentence(p)` produit la phrase
   factuelle de base (position + trait + menaces + solution) que Claude
   utilise comme socle, pour ne JAMAIS décrire une position de mémoire.

2. **Double-validation** : `facts_for(p)` retourne un dict structuré que
   `validate_prose_vs_fixtures.py` confronte au texte rédigé. Toute
   affirmation factuelle de la prose qui contredit la fiche est un bug.

Tout ce qui est dans ce module est DÉTERMINISTE et ne dépend QUE de la
géométrie FMJD et des champs de la fixture. Aucune interprétation
tactique (pourquoi un coup gagne, quel est le thème) n'est produite ici :
ça reste du ressort de Claude (interprétation) et du moteur Scan
(vérité tactique).

Usage CLI :
    DILF_ROOT=... python position_facts.py BEG_CH07_001
    DILF_ROOT=... python position_facts.py --all        # toutes les fixtures
"""
from __future__ import annotations

import os
import sys
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

from pedagogy.game import GameState  # noqa: E402
from pedagogy.notation.dubois import enumerate_pawn_captures  # noqa: E402


# ---------------------------------------------------------------------------
# Géométrie FMJD (déterministe)
# ---------------------------------------------------------------------------

def case_to_rc(n: int) -> tuple[int, int]:
    """Case 1-50 → (row, col) sur le damier 10x10."""
    n0 = n - 1
    row = n0 // 5
    pos_in_row = n0 % 5
    col = 2 * pos_in_row + 1 if row % 2 == 0 else 2 * pos_in_row
    return row, col


def rc_to_case(row: int, col: int) -> int | None:
    """(row, col) → case 1-50. None si case claire ou hors plateau."""
    if not (0 <= row < 10 and 0 <= col < 10):
        return None
    if (row + col) % 2 == 0:
        return None
    return row * 5 + col // 2 + 1


def pawn_simple_moves(case: int, color: str, occupied: set[int]) -> list[int]:
    """Coups simples légaux d'un pion (cases d'arrivée vides, vers l'avant)."""
    r, c = case_to_rc(case)
    direction = -1 if color == "white" else 1
    result = []
    for dc in (-1, 1):
        target = rc_to_case(r + direction, c + dc)
        if target is not None and target not in occupied:
            result.append(target)
    return sorted(result)


def pawn_diagonal_neighbors(case: int) -> list[int]:
    """Les 4 voisins diagonaux (toutes directions) d'une case, sur le plateau."""
    r, c = case_to_rc(case)
    result = []
    for dr in (-1, 1):
        for dc in (-1, 1):
            target = rc_to_case(r + dr, c + dc)
            if target is not None:
                result.append(target)
    return sorted(result)


def square_behind(jumper: int, victim: int) -> int | None:
    """Case d'atterrissage juste derrière 'victim' quand 'jumper' saute par-dessus.
    None si hors plateau ou non alignés diagonalement."""
    rj, cj = case_to_rc(jumper)
    rv, cv = case_to_rc(victim)
    dr, dc = rv - rj, cv - cj
    if abs(dr) != 1 or abs(dc) != 1:
        return None  # pas adjacents en diagonale
    return rc_to_case(rv + dr, cv + dc)


# ---------------------------------------------------------------------------
# Faits matériels / couleur
# ---------------------------------------------------------------------------

def piece_color_kind(state: GameState, case: int) -> tuple[str, str] | None:
    """Retourne ('white'|'black', 'man'|'king') pour la pièce en 'case', ou None."""
    if case in state.white_men:
        return ("white", "man")
    if case in state.white_kings:
        return ("white", "king")
    if case in state.black_men:
        return ("black", "man")
    if case in state.black_kings:
        return ("black", "king")
    return None


def color_fr(color: str) -> str:
    return "blanc" if color == "white" else "noir"


# ---------------------------------------------------------------------------
# Détection des menaces immédiates (pion contre pion)
# ---------------------------------------------------------------------------

def immediate_pawn_threats(state: GameState) -> list[dict]:
    """Détecte les menaces de capture immédiate de pion sur pion, pour LES
    DEUX camps. Une menace = un pion adverse adjacent en diagonale avec la
    case derrière vide.

    Retourne une liste de dicts : {attacker, victim, landing, attacker_color}.
    Déterministe, sans interprétation : ce sont des captures géométriquement
    possibles, pas forcément le meilleur coup.
    """
    occupied = set(state.all_pieces)
    threats = []
    # Pions blancs qui peuvent capturer un noir
    for attacker in state.white_men:
        for victim in pawn_diagonal_neighbors(attacker):
            vc = piece_color_kind(state, victim)
            if vc is None or vc[0] != "black":
                continue
            landing = square_behind(attacker, victim)
            if landing is not None and landing not in occupied:
                threats.append({
                    "attacker": attacker, "victim": victim,
                    "landing": landing, "attacker_color": "white",
                })
    # Pions noirs qui peuvent capturer un blanc
    for attacker in state.black_men:
        for victim in pawn_diagonal_neighbors(attacker):
            vc = piece_color_kind(state, victim)
            if vc is None or vc[0] != "white":
                continue
            landing = square_behind(attacker, victim)
            if landing is not None and landing not in occupied:
                threats.append({
                    "attacker": attacker, "victim": victim,
                    "landing": landing, "attacker_color": "black",
                })
    return threats


# ---------------------------------------------------------------------------
# Fiche de faits complète
# ---------------------------------------------------------------------------

def facts_for(p) -> dict:
    """Génère la fiche de faits déterministe d'une fixture.

    Retourne un dict structuré (sérialisable) avec :
    - pieces : {case: {color, kind}}
    - turn
    - simple_moves : {case: [cases d'arrivée]} pour les pions du trait
    - threats : menaces de capture pion/pion (les deux camps)
    - published_notation : verbatim
    - final_move : path + captures si présent
    """
    state = p.state
    occupied = set(state.all_pieces)

    pieces = {}
    for case in sorted(occupied):
        ck = piece_color_kind(state, case)
        if ck:
            pieces[case] = {"color": ck[0], "kind": ck[1]}

    # Coups simples des pions du camp au trait
    simple_moves = {}
    side_men = state.white_men if state.turn == "white" else state.black_men
    for case in sorted(side_men):
        moves = pawn_simple_moves(case, state.turn, occupied)
        simple_moves[case] = moves

    threats = immediate_pawn_threats(state)

    fm = None
    if p.final_move is not None:
        fm = {
            "path": list(p.final_move.path),
            "captures": sorted(p.final_move.captures),
        }

    return {
        "id": p.id,
        "turn": state.turn,
        "pieces": pieces,
        "white_men": sorted(state.white_men),
        "white_kings": sorted(state.white_kings),
        "black_men": sorted(state.black_men),
        "black_kings": sorted(state.black_kings),
        "simple_moves": simple_moves,
        "threats": threats,
        "published_notation": p.published_notation or "",
        "final_move": fm,
    }


def render_facts_sentence(p) -> str:
    """Produit la phrase factuelle de base, à utiliser comme socle de
    rédaction. Pure description déterministe, AUCUNE interprétation."""
    f = facts_for(p)
    lines = []

    # Position
    wm = ", ".join(str(c) for c in f["white_men"]) or "—"
    wk = ", ".join(str(c) for c in f["white_kings"])
    bm = ", ".join(str(c) for c in f["black_men"]) or "—"
    bk = ", ".join(str(c) for c in f["black_kings"])
    pos = f"Pions blancs : {wm}."
    if wk:
        pos += f" Dames blanches : {wk}."
    pos += f" Pions noirs : {bm}."
    if bk:
        pos += f" Dames noires : {bk}."
    lines.append(pos)

    trait = "blancs" if f["turn"] == "white" else "noirs"
    lines.append(f"Trait aux {trait}.")

    # Menaces
    if f["threats"]:
        threat_strs = []
        for t in f["threats"]:
            ac = color_fr(t["attacker_color"])
            vc = "blanc" if t["attacker_color"] == "black" else "noir"
            threat_strs.append(
                f"le pion {ac} {t['attacker']} peut capturer le pion {vc} "
                f"{t['victim']} (atterrissage en {t['landing']})"
            )
        lines.append("Menaces immédiates : " + " ; ".join(threat_strs) + ".")
    else:
        lines.append("Aucune menace de capture pion/pion immédiate.")

    # Solution
    if f["published_notation"]:
        lines.append(f"Solution publiée (verbatim) : {f['published_notation']}.")
    if f["final_move"]:
        path = "→".join(str(s) for s in f["final_move"]["path"])
        caps = ", ".join(str(s) for s in f["final_move"]["captures"])
        lines.append(f"Rafle finale : trajet {path}, captures {caps}.")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    import importlib
    fixtures_module_name = os.environ.get("FIXTURES_MODULE", "fixtures_debutant")
    fx = importlib.import_module(fixtures_module_name)
    fixtures_list = None
    for attr in dir(fx):
        if attr.startswith("ALL_") and attr.endswith("_POSITIONS"):
            fixtures_list = getattr(fx, attr)
            break
    if fixtures_list is None:
        sys.exit(f"Module {fixtures_module_name} sans liste ALL_*_POSITIONS")

    by_id = {p.id: p for p in fixtures_list}

    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    if sys.argv[1] == "--all":
        for p in fixtures_list:
            print(f"\n{'=' * 60}\n{p.id}\n{'=' * 60}")
            print(render_facts_sentence(p))
    else:
        for fid in sys.argv[1:]:
            p = by_id.get(fid)
            if p is None:
                print(f"❌ {fid} introuvable")
                continue
            print(f"\n{'=' * 60}\n{fid}\n{'=' * 60}")
            print(render_facts_sentence(p))


if __name__ == "__main__":
    main()

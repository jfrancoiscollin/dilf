"""Tests de cohérence prose / fixtures pour le manuel débutant.

Garde-fou contre la dérive entre le texte du manuel et les fixtures
Python qu'il référence. Vérifie deux invariants :

1. **Existence** : chaque `BEG_CHxx_yyy` cité dans le manuel doit
   correspondre à une fixture définie dans `fixtures_debutant.py`.

2. **Notation publiée** : chaque bloc `> ``published_notation`` Dubois :
   ``<notation>``` dans le manuel doit matcher exactement la valeur du
   champ `published_notation` de la fixture associée (la plus proche
   référence `BEG_CHxx_yyy` en amont).

Ces tests opèrent à plat (lecture du Markdown + import du module
fixtures), sans Scan ni moteur — exécution rapide.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CORPUS_DIR = ROOT / "docs" / "pre_process_corpus"
MANUAL = CORPUS_DIR / "manuel_debutant.md"

sys.path.insert(0, str(CORPUS_DIR))
from fixtures_debutant import ALL_BEGINNER_POSITIONS  # type: ignore[import-not-found]

FIXTURE_INDEX = {p.id: p for p in ALL_BEGINNER_POSITIONS}

REF_PATTERN = re.compile(r"\b(BEG_CH\d{2}_\d{3})\b")

# Bloc cité en début de section / sous-section :
#   > `published_notation` Dubois : `<notation>`
# (avec ou sans `pour ``BEG_X``` explicite — sinon le ref le plus
# proche en amont est utilisé).
NOTATION_BLOCK_PATTERN = re.compile(
    r"`published_notation`\s+Dubois"
    r"(?:\s+pour\s+`(?P<explicit_ref>BEG_CH\d{2}_\d{3})`)?"
    r"\s*:\s*`(?P<notation>[^`\n]+)`"
)

# Format bullet "variantes additionnelles" :
#   - `BEG_CH11_002` (ch...) : `notation`
NOTATION_BULLET_PATTERN = re.compile(
    r"^\s*[-*]\s+`(?P<ref>BEG_CH\d{2}_\d{3})`[^:\n]*:\s*\n?\s*`(?P<notation>[^`\n]+)`",
    re.MULTILINE,
)


@pytest.fixture(scope="module")
def manual_text() -> str:
    return MANUAL.read_text()


def test_manual_exists(manual_text: str) -> None:
    """Sanity : le manuel est lu et non vide."""
    assert len(manual_text) > 1000, "Manuel anormalement court"
    assert "BEG_CH" in manual_text


def test_all_referenced_fixtures_exist(manual_text: str) -> None:
    """Chaque BEG_CHxx_yyy cité dans le manuel doit exister."""
    cited = {m.group(1) for m in REF_PATTERN.finditer(manual_text)}
    missing = sorted(cited - FIXTURE_INDEX.keys())
    assert not missing, (
        f"Le manuel cite {len(missing)} fixture(s) inexistante(s) : {missing}"
    )


def test_every_fixture_is_cited(manual_text: str) -> None:
    """Chaque fixture définie doit être citée au moins une fois.

    Garde-fou contre les fixtures orphelines (laissées dans le code
    mais sorties du manuel) — utile au moment des refactors.
    """
    cited = {m.group(1) for m in REF_PATTERN.finditer(manual_text)}
    orphans = sorted(FIXTURE_INDEX.keys() - cited)
    assert not orphans, (
        f"{len(orphans)} fixture(s) jamais citée(s) dans le manuel : {orphans}"
    )


def _nearest_fixture_id(text: str, position: int) -> str | None:
    """Retourne le BEG_CHxx_yyy le plus récent avant `position` dans `text`."""
    nearest = None
    for m in REF_PATTERN.finditer(text, 0, position):
        nearest = m.group(1)
    return nearest


def _normalize(notation: str) -> str:
    """Normalise pour comparaison : strip, × -> x, espaces multiples."""
    return re.sub(r"\s+", " ", notation.replace("×", "x").strip())


def test_quoted_notations_match_fixtures(manual_text: str) -> None:
    """Chaque notation Dubois citée doit matcher la fixture associée.

    Couvre deux formats :
    - Bloc `> ``published_notation`` Dubois : ``<notation>``` — le ref
      est soit explicite (« pour ``BEG_X`` »), soit la référence
      `BEG_CHxx_yyy` la plus proche en amont.
    - Bullet `- ``BEG_X`` ... : ``<notation>``` — le ref est dans le
      bullet lui-même.

    Comparaison modulo normalisation `×` ↔ `x` et espaces.
    """
    mismatches: list[tuple[str, str, str]] = []

    for match in NOTATION_BLOCK_PATTERN.finditer(manual_text):
        cited = match.group("notation").strip()
        ref = match.group("explicit_ref") or _nearest_fixture_id(
            manual_text, match.start()
        )
        _check_match(ref, cited, mismatches)

    for match in NOTATION_BULLET_PATTERN.finditer(manual_text):
        cited = match.group("notation").strip()
        ref = match.group("ref")
        _check_match(ref, cited, mismatches)

    assert not mismatches, _format_mismatch_report(mismatches)


def _looks_like_notation(text: str) -> bool:
    """Heuristique : la chaîne contient au moins un coup damiste.

    Évite de matcher des bullets narratifs comme « - `BEG_X` :
    ``published_notation`` commence par ``(17-22)`` ... » où le premier
    backtick après le colon contient un identifiant, pas une notation.
    """
    return bool(re.search(r"\d{1,2}\s*[-x×]\s*\d{1,2}", text))


def _check_match(
    ref: str | None, cited: str, mismatches: list[tuple[str, str, str]]
) -> None:
    if ref is None or ref not in FIXTURE_INDEX:
        return
    if not _looks_like_notation(cited):
        return
    real = FIXTURE_INDEX[ref].published_notation or ""
    if not real:
        return
    if _normalize(cited) != _normalize(real):
        mismatches.append((ref, cited, real))


def _format_mismatch_report(mismatches: list[tuple[str, str, str]]) -> str:
    lines = [f"{len(mismatches)} notation(s) divergente(s) prose ↔ fixture :"]
    for ref, cited, real in mismatches[:20]:
        lines.append(f"  - {ref}")
        lines.append(f"      cité    : `{cited}`")
        lines.append(f"      fixture : `{real}`")
    if len(mismatches) > 20:
        lines.append(f"  ... + {len(mismatches) - 20} autres")
    return "\n".join(lines)


def test_validation_scan_tables_reference_real_fixtures(manual_text: str) -> None:
    """Chaque ligne de tableau `| BEG_CHxx_yyy | ...` doit pointer une fixture.

    Garde-fou spécifique aux tableaux Validation Scan introduits dans
    le refactor zéro-invention.
    """
    table_row_pattern = re.compile(r"^\|\s*`(BEG_CH\d{2}_\d{3})`\s*\|", re.MULTILINE)
    cited = {m.group(1) for m in table_row_pattern.finditer(manual_text)}
    missing = sorted(cited - FIXTURE_INDEX.keys())
    assert not missing, (
        f"Tableaux Validation Scan référencent {len(missing)} "
        f"fixture(s) inexistante(s) : {missing}"
    )

"""Pin the deterministic plumbing of scripts/index_prose.py.

Real-corpus runs need pdftotext on PATH + actual PDFs; these tests
cover only the pure-Python pieces of the pipeline (chunk + tag +
emit) so the contract stays stable as we add corpora.
"""
from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO))

_SCRIPT = _REPO / "scripts" / "index_prose.py"
_spec = importlib.util.spec_from_file_location("index_prose", _SCRIPT)
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)

from pedagogy.prose.passages import ProsePassage  # noqa: E402
from pedagogy.prose.concepts import Assertion, AssertionType, StrategicConcept  # noqa: E402


# ── Chunking ──
def test_chunk_pages_basic(tmp_path):
    page = tmp_path / "page_0042.txt"
    page.write_text(
        "Premier paragraphe assez long pour passer le seuil de minimum-chars "
        "qu'on a fixé à 80 caractères par défaut dans le module.\n"
        "\n"
        "Deuxième paragraphe — également au-delà du seuil grâce à du texte "
        "supplémentaire d'illustration ajouté ici exprès.\n"
        "\n"
        "court\n",  # below threshold → dropped
        encoding="utf-8",
    )
    passages = mod.chunk_pages([page], source="TEST", book="livre")
    assert len(passages) == 2
    assert passages[0].passage_id == "TEST_livre_p0042_00"
    assert passages[1].passage_id == "TEST_livre_p0042_01"
    assert passages[0].page == 42
    assert passages[0].source == "TEST"
    assert passages[0].book == "livre"


def test_chunk_skips_page_noise(tmp_path):
    """Page numbers, "page N", and chapter headers should not appear
    as passages and should not fragment the surrounding paragraph."""
    page = tmp_path / "page_0007.txt"
    page.write_text(
        "7\n"
        "page 7\n"
        "Chapitre 3 — Roozenburg\n"
        "Un vrai paragraphe substantiel de prose stratégique sur le système "
        "Roozenburg, suffisamment long pour franchir le seuil minimum.\n",
        encoding="utf-8",
    )
    passages = mod.chunk_pages([page], source="TEST", book="livre")
    assert len(passages) == 1
    assert "Roozenburg" in passages[0].text
    assert "page 7" not in passages[0].text


def test_passage_id_is_stable(tmp_path):
    page = tmp_path / "page_0001.txt"
    body = "x" * 100
    page.write_text(f"{body}\n", encoding="utf-8")
    a = mod.chunk_pages([page], source="S", book="b")
    b = mod.chunk_pages([page], source="S", book="b")
    assert [p.passage_id for p in a] == [p.passage_id for p in b]


# ── Tagging ──
def _p(text: str, idx: int = 0) -> ProsePassage:
    return ProsePassage(
        passage_id=f"X_y_p0001_{idx:02d}",
        text=text, source="X", book="y", page=1, char_offset=0,
    )


def test_tag_detects_systems():
    passages = mod.tag_passages([_p("Le Roozenburg cherche le contrôle du flanc.")])
    assert passages[0].systems == ("roozenburg",)


def test_tag_surfaces_multi_system_ambiguity():
    """Per CADRAGE_STRATEGIE.md §4.S3, when several systems are named
    we surface all of them rather than guess which one is the subject."""
    passages = mod.tag_passages([_p("Le Roozenburg dérive du jeu classique de Keller.")])
    assert "roozenburg" in passages[0].systems
    assert "classique" in passages[0].systems
    assert "keller" in passages[0].systems


def test_tag_detects_phase_and_nature():
    passages = mod.tag_passages([
        _p("Le principe est de garder le centre en ouverture.", 0),
        _p("Gare à la diagonale longue en finale, c'est un piège.", 1),
    ])
    assert passages[0].phase == "ouverture"
    assert passages[0].nature == "principe"
    assert passages[1].phase == "finale"
    assert passages[1].nature == "avertissement"  # piège wins over plan/principe


def test_tag_is_pure():
    p_in = _p("Roozenburg.")
    [p_out] = mod.tag_passages([p_in])
    # Inputs untouched (frozen dataclass guarantees this, but assert anyway).
    assert p_in.systems == ()
    assert p_out is not p_in


# ── Emit ──
def test_emit_module_roundtrip(tmp_path):
    passages = mod.tag_passages([
        _p("Long enough Roozenburg passage to be a paragraph in real life.", 0),
    ])
    out = tmp_path / "prose_passages_test_y.py"
    mod.emit_module(passages, out, pdf_path=Path("dummy.pdf"))

    # Load the emitted module and check ALL_PASSAGES is well-formed.
    spec = importlib.util.spec_from_file_location("prose_passages_test_y", out)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    assert len(m.ALL_PASSAGES) == 1
    p = m.ALL_PASSAGES[0]
    assert p.passage_id == "X_y_p0001_00"
    assert "Roozenburg" in p.text
    assert p.systems == ("roozenburg",)


def test_emit_escapes_triple_quotes(tmp_path):
    """A paragraph containing ``\"\"\"`` must not break the emitted
    module's triple-quoted string literal."""
    paragraph = 'Le maître écrit : """citation""" — fin.'
    passages = [
        _p(paragraph + " " + "x" * 80, 0),  # pad above min_chars when relevant
    ]
    out = tmp_path / "prose_passages_test_quote.py"
    mod.emit_module(passages, out, pdf_path=Path("dummy.pdf"))
    # Module must import without SyntaxError.
    spec = importlib.util.spec_from_file_location("prose_passages_test_quote", out)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    assert len(m.ALL_PASSAGES) == 1


# ── StrategicConcept format spec (§6) ──
def test_strategic_concept_minimal():
    """The wrapper accepts an empty body — verified=False by default."""
    from pedagogy.game import GameState
    c = StrategicConcept(
        id="SYS_ROOZENBURG_001",
        system="roozenburg",
        title="Test",
        phase="ouverture",
    )
    assert c.verified is False
    assert c.assertions == ()
    assert c.illustrations == ()


def test_assertion_types_are_explicit():
    """§4.S1 — every assertion declares its kind. No default `kind`."""
    a = Assertion(text="Le Roozenburg favorise le flanc.", kind=AssertionType.CITED,
                  passage_ids=("ROOZENBURG_systeme_p015_07",))
    assert a.kind == AssertionType.CITED
    assert a.confidence == "medium"
    assert a.passage_ids == ("ROOZENBURG_systeme_p015_07",)


def test_engine_assertion_carries_fen_and_eval():
    a = Assertion(
        text="Cette structure évalue à +0.8 pour les Blancs.",
        kind=AssertionType.ENGINE,
        engine_fen="W:W31,32,33:B14,15,16",
        engine_eval=0.8,
    )
    assert a.engine_eval == 0.8
    assert a.engine_fen.startswith("W:")

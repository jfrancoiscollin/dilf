"""Real Dubois references for the coup_royal detector.

This module catalogues coup royal examples drawn from
``jpdubois_perfectionnement_combinaisons_V4.pdf`` (FMJD edition, by
Jean-Pierre Dubois). Each :class:`DuboisCoupRoyalCase` carries:

* the bibliographic source (book, chapter, diagram, page),
* the historical attribution when the diagram is taken from a real game,
* the **exact PDN-style notation excerpt** as printed by Dubois,
* a hand-built :class:`pedagogy.game.Move` that satisfies the detector's
  signature (≥ 6 captures, ≥ 4 in :data:`CENTER_EXTENDED`, ≥ 4 distinct
  rows, AND ends on a promotion row OR crosses the great diagonal).

The Dubois notations are sometimes abbreviated (``40x7`` lists only the
endpoints, without intermediate squares or captured pieces). Reconstructing
the exact captured pieces would require OCR of the printed diagrams.
Instead, every ``final_move`` here is a **signature-matching
reconstruction**: it preserves the published landing square when
geometrically possible and otherwise stays close to the documented
trajectory. The provenance is fully recorded for the explanation layer
(spec §6.7).
"""

from __future__ import annotations

from dataclasses import dataclass

from pedagogy.game import Move


@dataclass(frozen=True)
class DuboisCoupRoyalCase:
    """One coup royal example sourced from Dubois Volume 5."""

    name: str
    book: str                       # PDF filename in the main-branch corpus
    chapter: int
    diagram: str                    # e.g. "D4", "D11"
    page: int
    description: str
    game_attribution: str           # e.g. "Kats vs van Leeuwen (1992)"
    published_notation: str         # exact Dubois excerpt
    final_move: Move                # synthetic signature-matching reconstruction
    expected_captures_min: int

    @property
    def book_reference(self) -> str:
        """Citation string for :class:`MotifMatch.metadata` (spec §6.7)."""
        return f"{self.book}, ch. {self.chapter}, {self.diagram}, p. {self.page}"


D4_KATS_VAN_LEEUWEN: DuboisCoupRoyalCase = DuboisCoupRoyalCase(
    name="Dubois V5 D4 — Kats vs Van Leeuwen 1992",
    book="jpdubois_perfectionnement_combinaisons_V4",
    chapter=1,
    diagram="D4",
    page=7,
    description="Un coup royal sous une forme inhabituelle.",
    game_attribution="Michael Kats vs Jan van Leeuwen (1992)",
    published_notation=(
        "28-23 (19x28) 32x23 (21x41) 42-37 (41x43) 47-42 (18x29) "
        "34x23 (43x34) 40x7"
    ),
    final_move=Move(
        path=(40, 29, 23, 18, 12, 7, 3),
        captures=(34, 28, 22, 17, 13, 8),
    ),
    expected_captures_min=6,
)


D11_PEENMAA: DuboisCoupRoyalCase = DuboisCoupRoyalCase(
    name="Dubois V5 D11 — Peenmaa vs Shliahovsky 1990",
    book="jpdubois_perfectionnement_combinaisons_V4",
    chapter=1,
    diagram="D11",
    page=7,
    description="La rafle finale traverse tout le damier et ramasse 6 pions.",
    game_attribution="Indrek Peenmaa vs Nicolai Shliahovsky (Tallinn-Cup jr 1990)",
    published_notation=(
        "(18-23) 29x20 (15x24) 30x19 (28-32) 37x28 (17-22) 28x17 "
        "(27-31) 36x27 (8-13) 19x8 (3x45)"
    ),
    final_move=Move(
        # Ends on 45 (row 9, not promo) but crosses the great diagonal
        # via 14, 23, 28, 32, 41.
        path=(3, 14, 23, 28, 32, 41, 45),
        captures=(8, 17, 18, 24, 27, 37),
    ),
    expected_captures_min=6,
)


D12_PIEGE_VIMONT: DuboisCoupRoyalCase = DuboisCoupRoyalCase(
    name="Dubois V5 D12 — piège Vimont",
    book="jpdubois_perfectionnement_combinaisons_V4",
    chapter=10,
    diagram="D12",
    page=44,
    description=(
        "Piège classique connu sous le nom de piège Vimont — black "
        "exécute la rafle finale jusqu'en case 4."
    ),
    game_attribution="Composition (M. Vimont)",
    published_notation=(
        "(24-29) 33x24 (19x30) 28x17 (11x31) 35x24 (31-36) 25-20 (36x47) "
        "37-31 (26x28) 38-33 (47x29) 24x4"
    ),
    final_move=Move(
        # Lands on 4 (row 1 = white promotion row); black king ranges
        # zigzag through center. Synthetic reconstruction.
        path=(24, 13, 9, 25, 8, 12, 4),
        captures=(19, 18, 27, 26, 11, 7),
    ),
    expected_captures_min=6,
)


D12_PIEGE_AANDAGT: DuboisCoupRoyalCase = DuboisCoupRoyalCase(
    name="Dubois V5 D12 — piège Aandagt (thème coup turc)",
    book="jpdubois_perfectionnement_combinaisons_V4",
    chapter=10,
    diagram="D12",
    page=43,
    description=(
        "Piège de coup royal composé par M. Aandagt, sur le thème du coup "
        "turc. Rafle finale 34x1 traversant le centre."
    ),
    game_attribution="Composition (M. Aandagt)",
    published_notation=(
        "(24-29) 33x24 (19x30) 28x17 (11x31) 35x24 (31-37) 42x31 "
        "(26x46) 38-33 (46x29) 34x1"
    ),
    final_move=Move(
        # Lands on 1 (row 1 = white promotion row).
        path=(34, 25, 14, 9, 13, 6, 1),
        captures=(29, 22, 17, 27, 8, 11),
    ),
    expected_captures_min=6,
)


ALL_DUBOIS_COUP_ROYAL: list[DuboisCoupRoyalCase] = [
    D4_KATS_VAN_LEEUWEN,
    D11_PEENMAA,
    D12_PIEGE_VIMONT,
    D12_PIEGE_AANDAGT,
]

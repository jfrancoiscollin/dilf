# Reference corpus

This directory holds the source PDFs the OCR workflow extracts positions from. The current Dubois ground-truth pipeline targets `jpdubois_perfectionnement_combinaisons_V4.pdf`; the rest are kept for future extension of the fixture base.

**Total**: 53 PDFs, ~217 MB, ~6 100 pages.

## Dubois (French)

Primary francophone reference, structured "apprentissage → perfectionnement → expert".

| File | Pages | Notes |
|---|---|---|
| `dubois_apprent_combin.pdf` | 133 | First combinatorial workbook |
| `jpdubois_apprentissage_fins_de_parties_V1.pdf` | 157 | Endgames, beginner |
| `jpdubois_apprentissage_sens_du_jeu_V1.pdf` | 150 | Positional sense, beginner |
| `jpdubois_expert_combinaisons_V2.pdf` | 118 | Combinations, expert level |
| `jpdubois_perfectionnement_combinaisons_V4.pdf` | 93 | **Active OCR target** |
| `jpdubois_perfectionnement_sens_du_jeu_tome_1_V2.pdf` | 139 | Positional sense, tome 1 |
| `jpdubois_perfectionnement_sens_du_jeu_tome_2_V1.pdf` | 120 | Tome 2 |
| `jpdubois_perfectionnement_sens_du_jeu_tome_3_V1.pdf` | 116 | Tome 3 |
| `maitrise-du-jeu-de-dames-dubois.pdf` | 160 | Master-level Dubois |

## Other French

| File | Pages | Notes |
|---|---|---|
| `le_systeme_keller.pdf` | 103 | Keller opening system |
| `le_systeme_roozenburg.pdf` | 76 | Roozenburg opening system |
| `CORPUS REFERENCE DAMES.pdf` | 11 | External corpus index reference |

## Master series — courses + workbooks

Each master has a "course" (theory) and "workbook" (exercises) PDF.

| Author | Course | Workbook |
|---|---|---|
| Hoogland | `hooglandcourse.pdf` (373 p) | — |
| Roozenburg | `roozenburgcourse.pdf` (409 p) | `roozenburgworkbook.pdf` (309 p) |
| Sijbrands | `sijbrandscourse.pdf` (202 p) | `sijbrandsworkbook.pdf` (229 p) |
| Springer | `springercourse.pdf` (409 p) | `springerworkbook.pdf` (249 p) |
| van der Wal | `vdwalcourse.pdf` (82 p) | `vdwalworkbook.pdf` (202 p) |
| Wiersma | `wiersmacourse.pdf` (187 p) | `wiersmaworkbook.pdf` (197 p) |

## Khachatryan / TaoW

A multi-volume tactical course distributed as separately numbered PDFs.

| File | Pages |
|---|---|
| `0.1.Preface(online).pdf` | 16 |
| `1.The_endgame(online).pdf` | 97 |
| `2.Classics(online).pdf` | 74 |
| `3.Center_play(online).pdf` | 39 |
| `4.Right_wing_attack.pdf` | 63 |
| `5.Attacking_systems(online).pdf` | 41 |
| `6.Edge_pieces(online).pdf` | 41 |
| `7.Locks(online).pdf` | 45 |
| `Exercise_2.pdf` | 204 |
| `Exercise_3.pdf` | 266 |
| `Index_TaoW.pdf` | 12 |
| `AppendixACID1.pdf` | 25 |

## Strategy & endgame compilations (S-series)

Standalone chapters from a multi-author strategy compilation.

- `Introduction(c).pdf`, `Introduction CID 3.pdf`, `Epilogue(c).pdf`
- `S1.Judging positions(c).pdf`, `S1.Using tactics as a weapon.pdf`
- `S2.The opening of the game.pdf`
- `S3.Classics(c).pdf`, `S3.Strategy.pdf`
- `S4.Right wing attack(c).pdf`, `S4.Thinking process.pdf`
- `S5. Attacking systems(c).pdf`, `S5.The endgame.pdf`
- `S6.Edge pieces(c).pdf`, `S6.Finsihing off the game.pdf`
- `S7.Epilogue.pdf`

## Introductory courses

| File | Pages |
|---|---|
| `Course in draughts.pdf` | 166 |
| `Introductory course in draughts.pdf` | 104 |
| `Pre-courseInDraughts.pdf` | 140 |

## How to reference a PDF in the workflow

The `extract-diagrams.yml` workflow takes the path relative to the repo root:

```
docs/corpus/jpdubois_perfectionnement_combinaisons_V4.pdf
```

Locally with the CLI:

```bash
python3 -m scripts.extract_diagrams all \
    --pdf docs/corpus/jpdubois_perfectionnement_combinaisons_V4.pdf \
    --pages 5-90 \
    --model claude-sonnet-4-6
```

Page counts above come from `pdfinfo` and can be verified with:

```bash
for f in docs/corpus/*.pdf; do
  pages=$(pdfinfo "$f" 2>/dev/null | awk '/^Pages:/ {print $2}')
  echo "$pages $f"
done | sort -n
```

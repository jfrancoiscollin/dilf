# Pinned Scan score units: source audit, no new scoring

The new D1 threshold proposal correctly requires an explicit unit contract before
interpreting costs as fractions of a material man. This source-only audit uses
the already pinned Scan commit `7aae17e7b7bfc47744601afb1ee7655e18983ce5` and
pinned `data/eval`; it accesses no tournament position, outcome or target score.
It does not amend D1 gates, choose a signature or rerun any D1 campaign.

## Verified conversion and score categories

At pinned [search.cpp lines 566–568](https://github.com/rhalbersma/scan/blob/7aae17e7b7bfc47744601afb1ee7655e18983ce5/src/search.cpp#L566),
Scan exports HUB `score` as `ml::ftos(double(score) / 100.0, 2)`.
[libmy.cpp](https://github.com/rhalbersma/scan/blob/7aae17e7b7bfc47744601afb1ee7655e18983ce5/src/libmy.cpp#L98)
uses fixed decimal formatting. The repository's `Scan.score` multiplies this
decimal by 100 with `Decimal`, restoring the integer score. Thus one stored
integer unit equals **0.01 of a HUB display unit**. It is valid to compare
ordinary regret in these fixed integer reference units.

[score.hpp](https://github.com/rhalbersma/scan/blob/7aae17e7b7bfc47744601afb1ee7655e18983ce5/src/score.hpp#L17)
sets `Inf=10000` and `Eval_Inf=8000`. Ordinary evaluation is inclusive
[-8000,8000]; winning/losing distance scores are strictly outside. The existing
MTDP `_category` boundaries match this contract. A category flag is not a
calibrated win probability or a universal W/D/L truth from finite search.
[eval.cpp](https://github.com/rhalbersma/scan/blob/7aae17e7b7bfc47744601afb1ee7655e18983ce5/src/eval.cpp#L210)
returns evaluation for the side to move; the existing successor audit negates
the successor's score when returning to the parent's mover.

## Why this does not establish a literal 100-units-per-man valuation

In `eval.cpp`, `Unit=10` denotes weight subunits per integer score. The first
feature is the white-minus-black man count; its middle/endgame weights are
loaded from the first two signed big-endian 16-bit values in `data/eval`.
The pinned bytes begin `050f04a90dbc0dfb0cb20caf`; their first six weights are
`1295,1193,3516,3579,3250,3247`. Consequently the **material-only** man-count
coefficients are 129.5 and 119.3 stored integer units before interpolation and
rounding, not a constant 100. Learned patterns, mobility, phase and drawish
scaling also contribute. This is not a way to infer the value of removing a man
from a real board while holding all other evaluation terms fixed.

Therefore the source audit confirms the decimal-to-integer scaling, but does
**not** certify a universal conversion of 100 stored units into one material
man. In reports, state that the repository's historical `centimen` field denotes
integer Scan reference units reconstructed from HUB. A difference of 2 means
0.02 HUB units; do not relabel it as 0.02 of a material man without a separately
specified calibration. Existing numerical scores, budgets, selections and
registered analysis remain unchanged. D1 retains ownership of its threshold
convention and any amendment before scoring.

## Reproduction

Use a clean Scan checkout at the pinned commit and verify `data/eval` SHA-256
`0e7161c38af605f5e367f3f8fe17525d1c40db722714c68921971b386e58abba`:

```python
from pathlib import Path
import hashlib
raw = Path('data/eval').read_bytes()
assert hashlib.sha256(raw).hexdigest() == '0e7161c38af605f5e367f3f8fe17525d1c40db722714c68921971b386e58abba'
w = [int.from_bytes(raw[i:i+2], 'big', signed=True) for i in range(0, 12, 2)]
assert w == [1295, 1193, 3516, 3579, 3250, 3247]
print('Man-count coefficients before interpolation:', w[0] / 10, w[1] / 10)
```

`scan-score-contract-audit-2026-11-18.json` records exact source hashes, weights
and category boundaries. This audit supplies no new decision-equivalence,
regret, Elo or independent-corpus result. Both reserved arenas remain excluded
from D1. No PC from Jeff is required.

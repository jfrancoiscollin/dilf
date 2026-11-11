# MTDP — experimental spatial research

This module is **research-only**, deliberately separate from the stable
`pedagogy/` public API and the downstream draught-master contract.

## First experiment

From the repository root:

```bash
python -m research.mtdp.dataset --output .cache/mtdp/dubois.jsonl
pytest research/mtdp/tests -q
```

The first experiment reuses the existing Dubois diagram fixtures and canonical
`GameState`, `state_to_fen`, geometry and material helpers. Each JSONL row
contains a schema version, source provenance, a stable position hash, and
**descriptive** spatial metrics. It makes no claim about playing strength.

### Limitations

- The Dubois diagram corpus is a selected tactical teaching sample, not a
  random sample of games. Do not infer population-level effects from it.
- The original extraction pipeline has incomplete king detection. The output
  explicitly marks `king_detection_verified: false`.
- The `extraction_confidence` field is copied from the source and is not an
  empirically calibrated correctness probability.
- Spatial adjacency and center occupancy are not the same as legal control,
  tactical threats or positional evaluation.
- Position hashes are identifiers, not proof of independent observations.
- No Scan/Jass evaluations or game trajectories are generated in this phase.
- Check source copyright and reuse permissions before redistributing data.

## Next experiments

1. Audit a stratified sample of source positions and king classifications.
2. Add a legally validated PDN replay adapter through `EngineProtocol` to
   produce per-ply trajectories (including capture and promotion validation).
3. Construct non-tactical controls, stratify by material and game phase, and
   compare with out-of-sample engine assessments.
4. Only promote independently validated metrics into `pedagogy/features/`.

"""MTDP-D1 score-blind signature collision audit.

Input is JSONL with FEN, owning game ID, legal-action identities and signature
values. No Scan/Jass score is accepted. This audit does not establish
decision equivalence or justify pruning.

Example row:
{"fen":"W:W31:B20","game_id":"g1","actions":[["31","26",[],false]],"signatures":{"L":"...", "Q":"..."}}
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from itertools import combinations
import json
from pathlib import Path
from typing import Any, Iterable


def _stable(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _canonical_actions(actions: Any) -> tuple[str, ...]:
    if not isinstance(actions, list):
        raise ValueError("actions must be a list")
    keys = tuple(sorted(_stable(a) for a in actions))
    if len(keys) != len(set(keys)):
        raise ValueError("ambiguous/duplicate legal-action identity")
    return keys


def audit(records: Iterable[dict[str, Any]], *, max_examples: int = 12) -> dict[str, Any]:
    """Audit signature collisions without examining target outcomes.

    Duplicate FENs must agree on legal actions and signature keys; distinct
    FENs from different games count as cross-game pairs, not independent
    samples. No ordering or sampling based on a target score is permitted.
    """
    by_fen: dict[str, dict[str, Any]] = {}
    observations = 0
    for row in records:
        observations += 1
        if not isinstance(row, dict):
            raise ValueError("row must be a JSON object")
        fen, game_id = row.get("fen"), row.get("game_id")
        signatures = row.get("signatures")
        if not isinstance(fen, str) or not fen.strip():
            raise ValueError("missing nonempty fen")
        if not isinstance(game_id, str) or not game_id.strip():
            raise ValueError("missing nonempty game_id")
        if not isinstance(signatures, dict) or not signatures:
            raise ValueError("missing signature mapping")
        if any(not isinstance(k, str) or not k or v is None for k, v in signatures.items()):
            raise ValueError("invalid signature key/value")
        actions = _canonical_actions(row.get("actions"))
        keys = {k: _stable(v) for k, v in signatures.items()}
        if fen not in by_fen:
            by_fen[fen] = {"actions": actions, "signatures": keys, "games": {game_id}}
        else:
            prior = by_fen[fen]
            if prior["actions"] != actions or prior["signatures"] != keys:
                raise ValueError(f"contradictory duplicate FEN: {fen}")
            prior["games"].add(game_id)

    # Different signature ladders must cover exactly the same FEN population.
    ladders = {tuple(sorted(v["signatures"])) for v in by_fen.values()}
    if len(ladders) > 1:
        raise ValueError("incomplete or inconsistent signature ladder")
    names = sorted(next(iter(ladders), ()))
    result: dict[str, Any] = {
        "schema_version": "mtdp-d1-score-blind-audit-v1",
        "observations": observations,
        "distinct_fens": len(by_fen),
        "signature_audits": {},
        "limitations": [
            "Same legal actions do not imply same successor, best move or minimax value",
            "Cross-game pairs can share openings and are not independent observations",
            "No Scan scores, regret, ranking agreement or search strength are measured",
            "Input signatures and FMJD legality require external provenance validation",
        ],
    }
    for name in names:
        groups: dict[str, list[tuple[str, dict[str, Any]]]] = defaultdict(list)
        for fen, row in by_fen.items():
            groups[row["signatures"][name]].append((fen, row))
        total = same = different = cross = cross_different = 0
        examples: list[dict[str, Any]] = []
        for group in groups.values():
            for (fa, a), (fb, b) in combinations(sorted(group), 2):
                total += 1
                mismatch = a["actions"] != b["actions"]
                cross_game = len(a["games"] | b["games"]) > 1
                # Distinct game provenance is descriptive, not independence proof.
                different += int(mismatch)
                same += int(not mismatch)
                cross += int(cross_game)
                cross_different += int(cross_game and mismatch)
                if mismatch and len(examples) < max_examples:
                    examples.append({"fen_a": fa, "fen_b": fb,
                                     "failure": "different_legal_actions",
                                     "cross_game": cross_game})
        result["signature_audits"][name] = {
            "distinct_signatures": len(groups),
            "compression_fraction": (1 - len(groups) / len(by_fen)) if by_fen else 0.0,
            "distinct_fen_pairs": total,
            "same_legal_action_pairs": same,
            "different_legal_action_pairs": different,
            "cross_game_pairs": cross,
            "cross_game_different_legal_action_pairs": cross_different,
            "counterexamples": examples,
        }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="Score-blind JSONL records")
    parser.add_argument("--output", type=Path, help="Deterministic JSON report")
    args = parser.parse_args()
    with args.input.open(encoding="utf-8") as stream:
        records = (json.loads(line) for line in stream if line.strip())
        report = audit(records)
    encoded = json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")


if __name__ == "__main__":
    main()

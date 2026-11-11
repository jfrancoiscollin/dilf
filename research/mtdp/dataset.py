"""Build a reproducible JSONL research dataset from curated Dubois fixtures.

Only the standard library and the existing dilf modules are required.
The source diagrams are not claimed to be a representative sample of games.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from pedagogy.game import GameState, state_to_fen
from research.mtdp.metrics import compute_spatial_metrics


def record(state: GameState, *, source: str, source_id: str,
           metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    """One versioned observation with provenance and descriptive metrics."""
    fen = state_to_fen(state)
    return {
        "schema_version": "mtdp-position-v1",
        "position_hash": hashlib.sha256(fen.encode("utf-8")).hexdigest()[:16],
        "source": source,
        "source_id": source_id,
        "metadata": metadata or {},
        "metrics": compute_spatial_metrics(state).as_dict(),
    }


def dubois_records() -> Iterable[dict[str, Any]]:
    """Read the existing fixture module; no PDF/OCR dependencies."""
    from pedagogy.tests.fixtures.dubois_diagrams import ALL_DIAGRAMS, to_state

    for diagram in ALL_DIAGRAMS:
        yield record(
            to_state(diagram),
            source="dubois_diagram_fixture",
            source_id=diagram.crop_id,
            metadata={
                "page": diagram.page,
                "region_index": diagram.region_index,
                "caption": diagram.caption_text,
                "extraction_confidence": diagram.confidence,
                "king_detection_verified": False,
            },
        )


def write_jsonl(records: Iterable[dict[str, Any]], output: Path) -> int:
    """Write a stable, newline-delimited dataset, returning the record count."""
    output.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with output.open("w", encoding="utf-8", newline="\n") as stream:
        for item in records:
            stream.write(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n")
            count += 1
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description="Build MTDP Dubois research dataset")
    parser.add_argument("--output", type=Path, default=Path(".cache/mtdp/dubois.jsonl"))
    args = parser.parse_args()
    print(f"Wrote {write_jsonl(dubois_records(), args.output)} records to {args.output}")


if __name__ == "__main__":
    main()

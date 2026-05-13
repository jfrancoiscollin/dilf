"""Hand-verified Dubois positions used as few-shot examples for the OCR pipeline.

Each :class:`FewShotExample` pairs a PNG crop image (relative to this file's
directory) with the expected JSON payload Claude Vision should produce. The
``scripts/extract_diagrams.py`` extract step prepends ``N`` of these examples
to every API call as ``[user: image, assistant: json]`` pairs when invoked
with ``--few-shot N``.

How to add an entry:

1. Pick a crop you have visually verified end-to-end (every square correct,
   piece colour/type correct, turn matches the caption).
2. Copy the PNG into ``pedagogy/tests/fixtures/few_shot_images/``.
3. Add a ``FewShotExample`` here. ``position`` keys must match the API
   schema exactly: ``white_men``, ``white_kings``, ``black_men``,
   ``black_kings``, ``turn``, ``confidence``.

Cost note: each example adds ~2k input tokens per API call (the image plus
its JSON answer). At Sonnet pricing, 3 examples cost roughly +$0.02 per
crop, ~$7 extra on a full V4 run. Worth it only when the examples cover
piece-type ambiguity (man vs king), unusual orientations, or dense
positions the base prompt struggles with.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class FewShotExample:
    """One hand-verified (image, position) pair."""

    name: str
    image_filename: str   # under pedagogy/tests/fixtures/few_shot_images/
    position: dict[str, Any] = field(default_factory=dict)


FEW_SHOT_IMAGES_DIR = Path(__file__).parent / "few_shot_images"


#: Ordered list of validated examples. Empty by default; populate from a
#: confirmed-correct run before bumping ``--few-shot`` above 0.
EXAMPLES: list[FewShotExample] = []


def load_examples(n: int) -> list[tuple[bytes, dict[str, Any]]]:
    """Return the first ``n`` (image_bytes, position) pairs.

    Returns an empty list if ``n <= 0`` or there are no examples on disk.
    Raises :class:`FileNotFoundError` if a referenced image is missing.
    """
    if n <= 0 or not EXAMPLES:
        return []
    out: list[tuple[bytes, dict[str, Any]]] = []
    for example in EXAMPLES[:n]:
        img_path = FEW_SHOT_IMAGES_DIR / example.image_filename
        if not img_path.exists():
            raise FileNotFoundError(
                f"few-shot image missing: {img_path} (referenced by {example.name})"
            )
        out.append((img_path.read_bytes(), example.position))
    return out

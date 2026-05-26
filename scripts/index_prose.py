"""Prose-indexing pipeline — strategic counterpart to extract_diagrams.py.

Implements CADRAGE_STRATEGIE.md §5.1: turn a strategic-corpus PDF
(Sijbrands, Springer, Keller, Roozenburg…) into a Python module
exposing ``ALL_PASSAGES`` as a frozen tuple of
:class:`pedagogy.prose.passages.ProsePassage`.

Five idempotent subcommands chained by ``all``::

    extract   PDF        -> per-page .txt via pdftotext -layout
    chunk     pages      -> per-paragraph passages with stable passage_id
    tag       chunks     -> system / phase / nature heuristics
    embed     chunks     -> sentence-transformers vectors (optional)
    emit      tagged     -> pedagogy/prose/fixtures/prose_passages_<src>.py

Requires ``poppler-utils`` (``pdftotext``) on ``PATH``. Embeddings
are optional — when ``sentence-transformers`` isn't installed, the
``embed`` step is a no-op and the emit module omits the sidecar.

The skeleton is deliberately minimal: the chunking heuristic is a
single regex (blank lines = paragraph boundaries), the tag detection
is a small keyword table, and the emit format is a flat module.
Each step is a pure function that can be replaced incrementally
without breaking the others.

Run from the dilf repo root::

    python3 scripts/index_prose.py all --pdf path/to/sijbrands.pdf --source SIJBRANDS --book classique
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import shutil
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Iterable, List, Optional

# ── Project import path ────────────────────────────────────────────────
_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO))

from pedagogy.prose.passages import ProsePassage  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("index_prose")

DEFAULT_CACHE = Path(".cache/prose")
DEFAULT_OUTPUT_DIR = Path("pedagogy/prose/fixtures")

# ── System keyword table ──
# Used by `tag` to attach a passage to one or more opening / strategic
# systems. Order matters: more specific names first. The regex matches
# whole words case-insensitively to avoid "classique" picking up
# "néoclassique" without a tag of its own.
_SYSTEM_KEYWORDS: dict[str, tuple[str, ...]] = {
    "roozenburg": (r"\broozenburg\b",),
    "keller":     (r"\bkeller\b",),
    "ghestem":    (r"\bghestem\b",),
    "manoury":    (r"\bmanoury\b",),
    "springer":   (r"\bspringer\b",),
    "classique":  (r"\bclassique\b", r"\bsystème classique\b", r"\bjeu classique\b"),
}

_PHASE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "ouverture": (r"\bouverture\b", r"\bdébut\b", r"\bpremiers coups\b"),
    "milieu":    (r"\bmilieu de (?:la )?partie\b", r"\bmilieu de jeu\b"),
    "finale":    (r"\bfinale\b", r"\bfinales\b", r"\bend(?:game|ing)\b"),
}

_NATURE_KEYWORDS: dict[str, tuple[str, ...]] = {
    # Order matters here too — "avertissement" wins over "principe" when both match.
    "avertissement": (r"\bpiège\b", r"\bgare à\b", r"\bne (?:jamais|pas)\b", r"\bdanger\b"),
    "plan":          (r"\bplan\b", r"\bstratégie\b", r"\bobjectif\b", r"\bil faut\b"),
    "principe":      (r"\bprincipe\b", r"\brègle\b", r"\bidée\b"),
}


# ── Step 1: extract ──────────────────────────────────────────────────────
def extract_pdf(pdf: Path, cache: Path) -> List[Path]:
    """Run ``pdftotext -layout`` page by page; cache one .txt per page.

    Returns the list of per-page text files in page order. Idempotent
    via cache hits — re-running on the same PDF skips already-extracted
    pages.
    """
    if shutil.which("pdftotext") is None:
        raise RuntimeError("pdftotext not found on PATH. Install poppler-utils.")
    cache.mkdir(parents=True, exist_ok=True)
    # First, get total page count via pdfinfo (also from poppler-utils).
    info = subprocess.check_output(["pdfinfo", str(pdf)], text=True)
    m = re.search(r"^Pages:\s+(\d+)", info, re.MULTILINE)
    if not m:
        raise RuntimeError(f"pdfinfo gave no page count for {pdf}")
    n_pages = int(m.group(1))

    outputs: List[Path] = []
    for page in range(1, n_pages + 1):
        out = cache / f"page_{page:04d}.txt"
        outputs.append(out)
        if out.exists():
            continue
        subprocess.check_call(
            ["pdftotext", "-layout", "-f", str(page), "-l", str(page), str(pdf), str(out)]
        )
    log.info("extract: %d pages -> %s", n_pages, cache)
    return outputs


# ── Step 2: chunk ────────────────────────────────────────────────────────
# A "passage" is a paragraph: a contiguous run of non-blank lines on the
# same page. Blank lines (≥1 empty line) delimit paragraphs. Lines that
# look like page headers/footers (digits only, or "page N", or all caps
# < 4 words) are skipped before chunking so they don't fragment a real
# paragraph and don't get tagged.

_PAGE_NOISE = re.compile(
    r"^\s*(?:\d+|page\s*\d+|chapitre\s+\d+\s*[—-]?\s*.*)\s*$",
    re.IGNORECASE,
)


def _strip_page_noise(text: str) -> str:
    return "\n".join(
        line for line in text.splitlines() if not _PAGE_NOISE.match(line)
    )


def chunk_pages(
    pages: Iterable[Path], source: str, book: str, min_chars: int = 80
) -> List[ProsePassage]:
    """Split each page into paragraphs and wrap them in ``ProsePassage``.

    Paragraphs shorter than ``min_chars`` are dropped (page numbers,
    captions, leftover noise). The ``passage_id`` is deterministic
    given (source, book, page, index-on-page), so re-running on the
    same input yields byte-identical ids.
    """
    passages: List[ProsePassage] = []
    for page_path in pages:
        m = re.search(r"page_(\d+)\.txt$", page_path.name)
        if not m:
            continue
        page = int(m.group(1))
        text = page_path.read_text(encoding="utf-8")
        cleaned = _strip_page_noise(text)
        # Paragraph = run between blank lines.
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", cleaned) if p.strip()]
        para_idx = 0
        offset = 0
        for body in paragraphs:
            if len(body) < min_chars:
                offset = cleaned.find(body, offset) + len(body) if body in cleaned else offset
                continue
            try:
                char_offset = cleaned.index(body, offset)
            except ValueError:
                char_offset = -1
            offset = (char_offset + len(body)) if char_offset >= 0 else offset
            passages.append(
                ProsePassage(
                    passage_id=f"{source}_{book}_p{page:04d}_{para_idx:02d}",
                    text=body,
                    source=source,
                    book=book,
                    page=page,
                    char_offset=char_offset,
                )
            )
            para_idx += 1
    log.info("chunk: %d passages", len(passages))
    return passages


# ── Step 3: tag ──────────────────────────────────────────────────────────
def _match_first(table: dict[str, tuple[str, ...]], text: str) -> Optional[str]:
    for label, patterns in table.items():
        if any(re.search(p, text, flags=re.IGNORECASE) for p in patterns):
            return label
    return None


def _match_all(table: dict[str, tuple[str, ...]], text: str) -> tuple[str, ...]:
    hits = [
        label
        for label, patterns in table.items()
        if any(re.search(p, text, flags=re.IGNORECASE) for p in patterns)
    ]
    return tuple(hits)


def tag_passages(passages: Iterable[ProsePassage]) -> List[ProsePassage]:
    """Heuristic tagging. Pure function: returns new ProsePassage tuples
    rather than mutating. Multiple systems may match — the cadrage
    §4.S3 (attribution exacte) means we surface the ambiguity rather
    than guess one."""
    out: List[ProsePassage] = []
    for p in passages:
        systems = _match_all(_SYSTEM_KEYWORDS, p.text)
        phase = _match_first(_PHASE_KEYWORDS, p.text)
        nature = _match_first(_NATURE_KEYWORDS, p.text)
        out.append(
            ProsePassage(
                passage_id=p.passage_id,
                text=p.text,
                source=p.source,
                book=p.book,
                page=p.page,
                char_offset=p.char_offset,
                systems=systems,
                phase=phase,
                nature=nature,
                embedding=p.embedding,
            )
        )
    n_tagged = sum(1 for p in out if p.systems or p.phase or p.nature)
    log.info("tag: %d/%d passages received at least one tag", n_tagged, len(out))
    return out


# ── Step 4: embed ────────────────────────────────────────────────────────
def embed_passages(
    passages: List[ProsePassage],
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    lsa_dim: int = 384,
) -> List[ProsePassage]:
    """Dense-vector embedding with graceful fallbacks.

    Three paths, in order of preference:

    1. **sentence-transformers** — best semantic quality. Requires the
       library AND network access to download the model. Used when both
       are available.
    2. **TF-IDF + Truncated SVD (LSA)** — sklearn-only fallback. Fully
       offline, deterministic, ~384 dims out of TruncatedSVD so the
       sidecar size matches the sentence-transformers path. Quality is
       lower than dense neural embeddings but workable for a technical
       corpus where vocabulary carries most of the signal.
    3. **No-op** — neither library available; return passages unchanged
       with a warning. The rest of the pipeline still runs.

    Stays a pure function: returns a new list, doesn't mutate inputs.
    """
    # Try path 1: sentence-transformers + network
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore
        try:
            model = SentenceTransformer(model_name)
            vectors = model.encode([p.text for p in passages], show_progress_bar=False)
            method = "sentence-transformers"
        except OSError as e:
            # Typically "couldn't connect to huggingface.co" in offline envs.
            log.warning("embed: sentence-transformers model unavailable (%s) — falling back to TF-IDF+LSA", e.__class__.__name__)
            raise
    except (ImportError, OSError):
        # Try path 2: sklearn TF-IDF + LSA
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer  # type: ignore
            from sklearn.decomposition import TruncatedSVD  # type: ignore
            import numpy as np  # type: ignore
        except ImportError:
            log.warning(
                "embed: neither sentence-transformers nor scikit-learn available — skipping. "
                "Install one with: pip install sentence-transformers  OR  pip install scikit-learn"
            )
            return passages
        texts = [p.text for p in passages]
        # max_features caps memory; sublinear_tf damps long-passage bias.
        vec = TfidfVectorizer(
            max_features=20_000,
            sublinear_tf=True,
            ngram_range=(1, 2),
            min_df=2,
        )
        tfidf = vec.fit_transform(texts)
        # Ensure n_components ≤ n_features and ≤ n_samples-1.
        n_comp = min(lsa_dim, tfidf.shape[1] - 1, tfidf.shape[0] - 1)
        if n_comp < 2:
            log.warning("embed: corpus too small for TF-IDF+LSA (n=%d) — skipping", len(texts))
            return passages
        svd = TruncatedSVD(n_components=n_comp, random_state=0)
        vectors = svd.fit_transform(tfidf)
        # Row-normalize so cosine-sim ≈ dot product downstream.
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        vectors = vectors / np.where(norms > 0, norms, 1.0)
        method = f"tfidf+lsa(d={n_comp})"

    out: List[ProsePassage] = []
    for p, v in zip(passages, vectors):
        out.append(
            ProsePassage(
                passage_id=p.passage_id, text=p.text, source=p.source, book=p.book,
                page=p.page, char_offset=p.char_offset, systems=p.systems,
                phase=p.phase, nature=p.nature, embedding=tuple(float(x) for x in v),
            )
        )
    log.info("embed: %d vectors (dim=%d, method=%s)", len(out), len(out[0].embedding) if out else 0, method)
    return out


# ── Step 5: emit ─────────────────────────────────────────────────────────
_MODULE_HEADER = '''"""Auto-generated by scripts/index_prose.py — do not edit by hand.

Source : {pdf}
Pipeline : extract → chunk → tag → emit
Cadrage : CADRAGE_STRATEGIE.md §5.1

Each entry is a verbatim paragraph extracted from the source PDF.
Embeddings, when present, ship in the sidecar `.embeddings.npy`
alongside this module (same row order as ALL_PASSAGES).
"""
from __future__ import annotations

from pedagogy.prose.passages import ProsePassage

ALL_PASSAGES: tuple[ProsePassage, ...] = (
'''


def emit_module(passages: List[ProsePassage], out_path: Path, pdf_path: Path) -> Path:
    """Write a Python module exposing ALL_PASSAGES. Each ProsePassage
    is rendered as a literal constructor call so the file is both
    machine-generated and human-readable. Embeddings, when present,
    are stripped from the literal (kept in the sidecar)."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = [_MODULE_HEADER.format(pdf=pdf_path.name)]
    for p in passages:
        # Triple-quoted body, escape any """ inside the verbatim text.
        body = p.text.replace('"""', '\\"\\"\\"')
        lines.append("    ProsePassage(")
        lines.append(f"        passage_id={p.passage_id!r},")
        lines.append(f'        text="""{body}""",')
        lines.append(f"        source={p.source!r},")
        lines.append(f"        book={p.book!r},")
        lines.append(f"        page={p.page!r},")
        lines.append(f"        char_offset={p.char_offset!r},")
        lines.append(f"        systems={p.systems!r},")
        lines.append(f"        phase={p.phase!r},")
        lines.append(f"        nature={p.nature!r},")
        lines.append("    ),")
    lines.append(")\n")
    out_path.write_text("\n".join(lines), encoding="utf-8")
    log.info("emit: %d passages → %s", len(passages), out_path)
    return out_path


def emit_embeddings_sidecar(passages: List[ProsePassage], module_path: Path) -> Optional[Path]:
    """Write the embedding matrix alongside the module as a .npy file."""
    has_vec = [p for p in passages if p.embedding is not None]
    if not has_vec:
        return None
    try:
        import numpy as np  # type: ignore
    except ImportError:
        log.warning("emit: numpy missing, skipping embeddings sidecar")
        return None
    sidecar = module_path.with_suffix(".embeddings.npy")
    matrix = np.array([p.embedding for p in passages], dtype="float32")
    np.save(sidecar, matrix)
    log.info("emit: sidecar %s (shape=%s)", sidecar, matrix.shape)
    return sidecar


# ── CLI ──────────────────────────────────────────────────────────────────
def _cmd_extract(args: argparse.Namespace) -> int:
    extract_pdf(args.pdf, args.cache)
    return 0


def _cmd_chunk(args: argparse.Namespace) -> int:
    pages = sorted(args.cache.glob("page_*.txt"))
    if not pages:
        log.error("chunk: no extracted pages in %s — run `extract` first.", args.cache)
        return 1
    passages = chunk_pages(pages, args.source, args.book, args.min_chars)
    args.intermediate.write_text(
        json.dumps([asdict(p) for p in passages], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return 0


def _cmd_tag(args: argparse.Namespace) -> int:
    raw = json.loads(args.intermediate.read_text(encoding="utf-8"))
    passages = [ProsePassage(**{k: v for k, v in r.items() if k != "embedding"} | {"embedding": None}) for r in raw]
    tagged = tag_passages(passages)
    args.intermediate.write_text(
        json.dumps([asdict(p) for p in tagged], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return 0


def _cmd_embed(args: argparse.Namespace) -> int:
    raw = json.loads(args.intermediate.read_text(encoding="utf-8"))
    passages = [ProsePassage(**{k: v for k, v in r.items() if k != "embedding"} | {"embedding": None}) for r in raw]
    embedded = embed_passages(passages)
    args.intermediate.write_text(
        json.dumps([asdict(p) for p in embedded], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return 0


def _cmd_emit(args: argparse.Namespace) -> int:
    raw = json.loads(args.intermediate.read_text(encoding="utf-8"))
    passages = [
        ProsePassage(
            passage_id=r["passage_id"], text=r["text"], source=r["source"], book=r["book"],
            page=r["page"], char_offset=r["char_offset"],
            systems=tuple(r.get("systems", ())),
            phase=r.get("phase"), nature=r.get("nature"),
            embedding=tuple(r["embedding"]) if r.get("embedding") else None,
        )
        for r in raw
    ]
    out = args.output_dir / f"prose_passages_{args.source.lower()}_{args.book}.py"
    emit_module(passages, out, args.pdf)
    emit_embeddings_sidecar(passages, out)
    return 0


def _cmd_all(args: argparse.Namespace) -> int:
    rc = _cmd_extract(args)
    if rc: return rc
    rc = _cmd_chunk(args)
    if rc: return rc
    rc = _cmd_tag(args)
    if rc: return rc
    rc = _cmd_embed(args)
    if rc: return rc
    return _cmd_emit(args)


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--cache", type=Path, default=DEFAULT_CACHE,
                   help="Directory for cached per-page .txt and intermediates.")
    p.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR,
                   help="Where the emitted prose_passages_*.py module lives.")
    sub = p.add_subparsers(dest="cmd", required=True)

    for name, fn in (
        ("extract", _cmd_extract), ("chunk", _cmd_chunk), ("tag", _cmd_tag),
        ("embed", _cmd_embed), ("emit", _cmd_emit), ("all", _cmd_all),
    ):
        s = sub.add_parser(name, help=fn.__doc__)
        s.add_argument("--pdf", type=Path, required=(name in ("extract", "all", "emit")),
                       help="Source PDF.")
        s.add_argument("--source", type=str, required=(name in ("chunk", "all", "emit")),
                       help="Uppercase source code, e.g. SIJBRANDS.")
        s.add_argument("--book", type=str, required=(name in ("chunk", "all", "emit")),
                       help="Book slug, e.g. classique.")
        s.add_argument("--min-chars", type=int, default=80,
                       help="Drop paragraphs shorter than this (default 80).")
        s.set_defaults(func=fn)

    args = p.parse_args(argv)
    args.cache = args.cache.resolve()
    args.output_dir = args.output_dir.resolve()
    args.intermediate = args.cache / "passages.json"
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

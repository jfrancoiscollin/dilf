"""Downloader for the priority-1 reference corpus.

Run this script from a machine that has internet access; it populates
``docs/livres/`` with the PDF tree described in section 5 of
``CORPUS REFERENCE DAMES.pdf``. It uses only the Python standard library
(``urllib``) and is idempotent: re-running skips files that already exist
with a non-zero size.

Sources
-------
* **Dubois** -- 10 free volumes on the FMJD promo page
  (https://www.fmjd.org/promo/jpd/download/). Volume 11 ("La partie
  classique", 2016) is commercial and is intentionally NOT downloaded.
* **Goedemoed** -- A Course in Draughts series and TAOW endgame, hosted at
  https://www.fmjd.org/downloads/Course/.
* **FFJD** -- Livret officiel and Les Enchaînements, hosted at
  https://www.ffjd.fr/fichiers/livres/.
* **Manoury 1770** -- Le jeu de dames à la polonoise, scanned by Gallica BNF.
* **Bonnard 1920-1931** -- the Damier Lyonnais hosts a multi-issue archive
  whose individual URLs are not enumerated in the corpus. Fetching this
  collection is a manual step; see ``--print-bonnard-instructions``.

Usage
-----
    python scripts/fetch_corpus_p1.py                     # download everything
    python scripts/fetch_corpus_p1.py --dry-run           # just list actions
    python scripts/fetch_corpus_p1.py --only dubois ffjd  # subset by editor
    python scripts/fetch_corpus_p1.py --target /tmp/dl    # custom target dir
    python scripts/fetch_corpus_p1.py --skip-bonnard      # silence the warning

Exit codes
----------
0   all downloads succeeded (or were already present)
1   one or more downloads failed
2   bad CLI arguments

Note on copyright (cf. corpus §6.7): every PDF retrieved here remains under
its author's copyright. The corpus authorises storage in a private repo for
personal use only. If this project is ever published as an open package, the
PDFs must not ship with it -- this script is the canonical replacement.
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import shutil
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

USER_AGENT = "dilf-fetch-corpus/0.1 (+https://github.com/jfrancoiscollin/dilf)"
CHUNK_SIZE = 64 * 1024
HTTP_TIMEOUT_SECONDS = 60
MAX_ATTEMPTS = 4
BACKOFF_BASE_SECONDS = 2


@dataclasses.dataclass(frozen=True)
class CorpusEntry:
    """One PDF to fetch.

    ``editor`` doubles as the sub-directory name inside ``docs/livres/``.
    ``local_name`` is the renamed file as recommended by corpus §5 (it
    replaces spaces and accented punctuation that some web servers mangle
    on download).
    """

    editor: str
    url: str
    local_name: str

    @property
    def relative_path(self) -> Path:
        return Path(self.editor) / self.local_name


# ---------------------------------------------------------------------------
# Catalog -- mirror of CORPUS REFERENCE DAMES.pdf section 1 (priorité P1).
# ---------------------------------------------------------------------------

_DUBOIS_ROOT = "https://www.fmjd.org/promo/jpd/download/"
DUBOIS: tuple[CorpusEntry, ...] = tuple(
    CorpusEntry(editor="dubois", url=_DUBOIS_ROOT + name, local_name=name)
    for name in (
        "jpdubois_level_1_combinations_V2.pdf",
        "jpdubois_level_1_openings_V0.pdf",
        "jpdubois_level_1_end_games_V0.pdf",
        "jpdubois_level_1_strategy_V0.pdf",
        "jpdubois_perfectionnement_combinaisons_V4.pdf",
        "jpdubois_level_2_fundamentals_V0.pdf",
        "jpdubois_level_2_locks_and_edge_pieces_V0.pdf",
        "jpdubois_level_2_offensive_and_side_play_V0.pdf",
        "jpdubois_level_2_end_games_V0.pdf",
        "maitrise-du-jeu-de-dames-dubois.pdf",
    )
)


_GOEDEMOED_ROOT = "https://www.fmjd.org/downloads/Course/"


def _goedemoed(remote_relative: str, local_name: str) -> CorpusEntry:
    """Build a Goedemoed entry, URL-encoding spaces in the remote path."""
    quoted = urllib.parse.quote(remote_relative, safe="/")
    return CorpusEntry(
        editor="goedemoed",
        url=_GOEDEMOED_ROOT + quoted,
        local_name=local_name,
    )


GOEDEMOED: tuple[CorpusEntry, ...] = (
    _goedemoed("en/Course in draughts.pdf", "Course_in_draughts.pdf"),
    _goedemoed("en/Introductory course in draughts.pdf", "Introductory_course.pdf"),
    _goedemoed("en/Course 3/S1.Using tactics as a weapon.pdf", "S1_Using_tactics.pdf"),
    _goedemoed("en/Course 3/S2.The opening of the game.pdf", "S2_Opening_of_the_game.pdf"),
    _goedemoed("en/Course 3/S3.Strategy.pdf", "S3_Strategy.pdf"),
    _goedemoed("en/Course 3/S4.The thinking process.pdf", "S4_Thinking_process.pdf"),
    _goedemoed("en/Course 3/S5.The endgame.pdf", "S5_Endgame.pdf"),
    _goedemoed("en/Course 3/S6.Finishing of the game.pdf", "S6_Finishing.pdf"),
    _goedemoed("en/Course 3/S7.Compositions.pdf", "S7_Compositions.pdf"),
    _goedemoed("en/Exercise_3.pdf", "Exercise_3.pdf"),
    _goedemoed("books/taow/en/1.The_endgame(online).pdf", "TAOW_endgame.pdf"),
    _goedemoed("books/taow/en/0.1.Preface(online).pdf", "TAOW_preface.pdf"),
)


FFJD: tuple[CorpusEntry, ...] = (
    CorpusEntry(
        editor="ffjd",
        url="https://www.ffjd.fr/fichiers/livres/livret-ffjd.pdf",
        local_name="livret-ffjd.pdf",
    ),
    CorpusEntry(
        editor="ffjd",
        url="https://www.ffjd.fr/fichiers/livres/Les_enchainements.pdf",
        local_name="Les_enchainements.pdf",
    ),
)


# Gallica exposes a direct PDF endpoint for many holdings; this is the
# canonical pattern. If a future Gallica change breaks it, see
# https://gallica.bnf.fr/services/Download for the manual downloader.
MANOURY: tuple[CorpusEntry, ...] = (
    CorpusEntry(
        editor="historique",
        url="https://gallica.bnf.fr/ark:/12148/bpt6k3045213j.pdf",
        local_name="manoury_1770_jeu_polonais.pdf",
    ),
)


# Bonnard 1920-1931: the corpus does not list per-issue URLs, only a root
# (http://damierlyonnais.free.fr/) and a presentation page. We surface a
# clear manual-fetch instruction instead of guessing 120 URLs.
BONNARD_INSTRUCTIONS = """\
Bonnard -- Revue Le Jeu de Dames 1920-1931 (manual fetch)
---------------------------------------------------------
The corpus does not enumerate individual PDF URLs for this archive. To
populate docs/livres/historique/bonnard_revue_1920-1931/ :

  1. Visit  http://damierlyonnais.free.fr/
     and    https://damerlepion.over-blog.fr/article-telecharger-la-revue-le-
            jeu-de-dames-1920-1931-de-m-bonnard-90628112.html
  2. Download the per-year archives (~120 issues total).
  3. Drop the resulting PDFs (or sub-archives) into
        docs/livres/historique/bonnard_revue_1920-1931/

This script will skip Bonnard automatically; pass --skip-bonnard to suppress
the printed reminder.
"""


ALL_ENTRIES: tuple[CorpusEntry, ...] = DUBOIS + GOEDEMOED + FFJD + MANOURY
EDITORS: tuple[str, ...] = ("dubois", "goedemoed", "ffjd", "historique")


# ---------------------------------------------------------------------------
# Download engine
# ---------------------------------------------------------------------------


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(CHUNK_SIZE), b""):
            h.update(chunk)
    return h.hexdigest()


def _download(entry: CorpusEntry, dest: Path, verbose: bool) -> None:
    """Stream ``entry.url`` to ``dest`` with retries and atomic rename."""
    tmp = dest.with_suffix(dest.suffix + ".part")
    request = urllib.request.Request(entry.url, headers={"User-Agent": USER_AGENT})
    last_error: Exception | None = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as resp:
                total = resp.headers.get("Content-Length")
                if verbose and total:
                    print(f"    -> {int(total) / 1024:.1f} KiB advertised")
                with tmp.open("wb") as out:
                    shutil.copyfileobj(resp, out, length=CHUNK_SIZE)
            tmp.replace(dest)
            return
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            last_error = exc
            wait = BACKOFF_BASE_SECONDS ** attempt
            if attempt < MAX_ATTEMPTS:
                print(
                    f"    [attempt {attempt}/{MAX_ATTEMPTS}] {exc}; retry in {wait}s",
                    file=sys.stderr,
                )
                time.sleep(wait)
            else:
                if tmp.exists():
                    tmp.unlink()
    raise RuntimeError(f"All attempts failed for {entry.url}") from last_error


def fetch(entries: list[CorpusEntry], target: Path, dry_run: bool, verbose: bool) -> int:
    """Fetch ``entries`` under ``target``. Returns count of failures."""
    failures = 0
    manifest_lines: list[str] = []
    for entry in entries:
        dest = target / entry.relative_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists() and dest.stat().st_size > 0:
            if verbose:
                print(f"[skip] {entry.relative_path} (already present)")
            manifest_lines.append(f"{_sha256(dest)}  {entry.relative_path}")
            continue
        print(f"[get ] {entry.relative_path}  <-  {entry.url}")
        if dry_run:
            continue
        try:
            _download(entry, dest, verbose=verbose)
            manifest_lines.append(f"{_sha256(dest)}  {entry.relative_path}")
        except Exception as exc:  # noqa: BLE001 - we want every failure logged
            failures += 1
            print(f"    FAILED: {exc}", file=sys.stderr)
    if not dry_run and manifest_lines:
        (target / "CHECKSUMS.txt").write_text(
            "# sha256  path (regenerated by fetch_corpus_p1.py)\n"
            + "\n".join(sorted(manifest_lines))
            + "\n",
            encoding="utf-8",
        )
    return failures


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--target",
        default="docs/livres",
        type=Path,
        help="directory under which to write the editor sub-trees (default: docs/livres)",
    )
    parser.add_argument(
        "--only",
        nargs="+",
        choices=EDITORS,
        help="restrict to the given editors (default: all)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print what would be downloaded but make no HTTP requests",
    )
    parser.add_argument(
        "--skip-bonnard",
        action="store_true",
        help="do not print the manual-fetch instructions for the Bonnard revue",
    )
    parser.add_argument(
        "--print-bonnard-instructions",
        action="store_true",
        help="print only the Bonnard manual instructions and exit",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="emit per-file progress information",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)

    if args.print_bonnard_instructions:
        print(BONNARD_INSTRUCTIONS)
        return 0

    selected_editors = set(args.only) if args.only else set(EDITORS)
    entries = [e for e in ALL_ENTRIES if e.editor in selected_editors]

    if not entries:
        print("No entries match the selected editors.", file=sys.stderr)
        return 2

    target: Path = args.target.resolve()
    print(f"Target tree : {target}")
    print(f"Entries     : {len(entries)} PDF(s) across {sorted(selected_editors)}")
    if args.dry_run:
        print("Mode        : DRY-RUN (no network calls)")

    failures = fetch(entries, target, dry_run=args.dry_run, verbose=args.verbose)

    if "historique" in selected_editors and not args.skip_bonnard:
        print()
        print(BONNARD_INSTRUCTIONS)

    if failures:
        print(f"\n{failures} download(s) failed.", file=sys.stderr)
        return 1
    print("\nDone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

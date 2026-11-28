"""Explicit research-only king-origin-v1 factory; never changes default rules."""
import sys
import types
from pathlib import Path

from research.mtdp.draught_master_adapter import DraughtMasterRules
from research.mtdp.fresh_candidate_integrity_replay import digest
from research.mtdp.jass_benchmark.named_arena_replay import checked_engine

PATCH_ID='king-origin-v1'
BASE_RULES_SHA='5855ceae76fc7db243af85c61508d9505e17904925b9f73d79ed327296690394'
BEFORE='            piece = board[s]\n'
AFTER='            piece = EMPTY if s == path[0] else board[s]\n'


def patch_source(raw):
    if digest(raw)!=BASE_RULES_SHA:
        raise ValueError('expected exact pinned base rules bytes')
    source=raw.decode('utf-8')
    start=source.index('def _capture_sequences_king(')
    end=source.index('\n\ndef _all_captures(',start)
    section=source[start:end]
    if section.count(BEFORE)!=1:
        raise ValueError('expected exactly one king ray read')
    patched=source[:start]+section.replace(BEFORE,AFTER,1)+source[end:]
    return patched.encode('utf-8')


def corrected_engine(adapter):
    legacy=checked_engine(Path(adapter).resolve())
    raw=Path(legacy._rules.__file__).read_bytes()
    corrected=patch_source(raw)
    name='_mtdp_research_king_origin_v1_'+digest(corrected)
    if name not in sys.modules:
        module=types.ModuleType(name)
        module.__file__=str(Path(legacy._rules.__file__).resolve())+'['+PATCH_ID+']'
        module.__mtdp_corrected_source_sha256__=digest(corrected)
        # Dataclass type resolution requires the isolated module name registered.
        sys.modules[name]=module
        try:
            exec(compile(corrected,module.__file__,'exec'),module.__dict__)
        except BaseException:
            sys.modules.pop(name,None)
            raise
    module=sys.modules[name]
    if module.__mtdp_corrected_source_sha256__!=digest(corrected):
        raise ValueError('research module identity mismatch')
    return DraughtMasterRules(module),dict(patch_id=PATCH_ID,base_rules_sha256=digest(raw),
        corrected_rules_sha256=digest(corrected),default_rules_changed=False)

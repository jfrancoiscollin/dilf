"""D1-C chronological metadata guard: SHA binds order but cannot prove it."""
def audit_ply_order(records):
    """Require explicit ascending ply indices per (source, game); no scores."""
    if not isinstance(records, list) or not records:
        raise ValueError("nonempty ordered records required")
    last, events, problems = {}, {}, []
    for i, row in enumerate(records):
        if not isinstance(row, dict):
            raise ValueError("candidate row must be an object")
        source, game, event, ply = (row.get(k) for k in ("source_id", "game_id", "event_id", "ply"))
        if not all(isinstance(x, str) and x.strip() for x in (source, game, event)):
            problems.append({"index": i, "reason": "missing_identity"})
            continue
        key = (source, game)
        if key in events and events[key] != event:
            problems.append({"index": i, "reason": "game_event_changed"})
        events[key] = event
        if type(ply) is not int or ply < 0:
            problems.append({"index": i, "reason": "missing_or_invalid_ply"})
            continue
        if key in last and ply <= last[key]:
            problems.append({"index": i, "reason": "non_increasing_ply"})
        last[key] = ply
    return {"chronological_metadata_pass": not problems, "problems": problems,
            "external_ply_provenance_authenticated": False}

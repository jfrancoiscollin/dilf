"""Synthetic lexical tests, not legality or equivalence claims."""
import pytest
from research.mtdp.decision_equivalence.fmjd_move_tokens import validate_move_token


@pytest.mark.parametrize("token", ["31-26", "1-6", "50-45", "12x23", "12x23x34", "1x12x23x34"])
def test_accepts_bounded_lexical_tokens(token):
    assert validate_move_token(token) == token


@pytest.mark.parametrize("token", [
    "", None, 42, "0-5", "51-46", "31-0", "31-51", "01-06",
    "31--26", "31:26", "31X26", "31-26-21", "12x23-34",
    "12x23x12", "31-31", " 31-26", "31-26 ", "31-26\\n",
    "٣١-٢٦", "31−26", "31x", "31x23x51",
])
def test_rejects_unsupported_or_ambiguous_tokens(token):
    with pytest.raises(ValueError):
        validate_move_token(token)

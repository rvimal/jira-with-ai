import pytest

from app.services.response_parser import JsonResponseParser, ResponseValidationError


def test_parse_valid_payload() -> None:
    parser = JsonResponseParser()
    result = parser.parse(
        '{"ticket_id":"PROJ-1","score":88,"reason":"High impact","confidence":0.92}'
    )
    assert result.ticket_id == "PROJ-1"
    assert result.score == 88
    assert result.reason == "High impact"
    assert result.confidence == 0.92


def test_parse_rejects_missing_keys() -> None:
    parser = JsonResponseParser()
    with pytest.raises(ResponseValidationError):
        parser.parse('{"ticket_id":"PROJ-1","score":88}')


def test_parse_rejects_out_of_range_score() -> None:
    parser = JsonResponseParser()
    with pytest.raises(ResponseValidationError):
        parser.parse(
            '{"ticket_id":"PROJ-1","score":101,"reason":"x","confidence":0.2}'
        )

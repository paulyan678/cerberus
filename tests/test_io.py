from __future__ import annotations

import io

import pytest

from cerberus.io import DataFormatError, load_json, load_jsonl, read_jsonl, write_jsonl


def test_jsonl_round_trip_is_compact_unicode_and_ignores_blank_lines() -> None:
    stream = io.StringIO()
    records = [{"id": 1, "label": "门口"}, {"id": 2, "active": True}]

    write_jsonl(records, stream)

    assert stream.getvalue() == ('{"id":1,"label":"门口"}\n{"id":2,"active":true}\n')
    assert list(read_jsonl(io.StringIO("\n" + stream.getvalue() + "  \n"))) == records


def test_read_jsonl_reports_the_source_line_for_invalid_json() -> None:
    stream = io.StringIO('{"ok": true}\n\n{"broken": }\n')

    with pytest.raises(DataFormatError, match="Invalid JSON on line 3"):
        list(read_jsonl(stream))


@pytest.mark.parametrize(
    ("value", "type_name"),
    [("[]", "list"), ("null", "NoneType"), ('"text"', "str")],
)
def test_read_jsonl_requires_objects(value: str, type_name: str) -> None:
    with pytest.raises(
        DataFormatError, match=f"Expected a JSON object on line 1, got {type_name}"
    ):
        list(read_jsonl(io.StringIO(value)))


def test_path_loaders_use_utf8_and_return_expected_values(tmp_path) -> None:
    jsonl_path = tmp_path / "events.jsonl"
    json_path = tmp_path / "ground-truth.json"
    jsonl_path.write_text('{"event":"包裹"}\n', encoding="utf-8")
    json_path.write_text('{"query":["camera.mp4"]}', encoding="utf-8")

    assert load_jsonl(jsonl_path) == [{"event": "包裹"}]
    assert load_json(json_path) == {"query": ["camera.mp4"]}

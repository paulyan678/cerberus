from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any

import pytest

import cerberus.cli as cli
from cerberus.fixtures import file_sha256, validate_video_fixture


@pytest.fixture
def fixture_files(tmp_path: Path) -> tuple[Path, Path, list[dict[str, Any]]]:
    # Byte fixtures exercise hash/manifest mechanics, not video/model quality.
    clip = tmp_path / "clip.mp4"
    clip.write_bytes(b"unit-test bytes, not a real evaluation video")
    truth = tmp_path / "truth.json"
    truth.write_text(json.dumps({"package": ["clip.mp4"]}))
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "dataset_kind": "real_video",
                "dataset_id": "unit-test-contract-only",
                "annotator": "test fixture author",
                "annotation_method": "manual_video_review",
                "model_outputs_seen": False,
                "frozen_at": "2026-10-06T12:00:00+00:00",
                "ground_truth_sha256": file_sha256(truth),
                "queries": ["package"],
                "clips": [
                    {
                        "pathname": "clip.mp4",
                        "source": "unit-test byte fixture",
                        "rights": "test data",
                        "sha256": file_sha256(clip),
                    }
                ],
            }
        )
    )
    records = [{"pathname": "clip.mp4", "description": "an empty driveway"}]
    return manifest, truth, records


def test_fixture_cli_keeps_independent_labels_and_reports_missed_retrieval(
    fixture_files: tuple[Path, Path, list[dict[str, Any]]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest, truth, records = fixture_files
    records_path = manifest.parent / "records.jsonl"
    records_path.write_text(json.dumps(records[0]) + "\n")
    output = io.StringIO()
    monkeypatch.setattr(cli, "stdout", output)
    cli.ir_eval_main(
        [
            "--queries",
            "package",
            "--embeddings-file",
            str(records_path),
            "--ground-truth-file",
            str(truth),
            "--fixture-manifest",
            str(manifest),
            "--method",
            "sparse",
            "--return-k",
            "1",
            "--top-k",
            "1",
            "--json",
        ]
    )
    report = json.loads(output.getvalue())
    assert report["overall"]["recall_at_k"] == 0
    assert report["retrieval"]["method"] == "sparse"
    assert report["retrieval"]["embedding_model"] is None
    assert report["top_k"] == report["return_k"] == 1
    assert report["fixture"]["system_records_sha256"] == file_sha256(records_path)
    assert (
        report["fixture"]["validation"]
        == "file_hashes_and_declared_annotation_protocol"
    )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("dataset_kind", "synthetic", "real_video"),
        ("model_outputs_seen", True, "model_outputs_seen"),
        ("annotation_method", "model_labels", "manual_video_review"),
        ("annotator", "", "annotator"),
        ("queries", ["changed"], "ordered queries"),
        ("clips", [], "1-50 clips"),
        ("ground_truth_sha256", "wrong", "ground-truth SHA"),
        ("frozen_at", "2026-10-06", "timezone"),
    ],
)
def test_fixture_rejects_unfrozen_or_nonindependent_inputs(
    fixture_files: tuple[Path, Path, list[dict[str, Any]]],
    field: str,
    value: Any,
    message: str,
) -> None:
    manifest, truth, records = fixture_files
    data = json.loads(manifest.read_text())
    data[field] = value
    manifest.write_text(json.dumps(data))
    with pytest.raises(ValueError, match=message):
        validate_video_fixture(manifest, truth, records, ["package"])


def test_fixture_rejects_changed_clip_bytes(
    fixture_files: tuple[Path, Path, list[dict[str, Any]]],
) -> None:
    manifest, truth, records = fixture_files
    (manifest.parent / "clip.mp4").write_bytes(b"changed")
    with pytest.raises(ValueError, match="clip SHA"):
        validate_video_fixture(manifest, truth, records, ["package"])


def test_fixture_rejects_unknown_relevant_ids_even_with_updated_hash(
    fixture_files: tuple[Path, Path, list[dict[str, Any]]],
) -> None:
    manifest, truth, records = fixture_files
    truth.write_text(json.dumps({"package": ["absent.mp4"]}))
    data = json.loads(manifest.read_text())
    data["ground_truth_sha256"] = file_sha256(truth)
    manifest.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="unknown clip IDs"):
        validate_video_fixture(manifest, truth, records, ["package"])


def test_fixture_rejects_missing_or_duplicate_system_records(
    fixture_files: tuple[Path, Path, list[dict[str, Any]]],
) -> None:
    manifest, truth, records = fixture_files
    for invalid in ([], records + records):
        with pytest.raises(ValueError, match="exactly once"):
            validate_video_fixture(manifest, truth, invalid, ["package"])

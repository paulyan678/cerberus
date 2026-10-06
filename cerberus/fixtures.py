"""Validate a small local evaluation set before reporting retrieval metrics."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from datetime import datetime
from pathlib import Path
from typing import Any

from cerberus.io import load_json


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _text(record: Mapping[str, Any], key: str) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"fixture requires non-empty {key}")
    return value


def validate_video_fixture(
    manifest_path: Path,
    ground_truth_path: Path,
    records: Sequence[Mapping[str, Any]],
    queries: Sequence[str],
) -> dict[str, Any]:
    """Check assets and label joins; human provenance remains an attestation.

    This does not decode videos or prove that the named annotator was blinded.
    It detects changes to a frozen set and rejects manifests declaring synthetic data.
    """
    manifest = load_json(manifest_path)
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1:
        raise ValueError("fixture requires schema_version 1")
    if manifest.get("dataset_kind") != "real_video":
        raise ValueError("fixture dataset_kind must be real_video; keep demos separate")
    dataset_id = _text(manifest, "dataset_id")
    annotator = _text(manifest, "annotator")
    frozen_at = datetime.fromisoformat(_text(manifest, "frozen_at"))
    if frozen_at.tzinfo is None:
        raise ValueError("fixture frozen_at requires a timezone")
    if manifest.get("annotation_method") != "manual_video_review":
        raise ValueError("fixture labels require manual_video_review")
    if manifest.get("model_outputs_seen") is not False:
        raise ValueError("fixture annotator must declare model_outputs_seen false")
    declared_queries = manifest.get("queries")
    if (
        not isinstance(declared_queries, list)
        or not 1 <= len(declared_queries) <= 20
        or not all(
            isinstance(query, str) and query.strip() for query in declared_queries
        )
        or len(set(declared_queries)) != len(declared_queries)
        or list(queries) != declared_queries
    ):
        raise ValueError("fixture must freeze the same 1-20 unique ordered queries")
    if file_sha256(ground_truth_path) != manifest.get("ground_truth_sha256"):
        raise ValueError("fixture ground-truth SHA-256 mismatch")

    clips = manifest.get("clips")
    if not isinstance(clips, list) or not 1 <= len(clips) <= 50:
        raise ValueError("fixture must contain 1-50 clips")
    root = manifest_path.resolve().parent
    names: set[str] = set()
    for clip in clips:
        if not isinstance(clip, dict):
            raise ValueError("fixture clip must be an object")
        relative = Path(_text(clip, "pathname"))
        path = (root / relative).resolve()
        if relative.is_absolute() or not path.is_relative_to(root):
            raise ValueError(
                "fixture clip paths must stay within the fixture directory"
            )
        if path.name in names:
            raise ValueError(f"duplicate fixture filename: {path.name}")
        names.add(path.name)
        _text(clip, "source")
        _text(clip, "rights")
        if file_sha256(path) != clip.get("sha256"):
            raise ValueError(f"fixture clip SHA-256 mismatch: {relative}")

    record_names = [Path(_text(record, "pathname")).name for record in records]
    if len(set(record_names)) != len(record_names) or set(record_names) != names:
        raise ValueError("system records must match each fixture clip exactly once")
    truth = load_json(ground_truth_path)
    if not isinstance(truth, dict) or set(truth) != set(declared_queries):
        raise ValueError("ground truth must match every frozen query")
    for query, relevant in truth.items():
        if (
            not isinstance(relevant, list)
            or not all(isinstance(name, str) for name in relevant)
            or len(set(relevant)) != len(relevant)
            or not set(relevant) <= names
        ):
            raise ValueError(f"ground truth has invalid or unknown clip IDs: {query}")
    return {
        "dataset_id": dataset_id,
        "dataset_kind": "real_video",
        "manifest_sha256": file_sha256(manifest_path),
        "ground_truth_sha256": file_sha256(ground_truth_path),
        "clip_count": len(names),
        "annotator": annotator,
        "frozen_at": frozen_at.isoformat(),
        "validation": "file_hashes_and_declared_annotation_protocol",
    }

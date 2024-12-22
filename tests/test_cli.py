from __future__ import annotations

import io
import json
import subprocess
import sys
from pathlib import Path

import pytest

import cerberus.cli as cli

ROOT = Path(__file__).resolve().parents[1]


def test_sparse_cli_reads_and_writes_jsonl(monkeypatch: pytest.MonkeyPatch) -> None:
    source = io.StringIO(
        '{"pathname":"delivery.mp4","description":"package delivery"}\n'
        '{"pathname":"animal.mp4","description":"dog in driveway"}\n'
    )
    output = io.StringIO()
    monkeypatch.setattr(cli, "stdin", source)
    monkeypatch.setattr(cli, "stdout", output)

    cli.sparse_main(["2", "package"])

    results = [json.loads(line) for line in output.getvalue().splitlines()]
    assert len(results) == 1
    score = results[0].pop("score")
    assert results[0] == {
        "pathname": "delivery.mp4",
        "description": "package delivery",
        "query": "package",
        "rank": 1,
        "retrieval_method": "sparse",
    }
    assert score > 0


def test_confusion_cli_emits_validated_jsonl(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    actual = tmp_path / "actual.jsonl"
    predicted = tmp_path / "predicted.jsonl"
    record = '{"pathname":"camera.mp4","classifications":[["Event",true]]}\n'
    actual.write_text(record, encoding="utf-8")
    predicted.write_text(record, encoding="utf-8")
    output = io.StringIO()
    monkeypatch.setattr(cli, "stdout", output)

    cli.confusion_main([str(actual), str(predicted)])

    class_name, counts = json.loads(output.getvalue())
    assert class_name == "Event"
    assert counts["total"] == 1
    assert counts["true_positive"] == 1


def test_sparse_ir_evaluation_cli_can_emit_machine_readable_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    records = tmp_path / "records.jsonl"
    ground_truth = tmp_path / "ground-truth.json"
    records.write_text(
        '{"pathname":"delivery.mp4","description":"package delivery"}\n'
        '{"pathname":"animal.mp4","description":"dog in driveway"}\n',
        encoding="utf-8",
    )
    ground_truth.write_text(json.dumps({"package": ["delivery.mp4"]}), encoding="utf-8")
    output = io.StringIO()
    monkeypatch.setattr(cli, "stdout", output)

    cli.ir_eval_main(
        [
            "--queries",
            "package",
            "--embeddings-file",
            str(records),
            "--ground-truth-file",
            str(ground_truth),
            "--return-k",
            "2",
            "--top-k",
            "1",
            "--method",
            "sparse",
            "--json",
        ]
    )

    report = json.loads(output.getvalue())
    assert report["queries"]["package"]["retrieved"] == ["delivery.mp4"]
    assert report["overall"]["precision_at_k"] == 1.0


def test_ir_evaluation_cli_rejects_top_k_above_return_k(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as error:
        cli.ir_eval_main(
            [
                "--queries",
                "query",
                "--embeddings-file",
                "unused.jsonl",
                "--ground-truth-file",
                "unused.json",
                "--return-k",
                "1",
                "--top-k",
                "2",
                "--method",
                "sparse",
            ]
        )

    assert error.value.code == 2
    assert "--top-k cannot exceed --return-k" in capsys.readouterr().err


def test_offline_demo_runs_from_outside_the_repository(tmp_path: Path) -> None:
    process = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "demo.py")],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )

    assert process.returncode == 0, process.stderr
    assert "Cerberus offline demonstration" in process.stdout
    assert "Sparse BM25 retrieval" in process.stdout
    assert "Dense cosine retrieval" in process.stdout
    assert (
        "PASS: deterministic retrieval and evaluation checks completed."
        in process.stdout
    )

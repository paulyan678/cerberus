"""Command-line adapters for the Cerberus pipeline."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from contextlib import contextmanager
from glob import glob
from pathlib import Path
from sys import stderr, stdin, stdout
from typing import Any

from cerberus import __version__
from cerberus.config import GeminiSettings, embedding_model_name
from cerberus.evaluation import classification_confusions, evaluate_retrieval
from cerberus.fixtures import file_sha256, validate_video_fixture
from cerberus.gemini import GeminiModel, create_client, retry, wait_for_file
from cerberus.io import load_json, load_jsonl, read_jsonl, write_jsonl
from cerberus.retrieval import rank_dense, rank_sparse
from cerberus.video_analysis import describe_and_classify


def _positive_integer(value: str) -> int:
    integer = int(value)
    if integer < 1:
        raise argparse.ArgumentTypeError("value must be at least 1")
    return integer


def _load_environment() -> None:
    from dotenv import load_dotenv

    load_dotenv()


@contextmanager
def _gemini() -> Any:
    _load_environment()
    settings = GeminiSettings.from_environment()
    client = create_client(settings)
    try:
        yield client, settings
    finally:
        client.close()


def _sentence_transformer() -> Any:
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as error:
        raise RuntimeError(
            "Dense retrieval requires the optional dependency group: "
            "python -m pip install -e '.[retrieval]'"
        ) from error
    return SentenceTransformer


def upload_main(argv: Sequence[str] | None = None) -> None:
    """Upload videos matched by one or more glob patterns."""
    parser = argparse.ArgumentParser(description="Upload videos to Gemini.")
    parser.add_argument("patterns", nargs="+", help="Recursive video glob patterns")
    parser.add_argument("--attempts", type=_positive_integer, default=3)
    args = parser.parse_args(argv)

    pathnames: list[str] = []
    seen: set[str] = set()
    for pattern in args.patterns:
        for pathname in glob(pattern, recursive=True):
            if pathname not in seen and Path(pathname).is_file():
                seen.add(pathname)
                pathnames.append(pathname)
    if not pathnames:
        parser.error("no files matched the supplied patterns")

    outputs = []
    from tqdm import tqdm

    with _gemini() as (client, _):
        for pathname in tqdm(pathnames, desc="Uploading", file=stderr):
            uploaded = retry(
                lambda pathname=pathname: client.files.upload(file=pathname),
                attempts=args.attempts,
            )
            outputs.append(
                {
                    "video_id": uploaded.name,
                    "pathname": pathname,
                    "name": uploaded.name,
                }
            )
    write_jsonl(outputs, stdout)


def list_files_main(argv: Sequence[str] | None = None) -> None:
    """List files currently stored by the Gemini Files API."""
    argparse.ArgumentParser(description="List uploaded Gemini files.").parse_args(argv)
    outputs = []
    with _gemini() as (client, _):
        for file in client.files.list():
            state = getattr(getattr(file, "state", None), "name", None)
            outputs.append(
                {
                    "name": getattr(file, "name", None),
                    "uri": getattr(file, "uri", None),
                    "state": state,
                }
            )
    write_jsonl(outputs, stdout)


def delete_files_main(argv: Sequence[str] | None = None) -> None:
    """Delete Gemini files named by JSONL objects on standard input."""
    parser = argparse.ArgumentParser(
        description="Delete uploaded Gemini files listed as JSONL on stdin."
    )
    parser.add_argument("--attempts", type=_positive_integer, default=3)
    args = parser.parse_args(argv)
    inputs = list(read_jsonl(stdin))
    from tqdm import tqdm

    with _gemini() as (client, _):
        for record in tqdm(inputs, desc="Deleting", file=stderr):
            name = record.get("name")
            if not isinstance(name, str) or not name:
                raise ValueError("every input record must contain a non-empty name")
            retry(
                lambda name=name: client.files.delete(name=name),
                attempts=args.attempts,
            )


def describe_main(argv: Sequence[str] | None = None) -> None:
    """Describe uploaded videos and classify them into caller-supplied classes."""
    parser = argparse.ArgumentParser(
        description="Describe and classify uploaded videos from JSONL stdin."
    )
    parser.add_argument("classes", nargs="+", help="Event classes")
    parser.add_argument("--attempts", type=_positive_integer, default=3)
    parser.add_argument("--file-timeout", type=float, default=300.0)
    args = parser.parse_args(argv)
    if args.file_timeout <= 0:
        parser.error("--file-timeout must be positive")

    inputs = list(read_jsonl(stdin))
    outputs = []
    from tqdm import tqdm

    with _gemini() as (client, settings):
        model = GeminiModel(client, settings.model)
        for record in tqdm(inputs, desc="Analyzing", file=stderr):
            name = record.get("name")
            if not isinstance(name, str) or not name:
                raise ValueError("every input record must contain a non-empty name")
            video_file = wait_for_file(client, name, timeout=args.file_timeout)
            description, classifications = retry(
                lambda video_file=video_file: describe_and_classify(
                    model, video_file, args.classes
                ),
                attempts=args.attempts,
            )
            outputs.append(
                {
                    **record,
                    "description": description,
                    "classifications": classifications,
                }
            )
    write_jsonl(outputs, stdout)


def embed_main(argv: Sequence[str] | None = None) -> None:
    """Generate dense embeddings for JSONL video descriptions."""
    parser = argparse.ArgumentParser(description="Embed video descriptions.")
    parser.add_argument("--batch-size", type=_positive_integer, default=32)
    args = parser.parse_args(argv)
    inputs = list(read_jsonl(stdin))
    descriptions = []
    for index, record in enumerate(inputs):
        description = record.get("description")
        if not isinstance(description, str) or not description.strip():
            raise ValueError(f"record {index} has no non-empty description")
        descriptions.append(description)

    _load_environment()
    model = _sentence_transformer()(embedding_model_name())
    embeddings = model.encode(
        descriptions,
        batch_size=args.batch_size,
        show_progress_bar=True,
    )
    outputs = [
        {**record, "embedding": embedding.tolist()}
        for record, embedding in zip(inputs, embeddings, strict=True)
    ]
    write_jsonl(outputs, stdout)


def dense_main(argv: Sequence[str] | None = None) -> None:
    """Run dense cosine retrieval over embedded JSONL input."""
    parser = argparse.ArgumentParser(description="Search descriptions densely.")
    parser.add_argument("k", type=_positive_integer)
    parser.add_argument("queries", nargs="+")
    args = parser.parse_args(argv)
    inputs = list(read_jsonl(stdin))

    _load_environment()
    model = _sentence_transformer()(embedding_model_name())
    query_embeddings = model.encode(args.queries).tolist()
    outputs = []
    for query, embedding in zip(args.queries, query_embeddings, strict=True):
        outputs.extend(rank_dense(inputs, query, embedding, args.k))
    write_jsonl(outputs, stdout)


def sparse_main(argv: Sequence[str] | None = None) -> None:
    """Run dependency-free BM25 retrieval over JSONL input."""
    parser = argparse.ArgumentParser(description="Search descriptions with BM25.")
    parser.add_argument("k", type=_positive_integer)
    parser.add_argument("queries", nargs="+")
    args = parser.parse_args(argv)
    inputs = list(read_jsonl(stdin))
    outputs = []
    for query in args.queries:
        outputs.extend(rank_sparse(inputs, query, args.k))
    write_jsonl(outputs, stdout)


def confusion_main(argv: Sequence[str] | None = None) -> None:
    """Calculate validated per-class confusion counts."""
    parser = argparse.ArgumentParser(description="Evaluate predicted classes.")
    parser.add_argument("actual_classifications_pathname")
    parser.add_argument("predicted_classifications_pathname")
    args = parser.parse_args(argv)
    results = classification_confusions(
        load_jsonl(args.actual_classifications_pathname),
        load_jsonl(args.predicted_classifications_pathname),
    )
    write_jsonl(results, stdout)


def _print_ir_report(report: dict[str, Any]) -> None:
    print("Evaluation results")
    if "fixture" in report:
        print(f"Fixture validation: {report['fixture']['validation']}")
    print("=" * 72)
    for query, result in report["queries"].items():
        print(f"Query: {query}")
        print(f"  Retrieved: {', '.join(result['retrieved']) or '(none)'}")
        print(
            f"  P@{report['top_k']}: {result['precision_at_k']:.3f}  "
            f"R@{report['top_k']}: {result['recall_at_k']:.3f}  "
            f"F1@{report['top_k']}: {result['f1_at_k']:.3f}  "
            f"AP@{report['return_k']}: "
            f"{result['average_precision_at_return_k']:.3f}"
        )
    overall = report["overall"]
    print("-" * 72)
    print(
        f"Mean P@{report['top_k']}: {overall['precision_at_k']:.3f}  "
        f"Mean R@{report['top_k']}: {overall['recall_at_k']:.3f}  "
        f"Mean F1@{report['top_k']}: {overall['f1_at_k']:.3f}  "
        f"MAP@{report['return_k']}: "
        f"{overall['average_precision_at_return_k']:.3f}"
    )


def ir_eval_main(argv: Sequence[str] | None = None) -> None:
    """Evaluate dense or sparse retrieval without spawning child processes."""
    parser = argparse.ArgumentParser(description="Evaluate information retrieval.")
    parser.add_argument("--queries", nargs="+", required=True)
    parser.add_argument(
        "--embeddings-file", "--embeddings_file", dest="embeddings_file", required=True
    )
    parser.add_argument(
        "--ground-truth-file",
        "--ground_truth_file",
        dest="ground_truth_file",
        required=True,
    )
    parser.add_argument(
        "--return-k",
        "--return_k",
        dest="return_k",
        type=_positive_integer,
        required=True,
    )
    parser.add_argument(
        "--top-k", "--top_k", dest="top_k", type=_positive_integer, required=True
    )
    parser.add_argument(
        "--method",
        "--sparse_or_dense",
        dest="method",
        choices=("sparse", "dense"),
        required=True,
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    parser.add_argument(
        "--fixture-manifest",
        type=Path,
        help="Validate frozen real-video assets and independent-label declarations",
    )
    args = parser.parse_args(argv)
    if args.top_k > args.return_k:
        parser.error("--top-k cannot exceed --return-k")

    records = load_jsonl(args.embeddings_file)
    ground_truth = load_json(args.ground_truth_file)
    if not isinstance(ground_truth, dict):
        raise ValueError("ground truth must be a JSON object")

    fixture = None
    if args.fixture_manifest:
        fixture = validate_video_fixture(
            args.fixture_manifest, Path(args.ground_truth_file), records, args.queries
        )
        fixture["system_records_sha256"] = file_sha256(Path(args.embeddings_file))

    model_name = None
    if args.method == "sparse":

        def search(query: str, k: int) -> list[dict[str, Any]]:
            return rank_sparse(records, query, k)
    else:
        _load_environment()
        model_name = embedding_model_name()
        model = _sentence_transformer()(model_name)
        query_embeddings = {
            query: vector
            for query, vector in zip(
                args.queries,
                model.encode(args.queries).tolist(),
                strict=True,
            )
        }

        def search(query: str, k: int) -> list[dict[str, Any]]:
            return rank_dense(records, query, query_embeddings[query], k)

    report = evaluate_retrieval(
        args.queries,
        search,
        ground_truth,
        return_k=args.return_k,
        top_k=args.top_k,
    )
    report["retrieval"] = {
        "method": args.method,
        "embedding_model": model_name,
        "embedding_revision": "unrecorded" if model_name else None,
        "cerberus_version": __version__,
        "source_revision": "unrecorded",
    }
    if fixture is not None:
        report["fixture"] = fixture
    else:
        report["fixture"] = {"validation": "unverified_inputs"}
    if args.json:
        json.dump(report, stdout, indent=2)
        stdout.write("\n")
    else:
        _print_ir_report(report)


def demo_main(argv: Sequence[str] | None = None) -> None:
    """Run the deterministic, credential-free smoke-test demonstration."""
    argparse.ArgumentParser(
        description="Run the offline Cerberus demonstration."
    ).parse_args(argv)
    from importlib.resources import files

    fixture_root = files("cerberus").joinpath("demo_data")
    records = load_jsonl(fixture_root / "demo_events.jsonl")
    ground_truth = load_json(fixture_root / "demo_ground_truth.json")
    queries = list(ground_truth)
    query_embeddings = {
        "package delivery": [1.0, 0.0, 0.0, 0.3],
        "animal in driveway": [0.0, 1.0, 0.0, 0.0],
        "person near front door": [0.0, 0.0, 0.0, 1.0],
    }

    sparse_report = evaluate_retrieval(
        queries,
        lambda query, k: rank_sparse(records, query, k),
        ground_truth,
        return_k=3,
        top_k=1,
    )
    dense_report = evaluate_retrieval(
        queries,
        lambda query, k: rank_dense(records, query, query_embeddings[query], k),
        ground_truth,
        return_k=3,
        top_k=1,
    )
    confusions = classification_confusions(
        load_jsonl(fixture_root / "demo_actual_classifications.jsonl"),
        load_jsonl(fixture_root / "demo_predicted_classifications.jsonl"),
    )

    print("Cerberus offline demonstration")
    print("Synthetic post-analysis records; no API key or private video required.\n")
    print("Sparse BM25 retrieval")
    _print_ir_report(sparse_report)
    print("\nDense cosine retrieval (precomputed fixture embeddings)")
    _print_ir_report(dense_report)
    print("\nClassification confusion checks")
    for class_name, counts in confusions:
        correct = counts["true_positive"] + counts["true_negative"]
        print(f"  {class_name:<20} {correct}/{counts['total']} correct")

    expected_first = {
        "package delivery": "camera_front_001.mp4",
        "animal in driveway": "camera_driveway_002.mp4",
        "person near front door": "camera_door_004.mp4",
    }
    for method, report in (("sparse", sparse_report), ("dense", dense_report)):
        for query, expected in expected_first.items():
            actual = report["queries"][query]["retrieved"][0]
            if actual != expected:
                raise RuntimeError(
                    f"{method} smoke check failed for {query!r}: {actual} != {expected}"
                )
    print("\nPASS: deterministic retrieval and evaluation checks completed.")

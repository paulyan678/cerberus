# Offline demonstration fixtures

The files in this directory are small, fictional inputs for
`python scripts/demo.py` and `cerberus-demo`. They let a reviewer exercise
Cerberus without an API key, network access, model download, or private video.
Equivalent copies under `cerberus/demo_data/` are packaged so the installed
`cerberus-demo` command remains self-contained.

## What the demo covers

- BM25 sparse ranking over event descriptions
- cosine dense ranking over precomputed vectors
- precision, recall, F1, average precision, and macro aggregation
- validated, filename-aligned per-class confusion counts
- deterministic first-result assertions with a nonzero failure exit

## What the demo does not cover

The fixture pathnames are fictional and no video files exist. Descriptions,
labels, query vectors, and event embeddings were written for the smoke test;
they were not produced by Gemini or a sentence-transformer model. Consequently,
the demo does not measure video understanding, classification accuracy, model
latency, cloud reliability, or real-world retrieval quality.

## Files

- `demo_events.jsonl`: six post-analysis event records with illustrative vectors
- `demo_ground_truth.json`: relevant filenames for three queries
- `demo_actual_classifications.jsonl`: synthetic reference labels
- `demo_predicted_classifications.jsonl`: the same records in a different order,
  exercising name- and class-based alignment

Run the demo from the repository root:

```bash
python scripts/demo.py
```

A successful run ends with:

```text
PASS: deterministic retrieval and evaluation checks completed.
```

Keep fixtures free of personal information, real surveillance footage, secrets,
and proprietary data. If a fixture changes, update its ground truth and tests in
the same pull request.

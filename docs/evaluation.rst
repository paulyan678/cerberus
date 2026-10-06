Evaluation
==========

Cerberus supports classification confusion counts and ranked-retrieval metrics.
The calculations cannot establish dataset quality, model fairness, causal
validity, or suitability for deployment; those require an experimental design
outside the software.

Classification evaluation
-------------------------

For each class, Cerberus reports:

``true_positive`` (TP)
   Actual and predicted values are both true.

``false_positive`` (FP)
   Actual is false and predicted is true.

``true_negative`` (TN)
   Actual and predicted values are both false.

``false_negative`` (FN)
   Actual is true and predicted is false.

It also reports totals for actual and predicted positive and negative values.
Records are joined by filename basename and classes by name, not input order.
Missing records, duplicates, mismatched class sets, and non-boolean values are
rejected to prevent plausible but invalid measurements.

Retrieval metrics
-----------------

Let ``k`` be ``top_k``, ``R`` the set of relevant documents for a query, and
``H_k`` the number of relevant documents among the first ``k`` ranks.

Precision at k
   ``P@k = H_k / k``. The denominator remains ``k`` if fewer results are
   returned.

Recall at k
   ``R@k = H_k / |R|`` when relevant documents exist, otherwise zero.

F1 at k
   The harmonic mean ``2 * P@k * R@k / (P@k + R@k)``, or zero when both are
   zero.

Average precision at return_k
   For every relevant result within the returned ranking, sum precision at its
   rank and divide by the total number of relevant ground-truth documents. A
   relevant item beyond ``return_k`` contributes zero. The report labels this
   ``average_precision_at_return_k`` to make truncation explicit.

Overall values are unweighted arithmetic means across the supplied queries.
The mean of average precision is MAP at ``return_k``.

Protocol checklist
------------------

Before reporting a real experiment, record:

* dataset provenance, permission or licensing basis, size, camera conditions,
  and inclusion/exclusion criteria;
* train, validation, and test separation, including leakage controls;
* annotation instructions, number of annotators, adjudication, and agreement;
* exact class definitions and handling of ambiguous or unresolved values;
* exact query list, relevant-document judgments, ``top_k``, and ``return_k``;
* Gemini and embedding model identifiers, access date, prompts, dependency
  versions, and any generation settings;
* sparse or dense parameters and hardware where it affects timing; and
* uncertainty, per-class/per-query results, failures, and known biases rather
  than only macro averages.

Example command
---------------

.. code-block:: bash

   cerberus-evaluate-ir \
     --queries 'package delivery' 'animal in driveway' \
     --embeddings-file data/video-event-embeddings.jsonl \
     --ground-truth-file data/ground-truth.json \
     --return-k 20 \
     --top-k 5 \
     --method dense \
     --json > data/dense-evaluation.json

Fixture results are not research results
----------------------------------------

The offline demonstration uses six hand-authored event records and intentionally
easy assertions. Its metrics show that the implementation connects and computes
as expected. They do not estimate accuracy, generalization, robustness, bias,
or real CCTV performance. This repository makes no claim of measured real-world
performance.

A bounded real-video fixture
----------------------------

The next useful measurement is a small holdout set, not a larger synthetic demo.
Start with 12-20 clips from footage you may use, including missed-event and
no-relevant-result cases, and 5-10 fixed queries. Keep related clips from the
same event/camera session together when splitting development and holdout data.
Use local ``data/`` storage; no real footage or results are included in this change.

A reviewer watches the clips and writes relevance judgments **before seeing
model descriptions, embeddings, or rankings**. Freeze queries, labels, clip
hashes and the review protocol; use a second reviewer to adjudicate ambiguous
cases before running evaluation. Do not use model-generated labels as truth,
or tune prompts on this holdout. Keep failed queries and report each result,
not only the average. Compare sparse and dense retrieval on these same inputs.

``--fixture-manifest`` checks a frozen fixture with 1-50 local clips and 1-20
queries. The following is a schema example, not an executed real-video result;
replace every placeholder and compute SHA-256 from the actual file bytes:

.. code-block:: json

   {
     "schema_version": 1,
     "dataset_kind": "real_video",
     "dataset_id": "your-holdout-version",
     "annotator": "actual reviewer identity",
     "annotation_method": "manual_video_review",
     "model_outputs_seen": false,
     "frozen_at": "ACTUAL_ISO8601_TIMESTAMP_WITH_TIMEZONE",
     "queries": ["package delivery"],
     "ground_truth_sha256": "SHA256_OF_GROUND_TRUTH_FILE",
     "clips": [{
       "pathname": "clips/clip-001.mp4",
       "source": "actual collection or source reference",
       "rights": "documented permission or license",
       "sha256": "SHA256_OF_CLIP_BYTES"
     }]
   }

Clip paths are relative to the manifest and must stay inside its directory.
Basenames must be unique. Ground truth uses the existing query-to-filename-list
format (for example ``{"package delivery": ["clip-001.mp4"]}``). Every record
must map to exactly one clip; unknown relevant IDs, duplicate records, changed
files, missing provenance fields and non-blinded label declarations are rejected
before model loading. Use ``shasum -a 256 FILE`` to compute file hashes.

.. code-block:: bash

   cerberus-evaluate-ir \
     --fixture-manifest data/holdout/manifest.json \
     --queries 'package delivery' \
     --embeddings-file data/holdout/system-records.jsonl \
     --ground-truth-file data/holdout/ground-truth.json \
     --return-k 10 --top-k 5 --method sparse --json \
     > data/holdout/sparse-report.json

The report includes manifest, label and system-record hashes, retrieval method,
cutoffs, package version, and the configured dense embedding model name. Exact
embedding/source revisions are marked ``unrecorded``; retain them in run notes.
A model name alone does not pin its weights or the earlier description generator. Without the flag,
reports say ``unverified_inputs``. With it they say
``file_hashes_and_declared_annotation_protocol``: software checks the files and
declarations, but cannot prove human independence, consent, video authenticity,
or that the frozen timestamp was recorded before model use. Retain review notes,
collection consent/license records, model/prompt versions and failures alongside
results. No measured real-video accuracy is claimed until this separate human
annotation and evaluation has actually happened.

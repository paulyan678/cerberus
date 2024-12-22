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

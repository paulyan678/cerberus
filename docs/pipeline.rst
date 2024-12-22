Pipeline
========

Cerberus persists each stage as JSONL so it can be inspected, versioned when
appropriate, or replaced with a separately generated artifact. The commands
below assume the repository root as the working directory.

1. Upload videos
----------------

.. code-block:: bash

   cerberus-upload --attempts 3 \
     'data/**/*.mp4' 'data/**/*.mov' \
     > data/video-files.jsonl

Glob patterns are expanded recursively. Each matched local file is uploaded to
the Gemini Files API and represented by a manifest record. The command rejects
an empty match instead of producing an empty manifest.

2. Describe and classify
------------------------

.. code-block:: bash

   cerberus-describe \
     --attempts 3 \
     --file-timeout 300 \
     'Home Access' 'Vehicle Moving' 'Break-in' 'Package Delivery' \
     'Animal Moving' 'People Walking' 'Porch Piracy' \
     < data/video-files.jsonl \
     > data/video-events.jsonl

The command waits for each uploaded file to become active, requests a detailed
description, and classifies that description independently against each class.
A classification response must begin with ``Yes`` or ``No``; otherwise its
value is ``null``. Review unresolved values before classification evaluation,
which intentionally accepts only booleans.

3a. Sparse retrieval
--------------------

.. code-block:: bash

   cerberus-search-sparse 3 \
     'package delivery' 'animal in driveway' \
     < data/video-events.jsonl \
     > data/sparse-results.jsonl

Sparse retrieval tokenizes and case-folds descriptions, then ranks matching
records with BM25. It is local, deterministic, and has no model dependency.
Each quoted positional argument is one query.

3b. Dense retrieval
-------------------

Generate event embeddings:

.. code-block:: bash

   cerberus-embed --batch-size 32 \
     < data/video-events.jsonl \
     > data/video-event-embeddings.jsonl

Search with query embeddings from the same configured model:

.. code-block:: bash

   cerberus-search-dense 3 \
     'package delivery' 'animal in driveway' \
     < data/video-event-embeddings.jsonl \
     > data/dense-results.jsonl

Dense ranking sorts by ascending cosine distance. The embedding model may be
downloaded on first use and all record and query vectors must have the same,
nonzero dimension.

4. Evaluate retrieval
---------------------

.. code-block:: bash

   cerberus-evaluate-ir \
     --queries 'package delivery' 'animal in driveway' \
     --embeddings-file data/video-event-embeddings.jsonl \
     --ground-truth-file data/ground-truth.json \
     --return-k 20 \
     --top-k 5 \
     --method dense

Use ``--method sparse`` with records that have descriptions; an embedding field
is not required for sparse evaluation. Add ``--json`` to emit a machine-readable
report rather than the default human-readable summary. See :doc:`evaluation`.

5. Evaluate classification
---------------------------

.. code-block:: bash

   cerberus-confusion \
     data/video-golden-outputs.jsonl \
     data/video-events.jsonl \
     > data/video-confusion.jsonl

The evaluator joins actual and predicted records by the basename of
``pathname`` and aligns labels by class name. Duplicate filenames, missing or
extra predictions, different class sets, and non-boolean labels are errors.

6. Clean up remote files
------------------------

.. code-block:: bash

   cerberus-list > data/remote-files.jsonl
   cerberus-delete --attempts 3 < data/remote-files.jsonl

Deleting local manifests does not delete uploaded remote files. Perform this
step explicitly and verify the remote listing according to the needs of the
experiment.

Legacy wrappers
---------------

The historical filenames in ``scripts/`` remain thin adapters to the same CLI:
``upload.py``, ``describe-and-classify.py``, ``generate-embeddings.py``,
``sparse-retrieval.py``, ``dense-retrieval.py``, ``ir_eval.py``, and
``confusion.py``. Prefer installed commands for new automation.

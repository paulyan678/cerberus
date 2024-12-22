Overview
========

Problem
-------

Long CCTV recordings are difficult to inspect manually. Cerberus explores a
pipeline that converts short videos into text descriptions and binary event
labels, then lets an evaluator retrieve relevant clips with natural-language
queries. The repository emphasizes inspectable intermediate JSONL artifacts and
reproducible evaluation rather than a hidden end-to-end service.

Goals
-----

* describe an uploaded video in natural language;
* classify the description independently against caller-provided event classes;
* compare interpretable BM25 retrieval with embedding-based cosine retrieval;
* compute validated classification and retrieval measurements; and
* provide a deterministic, private, credential-free software demonstration.

Non-goals
---------

Cerberus does not provide identity or face recognition, a live monitoring user
interface, emergency dispatch, access control, evidentiary validation, secure
video storage, or a guarantee that an event occurred. It must not be treated as
an autonomous surveillance decision maker.

System boundary
---------------

The video-understanding stage uses the configured Gemini service. Uploading,
remote file processing, description, and classification therefore require a
network connection, a valid API key, and a compatible hosted model. Sparse
retrieval and all evaluation logic run locally. Dense retrieval runs locally
after the configured sentence-transformer model has been downloaded.

Architecture
------------

.. code-block:: text

   local videos
        |
        v
   Gemini upload --> description + event labels --> event JSONL
                                                       |       \
                                                       |        \
                                                BM25 ranking   embedding model
                                                       |             |
                                                       |       cosine ranking
                                                       \             /
                                                        ranked JSONL
                                                             |
                                              ground truth + evaluation

The synthetic offline demo enters at ``event JSONL``. It deliberately does not
simulate cloud video understanding. See :doc:`pipeline` for stage-level details
and :doc:`data_formats` for the interfaces between stages.

Design principles
-----------------

Deterministic core
   Retrieval, joining, metric calculations, and JSONL handling are local,
   explicit, and unit-testable.

Validated boundaries
   Malformed records, mismatched filenames, duplicate labels, invalid vector
   dimensions, and impossible metric parameters fail with actionable errors.

Composable CLI
   Commands read JSONL from standard input and write data to standard output;
   progress and diagnostics go to standard error.

Finite external operations
   Cloud operations use bounded retries, and uploaded-file processing has a
   timeout rather than an unbounded loop.

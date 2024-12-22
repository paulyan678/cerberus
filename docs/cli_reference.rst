CLI reference
=============

Every data-producing command writes JSONL to standard output. Progress bars and
diagnostics are written to standard error. Redirect output to a file or pipe it
to another command without mixing progress text into the data stream.

Use ``COMMAND --help`` for the parser-generated reference.

Installed commands
------------------

``cerberus-demo``
   Run the credential-free deterministic smoke test. It takes no arguments.

``cerberus-upload PATTERN [PATTERN ...] [--attempts N]``
   Upload files matched by recursive glob patterns. ``--attempts`` defaults to
   3 and must be positive. Requires ``GEMINI_API_KEY``.

``cerberus-describe CLASS [CLASS ...] [--attempts N] [--file-timeout SECONDS]``
   Read upload manifest records from standard input, wait for active remote
   files, then append descriptions and classifications. Timeout defaults to
   300 seconds per file and must be positive.

``cerberus-embed [--batch-size N]``
   Read described events and append an ``embedding`` vector. Batch size defaults
   to 32. Requires the ``retrieval`` or ``dev`` extra.

``cerberus-search-sparse K QUERY [QUERY ...]``
   Rank input event records with BM25. ``K`` must be positive. Quote multi-word
   queries because each positional argument is handled as a separate query.

``cerberus-search-dense K QUERY [QUERY ...]``
   Embed the queries and rank input event records by cosine distance. Input
   records must already contain compatible embeddings.

``cerberus-evaluate-ir OPTIONS``
   Evaluate one retrieval method. Required options are ``--queries``,
   ``--embeddings-file``, ``--ground-truth-file``, ``--return-k``, ``--top-k``,
   and ``--method {sparse,dense}``. ``top-k`` cannot exceed ``return-k``. Add
   ``--json`` for structured output. Underscored legacy option names remain
   accepted for compatibility.

``cerberus-confusion ACTUAL.jsonl PREDICTED.jsonl``
   Emit one per-class confusion-count record. Both inputs must contain the same
   unique filename set and boolean value for every shared class.

Remote file administration
--------------------------

``cerberus-list`` (legacy wrapper: ``python scripts/list.py``)
   List files visible through the configured Gemini account as JSONL.

``cerberus-delete [--attempts N]`` (legacy wrapper: ``python scripts/delete.py``)
   Read objects containing ``name`` from standard input and delete those remote
   files. Deletion is an external, irreversible operation.

Legacy command mapping
----------------------

.. list-table::
   :header-rows: 1

   * - Installed command
     - Repository wrapper
   * - ``cerberus-demo``
     - ``python scripts/demo.py``
   * - ``cerberus-upload``
     - ``python scripts/upload.py``
   * - ``cerberus-describe``
     - ``python scripts/describe-and-classify.py``
   * - ``cerberus-embed``
     - ``python scripts/generate-embeddings.py``
   * - ``cerberus-search-sparse``
     - ``python scripts/sparse-retrieval.py``
   * - ``cerberus-search-dense``
     - ``python scripts/dense-retrieval.py``
   * - ``cerberus-evaluate-ir``
     - ``python scripts/ir_eval.py``
   * - ``cerberus-confusion``
     - ``python scripts/confusion.py``
   * - ``cerberus-list``
     - ``python scripts/list.py``
   * - ``cerberus-delete``
     - ``python scripts/delete.py``

Exit behavior
-------------

Invalid arguments are rejected by the argument parser. Malformed JSONL,
inconsistent schemas, exhausted cloud retries, processing timeouts, and invalid
metric inputs raise errors and produce a nonzero exit. A successful data command
may produce an empty JSONL stream when the valid operation has no results.

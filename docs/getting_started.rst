Getting started
===============

Requirements
------------

* Python 3.10 or newer
* a virtual environment (recommended)
* a Gemini API key and network access only for the full video workflow

Install from a checkout
-----------------------

.. code-block:: bash

   git clone https://github.com/paulyan678/cerberus.git
   cd cerberus
   python -m venv .venv
   source .venv/bin/activate
   python -m pip install --upgrade pip
   python -m pip install -e '.[dev]'

On Windows, activate the environment with
``.venv\Scripts\activate``. The ``dev`` extra installs the test, lint,
documentation, and dense-retrieval dependencies.

Offline demonstration
---------------------

.. code-block:: bash

   python scripts/demo.py

The installed equivalent is:

.. code-block:: bash

   cerberus-demo

The demo uses six fictional event records from ``examples/``. It performs BM25
and cosine ranking, calculates retrieval metrics and confusion counts, checks
the expected first result for each query, and ends with this line on success:

.. code-block:: text

   PASS: deterministic retrieval and evaluation checks completed.

No video is opened, no network request is made, and no model is downloaded.
The fixture vectors are illustrative rather than learned embeddings. The demo
therefore verifies software integration only; it is not a research result.

Configure the full workflow
---------------------------

Copy the template and add a key:

.. code-block:: bash

   cp .env.example .env

.. code-block:: text

   GEMINI_API_KEY=replace-with-your-key
   GEMINI_MODEL=gemini-3.5-flash
   EMBEDDING_MODEL=sentence-transformers/multi-qa-mpnet-base-cos-v1

The code also recognizes the previous ``GOOGLE_GENERATIVE_AI_API_KEY`` name for
compatibility, but new configurations should use ``GEMINI_API_KEY``. Never
commit ``.env``. Confirm that the configured hosted model exists for your
account and supports the input type before a run.

First cloud-backed run
----------------------

From the repository root:

.. code-block:: bash

   cerberus-upload 'data/**/*.mp4' > data/video-files.jsonl

   cerberus-describe \
     'Package Delivery' 'Animal Moving' 'Vehicle Moving' 'People Walking' \
     < data/video-files.jsonl \
     > data/video-events.jsonl

   cerberus-search-sparse 3 'package delivery' \
     < data/video-events.jsonl

Before uploading, read :doc:`limitations_and_ethics`. After the experiment,
inspect and delete remote files:

.. code-block:: bash

   cerberus-list > data/remote-files.jsonl
   cerberus-delete < data/remote-files.jsonl

Next steps
----------

* Follow :doc:`pipeline` for the complete sparse and dense workflows.
* Consult :doc:`cli_reference` for options and legacy wrapper names.
* Define inputs according to :doc:`data_formats`.
* Use :doc:`evaluation` before interpreting any measured result.

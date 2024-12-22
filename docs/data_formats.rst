Data formats
============

JSONL files use UTF-8 with one JSON object per nonblank line. Blank lines are
ignored. The parser rejects non-object JSON values and reports the failing line.

Uploaded video manifest
-----------------------

``cerberus-upload`` produces:

.. code-block:: json

   {"video_id":"files/abc123","pathname":"data/front-door.mp4","name":"files/abc123"}

``pathname`` is the local provenance and eventual evaluation identifier.
``name`` is the remote Gemini file name used by describe and delete operations.
``video_id`` is a stable project-facing copy of that remote name.

Analyzed event record
---------------------

``cerberus-describe`` preserves the manifest fields and adds:

.. code-block:: json

   {"video_id":"files/abc123","pathname":"data/front-door.mp4","name":"files/abc123","description":"A courier leaves a parcel beside the front door.","classifications":[["Package Delivery",true],["Animal Moving",false]]}

Each classification is ``[class_name, value]``. ``value`` is ``true`` or
``false`` only when the model response begins with an unambiguous ``Yes`` or
``No`` token; otherwise it is ``null``. Resolve ``null`` values before confusion
evaluation.

Embedded event record
---------------------

``cerberus-embed`` adds a numeric vector:

.. code-block:: json

   {"pathname":"data/front-door.mp4","description":"A courier leaves a parcel beside the front door.","embedding":[0.021,-0.118,0.304]}

Actual production vectors contain the dimension defined by the configured
embedding model. Do not combine vectors from different models or versions.

Retrieval result
----------------

Both retrieval methods preserve the event fields and add query metadata.
Sparse output contains a larger-is-better ``score``:

.. code-block:: json

   {"pathname":"data/front-door.mp4","description":"A courier leaves a parcel beside the front door.","query":"package delivery","rank":1,"score":1.42,"retrieval_method":"sparse"}

Dense output contains a smaller-is-better cosine ``distance``:

.. code-block:: json

   {"pathname":"data/front-door.mp4","description":"A courier leaves a parcel beside the front door.","embedding":[0.021,-0.118,0.304],"query":"package delivery","rank":1,"distance":0.08,"retrieval_method":"dense"}

Ranks restart at 1 for each query.

Retrieval ground truth
----------------------

Ground truth is one JSON object whose keys exactly match the evaluation queries
and whose values are relevant filename basenames:

.. code-block:: json

   {
     "package delivery": ["camera_front_001.mp4"],
     "person near front door": ["camera_door_004.mp4", "camera_porch_006.mp4"]
   }

Cerberus compares the basenames of record ``pathname`` values. Basenames must
therefore be unique within an evaluation set.

Classification annotations
--------------------------

Actual and predicted JSONL inputs use the analyzed event classification shape:

.. code-block:: json

   {"pathname":"annotations/camera_front_001.mp4","classifications":[["Package Delivery",true],["Animal Moving",false]]}

Records can appear in a different order and class pairs can be reordered;
alignment is by pathname basename and class name. Every class value must be a
JSON boolean, not ``null``, ``0``, ``1``, or a string.

Confusion output
----------------

Each line is a two-element JSON array containing a class name and counts:

.. code-block:: json

   ["Package Delivery",{"total":4,"actual_positive":1,"actual_negative":3,"predicted_positive":1,"predicted_negative":3,"true_positive":1,"false_positive":0,"true_negative":3,"false_negative":0}]

IR JSON report
--------------

With ``cerberus-evaluate-ir --json``, the output is one formatted JSON object,
not JSONL. It contains ``return_k``, ``top_k``, a per-query mapping with ranked
filenames and metrics, and an ``overall`` mapping with macro-averaged metrics.

Fixture provenance
------------------

All committed files in ``examples/`` are fictional. Their descriptions, labels,
and vectors were hand-authored to verify the program. See
``examples/README.md`` before interpreting their output.

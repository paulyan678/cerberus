Limitations, privacy, and ethics
================================

Intended use
------------

Cerberus is an academic tool for studying a CCTV description, classification,
retrieval, and evaluation pipeline. It is suitable for controlled experiments
with authorized or synthetic data. It is not a validated security product.

Privacy and data handling
-------------------------

The full workflow sends selected videos to an external Gemini service. Before
uploading footage:

* establish a lawful and ethical basis and obtain required consent;
* minimize the field of view, duration, resolution, and retention period;
* avoid footage of bystanders or sensitive locations where possible;
* review the service's current data-use, storage, regional, and deletion terms;
* restrict access to local videos, manifests, descriptions, labels, and queries;
* keep credentials outside source control; and
* define and verify both local and remote deletion procedures.

The ignored ``data/`` directory is only a version-control safeguard. It does not
encrypt files, enforce access control, redact people, or satisfy a retention
policy. Deleting a local manifest does not delete its corresponding remote file.
Use ``cerberus-list`` and ``cerberus-delete`` deliberately after a run.

Reliability limits
------------------

* A generated description may omit, invent, or misinterpret activity.
* Binary labels depend on the description, prompt, class wording, hosted model,
  and response format. An unresolved response becomes ``null``.
* Sparse search depends on lexical overlap. Dense search can retrieve semantic
  neighbors that are not relevant and depends on its embedding model.
* Camera position, lighting, occlusion, compression, weather, scene context, and
  event rarity can change performance.
* Hosted model behavior and availability can change independently of this code.
* Aggregate metrics can hide poor results for a particular class, location, or
  group. Small or convenient datasets can produce misleading confidence.

Human oversight
---------------

Do not use a Cerberus result as the sole basis for an emergency response,
disciplinary action, accusation, denial of access, employment or housing
decision, or report to law enforcement. A qualified person must review the
original source and consider uncertainty and context. Preserve an auditable
distinction between model output, human annotation, and verified fact.

Bias and study design
---------------------

Evaluate representative operating conditions and report disaggregated errors
where lawful and appropriate. Define labels before annotation, document
ambiguous cases, use independent reviewers, prevent test leakage, and report
negative findings. Do not imply demographic fairness from overall accuracy or
from the synthetic demo.

Security
--------

Protect API keys and treat derived text as sensitive: descriptions and queries
can reveal schedules, locations, possessions, and behavior even without video.
Review dependencies and provider advisories, rotate exposed keys, and follow the
repository's ``SECURITY.md`` for private disclosure.

Known functional non-goals
--------------------------

Cerberus does not implement face or identity recognition, tamper-resistant
evidence handling, encryption at rest, tenant isolation, role-based access,
real-time alerting, high-availability storage, monitoring, or compliance
certification.

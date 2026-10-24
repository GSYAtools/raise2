# RAISE² Replication Guide

This document describes how to inspect, verify, and re-execute the experiments
contained in the RAISE² evaluation package.

The guide distinguishes between **verification of the frozen evidence** and
**full experimental re-execution**.

These are intentionally separate operations.

---

# 1. Replication modes

## 1.1 Frozen-result verification

This is the recommended first step.

It does not make OpenAI API calls and does not re-run the stochastic
experiments.

It verifies that:

1. the preserved machine-readable results contain the principal values reported
   in `RESULTS.md`; and
2. the artefacts covered by the repository-level SHA-256 manifest have not
   changed.

The semantic result check is:

```bash
python -m raise2.validation.validate_results
```

The frozen package used to prepare this guide produced:

```text
Checks passed: 80/80
Checks failed: 0
FROZEN RESULTS VALIDATION: PASS
```

Repository integrity is checked with:

```bash
sha256sum -c SHA256SUMS
```

These two checks serve different purposes.

`validate_results` checks the semantic consistency of the reported experimental
values.

`sha256sum` checks byte-level integrity of the frozen artefacts.

## 1.2 Deterministic re-evaluation

The deterministic evaluators can be executed again over preserved experimental
outputs without generating new LLM responses.

This reproduces the aggregation and scoring stage of the evaluation.

The experiment-specific commands are documented later in this guide.

## 1.3 Full experimental re-execution

EQ1 and EQ2 contain LLM-based execution stages.

Full re-execution therefore requires:

- a valid OpenAI API key;
- explicit model configuration; and
- network access to the OpenAI API.

A new LLM execution is a **replication**, not a byte-identical reproduction of
the frozen model outputs.

Generative responses can vary even when the same protocol and model family are
used.

EQ3 executes the dTAS exemplar locally and does not require an OpenAI API call.

---

# 2. Repository root

All commands in this guide assume that the current directory is the repository
root:

```bash
cd ~/raise2-evaluation
```

For a repository cloned elsewhere, replace this path with the local clone
location.

The Python package is executed directly from the repository root using module
invocation, for example:

```bash
python -m raise2.validation.validate_results
```

---

# 3. Reference environment

The frozen evaluation was prepared and executed on the following reference
environment:

```text
Operating system: Ubuntu 24.04.4 LTS (Noble Numbat)
Architecture:     x86_64

Python:           3.13.11
Python build:     Anaconda distribution

openai:           2.54.0
python-dotenv:    1.2.4
jsonschema:       4.26.0

Java runtime:     OpenJDK 1.8.0_504
Java compiler:    javac 1.8.0_504
```

These versions document the environment used for the frozen evaluation.

They should not be interpreted as a claim that every patch-level version is
strictly required.

For the strongest replication, use the reference versions where practical.

---

# 4. Python environment

The RAISE² experimental code uses the Python standard library together with
the following external packages:

```text
openai
python-dotenv
jsonschema
```

The versions used in the reference environment were:

```text
openai==2.54.0
python-dotenv==1.2.4
jsonschema==4.26.0
```

A minimal environment can therefore be prepared with:

```bash
python -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip

python -m pip install \
    openai==2.54.0 \
    python-dotenv==1.2.4 \
    jsonschema==4.26.0
```

Verify the installation with:

```bash
python - <<'PY'
import importlib.metadata

for package in [
    "openai",
    "python-dotenv",
    "jsonschema",
]:
    print(
        package,
        importlib.metadata.version(package),
    )
PY
```

---

# 5. OpenAI configuration

LLM-based stages load their configuration from a `.env` file in the repository
root.

The code references the following environment variables:

```text
OPENAI_API_KEY
OPENAI_MODEL
OPENAI_JUDGE_MODEL
```

`OPENAI_MODEL` is used by the RAISE² derivation and lifecycle-revalidation
executors.

`OPENAI_JUDGE_MODEL` is used by the PoI-conformance evaluation stage.

Neither variable has an implicit model default in the executor code. They must
be configured explicitly when performing a new LLM-based execution.

Create the local configuration file as:

```bash
cat > .env <<'EOF_ENV'
OPENAI_API_KEY=YOUR_API_KEY
OPENAI_MODEL=YOUR_EXECUTION_MODEL
OPENAI_JUDGE_MODEL=YOUR_JUDGE_MODEL
EOF_ENV
```

Do **not** commit `.env` to the repository.

The API key used for the frozen experiments is not part of the replication
package.

## 5.1 Frozen execution-model identity

The frozen EQ1 audit and EQ2 evaluator expect the execution-model identifier:

```text
gpt-5.4-mini-2026-03-17
```

This identifier records the model snapshot associated with the frozen
experimental outputs.

A future replication should record the exact model identifier returned by the
API rather than assuming that a current model alias is equivalent to the
historical snapshot.

The judge-model identity used for PoI conformance should likewise be recorded
from the replication execution and should not be inferred from the execution
model.

---

# 6. Java environment for dTAS

EQ3 uses the original dTAS v1.0 software exemplar.

The reference environment uses Java 8:

```text
openjdk version "1.8.0_504"
javac 1.8.0_504
```

On an Ubuntu system where Java 8 development tools are available, verify the
environment with:

```bash
java -version
javac -version
```

Both the Java runtime and compiler must be available for rebuilding the
headless EQ3 harness.

The original dTAS distribution contains precompiled Java classes, but the
RAISE² EQ3 harness and compatibility shim are compiled locally.

---

# 7. Upstream artefact verification

Before re-executing experiments, verify the preserved upstream archives.

## 7.1 MobSTr

Run:

```bash
(
    cd mobstr/original
    sha256sum -c SHA256SUMS.txt
)
```

The preserved MobSTr archive has SHA-256:

```text
3e4a7f2558fddec12d4896316a884f29e68ae71738cb860bcdd3915bd1ddfd91
mobstr-dataset-2021-06.zip
```

## 7.2 dTAS

Run:

```bash
(
    cd dtas/original
    sha256sum -c SHA256SUMS.txt
)
```

The preserved upstream archives are:

```text
155b2f935bd21d43631a4d7cf0c5801e323d8ba872b8f112139401996e84c522
dtas-v1.0-source.zip

9dae192ac21336c9c0474b6c4c26cb4e0594cd60fafc518c55bbad8bfc72df77
dtas-paper-results.zip
```

Further provenance information is provided in `ARTIFACTS.md`.

---


# 7.3 Reconstruct extracted upstream workspaces

The public replication repository preserves the original upstream ZIP
archives rather than versioning duplicate extracted copies.

After verifying their SHA-256 checksums, reconstruct the local upstream
workspaces as follows.

Create the target directories:

~~bash
mkdir -p \
  dtas/work/source \
  dtas/work/paper-results \
  mobstr/original/extracted
~~

Extract the dTAS source distribution:

~~bash
unzip -q \
  dtas/original/dtas-v1.0-source.zip \
  -d dtas/work/source
~~

The archive contains `dTAS/` as its top-level directory, producing:

~~text
dtas/work/source/dTAS/
~~

Extract the original dTAS paper-result artefacts:

~~bash
unzip -q \
  dtas/original/dtas-paper-results.zip \
  -d dtas/work/paper-results
~~

This produces:

~~text
dtas/work/paper-results/results paper/
~~

Extract the MobSTr upstream dataset:

~~bash
unzip -q \
  mobstr/original/mobstr-dataset-2021-06.zip \
  -d mobstr/original/extracted
~~

The archive contains the versioned upstream directory:

~~text
panorama-research-mobstr-dataset-a73608d/
~~

and therefore produces:

~~text
mobstr/original/extracted/panorama-research-mobstr-dataset-a73608d/
~~

These extracted directories are local reconstruction products and are
intentionally excluded from Git.

The preserved ZIP archives and their SHA-256 manifests are the upstream
integrity roots.

---

# 8. Verify the frozen package before re-execution

Before performing any new experimental run, execute:

```bash
python -m raise2.validation.validate_results
```

and:

```bash
sha256sum -c SHA256SUMS
```

The first command verifies the principal reported results against the
machine-readable result artefacts.

The second verifies the selected frozen files against the repository-level
integrity manifest.

If either check fails on an unmodified public replication package, investigate
the discrepancy before executing new experiments.

---

# 9. Re-execution policy

The frozen artefacts under:

```text
raise2/evaluation/
raise2/results/
mobstr/work/frozen-protocol/
mobstr/work/test-visible/
mobstr/work/reference/
mobstr/work/raise2-output/
mobstr/work/revalidation/
dtas/work/eq3-harness/
dtas/work/eq3-b/
```

represent the evidence associated with the reported evaluation.

Do not overwrite these artefacts when performing an independent extension of
the study.

For exploratory or extended experiments, use a separate result namespace or a
separate repository clone.

The remaining sections of this guide document the original EQ1, EQ2, and EQ3
execution and evaluation procedures.

---

# 10. EQ1 — Concern-relative derivation

EQ1 evaluates repeated concern-relative derivation using the MobSTr exemplar.

The experiment uses two evaluation concerns:

```text
H1
H3
```

Development concerns H2 and H5 were used during protocol development and are
not counted as independent EQ1 evaluation cases.

The frozen EQ1 design is documented in:

```text
raise2/experiments/mobstr/EQ1-DESIGN.txt
```

The experiment definitions are:

```text
raise2/experiments/mobstr/H1.json
raise2/experiments/mobstr/H3.json
```

---

## 10.1 Frozen visible evidence

The evidence visible to the derivation executor is stored separately for each
evaluation concern.

For H1:

```text
mobstr/work/test-visible/H1/hazard.txt
mobstr/work/test-visible/H1/requirements.tsv
mobstr/work/test-visible/H1/architecture/
```

For H3:

```text
mobstr/work/test-visible/H3/hazard.txt
mobstr/work/test-visible/H3/requirements.tsv
mobstr/work/test-visible/H3/architecture/
```

The selection procedure is documented in:

```text
mobstr/work/test-visible/SELECTION-PROTOCOL.txt
```

Reference material used later for evaluation is stored separately and is not
part of these test-visible inputs.

---

## 10.2 Derivation execution

EQ1 contains:

```text
30 H1 derivations
30 H3 derivations
60 derivations total
```

Each run invokes:

```text
raise2.executor.rr_executor
```

using the corresponding frozen experiment definition.

The batch runner is:

```bash
python -m raise2.experiments.run_mobstr_eq1
```

### Historical H1-run-001 detail

The preserved experimental campaign contains:

```text
H1-run-001 ... H1-run-030
H3-run-001 ... H3-run-030
```

`H1-run-001` was executed before the batch runner was introduced.

Consequently, the preserved `run_mobstr_eq1.py` batch configuration covers:

```text
H1-run-002 ... H1-run-030
H3-run-001 ... H3-run-030
```

This is why invoking the batch runner over the already populated frozen
repository reports 59 skipped batch runs rather than 60.

The final experimental dataset nevertheless contains exactly 30 H1 runs and
30 H3 runs.

The runner does not automatically retry a failed derivation.

A failed execution therefore remains part of the experimental record rather
than being silently replaced.

---

## 10.3 EQ1 derivation audit

The 60 preserved derivations can be audited with:

```bash
python -m raise2.evaluator.audit_eq1
```

For the frozen experiment, the audit reports:

### H1

```text
Expected runs: 30
Audited runs:  30
Valid statuses: 30
Distinct raw derivation files: 30
Distinct semantic derivations: 30
Returned model:
  gpt-5.4-mini-2026-03-17: 30
CONFIGURATION CONSISTENCY: PASS
```

The number of CRDs per H1 run was:

```text
min = 1
median = 2
max = 4
```

The number of ORRs per H1 run was:

```text
min = 1
median = 2
max = 4
```

### H3

```text
Expected runs: 30
Audited runs:  30
Valid statuses: 30
Distinct raw derivation files: 30
Distinct semantic derivations: 30
Returned model:
  gpt-5.4-mini-2026-03-17: 30
CONFIGURATION CONSISTENCY: PASS
```

The number of CRDs per H3 run was:

```text
min = 1
median = 1
max = 3
```

The number of ORRs per H3 run was:

```text
min = 1
median = 1
max = 3
```

The audit output is written to:

```text
raise2/results/mobstr-eq1-audit.json
```

The audit is deterministic and does not require an OpenAI API call.

---

## 10.4 PoI-conformance assessment

The derived Phenomenon of Interest is assessed independently from reference
recovery.

The frozen design is documented in:

```text
raise2/experiments/mobstr/POI-CONFORMANCE-DESIGN.txt
```

Each of the 60 derivations is assessed three times:

```text
judge-01
judge-02
judge-03
```

Therefore the initial assessment design contains:

```text
60 derivations x 3 assessments = 180 assessments
```

The assessment runner is:

```bash
python -m raise2.experiments.run_poi_conformance
```

Each assessment invokes:

```text
raise2.evaluator.poi_conformance_evaluator
```

and uses the model configured by:

```text
OPENAI_JUDGE_MODEL
```

The runner does not automatically retry API failures.

---

## 10.5 PoI API-failure recovery

During the frozen PoI-conformance campaign, 22 of the original 180 assessment
attempts terminated with:

```text
status = api_error
```

All 22 occurred during H3 assessment.

The original failed assessment directories were preserved.

They were not overwritten.

A non-destructive recovery procedure created corresponding identifiers of the
form:

```text
judge-XX-resume-01
```

The frozen experimental record contains:

```text
Original API failures:       22
Historical resume records:   22
Valid historical recoveries: 22
```

All 22 recovery records have:

```text
status = completed_valid
```

The recovery utility is:

```bash
python -m raise2.experiments.resume_failed_poi_conformance
```

The public replication version of this utility is idempotent: an original
`api_error` is not considered pending when a valid `completed_valid`
`resume-*` record already exists.

Therefore, when executed over the complete frozen repository, it reports:

```text
Unrecovered API assessments found: 0
Nothing to resume.
```

A new recovery is created only when an original API failure does not already
have a valid recovery.

This preserves both the failed attempt and its recovery as separate provenance
records.

---

## 10.6 Aggregate PoI classification

After valid PoI assessments are available, aggregate them with:

```bash
python -m raise2.evaluator.aggregate_poi_conformance
```

The aggregate result is written to:

```text
raise2/results/mobstr-eq1-poi-conformance.json
```

The frozen aggregate contains:

```text
60 final run-level PoI classifications
59 unanimous decisions
1 majority decision
```

By concern:

```text
H1:
  ALIGNED          22
  OVEREXTENDED      8
  UNDERDETERMINED   0

H3:
  ALIGNED          30
  OVEREXTENDED      0
  UNDERDETERMINED   0
```

Aggregation is deterministic once the valid judge assessments have been
produced.

---

## 10.7 Extract the derived CRD catalogue

Extract all derived CRDs from the 60 frozen derivations with:

```bash
python -m raise2.evaluator.extract_eq1_crds
```

The principal outputs are:

```text
raise2/results/mobstr-eq1-crds.tsv
raise2/results/mobstr-eq1-crd-summary.json
```

This step is deterministic.

---

## 10.8 Reference distinctions

The independently prepared reference distinctions are:

```text
mobstr/work/reference/coder1/H1/reference-crds.tsv
mobstr/work/reference/coder1/H3/reference-crds.tsv
```

These reference artefacts were prepared separately from the LLM derivations.

Their integrity information is documented in `ARTIFACTS.md`.

The matching procedure is documented in:

```text
raise2/experiments/mobstr/EQ1-REFERENCE-MATCHING.txt
```

---

## 10.9 Deterministic reference matching

Generate reference-match candidates with:

```bash
python -m raise2.evaluator.match_eq1_references
```

The matcher consumes:

```text
raise2/results/mobstr-eq1-crds.tsv
raise2/results/mobstr-eq1-poi-conformance.json
```

and writes:

```text
raise2/results/mobstr-eq1-reference-candidates.tsv
```

The matcher distinguishes clear automatic matches from lexically ambiguous
cases requiring explicit review.

A lexical candidate is therefore not automatically treated as a recovered
reference distinction.

---

## 10.10 Adjudication-template construction

Construct the adjudication table with:

```bash
python -m raise2.evaluator.prepare_eq1_adjudication
```

For the frozen experiment this produces:

```text
Lexical reviews requiring human decision: 18
Pre-recorded H3-REF2 audit decisions:     30
Total adjudication rows:                  48
```

The output is:

```text
raise2/evaluation/mobstr/reference-adjudication.tsv
```

### Lexical-review cases

Eighteen run-reference pairs were lexically ambiguous and therefore required a
human decision.

The deterministic matcher does not decide these cases automatically.

### H3-REF2 zero-recovery audit

H3-REF2 produced zero lexical candidates.

Because absence of lexical candidates alone is not sufficient evidence of
non-recovery, all H3 derived CRDs were subsequently inspected for the
corresponding braking-relevant spatial-relation distinction.

No such distinction was identified.

The resulting 30 run-level decisions were therefore explicitly recorded as:

```text
NOT_RECOVERED
```

with:

```text
reason_for_adjudication = zero-recovery-audit
```

This audit is distinct from the 18 lexical-review adjudications.

---

## 10.11 Applying the human adjudications

The 18 human decisions and their rationales are preserved explicitly in:

```text
raise2/evaluator/apply_eq1_adjudication.py
```

Apply them to a newly generated adjudication template with:

```bash
python -m raise2.evaluator.apply_eq1_adjudication
```

For the frozen adjudication set the expected result is:

```text
Human adjudications applied: 18
Unresolved lexical reviews: 0
```

This script does **not** automate the human judgement.

It deterministically applies the already recorded human decisions to the
generated adjudication template.

The script fails if:

- an expected adjudication decision is missing;
- a lexical-review row has already been populated; or
- any lexical-review case remains unresolved.

The final adjudication table used by EQ1 is therefore explicit and
machine-inspectable.

---

## 10.12 Final EQ1 evaluation

Once PoI classification, deterministic matching, and adjudication are
available, compute the final EQ1 metrics with:

```bash
python -m raise2.evaluator.evaluate_eq1
```

The final outputs are:

```text
raise2/results/mobstr-eq1-final-results.json
raise2/results/mobstr-eq1-final-results.tsv
```

The principal frozen results are summarised in `RESULTS.md`.

The final evaluator is deterministic and does not make an OpenAI API call.

---

## 10.13 EQ1 reproduction paths

There are three useful levels of EQ1 reproduction.

### A. Verify the frozen result

No API call is required:

```bash
python -m raise2.validation.validate_results
```

### B. Recompute deterministic EQ1 artefacts

Starting from preserved derivations and preserved valid PoI assessments, the
deterministic stages are:

```bash
python -m raise2.evaluator.audit_eq1
python -m raise2.evaluator.aggregate_poi_conformance
python -m raise2.evaluator.extract_eq1_crds
python -m raise2.evaluator.match_eq1_references
python -m raise2.evaluator.evaluate_eq1
```

The frozen adjudication table is already present under
`raise2/evaluation/mobstr/`.

Do not run `prepare_eq1_adjudication` over the frozen adjudication file merely
to verify the published result, because that command intentionally constructs
a fresh adjudication template.

### C. Full EQ1 replication

A new full replication requires new LLM derivations and new PoI assessments.

Use a clean repository clone or separate result namespace before doing so.

The historical batch runner is:

```bash
python -m raise2.experiments.run_mobstr_eq1
```

and PoI assessment is launched with:

```bash
python -m raise2.experiments.run_poi_conformance
```

If API failures occur, recover only unrecovered failures with:

```bash
python -m raise2.experiments.resume_failed_poi_conformance
```

Then aggregate and evaluate using the deterministic stages described above.

Because the LLM stages are stochastic, a new full replication is not expected
to reproduce the frozen raw responses byte-for-byte.

The appropriate comparison is against the experimental metrics and
distributions reported in `RESULTS.md`.

---

# 11. EQ2 — Lifecycle revalidation

EQ2 evaluates lifecycle reasoning after a concern-relative representation
specification has already been established.

The experiment does not ask the model to derive a new representation
specification from scratch.

Instead, it starts from a frozen expert H1 baseline and introduces six
controlled lifecycle changes.

The frozen design is documented in:

```text
raise2/experiments/mobstr/EQ2-DESIGN.txt
```

---

## 11.1 Constructing the frozen H1 revalidation baseline

The baseline builder is:

```text
raise2/experiments/build_revalidation_baseline.py
```

It constructs:

```text
mobstr/work/revalidation/H1/baseline.json
```

from the frozen H1 representation specification and its supporting evidence.

The baseline contains:

```text
1 Evaluation Target
1 Phenomenon of Interest
3 CRDs
3 ORRs
3 assumptions
3 revalidation conditions
```

The Evaluation Target is:

```text
Determine whether the current operational situation requires a braking
maneuver to avoid collision.
```

The Phenomenon of Interest is:

```text
The collision-relevant spatial situation between the ego vehicle and
obstacles on or near its trajectory.
```

The three frozen CRDs concern:

```text
H1-CRD1  obstacle presence
H1-CRD2  object category
H1-CRD3  obstacle distance relative to braking need
```

The corresponding ORRs are:

```text
H1-ORR1  preserve collision-relevant obstacle presence
H1-ORR2  preserve vulnerable-road-user versus other-object distinction
H1-ORR3  preserve braking-relevant versus non-braking-relevant
         ego-object spatial condition
```

The baseline builder also records SHA-256 provenance for the source context,
expert CRDs, expert ORRs, requirements, and architecture representation.

Build the baseline with:

```bash
python -m raise2.experiments.build_revalidation_baseline
```

The frozen baseline identifier is:

```text
mobstr-H1-revalidation-baseline-v1
```

The frozen baseline SHA-256 is:

```text
e7e53a8058e7da0a0d22bc43c6dd38e629e704897b701239597302e777cc9965
```

The scenario builder refuses to proceed if this hash does not match.

---

## 11.2 Controlled lifecycle scenarios

The scenario builder is:

```text
raise2/experiments/build_eq2_scenarios.py
```

Run:

```bash
python -m raise2.experiments.build_eq2_scenarios
```

It first verifies the frozen baseline hash.

It then creates six executor-visible lifecycle changes under:

```text
mobstr/work/revalidation/H1/changes/
```

and a separate evaluation ground truth under:

```text
raise2/evaluation/mobstr/eq2-ground-truth.json
```

The six changes are:

### delta-01 — Driver-warning presentation update

```text
Change class:
  architecture / presentation

Expected lifecycle decision:
  NONE
```

The change modifies presentation only and explicitly leaves obstacle
information, object category, spatial information, PoI, and Evaluation Target
unchanged.

### delta-02 — Obstacle-presence information interface change

```text
Change class:
  representation dependency

Expected lifecycle decision:
  REVALIDATE

Expected affected ORR:
  H1-ORR1
```

This scenario changes the interface supplying obstacle-presence information to
the operational representation.

### delta-03 — Object-category scheme revision

```text
Change class:
  requirement

Expected lifecycle decision:
  REVALIDATE

Expected affected ORR:
  H1-ORR2
```

This scenario changes the object-category scheme covered by the corresponding
frozen revalidation condition.

### delta-04 — Dangerous-zone definition introduced

```text
Change class:
  requirement

Expected lifecycle decision:
  REVALIDATE

Expected affected ORR:
  H1-ORR3
```

This scenario replaces the previously unspecified dangerous-zone boundary with
an explicit configurable braking-zone definition.

### delta-05 — Phenomenon-of-Interest scope extension

```text
Change class:
  phenomenon scope

Expected lifecycle decision:
  REDERIVE

Expected return point:
  RR2
```

Road-surface condition is introduced as part of the phenomenon used to
determine whether braking is required.

The Evaluation Target itself remains unchanged.

### delta-06 — Evaluation Target extension

```text
Change class:
  evaluation target

Expected lifecycle decision:
  REDERIVE

Expected return point:
  RR1
```

The target is extended from deciding whether braking is required to deciding
whether either braking or an evasive lane-change manoeuvre is required.

---

## 11.3 Frozen ground truth

The ground-truth distribution is:

```text
NONE        1
REVALIDATE  3
REDERIVE    2
```

The scenario builder contains integrity checks requiring:

```text
exactly 6 change identifiers
exactly 6 ground-truth identifiers
one-to-one change/ground-truth identifier correspondence
decision distribution = 1 / 3 / 2
```

The ground truth is generated separately from the executor-visible change
files.

The builder explicitly separates:

```text
executor-visible lifecycle changes
```

from:

```text
hidden evaluation ground truth
```

The ground truth is not supplied to `rv_executor`.

---

## 11.4 Baseline/change binding

Each generated change file contains:

```text
baseline_id
baseline_sha256
change_id
change_type
description
changed_elements
```

Before an LLM request is made, `rv_executor` independently computes the hash
of the supplied baseline and checks:

```text
change.baseline_sha256 == actual baseline SHA-256
```

It also checks:

```text
change.baseline_id == baseline.baseline_id
```

Execution stops if either binding check fails.

This prevents a lifecycle scenario from being evaluated accidentally against a
different representation baseline.

---

## 11.5 RV execution inputs

The lifecycle executor is:

```text
raise2/executor/rv_executor.py
```

For each run it receives:

```text
frozen baseline
lifecycle change
RV protocol
structured-output schema
```

The protocol is:

```text
raise2/protocol/rv-protocol.txt
```

The output schema is:

```text
raise2/schemas/rv-result.schema.json
```

The executor does not load:

```text
raise2/evaluation/mobstr/eq2-ground-truth.json
```

The ground truth is loaded only later by the deterministic EQ2 evaluator.

The execution model is configured through:

```text
OPENAI_MODEL
```

The frozen 60-run experiment used the returned model identifier:

```text
gpt-5.4-mini-2026-03-17
```

---

## 11.6 Execute the 60 lifecycle assessments

The EQ2 runner is:

```text
raise2/experiments/run_mobstr_eq2.py
```

It defines:

```text
6 changes
10 independent runs per change
60 runs total
```

Execute with:

```bash
python -m raise2.experiments.run_mobstr_eq2
```

For each scenario, the runner invokes:

```text
raise2.executor.rv_executor
```

with run identifiers:

```text
run-001 ... run-010
```

Results are stored under:

```text
raise2/results/mobstr-eq2/<change-id>/<run-id>/
```

Existing result directories are skipped.

Failed executions are not automatically retried.

This preserves execution failures rather than silently replacing them.

---

## 11.7 Structured-output validation

`rv_executor` validates the returned lifecycle decision against:

```text
raise2/schemas/rv-result.schema.json
```

It additionally applies lifecycle invariants against the supplied baseline.

The result records include provenance such as:

```text
baseline SHA-256
change SHA-256
protocol SHA-256
schema SHA-256
requested model
returned model
validation status
```

Only structurally and semantically valid outputs are accepted as valid runs.

---

## 11.8 Deterministic EQ2 evaluation

Evaluate the preserved outputs with:

```bash
python -m raise2.evaluator.evaluate_eq2
```

This stage does not make an OpenAI API call.

The evaluator loads:

```text
raise2/evaluation/mobstr/eq2-ground-truth.json
```

only at evaluation time.

Before computing metrics it performs an integrity gate.

The frozen evaluation requires:

```text
60 expected runs
status = completed_valid
validation_passed = true
expected model identity
consistent baseline provenance
consistent change provenance
```

If the integrity checks fail, the evaluator does not report the final
experimental metrics.

For the frozen package:

```text
INTEGRITY CHECK: PASS
Valid runs: 60/60
```

---

## 11.9 EQ2 metrics

The evaluator computes four principal metrics.

### Lifecycle decision accuracy

Whether the predicted lifecycle action is:

```text
NONE
REVALIDATE
REDERIVE
```

as specified by the frozen ground truth.

Frozen result:

```text
55/60 = 91.7%
```

### Affected-ORR exact accuracy

For `REVALIDATE` scenarios, whether the predicted affected ORR set exactly
matches the ground truth.

Frozen result:

```text
25/30 = 83.3%
```

### Return-point accuracy

For `REDERIVE` scenarios, whether the predicted RAISE² return point exactly
matches the ground truth.

Frozen result:

```text
20/20 = 100.0%
```

### Exact lifecycle outcome

A run is exact only when all applicable lifecycle fields agree with the ground
truth.

Frozen result:

```text
55/60 = 91.7%
```

---

## 11.10 Scenario-level reproducibility

The frozen scenario results are:

```text
delta-01 [NONE]
  exact outcome: 10/10
  distinct outcomes: 1

delta-02 [REVALIDATE H1-ORR1]
  exact outcome: 10/10
  distinct outcomes: 1

delta-03 [REVALIDATE H1-ORR2]
  exact outcome: 10/10
  distinct outcomes: 1

delta-04 [REVALIDATE H1-ORR3]
  exact outcome: 5/10
  distinct outcomes: 2

delta-05 [REDERIVE RR2]
  exact outcome: 10/10
  distinct outcomes: 1

delta-06 [REDERIVE RR1]
  exact outcome: 10/10
  distinct outcomes: 1
```

`delta-04` is the only scenario that is not fully reproducible across the 10
runs.

Its decisions split between:

```text
REVALIDATE
REDERIVE
```

The five resulting `REDERIVE` classifications returned to:

```text
RR3
```

This is the only source of lifecycle-decision error in the frozen EQ2
campaign.

---

## 11.11 Decision confusion matrix

The frozen confusion matrix is:

```text
expected\actual   NONE   REVALIDATE   REDERIVE
NONE                10       0           0
REVALIDATE           0      25           5
REDERIVE             0       0          20
```

No `NONE` scenario was escalated.

No `REDERIVE` scenario was downgraded to either `NONE` or `REVALIDATE`.

All five errors occurred in the same `REVALIDATE` scenario.

---

## 11.12 EQ2 result artefacts

The final evaluator writes:

```text
raise2/results/mobstr-eq2-final-results.json
raise2/results/mobstr-eq2-final-results.tsv
raise2/results/mobstr-eq2-scenario-summary.tsv
```

The aggregate values are indexed in `RESULTS.md`.

---

## 11.13 EQ2 reproduction paths

### A. Verify the frozen result

No API call is required:

```bash
python -m raise2.evaluator.evaluate_eq2
```

The frozen package should report:

```text
INTEGRITY CHECK: PASS
Valid runs: 60/60
```

followed by the metrics documented above.

The repository-wide semantic validator can additionally be run with:

```bash
python -m raise2.validation.validate_results
```

### B. Rebuild the experimental definitions

The baseline and scenarios can be reconstructed with:

```bash
python -m raise2.experiments.build_revalidation_baseline
python -m raise2.experiments.build_eq2_scenarios
```

The scenario builder will refuse to proceed if the reconstructed baseline does
not have the frozen expected SHA-256.

These commands write the baseline, six change files, and ground-truth file.

They should therefore be used in a clean replication workspace when the goal
is to reconstruct the experiment rather than merely verify the frozen
evidence.

### C. Full EQ2 replication

A new LLM-based replication requires a configured `.env` and API access.

From a clean replication workspace:

```bash
python -m raise2.experiments.build_revalidation_baseline
python -m raise2.experiments.build_eq2_scenarios
python -m raise2.experiments.run_mobstr_eq2
python -m raise2.evaluator.evaluate_eq2
```

Because the model stage is stochastic, a new replication should be compared
against the frozen scenario-level and aggregate metrics rather than against
byte-identical raw responses.

---

# 12. EQ3 — Runtime representational adequacy in dTAS

EQ3 evaluates an operationalised Observable Representation Requirement in the
dTAS v1.0 self-adaptive-system exemplar.

Unlike EQ1 and EQ2, EQ3 does not require an OpenAI API call.

It executes the original dTAS software locally through a headless Java harness.

EQ3 has two phases:

```text
EQ3-A  observe representational adequacy under the original configuration

EQ3-B  introduce controlled degradation of the native representation-update
       mechanism and measure the resulting change in ORR violations
```

The frozen design is documented in:

```text
raise2/experiments/dtas/EQ3-DESIGN.txt
```

---

## 12.1 dTAS upstream artefacts

The preserved dTAS archives are:

```text
dtas/original/dtas-v1.0-source.zip
dtas/original/dtas-paper-results.zip
```

Verify them with:

```bash
(
    cd dtas/original
    sha256sum -c SHA256SUMS.txt
)
```

The source distribution is extracted under:

```text
dtas/work/source/dTAS/
```

The original paper-result artefacts are extracted under:

```text
dtas/work/paper-results/
```

The upstream ZIP files are the integrity roots for the external dTAS
distribution.

---

## 12.2 Java 8 compatibility

The original dTAS distribution targets Java 8.

The reference environment uses:

```text
openjdk version "1.8.0_504"
javac 1.8.0_504
```

Verify with:

```bash
java -version
javac -version
```

The original source distribution also relies on `javafx.util.Pair`.

The JavaFX library available on the reference Ubuntu system was compiled for a
newer class-file version than the Java 8 runtime required by dTAS.

A minimal compatibility shim is therefore provided at:

```text
dtas/work/eq3-harness/shim-src/javafx/util/Pair.java
```

The shim implements only the Pair API required by the original compiled dTAS
classes.

It does not implement or modify dTAS adaptation logic.

---

## 12.3 Build EQ3-A

The reproducible EQ3-A builder is:

```text
raise2/experiments/build_dtas_eq3.py
```

Run:

```bash
python -m raise2.experiments.build_dtas_eq3
```

The builder:

1. verifies the required dTAS classes and libraries;
2. compiles the JavaFX Pair compatibility shim for Java 8;
3. compiles the headless EQ3-A harness for Java 8; and
4. writes a build manifest.

The source harness is:

```text
dtas/work/eq3-harness/DTASEQ3Harness.java
```

with frozen SHA-256:

```text
c84f3652738de5b96fdb7dd47a6ed37e648824f77ba8830429c17e51c6d8692f
```

The Pair shim has frozen SHA-256:

```text
d08fcb8c575ea64ad5e170c490bbcbcdd752bc543836d19df503f9320a7220b0
```

The builder writes:

```text
dtas/work/eq3-harness/manifest.json
```

which records both source and compiled-artifact hashes.

The compiled classes themselves are build products. The frozen source hashes
are the principal integrity identifiers for the EQ3-A harness implementation.

---

## 12.4 EQ3-A operationalised ORR

The original dTAS reliability goal uses the threshold:

```text
failure rate < 0.19
```

The concern-relevant states are therefore:

```text
SATISFIED  failure rate < 0.19
VIOLATED   failure rate >= 0.19
```

For each adaptation cycle, EQ3 observes:

```text
real_failure_rate
represented_failure_rate
```

and derives:

```text
real_goal_state
represented_goal_state
```

The operationalised ORR is preserved exactly when:

```text
real_goal_state == represented_goal_state
```

Thus:

```text
ORR preserved
    iff
actual and represented failure rates lie on the same side
of the concern-relevant threshold
```

This criterion intentionally differs from a generic numerical-error threshold.

---

## 12.5 EQ3-A headless execution

The EQ3-A runner is:

```text
raise2/experiments/run_dtas_eq3.py
```

It defines:

```text
30 independent runs
20 adaptation cycles per run
600 cycle-level observations
```

Execute with:

```bash
python -m raise2.experiments.run_dtas_eq3
```

The runner invokes:

```text
DTASEQ3Harness
```

through Java using a classpath containing:

```text
EQ3 harness
Pair compatibility shim
TeleAssistanceSystem compiled classes
ResearchServicePlatform compiled classes
antlrworks-1.5.2-complete.jar
javax.jms-api-2.0.jar
xstream-1.5.0.jar
```

The Java process is executed with the dTAS `TAS_gui` directory as its working
directory because the original exemplar resolves runtime resources relative to
that location.

For each run, the runner writes:

```text
raise2/results/dtas-eq3-a/run-NNN/observations.csv
raise2/results/dtas-eq3-a/run-NNN/execution.log
```

---

## 12.6 EQ3-A run validation

A run is accepted only when its `observations.csv` passes the runner's
validation checks.

These require:

```text
exactly 20 rows
cycle identifiers exactly 1..20
orr_preserved in {true,false}
violation_type in {
    NONE,
    MISSED_VIOLATION,
    FALSE_VIOLATION
}
```

The runner additionally verifies the invariant:

```text
orr_preserved
    ==
(real_goal_state == represented_goal_state)
```

An existing valid run is skipped.

An existing invalid run is reported as failed rather than silently
overwritten.

---

## 12.7 Evaluate EQ3-A

Evaluate the preserved 30-run dataset with:

```bash
python -m raise2.evaluator.evaluate_dtas_eq3
```

The frozen package reproduces:

```text
INTEGRITY CHECK: PASS
Runs:         30/30
Observations: 600/600
```

The principal concern-relative result is:

```text
ORR violations:             30/600 (5.0%)
Runs with >=1 violation:    27/30 (90.0%)
```

All violations are:

```text
MISSED_VIOLATION
```

with:

```text
Missed violations: 30
False violations:   0
```

Therefore:

```text
Missed-violation rate: 30/30  = 100.0%
False-violation rate:   0/570 =   0.0%
```

---

## 12.8 Numerical error versus concern-relative adequacy

EQ3-A also compares absolute numerical representation error with the
concern-relative ORR.

For preserved observations:

```text
n      = 570
median = 0.003747096623333321
mean   = 0.009605891900643274
max    = 0.08416973824
```

For violated observations:

```text
n      = 30
median = 0.04491840162666663
mean   = 0.04634929942399995
max    = 0.07841787391999995
```

The frozen evaluator identifies an accuracy/adequacy inversion.

The maximum-error preserved observation is:

```text
run-021
cycle 1
absolute error = 0.08416973824
```

The minimum-error violated observation is:

```text
run-002
cycle 4
absolute error = 0.008019871099999937
```

Therefore a numerically less accurate representation can preserve the
concern-relevant distinction while a numerically more accurate representation
can fail to preserve it.

The evaluator reports:

```text
Error/adequacy inversion observed: True
```

---

## 12.9 EQ3-A outputs

The final deterministic evaluator writes:

```text
raise2/results/dtas-eq3-a-final-results.json
raise2/results/dtas-eq3-a-run-summary.tsv
raise2/results/dtas-eq3-a-cycle-results.tsv
```

The frozen result hashes are documented in `ARTIFACTS.md`.

---

# 13. EQ3-B — Controlled degradation

EQ3-B tests whether concern-relative representational failures respond to a
controlled degradation of the native dTAS representation-update mechanism.

The manipulated native parameter is:

```text
MonitorMinFailureDelta
```

The controlled parameter is:

```text
MonitorFailureChange
```

---

## 13.1 Build the EQ3-B conditions

The builder is:

```text
raise2/experiments/build_dtas_eq3b.py
```

Run:

```bash
python -m raise2.experiments.build_dtas_eq3b
```

The builder creates four conditions:

```text
mfd-0005  MonitorMinFailureDelta = 0.005
mfd-0010  MonitorMinFailureDelta = 0.010
mfd-0020  MonitorMinFailureDelta = 0.020
mfd-0040  MonitorMinFailureDelta = 0.040
```

Across all four conditions:

```text
MonitorFailureChange = 0.005
```

The generated XML files are:

```text
dtas/work/eq3-b/conditions/mfd-0005.xml
dtas/work/eq3-b/conditions/mfd-0010.xml
dtas/work/eq3-b/conditions/mfd-0020.xml
dtas/work/eq3-b/conditions/mfd-0040.xml
```

The builder also generates and compiles:

```text
dtas/work/eq3-b/DTASEQ3BHarness.java
```

and writes:

```text
dtas/work/eq3-b/manifest.json
```

The frozen builder SHA-256 is:

```text
0e737c8bf292b68512d91dd5e73a1272a233796d439f123213976c78428d34a3
```

The reconstructed frozen manifest SHA-256 is:

```text
f4d18ecf2240240e79b3218dd68ed8f9b1d8fe47c7f78cedaa1c470febed260b
```

The builder reports:

```text
Generated conditions: 4
Runs per condition: 10
Cycles per run: 20
New executions required: 30
```

---

## 13.2 Baseline reuse

EQ3-B does not generate a new stochastic baseline after observing EQ3-A.

Instead, condition:

```text
mfd-0005
```

reuses:

```text
EQ3-A run-001 ... run-010
```

The EQ3-B runner validates each source CSV and copies it into the uniform
EQ3-B result structure.

For each reused run it writes:

```text
provenance.json
```

containing:

```text
mode = reused_from_eq3_a
```

No new dTAS execution is performed for these 10 baseline runs.

This is why:

```text
EQ3-A:
  30 runs
  600 observations

EQ3-B baseline:
  first 10 frozen EQ3-A runs
  200 observations
```

are related but not numerically identical aggregate samples.

---

## 13.3 Execute EQ3-B

The runner is:

```text
raise2/experiments/run_dtas_eq3b.py
```

Run:

```bash
python -m raise2.experiments.run_dtas_eq3b
```

The execution design is:

```text
mfd-0005:
  10 reused EQ3-A runs
  0 new executions

mfd-0010:
  10 new executions

mfd-0020:
  10 new executions

mfd-0040:
  10 new executions
```

Therefore:

```text
40 total condition-runs
10 reused baseline runs
30 new dTAS executions
800 cycle-level observations
```

The baseline condition is explicitly excluded from the new-execution loop.

---

## 13.4 EQ3-B run validation

Each condition-run must contain exactly:

```text
20 cycles
```

The runner validates:

```text
cycle sequence
run identifier
ORR-preservation values
violation-type values
real/represented goal-state consistency
```

Existing valid outputs are skipped.

Existing invalid outputs are reported as failures rather than silently
overwritten.

---

## 13.5 Evaluate EQ3-B

Evaluate the preserved condition runs with:

```bash
python -m raise2.evaluator.evaluate_dtas_eq3b
```

The frozen package reproduces:

```text
INTEGRITY CHECK: PASS
Experimental unit: independent run
Runs:   40/40
Cycles: 800/800
```

The independent run, rather than the individual adaptation cycle, is the
experimental unit for inferential comparisons.

---

## 13.6 EQ3-B condition results

The frozen condition results are:

```text
mfd-0005
  ORR violations:       13/200 (6.5%)
  Runs affected:        10/10
  Mean violations/run:  1.300
  Mean abs. error/run:   0.011665

mfd-0010
  ORR violations:       24/200 (12.0%)
  Runs affected:         9/10
  Mean violations/run:   2.400
  Mean abs. error/run:    0.017419

mfd-0020
  ORR violations:       25/200 (12.5%)
  Runs affected:         9/10
  Mean violations/run:   2.500
  Mean abs. error/run:    0.034519

mfd-0040
  ORR violations:       31/200 (15.5%)
  Runs affected:        10/10
  Mean violations/run:   3.100
  Mean abs. error/run:    0.058202
```

All 93 violations across the four conditions are:

```text
MISSED_VIOLATION
```

No `FALSE_VIOLATION` occurs.

---

## 13.7 Run-level bootstrap comparison

The evaluator compares each degraded condition against the reused baseline
using the independent run as the resampling unit.

The frozen procedure uses:

```text
10,000 bootstrap replicates
seed = 20261024
resampling unit = run
```

For ORR violations per run:

```text
mfd-0010:
  delta = +1.100
  95% bootstrap CI = [0.300, 1.800]

mfd-0020:
  delta = +1.200
  95% bootstrap CI = [0.300, 2.100]

mfd-0040:
  delta = +1.800
  95% bootstrap CI = [1.300, 2.300]
```

For mean absolute representation error per run:

```text
mfd-0010:
  delta = +0.005753
  95% bootstrap CI = [0.004394, 0.007100]

mfd-0020:
  delta = +0.022853
  95% bootstrap CI = [0.021285, 0.024485]

mfd-0040:
  delta = +0.046536
  95% bootstrap CI = [0.045641, 0.047487]
```

---

## 13.8 Controlled trend

Mean ORR violations per independent run follow:

```text
1.300 -> 2.400 -> 2.500 -> 3.100
```

The frozen evaluator reports:

```text
Non-decreasing:      True
Strictly increasing: True
```

Thus, within the controlled dTAS experiment, increasing the minimum failure
delta required for representation updates is associated with a systematic
increase in concern-relative representation failures.

This result is interpreted within the dTAS exemplar and is not presented as a
universal causal law for self-adaptive systems.

---

## 13.9 EQ3-B outputs

The final evaluator writes:

```text
raise2/results/dtas-eq3-b-final-results.json
raise2/results/dtas-eq3-b-condition-summary.tsv
raise2/results/dtas-eq3-b-run-summary.tsv
```

The frozen result hashes are documented in `ARTIFACTS.md`.

---

# 14. EQ3 reproduction paths

## 14.1 Verify frozen EQ3 results

No Java re-execution is required.

Run:

```bash
python -m raise2.evaluator.evaluate_dtas_eq3
python -m raise2.evaluator.evaluate_dtas_eq3b
```

Both should report:

```text
INTEGRITY CHECK: PASS
```

The repository-wide semantic check is:

```bash
python -m raise2.validation.validate_results
```

## 14.2 Rebuild the Java harnesses and controlled conditions

Without executing the stochastic dTAS runs:

```bash
python -m raise2.experiments.build_dtas_eq3
python -m raise2.experiments.build_dtas_eq3b
```

The source hashes and EQ3-B manifest should match the values documented above.

## 14.3 Full EQ3 replication

From a clean replication workspace with Java 8 available:

```bash
python -m raise2.experiments.build_dtas_eq3
python -m raise2.experiments.run_dtas_eq3
python -m raise2.evaluator.evaluate_dtas_eq3

python -m raise2.experiments.build_dtas_eq3b
python -m raise2.experiments.run_dtas_eq3b
python -m raise2.evaluator.evaluate_dtas_eq3b
```

The dTAS service-failure behaviour is stochastic.

A new full execution is therefore not expected to reproduce every cycle-level
value byte-for-byte.

Replication should compare the resulting concern-relative adequacy patterns,
condition-level distributions, and run-level statistical results with the
frozen evidence in `RESULTS.md`.

---

# 15. End-to-end frozen-evidence verification

For reviewers who want to verify the published evidence without generating new
LLM responses or new dTAS stochastic runs, the compact verification procedure
is:

```bash
python -m raise2.evaluator.audit_eq1
python -m raise2.evaluator.aggregate_poi_conformance
python -m raise2.evaluator.extract_eq1_crds
python -m raise2.evaluator.match_eq1_references
python -m raise2.evaluator.evaluate_eq1

python -m raise2.evaluator.evaluate_eq2

python -m raise2.evaluator.evaluate_dtas_eq3
python -m raise2.evaluator.evaluate_dtas_eq3b

python -m raise2.validation.validate_results
```

Finally verify byte-level package integrity with:

```bash
sha256sum -c SHA256SUMS
```

The expected final semantic-validation result is:

```text
Checks passed: 80/80
Checks failed: 0
FROZEN RESULTS VALIDATION: PASS
```

The detailed aggregate results are reported in `RESULTS.md`, while provenance
and integrity information are documented in `ARTIFACTS.md`.

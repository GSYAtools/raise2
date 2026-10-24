# RAISE² Experimental Artefacts and Provenance

This document describes the provenance, role, and integrity model of the
artefacts preserved in the RAISE² evaluation repository.

It complements:

- `README.md`, which provides the repository overview;
- `RESULTS.md`, which indexes the frozen experimental results; and
- `REPLICATION.md`, which provides the reproduction procedure.

The repository distinguishes external upstream artefacts, frozen experimental
inputs, generated experimental artefacts, frozen outputs, and integrity
manifests.

---

# 1. Integrity model

SHA-256 is used to identify artefacts that were frozen during the experimental
process.

The repository contains two levels of integrity information.

## 1.1 Historical manifests

Several directories contain local `SHA256SUMS.txt` files created when
particular experimental stages were frozen.

These manifests are preserved because they document the state of the
corresponding artefacts at that point in the experimental process.

Examples include:

```text
mobstr/work/development/H2/coding/SHA256SUMS.txt
mobstr/work/development/H5/coding/SHA256SUMS.txt
mobstr/work/frozen-protocol/SHA256SUMS.txt
mobstr/work/test-visible/SHA256SUMS.txt
mobstr/work/reference/coder1/SHA256SUMS.txt
mobstr/work/raise2-output/H1/coding/SHA256SUMS.txt
mobstr/work/raise2-output/H3/coding/SHA256SUMS.txt
dtas/original/SHA256SUMS.txt
```

These historical manifests are not replaced by the final repository-level
manifest.

## 1.2 Repository-level manifest

The repository root contains:

```text
SHA256SUMS
```

This manifest provides a single integrity index over the selected experimental
and documentation artefacts required to inspect and reproduce the reported
evaluation.

The root manifest intentionally does not hash every extracted upstream source
file, generated Java class, Python cache, or temporary execution artefact.

Instead, it covers the preserved upstream archives and the experimental
artefacts that define or support the reported evaluation.

The root manifest should be regenerated only when the public replication
package itself is intentionally changed.

---

# 2. Artefact classes

The package distinguishes five classes of artefacts.

## 2.1 Upstream artefacts

External datasets and software distributions obtained from their original
sources.

## 2.2 Frozen experimental inputs

Artefacts fixed before the corresponding experimental execution, including
protocols, schemas, visible evidence, reference evidence, baselines, and
controlled changes.

## 2.3 Generated experimental artefacts

Artefacts deterministically generated from frozen inputs, such as controlled
dTAS configurations and lifecycle-change scenarios.

## 2.4 Raw and aggregated experimental outputs

Outputs produced by experimental executions and the deterministic evaluators
that aggregate them.

## 2.5 Documentation and validation artefacts

Documentation and executable checks connecting the repository contents to the
reported results.

---

# 3. MobSTr upstream provenance

MobSTr is used for EQ1 and EQ2.

The preserved upstream archive is:

```text
mobstr/original/mobstr-dataset-2021-06.zip
```

Its SHA-256 digest is:

```text
3e4a7f2558fddec12d4896316a884f29e68ae71738cb860bcdd3915bd1ddfd91
```

The checksum is recorded in:

```text
mobstr/original/SHA256SUMS.txt
```

and can be verified with:

```bash
cd mobstr/original
sha256sum -c SHA256SUMS.txt
```

The extracted upstream material is retained under:

```text
mobstr/original/extracted/
```

The upstream distribution includes its own README, licence, contributor
information, and installation documentation.

---

# 4. MobSTr development/evaluation separation

The MobSTr experimental material is divided explicitly between development and
evaluation.

## 4.1 Development concerns

The development cases are:

```text
mobstr/work/development/H2/
mobstr/work/development/H5/
```

These concerns were used while developing and refining the derivation and
coding procedure.

Their historical coding artefacts and manifests are retained for provenance.

They are not treated as independent evaluation cases in EQ1.

## 4.2 Evaluation concerns

The independent EQ1 evaluation uses:

```text
H1
H3
```

The evidence visible during derivation is stored separately under:

```text
mobstr/work/test-visible/H1/
mobstr/work/test-visible/H3/
```

This separation prevents reference material from being silently incorporated
into the derivation input.

---

# 5. MobSTr test-visible evidence

The frozen test-visible material contains, for each evaluation concern:

- the concern/hazard description;
- selected requirements; and
- architecture material.

The main files are:

```text
mobstr/work/test-visible/H1/hazard.txt
mobstr/work/test-visible/H1/requirements.tsv
mobstr/work/test-visible/H1/architecture/mobstr-architecture.pdf
mobstr/work/test-visible/H1/architecture/mobstr-architecture.uml

mobstr/work/test-visible/H3/hazard.txt
mobstr/work/test-visible/H3/requirements.tsv
mobstr/work/test-visible/H3/architecture/mobstr-architecture.pdf
mobstr/work/test-visible/H3/architecture/mobstr-architecture.uml
```

The selection procedure is documented in:

```text
mobstr/work/test-visible/SELECTION-PROTOCOL.txt
```

The local integrity manifest is:

```text
mobstr/work/test-visible/SHA256SUMS.txt
```

---

# 6. Frozen MobSTr coding protocol

The coding procedure developed using H2 and H5 was frozen before the H1/H3
evaluation.

The frozen protocol is stored under:

```text
mobstr/work/frozen-protocol/
```

It contains:

```text
coding-protocol.tsv
development-record.txt
matching-rules.tsv
reference-coding.tsv
unmatched-derived-rules.tsv
FROZEN-AT.txt
SHA256SUMS.txt
```

These artefacts record the transition from protocol development to independent
evaluation.

---

# 7. Independent reference artefacts

The independently prepared reference distinctions used in EQ1 are stored
under:

```text
mobstr/work/reference/coder1/
```

The principal reference files are:

```text
mobstr/work/reference/coder1/H1/reference-crds.tsv
mobstr/work/reference/coder1/H3/reference-crds.tsv
```

Their frozen SHA-256 digests are:

```text
c017dc77125a911a134c7fc81d55b8b6fbe792da5b214a4bf548804fb945837a
mobstr/work/reference/coder1/H1/reference-crds.tsv
```

```text
4af72bbed52c30cef2116ae30edceae34dd5ade50ff39682c73f843506c8d58d
mobstr/work/reference/coder1/H3/reference-crds.tsv
```

The directory also contains:

```text
CODER-STATUS.txt
FROZEN-AT.txt
SHA256SUMS.txt
```

Reference matching and adjudication are separate evaluation stages and are not
performed implicitly by the derivation executor.

---

# 8. RAISE² protocols and schemas

The execution and evaluation protocols are stored under:

```text
raise2/protocol/
```

The principal protocols are:

```text
raise2/protocol/rr-protocol.txt
raise2/protocol/poi-conformance-protocol.txt
raise2/protocol/rv-protocol.txt
```

Structured-output contracts are stored under:

```text
raise2/schemas/
```

and include:

```text
raise2/schemas/derivation.schema.json
raise2/schemas/experiment.schema.json
raise2/schemas/poi-conformance.schema.json
raise2/schemas/rv-result.schema.json
```

The schemas constrain machine-generated experimental outputs before
deterministic evaluation.

---

# 9. EQ1 experimental artefacts

The frozen EQ1 design is:

```text
raise2/experiments/mobstr/EQ1-DESIGN.txt
```

The reference-matching procedure is:

```text
raise2/experiments/mobstr/EQ1-REFERENCE-MATCHING.txt
```

The PoI-conformance design is:

```text
raise2/experiments/mobstr/POI-CONFORMANCE-DESIGN.txt
```

Concern-specific experiment definitions are:

```text
raise2/experiments/mobstr/H1.json
raise2/experiments/mobstr/H3.json
```

The deterministic final adjudication used by the evaluation is:

```text
raise2/evaluation/mobstr/reference-adjudication.tsv
```

The final machine-readable EQ1 results are indexed in `RESULTS.md`.

---

# 10. Frozen RAISE² representation specifications

The representation specifications used as the basis for lifecycle
revalidation are preserved under:

```text
mobstr/work/raise2-output/H1/coding/
mobstr/work/raise2-output/H3/coding/
```

Each directory contains the derivation context, CRD derivation record, final
CRDs, Observable Representation Requirements, adjudication information,
provenance information, and a local SHA-256 manifest.

The H1 specification is the basis of the EQ2 revalidation experiment.

---

# 11. EQ2 baseline and controlled changes

The frozen H1 revalidation baseline is:

```text
mobstr/work/revalidation/H1/baseline.json
```

Its frozen SHA-256 digest is:

```text
e7e53a8058e7da0a0d22bc43c6dd38e629e704897b701239597302e777cc9965
```

The six controlled changes are:

```text
mobstr/work/revalidation/H1/changes/delta-01.json
mobstr/work/revalidation/H1/changes/delta-02.json
mobstr/work/revalidation/H1/changes/delta-03.json
mobstr/work/revalidation/H1/changes/delta-04.json
mobstr/work/revalidation/H1/changes/delta-05.json
mobstr/work/revalidation/H1/changes/delta-06.json
```

The frozen ground truth is:

```text
raise2/evaluation/mobstr/eq2-ground-truth.json
```

Its SHA-256 digest at freeze time was:

```text
480a3957d341f7a87f2afec2862cb0b5bc8c28c663a3c73ec725d1291fe5d9c8
```

The scenarios were generated before the EQ2 model executions.

---

# 12. dTAS upstream provenance

dTAS v1.0 is used for EQ3.

The preserved upstream archives are:

```text
dtas/original/dtas-v1.0-source.zip
dtas/original/dtas-paper-results.zip
```

Their SHA-256 digests are:

```text
155b2f935bd21d43631a4d7cf0c5801e323d8ba872b8f112139401996e84c522
dtas-v1.0-source.zip
```

```text
9dae192ac21336c9c0474b6c4c26cb4e0594cd60fafc518c55bbad8bfc72df77
dtas-paper-results.zip
```

They are recorded in:

```text
dtas/original/SHA256SUMS.txt
```

and can be verified with:

```bash
cd dtas/original
sha256sum -c SHA256SUMS.txt
```

The source distribution is extracted under:

```text
dtas/work/source/
```

The paper-result archive is extracted under:

```text
dtas/work/paper-results/
```

The preserved ZIP archives, rather than every extracted file, are the upstream
integrity roots.

---

# 13. EQ3-A harness

The EQ3-A experiment uses a headless Java harness:

```text
dtas/work/eq3-harness/DTASEQ3Harness.java
```

Its frozen SHA-256 digest is:

```text
c84f3652738de5b96fdb7dd47a6ed37e648824f77ba8830429c17e51c6d8692f
```

A minimal JavaFX compatibility shim is stored at:

```text
dtas/work/eq3-harness/shim-src/javafx/util/Pair.java
```

with frozen digest:

```text
d08fcb8c575ea64ad5e170c490bbcbcdd752bc543836d19df503f9320a7220b0
```

The shim provides the Java 8-compatible `javafx.util.Pair` API required by the
original compiled dTAS classes.

It does not implement or replace dTAS adaptation behaviour.

A smoke-test harness is also preserved:

```text
dtas/work/eq3-harness/DTASSmoke.java
```

---

# 14. EQ3-B controlled conditions

The EQ3-B intervention is generated automatically by:

```text
raise2/experiments/build_dtas_eq3b.py
```

The builder was frozen with SHA-256:

```text
0e737c8bf292b68512d91dd5e73a1272a233796d439f123213976c78428d34a3
```

The generated EQ3-B workspace contains:

```text
dtas/work/eq3-b/conditions.json
dtas/work/eq3-b/conditions/mfd-0005.xml
dtas/work/eq3-b/conditions/mfd-0010.xml
dtas/work/eq3-b/conditions/mfd-0020.xml
dtas/work/eq3-b/conditions/mfd-0040.xml
dtas/work/eq3-b/DTASEQ3BHarness.java
dtas/work/eq3-b/manifest.json
```

The generated manifest was frozen with SHA-256:

```text
f4d18ecf2240240e79b3218dd68ed8f9b1d8fe47c7f78cedaa1c470febed260b
```

The four frozen `MonitorMinFailureDelta` conditions are:

```text
0.005
0.010
0.020
0.040
```

`MonitorFailureChange` remains fixed at:

```text
0.005
```

The baseline `0.005` condition reuses the first 10 already frozen EQ3-A runs
rather than generating a second baseline after inspecting EQ3-A.

---

# 15. Frozen result artefacts

The final aggregate result artefacts are stored under:

```text
raise2/results/
```

## 15.1 EQ1

```text
raise2/results/mobstr-eq1-final-results.json
raise2/results/mobstr-eq1-final-results.tsv
raise2/results/mobstr-eq1-poi-conformance.json
raise2/results/mobstr-eq1-audit.json
```

## 15.2 EQ2

```text
raise2/results/mobstr-eq2-final-results.json
raise2/results/mobstr-eq2-final-results.tsv
raise2/results/mobstr-eq2-scenario-summary.tsv
```

## 15.3 EQ3-A

```text
raise2/results/dtas-eq3-a-final-results.json
raise2/results/dtas-eq3-a-run-summary.tsv
raise2/results/dtas-eq3-a-cycle-results.tsv
```

The frozen EQ3-A result hashes are:

```text
6987cde89c39aa7ce120b47089e1819efdff8b6497a47a068d1571bceb4a54ae
dtas-eq3-a-final-results.json

e8b2a666a7ae42b9486706c0434f1cf63dafe41ef407c1efd82507cfdda1232e
dtas-eq3-a-run-summary.tsv

330060b9b4e59c15fa6d4ad186ab02e5e5a99a5c0ddf3dbf159eb9fa7c72aa33
dtas-eq3-a-cycle-results.tsv
```

## 15.4 EQ3-B

```text
raise2/results/dtas-eq3-b-final-results.json
raise2/results/dtas-eq3-b-condition-summary.tsv
raise2/results/dtas-eq3-b-run-summary.tsv
```

The frozen EQ3-B result hashes are:

```text
9728ca286265e77fd5728623a0283136f347bc2c703eba7bca01e62bf31647ae
dtas-eq3-b-final-results.json

92ccc9588afdeca9fe5510df1f80fcb3c789a16aa077e4abaa64c9e40160bd5d
dtas-eq3-b-condition-summary.tsv

5709915a53855d2f2d5f13428c48fd62ad81b632399905667dbd89dbca34cce0
dtas-eq3-b-run-summary.tsv
```

---

# 16. Executable result validation

The repository contains a permanent semantic validator:

```text
raise2/validation/validate_results.py
```

It verifies the principal frozen values reported in `RESULTS.md` directly
against the machine-readable JSON artefacts.

Run:

```bash
python -m raise2.validation.validate_results
```

At preparation time, the validator reported:

```text
Checks passed: 80/80
Checks failed: 0
FROZEN RESULTS VALIDATION: PASS
```

This check is distinct from SHA-256 integrity verification.

SHA-256 verifies that artefact bytes have not changed.

The semantic validator verifies that the principal reported experimental
values are consistent with the frozen machine-readable results.

---

# 17. Verifying repository integrity

The final public replication package contains a repository-level:

```text
SHA256SUMS
```

After the final documentation and public-package artefact set have been
frozen, verify the manifest from the repository root with:

```bash
sha256sum -c SHA256SUMS
```

The historical local manifests remain available for inspection of earlier
freeze points.

---

# 18. Provenance chain

The principal provenance chain of the evaluation is:

```text
upstream exemplars
        |
        v
development cases and protocol refinement
        |
        v
frozen protocols and evaluation inputs
        |
        v
independent experimental executions
        |
        v
ground truth / adjudication
        |
        v
deterministic evaluators
        |
        v
machine-readable frozen results
        |
        v
RESULTS.md
        |
        v
paper
```

For dTAS EQ3-B, an additional deterministic generation step occurs between the
upstream exemplar and experimental execution:

```text
original dTAS configuration
        |
        v
frozen EQ3-B builder
        |
        v
controlled condition XML files
        |
        v
independent dTAS runs
        |
        v
deterministic evaluation
```

---

# 19. Preservation policy

Frozen experimental artefacts should not be edited in place after the
corresponding results have been inspected.

A future extension of the evaluation should create new experiment identifiers,
new artefacts, and new result namespaces rather than silently replacing the
artefacts documented here.

Documentation corrections that do not change experimental evidence should be
committed separately and should result in a new repository-level
`SHA256SUMS` manifest for the revised public replication package.

---

# 20. EQ3-A reproducible build artefacts

During preparation of the public replication package, the original manual
EQ3-A Java compilation procedure was encapsulated in a deterministic builder:

```text
raise2/experiments/build_dtas_eq3.py
```

The builder does not modify dTAS behaviour or the frozen experimental results.

It automates the compilation steps required before executing the already
documented EQ3-A harness:

1. verify the required original dTAS classes and libraries;
2. compile the Java 8-compatible `javafx.util.Pair` shim;
3. compile the frozen EQ3-A harness source; and
4. record source and compiled-artifact hashes.

Run:

```bash
python -m raise2.experiments.build_dtas_eq3
```

The builder generates:

```text
dtas/work/eq3-harness/manifest.json
```

The manifest identifies the frozen source artefacts and the locally compiled
classes.

The frozen source hashes are:

```text
c84f3652738de5b96fdb7dd47a6ed37e648824f77ba8830429c17e51c6d8692f
dtas/work/eq3-harness/DTASEQ3Harness.java
```

and:

```text
d08fcb8c575ea64ad5e170c490bbcbcdd752bc543836d19df503f9320a7220b0
dtas/work/eq3-harness/shim-src/javafx/util/Pair.java
```

Rebuilding the harness during preparation of the replication package confirmed
that both source hashes match the previously frozen EQ3-A sources.

In the reference Java 8 environment, the resulting compiled-artifact hashes
recorded in the generated manifest were:

```text
020145faf4539f45756a49b20b3c0a9bde652d3a88a6ccdf4c06139ff6f6677f
dtas/work/eq3-harness/DTASEQ3Harness.class
```

and:

```text
d28171566376b4b756dfbdd43b5a6af7e1ec1b40b3141b9ec6378ba71c37ba2f
dtas/work/eq3-harness/shim-bin/javafx/util/Pair.class
```

The compiled-class hashes document the reference build but are not assumed to
be portable across arbitrary Java compiler implementations.

The source hashes are the stable integrity identifiers for the experimental
harness implementation.

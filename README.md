# RAISE² Evaluation and Replication Package

This repository contains the experimental artefacts, executable evaluation
code, and results used to evaluate RAISE².

RAISE² is a concern-driven method for deriving and maintaining requirements
on the observable representations used to evaluate software systems. Rather
than treating representation quality as a generic property such as numerical
accuracy, RAISE² asks which distinctions must be preserved in order to
evaluate a specific engineering concern.

The repository accompanies the RAISE² research paper and is intended to make
the experimental evidence independently inspectable and reproducible.

## Evaluation structure

The evaluation comprises three complementary evaluation questions.

### EQ1 — Concern-relative derivation

EQ1 studies the derivation of concern-relevant distinctions and representation
requirements from engineering artefacts.

The evaluation uses the MobSTr exemplar and separates development concerns
(H2 and H5) from evaluation concerns (H1 and H3). The evaluation includes
repeated independent derivations, Phenomenon-of-Interest (PoI) conformance
assessment, and comparison against independently prepared reference
distinctions.

EQ1 exposes the extent to which initial representation-requirement derivation
depends on semantic engineering judgement.

### EQ2 — Lifecycle revalidation

EQ2 studies what happens after a RAISE² representation specification has been
established.

Starting from a frozen H1 representation baseline, six controlled lifecycle
changes are introduced. The evaluation tests whether each change can be
classified as requiring:

- no representation action (`NONE`);
- revalidation of existing Observable Representation Requirements
  (`REVALIDATE`); or
- return to an earlier RAISE² derivation step (`REDERIVE`).

The experiment also evaluates localisation to affected representation
requirements and, for re-derivation, localisation to the appropriate return
point.

### EQ3 — Runtime representational adequacy

EQ3 operationalises a RAISE² representation requirement in the dTAS v1.0
self-adaptive-system exemplar.

The original dTAS reliability goal distinguishes:

```text
SATISFIED: failure rate < 0.19
VIOLATED:  failure rate >= 0.19
```

The corresponding representation requirement is preserved when the failure
rate represented internally by the adaptive system remains on the same side
of this concern-relevant boundary as the actual operational failure rate.

EQ3 has two phases:

- **EQ3-A** observes representational adequacy under the original dTAS
  configuration.
- **EQ3-B** introduces controlled degradation by varying the native
  `MonitorMinFailureDelta` parameter while keeping the remaining experimental
  condition fixed.

## Systems used

### MobSTr

MobSTr is used for EQ1 and EQ2.

The repository preserves the original downloaded MobSTr dataset separately
from the artefacts prepared for development and evaluation.

The experimental structure distinguishes:

- development cases (`H2`, `H5`);
- evaluation cases (`H1`, `H3`);
- test-visible evidence;
- reference evidence;
- frozen coding and matching protocols; and
- lifecycle-revalidation artefacts.

### dTAS

dTAS v1.0 is used for EQ3.

The exemplar accompanies:

J. Van De Sijpe and D. Weyns,
“dTAS: A Decentralized Self-Adaptive Service-Based System Exemplar,”
2020 IEEE International Conference on Autonomic Computing and Self-Organizing
Systems Companion (ACSOS-C), pp. 224–225, 2020.

DOI: `10.1109/ACSOS-C51401.2020.00060`

The original dTAS source and paper-results archives are preserved unchanged
under `dtas/original/`.

## Repository layout

```text
raise2-evaluation/
|
|-- raise2/
|   |-- executor/       RAISE² execution code
|   |-- evaluator/      deterministic evaluators and aggregators
|   |-- experiments/    experiment designs, builders, and runners
|   |-- protocol/       frozen execution and assessment protocols
|   |-- schemas/        structured-output schemas
|   |-- evaluation/     ground truth and adjudication artefacts
|   |-- results/        aggregated and machine-readable results
|   `-- tests/          infrastructure and validation tests
|
|-- mobstr/
|   |-- original/       preserved upstream MobSTr material
|   `-- work/           development and evaluation artefacts
|
`-- dtas/
    |-- original/       preserved upstream dTAS archives
    `-- work/
        |-- source/         extracted dTAS source distribution
        |-- paper-results/  original dTAS paper-result artefacts
        |-- eq3-harness/    EQ3-A headless experimental harness
        `-- eq3-b/          generated EQ3-B conditions and manifest
```

## Main frozen results

The principal machine-readable result artefacts are:

### EQ1

```text
raise2/results/mobstr-eq1-final-results.json
raise2/results/mobstr-eq1-final-results.tsv
raise2/results/mobstr-eq1-poi-conformance.json
raise2/results/mobstr-eq1-audit.json
```

### EQ2

```text
raise2/results/mobstr-eq2-final-results.json
raise2/results/mobstr-eq2-final-results.tsv
raise2/results/mobstr-eq2-scenario-summary.tsv
```

### EQ3-A

```text
raise2/results/dtas-eq3-a-final-results.json
raise2/results/dtas-eq3-a-run-summary.tsv
raise2/results/dtas-eq3-a-cycle-results.tsv
```

### EQ3-B

```text
raise2/results/dtas-eq3-b-final-results.json
raise2/results/dtas-eq3-b-condition-summary.tsv
raise2/results/dtas-eq3-b-run-summary.tsv
```

## Reproducibility principles

The experimental package follows four principles.

### Frozen artefacts

Experimental designs, protocols, schemas, reference artefacts, controlled
changes, and final results were frozen during the evaluation. SHA-256 hashes
are used to identify relevant artefacts.

### Separation of development and evaluation

MobSTr H2 and H5 were used during method and protocol development. H1 and H3
were subsequently used for evaluation.

Reference evidence used for evaluation was kept separate from the
test-visible artefacts used during derivation.

### Raw execution versus deterministic evaluation

LLM-based execution and deterministic evaluation are separate stages.

Preserved experimental outputs can therefore be re-evaluated without making
new LLM API calls.

### Experimental-unit awareness

Repeated cycles within a dTAS execution are not treated as independent
experimental replicates.

For EQ3-B, statistical comparisons use the independent dTAS run as the
resampling unit.

## Reproducing the experiments

Detailed prerequisites, provenance information, execution commands, integrity
checks, and evaluation procedures are documented in:

`REPLICATION.md`

A compact mapping from reported results to machine-readable artefacts is
provided in:

`RESULTS.md`

Integrity and provenance information is provided in:

`ARTIFACTS.md`

## Important interpretation

The evaluation does not support a claim of fully autonomous end-to-end
representation-requirement derivation.

Instead, the combined evidence distinguishes three stages:

1. initial concern-relative derivation is sensitive to semantic engineering
   judgement;
2. once a representation specification is established, lifecycle
   revalidation is substantially more reproducible; and
3. operationalised representation requirements can identify runtime loss of
   concern-relevant information that is not characterised by numerical
   approximation error alone.

This staged interpretation is the one supported by the frozen experimental
evidence in this repository.

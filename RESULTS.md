# RAISE² Experimental Results

This document provides the compact result index for the frozen RAISE²
evaluation.

Its purpose is to connect the results reported in the accompanying paper with
the machine-readable artefacts preserved in this repository.

The detailed experimental procedure is documented separately in
`REPLICATION.md`.

---

## 1. Evaluation overview

The evaluation comprises three complementary evaluation questions.

| Evaluation | System | Purpose |
|---|---|---|
| EQ1 | MobSTr | Evaluate concern-relative derivation and its sensitivity to semantic engineering judgement |
| EQ2 | MobSTr | Evaluate lifecycle revalidation after a representation specification has been established |
| EQ3-A | dTAS | Evaluate concern-relative representational adequacy during natural runtime behaviour |
| EQ3-B | dTAS | Evaluate the effect of controlled degradation of representation-update sensitivity |

The experiments should be interpreted jointly. They do not test the same
property of RAISE².

---

# 2. EQ1 — Concern-relative derivation and reproducibility

EQ1 evaluates two complementary properties of RAISE² derivation:

1. whether a controlled engineering application of the method can derive
   concern-relevant distinctions from upstream evidence that are subsequently
   supported by independent held-out evidence; and
2. how reproducibly the same derivation procedure can be executed autonomously.

The evaluation uses two held-out MobSTr concerns:

- `H1`
- `H3`

Development concerns H2 and H5 were used exclusively during protocol
development.

## 2.1 Frozen expert derivation and independent support

Before the repeated automated executions, RAISE² was applied to H1 and H3 using
only the frozen test-visible hazard, requirements, and architecture evidence.
Both expert derivations were frozen before the held-out downstream evidence
was used to construct the independent reference distinctions.

The frozen H1 derivation contains:

| CRD | Evaluation dimension |
|---|---|
| H1-CRD1 | Obstacle presence |
| H1-CRD2 | Object category |
| H1-CRD3 | Obstacle distance relative to braking need |

The frozen H3 derivation contains:

| CRD | Evaluation dimension |
|---|---|
| H3-CRD1 | Obstacle presence |
| H3-CRD2 | Obstacle distance relative to braking justification |

Independent downstream evidence establishes two reference distinctions for each
concern. Comparison with the frozen expert derivations gives:

| Reference | Frozen expert CRD | Recovery |
|---|---|---:|
| H1-REF1 — Obstacle presence | H1-CRD1 | Recovered |
| H1-REF2 — Braking-relevant spatial relation | H1-CRD3 | Recovered |
| H3-REF1 — Obstacle presence | H3-CRD1 | Recovered |
| H3-REF2 — Braking-relevant spatial relation | H3-CRD2 | Recovered |

Thus, the controlled expert application recovered all four independently
established reference distinctions (`4/4`). H1-CRD2 additionally preserves an
object-category distinction supported directly by the upstream requirements but
not represented as a downstream reference distinction.

The frozen expert specifications are preserved under:

```text
mobstr/work/raise2-output/H1/coding/
mobstr/work/raise2-output/H3/coding/
```

and the independent reference distinctions under:

```text
mobstr/work/reference/coder1/H1/reference-crds.tsv
mobstr/work/reference/coder1/H3/reference-crds.tsv
```

## 2.2 Reproducibility under automated execution

After establishing the frozen expert derivations, the derivation protocol was
executed autonomously 30 times for each held-out concern:

```text
30 H1 derivations
30 H3 derivations
60 derivations total
```

The resulting CRDs were evaluated in two complementary ways:

1. conformance of the derived Phenomenon of Interest (PoI); and
2. recovery of the independently prepared reference distinctions.

### PoI conformance

The final PoI-conformance aggregation classified the 60 automated derivations
as follows.

| Concern | ALIGNED | OVEREXTENDED | UNDERDETERMINED |
|---|---:|---:|---:|
| H1 | 22/30 | 8/30 | 0/30 |
| H3 | 30/30 | 0/30 | 0/30 |

H3 therefore produced a PoI aligned with the intended evaluation scope in all
30 runs. H1 produced 22 aligned and 8 overextended PoIs. No derivation was
classified as underdetermined.

Machine-readable artefact:

```text
raise2/results/mobstr-eq1-poi-conformance.json
```

### Reference recovery

Reference recovery varied across the repeated automated derivations.

| Reference | All runs | PoI-aligned runs |
|---|---:|---:|
| H1-REF1 | 9/30 (30.0%) | 5/22 (22.7%) |
| H1-REF2 | 5/30 (16.7%) | 3/22 (13.6%) |
| H3-REF1 | 23/30 (76.7%) | 23/30 (76.7%) |
| H3-REF2 | 0/30 (0.0%) | 0/30 (0.0%) |

Complete recovery requires both reference distinctions for a concern to be
recovered within the same automated derivation.

| Concern | All runs | PoI-aligned runs |
|---|---:|---:|
| H1 | 3/30 (10.0%) | 2/22 (9.1%) |
| H3 | 0/30 (0.0%) | 0/30 (0.0%) |

Machine-readable artefacts:

```text
raise2/results/mobstr-eq1-final-results.json
raise2/results/mobstr-eq1-final-results.tsv
```

## 2.3 EQ1 interpretation

The two stages distinguish method derivability from autonomous execution
reproducibility. The frozen expert application recovered all four reference
distinctions subsequently supported by independent downstream evidence, while
the repeated automated executions did not reproduce those distinctions
uniformly.

The automated results expose a semantic engineering boundary. PoI definition
can be stable for a comparatively explicit concern, as observed for H3, while
becoming sensitive to scope interpretation for a more complex concern, as
observed for H1. Distinction elicitation is more judgement-sensitive, with
reference recovery varying substantially across distinctions.

EQ1 therefore does not support replacing engineering judgement with end-to-end
autonomous derivation. It shows instead that RAISE² can structure a derivation
whose representational decisions are independently assessable, while autonomous
execution of that procedure remains sensitive to semantic engineering
judgement.

---

# 3. EQ2 — Lifecycle revalidation

EQ2 evaluates whether RAISE² can reason about controlled lifecycle changes
after a concern-relative representation specification has been established.

A frozen H1 baseline was subjected to six controlled change scenarios.

Each scenario was independently evaluated 10 times, producing:

```text
6 scenarios x 10 runs = 60 runs
```

All 60 runs passed the final integrity check.

## 3.1 Global lifecycle results

| Metric | Correct | Total | Accuracy |
|---|---:|---:|---:|
| Lifecycle decision | 55 | 60 | 91.7% |
| Exact lifecycle outcome | 55 | 60 | 91.7% |
| Affected-ORR set | 25 | 30 | 83.3% |
| Re-derivation return point | 20 | 20 | 100.0% |

The decision confusion matrix was:

| Expected / Actual | NONE | REVALIDATE | REDERIVE |
|---|---:|---:|---:|
| NONE | 10 | 0 | 0 |
| REVALIDATE | 0 | 25 | 5 |
| REDERIVE | 0 | 0 | 20 |

No `NONE` scenario was incorrectly escalated.

No `REDERIVE` scenario was incorrectly classified as either `NONE` or
`REVALIDATE`.

All five lifecycle-decision errors occurred in one `REVALIDATE` scenario.

## 3.2 Scenario-level results

| Scenario | Expected decision | Expected localisation | Exact outcome | Distinct outcomes |
|---|---|---|---:|---:|
| delta-01 | NONE | — | 10/10 | 1 |
| delta-02 | REVALIDATE | H1-ORR1 | 10/10 | 1 |
| delta-03 | REVALIDATE | H1-ORR2 | 10/10 | 1 |
| delta-04 | REVALIDATE | H1-ORR3 | 5/10 | 2 |
| delta-05 | REDERIVE | RR2 | 10/10 | 1 |
| delta-06 | REDERIVE | RR1 | 10/10 | 1 |

`delta-04` was the only non-fully-reproducible scenario.

For this scenario, the 10 decisions split evenly:

```text
REVALIDATE: 5
REDERIVE:   5
```

When classified as `REDERIVE`, the returned derivation point was `RR3`.

## 3.3 Token usage

The 60 EQ2 executions consumed:

| Measure | Tokens |
|---|---:|
| Input tokens | 165,210 |
| Output tokens | 9,866 |
| Total | 175,076 |
| Mean input/run | 2,753.5 |
| Mean output/run | 164.43 |

## 3.4 EQ2 interpretation

Once the representation specification has been established, lifecycle
reasoning is substantially more reproducible than initial derivation.

The strongest result is re-derivation localisation: all 20 scenarios requiring
re-derivation returned to the expected derivation point.

The observed ambiguity is concentrated in `delta-04`, at the boundary between
revalidating an existing distinction and redefining the distinction itself.

Machine-readable artefacts:

```text
raise2/results/mobstr-eq2-final-results.json
raise2/results/mobstr-eq2-final-results.tsv
raise2/results/mobstr-eq2-scenario-summary.tsv
```

---

# 4. EQ3-A — Natural runtime representational adequacy

EQ3-A evaluates the original dTAS v1.0 configuration without introducing
controlled degradation.

The experiment contains:

```text
30 independent runs
20 adaptation cycles per run
600 cycle-level observations
```

The concern-relevant boundary is the original dTAS reliability threshold:

```text
SATISFIED: failure rate < 0.19
VIOLATED:  failure rate >= 0.19
```

For each cycle, the operationalised ORR is preserved when the actual and
represented failure rates lie on the same side of this boundary.

## 4.1 Concern-relative adequacy

| Metric | Result |
|---|---:|
| ORR preserved | 570/600 (95.0%) |
| ORR violations | 30/600 (5.0%) |
| Runs containing at least one violation | 27/30 (90.0%) |

Although only 5.0% of cycle-level observations violated the ORR, at least one
violation occurred in 90.0% of independent runs.

## 4.2 Direction of the violations

All observed violations had the same direction.

| Violation type | Count |
|---|---:|
| MISSED_VIOLATION | 30 |
| FALSE_VIOLATION | 0 |

There were 30 cycles in which the actual reliability goal was violated.

All 30 were represented internally as satisfied:

```text
Missed-violation rate = 30/30 = 100.0%
```

There were 570 cycles in which the actual goal was satisfied.

None was incorrectly represented as violated:

```text
False-violation rate = 0/570 = 0.0%
```

## 4.3 Numerical error versus representational adequacy

EQ3-A also evaluates whether numerical approximation error alone can determine
concern-relative adequacy.

For ORR-preserved observations:

| Statistic | Absolute error |
|---|---:|
| n | 570 |
| Median | 0.0037471 |
| Mean | 0.0096059 |
| Maximum | 0.0841697 |

For ORR-violating observations:

| Statistic | Absolute error |
|---|---:|
| n | 30 |
| Minimum | 0.0080199 |
| Median | 0.0449184 |
| Mean | 0.0463493 |
| Maximum | 0.0784179 |

A direct accuracy/adequacy inversion was observed.

The largest numerical error for an adequate representation was:

```text
run-021, cycle 1
absolute error = 0.08416973824
actual state = SATISFIED
represented state = SATISFIED
```

The smallest numerical error for an inadequate representation was:

```text
run-002, cycle 4
absolute error = 0.00801987110
actual state = VIOLATED
represented state = SATISFIED
```

Therefore:

```text
0.08416973824 > 0.00801987110
```

yet the first observation preserves the concern-relevant distinction and the
second does not.

The frozen evaluator additionally identified:

```text
110 preserved observations with error larger than at least one violation
30 violations with error smaller than at least one preserved observation
```

Thus, within this experiment, numerical error magnitude is not sufficient to
determine concern-relative representational adequacy.

## 4.4 Temporal distribution

ORR violations were not confined to the first adaptation cycle.

They occurred in cycles:

```text
1, 2, 3, 4, 5, 7, 9, 10, 11, 12, 15, 18, 20
```

The highest counts occurred at:

| Cycle | Violations |
|---:|---:|
| 1 | 4/30 |
| 2 | 6/30 |
| 3 | 3/30 |
| 4 | 3/30 |
| 10 | 5/30 |

The phenomenon therefore cannot be reduced solely to an initialisation effect.

Machine-readable artefacts:

```text
raise2/results/dtas-eq3-a-final-results.json
raise2/results/dtas-eq3-a-run-summary.tsv
raise2/results/dtas-eq3-a-cycle-results.tsv
```

---

# 5. EQ3-B — Controlled representation degradation

EQ3-B evaluates whether concern-relative representational failures respond to
a controlled degradation of the native dTAS representation-update mechanism.

The manipulated parameter is:

```text
MonitorMinFailureDelta
```

The controlled parameter is:

```text
MonitorFailureChange = 0.005
```

Four conditions were frozen before the degraded conditions were executed:

```text
0.005
0.010
0.020
0.040
```

Each condition contains 10 independent runs and 20 cycles per run.

The experimental unit used for inferential comparison is the independent run,
not the individual adaptation cycle.

## 5.1 Baseline reuse

The `mfd-0005` condition reuses runs `run-001` through `run-010` from the
already frozen EQ3-A experiment.

It is therefore a 10-run subset of EQ3-A, not a second execution of the
baseline and not the complete 30-run EQ3-A dataset.

Consequently:

- EQ3-A reports 30 violations over 600 observations;
- the EQ3-B baseline reports 13 violations over the 200 observations contained
  in the first 10 frozen EQ3-A runs.

This reuse avoids generating a second stochastic baseline after the EQ3-A
results had already been observed.

## 5.2 Condition results

| MinFailureDelta | ORR violations | Runs affected | Mean violations/run | Mean abs. error/run |
|---:|---:|---:|---:|---:|
| 0.005 | 13/200 (6.5%) | 10/10 (100%) | 1.3 | 0.011665 |
| 0.010 | 24/200 (12.0%) | 9/10 (90%) | 2.4 | 0.017419 |
| 0.020 | 25/200 (12.5%) | 9/10 (90%) | 2.5 | 0.034519 |
| 0.040 | 31/200 (15.5%) | 10/10 (100%) | 3.1 | 0.058202 |

Across the four frozen conditions, mean ORR violations per run followed:

```text
1.3 -> 2.4 -> 2.5 -> 3.1
```

The frozen evaluator classifies this trend as:

```text
non-decreasing:     true
strictly increasing: true
```

## 5.3 Violation direction

All 93 ORR violations observed across EQ3-B were:

```text
MISSED_VIOLATION
```

No `FALSE_VIOLATION` occurred in any condition.

| MinFailureDelta | Missed | False |
|---:|---:|---:|
| 0.005 | 13 | 0 |
| 0.010 | 24 | 0 |
| 0.020 | 25 | 0 |
| 0.040 | 31 | 0 |

## 5.4 Run-level bootstrap comparison

Bootstrap comparison uses:

```text
10,000 bootstrap replicates
fixed seed = 20261024
resampling unit = independent run
```

Differences below are:

```text
condition mean - baseline mean
```

### ORR violations per run

| Condition | Difference vs baseline | 95% bootstrap CI |
|---:|---:|---:|
| 0.010 | +1.1 | [0.3, 1.8] |
| 0.020 | +1.2 | [0.3, 2.1] |
| 0.040 | +1.8 | [1.3, 2.3] |

### Mean absolute error per run

| Condition | Difference vs baseline | 95% bootstrap CI |
|---:|---:|---:|
| 0.010 | +0.005753 | [0.004394, 0.007100] |
| 0.020 | +0.022853 | [0.021285, 0.024485] |
| 0.040 | +0.046536 | [0.045641, 0.047487] |

All three bootstrap intervals for the increase in ORR violations per run lie
above zero.

## 5.5 EQ3-B interpretation

Within this controlled dTAS experiment, decreasing the sensitivity with which
the monitor updates its internal failure-rate representation is associated
with a systematic increase in concern-relative representational failures.

The experiment does not establish a universal causal law for adaptive
systems. It provides controlled evidence within the dTAS exemplar that a
degradation of the representation-update mechanism increases the frequency
with which the internal representation fails to preserve the distinction
required by the reliability concern.

Machine-readable artefacts:

```text
raise2/results/dtas-eq3-b-final-results.json
raise2/results/dtas-eq3-b-condition-summary.tsv
raise2/results/dtas-eq3-b-run-summary.tsv
```

---

# 6. Combined interpretation

The three evaluation stages support different conclusions.

## 6.1 Initial derivation remains judgement-sensitive

EQ1 shows that initial concern-relative derivation cannot be characterised as
fully autonomous or mechanically reproducible.

The definition of the phenomenon and the selection of concern-relevant
distinctions remain sensitive to semantic engineering judgement.

## 6.2 Lifecycle reasoning is more reproducible after specification

EQ2 shows substantially stronger reproducibility once the representation
specification has been established.

The system correctly classified and localised most controlled lifecycle
changes, including perfect return-point localisation for the 20 re-derivation
cases.

## 6.3 Runtime adequacy is concern-relative

EQ3 shows that an operationalised representation requirement can identify
runtime loss of information specifically relevant to an engineering concern.

The accuracy/adequacy inversion observed in EQ3-A demonstrates that numerical
approximation error and concern-relative adequacy are not equivalent.

EQ3-B further shows that controlled degradation of a native representation
update mechanism systematically increases the frequency of these
concern-relative failures.

---

# 7. Evidence supported by the evaluation

Taken together, the frozen experiments support the following staged
interpretation of RAISE²:

```text
engineering concern
        |
        v
concern-relevant distinctions
        |
        v
representation obligations
        |
        v
lifecycle dependencies
        |
        v
runtime representational adequacy
```

The empirical evidence does not support replacing engineering judgement with
end-to-end autonomous derivation.

Instead, it supports using explicit concern-relative representation
requirements to make that judgement traceable, maintainable, and
operationally testable.

---

# 8. Source-of-truth artefacts

The JSON files are the primary machine-readable aggregate result artefacts.

```text
raise2/results/mobstr-eq1-final-results.json
raise2/results/mobstr-eq2-final-results.json
raise2/results/dtas-eq3-a-final-results.json
raise2/results/dtas-eq3-b-final-results.json
```

The corresponding TSV files provide tabular views suitable for independent
inspection and secondary analysis.

Experimental procedures, frozen inputs, ground truth, adjudication,
provenance, and reproduction commands are documented separately in
`REPLICATION.md` and `ARTIFACTS.md`.

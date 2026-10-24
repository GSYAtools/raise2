import csv
import json
import math
import random
import statistics
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

RESULTS_ROOT = (
    PROJECT_ROOT
    / "raise2/results/dtas-eq3-b"
)

MANIFEST_PATH = (
    PROJECT_ROOT
    / "dtas/work/eq3-b/manifest.json"
)

OUTPUT_JSON = (
    PROJECT_ROOT
    / "raise2/results/dtas-eq3-b-final-results.json"
)

OUTPUT_TSV = (
    PROJECT_ROOT
    / "raise2/results/dtas-eq3-b-condition-summary.tsv"
)

RUN_OUTPUT_TSV = (
    PROJECT_ROOT
    / "raise2/results/dtas-eq3-b-run-summary.tsv"
)

CONDITIONS = [
    ("mfd-0005", 0.005),
    ("mfd-0010", 0.010),
    ("mfd-0020", 0.020),
    ("mfd-0040", 0.040),
]

BASELINE = "mfd-0005"

RUNS_PER_CONDITION = 10
CYCLES_PER_RUN = 20
EXPECTED_THRESHOLD = 0.19

BOOTSTRAP_REPLICATES = 10000
BOOTSTRAP_SEED = 20261024


def load_json(path):
    with path.open(
        encoding="utf-8"
    ) as f:
        return json.load(f)


def load_csv(path):
    with path.open(
        encoding="utf-8",
        newline="",
    ) as f:
        return list(
            csv.DictReader(f)
        )


def percentile(values, q):
    values = sorted(values)

    if not values:
        return None

    if len(values) == 1:
        return values[0]

    position = (
        (len(values) - 1) * q
    )

    low = math.floor(position)
    high = math.ceil(position)

    if low == high:
        return values[low]

    weight = position - low

    return (
        values[low] * (1 - weight)
        + values[high] * weight
    )


def describe(values):
    if not values:
        return {
            "n": 0,
            "min": None,
            "median": None,
            "mean": None,
            "max": None,
        }

    return {
        "n": len(values),
        "min": min(values),
        "median":
            statistics.median(values),
        "mean":
            statistics.mean(values),
        "max": max(values),
    }


def bootstrap_mean_difference(
    baseline_values,
    condition_values,
    rng,
):
    """
    Difference:
        condition mean - baseline mean

    Resampling unit:
        independent run
    """

    differences = []

    n_base = len(
        baseline_values
    )

    n_cond = len(
        condition_values
    )

    for _ in range(
        BOOTSTRAP_REPLICATES
    ):

        base_sample = [
            baseline_values[
                rng.randrange(n_base)
            ]
            for _ in range(n_base)
        ]

        cond_sample = [
            condition_values[
                rng.randrange(n_cond)
            ]
            for _ in range(n_cond)
        ]

        differences.append(
            statistics.mean(
                cond_sample
            )
            - statistics.mean(
                base_sample
            )
        )

    return {
        "observed_difference":
            statistics.mean(
                condition_values
            )
            - statistics.mean(
                baseline_values
            ),

        "ci95_low":
            percentile(
                differences,
                0.025,
            ),

        "ci95_high":
            percentile(
                differences,
                0.975,
            ),
    }


def main():

    manifest = load_json(
        MANIFEST_PATH
    )

    if (
        manifest.get("study")
        != "dTAS EQ3-B"
    ):
        raise ValueError(
            "Unexpected EQ3-B manifest."
        )

    integrity_errors = []

    cycle_records = []
    run_records = []

    # --------------------------------------------------
    # Ingest and independently validate all 800 cycles
    # --------------------------------------------------

    for (
        condition_id,
        min_failure_delta,
    ) in CONDITIONS:

        for number in range(
            1,
            RUNS_PER_CONDITION + 1,
        ):

            run_id = (
                f"run-{number:03d}"
            )

            path = (
                RESULTS_ROOT
                / condition_id
                / run_id
                / "observations.csv"
            )

            if not path.is_file():
                integrity_errors.append(
                    f"{condition_id}/"
                    f"{run_id}: missing CSV"
                )
                continue

            rows = load_csv(path)

            if (
                len(rows)
                != CYCLES_PER_RUN
            ):
                integrity_errors.append(
                    f"{condition_id}/"
                    f"{run_id}: "
                    f"{len(rows)} cycles"
                )
                continue

            run_violations = 0
            run_missed = 0
            run_false = 0
            run_errors = []

            for expected_cycle, row in enumerate(
                rows,
                start=1,
            ):

                try:
                    cycle = int(
                        row["cycle"]
                    )

                    real = float(
                        row[
                            "real_failure_rate"
                        ]
                    )

                    represented = float(
                        row[
                            "represented_failure_rate"
                        ]
                    )

                    stored_error = float(
                        row[
                            "absolute_error"
                        ]
                    )

                    threshold = float(
                        row["threshold"]
                    )

                except Exception as exc:
                    integrity_errors.append(
                        f"{condition_id}/"
                        f"{run_id}: "
                        f"invalid row: {exc}"
                    )
                    continue

                if (
                    row["run_id"]
                    != run_id
                ):
                    integrity_errors.append(
                        f"{condition_id}/"
                        f"{run_id}: "
                        "run_id mismatch"
                    )

                if (
                    cycle
                    != expected_cycle
                ):
                    integrity_errors.append(
                        f"{condition_id}/"
                        f"{run_id}: "
                        "cycle mismatch"
                    )

                if (
                    abs(
                        threshold
                        - EXPECTED_THRESHOLD
                    )
                    > 1e-12
                ):
                    integrity_errors.append(
                        f"{condition_id}/"
                        f"{run_id}/"
                        f"{cycle}: "
                        "threshold mismatch"
                    )

                error = abs(
                    real - represented
                )

                if (
                    abs(
                        error
                        - stored_error
                    )
                    > 1e-12
                ):
                    integrity_errors.append(
                        f"{condition_id}/"
                        f"{run_id}/"
                        f"{cycle}: "
                        "error mismatch"
                    )

                real_state = (
                    "SATISFIED"
                    if real < threshold
                    else "VIOLATED"
                )

                represented_state = (
                    "SATISFIED"
                    if represented
                    < threshold
                    else "VIOLATED"
                )

                preserved = (
                    real_state
                    == represented_state
                )

                if preserved:
                    violation_type = (
                        "NONE"
                    )

                elif (
                    real_state
                    == "VIOLATED"
                    and represented_state
                    == "SATISFIED"
                ):
                    violation_type = (
                        "MISSED_VIOLATION"
                    )

                else:
                    violation_type = (
                        "FALSE_VIOLATION"
                    )

                if (
                    row["real_goal_state"]
                    != real_state
                    or row[
                        "represented_goal_state"
                    ]
                    != represented_state
                    or (
                        row["orr_preserved"]
                        == "true"
                    )
                    != preserved
                    or row[
                        "violation_type"
                    ]
                    != violation_type
                ):
                    integrity_errors.append(
                        f"{condition_id}/"
                        f"{run_id}/"
                        f"{cycle}: "
                        "semantic mismatch"
                    )

                if not preserved:
                    run_violations += 1

                if (
                    violation_type
                    == "MISSED_VIOLATION"
                ):
                    run_missed += 1

                if (
                    violation_type
                    == "FALSE_VIOLATION"
                ):
                    run_false += 1

                run_errors.append(
                    error
                )

                cycle_records.append(
                    {
                        "condition_id":
                            condition_id,
                        "min_failure_delta":
                            min_failure_delta,
                        "run_id":
                            run_id,
                        "cycle":
                            cycle,
                        "real_failure_rate":
                            real,
                        "represented_failure_rate":
                            represented,
                        "absolute_error":
                            error,
                        "real_goal_state":
                            real_state,
                        "represented_goal_state":
                            represented_state,
                        "orr_preserved":
                            preserved,
                        "violation_type":
                            violation_type,
                    }
                )

            run_records.append(
                {
                    "condition_id":
                        condition_id,
                    "min_failure_delta":
                        min_failure_delta,
                    "run_id":
                        run_id,
                    "orr_violations":
                        run_violations,
                    "missed_violations":
                        run_missed,
                    "false_violations":
                        run_false,
                    "has_violation":
                        run_violations > 0,
                    "mean_absolute_error":
                        statistics.mean(
                            run_errors
                        ),
                    "max_absolute_error":
                        max(run_errors),
                }
            )

    # --------------------------------------------------
    # Integrity gate
    # --------------------------------------------------

    if integrity_errors:

        print("=" * 70)
        print(
            "dTAS EQ3-B EVALUATION"
        )
        print("=" * 70)

        print()
        print(
            "INTEGRITY CHECK: FAIL"
        )

        for error in integrity_errors:
            print(
                f"- {error}"
            )

        raise SystemExit(1)

    expected_cycles = (
        len(CONDITIONS)
        * RUNS_PER_CONDITION
        * CYCLES_PER_RUN
    )

    if (
        len(cycle_records)
        != expected_cycles
    ):
        raise ValueError(
            "Expected "
            f"{expected_cycles} "
            "cycle records, found "
            f"{len(cycle_records)}"
        )

    # --------------------------------------------------
    # Condition summaries
    # --------------------------------------------------

    summaries = []

    for (
        condition_id,
        min_failure_delta,
    ) in CONDITIONS:

        cycles = [
            row
            for row in cycle_records
            if row[
                "condition_id"
            ]
            == condition_id
        ]

        runs = [
            row
            for row in run_records
            if row[
                "condition_id"
            ]
            == condition_id
        ]

        violations = [
            row
            for row in cycles
            if not row[
                "orr_preserved"
            ]
        ]

        missed = [
            row
            for row in cycles
            if row[
                "violation_type"
            ]
            == "MISSED_VIOLATION"
        ]

        false = [
            row
            for row in cycles
            if row[
                "violation_type"
            ]
            == "FALSE_VIOLATION"
        ]

        real_violated = [
            row
            for row in cycles
            if row[
                "real_goal_state"
            ]
            == "VIOLATED"
        ]

        real_satisfied = [
            row
            for row in cycles
            if row[
                "real_goal_state"
            ]
            == "SATISFIED"
        ]

        runs_with_violation = sum(
            row["has_violation"]
            for row in runs
        )

        summaries.append(
            {
                "condition_id":
                    condition_id,
                "min_failure_delta":
                    min_failure_delta,
                "runs":
                    len(runs),
                "cycles":
                    len(cycles),

                "orr_violations":
                    len(violations),
                "cycle_violation_rate":
                    (
                        len(violations)
                        / len(cycles)
                    ),

                "runs_with_violation":
                    runs_with_violation,
                "run_incidence":
                    (
                        runs_with_violation
                        / len(runs)
                    ),

                "missed_violations":
                    len(missed),
                "false_violations":
                    len(false),

                "real_violated_cycles":
                    len(real_violated),

                "missed_violation_rate":
                    (
                        len(missed)
                        / len(real_violated)
                        if real_violated
                        else None
                    ),

                "false_violation_rate":
                    (
                        len(false)
                        / len(real_satisfied)
                        if real_satisfied
                        else None
                    ),

                "violations_per_run":
                    describe(
                        [
                            row[
                                "orr_violations"
                            ]
                            for row in runs
                        ]
                    ),

                "mean_absolute_error_per_run":
                    describe(
                        [
                            row[
                                "mean_absolute_error"
                            ]
                            for row in runs
                        ]
                    ),
            }
        )

    # --------------------------------------------------
    # Run-level bootstrap against baseline
    # --------------------------------------------------

    rng = random.Random(
        BOOTSTRAP_SEED
    )

    baseline_runs = [
        row
        for row in run_records
        if row[
            "condition_id"
        ]
        == BASELINE
    ]

    comparisons = []

    for (
        condition_id,
        min_failure_delta,
    ) in CONDITIONS[1:]:

        condition_runs = [
            row
            for row in run_records
            if row[
                "condition_id"
            ]
            == condition_id
        ]

        violation_comparison = (
            bootstrap_mean_difference(
                [
                    row[
                        "orr_violations"
                    ]
                    for row
                    in baseline_runs
                ],
                [
                    row[
                        "orr_violations"
                    ]
                    for row
                    in condition_runs
                ],
                rng,
            )
        )

        error_comparison = (
            bootstrap_mean_difference(
                [
                    row[
                        "mean_absolute_error"
                    ]
                    for row
                    in baseline_runs
                ],
                [
                    row[
                        "mean_absolute_error"
                    ]
                    for row
                    in condition_runs
                ],
                rng,
            )
        )

        comparisons.append(
            {
                "condition_id":
                    condition_id,
                "min_failure_delta":
                    min_failure_delta,
                "vs_baseline":
                    BASELINE,
                "orr_violations_per_run":
                    violation_comparison,
                "mean_absolute_error_per_run":
                    error_comparison,
            }
        )

    # --------------------------------------------------
    # Monotonic descriptive trend
    # --------------------------------------------------

    mean_violations = [
        summary[
            "violations_per_run"
        ]["mean"]
        for summary in summaries
    ]

    nondecreasing = all(
        mean_violations[i]
        <= mean_violations[i + 1]
        for i in range(
            len(mean_violations) - 1
        )
    )

    strictly_increasing = all(
        mean_violations[i]
        < mean_violations[i + 1]
        for i in range(
            len(mean_violations) - 1
        )
    )

    # --------------------------------------------------
    # Output
    # --------------------------------------------------

    results = {
        "study":
            "dTAS EQ3-B",

        "experimental_unit":
            "independent run",

        "conditions":
            summaries,

        "baseline_comparisons":
            comparisons,

        "trend": {
            "mean_orr_violations_per_run":
                mean_violations,
            "nondecreasing":
                nondecreasing,
            "strictly_increasing":
                strictly_increasing,
        },

        "bootstrap": {
            "replicates":
                BOOTSTRAP_REPLICATES,
            "seed":
                BOOTSTRAP_SEED,
            "resampling_unit":
                "run",
        },

        "run_records":
            run_records,
    }

    with OUTPUT_JSON.open(
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            results,
            f,
            indent=2,
            ensure_ascii=False,
        )

        f.write("\n")

    # --------------------------------------------------
    # Condition TSV
    # --------------------------------------------------

    with OUTPUT_TSV.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as f:

        fieldnames = [
            "condition_id",
            "min_failure_delta",
            "runs",
            "cycles",
            "orr_violations",
            "cycle_violation_rate",
            "runs_with_violation",
            "run_incidence",
            "missed_violations",
            "false_violations",
            "real_violated_cycles",
            "missed_violation_rate",
            "false_violation_rate",
        ]

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
            delimiter="\t",
        )

        writer.writeheader()

        for summary in summaries:
            writer.writerow(
                {
                    key:
                        summary.get(key)
                    for key
                    in fieldnames
                }
            )

    # --------------------------------------------------
    # Run TSV
    # --------------------------------------------------

    with RUN_OUTPUT_TSV.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as f:

        fieldnames = [
            "condition_id",
            "min_failure_delta",
            "run_id",
            "orr_violations",
            "missed_violations",
            "false_violations",
            "has_violation",
            "mean_absolute_error",
            "max_absolute_error",
        ]

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
            delimiter="\t",
        )

        writer.writeheader()
        writer.writerows(
            run_records
        )

    # --------------------------------------------------
    # Console
    # --------------------------------------------------

    print("=" * 70)
    print(
        "dTAS EQ3-B FINAL RESULTS"
    )
    print("=" * 70)

    print()
    print(
        "INTEGRITY CHECK: PASS"
    )

    print(
        "Experimental unit: "
        "independent run"
    )

    print(
        f"Runs:   "
        f"{len(run_records)}/40"
    )

    print(
        f"Cycles: "
        f"{len(cycle_records)}/800"
    )

    print()
    print("Condition results")
    print()

    for summary in summaries:

        print(
            f"{summary['condition_id']} "
            f"(MinFailureDelta="
            f"{summary['min_failure_delta']})"
        )

        print(
            "  ORR violations: "
            f"{summary['orr_violations']}/"
            f"{summary['cycles']} "
            f"("
            f"{100 * summary['cycle_violation_rate']:.1f}%"
            f")"
        )

        print(
            "  Runs affected:  "
            f"{summary['runs_with_violation']}/"
            f"{summary['runs']} "
            f"("
            f"{100 * summary['run_incidence']:.1f}%"
            f")"
        )

        print(
            "  Mean violations/run: "
            f"{summary['violations_per_run']['mean']:.3f}"
        )

        print(
            "  Missed violations: "
            f"{summary['missed_violations']}"
        )

        print(
            "  False violations:  "
            f"{summary['false_violations']}"
        )

        print(
            "  Mean abs. error/run: "
            f"{summary['mean_absolute_error_per_run']['mean']:.6f}"
        )

        print()

    print(
        "Run-level comparisons "
        "against baseline"
    )
    print()

    for comparison in comparisons:

        v = comparison[
            "orr_violations_per_run"
        ]

        e = comparison[
            "mean_absolute_error_per_run"
        ]

        print(
            comparison[
                "condition_id"
            ]
        )

        print(
            "  Delta violations/run: "
            f"{v['observed_difference']:.3f} "
            f"[95% bootstrap CI "
            f"{v['ci95_low']:.3f}, "
            f"{v['ci95_high']:.3f}]"
        )

        print(
            "  Delta mean error/run: "
            f"{e['observed_difference']:.6f} "
            f"[95% bootstrap CI "
            f"{e['ci95_low']:.6f}, "
            f"{e['ci95_high']:.6f}]"
        )

        print()

    print("Trend")
    print()

    print(
        "Mean ORR violations/run: "
        + " -> ".join(
            f"{value:.3f}"
            for value
            in mean_violations
        )
    )

    print(
        "Non-decreasing: "
        f"{nondecreasing}"
    )

    print(
        "Strictly increasing: "
        f"{strictly_increasing}"
    )

    print()
    print(
        f"JSON written to: "
        f"{OUTPUT_JSON}"
    )

    print(
        f"Condition TSV: "
        f"{OUTPUT_TSV}"
    )

    print(
        f"Run TSV: "
        f"{RUN_OUTPUT_TSV}"
    )


if __name__ == "__main__":
    main()

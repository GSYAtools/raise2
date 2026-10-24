import csv
import json
import math
import statistics
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

RESULTS_ROOT = (
    PROJECT_ROOT
    / "raise2/results/dtas-eq3-a"
)

OUTPUT_JSON = (
    PROJECT_ROOT
    / "raise2/results/dtas-eq3-a-final-results.json"
)

OUTPUT_RUN_TSV = (
    PROJECT_ROOT
    / "raise2/results/dtas-eq3-a-run-summary.tsv"
)

OUTPUT_CYCLE_TSV = (
    PROJECT_ROOT
    / "raise2/results/dtas-eq3-a-cycle-results.tsv"
)

EXPECTED_RUNS = 30
EXPECTED_CYCLES_PER_RUN = 20
EXPECTED_THRESHOLD = 0.19


def load_csv(path):
    with path.open(
        encoding="utf-8",
        newline="",
    ) as f:
        return list(csv.DictReader(f))


def percentile(values, q):
    if not values:
        return None

    values = sorted(values)

    if len(values) == 1:
        return values[0]

    position = (
        (len(values) - 1)
        * q
    )

    lower = math.floor(position)
    upper = math.ceil(position)

    if lower == upper:
        return values[lower]

    weight = position - lower

    return (
        values[lower]
        * (1 - weight)
        + values[upper]
        * weight
    )


def describe(values):
    if not values:
        return {
            "n": 0,
            "min": None,
            "q1": None,
            "median": None,
            "mean": None,
            "q3": None,
            "max": None,
        }

    return {
        "n": len(values),
        "min": min(values),
        "q1": percentile(
            values,
            0.25,
        ),
        "median": statistics.median(
            values
        ),
        "mean": statistics.mean(
            values
        ),
        "q3": percentile(
            values,
            0.75,
        ),
        "max": max(values),
    }


def fmt_rate(
    numerator,
    denominator,
):
    if denominator == 0:
        return "n/a"

    return (
        f"{numerator}/{denominator} "
        f"({100 * numerator / denominator:.1f}%)"
    )


def main():

    # --------------------------------------------------
    # Integrity and ingestion
    # --------------------------------------------------

    integrity_errors = []
    cycle_records = []
    run_records = []

    for number in range(
        1,
        EXPECTED_RUNS + 1,
    ):

        run_id = (
            f"run-{number:03d}"
        )

        csv_path = (
            RESULTS_ROOT
            / run_id
            / "observations.csv"
        )

        if not csv_path.is_file():
            integrity_errors.append(
                f"{run_id}: "
                "missing observations.csv"
            )
            continue

        rows = load_csv(
            csv_path
        )

        if (
            len(rows)
            != EXPECTED_CYCLES_PER_RUN
        ):
            integrity_errors.append(
                f"{run_id}: expected "
                f"{EXPECTED_CYCLES_PER_RUN} "
                f"cycles, found {len(rows)}"
            )
            continue

        try:
            cycles = [
                int(row["cycle"])
                for row in rows
            ]
        except Exception as exc:
            integrity_errors.append(
                f"{run_id}: invalid cycle "
                f"values: {exc}"
            )
            continue

        if cycles != list(
            range(
                1,
                EXPECTED_CYCLES_PER_RUN
                + 1,
            )
        ):
            integrity_errors.append(
                f"{run_id}: cycle sequence "
                "is not 1..20"
            )
            continue

        run_violation_count = 0
        run_missed = 0
        run_false = 0
        run_errors = []

        for row in rows:

            if row["run_id"] != run_id:
                integrity_errors.append(
                    f"{run_id}: row run_id "
                    "mismatch"
                )
                continue

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

                error = float(
                    row[
                        "absolute_error"
                    ]
                )

                threshold = float(
                    row["threshold"]
                )

            except Exception as exc:
                integrity_errors.append(
                    f"{run_id}: invalid "
                    f"numeric data: {exc}"
                )
                continue

            if (
                abs(
                    threshold
                    - EXPECTED_THRESHOLD
                )
                > 1e-12
            ):
                integrity_errors.append(
                    f"{run_id}/{cycle}: "
                    "unexpected threshold"
                )

            expected_error = abs(
                real - represented
            )

            if (
                abs(
                    expected_error
                    - error
                )
                > 1e-12
            ):
                integrity_errors.append(
                    f"{run_id}/{cycle}: "
                    "absolute error mismatch"
                )

            real_state = (
                "SATISFIED"
                if real < threshold
                else "VIOLATED"
            )

            represented_state = (
                "SATISFIED"
                if represented < threshold
                else "VIOLATED"
            )

            if (
                row["real_goal_state"]
                != real_state
            ):
                integrity_errors.append(
                    f"{run_id}/{cycle}: "
                    "real state mismatch"
                )

            if (
                row[
                    "represented_goal_state"
                ]
                != represented_state
            ):
                integrity_errors.append(
                    f"{run_id}/{cycle}: "
                    "represented state mismatch"
                )

            preserved = (
                real_state
                == represented_state
            )

            stored_preserved = (
                row["orr_preserved"]
                == "true"
            )

            if (
                preserved
                != stored_preserved
            ):
                integrity_errors.append(
                    f"{run_id}/{cycle}: "
                    "ORR preservation mismatch"
                )

            if preserved:
                expected_type = "NONE"
            elif (
                real_state == "VIOLATED"
                and represented_state
                == "SATISFIED"
            ):
                expected_type = (
                    "MISSED_VIOLATION"
                )
            else:
                expected_type = (
                    "FALSE_VIOLATION"
                )

            if (
                row["violation_type"]
                != expected_type
            ):
                integrity_errors.append(
                    f"{run_id}/{cycle}: "
                    "violation type mismatch"
                )

            if not preserved:
                run_violation_count += 1

            if (
                expected_type
                == "MISSED_VIOLATION"
            ):
                run_missed += 1

            if (
                expected_type
                == "FALSE_VIOLATION"
            ):
                run_false += 1

            run_errors.append(
                error
            )

            cycle_records.append(
                {
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
                    "threshold":
                        threshold,
                    "real_goal_state":
                        real_state,
                    "represented_goal_state":
                        represented_state,
                    "orr_preserved":
                        preserved,
                    "violation_type":
                        expected_type,
                }
            )

        run_records.append(
            {
                "run_id":
                    run_id,
                "cycles":
                    len(rows),
                "orr_violations":
                    run_violation_count,
                "missed_violations":
                    run_missed,
                "false_violations":
                    run_false,
                "has_violation":
                    (
                        run_violation_count
                        > 0
                    ),
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
        print("dTAS EQ3-A EVALUATION")
        print("=" * 70)
        print()
        print(
            "INTEGRITY CHECK: FAIL"
        )

        for error in (
            integrity_errors
        ):
            print(
                f"- {error}"
            )

        raise SystemExit(1)

    expected_observations = (
        EXPECTED_RUNS
        * EXPECTED_CYCLES_PER_RUN
    )

    if (
        len(cycle_records)
        != expected_observations
    ):
        raise ValueError(
            "Expected "
            f"{expected_observations} "
            "cycle observations, found "
            f"{len(cycle_records)}"
        )

    # --------------------------------------------------
    # Global counts
    # --------------------------------------------------

    violations = [
        row
        for row in cycle_records
        if not row[
            "orr_preserved"
        ]
    ]

    preserved = [
        row
        for row in cycle_records
        if row[
            "orr_preserved"
        ]
    ]

    missed = [
        row
        for row in cycle_records
        if row[
            "violation_type"
        ]
        == "MISSED_VIOLATION"
    ]

    false = [
        row
        for row in cycle_records
        if row[
            "violation_type"
        ]
        == "FALSE_VIOLATION"
    ]

    runs_with_violation = [
        row
        for row in run_records
        if row[
            "has_violation"
        ]
    ]

    # --------------------------------------------------
    # Conditional denominators
    # --------------------------------------------------

    real_violated = [
        row
        for row in cycle_records
        if row[
            "real_goal_state"
        ]
        == "VIOLATED"
    ]

    real_satisfied = [
        row
        for row in cycle_records
        if row[
            "real_goal_state"
        ]
        == "SATISFIED"
    ]

    # Missed violation:
    #
    # P(represented SATISFIED |
    #   real VIOLATED)
    #
    missed_rate = (
        len(missed)
        / len(real_violated)
        if real_violated
        else None
    )

    # False violation:
    #
    # P(represented VIOLATED |
    #   real SATISFIED)
    #
    false_rate = (
        len(false)
        / len(real_satisfied)
        if real_satisfied
        else None
    )

    # --------------------------------------------------
    # Error distributions
    # --------------------------------------------------

    all_errors = [
        row["absolute_error"]
        for row in cycle_records
    ]

    preserved_errors = [
        row["absolute_error"]
        for row in preserved
    ]

    violation_errors = [
        row["absolute_error"]
        for row in violations
    ]

    missed_errors = [
        row["absolute_error"]
        for row in missed
    ]

    false_errors = [
        row["absolute_error"]
        for row in false
    ]

    # --------------------------------------------------
    # Accuracy vs adequacy counterexamples
    # --------------------------------------------------

    max_violation_error = (
        max(violation_errors)
        if violation_errors
        else None
    )

    min_violation_error = (
        min(violation_errors)
        if violation_errors
        else None
    )

    preserved_larger_than_some_violation = []

    violations_smaller_than_some_preserved = []

    if violation_errors:

        for row in preserved:

            if (
                row["absolute_error"]
                > min_violation_error
            ):
                preserved_larger_than_some_violation.append(
                    row
                )

        max_preserved_error = max(
            preserved_errors
        )

        for row in violations:

            if (
                row["absolute_error"]
                < max_preserved_error
            ):
                violations_smaller_than_some_preserved.append(
                    row
                )

    else:
        max_preserved_error = (
            max(preserved_errors)
            if preserved_errors
            else None
        )

    # Strongest illustrative pair:
    #
    # preserved observation with maximum
    # error versus violated observation
    # with minimum error.
    #
    strongest_preserved = (
        max(
            preserved,
            key=lambda row:
                row["absolute_error"],
        )
        if preserved
        else None
    )

    strongest_violation = (
        min(
            violations,
            key=lambda row:
                row["absolute_error"],
        )
        if violations
        else None
    )

    inversion_exists = (
        strongest_preserved
        is not None
        and strongest_violation
        is not None
        and strongest_preserved[
            "absolute_error"
        ]
        > strongest_violation[
            "absolute_error"
        ]
    )

    # --------------------------------------------------
    # Temporal distribution
    # --------------------------------------------------

    violations_by_cycle = Counter(
        row["cycle"]
        for row in violations
    )

    missed_by_cycle = Counter(
        row["cycle"]
        for row in missed
    )

    false_by_cycle = Counter(
        row["cycle"]
        for row in false
    )

    temporal = []

    for cycle in range(
        1,
        EXPECTED_CYCLES_PER_RUN
        + 1,
    ):

        cycle_rows = [
            row
            for row in cycle_records
            if row["cycle"] == cycle
        ]

        temporal.append(
            {
                "cycle":
                    cycle,
                "observations":
                    len(cycle_rows),
                "orr_violations":
                    violations_by_cycle[
                        cycle
                    ],
                "missed_violations":
                    missed_by_cycle[
                        cycle
                    ],
                "false_violations":
                    false_by_cycle[
                        cycle
                    ],
                "mean_absolute_error":
                    statistics.mean(
                        row[
                            "absolute_error"
                        ]
                        for row
                        in cycle_rows
                    ),
            }
        )

    # --------------------------------------------------
    # Final structured results
    # --------------------------------------------------

    results = {
        "study":
            "dTAS EQ3-A",
        "runs":
            EXPECTED_RUNS,
        "cycles_per_run":
            EXPECTED_CYCLES_PER_RUN,
        "observations":
            len(cycle_records),
        "threshold":
            EXPECTED_THRESHOLD,

        "orr_adequacy": {
            "violations":
                len(violations),
            "preserved":
                len(preserved),
            "violation_rate":
                (
                    len(violations)
                    / len(cycle_records)
                ),
            "runs_with_violation":
                len(
                    runs_with_violation
                ),
            "run_incidence":
                (
                    len(
                        runs_with_violation
                    )
                    / EXPECTED_RUNS
                ),
        },

        "violation_types": {
            "missed_violations":
                len(missed),
            "false_violations":
                len(false),
            "real_violated_cycles":
                len(real_violated),
            "real_satisfied_cycles":
                len(real_satisfied),
            "missed_violation_rate":
                missed_rate,
            "false_violation_rate":
                false_rate,
        },

        "absolute_error": {
            "all":
                describe(
                    all_errors
                ),
            "orr_preserved":
                describe(
                    preserved_errors
                ),
            "orr_violated":
                describe(
                    violation_errors
                ),
            "missed_violation":
                describe(
                    missed_errors
                ),
            "false_violation":
                describe(
                    false_errors
                ),
        },

        "accuracy_adequacy_relation": {
            "inversion_exists":
                inversion_exists,
            "preserved_observations_with_error_larger_than_some_violation":
                len(
                    preserved_larger_than_some_violation
                ),
            "violations_with_error_smaller_than_some_preserved_observation":
                len(
                    violations_smaller_than_some_preserved
                ),
            "maximum_preserved_error_observation":
                strongest_preserved,
            "minimum_violation_error_observation":
                strongest_violation,
        },

        "temporal_distribution":
            temporal,

        "run_summary":
            run_records,
    }

    # --------------------------------------------------
    # Write JSON
    # --------------------------------------------------

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
    # Write run-level TSV
    # --------------------------------------------------

    with OUTPUT_RUN_TSV.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as f:

        fieldnames = [
            "run_id",
            "cycles",
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
    # Write cycle-level TSV
    # --------------------------------------------------

    with OUTPUT_CYCLE_TSV.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as f:

        fieldnames = [
            "run_id",
            "cycle",
            "real_failure_rate",
            "represented_failure_rate",
            "absolute_error",
            "threshold",
            "real_goal_state",
            "represented_goal_state",
            "orr_preserved",
            "violation_type",
        ]

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
            delimiter="\t",
        )

        writer.writeheader()
        writer.writerows(
            cycle_records
        )

    # --------------------------------------------------
    # Console report
    # --------------------------------------------------

    print("=" * 70)
    print(
        "dTAS EQ3-A FINAL RESULTS"
    )
    print("=" * 70)

    print()
    print(
        "INTEGRITY CHECK: PASS"
    )

    print(
        f"Runs:         "
        f"{EXPECTED_RUNS}/"
        f"{EXPECTED_RUNS}"
    )

    print(
        "Observations: "
        f"{len(cycle_records)}/"
        f"{expected_observations}"
    )

    print()
    print("Concern-relative adequacy")
    print()

    print(
        "ORR violations: "
        + fmt_rate(
            len(violations),
            len(cycle_records),
        )
    )

    print(
        "Runs with >=1 violation: "
        + fmt_rate(
            len(
                runs_with_violation
            ),
            EXPECTED_RUNS,
        )
    )

    print()
    print("Violation types")
    print()

    print(
        "Missed violations: "
        f"{len(missed)}"
    )

    print(
        "False violations:  "
        f"{len(false)}"
    )

    if real_violated:
        print(
            "Missed-violation rate: "
            + fmt_rate(
                len(missed),
                len(real_violated),
            )
        )
    else:
        print(
            "Missed-violation rate: n/a"
        )

    if real_satisfied:
        print(
            "False-violation rate:  "
            + fmt_rate(
                len(false),
                len(real_satisfied),
            )
        )
    else:
        print(
            "False-violation rate: n/a"
        )

    print()
    print(
        "Absolute representation error"
    )
    print()

    p = describe(
        preserved_errors
    )

    v = describe(
        violation_errors
    )

    print(
        "ORR preserved:"
    )
    print(
        f"  n={p['n']}, "
        f"median={p['median']}, "
        f"mean={p['mean']}, "
        f"max={p['max']}"
    )

    print(
        "ORR violated:"
    )
    print(
        f"  n={v['n']}, "
        f"median={v['median']}, "
        f"mean={v['mean']}, "
        f"max={v['max']}"
    )

    print()
    print(
        "Accuracy vs adequacy"
    )
    print()

    print(
        "Error/adequacy inversion "
        f"observed: {inversion_exists}"
    )

    if (
        strongest_preserved
        is not None
    ):
        print(
            "Maximum-error preserved "
            "observation:"
        )
        print(
            "  "
            f"{strongest_preserved['run_id']} "
            f"cycle "
            f"{strongest_preserved['cycle']}: "
            f"error="
            f"{strongest_preserved['absolute_error']}"
        )

    if (
        strongest_violation
        is not None
    ):
        print(
            "Minimum-error violated "
            "observation:"
        )
        print(
            "  "
            f"{strongest_violation['run_id']} "
            f"cycle "
            f"{strongest_violation['cycle']}: "
            f"error="
            f"{strongest_violation['absolute_error']}"
        )

    print()
    print(
        "Violations by adaptation cycle"
    )
    print()

    for row in temporal:
        if row["orr_violations"]:
            print(
                f"Cycle {row['cycle']:2d}: "
                f"{row['orr_violations']:2d}/"
                f"{row['observations']} "
                "violations"
            )

    print()
    print(
        f"JSON written to: "
        f"{OUTPUT_JSON}"
    )

    print(
        f"Run TSV written to: "
        f"{OUTPUT_RUN_TSV}"
    )

    print(
        f"Cycle TSV written to: "
        f"{OUTPUT_CYCLE_TSV}"
    )


if __name__ == "__main__":
    main()

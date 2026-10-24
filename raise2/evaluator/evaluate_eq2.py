import csv
import json
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

RESULTS_ROOT = (
    PROJECT_ROOT
    / "raise2/results/mobstr-eq2"
)

GROUND_TRUTH_PATH = (
    PROJECT_ROOT
    / "raise2/evaluation/mobstr/eq2-ground-truth.json"
)

BASELINE_PATH = (
    PROJECT_ROOT
    / "mobstr/work/revalidation/H1/baseline.json"
)

PROTOCOL_PATH = (
    PROJECT_ROOT
    / "raise2/protocol/rv-protocol.txt"
)

SCHEMA_PATH = (
    PROJECT_ROOT
    / "raise2/schemas/rv-result.schema.json"
)

OUTPUT_JSON = (
    PROJECT_ROOT
    / "raise2/results/mobstr-eq2-final-results.json"
)

OUTPUT_TSV = (
    PROJECT_ROOT
    / "raise2/results/mobstr-eq2-final-results.tsv"
)

SCENARIO_TSV = (
    PROJECT_ROOT
    / "raise2/results/mobstr-eq2-scenario-summary.tsv"
)

RUNS_PER_SCENARIO = 10

EXPECTED_MODEL = (
    "gpt-5.4-mini-2026-03-17"
)


def load_json(path: Path) -> dict:
    with path.open(
        "r",
        encoding="utf-8",
    ) as f:
        return json.load(f)


def safe_rate(
    numerator: int,
    denominator: int,
):
    if denominator == 0:
        return None

    return numerator / denominator


def fmt_rate(value):
    if value is None:
        return "n/a"

    return f"{100 * value:.1f}%"


def main():
    # --------------------------------------------------
    # Load frozen ground truth
    # --------------------------------------------------

    ground_truth = load_json(
        GROUND_TRUTH_PATH
    )

    baseline = load_json(
        BASELINE_PATH
    )

    expected_baseline_id = (
        ground_truth["baseline_id"]
    )

    if (
        baseline["baseline_id"]
        != expected_baseline_id
    ):
        raise ValueError(
            "Ground truth and baseline ID mismatch."
        )

    gt_by_change = {
        item["change_id"]: item
        for item in ground_truth[
            "scenarios"
        ]
    }

    if len(gt_by_change) != 6:
        raise ValueError(
            "Expected exactly six "
            "ground-truth scenarios."
        )

    # --------------------------------------------------
    # Read all planned executions
    # --------------------------------------------------

    run_records = []
    integrity_errors = []

    for change_id in sorted(
        gt_by_change.keys()
    ):
        gt = gt_by_change[
            change_id
        ]

        for number in range(
            1,
            RUNS_PER_SCENARIO + 1,
        ):
            run_id = (
                f"run-{number:03d}"
            )

            run_dir = (
                RESULTS_ROOT
                / change_id
                / run_id
            )

            metadata_path = (
                run_dir
                / "metadata.json"
            )

            result_path = (
                run_dir
                / "rv-result.json"
            )

            if not run_dir.is_dir():
                integrity_errors.append(
                    f"{change_id}/{run_id}: "
                    "missing run directory"
                )
                continue

            if not metadata_path.is_file():
                integrity_errors.append(
                    f"{change_id}/{run_id}: "
                    "missing metadata.json"
                )
                continue

            metadata = load_json(
                metadata_path
            )

            status = metadata.get(
                "status"
            )

            if status != "completed_valid":
                integrity_errors.append(
                    f"{change_id}/{run_id}: "
                    f"status={status}"
                )
                continue

            if not metadata.get(
                "validation_passed",
                False,
            ):
                integrity_errors.append(
                    f"{change_id}/{run_id}: "
                    "validation_passed != true"
                )
                continue

            if not result_path.is_file():
                integrity_errors.append(
                    f"{change_id}/{run_id}: "
                    "missing rv-result.json"
                )
                continue

            if (
                metadata.get(
                    "requested_model"
                )
                != EXPECTED_MODEL
            ):
                integrity_errors.append(
                    f"{change_id}/{run_id}: "
                    "unexpected requested model"
                )

            if (
                metadata.get(
                    "returned_model"
                )
                != EXPECTED_MODEL
            ):
                integrity_errors.append(
                    f"{change_id}/{run_id}: "
                    "unexpected returned model"
                )

            result = load_json(
                result_path
            )

            if (
                result.get("change_id")
                != change_id
            ):
                integrity_errors.append(
                    f"{change_id}/{run_id}: "
                    "result change_id mismatch"
                )

            if (
                result.get("run_id")
                != run_id
            ):
                integrity_errors.append(
                    f"{change_id}/{run_id}: "
                    "result run_id mismatch"
                )

            actual_decision = (
                result["decision"]
            )

            actual_orrs = sorted(
                result[
                    "affected_orrs"
                ]
            )

            actual_return_point = (
                result[
                    "return_point"
                ]
            )

            expected_decision = (
                gt[
                    "expected_decision"
                ]
            )

            expected_orrs = sorted(
                gt[
                    "affected_orrs"
                ]
            )

            expected_return_point = (
                gt[
                    "return_point"
                ]
            )

            decision_correct = (
                actual_decision
                == expected_decision
            )

            # ------------------------------------------
            # ORR localisation metric
            #
            # Meaningful for REVALIDATE scenarios.
            # For NONE/REDERIVE the invariant validator
            # already requires an empty ORR set.
            # ------------------------------------------

            if (
                expected_decision
                == "REVALIDATE"
            ):
                orr_set_correct = (
                    actual_orrs
                    == expected_orrs
                )
            else:
                orr_set_correct = None

            # ------------------------------------------
            # Return-point metric
            #
            # Meaningful for REDERIVE scenarios.
            # ------------------------------------------

            if (
                expected_decision
                == "REDERIVE"
            ):
                return_point_correct = (
                    actual_return_point
                    == expected_return_point
                )
            else:
                return_point_correct = None

            # ------------------------------------------
            # Exact scenario outcome
            #
            # This is the strongest run-level metric.
            # ------------------------------------------

            exact_outcome = (
                actual_decision
                == expected_decision
                and actual_orrs
                == expected_orrs
                and actual_return_point
                == expected_return_point
            )

            usage = metadata.get(
                "usage",
                {}
            )

            run_records.append(
                {
                    "change_id":
                        change_id,
                    "run_id":
                        run_id,

                    "expected_decision":
                        expected_decision,
                    "actual_decision":
                        actual_decision,
                    "decision_correct":
                        decision_correct,

                    "expected_orrs":
                        expected_orrs,
                    "actual_orrs":
                        actual_orrs,
                    "orr_set_correct":
                        orr_set_correct,

                    "expected_return_point":
                        expected_return_point,
                    "actual_return_point":
                        actual_return_point,
                    "return_point_correct":
                        return_point_correct,

                    "exact_outcome":
                        exact_outcome,

                    "triggered_conditions":
                        sorted(
                            result[
                                "triggered_conditions"
                            ]
                        ),

                    "input_tokens":
                        usage.get(
                            "input_tokens"
                        ),
                    "output_tokens":
                        usage.get(
                            "output_tokens"
                        ),
                    "total_tokens":
                        usage.get(
                            "total_tokens"
                        ),
                }
            )

    # --------------------------------------------------
    # Integrity gate
    # --------------------------------------------------

    if integrity_errors:
        print("=" * 70)
        print("MOBSTR EQ2 EVALUATION")
        print("=" * 70)
        print()
        print("INTEGRITY CHECK: FAIL")

        for error in integrity_errors:
            print(f"- {error}")

        raise SystemExit(1)

    if len(run_records) != 60:
        raise ValueError(
            "Expected 60 valid runs, found "
            f"{len(run_records)}"
        )

    print("=" * 70)
    print("MOBSTR EQ2 EVALUATION")
    print("=" * 70)
    print()
    print("INTEGRITY CHECK: PASS")
    print(
        f"Valid runs: {len(run_records)}/60"
    )

    # --------------------------------------------------
    # Global metrics
    # --------------------------------------------------

    decision_correct = sum(
        row["decision_correct"]
        for row in run_records
    )

    exact_correct = sum(
        row["exact_outcome"]
        for row in run_records
    )

    revalidate_rows = [
        row
        for row in run_records
        if (
            row["expected_decision"]
            == "REVALIDATE"
        )
    ]

    orr_correct = sum(
        row["orr_set_correct"]
        for row in revalidate_rows
    )

    rederive_rows = [
        row
        for row in run_records
        if (
            row["expected_decision"]
            == "REDERIVE"
        )
    ]

    return_correct = sum(
        row["return_point_correct"]
        for row in rederive_rows
    )

    # --------------------------------------------------
    # Decision confusion matrix
    # --------------------------------------------------

    decisions = [
        "NONE",
        "REVALIDATE",
        "REDERIVE",
    ]

    confusion = {
        expected: {
            actual: 0
            for actual in decisions
        }
        for expected in decisions
    }

    for row in run_records:
        confusion[
            row["expected_decision"]
        ][
            row["actual_decision"]
        ] += 1

    # --------------------------------------------------
    # Per-scenario summaries
    # --------------------------------------------------

    scenario_summaries = []

    for change_id in sorted(
        gt_by_change.keys()
    ):
        rows = [
            row
            for row in run_records
            if row["change_id"]
            == change_id
        ]

        if len(rows) != 10:
            raise ValueError(
                f"{change_id}: expected 10 "
                f"runs, found {len(rows)}"
            )

        decision_counts = Counter(
            row["actual_decision"]
            for row in rows
        )

        exact_count = sum(
            row["exact_outcome"]
            for row in rows
        )

        expected_decision = (
            gt_by_change[
                change_id
            ]["expected_decision"]
        )

        decision_match_count = sum(
            row["decision_correct"]
            for row in rows
        )

        if (
            expected_decision
            == "REVALIDATE"
        ):
            scenario_orr_correct = sum(
                row["orr_set_correct"]
                for row in rows
            )
        else:
            scenario_orr_correct = None

        if (
            expected_decision
            == "REDERIVE"
        ):
            scenario_return_correct = sum(
                row[
                    "return_point_correct"
                ]
                for row in rows
            )
        else:
            scenario_return_correct = None

        # Exact-output reproducibility:
        # all 10 runs produced the same lifecycle
        # decision, ORR set, and return point.
        outcome_signatures = {
            (
                row["actual_decision"],
                tuple(
                    row["actual_orrs"]
                ),
                row[
                    "actual_return_point"
                ],
            )
            for row in rows
        }

        deterministic_outcome = (
            len(
                outcome_signatures
            )
            == 1
        )

        scenario_summaries.append(
            {
                "change_id":
                    change_id,
                "expected_decision":
                    expected_decision,
                "expected_orrs":
                    gt_by_change[
                        change_id
                    ]["affected_orrs"],
                "expected_return_point":
                    gt_by_change[
                        change_id
                    ]["return_point"],
                "runs":
                    len(rows),
                "decision_counts":
                    dict(
                        decision_counts
                    ),
                "decision_correct":
                    decision_match_count,
                "orr_set_correct":
                    scenario_orr_correct,
                "return_point_correct":
                    scenario_return_correct,
                "exact_outcome_correct":
                    exact_count,
                "distinct_outcomes":
                    len(
                        outcome_signatures
                    ),
                "fully_reproducible":
                    deterministic_outcome,
            }
        )

    # --------------------------------------------------
    # Token statistics
    # --------------------------------------------------

    input_tokens = [
        row["input_tokens"]
        for row in run_records
        if row["input_tokens"]
        is not None
    ]

    output_tokens = [
        row["output_tokens"]
        for row in run_records
        if row["output_tokens"]
        is not None
    ]

    total_tokens = [
        row["total_tokens"]
        for row in run_records
        if row["total_tokens"]
        is not None
    ]

    token_summary = {
        "input_tokens_total":
            sum(input_tokens),
        "output_tokens_total":
            sum(output_tokens),
        "total_tokens":
            sum(total_tokens),
        "mean_input_tokens":
            (
                sum(input_tokens)
                / len(input_tokens)
                if input_tokens
                else None
            ),
        "mean_output_tokens":
            (
                sum(output_tokens)
                / len(output_tokens)
                if output_tokens
                else None
            ),
    }

    # --------------------------------------------------
    # Final machine-readable output
    # --------------------------------------------------

    final_output = {
        "study": "MobSTr EQ2",
        "valid_runs": len(
            run_records
        ),
        "global_metrics": {
            "decision_accuracy": {
                "correct":
                    decision_correct,
                "total":
                    len(run_records),
                "rate":
                    safe_rate(
                        decision_correct,
                        len(run_records),
                    ),
            },
            "affected_orr_exact_accuracy": {
                "correct":
                    orr_correct,
                "total":
                    len(
                        revalidate_rows
                    ),
                "rate":
                    safe_rate(
                        orr_correct,
                        len(
                            revalidate_rows
                        ),
                    ),
            },
            "return_point_accuracy": {
                "correct":
                    return_correct,
                "total":
                    len(
                        rederive_rows
                    ),
                "rate":
                    safe_rate(
                        return_correct,
                        len(
                            rederive_rows
                        ),
                    ),
            },
            "exact_outcome_accuracy": {
                "correct":
                    exact_correct,
                "total":
                    len(run_records),
                "rate":
                    safe_rate(
                        exact_correct,
                        len(
                            run_records
                        ),
                    ),
            },
        },
        "decision_confusion_matrix":
            confusion,
        "scenario_summaries":
            scenario_summaries,
        "token_usage":
            token_summary,
        "runs":
            run_records,
    }

    with OUTPUT_JSON.open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            final_output,
            f,
            indent=2,
            ensure_ascii=False,
        )
        f.write("\n")

    # --------------------------------------------------
    # Flat run-level TSV
    # --------------------------------------------------

    with OUTPUT_TSV.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as f:

        fieldnames = [
            "change_id",
            "run_id",
            "expected_decision",
            "actual_decision",
            "decision_correct",
            "expected_orrs",
            "actual_orrs",
            "orr_set_correct",
            "expected_return_point",
            "actual_return_point",
            "return_point_correct",
            "exact_outcome",
            "triggered_conditions",
            "input_tokens",
            "output_tokens",
            "total_tokens",
        ]

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
            delimiter="\t",
        )

        writer.writeheader()

        for row in run_records:
            out = dict(row)

            out["expected_orrs"] = (
                ";".join(
                    row[
                        "expected_orrs"
                    ]
                )
            )

            out["actual_orrs"] = (
                ";".join(
                    row[
                        "actual_orrs"
                    ]
                )
            )

            out[
                "triggered_conditions"
            ] = ";".join(
                row[
                    "triggered_conditions"
                ]
            )

            writer.writerow(out)

    # --------------------------------------------------
    # Scenario summary TSV
    # --------------------------------------------------

    with SCENARIO_TSV.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as f:

        fieldnames = [
            "change_id",
            "expected_decision",
            "runs",
            "decision_correct",
            "orr_set_correct",
            "return_point_correct",
            "exact_outcome_correct",
            "distinct_outcomes",
            "fully_reproducible",
        ]

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
            delimiter="\t",
        )

        writer.writeheader()

        for summary in (
            scenario_summaries
        ):
            writer.writerow(
                {
                    key:
                        summary.get(
                            key
                        )
                    for key
                    in fieldnames
                }
            )

    # --------------------------------------------------
    # Console report
    # --------------------------------------------------

    print()
    print("Global metrics")
    print()

    print(
        "Lifecycle decision accuracy: "
        f"{decision_correct}/"
        f"{len(run_records)} "
        f"({fmt_rate(
            safe_rate(
                decision_correct,
                len(run_records),
            )
        )})"
    )

    print(
        "Affected-ORR exact accuracy: "
        f"{orr_correct}/"
        f"{len(revalidate_rows)} "
        f"({fmt_rate(
            safe_rate(
                orr_correct,
                len(revalidate_rows),
            )
        )})"
    )

    print(
        "Return-point accuracy: "
        f"{return_correct}/"
        f"{len(rederive_rows)} "
        f"({fmt_rate(
            safe_rate(
                return_correct,
                len(rederive_rows),
            )
        )})"
    )

    print(
        "Exact lifecycle outcome: "
        f"{exact_correct}/"
        f"{len(run_records)} "
        f"({fmt_rate(
            safe_rate(
                exact_correct,
                len(run_records),
            )
        )})"
    )

    print()
    print("Per-scenario reproducibility")
    print()

    for summary in (
        scenario_summaries
    ):
        print(
            f"{summary['change_id']} "
            f"[{summary['expected_decision']}]"
        )

        print(
            "  Decision correct: "
            f"{summary['decision_correct']}/10"
        )

        if (
            summary[
                "orr_set_correct"
            ]
            is not None
        ):
            print(
                "  ORR set correct:  "
                f"{summary['orr_set_correct']}/10"
            )

        if (
            summary[
                "return_point_correct"
            ]
            is not None
        ):
            print(
                "  Return point:      "
                f"{summary['return_point_correct']}/10"
            )

        print(
            "  Exact outcome:     "
            f"{summary['exact_outcome_correct']}/10"
        )

        print(
            "  Distinct outcomes: "
            f"{summary['distinct_outcomes']}"
        )

        print(
            "  Fully reproducible: "
            f"{summary['fully_reproducible']}"
        )

        print()

    print("Decision confusion matrix")
    print()

    print(
        "expected\\actual\t"
        "NONE\tREVALIDATE\tREDERIVE"
    )

    for expected in decisions:
        print(
            f"{expected}\t"
            f"{confusion[expected]['NONE']}\t"
            f"{confusion[expected]['REVALIDATE']}\t"
            f"{confusion[expected]['REDERIVE']}"
        )

    print()
    print(
        f"JSON written to: {OUTPUT_JSON}"
    )
    print(
        f"Run TSV written to: {OUTPUT_TSV}"
    )
    print(
        f"Scenario TSV written to: "
        f"{SCENARIO_TSV}"
    )


if __name__ == "__main__":
    main()

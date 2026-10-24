import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULTS_ROOT = PROJECT_ROOT / "raise2" / "results"

CANDIDATES_PATH = (
    RESULTS_ROOT
    / "mobstr-eq1-reference-candidates.tsv"
)

POI_PATH = (
    RESULTS_ROOT
    / "mobstr-eq1-poi-conformance.json"
)

ADJUDICATION_PATH = (
    PROJECT_ROOT
    / "raise2"
    / "evaluation"
    / "mobstr"
    / "reference-adjudication.tsv"
)

OUTPUT_JSON = (
    RESULTS_ROOT
    / "mobstr-eq1-final-results.json"
)

OUTPUT_TSV = (
    RESULTS_ROOT
    / "mobstr-eq1-final-results.tsv"
)


REFERENCES = [
    "H1-REF1",
    "H1-REF2",
    "H3-REF1",
    "H3-REF2",
]


def load_json(path):
    with path.open(
        "r",
        encoding="utf-8",
    ) as f:
        return json.load(f)


def load_tsv(path):
    with path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as f:
        return list(
            csv.DictReader(
                f,
                delimiter="\t",
            )
        )


def main():

    # --------------------------------------------------
    # Load PoI conformance
    # --------------------------------------------------

    poi_data = load_json(
        POI_PATH
    )

    poi_classification = {
        item["run_id"]:
            item["final_classification"]
        for item in poi_data["runs"]
    }

    # --------------------------------------------------
    # Load deterministic matcher results
    # --------------------------------------------------

    candidate_rows = load_tsv(
        CANDIDATES_PATH
    )

    groups = defaultdict(list)

    for row in candidate_rows:
        key = (
            row["concern"],
            row["run_id"],
            row["reference_id"],
        )

        groups[key].append(row)

    # --------------------------------------------------
    # Load frozen adjudications
    # --------------------------------------------------

    adjudication_rows = load_tsv(
        ADJUDICATION_PATH
    )

    adjudications = {}

    for row in adjudication_rows:

        key = (
            row["run_id"],
            row["reference_id"],
        )

        decision = row["decision"]

        if decision not in {
            "RECOVERED",
            "NOT_RECOVERED",
        }:
            raise ValueError(
                "Invalid or missing adjudication "
                f"for {key}: {decision}"
            )

        if key in adjudications:
            raise ValueError(
                f"Duplicate adjudication: {key}"
            )

        adjudications[key] = {
            "decision": decision,
            "reason":
                row[
                    "reason_for_adjudication"
                ],
            "rationale":
                row["rationale"],
        }

    # --------------------------------------------------
    # Resolve every run-reference pair
    # --------------------------------------------------

    decisions = []

    for (
        concern,
        run_id,
        reference_id,
    ), items in sorted(groups.items()):

        statuses = {
            item["status"]
            for item in items
        }

        adjudication_key = (
            run_id,
            reference_id,
        )

        # ----------------------------------------------
        # Explicit frozen adjudication takes precedence.
        #
        # This includes:
        # - lexical REVIEW cases;
        # - H3-REF2 zero-recovery audit.
        # ----------------------------------------------

        if adjudication_key in adjudications:

            final_decision = (
                adjudications[
                    adjudication_key
                ]["decision"]
            )

            decision_source = (
                "frozen_adjudication"
            )

        # ----------------------------------------------
        # Otherwise a conservative automatic MATCH
        # establishes run-level recovery.
        # ----------------------------------------------

        elif "MATCH" in statuses:

            final_decision = (
                "RECOVERED"
            )

            decision_source = (
                "deterministic_match"
            )

        # ----------------------------------------------
        # REVIEW must never remain unresolved.
        # ----------------------------------------------

        elif "REVIEW" in statuses:

            raise ValueError(
                "Unresolved REVIEW for "
                f"{run_id} / {reference_id}"
            )

        # ----------------------------------------------
        # No candidate match.
        # ----------------------------------------------

        else:

            final_decision = (
                "NOT_RECOVERED"
            )

            decision_source = (
                "deterministic_no_match"
            )

        decisions.append(
            {
                "concern":
                    concern,
                "run_id":
                    run_id,
                "reference_id":
                    reference_id,
                "poi_classification":
                    poi_classification[
                        run_id
                    ],
                "decision":
                    final_decision,
                "decision_source":
                    decision_source,
            }
        )

    # --------------------------------------------------
    # Integrity checks
    # --------------------------------------------------

    if len(decisions) != 120:
        raise ValueError(
            "Expected 120 run-reference "
            f"decisions, found {len(decisions)}"
        )

    per_reference = Counter(
        item["reference_id"]
        for item in decisions
    )

    for reference in REFERENCES:

        if per_reference[
            reference
        ] != 30:

            raise ValueError(
                f"{reference}: expected 30 "
                f"decisions, found "
                f"{per_reference[reference]}"
            )

    # --------------------------------------------------
    # Aggregate results
    # --------------------------------------------------

    results = {}

    for reference in REFERENCES:

        ref_rows = [
            row
            for row in decisions
            if row["reference_id"]
            == reference
        ]

        recovered = sum(
            row["decision"]
            == "RECOVERED"
            for row in ref_rows
        )

        aligned_rows = [
            row
            for row in ref_rows
            if row[
                "poi_classification"
            ] == "ALIGNED"
        ]

        aligned_recovered = sum(
            row["decision"]
            == "RECOVERED"
            for row in aligned_rows
        )

        results[reference] = {
            "all_runs": {
                "recovered":
                    recovered,
                "total":
                    len(ref_rows),
                "rate":
                    recovered
                    / len(ref_rows),
            },
            "poi_aligned_runs": {
                "recovered":
                    aligned_recovered,
                "total":
                    len(aligned_rows),
                "rate": (
                    aligned_recovered
                    / len(aligned_rows)
                    if aligned_rows
                    else None
                ),
            },
        }

    # --------------------------------------------------
    # Concern-level complete recovery
    #
    # A run completely recovers the frozen reference
    # when all reference distinctions for that concern
    # are recovered.
    # --------------------------------------------------

    run_decisions = defaultdict(dict)

    for row in decisions:
        run_decisions[
            row["run_id"]
        ][
            row["reference_id"]
        ] = row["decision"]

    complete_recovery = {}

    for concern in [
        "H1",
        "H3",
    ]:

        refs = (
            ["H1-REF1", "H1-REF2"]
            if concern == "H1"
            else ["H3-REF1", "H3-REF2"]
        )

        prefix = (
            "H1-run-"
            if concern == "H1"
            else "H3-run-"
        )

        runs = [
            run_id
            for run_id
            in sorted(
                run_decisions.keys()
            )
            if run_id.startswith(
                prefix
            )
        ]

        complete = sum(
            all(
                run_decisions[
                    run_id
                ][ref]
                == "RECOVERED"
                for ref in refs
            )
            for run_id in runs
        )

        aligned_runs = [
            run_id
            for run_id in runs
            if poi_classification[
                run_id
            ] == "ALIGNED"
        ]

        aligned_complete = sum(
            all(
                run_decisions[
                    run_id
                ][ref]
                == "RECOVERED"
                for ref in refs
            )
            for run_id
            in aligned_runs
        )

        complete_recovery[
            concern
        ] = {
            "all_runs": {
                "complete":
                    complete,
                "total":
                    len(runs),
                "rate":
                    complete
                    / len(runs),
            },
            "poi_aligned_runs": {
                "complete":
                    aligned_complete,
                "total":
                    len(aligned_runs),
                "rate": (
                    aligned_complete
                    / len(aligned_runs)
                    if aligned_runs
                    else None
                ),
            },
        }

    # --------------------------------------------------
    # Persist machine-readable output
    # --------------------------------------------------

    final_output = {
        "reference_recovery":
            results,
        "complete_recovery":
            complete_recovery,
        "run_reference_decisions":
            decisions,
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
    # Persist flat TSV
    # --------------------------------------------------

    with OUTPUT_TSV.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as f:

        fieldnames = [
            "concern",
            "run_id",
            "reference_id",
            "poi_classification",
            "decision",
            "decision_source",
        ]

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
            delimiter="\t",
        )

        writer.writeheader()
        writer.writerows(
            decisions
        )

    # --------------------------------------------------
    # Console report
    # --------------------------------------------------

    print("=" * 70)
    print("MOBSTR EQ1 FINAL RESULTS")
    print("=" * 70)

    print()
    print("Reference recovery")
    print()

    for reference in REFERENCES:

        result = results[
            reference
        ]

        all_runs = result[
            "all_runs"
        ]

        aligned = result[
            "poi_aligned_runs"
        ]

        print(reference)

        print(
            "  All runs:        "
            f"{all_runs['recovered']}/"
            f"{all_runs['total']} "
            f"({100 * all_runs['rate']:.1f}%)"
        )

        print(
            "  PoI-aligned:     "
            f"{aligned['recovered']}/"
            f"{aligned['total']} "
            f"({100 * aligned['rate']:.1f}%)"
        )

        print()

    print("Complete reference recovery")
    print()

    for concern in [
        "H1",
        "H3",
    ]:

        result = (
            complete_recovery[
                concern
            ]
        )

        all_runs = result[
            "all_runs"
        ]

        aligned = result[
            "poi_aligned_runs"
        ]

        print(concern)

        print(
            "  All runs:        "
            f"{all_runs['complete']}/"
            f"{all_runs['total']} "
            f"({100 * all_runs['rate']:.1f}%)"
        )

        print(
            "  PoI-aligned:     "
            f"{aligned['complete']}/"
            f"{aligned['total']} "
            f"({100 * aligned['rate']:.1f}%)"
        )

        print()

    print(
        f"JSON written to: {OUTPUT_JSON}"
    )

    print(
        f"TSV written to: {OUTPUT_TSV}"
    )


if __name__ == "__main__":
    main()

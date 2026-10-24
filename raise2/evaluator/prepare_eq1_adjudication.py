import csv
import json
from collections import defaultdict
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULTS_ROOT = PROJECT_ROOT / "raise2" / "results"

CANDIDATES_PATH = (
    RESULTS_ROOT
    / "mobstr-eq1-reference-candidates.tsv"
)

POI_RESULTS_PATH = (
    RESULTS_ROOT
    / "mobstr-eq1-poi-conformance.json"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "raise2"
    / "evaluation"
    / "mobstr"
    / "reference-adjudication.tsv"
)


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main():
    # --------------------------------------------------
    # Load PoI classifications
    # --------------------------------------------------

    poi_data = load_json(
        POI_RESULTS_PATH
    )

    poi_classification = {
        item["run_id"]:
            item["final_classification"]
        for item in poi_data["runs"]
    }

    # --------------------------------------------------
    # Load deterministic matcher output
    # --------------------------------------------------

    with CANDIDATES_PATH.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as f:
        rows = list(
            csv.DictReader(
                f,
                delimiter="\t",
            )
        )

    groups = defaultdict(list)

    for row in rows:
        key = (
            row["concern"],
            row["run_id"],
            row["reference_id"],
        )

        groups[key].append(row)

    adjudication_rows = []

    # --------------------------------------------------
    # Determine which run-reference pairs require
    # explicit human adjudication
    # --------------------------------------------------

    for (
        concern,
        run_id,
        reference_id,
    ), items in sorted(groups.items()):

        statuses = {
            item["status"]
            for item in items
        }

        # --------------------------------------------------
        # Special audit decision:
        #
        # H3-REF2 produced zero lexical candidates.
        # All H3 CRDs were subsequently inspected and no
        # braking-relevant spatial-relation distinction
        # was found.
        #
        # We therefore record this explicitly as an
        # audited run-level decision for every H3 run.
        # --------------------------------------------------

        if reference_id == "H3-REF2":
            adjudication_rows.append(
                {
                    "concern": concern,
                    "run_id": run_id,
                    "poi_classification":
                        poi_classification[
                            run_id
                        ],
                    "reference_id":
                        reference_id,
                    "reason_for_adjudication":
                        "zero-recovery-audit",
                    "candidate_crds": "",
                    "decision":
                        "NOT_RECOVERED",
                    "rationale": (
                        "No derived CRD expresses "
                        "a braking-relevant spatial "
                        "relation distinguishing a "
                        "condition that justifies "
                        "braking from one that does "
                        "not."
                    ),
                }
            )

            continue

        # --------------------------------------------------
        # Clear automatic match.
        #
        # These do not require human adjudication.
        # They will be audited separately by the final
        # evaluator against the frozen matching rule.
        # --------------------------------------------------

        if "MATCH" in statuses:
            continue

        # --------------------------------------------------
        # Lexically ambiguous cases require adjudication.
        # --------------------------------------------------

        review_items = [
            item
            for item in items
            if item["status"] == "REVIEW"
        ]

        if not review_items:
            continue

        candidate_descriptions = []

        for item in review_items:
            candidate_descriptions.append(
                " | ".join(
                    [
                        item["crd_id"],
                        item["dimension"],
                        item["contrast_a"],
                        item["contrast_b"],
                    ]
                )
            )

        adjudication_rows.append(
            {
                "concern": concern,
                "run_id": run_id,
                "poi_classification":
                    poi_classification[
                        run_id
                    ],
                "reference_id":
                    reference_id,
                "reason_for_adjudication":
                    "lexical-review",
                "candidate_crds":
                    " || ".join(
                        candidate_descriptions
                    ),
                "decision": "",
                "rationale": "",
            }
        )

    # --------------------------------------------------
    # Write immutable adjudication template
    # --------------------------------------------------

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fieldnames = [
        "concern",
        "run_id",
        "poi_classification",
        "reference_id",
        "reason_for_adjudication",
        "candidate_crds",
        "decision",
        "rationale",
    ]

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
            delimiter="\t",
        )

        writer.writeheader()
        writer.writerows(
            adjudication_rows
        )

    # --------------------------------------------------
    # Summary
    # --------------------------------------------------

    lexical_reviews = sum(
        1
        for row in adjudication_rows
        if row[
            "reason_for_adjudication"
        ] == "lexical-review"
    )

    zero_audits = sum(
        1
        for row in adjudication_rows
        if row[
            "reason_for_adjudication"
        ] == "zero-recovery-audit"
    )

    print("=" * 70)
    print("EQ1 ADJUDICATION TEMPLATE")
    print("=" * 70)

    print(
        f"Lexical reviews requiring "
        f"human decision: {lexical_reviews}"
    )

    print(
        f"Pre-recorded H3-REF2 audit "
        f"decisions: {zero_audits}"
    )

    print(
        f"Total adjudication rows: "
        f"{len(adjudication_rows)}"
    )

    print()
    print(
        f"Written to: {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()

import json
import sys
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULTS_ROOT = PROJECT_ROOT / "raise2" / "results"

EXPERIMENTS = [
    {
        "concern": "H1",
        "experiment_id": "mobstr-H1",
        "prefix": "H1-run",
        "runs": 30,
    },
    {
        "concern": "H3",
        "experiment_id": "mobstr-H3",
        "prefix": "H3-run",
        "runs": 30,
    },
]

JUDGES = [
    "judge-01",
    "judge-02",
    "judge-03",
]

VALID_CLASSES = {
    "ALIGNED",
    "OVEREXTENDED",
    "UNDERDETERMINED",
}


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def valid_candidate(
    assessment_dir: Path,
):
    metadata_path = (
        assessment_dir / "metadata.json"
    )
    assessment_path = (
        assessment_dir / "assessment.json"
    )

    if not metadata_path.is_file():
        return None

    if not assessment_path.is_file():
        return None

    metadata = load_json(metadata_path)

    if (
        metadata.get("status")
        != "completed_valid"
    ):
        return None

    if not metadata.get(
        "validation_passed",
        False,
    ):
        return None

    assessment = load_json(
        assessment_path
    )

    classification = assessment.get(
        "classification"
    )

    if classification not in VALID_CLASSES:
        return None

    return {
        "classification": classification,
        "assessment": assessment,
        "metadata": metadata,
        "directory": assessment_dir.name,
    }


def resolve_judge_vote(
    poi_dir: Path,
    judge_id: str,
):
    """
    Select the first valid observation for one
    logical judge slot.

    Search order:
      judge-01
      judge-01-resume-01
      judge-01-resume-02
      ...

    Failed API attempts are preserved but do not
    constitute experimental observations.
    """

    candidates = []

    original = poi_dir / judge_id

    if original.exists():
        candidates.append(original)

    resumes = sorted(
        poi_dir.glob(
            f"{judge_id}-resume-*"
        )
    )

    candidates.extend(resumes)

    valid = []

    for candidate in candidates:
        result = valid_candidate(candidate)

        if result is not None:
            valid.append(result)

    if not valid:
        return None, (
            f"No valid assessment for {judge_id}"
        )

    if len(valid) > 1:
        return None, (
            f"Multiple valid assessments for "
            f"{judge_id}: "
            + ", ".join(
                item["directory"]
                for item in valid
            )
        )

    return valid[0], None


def majority_vote(classifications):
    counts = Counter(classifications)

    ordered = counts.most_common()

    winner, winner_count = ordered[0]

    if winner_count >= 2:
        agreement = (
            "unanimous"
            if winner_count == 3
            else "majority"
        )

        return (
            winner,
            agreement,
            winner_count,
            counts,
        )

    return (
        None,
        "no_majority",
        winner_count,
        counts,
    )


def main():
    records = []
    errors = []

    global_classifications = Counter()
    global_agreement = Counter()

    by_concern_classification = {
        "H1": Counter(),
        "H3": Counter(),
    }

    by_concern_agreement = {
        "H1": Counter(),
        "H3": Counter(),
    }

    recovered_votes = 0

    for experiment in EXPERIMENTS:
        concern = experiment["concern"]

        experiment_dir = (
            RESULTS_ROOT
            / experiment["experiment_id"]
        )

        for number in range(
            1,
            experiment["runs"] + 1,
        ):
            run_id = (
                f"{experiment['prefix']}"
                f"-{number:03d}"
            )

            poi_dir = (
                experiment_dir
                / run_id
                / "poi-conformance"
            )

            votes = []
            vote_details = []

            for judge_id in JUDGES:
                vote, error = (
                    resolve_judge_vote(
                        poi_dir,
                        judge_id,
                    )
                )

                if error:
                    errors.append(
                        f"{run_id}: {error}"
                    )
                    continue

                votes.append(
                    vote["classification"]
                )

                if "-resume-" in vote["directory"]:
                    recovered_votes += 1

                vote_details.append(
                    {
                        "judge_id": judge_id,
                        "source_directory":
                            vote["directory"],
                        "classification":
                            vote[
                                "classification"
                            ],
                        "response_id":
                            vote["metadata"].get(
                                "response_id"
                            ),
                    }
                )

            if len(votes) != 3:
                errors.append(
                    f"{run_id}: expected 3 valid "
                    f"votes, found {len(votes)}"
                )
                continue

            (
                final_classification,
                agreement,
                winner_count,
                counts,
            ) = majority_vote(votes)

            if final_classification is None:
                errors.append(
                    f"{run_id}: no majority vote"
                )
                continue

            global_classifications[
                final_classification
            ] += 1

            global_agreement[
                agreement
            ] += 1

            by_concern_classification[
                concern
            ][final_classification] += 1

            by_concern_agreement[
                concern
            ][agreement] += 1

            records.append(
                {
                    "concern": concern,
                    "run_id": run_id,
                    "votes": vote_details,
                    "vote_counts": dict(counts),
                    "final_classification":
                        final_classification,
                    "agreement": agreement,
                    "majority_size":
                        winner_count,
                }
            )

    # --------------------------------------------------
    # Persist aggregate result
    # --------------------------------------------------

    output = {
        "total_runs": len(records),
        "recovered_votes_used":
            recovered_votes,
        "classification_counts":
            dict(global_classifications),
        "agreement_counts":
            dict(global_agreement),
        "by_concern": {
            concern: {
                "classification_counts":
                    dict(
                        by_concern_classification[
                            concern
                        ]
                    ),
                "agreement_counts":
                    dict(
                        by_concern_agreement[
                            concern
                        ]
                    ),
            }
            for concern in ["H1", "H3"]
        },
        "runs": records,
        "errors": errors,
    }

    output_path = (
        RESULTS_ROOT
        / "mobstr-eq1-poi-conformance.json"
    )

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            output,
            f,
            indent=2,
            ensure_ascii=False,
        )
        f.write("\n")

    # --------------------------------------------------
    # Console summary
    # --------------------------------------------------

    print("=" * 70)
    print("PoI CONFORMANCE AGGREGATION")
    print("=" * 70)

    print(
        f"Runs aggregated: "
        f"{len(records)}/60"
    )

    print(
        f"Recovered votes used: "
        f"{recovered_votes}"
    )

    print()

    for concern in ["H1", "H3"]:
        print(concern)

        classifications = (
            by_concern_classification[
                concern
            ]
        )

        agreements = (
            by_concern_agreement[
                concern
            ]
        )

        print(
            "  ALIGNED:         "
            f"{classifications['ALIGNED']}"
        )

        print(
            "  OVEREXTENDED:    "
            f"{classifications['OVEREXTENDED']}"
        )

        print(
            "  UNDERDETERMINED: "
            f"{classifications['UNDERDETERMINED']}"
        )

        print(
            "  Unanimous:       "
            f"{agreements['unanimous']}"
        )

        print(
            "  Majority 2/3:    "
            f"{agreements['majority']}"
        )

        print()

    if errors:
        print("AGGREGATION: FAIL")

        for error in errors:
            print(f"- {error}")

        print(
            f"Aggregate written to: "
            f"{output_path}"
        )

        sys.exit(1)

    print("AGGREGATION: PASS")

    print(
        f"Aggregate written to: "
        f"{output_path}"
    )


if __name__ == "__main__":
    main()


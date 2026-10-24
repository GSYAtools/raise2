import csv
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

PATH = (
    PROJECT_ROOT
    / "raise2"
    / "evaluation"
    / "mobstr"
    / "reference-adjudication.tsv"
)


DECISIONS = {
    ("H1-run-001", "H1-REF2"): (
        "NOT_RECOVERED",
        "Detection/timing state, not a spatial relation."
    ),
    ("H1-run-007", "H1-REF2"): (
        "RECOVERED",
        "Distance separates an obstacle near enough to require braking from one present but not yet requiring braking."
    ),
    ("H1-run-008", "H1-REF2"): (
        "NOT_RECOVERED",
        "Braking-response timing, not a spatial relation."
    ),
    ("H1-run-010", "H1-REF2"): (
        "NOT_RECOVERED",
        "Detection versus non-detection, not a phenomenon-level spatial relation."
    ),
    ("H1-run-011", "H1-REF2"): (
        "NOT_RECOVERED",
        "Candidates express braking timing or obstacle detection/presence rather than spatial relation."
    ),
    ("H1-run-013", "H1-REF2"): (
        "NOT_RECOVERED",
        "Presence versus absence of a braking-relevant obstacle, not two spatial-relation classes."
    ),
    ("H1-run-014", "H1-REF1"): (
        "NOT_RECOVERED",
        "Presence is conflated with detectability, so obstacle presence versus absence is not preserved."
    ),
    ("H1-run-016", "H1-REF2"): (
        "RECOVERED",
        "Contrasts a braking-relevant obstacle position with absence or a position where braking relevance does not arise."
    ),
    ("H1-run-019", "H1-REF2"): (
        "RECOVERED",
        "Trajectory proximity and distance distinguish braking-relevant from non-braking-relevant spatial conditions."
    ),
    ("H3-run-002", "H3-REF1"): (
        "RECOVERED",
        "Contrasts braking with an obstacle present against braking with no obstacle present."
    ),
    ("H3-run-007", "H3-REF1"): (
        "NOT_RECOVERED",
        "Both contrasts assume no front obstacle and differ only in braking occurrence."
    ),
    ("H3-run-009", "H3-REF1"): (
        "NOT_RECOVERED",
        "Both contrasts concern the no-obstacle situation and differ only in braking response."
    ),
    ("H3-run-017", "H3-REF1"): (
        "RECOVERED",
        "Explicit obstacle-presence versus obstacle-absence contrast."
    ),
    ("H3-run-022", "H3-REF1"): (
        "RECOVERED",
        "Contrasts obstacle-supported intended braking with unintended braking in the absence of an obstacle."
    ),
    ("H3-run-025", "H3-REF1"): (
        "NOT_RECOVERED",
        "The obstacle condition is fixed while braking behaviour changes."
    ),
    ("H3-run-028", "H3-REF1"): (
        "NOT_RECOVERED",
        "The no-obstacle condition is fixed while braking behaviour changes."
    ),
    ("H3-run-029", "H3-REF1"): (
        "NOT_RECOVERED",
        "The no-obstacle condition is fixed while braking behaviour changes."
    ),
    ("H3-run-030", "H3-REF1"): (
        "RECOVERED",
        "Contrasts braking with an obstacle present against braking with no obstacle present."
    ),
}


def main():
    with PATH.open(
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

        fieldnames = list(
            rows[0].keys()
        )

    applied = 0

    for row in rows:
        if (
            row["reason_for_adjudication"]
            != "lexical-review"
        ):
            continue

        key = (
            row["run_id"],
            row["reference_id"],
        )

        if key not in DECISIONS:
            raise ValueError(
                f"Missing adjudication decision: {key}"
            )

        decision, rationale = DECISIONS[key]

        if row["decision"]:
            raise ValueError(
                f"Decision already populated: {key}"
            )

        row["decision"] = decision
        row["rationale"] = rationale

        applied += 1

    expected = len(DECISIONS)

    if applied != expected:
        raise ValueError(
            f"Expected {expected} decisions, "
            f"applied {applied}"
        )

    unresolved = [
        (
            row["run_id"],
            row["reference_id"],
        )
        for row in rows
        if (
            row["reason_for_adjudication"]
            == "lexical-review"
            and not row["decision"]
        )
    ]

    if unresolved:
        raise ValueError(
            f"Unresolved adjudications: {unresolved}"
        )

    with PATH.open(
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
        writer.writerows(rows)

    print(
        f"Human adjudications applied: {applied}"
    )
    print(
        "Unresolved lexical reviews: 0"
    )
    print(
        f"Updated: {PATH}"
    )


if __name__ == "__main__":
    main()

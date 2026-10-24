import hashlib
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

BASELINE_PATH = (
    PROJECT_ROOT
    / "mobstr/work/revalidation/H1/baseline.json"
)

CHANGES_DIR = (
    PROJECT_ROOT
    / "mobstr/work/revalidation/H1/changes"
)

GROUND_TRUTH_PATH = (
    PROJECT_ROOT
    / "raise2/evaluation/mobstr/eq2-ground-truth.json"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            digest.update(chunk)

    return digest.hexdigest()


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            data,
            f,
            indent=2,
            ensure_ascii=False,
        )
        f.write("\n")


def main():
    if not BASELINE_PATH.is_file():
        raise FileNotFoundError(
            f"Baseline not found: {BASELINE_PATH}"
        )

    baseline_hash = sha256_file(
        BASELINE_PATH
    )

    expected_baseline_hash = (
        "e7e53a8058e7da0a0d22bc43c6dd38e629e704897b701239597302e777cc9965"
    )

    if baseline_hash != expected_baseline_hash:
        raise ValueError(
            "Baseline hash mismatch.\n"
            f"Expected: {expected_baseline_hash}\n"
            f"Actual:   {baseline_hash}"
        )

    # --------------------------------------------------
    # Experimental changes
    #
    # IMPORTANT:
    # These objects contain only information visible
    # to the RV executor.
    # --------------------------------------------------

    changes = [
        {
            "change_id": "delta-01",
            "title": (
                "Driver-warning presentation update"
            ),
            "change_type": (
                "architecture"
            ),
            "description": (
                "The driver-warning presentation "
                "component is changed to use a new "
                "visual layout and notification "
                "presentation. The change does not "
                "modify obstacle information, object "
                "category information, ego-object "
                "spatial information, the declared "
                "Phenomenon of Interest, or the "
                "Evaluation Target."
            ),
            "changed_elements": [
                "Driver Warnings"
            ],
        },

        {
            "change_id": "delta-02",
            "title": (
                "Obstacle-presence information "
                "interface change"
            ),
            "change_type": (
                "representation_dependency"
            ),
            "description": (
                "The interface supplying obstacle "
                "information to the operational "
                "representation is changed. Obstacle "
                "presence is now supplied through a "
                "revised object-detection information "
                "interface, while the engineering "
                "concern, Phenomenon of Interest, "
                "object-category scheme, and "
                "ego-object spatial relation remain "
                "unchanged."
            ),
            "changed_elements": [
                "Object Detection",
                "obstacle-information interface"
            ],
        },

        {
            "change_id": "delta-03",
            "title": (
                "Object-category scheme revision"
            ),
            "change_type": (
                "requirement"
            ),
            "description": (
                "The object-category scheme used by "
                "Object Detection is revised. The "
                "distinction between vulnerable road "
                "users and other objects must be "
                "reassessed under the revised category "
                "scheme. Obstacle-presence information, "
                "ego-object spatial information, the "
                "Phenomenon of Interest, and the "
                "Evaluation Target remain unchanged."
            ),
            "changed_elements": [
                "FR-7.2.2",
                "object-category scheme"
            ],
        },

        {
            "change_id": "delta-04",
            "title": (
                "Dangerous-zone definition introduced"
            ),
            "change_type": (
                "requirement"
            ),
            "description": (
                "The previously unspecified dangerous-"
                "zone boundary is replaced by an "
                "explicit configurable braking-zone "
                "definition determined by the active "
                "operational profile. The engineering "
                "concern and Phenomenon of Interest "
                "remain unchanged."
            ),
            "changed_elements": [
                "FR-7.1",
                "dangerous-zone definition"
            ],
        },

        {
            "change_id": "delta-05",
            "title": (
                "Phenomenon-of-Interest scope extension"
            ),
            "change_type": (
                "phenomenon_scope"
            ),
            "description": (
                "The scope of the Phenomenon of "
                "Interest is extended beyond the "
                "collision-relevant spatial situation. "
                "The revised evaluation must also "
                "characterise road-surface condition "
                "as part of the phenomenon because "
                "road-surface state is now considered "
                "part of determining whether braking "
                "is required. The Evaluation Target "
                "itself remains unchanged."
            ),
            "changed_elements": [
                "P_H1",
                "phenomenon scope",
                "road-surface condition"
            ],
        },

        {
            "change_id": "delta-06",
            "title": (
                "Evaluation Target extension"
            ),
            "change_type": (
                "evaluation_target"
            ),
            "description": (
                "The Evaluation Target is changed. "
                "Instead of determining only whether "
                "the current operational situation "
                "requires braking to avoid collision, "
                "the evaluation must now determine "
                "whether either braking or an evasive "
                "lane-change maneuver is required to "
                "avoid collision."
            ),
            "changed_elements": [
                "T_H1",
                "evaluation target",
                "evasive lane-change maneuver"
            ],
        },
    ]

    # --------------------------------------------------
    # Ground truth
    #
    # NEVER supplied to the RV executor.
    # --------------------------------------------------

    ground_truth = {
        "study": "MobSTr EQ2",
        "baseline_id": (
            "mobstr-H1-revalidation-baseline-v1"
        ),
        "baseline_sha256": baseline_hash,
        "scenarios": [
            {
                "change_id": "delta-01",
                "expected_decision": "NONE",
                "affected_orrs": [],
                "return_point": None,
                "rationale": (
                    "The presentation-only change does "
                    "not intersect any frozen assumption "
                    "or revalidation condition and does "
                    "not alter T or P."
                ),
            },
            {
                "change_id": "delta-02",
                "expected_decision": "REVALIDATE",
                "affected_orrs": [
                    "H1-ORR1"
                ],
                "return_point": None,
                "rationale": (
                    "H1-RC1 explicitly requires "
                    "revalidation when the information "
                    "supplied for representing obstacle "
                    "presence changes."
                ),
            },
            {
                "change_id": "delta-03",
                "expected_decision": "REVALIDATE",
                "affected_orrs": [
                    "H1-ORR2"
                ],
                "return_point": None,
                "rationale": (
                    "H1-RC2 explicitly covers changes "
                    "to FR-7.2.2 and the object-category "
                    "scheme."
                ),
            },
            {
                "change_id": "delta-04",
                "expected_decision": "REVALIDATE",
                "affected_orrs": [
                    "H1-ORR3"
                ],
                "return_point": None,
                "rationale": (
                    "H1-RC3 explicitly covers changes "
                    "to the dangerous-zone definition "
                    "and spatial-information basis."
                ),
            },
            {
                "change_id": "delta-05",
                "expected_decision": "REDERIVE",
                "affected_orrs": [],
                "return_point": "RR2",
                "rationale": (
                    "The declared Phenomenon of Interest "
                    "changes, invalidating the scope from "
                    "which concern-relevant distinctions "
                    "are derived."
                ),
            },
            {
                "change_id": "delta-06",
                "expected_decision": "REDERIVE",
                "affected_orrs": [],
                "return_point": "RR1",
                "rationale": (
                    "The Evaluation Target itself "
                    "changes, requiring the derivation "
                    "to restart at RR1."
                ),
            },
        ],
    }

    # --------------------------------------------------
    # Integrity checks
    # --------------------------------------------------

    if len(changes) != 6:
        raise ValueError(
            "Expected exactly six changes."
        )

    change_ids = [
        item["change_id"]
        for item in changes
    ]

    if len(set(change_ids)) != 6:
        raise ValueError(
            "Duplicate change identifiers."
        )

    gt_ids = [
        item["change_id"]
        for item in ground_truth["scenarios"]
    ]

    if set(change_ids) != set(gt_ids):
        raise ValueError(
            "Change/ground-truth identifier mismatch."
        )

    expected_distribution = {
        "NONE": 1,
        "REVALIDATE": 3,
        "REDERIVE": 2,
    }

    actual_distribution = {}

    for scenario in ground_truth["scenarios"]:
        decision = scenario[
            "expected_decision"
        ]

        actual_distribution[
            decision
        ] = (
            actual_distribution.get(
                decision,
                0,
            )
            + 1
        )

    if (
        actual_distribution
        != expected_distribution
    ):
        raise ValueError(
            "Unexpected decision distribution: "
            f"{actual_distribution}"
        )

    # --------------------------------------------------
    # Write executor-visible changes
    # --------------------------------------------------

    CHANGES_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    for change in changes:
        path = (
            CHANGES_DIR
            / f"{change['change_id']}.json"
        )

        write_json(
            path,
            {
                "baseline_id": (
                    "mobstr-H1-revalidation-baseline-v1"
                ),
                "baseline_sha256":
                    baseline_hash,
                **change,
            },
        )

    # --------------------------------------------------
    # Write hidden evaluation ground truth
    # --------------------------------------------------

    write_json(
        GROUND_TRUTH_PATH,
        ground_truth,
    )

    # --------------------------------------------------
    # Summary
    # --------------------------------------------------

    print("=" * 70)
    print("MOBSTR EQ2 CHANGE SCENARIOS")
    print("=" * 70)

    print(
        f"Baseline SHA-256: {baseline_hash}"
    )

    print(
        f"Changes generated: {len(changes)}"
    )

    print(
        "Ground-truth distribution:"
    )

    for decision in [
        "NONE",
        "REVALIDATE",
        "REDERIVE",
    ]:
        print(
            f"  {decision}: "
            f"{actual_distribution[decision]}"
        )

    print()
    print(
        f"Changes directory: {CHANGES_DIR}"
    )

    print(
        f"Ground truth: {GROUND_TRUTH_PATH}"
    )


if __name__ == "__main__":
    main()

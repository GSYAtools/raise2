import hashlib
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

CONTEXT_PATH = (
    PROJECT_ROOT
    / "mobstr/work/raise2-output/H1/coding/context.txt"
)

CRDS_PATH = (
    PROJECT_ROOT
    / "mobstr/work/raise2-output/H1/coding/final-crds.tsv"
)

ORRS_PATH = (
    PROJECT_ROOT
    / "mobstr/work/raise2-output/H1/coding/orr-specification.tsv"
)

REQUIREMENTS_PATH = (
    PROJECT_ROOT
    / "mobstr/work/test-visible/H1/requirements.tsv"
)

ARCHITECTURE_PATH = (
    PROJECT_ROOT
    / "mobstr/work/executor-input/H1/architecture.json"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "mobstr/work/revalidation/H1/baseline.json"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            digest.update(chunk)

    return digest.hexdigest()


def require_file(path: Path) -> None:
    if not path.is_file():
        raise FileNotFoundError(
            f"Required source file does not exist: {path}"
        )


def main():

    # --------------------------------------------------
    # Verify source artefacts exist
    # --------------------------------------------------

    source_paths = [
        CONTEXT_PATH,
        CRDS_PATH,
        ORRS_PATH,
        REQUIREMENTS_PATH,
        ARCHITECTURE_PATH,
    ]

    for path in source_paths:
        require_file(path)

    # --------------------------------------------------
    # Frozen expert RR1 result
    # --------------------------------------------------

    evaluation_target = {
        "id": "T_H1",
        "statement": (
            "Determine whether the current operational "
            "situation requires a braking maneuver to "
            "avoid collision."
        ),
        "sources": [
            "SG-1",
            "H-1",
            "FR-7",
        ],
    }

    # --------------------------------------------------
    # Frozen expert RR2 result
    # --------------------------------------------------

    phenomenon = {
        "id": "P_H1",
        "statement": (
            "The collision-relevant spatial situation "
            "between the ego vehicle and obstacles on "
            "or near its trajectory."
        ),
        "scope": (
            "Concern-relevant properties of obstacles "
            "and their spatial relationship to the ego "
            "vehicle, including obstacle presence, "
            "source-required obstacle categories, and "
            "relative distance where these properties "
            "can change whether braking is required."
        ),
        "sources": [
            "H-1",
            "FR-7",
            "FR-7.2",
            "FR-7.2.1",
            "FR-7.2.2",
            "FR-7.2.4",
        ],
    }

    # --------------------------------------------------
    # Frozen expert RR3 results
    #
    # These values reproduce the expert derivation
    # frozen before downstream reference inspection.
    # --------------------------------------------------

    crds = [
        {
            "id": "H1-CRD1",
            "dimension": "Obstacle presence",
            "contrast_a": (
                "Collision-relevant obstacle present"
            ),
            "contrast_b": (
                "Collision-relevant obstacle absent"
            ),
            "sources": [
                "H-1",
                "FR-7",
                "FR-7.2",
                "FR-7.2.1",
            ],
            "rationale": (
                "Collapsing obstacle presence and "
                "absence removes information required "
                "to determine whether braking is "
                "required."
            ),
        },
        {
            "id": "H1-CRD2",
            "dimension": "Object category",
            "contrast_a": (
                "Vulnerable road user"
            ),
            "contrast_b": (
                "Other object"
            ),
            "sources": [
                "FR-7.2.2",
            ],
            "rationale": (
                "The visible source explicitly requires "
                "this category distinction within the "
                "obstacle information supporting the "
                "braking concern."
            ),
        },
        {
            "id": "H1-CRD3",
            "dimension": (
                "Obstacle distance relative to "
                "braking need"
            ),
            "contrast_a": (
                "Distance condition requires braking"
            ),
            "contrast_b": (
                "Distance condition does not require "
                "braking"
            ),
            "sources": [
                "H-1",
                "FR-7.1",
                "FR-7.2.4",
            ],
            "rationale": (
                "Relative distance can change whether "
                "braking is required; no numerical "
                "threshold is introduced because the "
                "dangerous-zone boundary is tbd and "
                "the 20 m value is scenario-specific."
            ),
        },
    ]

    # --------------------------------------------------
    # Frozen expert RR4 results + lifecycle extension
    # --------------------------------------------------

    orrs = [
        {
            "id": "H1-ORR1",
            "covered_crds": [
                "H1-CRD1"
            ],
            "preservation_obligation": (
                "The Observable Representation shall "
                "preserve whether a collision-relevant "
                "obstacle is present in the operational "
                "situation."
            ),
            "distinguishability_criterion": (
                "ObstaclePresent_R(x) != "
                "ObstaclePresent_R(y) for situations "
                "separated by H1-CRD1."
            ),
            "sources": [
                "H-1",
                "FR-7",
                "FR-7.2",
                "FR-7.2.1",
            ],
            "rationale": (
                "Without this distinction the "
                "representation cannot support "
                "evaluation of whether an "
                "obstacle-induced braking condition "
                "exists."
            ),
            "assumptions": [
                {
                    "id": "H1-A1",
                    "statement": (
                        "The obstacle-information basis "
                        "used by the Observable "
                        "Representation continues to "
                        "support distinguishing "
                        "collision-relevant obstacle "
                        "presence from absence."
                    ),
                    "sources": [
                        "FR-7.2",
                        "FR-7.2.1",
                    ],
                    "revalidation_conditions": [
                        {
                            "id": "H1-RC1",
                            "statement": (
                                "Revalidate if the "
                                "obstacle-detection "
                                "requirements, the "
                                "architectural "
                                "responsibility for "
                                "obstacle information, "
                                "or the information "
                                "supplied for representing "
                                "obstacle presence changes."
                            ),
                        }
                    ],
                }
            ],
        },

        {
            "id": "H1-ORR2",
            "covered_crds": [
                "H1-CRD2"
            ],
            "preservation_obligation": (
                "The Observable Representation shall "
                "preserve the source-required "
                "distinction between vulnerable road "
                "users and other objects when an "
                "obstacle is represented."
            ),
            "distinguishability_criterion": (
                "VRU_R(x) != VRU_R(y) for situations "
                "separated by H1-CRD2."
            ),
            "sources": [
                "FR-7.2.2",
            ],
            "rationale": (
                "The visible functional specification "
                "explicitly requires this category "
                "distinction within obstacle "
                "information supporting the braking "
                "concern."
            ),
            "assumptions": [
                {
                    "id": "H1-A2",
                    "statement": (
                        "The source-required distinction "
                        "between vulnerable road users "
                        "and other objects remains part "
                        "of the obstacle information "
                        "relevant to the concern."
                    ),
                    "sources": [
                        "FR-7.2.2",
                    ],
                    "revalidation_conditions": [
                        {
                            "id": "H1-RC2",
                            "statement": (
                                "Revalidate if FR-7.2.2, "
                                "the object-category "
                                "scheme, or the "
                                "architectural "
                                "responsibility or "
                                "information used to "
                                "represent object category "
                                "changes."
                            ),
                        }
                    ],
                }
            ],
        },

        {
            "id": "H1-ORR3",
            "covered_crds": [
                "H1-CRD3"
            ],
            "preservation_obligation": (
                "The Observable Representation shall "
                "preserve whether the spatial relation "
                "between the ego vehicle and an "
                "obstacle falls in a condition "
                "requiring braking or one not requiring "
                "braking."
            ),
            "distinguishability_criterion": (
                "BrakingRelevantDistanceClass_R(x) != "
                "BrakingRelevantDistanceClass_R(y) "
                "for situations separated by H1-CRD3."
            ),
            "sources": [
                "H-1",
                "FR-7.1",
                "FR-7.2.4",
            ],
            "rationale": (
                "Distance is explicitly required for "
                "the braking concern, but the "
                "dangerous-zone boundary is tbd; "
                "therefore the ORR preserves the "
                "concern-relative distance class "
                "without inventing a numerical "
                "threshold."
            ),
            "assumptions": [
                {
                    "id": "H1-A3",
                    "statement": (
                        "The representation continues "
                        "to receive information "
                        "sufficient to distinguish "
                        "braking-relevant spatial "
                        "conditions of obstacles "
                        "relative to the ego vehicle."
                    ),
                    "sources": [
                        "FR-7.1",
                        "FR-7.2.4",
                    ],
                    "revalidation_conditions": [
                        {
                            "id": "H1-RC3",
                            "statement": (
                                "Revalidate if the "
                                "distance or spatial-"
                                "information requirement, "
                                "the dangerous-zone "
                                "definition, or the "
                                "architectural "
                                "responsibility or "
                                "information used to "
                                "determine the ego-object "
                                "spatial relation changes."
                            ),
                        }
                    ],
                }
            ],
        },
    ]

    # --------------------------------------------------
    # Structural integrity checks
    # --------------------------------------------------

    crd_ids = {
        crd["id"]
        for crd in crds
    }

    if crd_ids != {
        "H1-CRD1",
        "H1-CRD2",
        "H1-CRD3",
    }:
        raise ValueError(
            "Unexpected CRD baseline."
        )

    orr_ids = {
        orr["id"]
        for orr in orrs
    }

    if orr_ids != {
        "H1-ORR1",
        "H1-ORR2",
        "H1-ORR3",
    }:
        raise ValueError(
            "Unexpected ORR baseline."
        )

    for orr in orrs:
        for crd_id in orr["covered_crds"]:
            if crd_id not in crd_ids:
                raise ValueError(
                    f"{orr['id']} references "
                    f"unknown CRD {crd_id}"
                )

    # --------------------------------------------------
    # Provenance
    # --------------------------------------------------

    provenance = {
        "context": {
            "path": (
                "mobstr/work/raise2-output/"
                "H1/coding/context.txt"
            ),
            "sha256":
                sha256_file(CONTEXT_PATH),
        },
        "expert_crds": {
            "path": (
                "mobstr/work/raise2-output/"
                "H1/coding/final-crds.tsv"
            ),
            "sha256":
                sha256_file(CRDS_PATH),
        },
        "expert_orrs": {
            "path": (
                "mobstr/work/raise2-output/"
                "H1/coding/orr-specification.tsv"
            ),
            "sha256":
                sha256_file(ORRS_PATH),
        },
        "requirements": {
            "path": (
                "mobstr/work/test-visible/"
                "H1/requirements.tsv"
            ),
            "sha256":
                sha256_file(REQUIREMENTS_PATH),
        },
        "architecture": {
            "path": (
                "mobstr/work/executor-input/"
                "H1/architecture.json"
            ),
            "sha256":
                sha256_file(ARCHITECTURE_PATH),
        },
    }

    baseline = {
        "baseline_id":
            "mobstr-H1-revalidation-baseline-v1",
        "concern_id":
            "H1",
        "evaluation_target":
            evaluation_target,
        "phenomenon_of_interest":
            phenomenon,
        "crds":
            crds,
        "orrs":
            orrs,
        "provenance":
            provenance,
    }

    # --------------------------------------------------
    # Write baseline
    # --------------------------------------------------

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            baseline,
            f,
            indent=2,
            ensure_ascii=False,
        )
        f.write("\n")

    assumption_count = sum(
        len(orr["assumptions"])
        for orr in orrs
    )

    rc_count = sum(
        len(
            assumption[
                "revalidation_conditions"
            ]
        )
        for orr in orrs
        for assumption in orr[
            "assumptions"
        ]
    )

    print("=" * 70)
    print("RAISE2 REVALIDATION BASELINE")
    print("=" * 70)

    print(
        f"Baseline: "
        f"{baseline['baseline_id']}"
    )
    print(f"CRDs: {len(crds)}")
    print(f"ORRs: {len(orrs)}")
    print(
        f"Assumptions: {assumption_count}"
    )
    print(
        f"Revalidation conditions: "
        f"{rc_count}"
    )
    print(
        f"Written to: {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()

import csv
import json
import re
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULTS_ROOT = PROJECT_ROOT / "raise2" / "results"

CRD_CATALOGUE = (
    RESULTS_ROOT
    / "mobstr-eq1-crds.tsv"
)

POI_RESULTS = (
    RESULTS_ROOT
    / "mobstr-eq1-poi-conformance.json"
)


def normalize(value: str) -> str:
    value = value.lower()
    value = value.replace("–", "-")
    value = value.replace("—", "-")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def contains_any(text: str, terms) -> bool:
    return any(term in text for term in terms)


def crd_text(row: dict) -> str:
    return normalize(
        " ".join(
            [
                row["dimension"],
                row["contrast_a"],
                row["contrast_b"],
            ]
        )
    )


def classify_presence(
    row: dict,
    concern: str,
):
    """
    Conservative candidate matcher for obstacle-presence
    reference distinctions.
    """

    text = crd_text(row)

    presence_terms = [
        "obstacle present",
        "obstacle absent",
        "obstacle presence",
        "presence of an obstacle",
        "no obstacle",
        "without an obstacle",
        "road user present",
        "road user absent",
        "presence of a road user",
        "no road user",
        "obstacle condition present",
        "obstacle condition absent",
    ]

    mechanism_terms = [
        "detectability",
        "detection status",
        "detection outcome",
        "detected in time",
        "not detected",
        "sensor",
        "camera",
        "lidar",
        "failure",
        "availability",
    ]

    braking_response_terms = [
        "braking occurs",
        "braking occurrence",
        "braking intent",
        "braking initiated",
        "braking initiation",
        "braking executed",
        "braking execution",
        "brake command",
        "braking response",
    ]

    has_presence = contains_any(
        text,
        presence_terms,
    )

    has_mechanism = contains_any(
        text,
        mechanism_terms,
    )

    has_braking_response = contains_any(
        text,
        braking_response_terms,
    )

    if (
        has_presence
        and not has_mechanism
        and not has_braking_response
    ):
        return "MATCH"

    if has_presence:
        return "REVIEW"

    return "NO_MATCH"


def classify_spatial(
    row: dict,
    concern: str,
):
    """
    Conservative candidate matcher for the
    braking-relevant spatial-relation references.
    """

    text = crd_text(row)

    spatial_terms = [
        "distance",
        "spatial",
        "proximity",
        "trajectory relation",
        "relative position",
        "position relative",
        "dangerous zone",
        "close to the trajectory",
        "on the trajectory",
    ]

    evaluative_terms_h1 = [
        "requires braking",
        "require braking",
        "braking required",
        "need for braking",
        "braking need",
        "does not require braking",
        "no braking required",
    ]

    evaluative_terms_h3 = [
        "justifies braking",
        "justify braking",
        "braking justified",
        "does not justify braking",
        "unjustified braking",
        "braking justification",
    ]

    mechanism_terms = [
        "detected in time",
        "detection timing",
        "braking initiation",
        "braking timing",
        "brake command",
        "braking execution",
        "controller",
        "sensor",
        "camera",
        "lidar",
    ]

    evaluative_terms = (
        evaluative_terms_h1
        if concern == "H1"
        else evaluative_terms_h3
    )

    has_spatial = contains_any(
        text,
        spatial_terms,
    )

    has_evaluative = contains_any(
        text,
        evaluative_terms,
    )

    has_mechanism = contains_any(
        text,
        mechanism_terms,
    )

    if (
        has_spatial
        and has_evaluative
        and not has_mechanism
    ):
        return "MATCH"

    if has_spatial:
        return "REVIEW"

    return "NO_MATCH"


def main():
    # --------------------------------------------------
    # PoI classifications
    # --------------------------------------------------

    poi_data = json.loads(
        POI_RESULTS.read_text(
            encoding="utf-8"
        )
    )

    poi_classification = {
        item["run_id"]:
            item["final_classification"]
        for item in poi_data["runs"]
    }

    # --------------------------------------------------
    # Load CRD catalogue
    # --------------------------------------------------

    with CRD_CATALOGUE.open(
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

    output_rows = []

    counters = Counter()

    for row in rows:
        concern = row["concern"]

        if concern == "H1":
            references = [
                (
                    "H1-REF1",
                    classify_presence,
                ),
                (
                    "H1-REF2",
                    classify_spatial,
                ),
            ]

        elif concern == "H3":
            references = [
                (
                    "H3-REF1",
                    classify_presence,
                ),
                (
                    "H3-REF2",
                    classify_spatial,
                ),
            ]

        else:
            raise ValueError(
                f"Unexpected concern: {concern}"
            )

        for reference_id, classifier in references:

            status = classifier(
                row,
                concern,
            )

            counters[
                (
                    concern,
                    reference_id,
                    status,
                )
            ] += 1

            output_rows.append(
                {
                    "concern":
                        concern,
                    "run_id":
                        row["run_id"],
                    "poi_classification":
                        poi_classification[
                            row["run_id"]
                        ],
                    "crd_id":
                        row["crd_id"],
                    "reference_id":
                        reference_id,
                    "status":
                        status,
                    "dimension":
                        row["dimension"],
                    "contrast_a":
                        row["contrast_a"],
                    "contrast_b":
                        row["contrast_b"],
                    "sources":
                        row["sources"],
                }
            )

    # --------------------------------------------------
    # Write candidate decisions
    # --------------------------------------------------

    output_path = (
        RESULTS_ROOT
        / "mobstr-eq1-reference-candidates.tsv"
    )

    fieldnames = [
        "concern",
        "run_id",
        "poi_classification",
        "crd_id",
        "reference_id",
        "status",
        "dimension",
        "contrast_a",
        "contrast_b",
        "sources",
    ]

    with output_path.open(
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
            output_rows
        )

    # --------------------------------------------------
    # Console summary
    # --------------------------------------------------

    print("=" * 70)
    print("EQ1 REFERENCE MATCHING CANDIDATES")
    print("=" * 70)

    for concern in ["H1", "H3"]:

        refs = (
            ["H1-REF1", "H1-REF2"]
            if concern == "H1"
            else ["H3-REF1", "H3-REF2"]
        )

        print()
        print(concern)

        for ref in refs:
            print(f"  {ref}")

            for status in [
                "MATCH",
                "REVIEW",
                "NO_MATCH",
            ]:
                print(
                    f"    {status:8s} "
                    f"{counters[(concern, ref, status)]}"
                )

    review_rows = [
        row
        for row in output_rows
        if row["status"] == "REVIEW"
    ]

    print()
    print(
        f"Total CRD-reference pairs: "
        f"{len(output_rows)}"
    )

    print(
        f"Manual review candidates: "
        f"{len(review_rows)}"
    )

    print(
        f"Written to: {output_path}"
    )


if __name__ == "__main__":
    main()

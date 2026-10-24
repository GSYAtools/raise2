import csv
import json
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULTS_ROOT = PROJECT_ROOT / "raise2" / "results"

EXPERIMENTS = {
    "H1": {
        "experiment_id": "mobstr-H1",
        "prefix": "H1-run",
        "runs": 30,
    },
    "H3": {
        "experiment_id": "mobstr-H3",
        "prefix": "H3-run",
        "runs": 30,
    },
}


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def normalize_text(value: str) -> str:
    """
    Conservative normalization for frequency analysis only.

    This does not establish semantic equivalence.
    """
    return " ".join(
        value.lower().strip().split()
    )


def normalize_sources(sources: list[str]) -> str:
    return ";".join(
        sorted(
            normalize_text(source)
            for source in sources
        )
    )


def main():
    rows = []

    dimension_counter = Counter()
    source_counter = Counter()
    dimension_source_counter = Counter()

    concern_crd_counts = {
        "H1": [],
        "H3": [],
    }

    for concern, config in EXPERIMENTS.items():
        experiment_dir = (
            RESULTS_ROOT
            / config["experiment_id"]
        )

        for number in range(
            1,
            config["runs"] + 1,
        ):
            run_id = (
                f"{config['prefix']}-{number:03d}"
            )

            derivation_path = (
                experiment_dir
                / run_id
                / "derivation.json"
            )

            derivation = load_json(
                derivation_path
            )

            distinctions = derivation[
                "distinctions"
            ]

            concern_crd_counts[
                concern
            ].append(
                len(distinctions)
            )

            for distinction in distinctions:
                dimension = distinction[
                    "dimension"
                ]

                sources = distinction[
                    "source"
                ]

                normalized_dimension = (
                    normalize_text(dimension)
                )

                normalized_source_set = (
                    normalize_sources(sources)
                )

                dimension_counter[
                    (
                        concern,
                        normalized_dimension,
                    )
                ] += 1

                source_counter[
                    (
                        concern,
                        normalized_source_set,
                    )
                ] += 1

                dimension_source_counter[
                    (
                        concern,
                        normalized_dimension,
                        normalized_source_set,
                    )
                ] += 1

                rows.append(
                    {
                        "concern": concern,
                        "run_id": run_id,
                        "crd_id": distinction[
                            "id"
                        ],
                        "dimension": dimension,
                        "normalized_dimension":
                            normalized_dimension,
                        "contrast_a": distinction[
                            "contrast_a"
                        ],
                        "contrast_b": distinction[
                            "contrast_b"
                        ],
                        "sources": ";".join(
                            sources
                        ),
                        "normalized_sources":
                            normalized_source_set,
                        "rationale": distinction[
                            "rationale"
                        ],
                    }
                )

    # --------------------------------------------------
    # Write complete CRD catalogue
    # --------------------------------------------------

    output_tsv = (
        RESULTS_ROOT
        / "mobstr-eq1-crds.tsv"
    )

    fieldnames = [
        "concern",
        "run_id",
        "crd_id",
        "dimension",
        "normalized_dimension",
        "contrast_a",
        "contrast_b",
        "sources",
        "normalized_sources",
        "rationale",
    ]

    with output_tsv.open(
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

    # --------------------------------------------------
    # Write deterministic frequency summary
    # --------------------------------------------------

    summary = {
        "total_crds": len(rows),
        "crds_by_concern": {
            concern: sum(counts)
            for concern, counts
            in concern_crd_counts.items()
        },
        "dimension_frequencies": [],
        "source_set_frequencies": [],
        "dimension_source_frequencies": [],
    }

    for (
        concern,
        dimension,
    ), count in sorted(
        dimension_counter.items()
    ):
        summary[
            "dimension_frequencies"
        ].append(
            {
                "concern": concern,
                "dimension": dimension,
                "count": count,
            }
        )

    for (
        concern,
        source_set,
    ), count in sorted(
        source_counter.items()
    ):
        summary[
            "source_set_frequencies"
        ].append(
            {
                "concern": concern,
                "source_set": source_set,
                "count": count,
            }
        )

    for (
        concern,
        dimension,
        source_set,
    ), count in sorted(
        dimension_source_counter.items()
    ):
        summary[
            "dimension_source_frequencies"
        ].append(
            {
                "concern": concern,
                "dimension": dimension,
                "source_set": source_set,
                "count": count,
            }
        )

    output_json = (
        RESULTS_ROOT
        / "mobstr-eq1-crd-summary.json"
    )

    with output_json.open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            summary,
            f,
            indent=2,
            ensure_ascii=False,
        )
        f.write("\n")

    # --------------------------------------------------
    # Console summary
    # --------------------------------------------------

    print(
        f"Total extracted CRDs: "
        f"{len(rows)}"
    )

    for concern in ["H1", "H3"]:
        print(
            f"{concern} CRDs: "
            f"{summary['crds_by_concern'][concern]}"
        )

    print()
    print("Most frequent dimensions:")

    ordered_dimensions = sorted(
        dimension_counter.items(),
        key=lambda item: (
            item[0][0],
            -item[1],
            item[0][1],
        ),
    )

    current_concern = None

    for (
        concern,
        dimension,
    ), count in ordered_dimensions:

        if concern != current_concern:
            print()
            print(concern)
            current_concern = concern

        print(
            f"  {count:>2}  {dimension}"
        )

    print()
    print(
        f"Catalogue written to: "
        f"{output_tsv}"
    )

    print(
        f"Summary written to: "
        f"{output_json}"
    )


if __name__ == "__main__":
    main()

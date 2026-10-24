import csv
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULTS_ROOT = PROJECT_ROOT / "raise2" / "results"

POI_RESULTS = (
    RESULTS_ROOT
    / "mobstr-eq1-poi-conformance.json"
)

EXPERIMENTS = {
    "H1": {
        "experiment_id": "mobstr-H1",
    },
    "H3": {
        "experiment_id": "mobstr-H3",
    },
}


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def normalize_text(value: str) -> str:
    return " ".join(
        value.lower().strip().split()
    )


def summarize(values):
    if not values:
        return {
            "n": 0,
            "min": None,
            "median": None,
            "mean": None,
            "max": None,
        }

    return {
        "n": len(values),
        "min": min(values),
        "median": statistics.median(values),
        "mean": statistics.mean(values),
        "max": max(values),
    }


def main():
    poi_data = load_json(POI_RESULTS)

    classifications = {
        record["run_id"]:
            record["final_classification"]
        for record in poi_data["runs"]
    }

    rows = []

    counts_by_group = defaultdict(list)
    dimensions_by_group = defaultdict(Counter)
    sources_by_group = defaultdict(Counter)

    for concern, config in EXPERIMENTS.items():

        experiment_dir = (
            RESULTS_ROOT
            / config["experiment_id"]
        )

        for run_dir in sorted(
            experiment_dir.glob(
                f"{concern}-run-*"
            )
        ):
            run_id = run_dir.name

            if run_id not in classifications:
                raise ValueError(
                    f"No PoI classification for {run_id}"
                )

            classification = (
                classifications[run_id]
            )

            derivation = load_json(
                run_dir / "derivation.json"
            )

            distinctions = derivation[
                "distinctions"
            ]

            crd_count = len(distinctions)

            group = (
                concern,
                classification,
            )

            counts_by_group[
                group
            ].append(crd_count)

            for distinction in distinctions:

                dimension = normalize_text(
                    distinction["dimension"]
                )

                source_set = ";".join(
                    sorted(
                        distinction["source"]
                    )
                )

                dimensions_by_group[
                    group
                ][dimension] += 1

                sources_by_group[
                    group
                ][source_set] += 1

                rows.append(
                    {
                        "concern": concern,
                        "run_id": run_id,
                        "poi_classification":
                            classification,
                        "crd_id":
                            distinction["id"],
                        "dimension":
                            distinction[
                                "dimension"
                            ],
                        "contrast_a":
                            distinction[
                                "contrast_a"
                            ],
                        "contrast_b":
                            distinction[
                                "contrast_b"
                            ],
                        "sources":
                            ";".join(
                                distinction[
                                    "source"
                                ]
                            ),
                        "rationale":
                            distinction[
                                "rationale"
                            ],
                    }
                )

    # --------------------------------------------------
    # Detailed catalogue
    # --------------------------------------------------

    output_tsv = (
        RESULTS_ROOT
        / "mobstr-eq1-poi-crd-relation.tsv"
    )

    fieldnames = [
        "concern",
        "run_id",
        "poi_classification",
        "crd_id",
        "dimension",
        "contrast_a",
        "contrast_b",
        "sources",
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
    # Aggregate JSON
    # --------------------------------------------------

    summary = {
        "groups": []
    }

    for group in sorted(
        counts_by_group.keys()
    ):
        concern, classification = group

        counts = counts_by_group[group]

        dimensions = (
            dimensions_by_group[group]
        )

        source_sets = (
            sources_by_group[group]
        )

        summary["groups"].append(
            {
                "concern": concern,
                "poi_classification":
                    classification,
                "crd_count_summary":
                    summarize(counts),
                "total_crds":
                    sum(counts),
                "dimension_frequencies": [
                    {
                        "dimension": dimension,
                        "count": count,
                    }
                    for dimension, count
                    in dimensions.most_common()
                ],
                "source_set_frequencies": [
                    {
                        "sources": sources,
                        "count": count,
                    }
                    for sources, count
                    in source_sets.most_common()
                ],
            }
        )

    output_json = (
        RESULTS_ROOT
        / "mobstr-eq1-poi-crd-relation.json"
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

    print("=" * 70)
    print("PoI CONFORMANCE x CRD ANALYSIS")
    print("=" * 70)

    for group in sorted(
        counts_by_group.keys()
    ):
        concern, classification = group

        counts = counts_by_group[group]
        stats = summarize(counts)

        print()
        print(
            f"{concern} / {classification}"
        )

        print(
            f"  Runs:       {stats['n']}"
        )

        print(
            f"  Total CRDs: {sum(counts)}"
        )

        print(
            "  CRDs/run:   "
            f"min={stats['min']}, "
            f"median={stats['median']}, "
            f"mean={stats['mean']:.2f}, "
            f"max={stats['max']}"
        )

        print(
            "  Most frequent dimensions:"
        )

        for (
            dimension,
            count,
        ) in dimensions_by_group[
            group
        ].most_common(10):

            print(
                f"    {count:>2}  "
                f"{dimension}"
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

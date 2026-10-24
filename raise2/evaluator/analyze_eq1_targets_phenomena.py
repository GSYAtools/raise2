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
    Conservative lexical normalization only.

    No semantic equivalence is inferred.
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

    target_statement_counter = Counter()
    target_source_counter = Counter()

    phenomenon_statement_counter = Counter()
    phenomenon_scope_counter = Counter()
    phenomenon_source_counter = Counter()

    target_phenomenon_counter = Counter()

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

            target = derivation[
                "evaluation_target"
            ]

            phenomenon = derivation[
                "phenomenon_of_interest"
            ]

            target_statement = normalize_text(
                target["statement"]
            )

            target_sources = normalize_sources(
                target["source"]
            )

            phenomenon_statement = normalize_text(
                phenomenon["statement"]
            )

            phenomenon_scope = normalize_text(
                phenomenon["scope"]
            )

            phenomenon_sources = normalize_sources(
                phenomenon["source"]
            )

            target_statement_counter[
                (
                    concern,
                    target_statement,
                )
            ] += 1

            target_source_counter[
                (
                    concern,
                    target_sources,
                )
            ] += 1

            phenomenon_statement_counter[
                (
                    concern,
                    phenomenon_statement,
                )
            ] += 1

            phenomenon_scope_counter[
                (
                    concern,
                    phenomenon_scope,
                )
            ] += 1

            phenomenon_source_counter[
                (
                    concern,
                    phenomenon_sources,
                )
            ] += 1

            target_phenomenon_counter[
                (
                    concern,
                    target_statement,
                    phenomenon_statement,
                )
            ] += 1

            rows.append(
                {
                    "concern": concern,
                    "run_id": run_id,

                    "target_id": target["id"],
                    "target_statement":
                        target["statement"],
                    "target_sources":
                        ";".join(target["source"]),
                    "target_rationale":
                        target["rationale"],

                    "phenomenon_id":
                        phenomenon["id"],
                    "phenomenon_statement":
                        phenomenon["statement"],
                    "phenomenon_scope":
                        phenomenon["scope"],
                    "phenomenon_sources":
                        ";".join(
                            phenomenon["source"]
                        ),
                    "phenomenon_rationale":
                        phenomenon["rationale"],

                    "crd_count":
                        len(
                            derivation[
                                "distinctions"
                            ]
                        ),
                    "orr_count":
                        len(
                            derivation[
                                "orrs"
                            ]
                        ),
                }
            )

    # --------------------------------------------------
    # Complete catalogue
    # --------------------------------------------------

    output_tsv = (
        RESULTS_ROOT
        / "mobstr-eq1-targets-phenomena.tsv"
    )

    fieldnames = [
        "concern",
        "run_id",
        "target_id",
        "target_statement",
        "target_sources",
        "target_rationale",
        "phenomenon_id",
        "phenomenon_statement",
        "phenomenon_scope",
        "phenomenon_sources",
        "phenomenon_rationale",
        "crd_count",
        "orr_count",
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
    # JSON summary
    # --------------------------------------------------

    summary = {
        "runs": len(rows),
        "target_statement_frequencies": [],
        "target_source_frequencies": [],
        "phenomenon_statement_frequencies": [],
        "phenomenon_scope_frequencies": [],
        "phenomenon_source_frequencies": [],
        "target_phenomenon_frequencies": [],
    }

    for (
        concern,
        statement,
    ), count in sorted(
        target_statement_counter.items()
    ):
        summary[
            "target_statement_frequencies"
        ].append(
            {
                "concern": concern,
                "statement": statement,
                "count": count,
            }
        )

    for (
        concern,
        sources,
    ), count in sorted(
        target_source_counter.items()
    ):
        summary[
            "target_source_frequencies"
        ].append(
            {
                "concern": concern,
                "sources": sources,
                "count": count,
            }
        )

    for (
        concern,
        statement,
    ), count in sorted(
        phenomenon_statement_counter.items()
    ):
        summary[
            "phenomenon_statement_frequencies"
        ].append(
            {
                "concern": concern,
                "statement": statement,
                "count": count,
            }
        )

    for (
        concern,
        scope,
    ), count in sorted(
        phenomenon_scope_counter.items()
    ):
        summary[
            "phenomenon_scope_frequencies"
        ].append(
            {
                "concern": concern,
                "scope": scope,
                "count": count,
            }
        )

    for (
        concern,
        sources,
    ), count in sorted(
        phenomenon_source_counter.items()
    ):
        summary[
            "phenomenon_source_frequencies"
        ].append(
            {
                "concern": concern,
                "sources": sources,
                "count": count,
            }
        )

    for (
        concern,
        target_statement,
        phenomenon_statement,
    ), count in sorted(
        target_phenomenon_counter.items()
    ):
        summary[
            "target_phenomenon_frequencies"
        ].append(
            {
                "concern": concern,
                "target_statement":
                    target_statement,
                "phenomenon_statement":
                    phenomenon_statement,
                "count": count,
            }
        )

    output_json = (
        RESULTS_ROOT
        / "mobstr-eq1-targets-phenomena-summary.json"
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
    # Console output
    # --------------------------------------------------

    print(
        f"Total runs analysed: {len(rows)}"
    )

    for concern in ["H1", "H3"]:
        print()
        print("=" * 70)
        print(concern)
        print("=" * 70)

        print()
        print("Evaluation Target statements:")

        target_items = [
            (
                statement,
                count,
            )
            for (
                item_concern,
                statement,
            ), count
            in target_statement_counter.items()
            if item_concern == concern
        ]

        target_items.sort(
            key=lambda item: (
                -item[1],
                item[0],
            )
        )

        for statement, count in target_items:
            print(
                f"  {count:>2}  {statement}"
            )

        print()
        print("Phenomenon statements:")

        phenomenon_items = [
            (
                statement,
                count,
            )
            for (
                item_concern,
                statement,
            ), count
            in phenomenon_statement_counter.items()
            if item_concern == concern
        ]

        phenomenon_items.sort(
            key=lambda item: (
                -item[1],
                item[0],
            )
        )

        for statement, count in phenomenon_items:
            print(
                f"  {count:>2}  {statement}"
            )

        print()
        print("Phenomenon scopes:")

        scope_items = [
            (
                scope,
                count,
            )
            for (
                item_concern,
                scope,
            ), count
            in phenomenon_scope_counter.items()
            if item_concern == concern
        ]

        scope_items.sort(
            key=lambda item: (
                -item[1],
                item[0],
            )
        )

        for scope, count in scope_items:
            print(
                f"  {count:>2}  {scope}"
            )

    print()
    print(
        f"Catalogue written to: {output_tsv}"
    )

    print(
        f"Summary written to: {output_json}"
    )


if __name__ == "__main__":
    main()

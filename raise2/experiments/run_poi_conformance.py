import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

EXPERIMENTS = [
    {
        "concern": "H1",
        "prefix": "H1-run",
        "runs": 30,
    },
    {
        "concern": "H3",
        "prefix": "H3-run",
        "runs": 30,
    },
]

ASSESSMENTS = [
    "judge-01",
    "judge-02",
    "judge-03",
]


def assessment_exists(
    concern: str,
    run_id: str,
    assessment_id: str,
) -> bool:

    experiment_id = (
        "mobstr-H1"
        if concern == "H1"
        else "mobstr-H3"
    )

    assessment_dir = (
        PROJECT_ROOT
        / "raise2"
        / "results"
        / experiment_id
        / run_id
        / "poi-conformance"
        / assessment_id
    )

    return assessment_dir.exists()


def main():
    completed = 0
    failed = 0
    skipped = 0

    for experiment in EXPERIMENTS:
        concern = experiment["concern"]

        for number in range(
            1,
            experiment["runs"] + 1,
        ):
            run_id = (
                f"{experiment['prefix']}-{number:03d}"
            )

            for assessment_id in ASSESSMENTS:

                if assessment_exists(
                    concern,
                    run_id,
                    assessment_id,
                ):
                    print(
                        f"[SKIP] {run_id} "
                        f"{assessment_id}"
                    )
                    skipped += 1
                    continue

                print()
                print("=" * 70)
                print(
                    f"Starting {run_id} "
                    f"{assessment_id}"
                )
                print("=" * 70)

                command = [
                    sys.executable,
                    "-m",
                    (
                        "raise2.evaluator."
                        "poi_conformance_evaluator"
                    ),
                    "--concern",
                    concern,
                    "--run-id",
                    run_id,
                    "--assessment-id",
                    assessment_id,
                ]

                result = subprocess.run(
                    command,
                    cwd=PROJECT_ROOT,
                )

                if result.returncode == 0:
                    completed += 1
                    print(
                        f"[PASS] {run_id} "
                        f"{assessment_id}"
                    )
                else:
                    failed += 1
                    print(
                        f"[FAIL] {run_id} "
                        f"{assessment_id} "
                        f"(exit={result.returncode})"
                    )

                    # No automatic retry.
                    # Failed assessments remain part
                    # of the experimental record.

    print()
    print("=" * 70)
    print("PoI conformance assessment completed")
    print(f"Completed: {completed}")
    print(f"Failed:    {failed}")
    print(f"Skipped:   {skipped}")
    print("=" * 70)


if __name__ == "__main__":
    main()

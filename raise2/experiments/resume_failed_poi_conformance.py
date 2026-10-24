import json
import subprocess
import sys
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

ASSESSMENTS = [
    "judge-01",
    "judge-02",
    "judge-03",
]


def load_json(path: Path) -> dict:
    with path.open(
        "r",
        encoding="utf-8",
    ) as f:
        return json.load(f)


def has_valid_resume(
    run_dir: Path,
    original_assessment_id: str,
) -> bool:
    """
    Return True when a valid non-destructive
    recovery already exists for the original
    assessment.

    Example:
        judge-02
        -> judge-02-resume-01
        -> judge-02-resume-02
        -> ...
    """

    poi_dir = (
        run_dir
        / "poi-conformance"
    )

    pattern = (
        f"{original_assessment_id}"
        "-resume-*"
    )

    for resume_dir in sorted(
        poi_dir.glob(pattern)
    ):
        metadata_path = (
            resume_dir
            / "metadata.json"
        )

        if not metadata_path.is_file():
            continue

        metadata = load_json(
            metadata_path
        )

        if (
            metadata.get("status")
            == "completed_valid"
        ):
            return True

    return False


def find_failed_assessments():
    """
    Return original API failures that do not
    already have a valid recovery.

    Original failed assessments remain preserved
    as part of the experimental record.
    """

    failed = []

    for experiment in EXPERIMENTS:
        concern = experiment["concern"]
        experiment_id = (
            experiment["experiment_id"]
        )

        for number in range(
            1,
            experiment["runs"] + 1,
        ):
            run_id = (
                f"{experiment['prefix']}"
                f"-{number:03d}"
            )

            run_dir = (
                RESULTS_ROOT
                / experiment_id
                / run_id
            )

            for assessment_id in ASSESSMENTS:
                assessment_dir = (
                    run_dir
                    / "poi-conformance"
                    / assessment_id
                )

                metadata_path = (
                    assessment_dir
                    / "metadata.json"
                )

                if not metadata_path.is_file():
                    continue

                metadata = load_json(
                    metadata_path
                )

                if (
                    metadata.get("status")
                    != "api_error"
                ):
                    continue

                if has_valid_resume(
                    run_dir,
                    assessment_id,
                ):
                    continue

                failed.append(
                    {
                        "concern":
                            concern,
                        "experiment_id":
                            experiment_id,
                        "run_id":
                            run_id,
                        "assessment_id":
                            assessment_id,
                        "assessment_dir":
                            assessment_dir,
                    }
                )

    return failed


def next_resume_id(
    run_dir: Path,
    original_assessment_id: str,
) -> str:
    """
    Generate a non-destructive resume identifier.

    Example:
        judge-02
        -> judge-02-resume-01
    """

    counter = 1

    while True:
        candidate = (
            f"{original_assessment_id}"
            f"-resume-{counter:02d}"
        )

        candidate_dir = (
            run_dir
            / "poi-conformance"
            / candidate
        )

        if not candidate_dir.exists():
            return candidate

        counter += 1


def main():
    failed = find_failed_assessments()

    print(
        "Unrecovered API assessments found: "
        f"{len(failed)}"
    )

    if not failed:
        print(
            "Nothing to resume."
        )
        return

    completed = 0
    resume_failed = 0

    for item in failed:
        run_dir = (
            RESULTS_ROOT
            / item["experiment_id"]
            / item["run_id"]
        )

        resume_id = next_resume_id(
            run_dir,
            item["assessment_id"],
        )

        print()
        print("=" * 70)
        print(
            f"Resuming {item['run_id']} "
            f"{item['assessment_id']} "
            f"as {resume_id}"
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
            item["concern"],
            "--run-id",
            item["run_id"],
            "--assessment-id",
            resume_id,
        ]

        result = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
        )

        if result.returncode == 0:
            completed += 1

            print(
                f"[PASS] {item['run_id']} "
                f"{resume_id}"
            )
        else:
            resume_failed += 1

            print(
                f"[FAIL] {item['run_id']} "
                f"{resume_id} "
                f"(exit={result.returncode})"
            )

            # Do not retry automatically.
            # A failed recovery remains part
            # of the experimental record.

    print()
    print("=" * 70)
    print(
        "PoI conformance recovery completed"
    )
    print(
        f"Recovered: {completed}"
    )
    print(
        f"Failed:    {resume_failed}"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()

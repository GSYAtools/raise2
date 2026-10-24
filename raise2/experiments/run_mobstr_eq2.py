import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

CHANGES_DIR = (
    PROJECT_ROOT
    / "mobstr/work/revalidation/H1/changes"
)

RESULTS_ROOT = (
    PROJECT_ROOT
    / "raise2/results/mobstr-eq2"
)

CHANGES = [
    "delta-01",
    "delta-02",
    "delta-03",
    "delta-04",
    "delta-05",
    "delta-06",
]

RUNS_PER_CHANGE = 10


def run_exists(
    change_id: str,
    run_id: str,
) -> bool:

    run_dir = (
        RESULTS_ROOT
        / change_id
        / run_id
    )

    return run_dir.exists()


def main():
    completed = 0
    failed = 0
    skipped = 0

    for change_id in CHANGES:

        change_path = (
            CHANGES_DIR
            / f"{change_id}.json"
        )

        if not change_path.is_file():
            raise FileNotFoundError(
                f"Missing change: {change_path}"
            )

        for number in range(
            1,
            RUNS_PER_CHANGE + 1,
        ):
            run_id = (
                f"run-{number:03d}"
            )

            if run_exists(
                change_id,
                run_id,
            ):
                print(
                    f"[SKIP] {change_id} "
                    f"{run_id}: already exists"
                )
                skipped += 1
                continue

            print()
            print("=" * 70)
            print(
                f"Starting {change_id} "
                f"{run_id}"
            )
            print("=" * 70)

            command = [
                sys.executable,
                "-m",
                "raise2.executor.rv_executor",
                str(change_path),
                "--run-id",
                run_id,
            ]

            result = subprocess.run(
                command,
                cwd=PROJECT_ROOT,
            )

            if result.returncode == 0:
                completed += 1
                print(
                    f"[PASS] {change_id} "
                    f"{run_id}"
                )
            else:
                failed += 1
                print(
                    f"[FAIL] {change_id} "
                    f"{run_id} "
                    f"(exit={result.returncode})"
                )

                # No automatic retries.
                # Failures remain part of the record.

    print()
    print("=" * 70)
    print("MobSTr EQ2 execution completed")
    print(f"Completed: {completed}")
    print(f"Failed:    {failed}")
    print(f"Skipped:   {skipped}")
    print("=" * 70)


if __name__ == "__main__":
    main()

import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

EXPERIMENTS = [
    {
        "manifest": "raise2/experiments/mobstr/H1.json",
        "prefix": "H1-run",
        "start": 2,
        "end": 30,
    },
    {
        "manifest": "raise2/experiments/mobstr/H3.json",
        "prefix": "H3-run",
        "start": 1,
        "end": 30,
    },
]


def run_exists(experiment_id: str, run_id: str) -> bool:
    run_dir = (
        PROJECT_ROOT
        / "raise2"
        / "results"
        / experiment_id
        / run_id
    )

    return run_dir.exists()


def main():
    completed = 0
    failed = 0
    skipped = 0

    for experiment in EXPERIMENTS:
        manifest = (
            PROJECT_ROOT
            / experiment["manifest"]
        )

        experiment_id = (
            "mobstr-H1"
            if experiment["prefix"] == "H1-run"
            else "mobstr-H3"
        )

        for number in range(
            experiment["start"],
            experiment["end"] + 1,
        ):
            run_id = (
                f"{experiment['prefix']}-{number:03d}"
            )

            if run_exists(experiment_id, run_id):
                print(
                    f"[SKIP] {run_id}: "
                    "result directory already exists"
                )
                skipped += 1
                continue

            print()
            print("=" * 70)
            print(f"Starting {run_id}")
            print("=" * 70)

            command = [
                sys.executable,
                "-m",
                "raise2.executor.rr_executor",
                str(manifest),
                "--run-id",
                run_id,
                "--root",
                str(PROJECT_ROOT),
            ]

            result = subprocess.run(
                command,
                cwd=PROJECT_ROOT,
            )

            if result.returncode == 0:
                completed += 1
                print(f"[PASS] {run_id}")
            else:
                failed += 1
                print(
                    f"[FAIL] {run_id} "
                    f"(exit={result.returncode})"
                )

                # Do not retry automatically.
                # A failed execution remains part of
                # the experimental record.

    print()
    print("=" * 70)
    print("MobSTr EQ1 execution completed")
    print(f"Completed: {completed}")
    print(f"Failed:    {failed}")
    print(f"Skipped:   {skipped}")
    print("=" * 70)


if __name__ == "__main__":
    main()

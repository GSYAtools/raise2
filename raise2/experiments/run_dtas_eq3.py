import csv
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DTAS_ROOT = (
    PROJECT_ROOT
    / "dtas/work/source/dTAS"
)

TAS_GUI = (
    DTAS_ROOT
    / "TAS_gui"
)

HARNESS_DIR = (
    PROJECT_ROOT
    / "dtas/work/eq3-harness"
)

RESULTS_ROOT = (
    PROJECT_ROOT
    / "raise2/results/dtas-eq3-a"
)

RUNS = 30
EXPECTED_CYCLES = 20


CLASSPATH = ":".join(
    [
        str(HARNESS_DIR),
        str(HARNESS_DIR / "shim-bin"),
        str(
            DTAS_ROOT
            / "TeleAssistanceSystem/bin"
        ),
        str(
            DTAS_ROOT
            / "ResearchServicePlatform/bin"
        ),
        str(
            DTAS_ROOT
            / "TeleAssistanceSystem/libs/"
            "antlrworks-1.5.2-complete.jar"
        ),
        str(
            DTAS_ROOT
            / "TeleAssistanceSystem/libs/"
            "javax.jms-api-2.0.jar"
        ),
        str(
            DTAS_ROOT
            / "TeleAssistanceSystem/libs/"
            "xstream-1.5.0.jar"
        ),
    ]
)


def validate_csv(path: Path) -> tuple[bool, str]:

    if not path.is_file():
        return False, "CSV not created"

    with path.open(
        encoding="utf-8",
        newline="",
    ) as f:
        rows = list(
            csv.DictReader(f)
        )

    if len(rows) != EXPECTED_CYCLES:
        return (
            False,
            "expected "
            f"{EXPECTED_CYCLES} cycles, "
            f"found {len(rows)}",
        )

    expected_cycles = set(
        range(
            1,
            EXPECTED_CYCLES + 1,
        )
    )

    try:
        actual_cycles = {
            int(row["cycle"])
            for row in rows
        }
    except Exception as exc:
        return (
            False,
            f"invalid cycle data: {exc}",
        )

    if actual_cycles != expected_cycles:
        return (
            False,
            "cycle set mismatch",
        )

    for row in rows:

        if row["orr_preserved"] not in {
            "true",
            "false",
        }:
            return (
                False,
                "invalid orr_preserved value",
            )

        if row["violation_type"] not in {
            "NONE",
            "MISSED_VIOLATION",
            "FALSE_VIOLATION",
        }:
            return (
                False,
                "invalid violation_type",
            )

        real_state = row[
            "real_goal_state"
        ]

        represented_state = row[
            "represented_goal_state"
        ]

        preserved = (
            row["orr_preserved"]
            == "true"
        )

        if (
            preserved
            != (
                real_state
                == represented_state
            )
        ):
            return (
                False,
                "ORR consistency failure",
            )

    return True, "valid"


def main():

    RESULTS_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    completed = 0
    failed = 0
    skipped = 0

    for number in range(
        1,
        RUNS + 1,
    ):

        run_id = (
            f"run-{number:03d}"
        )

        run_dir = (
            RESULTS_ROOT
            / run_id
        )

        csv_path = (
            run_dir
            / "observations.csv"
        )

        log_path = (
            run_dir
            / "execution.log"
        )

        if csv_path.is_file():

            valid, reason = (
                validate_csv(
                    csv_path
                )
            )

            if valid:
                print(
                    f"[SKIP] {run_id}: "
                    "valid result exists"
                )
                skipped += 1
                continue

            print(
                f"[FAIL] {run_id}: "
                "existing invalid result: "
                f"{reason}"
            )

            failed += 1
            continue

        run_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        print()
        print("=" * 70)
        print(
            f"Starting dTAS EQ3-A "
            f"{run_id}"
        )
        print("=" * 70)

        command = [
            "java",
            "-cp",
            CLASSPATH,
            "DTASEQ3Harness",
            str(DTAS_ROOT),
            run_id,
            str(csv_path),
        ]

        with log_path.open(
            "w",
            encoding="utf-8",
        ) as log:

            result = subprocess.run(
                command,
                cwd=TAS_GUI,
                stdout=log,
                stderr=subprocess.STDOUT,
            )

        if result.returncode != 0:

            print(
                f"[FAIL] {run_id}: "
                "Java exit code "
                f"{result.returncode}"
            )

            print(
                f"       log: {log_path}"
            )

            failed += 1
            continue

        valid, reason = validate_csv(
            csv_path
        )

        if not valid:

            print(
                f"[FAIL] {run_id}: "
                f"{reason}"
            )

            failed += 1
            continue

        with csv_path.open(
            encoding="utf-8",
            newline="",
        ) as f:

            rows = list(
                csv.DictReader(f)
            )

        violations = sum(
            row["orr_preserved"]
            == "false"
            for row in rows
        )

        print(
            f"[PASS] {run_id}: "
            f"{EXPECTED_CYCLES} cycles, "
            f"{violations} ORR violations"
        )

        completed += 1

    print()
    print("=" * 70)
    print(
        "dTAS EQ3-A execution completed"
    )
    print(
        f"Completed: {completed}"
    )
    print(
        f"Failed:    {failed}"
    )
    print(
        f"Skipped:   {skipped}"
    )
    print("=" * 70)

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()


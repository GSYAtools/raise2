import csv
import json
import shutil
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

EQ3B_ROOT = (
    PROJECT_ROOT
    / "dtas/work/eq3-b"
)

HARNESS_BIN = (
    EQ3B_ROOT
    / "bin"
)

SHIM_BIN = (
    PROJECT_ROOT
    / "dtas/work/eq3-harness/shim-bin"
)

CONDITIONS_DIR = (
    EQ3B_ROOT
    / "conditions"
)

MANIFEST_PATH = (
    EQ3B_ROOT
    / "manifest.json"
)

EQ3A_RESULTS = (
    PROJECT_ROOT
    / "raise2/results/dtas-eq3-a"
)

RESULTS_ROOT = (
    PROJECT_ROOT
    / "raise2/results/dtas-eq3-b"
)

CONDITIONS = [
    "mfd-0005",
    "mfd-0010",
    "mfd-0020",
    "mfd-0040",
]

RUNS_PER_CONDITION = 10
EXPECTED_CYCLES = 20


CLASSPATH = ":".join(
    [
        str(HARNESS_BIN),
        str(SHIM_BIN),
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


def load_manifest():
    with MANIFEST_PATH.open(
        encoding="utf-8"
    ) as f:
        return json.load(f)


def validate_csv(
    path: Path,
    expected_run_id: str,
):
    if not path.is_file():
        return False, "CSV not found"

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
            f"expected {EXPECTED_CYCLES} "
            f"cycles, found {len(rows)}",
        )

    expected_cycles = list(
        range(
            1,
            EXPECTED_CYCLES + 1,
        )
    )

    try:
        actual_cycles = [
            int(row["cycle"])
            for row in rows
        ]
    except Exception as exc:
        return (
            False,
            f"invalid cycle data: {exc}",
        )

    if actual_cycles != expected_cycles:
        return (
            False,
            "cycle sequence mismatch",
        )

    for row in rows:

        if (
            row["run_id"]
            != expected_run_id
        ):
            return (
                False,
                "run_id mismatch",
            )

        if row["orr_preserved"] not in {
            "true",
            "false",
        }:
            return (
                False,
                "invalid orr_preserved",
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

        real_state = (
            row["real_goal_state"]
        )

        represented_state = (
            row[
                "represented_goal_state"
            ]
        )

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


def reuse_baseline():
    """
    Copy EQ3-A runs 001-010 into the
    uniform EQ3-B result structure.

    No new dTAS execution is performed.
    """

    condition = "mfd-0005"

    print()
    print("=" * 70)
    print(
        "Reusing frozen EQ3-A baseline"
    )
    print("=" * 70)

    reused = 0

    for number in range(
        1,
        RUNS_PER_CONDITION + 1,
    ):

        run_id = (
            f"run-{number:03d}"
        )

        source = (
            EQ3A_RESULTS
            / run_id
            / "observations.csv"
        )

        destination_dir = (
            RESULTS_ROOT
            / condition
            / run_id
        )

        destination = (
            destination_dir
            / "observations.csv"
        )

        valid, reason = validate_csv(
            source,
            run_id,
        )

        if not valid:
            raise RuntimeError(
                f"Frozen EQ3-A "
                f"{run_id} invalid: "
                f"{reason}"
            )

        destination_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        if destination.exists():

            valid, reason = (
                validate_csv(
                    destination,
                    run_id,
                )
            )

            if not valid:
                raise RuntimeError(
                    "Existing baseline copy "
                    f"{run_id} invalid: "
                    f"{reason}"
                )

            print(
                f"[SKIP] {condition} "
                f"{run_id}: already reused"
            )

            continue

        shutil.copy2(
            source,
            destination,
        )

        provenance = {
            "condition_id":
                condition,
            "run_id":
                run_id,
            "source":
                str(
                    source.relative_to(
                        PROJECT_ROOT
                    )
                ),
            "mode":
                "reused_from_eq3_a",
        }

        with (
            destination_dir
            / "provenance.json"
        ).open(
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(
                provenance,
                f,
                indent=2,
            )
            f.write("\n")

        print(
            f"[REUSE] {condition} "
            f"{run_id}"
        )

        reused += 1

    return reused


def execute_condition(
    condition: str,
):

    entity_xml = (
        CONDITIONS_DIR
        / f"{condition}.xml"
    )

    if not entity_xml.is_file():
        raise FileNotFoundError(
            f"Condition XML missing: "
            f"{entity_xml}"
        )

    completed = 0
    failed = 0
    skipped = 0

    for number in range(
        1,
        RUNS_PER_CONDITION + 1,
    ):

        run_id = (
            f"run-{number:03d}"
        )

        run_dir = (
            RESULTS_ROOT
            / condition
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
                    csv_path,
                    run_id,
                )
            )

            if valid:
                print(
                    f"[SKIP] {condition} "
                    f"{run_id}"
                )
                skipped += 1
                continue

            print(
                f"[FAIL] {condition} "
                f"{run_id}: existing "
                f"invalid result: {reason}"
            )

            failed += 1
            continue

        run_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        print()
        print("-" * 70)
        print(
            f"Starting {condition} "
            f"{run_id}"
        )
        print("-" * 70)

        command = [
            "java",
            "-cp",
            CLASSPATH,
            "DTASEQ3BHarness",
            str(DTAS_ROOT),
            run_id,
            str(csv_path),
            str(entity_xml),
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
                f"[FAIL] {condition} "
                f"{run_id}: Java "
                f"exit={result.returncode}"
            )

            print(
                f"       {log_path}"
            )

            failed += 1
            continue

        valid, reason = validate_csv(
            csv_path,
            run_id,
        )

        if not valid:

            print(
                f"[FAIL] {condition} "
                f"{run_id}: {reason}"
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
            f"[PASS] {condition} "
            f"{run_id}: "
            f"{violations} "
            "ORR violations"
        )

        completed += 1

    return (
        completed,
        failed,
        skipped,
    )


def main():

    manifest = load_manifest()

    if (
        manifest.get("study")
        != "dTAS EQ3-B"
    ):
        raise ValueError(
            "Unexpected EQ3-B manifest."
        )

    RESULTS_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    reused = reuse_baseline()

    completed = 0
    failed = 0
    skipped = 0

    # Baseline mfd-0005 is reused.
    for condition in CONDITIONS[1:]:

        print()
        print("=" * 70)
        print(
            f"Condition: {condition}"
        )
        print("=" * 70)

        c, f, s = execute_condition(
            condition
        )

        completed += c
        failed += f
        skipped += s

    print()
    print("=" * 70)
    print(
        "dTAS EQ3-B execution completed"
    )
    print(
        f"Baseline reused: "
        f"{reused}"
    )
    print(
        f"New completed:   "
        f"{completed}"
    )
    print(
        f"Failed:          "
        f"{failed}"
    )
    print(
        f"Skipped new:     "
        f"{skipped}"
    )
    print("=" * 70)

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()

import hashlib
import json
import shutil
import subprocess
from pathlib import Path
import xml.etree.ElementTree as ET


PROJECT_ROOT = Path(__file__).resolve().parents[2]

# --------------------------------------------------
# Frozen / upstream inputs
# --------------------------------------------------

SOURCE_ZIP = (
    PROJECT_ROOT
    / "dtas/original/dtas-v1.0-source.zip"
)

SOURCE_ENTITY = (
    PROJECT_ROOT
    / "dtas/work/source/dTAS/TAS_gui/"
    "resources/files/entities/System Entity 1.xml"
)

EQ3A_HARNESS = (
    PROJECT_ROOT
    / "dtas/work/eq3-harness/"
    "DTASEQ3Harness.java"
)

SHIM_BIN = (
    PROJECT_ROOT
    / "dtas/work/eq3-harness/shim-bin"
)

DTAS_ROOT = (
    PROJECT_ROOT
    / "dtas/work/source/dTAS"
)

# --------------------------------------------------
# Generated EQ3-B workspace
# --------------------------------------------------

WORK_ROOT = (
    PROJECT_ROOT
    / "dtas/work/eq3-b"
)

CONDITIONS_DIR = (
    WORK_ROOT
    / "conditions"
)

HARNESS_SOURCE = (
    WORK_ROOT
    / "DTASEQ3BHarness.java"
)

HARNESS_BIN = (
    WORK_ROOT
    / "bin"
)

MANIFEST_PATH = (
    WORK_ROOT
    / "manifest.json"
)

CONDITION_SPEC_PATH = (
    WORK_ROOT
    / "conditions.json"
)

# --------------------------------------------------
# Frozen upstream hashes
# --------------------------------------------------

EXPECTED_SOURCE_ZIP_SHA256 = (
    "155b2f935bd21d43631a4d7cf0c5801e"
    "323d8ba872b8f112139401996e84c522"
)

EXPECTED_EQ3A_HARNESS_SHA256 = (
    "c84f3652738de5b96fdb7dd47a6ed37"
    "e648824f77ba8830429c17e51c6d8692f"
)

# --------------------------------------------------
# Experimental design
# --------------------------------------------------

ORIGINAL_MIN_FAILURE_DELTA = 0.005
CONTROLLED_FAILURE_CHANGE = 0.005

CONDITIONS = [
    {
        "condition_id": "mfd-0005",
        "min_failure_delta": 0.005,
        "status": "original_baseline",
    },
    {
        "condition_id": "mfd-0010",
        "min_failure_delta": 0.010,
        "status": "controlled_degradation",
    },
    {
        "condition_id": "mfd-0020",
        "min_failure_delta": 0.020,
        "status": "controlled_degradation",
    },
    {
        "condition_id": "mfd-0040",
        "min_failure_delta": 0.040,
        "status": "controlled_degradation",
    },
]

RUNS_PER_CONDITION = 10
CYCLES_PER_RUN = 20


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as f:
        for chunk in iter(
            lambda: f.read(65536),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def require_file(path: Path) -> None:
    if not path.is_file():
        raise FileNotFoundError(
            f"Required file not found: {path}"
        )


def verify_frozen_inputs() -> None:

    require_file(SOURCE_ZIP)
    require_file(SOURCE_ENTITY)
    require_file(EQ3A_HARNESS)

    source_hash = sha256_file(
        SOURCE_ZIP
    )

    if (
        source_hash
        != EXPECTED_SOURCE_ZIP_SHA256
    ):
        raise ValueError(
            "dTAS source ZIP hash mismatch.\n"
            f"Expected: "
            f"{EXPECTED_SOURCE_ZIP_SHA256}\n"
            f"Actual:   {source_hash}"
        )

    harness_hash = sha256_file(
        EQ3A_HARNESS
    )

    if (
        harness_hash
        != EXPECTED_EQ3A_HARNESS_SHA256
    ):
        raise ValueError(
            "EQ3-A harness hash mismatch.\n"
            f"Expected: "
            f"{EXPECTED_EQ3A_HARNESS_SHA256}\n"
            f"Actual:   {harness_hash}"
        )


def verify_source_entity() -> dict:

    tree = ET.parse(
        SOURCE_ENTITY
    )

    root = tree.getroot()

    min_delta = root.find(
        "MonitorMinFailureDelta"
    )

    failure_change = root.find(
        "MonitorFailureChange"
    )

    if min_delta is None:
        raise ValueError(
            "Source entity has no "
            "MonitorMinFailureDelta."
        )

    if failure_change is None:
        raise ValueError(
            "Source entity has no "
            "MonitorFailureChange."
        )

    source_min_delta = float(
        min_delta.text
    )

    source_failure_change = float(
        failure_change.text
    )

    if (
        source_min_delta
        != ORIGINAL_MIN_FAILURE_DELTA
    ):
        raise ValueError(
            "Unexpected source "
            "MonitorMinFailureDelta: "
            f"{source_min_delta}"
        )

    if (
        source_failure_change
        != CONTROLLED_FAILURE_CHANGE
    ):
        raise ValueError(
            "Unexpected source "
            "MonitorFailureChange: "
            f"{source_failure_change}"
        )

    return {
        "MonitorMinFailureDelta":
            source_min_delta,
        "MonitorFailureChange":
            source_failure_change,
    }


def write_condition_spec() -> None:

    data = {
        "study": "dTAS EQ3-B",
        "independent_variable":
            "MonitorMinFailureDelta",
        "controlled_variables": {
            "MonitorFailureChange":
                CONTROLLED_FAILURE_CHANGE,
        },
        "conditions":
            CONDITIONS,
        "runs_per_condition":
            RUNS_PER_CONDITION,
        "cycles_per_run":
            CYCLES_PER_RUN,
        "total_condition_runs":
            (
                len(CONDITIONS)
                * RUNS_PER_CONDITION
            ),
        "baseline_reuse": {
            "condition_id":
                "mfd-0005",
            "source":
                "EQ3-A runs 001-010",
            "new_executions_required":
                0,
        },
    }

    with CONDITION_SPEC_PATH.open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            data,
            f,
            indent=2,
            ensure_ascii=False,
        )
        f.write("\n")


def generate_condition_xml(
    condition: dict,
) -> Path:

    tree = ET.parse(
        SOURCE_ENTITY
    )

    root = tree.getroot()

    min_delta = root.find(
        "MonitorMinFailureDelta"
    )

    failure_change = root.find(
        "MonitorFailureChange"
    )

    if (
        min_delta is None
        or failure_change is None
    ):
        raise ValueError(
            "Required monitor parameters "
            "missing from source XML."
        )

    # Verify every generated condition starts
    # from the original frozen configuration.
    if (
        float(min_delta.text)
        != ORIGINAL_MIN_FAILURE_DELTA
    ):
        raise ValueError(
            "Source min failure delta "
            "changed unexpectedly."
        )

    if (
        float(failure_change.text)
        != CONTROLLED_FAILURE_CHANGE
    ):
        raise ValueError(
            "Source failure change "
            "changed unexpectedly."
        )

    min_delta.text = str(
        condition[
            "min_failure_delta"
        ]
    )

    # Explicitly preserve controlled variable.
    failure_change.text = str(
        CONTROLLED_FAILURE_CHANGE
    )

    destination = (
        CONDITIONS_DIR
        / (
            condition[
                "condition_id"
            ]
            + ".xml"
        )
    )

    tree.write(
        destination,
        encoding="UTF-8",
        xml_declaration=True,
    )

    # Re-read and verify generated artefact.
    check_tree = ET.parse(
        destination
    )

    check_root = (
        check_tree.getroot()
    )

    actual_delta = float(
        check_root.find(
            "MonitorMinFailureDelta"
        ).text
    )

    actual_change = float(
        check_root.find(
            "MonitorFailureChange"
        ).text
    )

    if (
        actual_delta
        != condition[
            "min_failure_delta"
        ]
    ):
        raise ValueError(
            f"{condition['condition_id']}: "
            "generated min delta mismatch."
        )

    if (
        actual_change
        != CONTROLLED_FAILURE_CHANGE
    ):
        raise ValueError(
            f"{condition['condition_id']}: "
            "controlled variable changed."
        )

    return destination


def generate_harness() -> None:

    text = EQ3A_HARNESS.read_text(
        encoding="utf-8"
    )

    old_class = (
        "public class "
        "DTASEQ3Harness {"
    )

    new_class = (
        "public class "
        "DTASEQ3BHarness {"
    )

    if old_class not in text:
        raise ValueError(
            "EQ3-A harness class "
            "declaration not found."
        )

    text = text.replace(
        old_class,
        new_class,
        1,
    )

    old_args = (
        "if (args.length != 3) {"
    )

    new_args = (
        "if (args.length != 4) {"
    )

    if old_args not in text:
        raise ValueError(
            "EQ3-A argument check "
            "not found."
        )

    text = text.replace(
        old_args,
        new_args,
        1,
    )

    old_usage = (
        '"Usage: DTASEQ3Harness "'
        '\n                + "<dTAS-root> '
        '<run-id> <output.csv>"'
    )

    new_usage = (
        '"Usage: DTASEQ3BHarness "'
        '\n                + "<dTAS-root> '
        '<run-id> <output.csv> '
        '<entity-xml>"'
    )

    if old_usage not in text:
        raise ValueError(
            "EQ3-A usage text "
            "not found."
        )

    text = text.replace(
        old_usage,
        new_usage,
        1,
    )

    old_entity = '''File entityFile = new File(
            root,
            "TAS_gui/resources/files/entities/"
            + "System Entity 1.xml"
        );'''

    new_entity = '''File entityFile = new File(
            args[3]
        );

        if (!entityFile.isFile()) {
            throw new IllegalArgumentException(
                "Entity XML not found: "
                + entityFile.getPath()
            );
        }'''

    if old_entity not in text:
        raise ValueError(
            "EQ3-A entity-file block "
            "not found."
        )

    text = text.replace(
        old_entity,
        new_entity,
        1,
    )

    HARNESS_SOURCE.write_text(
        text,
        encoding="utf-8",
    )


def compile_harness() -> None:

    HARNESS_BIN.mkdir(
        parents=True,
        exist_ok=True,
    )

    classpath = ":".join(
        [
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

    command = [
        "javac",
        "-source",
        "1.8",
        "-target",
        "1.8",
        "-cp",
        classpath,
        "-d",
        str(HARNESS_BIN),
        str(HARNESS_SOURCE),
    ]

    result = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "EQ3-B harness compilation "
            "failed:\n"
            + result.stdout
            + result.stderr
        )

    class_file = (
        HARNESS_BIN
        / "DTASEQ3BHarness.class"
    )

    if not class_file.is_file():
        raise RuntimeError(
            "Compiled EQ3-B harness "
            "class not found."
        )


def write_manifest(
    source_entity_config: dict,
    condition_paths: list[Path],
) -> None:

    manifest = {
        "study":
            "dTAS EQ3-B",

        "source": {
            "dtas_source_zip": {
                "path":
                    str(
                        SOURCE_ZIP.relative_to(
                            PROJECT_ROOT
                        )
                    ),
                "sha256":
                    sha256_file(
                        SOURCE_ZIP
                    ),
            },
            "source_entity": {
                "path":
                    str(
                        SOURCE_ENTITY.relative_to(
                            PROJECT_ROOT
                        )
                    ),
                "sha256":
                    sha256_file(
                        SOURCE_ENTITY
                    ),
                "configuration":
                    source_entity_config,
            },
            "eq3a_harness": {
                "path":
                    str(
                        EQ3A_HARNESS.relative_to(
                            PROJECT_ROOT
                        )
                    ),
                "sha256":
                    sha256_file(
                        EQ3A_HARNESS
                    ),
            },
        },

        "experimental_design": {
            "conditions_spec": {
                "path":
                    str(
                        CONDITION_SPEC_PATH.relative_to(
                            PROJECT_ROOT
                        )
                    ),
                "sha256":
                    sha256_file(
                        CONDITION_SPEC_PATH
                    ),
            },
            "independent_variable":
                "MonitorMinFailureDelta",
            "controlled_variable": {
                "MonitorFailureChange":
                    CONTROLLED_FAILURE_CHANGE,
            },
            "runs_per_condition":
                RUNS_PER_CONDITION,
            "cycles_per_run":
                CYCLES_PER_RUN,
        },

        "generated_conditions": [
            {
                "condition_id":
                    condition[
                        "condition_id"
                    ],
                "min_failure_delta":
                    condition[
                        "min_failure_delta"
                    ],
                "status":
                    condition[
                        "status"
                    ],
                "path":
                    str(
                        path.relative_to(
                            PROJECT_ROOT
                        )
                    ),
                "sha256":
                    sha256_file(
                        path
                    ),
            }
            for condition, path
            in zip(
                CONDITIONS,
                condition_paths,
            )
        ],

        "generated_harness": {
            "path":
                str(
                    HARNESS_SOURCE.relative_to(
                        PROJECT_ROOT
                    )
                ),
            "sha256":
                sha256_file(
                    HARNESS_SOURCE
                ),
            "compiled_class": {
                "path":
                    str(
                        (
                            HARNESS_BIN
                            / "DTASEQ3BHarness.class"
                        ).relative_to(
                            PROJECT_ROOT
                        )
                    ),
                "sha256":
                    sha256_file(
                        HARNESS_BIN
                        / "DTASEQ3BHarness.class"
                    ),
            },
        },
    }

    with MANIFEST_PATH.open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            manifest,
            f,
            indent=2,
            ensure_ascii=False,
        )
        f.write("\n")


def main():

    print("=" * 70)
    print(
        "dTAS EQ3-B EXPERIMENT BUILDER"
    )
    print("=" * 70)

    verify_frozen_inputs()

    source_config = (
        verify_source_entity()
    )

    # Clean generated workspace only.
    # Never touch upstream source or EQ3-A.
    if WORK_ROOT.exists():
        shutil.rmtree(
            WORK_ROOT
        )

    CONDITIONS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    write_condition_spec()

    condition_paths = []

    for condition in CONDITIONS:

        path = generate_condition_xml(
            condition
        )

        condition_paths.append(
            path
        )

        print(
            f"{condition['condition_id']}: "
            "MonitorMinFailureDelta="
            f"{condition['min_failure_delta']}"
        )

    generate_harness()

    print()
    print(
        "Compiling generated "
        "EQ3-B harness..."
    )

    compile_harness()

    write_manifest(
        source_config,
        condition_paths,
    )

    print()
    print(
        "Generated conditions: "
        f"{len(condition_paths)}"
    )

    print(
        "Runs per condition: "
        f"{RUNS_PER_CONDITION}"
    )

    print(
        "Cycles per run: "
        f"{CYCLES_PER_RUN}"
    )

    print(
        "New executions required: 30"
    )

    print()
    print(
        f"Manifest: {MANIFEST_PATH}"
    )

    print(
        "EQ3-B BUILD: PASS"
    )


if __name__ == "__main__":
    main()

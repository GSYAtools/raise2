import hashlib
import json
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DTAS_ROOT = (
    PROJECT_ROOT
    / "dtas/work/source/dTAS"
)

HARNESS_DIR = (
    PROJECT_ROOT
    / "dtas/work/eq3-harness"
)

SHIM_SOURCE = (
    HARNESS_DIR
    / "shim-src/javafx/util/Pair.java"
)

SHIM_BIN = (
    HARNESS_DIR
    / "shim-bin"
)

HARNESS_SOURCE = (
    HARNESS_DIR
    / "DTASEQ3Harness.java"
)

HARNESS_CLASS = (
    HARNESS_DIR
    / "DTASEQ3Harness.class"
)

SMOKE_SOURCE = (
    HARNESS_DIR
    / "DTASSmoke.java"
)

MANIFEST_PATH = (
    HARNESS_DIR
    / "manifest.json"
)


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


def run_command(command):
    print(
        " ".join(str(item) for item in command)
    )

    result = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "Command failed with exit code "
            f"{result.returncode}"
        )


def main():
    print("=" * 70)
    print("dTAS EQ3-A BUILD")
    print("=" * 70)

    # --------------------------------------------------
    # Required original dTAS compiled artefacts
    # --------------------------------------------------

    required = [
        SHIM_SOURCE,
        HARNESS_SOURCE,
        SMOKE_SOURCE,
        (
            DTAS_ROOT
            / "TeleAssistanceSystem/bin"
            / "tas/mape/knowledge/Goal.class"
        ),
        (
            DTAS_ROOT
            / "TeleAssistanceSystem/libs/"
            "antlrworks-1.5.2-complete.jar"
        ),
        (
            DTAS_ROOT
            / "TeleAssistanceSystem/libs/"
            "javax.jms-api-2.0.jar"
        ),
        (
            DTAS_ROOT
            / "TeleAssistanceSystem/libs/"
            "xstream-1.5.0.jar"
        ),
    ]

    for path in required:
        require_file(path)

    # --------------------------------------------------
    # Compile JavaFX Pair compatibility shim
    # --------------------------------------------------

    SHIM_BIN.mkdir(
        parents=True,
        exist_ok=True,
    )

    print()
    print("Compiling JavaFX Pair shim...")

    run_command(
        [
            "javac",
            "-source",
            "1.8",
            "-target",
            "1.8",
            "-d",
            str(SHIM_BIN),
            str(SHIM_SOURCE),
        ]
    )

    pair_class = (
        SHIM_BIN
        / "javafx/util/Pair.class"
    )

    require_file(pair_class)

    # --------------------------------------------------
    # Compile EQ3-A harness
    # --------------------------------------------------

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

    print()
    print("Compiling EQ3-A harness...")

    run_command(
        [
            "javac",
            "-source",
            "1.8",
            "-target",
            "1.8",
            "-cp",
            classpath,
            str(HARNESS_SOURCE),
        ]
    )

    require_file(HARNESS_CLASS)

    # --------------------------------------------------
    # Write reproducibility manifest
    # --------------------------------------------------

    manifest = {
        "study": "dTAS EQ3-A",
        "java_target": "1.8",
        "source_artifacts": {
            "harness": {
                "path": str(
                    HARNESS_SOURCE.relative_to(
                        PROJECT_ROOT
                    )
                ),
                "sha256": sha256_file(
                    HARNESS_SOURCE
                ),
            },
            "pair_shim": {
                "path": str(
                    SHIM_SOURCE.relative_to(
                        PROJECT_ROOT
                    )
                ),
                "sha256": sha256_file(
                    SHIM_SOURCE
                ),
            },
        },
        "compiled_artifacts": {
            "harness_class": {
                "path": str(
                    HARNESS_CLASS.relative_to(
                        PROJECT_ROOT
                    )
                ),
                "sha256": sha256_file(
                    HARNESS_CLASS
                ),
            },
            "pair_class": {
                "path": str(
                    pair_class.relative_to(
                        PROJECT_ROOT
                    )
                ),
                "sha256": sha256_file(
                    pair_class
                ),
            },
        },
        "execution": {
            "runs": 30,
            "cycles_per_run": 20,
            "runner": (
                "raise2.experiments."
                "run_dtas_eq3"
            ),
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

    print()
    print(
        f"Harness SHA-256: "
        f"{manifest['source_artifacts']['harness']['sha256']}"
    )

    print(
        f"Pair shim SHA-256: "
        f"{manifest['source_artifacts']['pair_shim']['sha256']}"
    )

    print(
        f"Manifest: {MANIFEST_PATH}"
    )

    print()
    print("dTAS EQ3-A BUILD: PASS")


if __name__ == "__main__":
    main()

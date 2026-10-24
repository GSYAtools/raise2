import argparse
import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            digest.update(chunk)

    return digest.hexdigest()


def validate_manifest(manifest: dict, schema: dict) -> None:
    validator = Draft202012Validator(schema)

    errors = sorted(
        validator.iter_errors(manifest),
        key=lambda error: list(error.path),
    )

    if errors:
        messages = []

        for error in errors:
            location = ".".join(
                str(part) for part in error.path
            )
            location = location or "<root>"
            messages.append(
                f"{location}: {error.message}"
            )

        raise ValueError(
            "Experiment manifest validation failed:\n"
            + "\n".join(messages)
        )


def resolve_project_path(root: Path, relative_path: str) -> Path:
    path = (root / relative_path).resolve()

    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError(
            f"Artefact escapes project root: {relative_path}"
        ) from exc

    return path


def load_text_artefact(path: Path, artefact_type: str):
    if artefact_type == "architecture":
        return load_json(path)

    return path.read_text(encoding="utf-8")


def load_experiment(
    manifest_path: Path,
    schema_path: Path,
    project_root: Path,
) -> dict:

    project_root = project_root.resolve()

    if not project_root.is_dir():
        raise NotADirectoryError(
            f"Project root does not exist: {project_root}"
        )

    manifest = load_json(manifest_path)
    schema = load_json(schema_path)

    validate_manifest(manifest, schema)

    loaded_artefacts = []

    for artefact in manifest["artefacts"]:
        path = resolve_project_path(
            project_root,
            artefact["path"],
        )

        if not path.is_file():
            raise FileNotFoundError(
                f"Artefact does not exist: {path}"
            )

        actual_hash = sha256_file(path)
        expected_hash = artefact["sha256"]

        if actual_hash != expected_hash:
            raise ValueError(
                "Artefact integrity check failed for "
                f"{artefact['id']}:\n"
                f"expected {expected_hash}\n"
                f"actual   {actual_hash}"
            )

        content = load_text_artefact(
            path,
            artefact["type"],
        )

        loaded_artefacts.append(
            {
                "id": artefact["id"],
                "type": artefact["type"],
                "source_path": artefact["path"],
                "sha256": actual_hash,
                "content": content,
            }
        )

    return {
        "experiment_id": manifest["experiment_id"],
        "concern_id": manifest["concern_id"],
        "artefacts": loaded_artefacts,
    }


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Load and verify a frozen RAISE2 experiment."
        )
    )

    parser.add_argument(
        "manifest",
        help="Experiment manifest."
    )

    parser.add_argument(
        "--schema",
        default="raise2/schemas/experiment.schema.json",
        help="Experiment JSON schema."
    )

    parser.add_argument(
        "--root",
        default=".",
        help="Project root."
    )

    parser.add_argument(
        "--output",
        help=(
            "Optional path for the verified executor input."
        )
    )

    args = parser.parse_args()

    context = load_experiment(
        Path(args.manifest),
        Path(args.schema),
        Path(args.root),
    )

    if args.output:
        output_path = Path(args.output)

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with output_path.open(
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(
                context,
                f,
                indent=2,
                ensure_ascii=False,
            )
            f.write("\n")

        print(
            f"Verified executor input written to: "
            f"{output_path}"
        )

    print(
        f"Experiment: {context['experiment_id']}"
    )
    print(
        f"Concern: {context['concern_id']}"
    )
    print(
        f"Verified artefacts: "
        f"{len(context['artefacts'])}"
    )

    for artefact in context["artefacts"]:
        print(
            f"- {artefact['id']} "
            f"[{artefact['type']}]: "
            f"{artefact['sha256']}"
        )


if __name__ == "__main__":
    main()

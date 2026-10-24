import argparse
import hashlib
import json
from pathlib import Path


def sha256_file(path: Path) -> str:
    """Calculate the SHA-256 digest of a file."""
    digest = hashlib.sha256()

    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            digest.update(chunk)

    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(
        description="Build a portable RAISE2 experiment manifest."
    )

    parser.add_argument(
        "--experiment-id",
        required=True
    )

    parser.add_argument(
        "--concern-id",
        required=True
    )

    parser.add_argument(
        "--root",
        required=True,
        help=(
            "Project root used to convert artefact paths "
            "to portable relative paths."
        )
    )

    parser.add_argument(
        "--output",
        required=True
    )

    parser.add_argument(
        "--artefact",
        action="append",
        nargs=3,
        metavar=("ID", "TYPE", "PATH"),
        required=True,
        help="Artefact identifier, type, and path."
    )

    args = parser.parse_args()

    root = Path(args.root).resolve()

    if not root.is_dir():
        raise NotADirectoryError(
            f"Project root does not exist: {root}"
        )

    artefacts = []

    for artefact_id, artefact_type, artefact_path in args.artefact:
        path = Path(artefact_path).resolve()

        if not path.is_file():
            raise FileNotFoundError(
                f"Artefact does not exist: {path}"
            )

        try:
            relative_path = path.relative_to(root)
        except ValueError as exc:
            raise ValueError(
                f"Artefact is outside project root: {path}"
            ) from exc

        artefacts.append(
            {
                "id": artefact_id,
                "type": artefact_type,
                "path": relative_path.as_posix(),
                "sha256": sha256_file(path)
            }
        )

    manifest = {
        "experiment_id": args.experiment_id,
        "concern_id": args.concern_id,
        "artefacts": artefacts
    }

    output = Path(args.output)

    output.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with output.open(
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            manifest,
            f,
            indent=2,
            ensure_ascii=False
        )

        f.write("\n")

    print(f"Experiment manifest written to: {output}")

    for artefact in artefacts:
        print(
            f"{artefact['id']}: "
            f"{artefact['sha256']}  "
            f"{artefact['path']}"
        )


if __name__ == "__main__":
    main()

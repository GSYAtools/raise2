import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from jsonschema import Draft202012Validator
from openai import OpenAI

from raise2.evaluator.validate_derivation import (
    validate_raise2_invariants,
)
from raise2.executor.load_experiment import load_experiment


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            digest.update(chunk)

    return digest.hexdigest()


def build_executor_input(context: dict) -> str:
    """
    Serialize the verified experiment context supplied to the model.

    No artefact outside the verified experiment context can enter
    the model input through this function.
    """
    payload = {
        "experiment_id": context["experiment_id"],
        "concern_id": context["concern_id"],
        "engineering_artefacts": [],
    }

    for artefact in context["artefacts"]:
        payload["engineering_artefacts"].append(
            {
                "id": artefact["id"],
                "type": artefact["type"],
                "content": artefact["content"],
            }
        )

    return json.dumps(
        payload,
        indent=2,
        ensure_ascii=False,
    )


def validate_output(
    derivation: dict,
    schema: dict,
) -> tuple[bool, list[str]]:
    errors = []

    validator = Draft202012Validator(schema)

    schema_errors = sorted(
        validator.iter_errors(derivation),
        key=lambda error: list(error.path),
    )

    for error in schema_errors:
        location = ".".join(
            str(part) for part in error.path
        )
        location = location or "<root>"

        errors.append(
            f"Schema: {location}: {error.message}"
        )

    if not schema_errors:
        invariant_errors = validate_raise2_invariants(
            derivation
        )

        for error in invariant_errors:
            errors.append(f"RAISE2: {error}")

    return len(errors) == 0, errors


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Execute RAISE2 Representation Requirements "
            "for one frozen experiment manifest."
        )
    )

    parser.add_argument(
        "manifest",
        help="Frozen experiment manifest."
    )

    parser.add_argument(
        "--run-id",
        required=True,
        help="Unique identifier for this independent execution."
    )

    parser.add_argument(
        "--root",
        default=".",
        help="Project root."
    )

    parser.add_argument(
        "--output-dir",
        default="raise2/results",
        help="Root directory for execution results."
    )

    parser.add_argument(
        "--experiment-schema",
        default="raise2/schemas/experiment.schema.json"
    )

    parser.add_argument(
        "--derivation-schema",
        default="raise2/schemas/derivation.schema.json"
    )

    parser.add_argument(
        "--protocol",
        default="raise2/protocol/rr-protocol.txt"
    )

    args = parser.parse_args()

    # --------------------------------------------------
    # Paths and configuration
    # --------------------------------------------------

    project_root = Path(args.root).resolve()

    manifest_path = Path(args.manifest).resolve()
    experiment_schema_path = Path(
        args.experiment_schema
    ).resolve()
    derivation_schema_path = Path(
        args.derivation_schema
    ).resolve()
    protocol_path = Path(args.protocol).resolve()

    env_path = project_root / ".env"

    load_dotenv(dotenv_path=env_path)

    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL")

    if not api_key:
        print("ERROR: OPENAI_API_KEY is not configured.")
        sys.exit(1)

    if not model:
        print("ERROR: OPENAI_MODEL is not configured.")
        sys.exit(1)

    # --------------------------------------------------
    # Load and verify frozen experiment
    # --------------------------------------------------

    context = load_experiment(
        manifest_path,
        experiment_schema_path,
        project_root,
    )

    # --------------------------------------------------
    # Load frozen protocol and output schema
    # --------------------------------------------------

    protocol = load_text(protocol_path)
    derivation_schema = load_json(
        derivation_schema_path
    )

    # --------------------------------------------------
    # Build model input
    # --------------------------------------------------

    executor_input = build_executor_input(context)

    # --------------------------------------------------
    # Output directory
    # --------------------------------------------------

    run_dir = (
        Path(args.output_dir)
        / context["experiment_id"]
        / args.run_id
    )

    if run_dir.exists():
        print(
            f"ERROR: run directory already exists: "
            f"{run_dir}"
        )
        print(
            "Run identifiers must not overwrite "
            "previous executions."
        )
        sys.exit(1)

    run_dir.mkdir(
        parents=True,
        exist_ok=False,
    )

    # --------------------------------------------------
    # Freeze execution metadata before inference
    # --------------------------------------------------

    started_at = datetime.now(
        timezone.utc
    ).isoformat()

    metadata = {
        "run_id": args.run_id,
        "experiment_id": context["experiment_id"],
        "concern_id": context["concern_id"],
        "started_at_utc": started_at,
        "requested_model": model,
        "manifest_sha256": sha256_file(
            manifest_path
        ),
        "experiment_schema_sha256": sha256_file(
            experiment_schema_path
        ),
        "derivation_schema_sha256": sha256_file(
            derivation_schema_path
        ),
        "protocol_sha256": sha256_file(
            protocol_path
        ),
        "input_artefacts": [
            {
                "id": artefact["id"],
                "type": artefact["type"],
                "source_path": artefact["source_path"],
                "sha256": artefact["sha256"],
            }
            for artefact in context["artefacts"]
        ],
    }

    with (
        run_dir / "metadata.pre.json"
    ).open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            metadata,
            f,
            indent=2,
            ensure_ascii=False,
        )
        f.write("\n")

    # Save the exact verified input supplied to the model.
    with (
        run_dir / "executor-input.json"
    ).open(
        "w",
        encoding="utf-8",
    ) as f:
        f.write(executor_input)
        f.write("\n")

    # --------------------------------------------------
    # Execute RAISE2
    # --------------------------------------------------

    client = OpenAI(api_key=api_key)

    print(
        f"Executing {context['experiment_id']} "
        f"run {args.run_id}"
    )
    print(f"Model: {model}")

    try:
        response = client.responses.create(
            model=model,
            instructions=protocol,
            input=executor_input,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "raise2_derivation",
                    "strict": True,
                    "schema": derivation_schema,
                }
            },
        )

    except Exception as exc:
        metadata["status"] = "api_error"
        metadata["error"] = str(exc)
        metadata["completed_at_utc"] = datetime.now(
            timezone.utc
        ).isoformat()

        with (
            run_dir / "metadata.json"
        ).open(
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(
                metadata,
                f,
                indent=2,
                ensure_ascii=False,
            )
            f.write("\n")

        print(f"API ERROR: {exc}")
        sys.exit(1)

    # --------------------------------------------------
    # Record API metadata
    # --------------------------------------------------

    metadata["response_id"] = response.id
    metadata["returned_model"] = response.model
    metadata["response_status"] = response.status

    # Usage is useful experimental metadata when available.
    if response.usage is not None:
        metadata["usage"] = {
            "input_tokens": getattr(
                response.usage,
                "input_tokens",
                None,
            ),
            "output_tokens": getattr(
                response.usage,
                "output_tokens",
                None,
            ),
            "total_tokens": getattr(
                response.usage,
                "total_tokens",
                None,
            ),
        }

    # --------------------------------------------------
    # Parse structured result
    # --------------------------------------------------

    if not response.output_text:
        metadata["status"] = "empty_output"
        metadata["completed_at_utc"] = datetime.now(
            timezone.utc
        ).isoformat()

        with (
            run_dir / "metadata.json"
        ).open(
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(
                metadata,
                f,
                indent=2,
                ensure_ascii=False,
            )
            f.write("\n")

        print("ERROR: model returned no output text.")
        sys.exit(1)

    try:
        derivation = json.loads(
            response.output_text
        )
    except json.JSONDecodeError as exc:
        metadata["status"] = "invalid_json"
        metadata["error"] = str(exc)
        metadata["completed_at_utc"] = datetime.now(
            timezone.utc
        ).isoformat()

        with (
            run_dir / "raw-output.txt"
        ).open(
            "w",
            encoding="utf-8",
        ) as f:
            f.write(response.output_text)

        with (
            run_dir / "metadata.json"
        ).open(
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(
                metadata,
                f,
                indent=2,
                ensure_ascii=False,
            )
            f.write("\n")

        print("ERROR: model returned invalid JSON.")
        sys.exit(1)

    # --------------------------------------------------
    # Ensure experimental identifiers are correct
    # --------------------------------------------------

    if derivation["run_id"] != args.run_id:
        derivation["run_id"] = args.run_id

    if (
        derivation["concern_id"]
        != context["concern_id"]
    ):
        derivation["concern_id"] = (
            context["concern_id"]
        )

    # --------------------------------------------------
    # Save derivation
    # --------------------------------------------------

    derivation_path = (
        run_dir / "derivation.json"
    )

    with derivation_path.open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            derivation,
            f,
            indent=2,
            ensure_ascii=False,
        )
        f.write("\n")

    # --------------------------------------------------
    # Independent deterministic validation
    # --------------------------------------------------

    valid, validation_errors = validate_output(
        derivation,
        derivation_schema,
    )

    metadata["validation_passed"] = valid
    metadata["validation_errors"] = (
        validation_errors
    )

    metadata["derivation_sha256"] = sha256_file(
        derivation_path
    )

    metadata["completed_at_utc"] = datetime.now(
        timezone.utc
    ).isoformat()

    metadata["status"] = (
        "completed_valid"
        if valid
        else "completed_invalid"
    )

    # --------------------------------------------------
    # Final metadata
    # --------------------------------------------------

    with (
        run_dir / "metadata.json"
    ).open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            metadata,
            f,
            indent=2,
            ensure_ascii=False,
        )
        f.write("\n")

    # --------------------------------------------------
    # Console summary
    # --------------------------------------------------

    print(f"Response ID: {response.id}")
    print(f"Returned model: {response.model}")
    print(
        f"Response status: {response.status}"
    )

    if valid:
        print("SCHEMA VALIDATION: PASS")
        print("RAISE2 VALIDATION: PASS")
        print("RUN STATUS: VALID")
    else:
        print("RUN STATUS: INVALID")

        for error in validation_errors:
            print(f"- {error}")

    print(f"Results: {run_dir}")

    if not valid:
        sys.exit(1)


if __name__ == "__main__":
    main()

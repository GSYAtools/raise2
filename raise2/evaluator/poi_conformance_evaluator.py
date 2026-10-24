import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from jsonschema import Draft202012Validator
from openai import OpenAI

from raise2.executor.load_experiment import load_experiment


PROJECT_ROOT = Path(__file__).resolve().parents[2]

PROTOCOL_PATH = (
    PROJECT_ROOT
    / "raise2"
    / "protocol"
    / "poi-conformance-protocol.txt"
)

SCHEMA_PATH = (
    PROJECT_ROOT
    / "raise2"
    / "schemas"
    / "poi-conformance.schema.json"
)

EXPERIMENT_SCHEMA_PATH = (
    PROJECT_ROOT
    / "raise2"
    / "schemas"
    / "experiment.schema.json"
)

MANIFESTS = {
    "H1": (
        PROJECT_ROOT
        / "raise2"
        / "experiments"
        / "mobstr"
        / "H1.json"
    ),
    "H3": (
        PROJECT_ROOT
        / "raise2"
        / "experiments"
        / "mobstr"
        / "H3.json"
    ),
}


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def build_judge_input(
    run_id: str,
    concern_id: str,
    derivation: dict,
    context: dict,
) -> str:
    """
    Build the complete judge input.

    Deliberately excludes:
    - distinctions;
    - ORRs;
    - assumptions;
    - revalidation conditions;
    - downstream reference evidence.
    """

    target = derivation["evaluation_target"]
    phenomenon = derivation["phenomenon_of_interest"]

    artefacts = []

    for artefact in context["artefacts"]:
        artefacts.append(
            {
                "id": artefact["id"],
                "type": artefact["type"],
                "content": artefact["content"],
            }
        )

    payload = {
        "run_id": run_id,
        "concern_id": concern_id,
        "evaluation_target": {
            "statement": target["statement"],
            "sources": target["source"],
            "rationale": target["rationale"],
        },
        "phenomenon_of_interest": {
            "statement": phenomenon["statement"],
            "scope": phenomenon["scope"],
            "sources": phenomenon["source"],
            "rationale": phenomenon["rationale"],
        },
        "upstream_engineering_artefacts": artefacts,
    }

    return json.dumps(
        payload,
        indent=2,
        ensure_ascii=False,
    )


def validate_assessment(
    assessment: dict,
    schema: dict,
) -> list[str]:
    validator = Draft202012Validator(schema)

    errors = sorted(
        validator.iter_errors(assessment),
        key=lambda error: list(error.path),
    )

    messages = []

    for error in errors:
        location = ".".join(
            str(part) for part in error.path
        )
        location = location or "<root>"

        messages.append(
            f"{location}: {error.message}"
        )

    return messages


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Assess RR2 Phenomenon-of-Interest "
            "conformance for one RAISE2 run."
        )
    )

    parser.add_argument(
        "--concern",
        choices=["H1", "H3"],
        required=True,
    )

    parser.add_argument(
        "--run-id",
        required=True,
    )

    parser.add_argument(
        "--assessment-id",
        required=True,
        help=(
            "Identifier for this independent judge "
            "assessment, e.g. judge-01."
        ),
    )

    parser.add_argument(
        "--results-root",
        default="raise2/results",
    )

    args = parser.parse_args()

    # --------------------------------------------------
    # Configuration
    # --------------------------------------------------

    load_dotenv(
        dotenv_path=PROJECT_ROOT / ".env"
    )

    api_key = os.getenv("OPENAI_API_KEY")
    judge_model = os.getenv(
        "OPENAI_JUDGE_MODEL"
    )

    if not api_key:
        print(
            "ERROR: OPENAI_API_KEY is not configured."
        )
        sys.exit(1)

    if not judge_model:
        print(
            "ERROR: OPENAI_JUDGE_MODEL is not configured."
        )
        sys.exit(1)

    concern = args.concern

    experiment_id = (
        "mobstr-H1"
        if concern == "H1"
        else "mobstr-H3"
    )

    # --------------------------------------------------
    # Locate derivation
    # --------------------------------------------------

    run_dir = (
        PROJECT_ROOT
        / args.results_root
        / experiment_id
        / args.run_id
    )

    derivation_path = (
        run_dir / "derivation.json"
    )

    if not derivation_path.is_file():
        print(
            f"ERROR: derivation not found: "
            f"{derivation_path}"
        )
        sys.exit(1)

    derivation = load_json(
        derivation_path
    )

    # --------------------------------------------------
    # Load frozen upstream experiment
    # --------------------------------------------------

    context = load_experiment(
        MANIFESTS[concern],
        EXPERIMENT_SCHEMA_PATH,
        PROJECT_ROOT,
    )

    # --------------------------------------------------
    # Load frozen judge protocol and schema
    # --------------------------------------------------

    protocol = load_text(
        PROTOCOL_PATH
    )

    schema = load_json(
        SCHEMA_PATH
    )

    # --------------------------------------------------
    # Construct restricted judge input
    # --------------------------------------------------

    judge_input = build_judge_input(
        args.run_id,
        concern,
        derivation,
        context,
    )

    # --------------------------------------------------
    # Assessment directory
    # --------------------------------------------------

    assessment_dir = (
        run_dir
        / "poi-conformance"
        / args.assessment_id
    )

    if assessment_dir.exists():
        print(
            "ERROR: assessment directory already "
            f"exists: {assessment_dir}"
        )
        sys.exit(1)

    assessment_dir.mkdir(
        parents=True,
        exist_ok=False,
    )

    with (
        assessment_dir / "judge-input.json"
    ).open(
        "w",
        encoding="utf-8",
    ) as f:
        f.write(judge_input)
        f.write("\n")

    # --------------------------------------------------
    # Execute independent judge
    # --------------------------------------------------

    client = OpenAI(
        api_key=api_key
    )

    started_at = datetime.now(
        timezone.utc
    ).isoformat()

    print(
        f"Assessing {args.run_id} "
        f"({args.assessment_id})"
    )

    print(
        f"Judge model: {judge_model}"
    )

    try:
        response = client.responses.create(
            model=judge_model,
            reasoning={
                "effort": "high"
            },
            instructions=protocol,
            input=judge_input,
            text={
                "format": {
                    "type": "json_schema",
                    "name": (
                        "raise2_poi_conformance"
                    ),
                    "strict": True,
                    "schema": schema,
                }
            },
        )

    except Exception as exc:
        metadata = {
            "run_id": args.run_id,
            "concern_id": concern,
            "assessment_id":
                args.assessment_id,
            "requested_model":
                judge_model,
            "started_at_utc":
                started_at,
            "completed_at_utc":
                datetime.now(
                    timezone.utc
                ).isoformat(),
            "status": "api_error",
            "error": str(exc),
        }

        with (
            assessment_dir
            / "metadata.json"
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
    # Parse assessment
    # --------------------------------------------------

    if not response.output_text:
        print(
            "ERROR: judge returned no output."
        )
        sys.exit(1)

    try:
        assessment = json.loads(
            response.output_text
        )
    except json.JSONDecodeError as exc:
        print(
            f"ERROR: invalid judge JSON: {exc}"
        )
        sys.exit(1)

    # Harness-controlled identifiers.
    assessment["run_id"] = args.run_id
    assessment["concern_id"] = concern

    # --------------------------------------------------
    # Validate assessment
    # --------------------------------------------------

    validation_errors = (
        validate_assessment(
            assessment,
            schema,
        )
    )

    valid = (
        len(validation_errors) == 0
    )

    with (
        assessment_dir
        / "assessment.json"
    ).open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            assessment,
            f,
            indent=2,
            ensure_ascii=False,
        )
        f.write("\n")

    # --------------------------------------------------
    # Metadata
    # --------------------------------------------------

    metadata = {
        "run_id": args.run_id,
        "concern_id": concern,
        "assessment_id":
            args.assessment_id,
        "started_at_utc":
            started_at,
        "completed_at_utc":
            datetime.now(
                timezone.utc
            ).isoformat(),
        "requested_model":
            judge_model,
        "returned_model":
            response.model,
        "response_id":
            response.id,
        "response_status":
            response.status,
        "reasoning_effort":
            "high",
        "validation_passed":
            valid,
        "validation_errors":
            validation_errors,
        "status": (
            "completed_valid"
            if valid
            else "completed_invalid"
        ),
    }

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

    with (
        assessment_dir
        / "metadata.json"
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
    # Summary
    # --------------------------------------------------

    print(
        f"Returned model: "
        f"{response.model}"
    )

    print(
        f"Classification: "
        f"{assessment['classification']}"
    )

    print(
        "VALIDATION: "
        + ("PASS" if valid else "FAIL")
    )

    if not valid:
        for error in validation_errors:
            print(f"- {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()

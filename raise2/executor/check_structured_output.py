import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from jsonschema import Draft202012Validator
from openai import OpenAI

from raise2.evaluator.validate_derivation import (
    validate_raise2_invariants,
)


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main():
    # --------------------------------------------------
    # Project configuration
    # --------------------------------------------------

    project_root = Path(__file__).resolve().parents[2]

    env_path = project_root / ".env"
    schema_path = (
        project_root
        / "raise2"
        / "schemas"
        / "derivation.schema.json"
    )

    output_path = (
        project_root
        / "raise2"
        / "tests"
        / "structured-output-test.json"
    )

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
    # Load RAISE2 output schema
    # --------------------------------------------------

    schema = load_json(schema_path)

    # --------------------------------------------------
    # OpenAI client
    # --------------------------------------------------

    client = OpenAI(api_key=api_key)

    print(f"Requested model: {model}")

    # --------------------------------------------------
    # Synthetic test
    # --------------------------------------------------

    instructions = """
You are testing a structured-output contract.

Produce one minimal RAISE2 derivation for the synthetic engineering
requirement supplied by the user.

The derivation must contain:

- one Evaluation Target;
- one Phenomenon of Interest;
- one Concern-Relevant Distinction;
- one Operational Representation Requirement covering that distinction;
- one traceable assumption;
- one revalidation condition;
- RR5 coverage=true;
- RR5 consistency=true;
- no RR5 issues.

Use only the source identifier REQ-TEST-1.

Return only the structured result required by the supplied schema.
""".strip()

    user_input = """
REQ-TEST-1:
The service shall remain operationally available to authorised users.
""".strip()

    response = client.responses.create(
        model=model,
        instructions=instructions,
        input=user_input,
        text={
            "format": {
                "type": "json_schema",
                "name": "raise2_derivation",
                "strict": True,
                "schema": schema,
            }
        },
    )

    print(f"Response ID: {response.id}")
    print(f"Returned model: {response.model}")
    print(f"Response status: {response.status}")

    if not response.output_text:
        print("STRUCTURED OUTPUT: FAIL")
        print("No output text returned.")
        sys.exit(1)

    # --------------------------------------------------
    # Parse model output
    # --------------------------------------------------

    try:
        derivation = json.loads(response.output_text)
    except json.JSONDecodeError as exc:
        print("STRUCTURED OUTPUT: FAIL")
        print(f"Invalid JSON returned: {exc}")
        sys.exit(1)

    # --------------------------------------------------
    # Save raw structured derivation
    # --------------------------------------------------

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_path.open(
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

    print(f"Output written to: {output_path}")

    # --------------------------------------------------
    # Independent JSON Schema validation
    # --------------------------------------------------

    validator = Draft202012Validator(schema)

    schema_errors = sorted(
        validator.iter_errors(derivation),
        key=lambda error: list(error.path),
    )

    if schema_errors:
        print("SCHEMA VALIDATION: FAIL")

        for error in schema_errors:
            location = ".".join(
                str(part) for part in error.path
            )
            location = location or "<root>"

            print(
                f"- {location}: "
                f"{error.message}"
            )

        sys.exit(1)

    print("SCHEMA VALIDATION: PASS")

    # --------------------------------------------------
    # Independent RAISE2 invariant validation
    # --------------------------------------------------

    invariant_errors = validate_raise2_invariants(
        derivation
    )

    if invariant_errors:
        print("RAISE2 VALIDATION: FAIL")

        for error in invariant_errors:
            print(f"- {error}")

        sys.exit(1)

    print("RAISE2 VALIDATION: PASS")
    print("STRUCTURED OUTPUT TEST: PASS")


if __name__ == "__main__":
    main()

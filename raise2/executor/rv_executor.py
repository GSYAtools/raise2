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


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_BASELINE = (
    PROJECT_ROOT
    / "mobstr/work/revalidation/H1/baseline.json"
)

DEFAULT_PROTOCOL = (
    PROJECT_ROOT
    / "raise2/protocol/rv-protocol.txt"
)

DEFAULT_SCHEMA = (
    PROJECT_ROOT
    / "raise2/schemas/rv-result.schema.json"
)

DEFAULT_RESULTS_ROOT = (
    PROJECT_ROOT
    / "raise2/results/mobstr-eq2"
)


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


def validate_rv_invariants(
    result: dict,
    baseline: dict,
) -> list[str]:

    errors = []

    decision = result["decision"]
    affected = result["affected_orrs"]
    return_point = result["return_point"]
    triggered = result["triggered_conditions"]
    if len(affected) != len(set(affected)):
        errors.append(
            "Affected ORRs must be unique."
        )

    if len(triggered) != len(set(triggered)):
        errors.append(
            "Triggered revalidation conditions "
            "must be unique."
        )

    valid_orrs = {
        orr["id"]
        for orr in baseline["orrs"]
    }

    valid_rcs = {
        rc["id"]
        for orr in baseline["orrs"]
        for assumption in orr["assumptions"]
        for rc in assumption[
            "revalidation_conditions"
        ]
    }

    unknown_orrs = (
        set(affected) - valid_orrs
    )

    if unknown_orrs:
        errors.append(
            "Unknown affected ORRs: "
            + ", ".join(
                sorted(unknown_orrs)
            )
        )

    unknown_rcs = (
        set(triggered) - valid_rcs
    )

    if unknown_rcs:
        errors.append(
            "Unknown triggered conditions: "
            + ", ".join(
                sorted(unknown_rcs)
            )
        )

    if decision == "NONE":
        if affected:
            errors.append(
                "NONE must have no affected ORRs."
            )

        if return_point is not None:
            errors.append(
                "NONE must have no return point."
            )

        if triggered:
            errors.append(
                "NONE must have no triggered "
                "revalidation conditions."
            )

    elif decision == "REVALIDATE":
        if not affected:
            errors.append(
                "REVALIDATE must identify at least "
                "one affected ORR."
            )

        if return_point is not None:
            errors.append(
                "REVALIDATE must have no return point."
            )

        if not triggered:
            errors.append(
                "REVALIDATE must identify at least "
                "one triggered revalidation condition."
            )

    elif decision == "REDERIVE":
        if affected:
            errors.append(
                "REDERIVE must not identify affected "
                "ORRs."
            )

        if return_point not in {
            "RR1",
            "RR2",
            "RR3",
        }:
            errors.append(
                "REDERIVE requires return point "
                "RR1, RR2, or RR3."
            )

    return errors


def validate_result(
    result: dict,
    schema: dict,
    baseline: dict,
) -> list[str]:

    errors = []

    validator = Draft202012Validator(
        schema
    )

    schema_errors = sorted(
        validator.iter_errors(result),
        key=lambda error: list(error.path),
    )

    for error in schema_errors:
        location = ".".join(
            str(part)
            for part in error.path
        )

        location = (
            location or "<root>"
        )

        errors.append(
            f"Schema: {location}: "
            f"{error.message}"
        )

    if not schema_errors:
        errors.extend(
            "RAISE2: " + error
            for error
            in validate_rv_invariants(
                result,
                baseline,
            )
        )

    return errors


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Execute RAISE2 Representation "
            "Revalidation for one frozen "
            "lifecycle change."
        )
    )

    parser.add_argument(
        "change",
        help="Lifecycle change JSON."
    )

    parser.add_argument(
        "--run-id",
        required=True,
    )

    parser.add_argument(
        "--baseline",
        default=str(DEFAULT_BASELINE),
    )

    parser.add_argument(
        "--protocol",
        default=str(DEFAULT_PROTOCOL),
    )

    parser.add_argument(
        "--schema",
        default=str(DEFAULT_SCHEMA),
    )

    parser.add_argument(
        "--output-root",
        default=str(
            DEFAULT_RESULTS_ROOT
        ),
    )

    args = parser.parse_args()

    # --------------------------------------------------
    # Paths
    # --------------------------------------------------

    change_path = Path(
        args.change
    ).resolve()

    baseline_path = Path(
        args.baseline
    ).resolve()

    protocol_path = Path(
        args.protocol
    ).resolve()

    schema_path = Path(
        args.schema
    ).resolve()

    output_root = Path(
        args.output_root
    ).resolve()

    for path in [
        change_path,
        baseline_path,
        protocol_path,
        schema_path,
    ]:
        if not path.is_file():
            print(
                f"ERROR: missing file: {path}"
            )
            sys.exit(1)

    # --------------------------------------------------
    # Configuration
    # --------------------------------------------------

    load_dotenv(
        dotenv_path=PROJECT_ROOT / ".env"
    )

    api_key = os.getenv(
        "OPENAI_API_KEY"
    )

    model = os.getenv(
        "OPENAI_MODEL"
    )

    if not api_key:
        print(
            "ERROR: OPENAI_API_KEY "
            "is not configured."
        )
        sys.exit(1)

    if not model:
        print(
            "ERROR: OPENAI_MODEL "
            "is not configured."
        )
        sys.exit(1)

    # --------------------------------------------------
    # Load frozen inputs
    # --------------------------------------------------

    baseline = load_json(
        baseline_path
    )

    change = load_json(
        change_path
    )

    protocol = load_text(
        protocol_path
    )

    schema = load_json(
        schema_path
    )

    # --------------------------------------------------
    # Verify baseline/change binding
    # --------------------------------------------------

    baseline_hash = sha256_file(
        baseline_path
    )

    declared_baseline_hash = (
        change.get(
            "baseline_sha256"
        )
    )

    if (
        declared_baseline_hash
        != baseline_hash
    ):
        print(
            "ERROR: change is not bound "
            "to the supplied baseline."
        )
        sys.exit(1)

    if (
        change.get("baseline_id")
        != baseline.get("baseline_id")
    ):
        print(
            "ERROR: baseline ID mismatch."
        )
        sys.exit(1)

    change_id = change[
        "change_id"
    ]

    # --------------------------------------------------
    # Output directory
    # --------------------------------------------------

    run_dir = (
        output_root
        / change_id
        / args.run_id
    )

    if run_dir.exists():
        print(
            "ERROR: run directory "
            f"already exists: {run_dir}"
        )
        sys.exit(1)

    run_dir.mkdir(
        parents=True,
        exist_ok=False,
    )

    # --------------------------------------------------
    # Executor-visible input
    # --------------------------------------------------

    executor_payload = {
        "baseline": baseline,
        "lifecycle_change": change,
    }

    executor_input = json.dumps(
        executor_payload,
        indent=2,
        ensure_ascii=False,
    )

    with (
        run_dir
        / "executor-input.json"
    ).open(
        "w",
        encoding="utf-8",
    ) as f:
        f.write(executor_input)
        f.write("\n")

    # --------------------------------------------------
    # Pre-inference metadata
    # --------------------------------------------------

    started_at = datetime.now(
        timezone.utc
    ).isoformat()

    metadata = {
        "run_id":
            args.run_id,
        "change_id":
            change_id,
        "started_at_utc":
            started_at,
        "requested_model":
            model,
        "baseline_sha256":
            baseline_hash,
        "change_sha256":
            sha256_file(
                change_path
            ),
        "protocol_sha256":
            sha256_file(
                protocol_path
            ),
        "schema_sha256":
            sha256_file(
                schema_path
            ),
    }

    with (
        run_dir
        / "metadata.pre.json"
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
    # Execute RV1-RV5
    # --------------------------------------------------

    client = OpenAI(
        api_key=api_key
    )

    print(
        f"Executing {change_id} "
        f"run {args.run_id}"
    )

    print(
        f"Model: {model}"
    )

    try:
        response = (
            client.responses.create(
                model=model,
                instructions=protocol,
                input=executor_input,
                text={
                    "format": {
                        "type":
                            "json_schema",
                        "name":
                            "raise2_rv_result",
                        "strict":
                            True,
                        "schema":
                            schema,
                    }
                },
            )
        )

    except Exception as exc:
        metadata[
            "status"
        ] = "api_error"

        metadata[
            "error"
        ] = str(exc)

        metadata[
            "completed_at_utc"
        ] = datetime.now(
            timezone.utc
        ).isoformat()

        with (
            run_dir
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

        print(
            f"API ERROR: {exc}"
        )
        sys.exit(1)

    # --------------------------------------------------
    # API metadata
    # --------------------------------------------------

    metadata[
        "response_id"
    ] = response.id

    metadata[
        "returned_model"
    ] = response.model

    metadata[
        "response_status"
    ] = response.status

    if response.usage is not None:
        metadata["usage"] = {
            "input_tokens":
                getattr(
                    response.usage,
                    "input_tokens",
                    None,
                ),
            "output_tokens":
                getattr(
                    response.usage,
                    "output_tokens",
                    None,
                ),
            "total_tokens":
                getattr(
                    response.usage,
                    "total_tokens",
                    None,
                ),
        }

    # --------------------------------------------------
    # Parse result
    # --------------------------------------------------

    if not response.output_text:
        print(
            "ERROR: model returned "
            "no output."
        )
        sys.exit(1)

    try:
        result = json.loads(
            response.output_text
        )

    except json.JSONDecodeError as exc:
        print(
            "ERROR: model returned "
            f"invalid JSON: {exc}"
        )
        sys.exit(1)

    # Harness-controlled identifiers.
    result["run_id"] = (
        args.run_id
    )

    result["change_id"] = (
        change_id
    )

    # --------------------------------------------------
    # Deterministic validation
    # --------------------------------------------------

    validation_errors = (
        validate_result(
            result,
            schema,
            baseline,
        )
    )

    valid = (
        len(validation_errors) == 0
    )

    result_path = (
        run_dir
        / "rv-result.json"
    )

    with result_path.open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            result,
            f,
            indent=2,
            ensure_ascii=False,
        )
        f.write("\n")

    metadata[
        "validation_passed"
    ] = valid

    metadata[
        "validation_errors"
    ] = validation_errors

    metadata[
        "result_sha256"
    ] = sha256_file(
        result_path
    )

    metadata[
        "completed_at_utc"
    ] = datetime.now(
        timezone.utc
    ).isoformat()

    metadata[
        "status"
    ] = (
        "completed_valid"
        if valid
        else "completed_invalid"
    )

    with (
        run_dir
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
        f"Decision: "
        f"{result['decision']}"
    )

    print(
        "Affected ORRs: "
        + (
            ", ".join(
                result[
                    "affected_orrs"
                ]
            )
            if result[
                "affected_orrs"
            ]
            else "none"
        )
    )

    print(
        "Return point: "
        f"{result['return_point']}"
    )

    if valid:
        print(
            "RV VALIDATION: PASS"
        )
        print(
            "RUN STATUS: VALID"
        )

    else:
        print(
            "RV VALIDATION: FAIL"
        )

        for error in validation_errors:
            print(
                f"- {error}"
            )

        sys.exit(1)

    print(
        f"Results: {run_dir}"
    )


if __name__ == "__main__":
    main()

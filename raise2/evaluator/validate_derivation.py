import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def find_duplicates(values):
    seen = set()
    duplicates = set()

    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)

    return sorted(duplicates)


def validate_raise2_invariants(data: dict) -> list[str]:
    errors = []

    distinctions = data["distinctions"]
    orrs = data["orrs"]

    distinction_ids = [d["id"] for d in distinctions]
    orr_ids = [o["id"] for o in orrs]

    # --------------------------------------------------
    # Unique identifiers
    # --------------------------------------------------

    for duplicate in find_duplicates(distinction_ids):
        errors.append(f"Duplicate distinction ID: {duplicate}")

    for duplicate in find_duplicates(orr_ids):
        errors.append(f"Duplicate ORR ID: {duplicate}")

    distinction_set = set(distinction_ids)

    # --------------------------------------------------
    # ORR -> distinction traceability and coverage
    # --------------------------------------------------

    covered_distinctions = set()

    for orr in orrs:
        for distinction_id in orr["covers"]:
            if distinction_id not in distinction_set:
                errors.append(
                    f"{orr['id']} covers unknown distinction: "
                    f"{distinction_id}"
                )
            else:
                covered_distinctions.add(distinction_id)

    uncovered = distinction_set - covered_distinctions

    for distinction_id in sorted(uncovered):
        errors.append(f"Uncovered distinction: {distinction_id}")

    actual_coverage = (
        bool(distinction_set)
        and covered_distinctions == distinction_set
    )

    if data["rr5"]["coverage"] != actual_coverage:
        errors.append(
            "RR5 coverage declaration does not match actual coverage"
        )

    # --------------------------------------------------
    # Assumption and revalidation-condition identifiers
    # --------------------------------------------------

    assumption_ids = []
    rc_ids = []

    for orr in orrs:
        for assumption in orr["assumptions"]:
            assumption_ids.append(assumption["id"])

            for rc in assumption["revalidation_conditions"]:
                rc_ids.append(rc["id"])

    for duplicate in find_duplicates(assumption_ids):
        errors.append(f"Duplicate assumption ID: {duplicate}")

    for duplicate in find_duplicates(rc_ids):
        errors.append(
            f"Duplicate revalidation condition ID: {duplicate}"
        )

    # --------------------------------------------------
    # RR5 consistency declaration
    # --------------------------------------------------

    if data["rr5"]["consistency"] and data["rr5"]["issues"]:
        errors.append(
            "RR5 declares consistency=true but reports issues"
        )

    return errors


def main():
    if len(sys.argv) != 3:
        print(
            "Usage: python -m raise2.evaluator.validate_derivation "
            "<schema.json> <derivation.json>"
        )
        sys.exit(2)

    schema_path = Path(sys.argv[1])
    derivation_path = Path(sys.argv[2])

    schema = load_json(schema_path)
    derivation = load_json(derivation_path)

    # --------------------------------------------------
    # JSON Schema validation
    # --------------------------------------------------

    validator = Draft202012Validator(schema)

    schema_errors = sorted(
        validator.iter_errors(derivation),
        key=lambda error: list(error.path),
    )

    if schema_errors:
        print("SCHEMA VALIDATION: FAIL")

        for error in schema_errors:
            location = ".".join(str(p) for p in error.path)
            location = location or "<root>"
            print(f"- {location}: {error.message}")

        sys.exit(1)

    print("SCHEMA VALIDATION: PASS")

    # --------------------------------------------------
    # RAISE2 invariant validation
    # --------------------------------------------------

    invariant_errors = validate_raise2_invariants(derivation)

    if invariant_errors:
        print("RAISE2 VALIDATION: FAIL")

        for error in invariant_errors:
            print(f"- {error}")

        sys.exit(1)

    print("RAISE2 VALIDATION: PASS")


if __name__ == "__main__":
    main()

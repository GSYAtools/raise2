import hashlib
import json
import statistics
import sys
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

RESULTS_ROOT = PROJECT_ROOT / "raise2" / "results"

EXPECTED = {
    "mobstr-H1": {
        "prefix": "H1-run",
        "runs": 30,
        "manifest_sha256":
            "ff1abecb327b47eed4bdbbab250e204692f11551a2da209adc89acbb81bff7cd",
    },
    "mobstr-H3": {
        "prefix": "H3-run",
        "runs": 30,
        "manifest_sha256":
            "8a6a874246faf13c280833c4242e685325a75616d18a50be1205d51a3354bb09",
    },
}

EXPECTED_MODEL = "gpt-5.4-mini-2026-03-17"

EXPECTED_PROTOCOL = (
    "2b84d05ab135a5c318ccabb951dc9f95387e3db71b1719fb48dec7dafb418b42"
)

EXPECTED_EXPERIMENT_SCHEMA = (
    "93a2088e99f065c1a5ca3114f06b6614d3986ec1710702b1cdcf441537a1ce1c"
)

EXPECTED_DERIVATION_SCHEMA = (
    "82c976968517ef181cf5d7fe9236973484a66227c979e56478e1ba7cc8f7f0f8"
)


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            digest.update(chunk)

    return digest.hexdigest()


def median(values):
    if not values:
        return None

    return statistics.median(values)


def summarize_numeric(values):
    if not values:
        return "n/a"

    return (
        f"min={min(values)}, "
        f"median={median(values)}, "
        f"max={max(values)}"
    )


def canonical_semantic_derivation(derivation: dict) -> str:
    """
    Return a canonical representation excluding run_id.

    concern_id is retained because comparisons are only performed
    within the same concern.

    This lets us distinguish semantic derivation variability from
    the intentionally different run identifiers.
    """
    normalized = dict(derivation)
    normalized.pop("run_id", None)

    return json.dumps(
        normalized,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )


def audit_experiment(
    experiment_id: str,
    config: dict,
):
    experiment_dir = RESULTS_ROOT / experiment_id

    errors = []

    crd_counts = []
    orr_counts = []
    assumption_counts = []
    rc_counts = []

    input_tokens = []
    output_tokens = []
    total_tokens = []

    raw_derivation_hashes = []
    semantic_derivation_hashes = []

    statuses = Counter()
    returned_models = Counter()

    for number in range(1, config["runs"] + 1):
        run_id = f"{config['prefix']}-{number:03d}"
        run_dir = experiment_dir / run_id

        metadata_path = run_dir / "metadata.json"
        derivation_path = run_dir / "derivation.json"

        if not run_dir.is_dir():
            errors.append(
                f"{run_id}: missing run directory"
            )
            continue

        if not metadata_path.is_file():
            errors.append(
                f"{run_id}: missing metadata.json"
            )
            continue

        if not derivation_path.is_file():
            errors.append(
                f"{run_id}: missing derivation.json"
            )
            continue

        metadata = load_json(metadata_path)
        derivation = load_json(derivation_path)

        # --------------------------------------------------
        # Configuration consistency
        # --------------------------------------------------

        statuses[metadata.get("status")] += 1
        returned_models[
            metadata.get("returned_model")
        ] += 1

        if metadata.get("status") != "completed_valid":
            errors.append(
                f"{run_id}: status="
                f"{metadata.get('status')}"
            )

        if not metadata.get("validation_passed"):
            errors.append(
                f"{run_id}: validation did not pass"
            )

        if (
            metadata.get("requested_model")
            != EXPECTED_MODEL
        ):
            errors.append(
                f"{run_id}: unexpected requested model"
            )

        if (
            metadata.get("returned_model")
            != EXPECTED_MODEL
        ):
            errors.append(
                f"{run_id}: unexpected returned model"
            )

        if (
            metadata.get("protocol_sha256")
            != EXPECTED_PROTOCOL
        ):
            errors.append(
                f"{run_id}: protocol hash mismatch"
            )

        if (
            metadata.get(
                "experiment_schema_sha256"
            )
            != EXPECTED_EXPERIMENT_SCHEMA
        ):
            errors.append(
                f"{run_id}: experiment schema hash mismatch"
            )

        if (
            metadata.get(
                "derivation_schema_sha256"
            )
            != EXPECTED_DERIVATION_SCHEMA
        ):
            errors.append(
                f"{run_id}: derivation schema hash mismatch"
            )

        if (
            metadata.get("manifest_sha256")
            != config["manifest_sha256"]
        ):
            errors.append(
                f"{run_id}: manifest hash mismatch"
            )

        # --------------------------------------------------
        # Verify recorded derivation hash
        # --------------------------------------------------

        actual_hash = sha256_file(
            derivation_path
        )

        recorded_hash = metadata.get(
            "derivation_sha256"
        )

        if actual_hash != recorded_hash:
            errors.append(
                f"{run_id}: derivation hash mismatch"
            )

        raw_derivation_hashes.append(
            actual_hash
        )

        # --------------------------------------------------
        # Semantic derivation hash
        # --------------------------------------------------

        semantic = canonical_semantic_derivation(
            derivation
        )

        semantic_hash = hashlib.sha256(
            semantic.encode("utf-8")
        ).hexdigest()

        semantic_derivation_hashes.append(
            semantic_hash
        )

        # --------------------------------------------------
        # Structural counts
        # --------------------------------------------------

        distinctions = derivation.get(
            "distinctions",
            []
        )

        orrs = derivation.get(
            "orrs",
            []
        )

        crd_counts.append(
            len(distinctions)
        )

        orr_counts.append(
            len(orrs)
        )

        assumptions = 0
        revalidation_conditions = 0

        for orr in orrs:
            orr_assumptions = orr.get(
                "assumptions",
                []
            )

            assumptions += len(
                orr_assumptions
            )

            for assumption in orr_assumptions:
                revalidation_conditions += len(
                    assumption.get(
                        "revalidation_conditions",
                        []
                    )
                )

        assumption_counts.append(
            assumptions
        )

        rc_counts.append(
            revalidation_conditions
        )

        # --------------------------------------------------
        # Token usage
        # --------------------------------------------------

        usage = metadata.get("usage", {})

        if usage.get("input_tokens") is not None:
            input_tokens.append(
                usage["input_tokens"]
            )

        if usage.get("output_tokens") is not None:
            output_tokens.append(
                usage["output_tokens"]
            )

        if usage.get("total_tokens") is not None:
            total_tokens.append(
                usage["total_tokens"]
            )

    # --------------------------------------------------
    # Summary
    # --------------------------------------------------

    expected_runs = config["runs"]
    observed_runs = len(crd_counts)

    print()
    print("=" * 70)
    print(experiment_id)
    print("=" * 70)

    print(
        f"Expected runs: {expected_runs}"
    )
    print(
        f"Audited runs:  {observed_runs}"
    )

    print(
        "Valid statuses: "
        f"{statuses.get('completed_valid', 0)}"
    )

    print(
        "Distinct raw derivation files: "
        f"{len(set(raw_derivation_hashes))}"
    )

    print(
        "Distinct semantic derivations: "
        f"{len(set(semantic_derivation_hashes))}"
    )

    print(
        f"CRDs/run: {summarize_numeric(crd_counts)}"
    )

    print(
        f"ORRs/run: {summarize_numeric(orr_counts)}"
    )

    print(
        "Assumptions/run: "
        f"{summarize_numeric(assumption_counts)}"
    )

    print(
        "RCs/run: "
        f"{summarize_numeric(rc_counts)}"
    )

    print(
        "Input tokens/run: "
        f"{summarize_numeric(input_tokens)}"
    )

    print(
        "Output tokens/run: "
        f"{summarize_numeric(output_tokens)}"
    )

    print(
        "Total tokens/run: "
        f"{summarize_numeric(total_tokens)}"
    )

    print(
        "Returned models:"
    )

    for model, count in returned_models.items():
        print(
            f"  {model}: {count}"
        )

    if errors:
        print()
        print("CONFIGURATION CONSISTENCY: FAIL")

        for error in errors:
            print(f"- {error}")

    else:
        print()
        print("CONFIGURATION CONSISTENCY: PASS")

    return {
        "experiment_id": experiment_id,
        "expected_runs": expected_runs,
        "audited_runs": observed_runs,
        "valid_runs": statuses.get(
            "completed_valid",
            0,
        ),
        "distinct_raw_derivations": len(
            set(raw_derivation_hashes)
        ),
        "distinct_semantic_derivations": len(
            set(semantic_derivation_hashes)
        ),
        "crd_counts": crd_counts,
        "orr_counts": orr_counts,
        "assumption_counts": assumption_counts,
        "rc_counts": rc_counts,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "configuration_consistency": (
            len(errors) == 0
        ),
        "errors": errors,
    }


def main():
    summaries = []

    for experiment_id, config in EXPECTED.items():
        summaries.append(
            audit_experiment(
                experiment_id,
                config,
            )
        )

    output_path = (
        RESULTS_ROOT
        / "mobstr-eq1-audit.json"
    )

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            summaries,
            f,
            indent=2,
            ensure_ascii=False,
        )
        f.write("\n")

    print()
    print(
        f"Audit written to: {output_path}"
    )

    if not all(
        summary["configuration_consistency"]
        for summary in summaries
    ):
        sys.exit(1)


if __name__ == "__main__":
    main()

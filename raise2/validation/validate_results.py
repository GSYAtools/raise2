import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load(relative_path):
    path = ROOT / relative_path
    with path.open(encoding="utf-8") as f:
        return json.load(f)


eq1 = load(
    "raise2/results/mobstr-eq1-final-results.json"
)

poi = load(
    "raise2/results/mobstr-eq1-poi-conformance.json"
)

eq2 = load(
    "raise2/results/mobstr-eq2-final-results.json"
)

eq3a = load(
    "raise2/results/dtas-eq3-a-final-results.json"
)

eq3b = load(
    "raise2/results/dtas-eq3-b-final-results.json"
)


checks = []


def check(label, actual, expected):
    ok = actual == expected
    checks.append(ok)

    status = "PASS" if ok else "FAIL"

    print(f"{status:4s}  {label}")

    if not ok:
        print(f"      expected: {expected!r}")
        print(f"      actual:   {actual!r}")


print("=" * 70)
print("RAISE2 FROZEN RESULTS VALIDATION")
print("=" * 70)
print()

# --------------------------------------------------
# EQ1
# --------------------------------------------------

print("EQ1")
print("-" * 70)

rr = eq1["reference_recovery"]

expected_reference = {
    "H1-REF1": {
        "all": (9, 30),
        "aligned": (5, 22),
    },
    "H1-REF2": {
        "all": (5, 30),
        "aligned": (3, 22),
    },
    "H3-REF1": {
        "all": (23, 30),
        "aligned": (23, 30),
    },
    "H3-REF2": {
        "all": (0, 30),
        "aligned": (0, 30),
    },
}

for ref_id, expected in expected_reference.items():
    row = rr[ref_id]

    check(
        f"{ref_id} all runs",
        (
            row["all_runs"]["recovered"],
            row["all_runs"]["total"],
        ),
        expected["all"],
    )

    check(
        f"{ref_id} PoI-aligned",
        (
            row["poi_aligned_runs"]["recovered"],
            row["poi_aligned_runs"]["total"],
        ),
        expected["aligned"],
    )


complete = eq1["complete_recovery"]

check(
    "H1 complete recovery all",
    (
        complete["H1"]["all_runs"]["complete"],
        complete["H1"]["all_runs"]["total"],
    ),
    (3, 30),
)

check(
    "H1 complete recovery aligned",
    (
        complete["H1"]["poi_aligned_runs"]["complete"],
        complete["H1"]["poi_aligned_runs"]["total"],
    ),
    (2, 22),
)

check(
    "H3 complete recovery all",
    (
        complete["H3"]["all_runs"]["complete"],
        complete["H3"]["all_runs"]["total"],
    ),
    (0, 30),
)

check(
    "H3 complete recovery aligned",
    (
        complete["H3"]["poi_aligned_runs"]["complete"],
        complete["H3"]["poi_aligned_runs"]["total"],
    ),
    (0, 30),
)


poi_h1 = (
    poi["by_concern"]["H1"]
    ["classification_counts"]
)

poi_h3 = (
    poi["by_concern"]["H3"]
    ["classification_counts"]
)

check(
    "H1 PoI ALIGNED",
    poi_h1.get("ALIGNED", 0),
    22,
)

check(
    "H1 PoI OVEREXTENDED",
    poi_h1.get("OVEREXTENDED", 0),
    8,
)

check(
    "H1 PoI UNDERDETERMINED",
    poi_h1.get("UNDERDETERMINED", 0),
    0,
)

check(
    "H3 PoI ALIGNED",
    poi_h3.get("ALIGNED", 0),
    30,
)

check(
    "H3 PoI OVEREXTENDED",
    poi_h3.get("OVEREXTENDED", 0),
    0,
)

check(
    "H3 PoI UNDERDETERMINED",
    poi_h3.get("UNDERDETERMINED", 0),
    0,
)

check(
    "PoI total runs",
    poi["total_runs"],
    60,
)

check(
    "PoI unanimous classifications",
    poi["agreement_counts"].get(
        "unanimous", 0
    ),
    59,
)

check(
    "PoI majority classifications",
    poi["agreement_counts"].get(
        "majority", 0
    ),
    1,
)

print()

# --------------------------------------------------
# EQ2
# --------------------------------------------------

print("EQ2")
print("-" * 70)

gm = eq2["global_metrics"]

check(
    "EQ2 valid runs",
    eq2["valid_runs"],
    60,
)

check(
    "Lifecycle decision accuracy",
    (
        gm["decision_accuracy"]["correct"],
        gm["decision_accuracy"]["total"],
    ),
    (55, 60),
)

check(
    "Affected-ORR exact accuracy",
    (
        gm["affected_orr_exact_accuracy"]["correct"],
        gm["affected_orr_exact_accuracy"]["total"],
    ),
    (25, 30),
)

check(
    "Return-point accuracy",
    (
        gm["return_point_accuracy"]["correct"],
        gm["return_point_accuracy"]["total"],
    ),
    (20, 20),
)

check(
    "Exact lifecycle outcome",
    (
        gm["exact_outcome_accuracy"]["correct"],
        gm["exact_outcome_accuracy"]["total"],
    ),
    (55, 60),
)


scenarios = {
    row["change_id"]: row
    for row in eq2["scenario_summaries"]
}

expected_exact = {
    "delta-01": 10,
    "delta-02": 10,
    "delta-03": 10,
    "delta-04": 5,
    "delta-05": 10,
    "delta-06": 10,
}

for change_id, expected in expected_exact.items():
    check(
        f"{change_id} exact outcomes",
        scenarios[change_id][
            "exact_outcome_correct"
        ],
        expected,
    )

check(
    "delta-04 distinct outcomes",
    scenarios["delta-04"]["distinct_outcomes"],
    2,
)

check(
    "delta-05 expected return point",
    scenarios["delta-05"]["expected_return_point"],
    "RR2",
)

check(
    "delta-06 expected return point",
    scenarios["delta-06"]["expected_return_point"],
    "RR1",
)

check(
    "EQ2 total tokens",
    eq2["token_usage"]["total_tokens"],
    175076,
)

print()

# --------------------------------------------------
# EQ3-A
# --------------------------------------------------

print("EQ3-A")
print("-" * 70)

check(
    "EQ3-A runs",
    eq3a["runs"],
    30,
)

check(
    "EQ3-A observations",
    eq3a["observations"],
    600,
)

check(
    "EQ3-A threshold",
    eq3a["threshold"],
    0.19,
)

adequacy = eq3a["orr_adequacy"]

check(
    "EQ3-A ORR violations",
    adequacy["violations"],
    30,
)

check(
    "EQ3-A ORR preserved",
    adequacy["preserved"],
    570,
)

check(
    "EQ3-A runs with violation",
    adequacy["runs_with_violation"],
    27,
)

types = eq3a["violation_types"]

check(
    "EQ3-A missed violations",
    types["missed_violations"],
    30,
)

check(
    "EQ3-A false violations",
    types["false_violations"],
    0,
)

check(
    "EQ3-A real violated cycles",
    types["real_violated_cycles"],
    30,
)

check(
    "EQ3-A real satisfied cycles",
    types["real_satisfied_cycles"],
    570,
)

relation = eq3a[
    "accuracy_adequacy_relation"
]

check(
    "EQ3-A inversion exists",
    relation["inversion_exists"],
    True,
)

check(
    "EQ3-A preserved > some violation",
    relation[
        "preserved_observations_with_error_larger_than_some_violation"
    ],
    110,
)

check(
    "EQ3-A violations < some preserved",
    relation[
        "violations_with_error_smaller_than_some_preserved_observation"
    ],
    30,
)

check(
    "EQ3-A maximum preserved error",
    relation[
        "maximum_preserved_error_observation"
    ]["absolute_error"],
    0.08416973824,
)

check(
    "EQ3-A minimum violation error",
    relation[
        "minimum_violation_error_observation"
    ]["absolute_error"],
    0.008019871099999937,
)

print()

# --------------------------------------------------
# EQ3-B
# --------------------------------------------------

print("EQ3-B")
print("-" * 70)

check(
    "EQ3-B experimental unit",
    eq3b["experimental_unit"],
    "independent run",
)

conditions = {
    row["condition_id"]: row
    for row in eq3b["conditions"]
}

expected_conditions = {
    "mfd-0005": (13, 10, 1.3, 0),
    "mfd-0010": (24, 9, 2.4, 0),
    "mfd-0020": (25, 9, 2.5, 0),
    "mfd-0040": (31, 10, 3.1, 0),
}

for condition_id, expected in (
    expected_conditions.items()
):
    row = conditions[condition_id]

    violations, affected, mean_run, false = (
        expected
    )

    check(
        f"{condition_id} cycles",
        row["cycles"],
        200,
    )

    check(
        f"{condition_id} violations",
        row["orr_violations"],
        violations,
    )

    check(
        f"{condition_id} runs affected",
        row["runs_with_violation"],
        affected,
    )

    check(
        f"{condition_id} mean violations/run",
        row["violations_per_run"]["mean"],
        mean_run,
    )

    check(
        f"{condition_id} false violations",
        row["false_violations"],
        false,
    )


comparisons = {
    row["condition_id"]: row
    for row in eq3b["baseline_comparisons"]
}

expected_bootstrap = {
    "mfd-0010": (1.1, 0.3, 1.8),
    "mfd-0020": (1.2, 0.3, 2.1),
    "mfd-0040": (1.8, 1.3, 2.3),
}

for condition_id, expected in (
    expected_bootstrap.items()
):
    row = comparisons[condition_id][
        "orr_violations_per_run"
    ]

    actual = (
        round(
            row["observed_difference"],
            1,
        ),
        round(
            row["ci95_low"],
            1,
        ),
        round(
            row["ci95_high"],
            1,
        ),
    )

    check(
        f"{condition_id} bootstrap ORR delta",
        actual,
        expected,
    )


check(
    "EQ3-B non-decreasing trend",
    eq3b["trend"]["nondecreasing"],
    True,
)

check(
    "EQ3-B strictly increasing trend",
    eq3b["trend"]["strictly_increasing"],
    True,
)

check(
    "EQ3-B bootstrap replicates",
    eq3b["bootstrap"]["replicates"],
    10000,
)

check(
    "EQ3-B bootstrap seed",
    eq3b["bootstrap"]["seed"],
    20261024,
)

check(
    "EQ3-B bootstrap unit",
    eq3b["bootstrap"]["resampling_unit"],
    "run",
)

print()
print("=" * 70)

passed = sum(checks)
total = len(checks)
failed = total - passed

print(f"Checks passed: {passed}/{total}")
print(f"Checks failed: {failed}")

if failed:
    print(
        "FROZEN RESULTS VALIDATION: FAIL"
    )
    raise SystemExit(1)

print(
    "FROZEN RESULTS VALIDATION: PASS"
)

"""Focused negative and precision tests for the review-only business-rule candidate loader."""
from __future__ import annotations

import ast
import json
import subprocess
import sys
import tempfile
import unittest
from decimal import Decimal, localcontext
from pathlib import Path

from packages.application.business_rules_candidate import CandidateBundleError, load_bundle

ROOT = Path(__file__).resolve().parents[1]


def field(field_id="FIELD_1", **overrides):
    value = {
        "id": field_id, "name": field_id, "kind": "text", "unit": "none",
        "source_qualification": {"state": "FIXED", "values": ["MEASURED"]},
        "default": {"state": "NONE"},
        "locking": {
            "value": {"state": "EDITABLE", "reason": "Editable by user"},
            "source": {"state": "EDITABLE", "reason": "Source can be selected"},
        },
        "channel_projections": [{
            "channel": "GUI", "label": field_id, "unit": "none",
            "binding": f"GUI:{field_id}", "notes": "synthetic projection",
        }],
        "basis": ["Synthetic evidence; no production rules changed"],
        "consumers": ["packages.application.business_rules_candidate.CandidateBundle.apply_context"],
        "cases": ["tests/test_business_rules_candidate.py::CandidateLoaderTests"],
        "pending": [], "rule_ids": [],
    }
    value.update(overrides)
    return value


def applicability(scope="ALL_ADOPTED", reason=None, **updates):
    value = {
        "scope": scope, "standard_ids": [], "regions": [], "industries": [],
        "subject_ids": [], "parameter_types": [], "emission_source_types": [],
        "greenhouse_gases": [], "period_from": None, "period_to": None,
        "conditions": {}, "reason": reason,
    }
    value.update(updates)
    return value


def rule(rule_id, *, standard_id=None):
    return {
        "rule_id": rule_id, "rule_domain": "TEST_DOMAIN", "relation": "BASE",
        "description": "synthetic test rule", "standard_id": standard_id, "target_id": None,
        "applicability": applicability(), "priority": 1,
        "origin": "STANDARD_EXPLICIT", "evidence_status": "VERIFIED",
        "supersedes_rule_ids": [], "conflict_resolved": False, "resolution_reason": None,
        "parameter_id": None, "selection_policy": None, "required_factor_id": None,
        "required_factor_version": None, "payload": {}, "applies_to_parameter_ids": [],
        "required_factor_ids": [], "source_location": None, "evidence_source_id": None,
        "confirmation_id": None,
    }


def package(rule_set_id="test.common", *, kind="COMMON", fields=None, rules=None,
            groups=None, adopts=None, dependency=None, policies=None):
    return {
        "schema_version": "1.2", "rule_set_id": rule_set_id, "kind": kind,
        "revision": "r1", "base": "main@204dded5", "dependency": dependency or [],
        "status": "CANDIDATE", "groups": groups or [], "adopts": adopts or [],
        "rules": rules or [], "policies": policies or [], "fields": fields or [],
        "operations": [], "changes": [],
    }


class CandidateLoaderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)

    def write(self, doc, name="package.json"):
        path = self.directory / name
        path.write_text(json.dumps(doc, separators=(",", ":")), encoding="utf-8")
        return path

    def load_one(self, doc):
        return load_bundle([self.write(doc)])

    def test_explicit_states_and_missing_null_blank_empty_are_distinct(self):
        doc = package(fields=[field(
            "F", default={"state": "NONE"},
            source_qualification={"state": "NOT_APPLICABLE", "reason": "No source selector applies"},
        )])
        bundle = self.load_one(doc)
        outcome = bundle.apply_context()["outcomes"]["test.common:F"]
        self.assertEqual(outcome["default"]["value"], {"state": "NONE"})
        self.assertEqual(outcome["source_qualification"]["value"]["state"], "NOT_APPLICABLE")
        for bad in (None, "", [], {}):
            with self.subTest(value=bad), self.assertRaises(CandidateBundleError):
                self.load_one(package(fields=[field("F", default=bad)]))
        missing = package(fields=[field("F")])
        del missing["fields"][0]["default"]
        with self.assertRaisesRegex(CandidateBundleError, "missing required keys"):
            self.load_one(missing)

    def test_fixed_source_empty_and_unregistered_kind_are_rejected(self):
        with self.assertRaises(CandidateBundleError):
            self.load_one(package(fields=[field("F", source_qualification={"state": "FIXED", "values": []})]))
        with self.assertRaises(CandidateBundleError):
            self.load_one(package(fields=[field("F", kind="future_kind")]))

    def test_boolean_default_is_kind_aware(self):
        bundle = self.load_one(package(fields=[field("FLAG", kind="boolean", default={"state": "FIXED", "value": False})]))
        self.assertIs(bundle.apply_context()["outcomes"]["test.common:FLAG"]["default"]["value"]["value"], False)
        with self.assertRaises(CandidateBundleError):
            self.load_one(package(fields=[field("COUNT", kind="integer", default={"state": "FIXED", "value": False})]))
        with self.assertRaises(CandidateBundleError):
            self.load_one(package(fields=[field("FLAG", kind="boolean", default={"state": "FIXED", "value": "false"})]))

    def test_numeric_fixed_defaults_are_finite_decimal_values_and_integer_is_integral(self):
        for kind in ("quantity", "percentage", "integer", "readonly_parameter"):
            for value in ("NaN", "Infinity", "-Infinity", "abc", "1_0", " 1"):
                with self.subTest(kind=kind, value=value), self.assertRaises(CandidateBundleError):
                    self.load_one(package(fields=[field(
                        "VALUE", kind=kind, default={"state": "FIXED", "value": value},
                    )]))
        for value in ("1.5", "1e-1", 1.5):
            with self.subTest(integer_value=value), self.assertRaisesRegex(CandidateBundleError, "integral"):
                self.load_one(package(fields=[field(
                    "COUNT", kind="integer", default={"state": "FIXED", "value": value},
                )]))
        accepted = self.load_one(package(fields=[
            field("COUNT", kind="integer", default={"state": "FIXED", "value": "1.000"}),
            field("AMOUNT", kind="quantity", default={"state": "FIXED", "value": "1.234567890123456789"}),
        ]))
        self.assertEqual(accepted.primary.document["fields"][0]["default"]["value"], "1.000")

    def test_numeric_policy_defaults_are_validated_against_referencing_field_kind(self):
        policy = {
            "id": "numeric-default", "property": "default", "strategy": "UNIQUE_CONTEXT_MATCH",
            "branches": [{
                "id": "numeric-branch", "when": {"tags": {"origin": "CATALOG"}, "ranges": {}},
                "value": {"state": "FIXED", "value": "NaN"},
            }],
        }
        with self.assertRaisesRegex(CandidateBundleError, "finite decimal literal"):
            self.load_one(package(
                fields=[field("AMOUNT", kind="quantity", default={"state": "POLICY", "policy_id": "numeric-default"})],
                policies=[policy],
            ))

    def test_no_legal_sources_and_pending_block_only_selected_field(self):
        doc = package(fields=[
            field("ELECTRICITY", source_qualification={"state": "PENDING", "reason": "Issue014 pending"}),
            field("NO_SOURCE", source_qualification={"state": "NO_LEGAL_SOURCES", "reason": "No registered legal source"}),
            field("FUEL"),
        ])
        bundle = self.load_one(doc)
        electricity = bundle.apply_context(field_ids=["ELECTRICITY"])["outcomes"]["test.common:ELECTRICITY"]
        fuel = bundle.apply_context(field_ids=["FUEL"])["outcomes"]["test.common:FUEL"]
        no_source = bundle.apply_context(field_ids=["NO_SOURCE"])["outcomes"]["test.common:NO_SOURCE"]
        self.assertEqual(electricity["status"], "BLOCKED")
        self.assertEqual(no_source["status"], "BLOCKED")
        self.assertEqual(no_source["source_qualification"]["status"], "NO_LEGAL_SOURCES")
        self.assertEqual(fuel["status"], "READY")
        with self.assertRaisesRegex(CandidateBundleError, "unknown fields"):
            bundle.apply_context(field_ids=["UNREGISTERED"])

    def test_bare_field_id_is_ambiguous_across_selected_packages(self):
        common = package(
            "common.rules", rules=[rule("common.rule")],
            groups=[{"id": "common.group", "rule_ids": ["common.rule"]}],
            fields=[field("DUPLICATE", rule_ids=["common.rule"])],
        )
        primary = package(
            "industry.primary", kind="INDUSTRY", rules=[rule("industry.rule")],
            dependency=[{"rule_set_id": "common.rules", "revision": "r1"}],
            adopts=[{"rule_set_id": "common.rules", "revision": "r1",
                     "group_ids": ["common.group"], "rule_ids": ["common.rule"]}],
            fields=[field("DUPLICATE")],
        )
        bundle = load_bundle(
            [self.write(common, "common.json"), self.write(primary, "primary.json")],
            primary_rule_set_id="industry.primary",
        )
        with self.assertRaisesRegex(CandidateBundleError, "ambiguous unqualified field ID"):
            bundle.apply_context(field_ids=["DUPLICATE"])
        selected = bundle.apply_context(field_ids=["industry.primary:DUPLICATE"])
        self.assertEqual(set(selected["outcomes"]), {"industry.primary:DUPLICATE"})

    def test_policy_refs_and_context_keys_are_strict(self):
        policy = {
            "id": "p", "property": "source_qualification", "strategy": "UNIQUE_CONTEXT_MATCH",
            "branches": [{
                "id": "b", "when": {"tags": {"origin": "CATALOG"}, "ranges": {}},
                "value": {"state": "FIXED", "values": ["MEASURED"]},
            }],
        }
        with self.assertRaisesRegex(CandidateBundleError, "unknown local policy"):
            self.load_one(package(fields=[field("F", default={"state": "POLICY", "policy_id": "missing"})]))
        with self.assertRaisesRegex(CandidateBundleError, "policy property"):
            self.load_one(package(fields=[field("F", default={"state": "POLICY", "policy_id": "p"})], policies=[policy]))
        typo = dict(policy)
        typo["branches"] = [{
            "id": "b", "when": {"tags": {"has_resovler_binding": "true"}, "ranges": {}},
            "value": {"state": "FIXED", "values": ["MEASURED"]},
        }]
        with self.assertRaisesRegex(CandidateBundleError, "context key is not registered"):
            self.load_one(package(fields=[field("F", source_qualification={"state": "POLICY", "policy_id": "p"})], policies=[typo]))

    def test_review_exports_condition_and_decimal_representative_ignores_ambient_precision(self):
        condition = {
            "tags": {"binding_status": "ABSENT"},
            "ranges": {"carbonate_component_count": {
                "min": "1.0000000000000000000000000000000001", "include_min": False,
                "max": "1.0000000000000000000000000000000003", "include_max": False,
            }},
        }
        policy = {
            "id": "p", "property": "default", "strategy": "UNIQUE_CONTEXT_MATCH",
            "branches": [{"id": "narrow", "when": condition, "value": {"state": "FIXED", "value": "matched"}}],
        }
        bundle = self.load_one(package(
            fields=[field("F", default={"state": "POLICY", "policy_id": "p"})], policies=[policy],
        ))
        with localcontext() as context:
            context.prec = 2
            rows = bundle.review_rows()["fields"]
        self.assertEqual(rows[0]["condition"], condition)
        self.assertEqual(rows[0]["default"]["value"], "matched")
        self.assertEqual(rows[0]["evaluation_status"], "READY")
        self.assertTrue(all(p["entry_key"] == "test.common:F" for p in rows[0]["evaluation_problems"]))

    def test_boolean_policy_branch_is_checked_against_each_referencing_field_kind(self):
        policy = {
            "id": "p", "property": "default", "strategy": "UNIQUE_CONTEXT_MATCH",
            "branches": [{
                "id": "b", "when": {"tags": {"origin": "CATALOG"}, "ranges": {}},
                "value": {"state": "FIXED", "value": False},
            }],
        }
        accepted = package(
            fields=[field("FLAG", kind="boolean", default={"state": "POLICY", "policy_id": "p"})],
            policies=[policy],
        )
        self.assertEqual(self.load_one(accepted).primary.rule_set_id, "test.common")
        rejected = package(
            fields=[field("LABEL", kind="text", default={"state": "POLICY", "policy_id": "p"})],
            policies=[policy],
        )
        with self.assertRaisesRegex(CandidateBundleError, "boolean"):
            self.load_one(rejected)

    def test_policy_overlap_is_ambiguous_not_first_match(self):
        when = {"tags": {"origin": "CATALOG"}, "ranges": {}}
        policy = {
            "id": "p", "property": "default", "strategy": "UNIQUE_CONTEXT_MATCH",
            "branches": [
                {"id": "one", "when": when, "value": {"state": "FIXED", "value": "one"}},
                {"id": "two", "when": when, "value": {"state": "FIXED", "value": "two"}},
            ],
        }
        bundle = self.load_one(package(fields=[field("F", default={"state": "POLICY", "policy_id": "p"})], policies=[policy]))
        out = bundle.apply_context({"origin": "CATALOG"}, field_ids=["F"])["outcomes"]["test.common:F"]
        self.assertEqual(out["default"]["status"], "AMBIGUOUS_POLICY_MATCH")
        self.assertEqual(out["status"], "BLOCKED")

    def test_filtered_empty_conditions_fail(self):
        bad = rule("r", standard_id="gbt_test_1")
        bad["applicability"] = applicability("FILTERED")
        with self.assertRaisesRegex(CandidateBundleError, "FILTERED requires"):
            self.load_one(package(rules=[bad]))

    def test_duplicate_key_id_unknown_keys_nan_and_infinity_fail_with_location(self):
        duplicate = self.directory / "duplicate.json"
        duplicate.write_text('{"schema_version":"1.2","schema_version":"1.2"}', encoding="utf-8")
        with self.assertRaisesRegex(CandidateBundleError, r"duplicate\.json:.*duplicate JSON object key"):
            load_bundle([duplicate])
        with self.assertRaisesRegex(CandidateBundleError, "duplicate field ID"):
            self.load_one(package(fields=[field("F"), field("F")]))
        bad = package(fields=[field("F")])
        bad["unknown"] = True
        with self.assertRaisesRegex(CandidateBundleError, "unknown keys"):
            self.load_one(bad)
        for literal in ("NaN", "Infinity", "-Infinity"):
            path = self.directory / f"{literal.replace('-', 'minus')}.json"
            path.write_text('{"schema_version":' + literal + "}", encoding="utf-8")
            with self.assertRaisesRegex(CandidateBundleError, "non-finite"):
                load_bundle([path])

    def test_decimal_json_number_retains_full_precision(self):
        path = self.directory / "decimal.json"
        raw = json.dumps(package(fields=[field("F", kind="quantity")]), separators=(",", ":"))
        raw = raw.replace('"state":"NONE"', '"state":"FIXED","value":0.123456789012345678901234567890123456789', 1)
        path.write_text(raw, encoding="utf-8")
        value = load_bundle([path]).primary.document["fields"][0]["default"]["value"]
        self.assertIsInstance(value, Decimal)
        self.assertEqual(str(value), "0.123456789012345678901234567890123456789")

    def test_adoption_requires_exact_revision_and_known_group(self):
        common = package("common.rules", rules=[rule("common.rule")], groups=[{"id": "g", "rule_ids": ["common.rule"]}])
        industry = package("industry.rules", kind="INDUSTRY",
            dependency=[{"rule_set_id": "common.rules", "revision": "r1"}],
            adopts=[{"rule_set_id": "common.rules", "revision": "r2", "group_ids": ["g"], "rule_ids": ["common.rule"]}])
        cp, ip = self.write(common, "common.json"), self.write(industry, "industry.json")
        with self.assertRaisesRegex(CandidateBundleError, "revision"):
            load_bundle([cp, ip], primary_rule_set_id="industry.rules")
        industry["adopts"][0]["revision"] = "r1"
        industry["adopts"][0]["group_ids"] = ["unknown"]
        ip.write_text(json.dumps(industry), encoding="utf-8")
        with self.assertRaisesRegex(CandidateBundleError, "unknown groups"):
            load_bundle([cp, ip], primary_rule_set_id="industry.rules")

    def test_dependency_cycle_fails(self):
        first = package("first", dependency=[{"rule_set_id": "second", "revision": "r1"}])
        second = package("second", kind="SOFTWARE", dependency=[{"rule_set_id": "first", "revision": "r1"}])
        with self.assertRaisesRegex(CandidateBundleError, "cycle"):
            load_bundle([self.write(first, "first.json"), self.write(second, "second.json")])

    def test_new_common_rules_and_unrelated_industry_do_not_expand_primary(self):
        common = package(
            "common.rules", rules=[rule("common.keep"), rule("common.new")],
            groups=[{"id": "approved", "rule_ids": ["common.keep"]}],
            fields=[field("COMMON_KEEP", rule_ids=["common.keep"]), field("COMMON_NEW", rule_ids=["common.new"])],
        )
        common["operations"] = [
            {"key": "keep-operation", "operation_id": "KEEP_OP", "name": "Keep operation",
             "initial_context": {}, "action": "Keep", "changes": [], "preserves": [], "invalidates": [],
             "confirmation": [], "basis": ["basis"], "cases": ["case"], "pending": [],
             "rule_ids": ["common.keep"]},
            {"key": "new-operation", "operation_id": "NEW_OP", "name": "Unadopted operation",
             "initial_context": {}, "action": "Do not include", "changes": [], "preserves": [], "invalidates": [],
             "confirmation": [], "basis": ["basis"], "cases": ["case"], "pending": [],
             "rule_ids": ["common.new"]},
        ]
        common["changes"] = [{
            "key": "common-change", "change_type": "RULE_ADD", "before": "none", "after": "new rule",
            "reason": "candidate change log", "basis": ["basis"], "pending": [],
        }]
        primary = package(
            "industry.primary", kind="INDUSTRY",
            dependency=[{"rule_set_id": "common.rules", "revision": "r1"}],
            adopts=[{"rule_set_id": "common.rules", "revision": "r1", "group_ids": ["approved"], "rule_ids": ["common.keep"]}],
            fields=[field("PRIMARY_FIELD")],
        )
        other = package("industry.other", kind="INDUSTRY",
            dependency=[{"rule_set_id": "other.common", "revision": "r1"}],
            adopts=[{"rule_set_id": "other.common", "revision": "r1", "group_ids": ["g"], "rule_ids": ["other.rule"]}],
            fields=[field("OTHER_INDUSTRY_FIELD")])
        other_common = package("other.common", rules=[rule("other.rule")],
            groups=[{"id": "g", "rule_ids": ["other.rule"]}],
            fields=[field("OTHER_COMMON_FIELD", rule_ids=["other.rule"])])
        paths = [
            self.write(common, "common.json"), self.write(primary, "primary.json"),
            self.write(other, "other.json"), self.write(other_common, "other_common.json"),
        ]
        bundle = load_bundle(paths, primary_rule_set_id="industry.primary")
        review = bundle.review_rows()
        self.assertEqual({row["field_id"] for row in review["fields"]}, {"PRIMARY_FIELD", "COMMON_KEEP"})
        self.assertEqual({row["operation_id"] for row in review["operations"]}, {"KEEP_OP"})
        self.assertEqual(review["changes"][0]["scope_note"], "Package change log; common-package entries may include non-adopted rules.")
        from packages.core import RuleContext
        resolved = bundle.resolve_rules(RuleContext())
        self.assertEqual({item.rule_id for item in resolved.considered_rules}, {"common.keep"})

    def test_review_keys_change_with_revision_for_all_row_types(self):
        doc = package(fields=[field("F")])
        doc["operations"] = [{
            "key": "operation-key", "operation_id": "SAVE_PROJECT", "name": "Save project",
            "initial_context": {}, "action": "Save draft", "changes": [], "preserves": [],
            "invalidates": [], "confirmation": [], "basis": ["basis"], "cases": ["case"],
            "pending": [], "rule_ids": [],
        }]
        doc["changes"] = [{
            "key": "change-key", "change_type": "MIGRATION", "before": "old",
            "after": "new", "reason": "reason", "basis": ["basis"], "pending": [],
        }]
        first = self.load_one(doc).review_rows()
        revised = dict(doc)
        revised["revision"] = "r2"
        second = load_bundle([self.write(revised, "revision2.json")]).review_rows()
        self.assertNotEqual(first["fields"][0]["review_key"], second["fields"][0]["review_key"])
        self.assertNotEqual(first["operations"][0]["review_key"], second["operations"][0]["review_key"])
        self.assertNotEqual(first["changes"][0]["review_key"], second["changes"][0]["review_key"])
        self.assertEqual(first["operations"][0]["key"], "operation-key")

    def test_policy_standard_id_must_be_registered_by_loaded_rules(self):
        policy = {
            "id": "p", "property": "default", "strategy": "UNIQUE_CONTEXT_MATCH",
            "branches": [{
                "id": "b", "when": {"tags": {"standard_id": "gbt_unregistered_9999"}, "ranges": {}},
                "value": {"state": "FIXED", "value": "x"},
            }],
        }
        with self.assertRaisesRegex(CandidateBundleError, "not registered by this package's effective rules"):
            self.load_one(package(fields=[field("F", default={"state": "POLICY", "policy_id": "p"})], policies=[policy]))

    def test_unrelated_industry_standard_id_does_not_enter_primary_scope(self):
        common = package(
            "common.rules", rules=[rule("common.rule", standard_id="gbt_common")],
            groups=[{"id": "common.group", "rule_ids": ["common.rule"]}],
        )
        primary_policy = {
            "id": "primary.standard", "property": "default", "strategy": "UNIQUE_CONTEXT_MATCH",
            "branches": [{
                "id": "primary.branch", "when": {"tags": {"standard_id": "gbt_unrelated"}, "ranges": {}},
                "value": {"state": "FIXED", "value": "selected"},
            }],
        }
        primary = package(
            "industry.primary", kind="INDUSTRY", rules=[rule("primary.rule", standard_id="gbt_primary")],
            dependency=[{"rule_set_id": "common.rules", "revision": "r1"}],
            adopts=[{"rule_set_id": "common.rules", "revision": "r1",
                     "group_ids": ["common.group"], "rule_ids": ["common.rule"]}],
            policies=[primary_policy],
            fields=[field("VALUE", default={"state": "POLICY", "policy_id": "primary.standard"})],
        )
        other_common = package(
            "other.common", rules=[rule("other.common.rule", standard_id="gbt_unrelated")],
            groups=[{"id": "other.group", "rule_ids": ["other.common.rule"]}],
        )
        unrelated = package(
            "industry.unrelated", kind="INDUSTRY", rules=[rule("unrelated.rule", standard_id="gbt_unrelated")],
            dependency=[{"rule_set_id": "other.common", "revision": "r1"}],
            adopts=[{"rule_set_id": "other.common", "revision": "r1",
                     "group_ids": ["other.group"], "rule_ids": ["other.common.rule"]}],
        )
        paths = [
            self.write(common, "common.json"), self.write(primary, "primary.json"),
            self.write(other_common, "other-common.json"), self.write(unrelated, "unrelated.json"),
        ]
        with self.assertRaisesRegex(CandidateBundleError, "not registered by this package's effective rules"):
            load_bundle(paths, primary_rule_set_id="industry.primary")

        primary["policies"][0]["branches"][0]["when"]["tags"]["standard_id"] = "gbt_primary"
        paths[1].write_text(json.dumps(primary), encoding="utf-8")
        bundle = load_bundle(paths, primary_rule_set_id="industry.primary")
        with self.assertRaisesRegex(CandidateBundleError, "not registered by this package's effective rules"):
            bundle.apply_context({"standard_id": "gbt_unrelated"})

        primary["fields"][0]["rule_ids"] = ["unrelated.rule"]
        paths[1].write_text(json.dumps(primary), encoding="utf-8")
        with self.assertRaisesRegex(CandidateBundleError, "fields references rule .* outside this package's effective rule scope"):
            load_bundle(paths, primary_rule_set_id="industry.primary")

        primary["fields"][0]["rule_ids"] = []
        primary["rules"][0]["supersedes_rule_ids"] = ["unrelated.rule"]
        paths[1].write_text(json.dumps(primary), encoding="utf-8")
        with self.assertRaisesRegex(CandidateBundleError, "supersedes rule .* outside this package's effective rule scope"):
            load_bundle(paths, primary_rule_set_id="industry.primary")

    def test_cli_review_json_and_production_import_boundary(self):
        package_path = self.write(package(fields=[field("F")]))
        review_path = self.directory / "review.json"
        completed = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "validate_business_rules_candidate.py"),
             "--review-json", str(review_path), str(package_path)],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(json.loads(review_path.read_text(encoding="utf-8"))["metadata"]["rule_set_id"], "test.common")
        for folder in (ROOT / "apps", ROOT / "packages"):
            for source in folder.rglob("*.py"):
                if source.name == "business_rules_candidate.py":
                    continue
                tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom):
                        self.assertNotIn("business_rules_candidate", node.module or "", str(source))
                    elif isinstance(node, ast.Import):
                        self.assertTrue(all("business_rules_candidate" not in item.name for item in node.names), str(source))


if __name__ == "__main__":
    unittest.main()

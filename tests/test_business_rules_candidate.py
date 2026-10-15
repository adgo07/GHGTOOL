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
        for value in ("1.5", "1e-1", "100e-2", "1e-0", "1e+2", 1.5):
            with self.subTest(integer_value=value), self.assertRaisesRegex(CandidateBundleError, "integral"):
                self.load_one(package(fields=[field(
                    "COUNT", kind="integer", default={"state": "FIXED", "value": value},
                )]))
        accepted = self.load_one(package(fields=[
            field("COUNT", kind="integer", default={"state": "FIXED", "value": "1.000"}),
            field("JSON_NUMBER_COUNT", kind="integer", default={"state": "FIXED", "value": 1.0}),
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

    def test_policy_branch_values_are_terminal_and_match_the_declared_property(self):
        for property_name, field_property, nested_value in (
            ("default", "default", {"state": "POLICY", "policy_id": "nested"}),
            ("source_qualification", "source_qualification", {"state": "POLICY", "policy_id": "nested"}),
        ):
            with self.subTest(property=property_name), self.assertRaisesRegex(CandidateBundleError, "terminal; nested POLICY"):
                self.load_one(package(
                    fields=[field("FIELD", **{
                        field_property: {"state": "POLICY", "policy_id": "outer"},
                    })],
                    policies=[{
                        "id": "outer", "property": property_name, "strategy": "UNIQUE_CONTEXT_MATCH",
                        "branches": [{
                            "id": "branch", "when": {"tags": {"origin": "CUSTOM"}, "ranges": {}},
                            "value": nested_value,
                        }],
                    }],
                ))

        mismatched = {
            "id": "default-with-source-value", "property": "default",
            "strategy": "UNIQUE_CONTEXT_MATCH", "branches": [{
                "id": "branch", "when": {"tags": {"origin": "CUSTOM"}, "ranges": {}},
                "value": {"state": "FIXED", "values": ["MEASURED"]},
            }],
        }
        with self.assertRaisesRegex(CandidateBundleError, "requires exactly"):
            self.load_one(package(
                fields=[field("FIELD", default={"state": "POLICY", "policy_id": mismatched["id"]})],
                policies=[mismatched],
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

    def test_no_legal_source_policy_blocks_only_its_field_and_keeps_reason(self):
        policy = {
            "id": "electricity-source", "property": "source_qualification",
            "strategy": "UNIQUE_CONTEXT_MATCH", "branches": [{
                "id": "no-legal-source", "when": {"tags": {"origin": "CUSTOM"}, "ranges": {}},
                "value": {"state": "NO_LEGAL_SOURCES", "reason": "No applicable electricity source is registered"},
            }],
        }
        bundle = self.load_one(package(
            fields=[
                field("ELECTRICITY", source_qualification={"state": "POLICY", "policy_id": "electricity-source"}),
                field("FUEL"),
            ],
            policies=[policy],
        ))
        electricity = bundle.apply_context({"origin": "CUSTOM"}, field_ids=["ELECTRICITY"])["outcomes"]["test.common:ELECTRICITY"]
        fuel = bundle.apply_context(field_ids=["FUEL"])["outcomes"]["test.common:FUEL"]
        self.assertEqual(electricity["status"], "BLOCKED")
        self.assertEqual(electricity["source_qualification"]["status"], "NO_LEGAL_SOURCES")
        self.assertEqual(electricity["source_qualification"]["message"], "No applicable electricity source is registered")
        self.assertEqual(fuel["status"], "READY")

    def test_provided_business_source_must_be_in_resolved_field_qualification(self):
        source_policy = {
            "id": "fgd-multi-source", "property": "source_qualification",
            "strategy": "UNIQUE_CONTEXT_MATCH", "branches": [{
                "id": "CUSTOM_FGD_MEASURED",
                "when": {"tags": {"origin": "CUSTOM"}, "ranges": {}},
                "value": {"state": "FIXED", "values": ["MEASURED"]},
            }],
        }
        bundle = self.load_one(package(
            fields=[
                field("FGD_MULTI_GROUP_2", kind="quantity",
                      source_qualification={"state": "POLICY", "policy_id": "fgd-multi-source"}),
                field("FUEL_FIELD", source_qualification={"state": "FIXED", "values": ["STANDARD_DEFAULT"]}),
                field("NO_SOURCE_FIELD", source_qualification={
                    "state": "NOT_APPLICABLE", "reason": "No source selector applies",
                }),
                field("PENDING_SOURCE_FIELD", source_qualification={
                    "state": "PENDING", "reason": "Source qualification needs evidence",
                }),
            ],
            policies=[source_policy],
        ))

        illegal = bundle.apply_context(
            {"origin": "CUSTOM", "business_source": "STANDARD_DEFAULT"},
        )["outcomes"]
        multi = illegal["test.common:FGD_MULTI_GROUP_2"]
        self.assertEqual(multi["status"], "BLOCKED")
        source_problem = next(problem for problem in multi["problems"] if problem["code"] == "SOURCE_NOT_ALLOWED")
        self.assertEqual(source_problem["entry_key"], "test.common:FGD_MULTI_GROUP_2")
        self.assertEqual(source_problem["property"], "source_qualification")
        self.assertEqual(source_problem["business_source"], "STANDARD_DEFAULT")
        self.assertEqual(source_problem["allowed_sources"], ["MEASURED"])
        self.assertEqual(illegal["test.common:FUEL_FIELD"]["status"], "READY")
        self.assertEqual(illegal["test.common:NO_SOURCE_FIELD"]["status"], "READY")
        pending = illegal["test.common:PENDING_SOURCE_FIELD"]
        self.assertEqual(pending["status"], "BLOCKED")
        self.assertNotIn("SOURCE_NOT_ALLOWED", {problem["code"] for problem in pending["problems"]})

        no_source_context = bundle.apply_context(
            {"origin": "CUSTOM"}, field_ids=["FGD_MULTI_GROUP_2"],
        )["outcomes"]["test.common:FGD_MULTI_GROUP_2"]
        self.assertEqual(no_source_context["status"], "READY")
        allowed = bundle.apply_context(
            {"origin": "CUSTOM", "business_source": "MEASURED"}, field_ids=["FGD_MULTI_GROUP_2"],
        )["outcomes"]["test.common:FGD_MULTI_GROUP_2"]
        self.assertEqual(allowed["status"], "READY")

    def test_locking_policy_expands_joint_conditions_and_resolves_concrete_states(self):
        default_policy = {
            "id": "default-policy", "property": "default", "strategy": "UNIQUE_CONTEXT_MATCH",
            "branches": [
                {"id": "DEFAULT_CUSTOM", "when": {"tags": {"origin": "CUSTOM"}, "ranges": {}},
                 "value": {"state": "FIXED", "value": "custom default"}},
                {"id": "DEFAULT_CATALOG", "when": {"tags": {"origin": "CATALOG"}, "ranges": {}},
                 "value": {"state": "FIXED", "value": "catalog default"}},
            ],
        }
        source_policy = {
            "id": "source-policy", "property": "source_qualification", "strategy": "UNIQUE_CONTEXT_MATCH",
            "branches": [
                {"id": "SOURCE_CUSTOM", "when": {"tags": {"origin": "CUSTOM"}, "ranges": {}},
                 "value": {"state": "FIXED", "values": ["MEASURED"]}},
                {"id": "SOURCE_CATALOG", "when": {"tags": {"origin": "CATALOG"}, "ranges": {}},
                 "value": {"state": "FIXED", "values": ["STANDARD_DEFAULT"]}},
            ],
        }
        locking_policy = {
            "id": "parameter-locking", "property": "locking", "strategy": "UNIQUE_CONTEXT_MATCH",
            "branches": [{
                "id": "MEASURED_LOCKING",
                "when": {"tags": {"business_source": "MEASURED"}, "ranges": {}},
                "value": {
                    "value": {"state": "EDITABLE", "reason": "Measured values are editable"},
                    "source": {"state": "LOCKED", "reason": "Source identity is retained"},
                },
            }],
        }
        policies = [default_policy, source_policy, locking_policy]
        bundle = self.load_one(package(
            fields=[field(
                "PARAMETER", kind="text",
                default={"state": "POLICY", "policy_id": "default-policy"},
                source_qualification={"state": "POLICY", "policy_id": "source-policy"},
                locking={"state": "POLICY", "policy_id": "parameter-locking"},
            )],
            policies=policies,
        ))
        evaluated = bundle.apply_context(
            {"origin": "CUSTOM", "business_source": "MEASURED"}, field_ids=["PARAMETER"],
        )["outcomes"]["test.common:PARAMETER"]
        self.assertEqual(evaluated["status"], "READY")
        self.assertEqual(evaluated["locking"]["value"]["state"], "EDITABLE")
        self.assertEqual(evaluated["locking"]["source"]["state"], "LOCKED")
        unresolved = bundle.apply_context(field_ids=["PARAMETER"])["outcomes"]["test.common:PARAMETER"]
        self.assertEqual(unresolved["locking_outcome"]["status"], "MISSING_CONTEXT")
        self.assertEqual(unresolved["status"], "BLOCKED")

        rows = bundle.review_rows()["fields"]
        self.assertEqual(len(rows), 2)
        resolved_rows = [row for row in rows if row["condition_status"] == "INTERSECTED"]
        self.assertEqual(len(resolved_rows), 2)
        for row in resolved_rows:
            self.assertEqual(set(row["condition_ids"]), {"default", "source_qualification", "locking"})
            self.assertIn("test.common|r1|PARAMETER|COMBINED|", row["review_key"])
            self.assertEqual(row["locking_outcome"]["status"], "RESOLVED")
            self.assertEqual(row["locking"]["value"]["state"], "EDITABLE")
            if row["condition_ids"]["source_qualification"] == "SOURCE_CUSTOM":
                self.assertEqual(row["evaluation_status"], "READY")
            else:
                self.assertEqual(row["evaluation_status"], "BLOCKED")
                self.assertIn("SOURCE_NOT_ALLOWED", {
                    problem["code"] for problem in row["evaluation_problems"]
                })

    def test_review_reports_each_uncomposable_branch_once(self):
        default_policy = {
            "id": "default-policy", "property": "default", "strategy": "UNIQUE_CONTEXT_MATCH",
            "branches": [
                {"id": "CUSTOM", "when": {"tags": {"origin": "CUSTOM"}, "ranges": {}},
                 "value": {"state": "FIXED", "value": "custom"}},
                {"id": "CATALOG", "when": {"tags": {"origin": "CATALOG"}, "ranges": {}},
                 "value": {"state": "FIXED", "value": "catalog"}},
            ],
        }
        source_policy = {
            "id": "source-policy", "property": "source_qualification", "strategy": "UNIQUE_CONTEXT_MATCH",
            "branches": [{
                "id": "CUSTOM_SOURCE", "when": {"tags": {"origin": "CUSTOM"}, "ranges": {}},
                "value": {"state": "FIXED", "values": ["MEASURED"]},
            }],
        }
        bundle = self.load_one(package(
            fields=[field("FIELD", kind="text",
                          default={"state": "POLICY", "policy_id": "default-policy"},
                          source_qualification={"state": "POLICY", "policy_id": "source-policy"})],
            policies=[default_policy, source_policy],
        ))
        rows = bundle.review_rows()["fields"]
        diagnostics = [row for row in rows if row["condition_status"] == "UNCOMPOSABLE_BRANCH"]
        self.assertEqual(len(rows), 2)
        self.assertEqual(len(diagnostics), 1)
        self.assertEqual(diagnostics[0]["uncomposable_branch"]["branch_id"], "CATALOG")
        self.assertEqual(diagnostics[0]["condition"]["tags"], {"origin": "CATALOG"})
        self.assertEqual(diagnostics[0]["condition_ids"], {"default": "CATALOG"})
        self.assertEqual(diagnostics[0]["evaluation_status"], "UNCOMPOSABLE_BRANCH")

    def test_condition_intersection_respects_open_range_boundaries(self):
        bundle = self.load_one(package())
        empty_count, error = bundle._intersect_conditions([
            {"tags": {}, "ranges": {"carbonate_component_count": {"min": "1", "include_min": False}}},
            {"tags": {}, "ranges": {"carbonate_component_count": {"max": "2", "include_max": False}}},
        ])
        self.assertIsNone(empty_count)
        self.assertIn("no non-negative integer", error)
        integer_overlap, error = bundle._intersect_conditions([
            {"tags": {}, "ranges": {"carbonate_component_count": {"min": "1", "include_min": False}}},
            {"tags": {}, "ranges": {"carbonate_component_count": {"max": "3", "include_max": False}}},
        ])
        self.assertIsNone(error)
        representative = bundle._representative_context(integer_overlap)
        self.assertEqual(representative["carbonate_component_count"], Decimal("2"))
        self.assertEqual(representative["carbonate_component_count"] % 1, 0)
        empty, error = bundle._intersect_conditions([
            {"tags": {}, "ranges": {"carbonate_component_count": {"min": "2.000", "include_min": False}}},
            {"tags": {}, "ranges": {"carbonate_component_count": {"max": "2", "include_max": True}}},
        ])
        self.assertIsNone(empty)
        self.assertIn("boundary is excluded", error)
        for invalid_count in (Decimal("1.5"), Decimal("-1")):
            with self.subTest(count=invalid_count), self.assertRaisesRegex(CandidateBundleError, "non-negative integer count"):
                bundle.apply_context({"carbonate_component_count": invalid_count})

    def test_count_range_conditions_require_nonnegative_integer_domain(self):
        policy = {
            "id": "count-policy", "property": "default", "strategy": "UNIQUE_CONTEXT_MATCH",
            "branches": [{
                "id": "empty-integer-interval",
                "when": {"tags": {}, "ranges": {"carbonate_component_count": {
                    "min": "1", "include_min": False, "max": "2", "include_max": False,
                }}},
                "value": {"state": "FIXED", "value": "x"},
            }],
        }
        with self.assertRaisesRegex(CandidateBundleError, "no non-negative integer"):
            self.load_one(package(
                fields=[field("COUNTED", kind="text", default={"state": "POLICY", "policy_id": "count-policy"})],
                policies=[policy],
            ))

        policy["branches"][0]["when"]["ranges"]["carbonate_component_count"]["min"] = "1.5"
        with self.assertRaisesRegex(CandidateBundleError, "non-negative integer literals"):
            self.load_one(package(
                fields=[field("COUNTED", kind="text", default={"state": "POLICY", "policy_id": "count-policy"})],
                policies=[policy],
            ))

    def test_explicit_empty_text_default_is_distinct_from_missing_and_nontext_blank(self):
        direct = self.load_one(package(fields=[field(
            "EMPTY_TEXT", kind="text", default={"state": "FIXED", "value": ""},
        )]))
        outcome = direct.apply_context()["outcomes"]["test.common:EMPTY_TEXT"]
        self.assertEqual(outcome["status"], "READY")
        self.assertEqual(outcome["default"]["value"]["value"], "")
        policy = {
            "id": "empty-text", "property": "default", "strategy": "UNIQUE_CONTEXT_MATCH",
            "branches": [{
                "id": "empty", "when": {"tags": {"origin": "CUSTOM"}, "ranges": {}},
                "value": {"state": "FIXED", "value": ""},
            }],
        }
        policy_bundle = self.load_one(package(
            fields=[field("POLICY_EMPTY_TEXT", kind="text", default={"state": "POLICY", "policy_id": "empty-text"})],
            policies=[policy],
        ))
        policy_outcome = policy_bundle.apply_context({"origin": "CUSTOM"})["outcomes"]["test.common:POLICY_EMPTY_TEXT"]
        self.assertEqual(policy_outcome["default"]["value"]["value"], "")
        for kind in ("enum", "quantity", "integer", "boolean"):
            with self.subTest(kind=kind), self.assertRaises(CandidateBundleError):
                self.load_one(package(fields=[field(kind, kind=kind, default={"state": "FIXED", "value": ""})]))
        with self.assertRaises(CandidateBundleError):
            self.load_one(package(fields=[field("WHITESPACE", kind="text", default={"state": "FIXED", "value": " "})]))

    def test_review_json_serializes_large_integers_as_exact_strings(self):
        from packages.application.business_rules_candidate import _json_safe
        self.assertEqual(_json_safe(2**53), str(2**53))
        self.assertEqual(_json_safe(-(2**80)), str(-(2**80)))
        self.assertEqual(_json_safe(2**53 - 1), 2**53 - 1)
        self.assertIs(_json_safe(True), True)
        self.assertEqual(_json_safe({"large": 2**53}), {"large": str(2**53)})

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

    def test_review_exports_integer_count_condition_and_representative_ignores_ambient_precision(self):
        condition = {
            "tags": {"binding_status": "ABSENT"},
            "ranges": {"carbonate_component_count": {
                "min": "1", "include_min": False,
                "max": "3", "include_max": False,
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
        self.assertEqual(rows[0]["condition"]["ranges"]["carbonate_component_count"]["min"], "1")
        self.assertEqual(rows[0]["condition"]["ranges"]["carbonate_component_count"]["max"], "3")
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

from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import date, datetime, timezone
from decimal import Decimal
import unittest

from packages.core import (
    ActivityData,
    ActivityDataContract,
    ActivityDataSource,
    ActivitySourceLevel,
    AggregationContract,
    AggregationLine,
    AggregationOperation,
    EffectiveRuleResolver,
    Factor,
    FactorSourceMode,
    IssueLevel,
    Parameter,
    ParameterResolutionContext,
    ParameterResolver,
    ParameterSelectionMethod,
    ParameterSelectionPolicy,
    ParameterType,
    ParameterValueCategory,
    RuleApplicability,
    RuleContext,
    RuleDefinition,
    RuleEvidenceStatus,
    RuleOrigin,
    RuleRelation,
    RuleRepository,
    ValueType,
    ReviewStatus,
    default_g05_rules,
)


STANDARD_ID = "gbt_32151_34_2024"
COMMON_ID = "gbt_32150_2025"
NOW = datetime(2026, 9, 12, 12, 0, tzinfo=timezone.utc)


class MemoryParameterRepository:
    def __init__(self, parameters: tuple[Parameter, ...], factors: tuple[Factor, ...]) -> None:
        self.parameters = parameters
        self.factors = factors

    def get_parameter(self, parameter_id: str) -> Parameter | None:
        return next((item for item in self.parameters if item.parameter_id == parameter_id), None)

    def get_factor(self, factor_id: str) -> Factor | None:
        return next((item for item in self.factors if item.factor_id == factor_id), None)

    def list_factors(self, parameter_id: str) -> tuple[Factor, ...]:
        return tuple(item for item in self.factors if item.parameter_id == parameter_id)


class MemoryRuleRepository:
    def __init__(self, rules: tuple[RuleDefinition, ...]) -> None:
        self.rules = rules

    def list_rules(self, standard_id: str | None = None) -> tuple[RuleDefinition, ...]:
        if standard_id is None:
            return tuple(rule for rule in self.rules if rule.standard_id is None)
        return tuple(rule for rule in self.rules if rule.standard_id == standard_id)


def rule(
    rule_id: str,
    relation: RuleRelation,
    *,
    domain: str = "scope",
    target_id: str = "scope.total",
    standard_id: str = COMMON_ID,
    applicability: RuleApplicability = RuleApplicability(),
    priority: int = 100,
    supersedes: tuple[str, ...] = (),
    conflict_resolved: bool = False,
) -> RuleDefinition:
    return RuleDefinition(
        rule_id=rule_id,
        rule_domain=domain,
        target_id=target_id,
        relation=relation,
        description=f"测试规则 {rule_id}",
        standard_id=standard_id,
        applicability=applicability,
        priority=priority,
        origin=RuleOrigin.STANDARD_EXPLICIT,
        evidence_status=(
            RuleEvidenceStatus.CONFLICT
            if relation is RuleRelation.CONFLICT_REVIEW
            else RuleEvidenceStatus.VERIFIED
        ),
        supersedes_rule_ids=supersedes,
        conflict_resolved=conflict_resolved,
        resolution_reason="已由行业规则明确覆盖" if conflict_resolved else None,
    )


def factor(
    factor_id: str,
    parameter_id: str,
    value: str,
    value_type: ValueType,
    *,
    version: str = "2025",
    factor_year: int = 2025,
    applicable_standard_ids: tuple[str, ...] = (STANDARD_ID,),
    source_id: str | None = "SRC-TEST",
    review_status: ReviewStatus = ReviewStatus.VERIFIED,
    unit: str = "ratio",
    subject_id: str = "subject.test",
) -> Factor:
    return Factor(
        factor_id=factor_id,
        parameter_id=parameter_id,
        subject_id=subject_id,
        parameter_type=ParameterType.GWP,
        value=value,
        unit=unit,
        version=version,
        value_type=value_type,
        review_status=review_status,
        source_id=source_id,
        source_location="测试来源条款",
        applicable_standard_ids=applicable_standard_ids,
        factor_year=factor_year,
    )


class G05RuleTests(unittest.TestCase):
    def test_rule_relations_preserve_provenance_and_explicit_override(self) -> None:
        base = rule("GEN-RULE-BASE", RuleRelation.BASE)
        conflict = rule("GEN-RULE-CONFLICT", RuleRelation.CONFLICT_REVIEW)
        override = rule(
            "CAR-RULE-OVERRIDE",
            RuleRelation.OVERRIDE,
            standard_id=STANDARD_ID,
            supersedes=(base.rule_id, conflict.rule_id),
        )
        specialized = rule(
            "CAR-RULE-SPECIALIZE",
            RuleRelation.SPECIALIZE,
            domain="boundary",
            target_id="boundary.entity",
            standard_id=STANDARD_ID,
            applicability=RuleApplicability(standard_ids=(STANDARD_ID,)),
        )
        boundary_base = rule(
            "GEN-RULE-BOUNDARY",
            RuleRelation.BASE,
            domain="boundary",
            target_id="boundary.entity",
        )
        effective = EffectiveRuleResolver().resolve(
            (base, conflict, boundary_base),
            (override, specialized),
            RuleContext(standard_id=STANDARD_ID),
        )
        self.assertFalse(effective.blocked)
        self.assertIn(override.rule_id, effective.rule_ids)
        self.assertIn(specialized.rule_id, effective.rule_ids)
        self.assertEqual(
            set(effective.overridden_rule_ids),
            {base.rule_id, conflict.rule_id},
        )
        self.assertIn(boundary_base.rule_id, effective.inherited_rule_ids)

    def test_unresolved_conflict_blocks_effective_rules(self) -> None:
        conflict = rule("GEN-RULE-UNRESOLVED", RuleRelation.CONFLICT_REVIEW)
        effective = EffectiveRuleResolver().resolve(
            (conflict,),
            (),
            RuleContext(standard_id=STANDARD_ID),
        )
        self.assertTrue(effective.blocked)
        self.assertTrue(
            any(problem.code == "GEN-RULE-CONFLICT-REVIEW" for problem in effective.problems)
        )
        with self.assertRaises(ValueError):
            effective.ensure_resolved()

    def test_extend_and_supplement_keep_common_provenance(self) -> None:
        boundary_base = rule(
            "GEN-RULE-BOUNDARY-BASE",
            RuleRelation.BASE,
            domain="boundary",
            target_id="boundary.entity",
            standard_id=None,
        )
        boundary_extension = rule(
            "CAR-RULE-BOUNDARY-EXTEND",
            RuleRelation.EXTEND,
            domain="boundary",
            target_id="boundary.entity",
            standard_id=STANDARD_ID,
        )
        evidence_base = rule(
            "GEN-RULE-EVIDENCE-BASE",
            RuleRelation.BASE,
            domain="evidence",
            target_id="evidence.source",
            standard_id=None,
        )
        evidence_supplement = rule(
            "CAR-RULE-EVIDENCE-SUPPLEMENT",
            RuleRelation.SUPPLEMENT,
            domain="evidence",
            target_id="evidence.source",
            standard_id=STANDARD_ID,
        )
        rule_repository = MemoryRuleRepository(
            (boundary_base, boundary_extension, evidence_base, evidence_supplement)
        )
        self.assertIsInstance(rule_repository, RuleRepository)
        effective = EffectiveRuleResolver().resolve(
            rule_repository.list_rules(),
            rule_repository.list_rules(STANDARD_ID),
            RuleContext(standard_id=STANDARD_ID),
        )
        self.assertFalse(effective.blocked)
        self.assertIn(boundary_base.rule_id, effective.rule_ids)
        self.assertIn(boundary_extension.rule_id, effective.rule_ids)
        self.assertIn(evidence_base.rule_id, effective.rule_ids)
        self.assertIn(evidence_supplement.rule_id, effective.rule_ids)
        self.assertTrue(
            any(
                trace.rule_id == evidence_supplement.rule_id
                and trace.action.value == "SUPPLEMENTED"
                for trace in effective.traces
            )
        )

    def test_default_rules_select_standard_and_official_values(self) -> None:
        parameter = Parameter(
            "electricity_emission_factor_national",
            "purchased_electricity",
            ParameterType.ELECTRICITY_EMISSION_FACTOR,
            "全国电力因子",
            "tCO2/MWh",
            "2025",
        )
        national = Factor(
            factor_id="electricity_national_average_2024",
            parameter_id=parameter.parameter_id,
            subject_id=parameter.subject_id,
            parameter_type=parameter.parameter_type,
            value="0.5306",
            unit="tCO2/MWh",
            version="2024",
            value_type=ValueType.GOVERNMENT_PUBLISHED,
            review_status=ReviewStatus.VERIFIED,
            source_id="SRC-ELEC-2024-OFFICIAL",
            source_location="测试官方 2024 年全国因子",
            applicable_standard_ids=(STANDARD_ID,),
            factor_year=2024,
        )
        ningxia = Factor(
            factor_id="electricity_ningxia_2023",
            parameter_id=parameter.parameter_id,
            subject_id=parameter.subject_id,
            parameter_type=parameter.parameter_type,
            value="0.6187",
            unit="tCO2/MWh",
            version="2025",
            value_type=ValueType.GOVERNMENT_PUBLISHED,
            review_status=ReviewStatus.VERIFIED,
            source_id="SRC-ELEC-NX-2023",
            source_location="测试区域因子",
            applicable_standard_ids=(STANDARD_ID,),
            factor_year=2023,
        )
        resolver = ParameterResolver.with_default_g05_rules(
            MemoryParameterRepository((parameter,), (national, ningxia))
        )
        result = resolver.resolve(
            ParameterResolutionContext(
                parameter_id=parameter.parameter_id,
                standard_id=STANDARD_ID,
                subject_id=parameter.subject_id,
                parameter_type=parameter.parameter_type,
                region="ningxia",
                electricity_type="ordinary_purchase",
            )
        )
        self.assertIsNotNone(result.recommended)
        assert result.recommended is not None
        self.assertEqual(result.recommended.factor.factor_id, national.factor_id)
        self.assertEqual(result.recommended.factor.value, Decimal("0.5306"))
        self.assertIn(ningxia.factor_id, {item.factor_id for item in result.alternatives})
        self.assertEqual(result.selection_method, ParameterSelectionMethod.SYSTEM_RECOMMENDED)
        self.assertNotIn(
            "CAR-RULE-NONFOSSIL-POWER-001",
            {item.rule_id for item in result.effective_rules.rules_for_parameter(parameter.parameter_id)},
        )
        self.assertTrue(
            any(
                trace.rule_id == "CAR-RULE-POWER-HEAT-001"
                and trace.action.value == "SELECTED"
                for trace in result.effective_rules.traces
            )
        )
        self.assertTrue(
            any(
                trace.rule_id == "GEN-RULE-ELECTRICITY-001"
                and trace.action.value == "INHERITED"
                for trace in result.effective_rules.traces
            )
        )

    def test_heat_measured_value_precedes_default_and_falls_back_with_warning(self) -> None:
        parameter = Parameter(
            "heat_emission_factor_default",
            "purchased_heat",
            ParameterType.HEAT_EMISSION_FACTOR,
            "外购热力排放因子",
            "tCO2/GJ",
            "2025",
        )
        default = Factor(
            factor_id="heat_default_2025",
            parameter_id=parameter.parameter_id,
            subject_id=parameter.subject_id,
            parameter_type=parameter.parameter_type,
            value="0.11",
            unit="tCO2/GJ",
            version="2025",
            value_type=ValueType.STANDARD_DEFAULT,
            review_status=ReviewStatus.VERIFIED,
            source_id="SRC-32150-2025",
            source_location="GB/T 32150—2025第7.5.6～7.5.7条",
            applicable_standard_ids=(STANDARD_ID,),
            factor_year=2025,
        )
        measured = Factor(
            factor_id="heat_measured_2026",
            parameter_id=parameter.parameter_id,
            subject_id=parameter.subject_id,
            parameter_type=parameter.parameter_type,
            value="0.08",
            unit="tCO2/GJ",
            version="2026",
            value_type=ValueType.MEASURED,
            review_status=ReviewStatus.VERIFIED,
            source_id="LAB-HEAT-2026",
            source_location="企业供热单位检测报告",
            applicable_standard_ids=(STANDARD_ID,),
            factor_year=2026,
        )
        repository = MemoryParameterRepository((parameter,), (default,))
        resolver = ParameterResolver.with_default_g05_rules(repository)
        fallback = resolver.resolve(
            ParameterResolutionContext(
                parameter_id=parameter.parameter_id,
                standard_id=STANDARD_ID,
                subject_id=parameter.subject_id,
                parameter_type=parameter.parameter_type,
                measured_factor=measured,
                measured_value_available=True,
                measured_evidence_available=False,
            )
        )
        self.assertEqual(fallback.recommended.factor.factor_id, default.factor_id)  # type: ignore[union-attr]
        self.assertTrue(any(item.code == "GEN-VAL-MEASURED-NO-TEST-INFO" for item in fallback.warnings))
        self.assertIn(
            "CAR-RULE-POWER-HEAT-001",
            {item.rule_id for item in fallback.effective_rules.rules_for_parameter(parameter.parameter_id)},
        )
        self.assertTrue(
            any(
                trace.rule_id == "GEN-RULE-HEAT-001"
                and trace.action.value == "INHERITED"
                for trace in fallback.effective_rules.traces
            )
        )

        measured_result = resolver.resolve(
            ParameterResolutionContext(
                parameter_id=parameter.parameter_id,
                standard_id=STANDARD_ID,
                subject_id=parameter.subject_id,
                parameter_type=parameter.parameter_type,
                measured_factor=measured,
                measured_value_available=True,
                measured_evidence_available=True,
            )
        )
        self.assertEqual(measured_result.recommended.factor.factor_id, measured.factor_id)  # type: ignore[union-attr]
        self.assertEqual(measured_result.selection_method, ParameterSelectionMethod.ENTERPRISE_MEASURED)

    def test_ambiguous_value_requires_confirmation_and_snapshot_preserves_version(self) -> None:
        parameter_id = "gwp_n2o_100"
        parameter = Parameter(
            parameter_id,
            "n2o",
            ParameterType.GWP,
            "N2O GWP100",
            "ratio",
            "2026",
        )
        ar6 = factor(
            "gwp_n2o_ar6",
            parameter_id,
            "273",
            ValueType.SCIENTIFIC_REFERENCE,
            version="AR6",
            factor_year=2021,
            subject_id="n2o",
        )
        ar5 = factor(
            "gwp_n2o_ar5",
            parameter_id,
            "265",
            ValueType.SCIENTIFIC_REFERENCE,
            version="AR5",
            factor_year=2021,
            subject_id="n2o",
        )
        common_rule = RuleDefinition(
            rule_id="GEN-PAR-GWP-N2O",
            rule_domain="parameter_selection",
            target_id=parameter_id,
            parameter_id=parameter_id,
            relation=RuleRelation.BASE,
            description="系统 GWP 测试规则",
            applicability=RuleApplicability(standard_ids=(STANDARD_ID,)),
            selection_policy=ParameterSelectionPolicy.SYSTEM_GWP,
        )
        repository = MemoryParameterRepository((parameter,), (ar6, ar5))
        resolver = ParameterResolver(
            repository,
            common_rules=(common_rule,),
        )
        context = ParameterResolutionContext(
            parameter_id=parameter_id,
            standard_id=STANDARD_ID,
            subject_id="n2o",
            parameter_type=ParameterType.GWP,
        )
        ambiguous = resolver.resolve(context)
        self.assertIsNone(ambiguous.recommended)
        self.assertTrue(ambiguous.requires_confirmation)
        self.assertTrue(any(item.code == "GEN-PAR-CONFIRMATION-REQUIRED" for item in ambiguous.warnings))

        confirmed = resolver.resolve(
            ParameterResolutionContext(
                parameter_id=context.parameter_id,
                standard_id=context.standard_id,
                subject_id=context.subject_id,
                parameter_type=context.parameter_type,
                confirmed_factor_id=ar6.factor_id,
                confirmation_reason="本报告制度明确指定 IPCC AR6。",
            )
        )
        self.assertEqual(confirmed.recommended.factor.factor_id, ar6.factor_id)  # type: ignore[union-attr]
        self.assertEqual(confirmed.selection_method, ParameterSelectionMethod.USER_SELECTED_LIBRARY_VALUE)
        snapshot = confirmed.to_snapshot("snapshot.g05.001", NOW)
        self.assertEqual(snapshot.factor_version, "AR6")
        self.assertEqual(snapshot.source_location, "测试来源条款")
        repository.factors = (replace(ar6, value="274"), ar5)
        self.assertEqual(snapshot.value_used, Decimal("273"))
        with self.assertRaises(FrozenInstanceError):
            snapshot.value_used = Decimal("1")  # type: ignore[misc]

    def test_default_rules_match_frozen_ids_sources_and_conflict_paths(self) -> None:
        common, industry = default_g05_rules()
        common_by_id = {item.rule_id: item for item in common}
        industry_by_id = {item.rule_id: item for item in industry}

        expected_common = {
            "GEN-RULE-REFERENCE-MODE-001",
            "GEN-RULE-INDUSTRY-DELEGATION-001",
            "GEN-RULE-GHG-SCOPE-001",
            "GEN-RULE-BOUNDARY-ENTITY-001",
            "GEN-RULE-BOUNDARY-SYSTEMS-001",
            "GEN-RULE-BOUNDARY-AUXILIARY-001",
            "GEN-RULE-BOUNDARY-ANCILLARY-001",
            "GEN-RULE-BOUNDARY-INCLUDED-SOURCES-001",
            "GEN-RULE-BIOMASS-001",
            "GEN-RULE-REMOVAL-001",
            "GEN-RULE-ACTIVITY-PRIMARY-001",
            "GEN-RULE-ACTIVITY-PROXY-001",
            "GEN-RULE-ACTIVITY-SECONDARY-001",
            "GEN-RULE-FUGITIVE-EXECUTION-BLOCK-001",
            "GEN-RULE-TOTAL-COVERAGE-REQUIRED-001",
            "GEN-MTH-FACTOR-001",
            "GEN-MTH-MATERIAL-BALANCE-001",
            "GEN-MTH-MEASURED-001",
            "GEN-FML-FACTOR-001",
            "GEN-FML-MATERIAL-BALANCE-001",
            "GEN-FML-FUEL-AGG-001",
            "GEN-FML-FUGITIVE-AGG-001",
            "GEN-FML-PROCESS-AGG-001",
            "GEN-FML-WASTE-AGG-001",
            "GEN-FML-PURCHASED-ELECTRICITY-001",
            "GEN-FML-PURCHASED-HEAT-001",
            "GEN-RULE-TOTAL-001",
            "GEN-FML-TOTAL-001",
            "GEN-FML-EXPORTED-ELECTRICITY-001",
            "GEN-FML-EXPORTED-HEAT-001",
            "GEN-AGG-FUEL-ADD",
            "GEN-AGG-PROCESS-ADD",
            "GEN-AGG-WASTE-ADD",
            "GEN-AGG-FUGITIVE-REVIEW-001",
            "GEN-RULE-FACTOR-PRIORITY-001",
            "GEN-RULE-ELECTRICITY-001",
            "GEN-RULE-HEAT-001",
            "GEN-RULE-PRINCIPLE-001",
            "GEN-RULE-SOURCE-CATALOG-001",
            "GEN-RULE-WORKFLOW-001",
            "GEN-RULE-QA-001",
        }
        expected_industry = {
            "CAR-RULE-GHG-SCOPE-001",
            "CAR-RULE-BOUNDARY-001",
            "CAR-RULE-FUEL-001",
            "CAR-RULE-PROCESS-001",
            "CAR-RULE-POWER-HEAT-001",
            "CAR-RULE-TOTAL-001",
            "CAR-RULE-TOTAL-COVERAGE-001",
            "CAR-RULE-FUGITIVE-COVERAGE-001",
            "CAR-RULE-NONFOSSIL-POWER-001",
            "CAR-RULE-QA-001",
        }
        self.assertEqual(set(common_by_id), expected_common)
        self.assertEqual(set(industry_by_id), expected_industry)
        self.assertFalse(
            any(item.rule_id.startswith(("GEN-PAR-", "CAR-PAR-")) for item in (*common, *industry))
        )
        for item in common:
            self.assertIsNotNone(item.source_location)
            self.assertIsNotNone(item.evidence_source_id)
        source_markers = {
            "GEN-RULE-ACTIVITY-PRIMARY-001": "表2",
            "GEN-RULE-INDUSTRY-DELEGATION-001": "第7.5.4条",
            "GEN-MTH-FACTOR-001": "第7.2.2条",
            "GEN-MTH-MATERIAL-BALANCE-001": "第7.2.3条",
            "GEN-MTH-MEASURED-001": "第7.2.4条",
            "GEN-FML-FACTOR-001": "第7.2.2条",
            "GEN-FML-MATERIAL-BALANCE-001": "第7.2.3条",
            "GEN-FML-FUEL-AGG-001": "第7.5.2条",
            "GEN-FML-PROCESS-AGG-001": "第7.5.3条",
            "GEN-FML-WASTE-AGG-001": "第7.5.4条",
            "GEN-FML-FUGITIVE-AGG-001": "第7.5.5条",
            "GEN-FML-PURCHASED-ELECTRICITY-001": "第7.5.6条",
            "GEN-FML-PURCHASED-HEAT-001": "第7.5.6条",
            "GEN-FML-EXPORTED-ELECTRICITY-001": "第7.5.7条",
            "GEN-FML-EXPORTED-HEAT-001": "第7.5.7条",
            "GEN-FML-TOTAL-001": "第7.5.8条",
            "GEN-RULE-TOTAL-001": "第7.5.8条",
            "GEN-AGG-FUEL-ADD": "第7.5.2条",
            "GEN-AGG-PROCESS-ADD": "第7.5.3条",
            "GEN-AGG-WASTE-ADD": "第7.5.4条",
            "GEN-AGG-FUGITIVE-REVIEW-001": "第7.5.5条",
        }
        for rule_id, marker in source_markers.items():
            self.assertIn(marker, common_by_id[rule_id].source_location or "")
        self.assertIn("第7.5.8条", common_by_id["GEN-RULE-TOTAL-COVERAGE-REQUIRED-001"].source_location or "")
        self.assertNotIn("第5.2.7条", common_by_id["GEN-RULE-TOTAL-COVERAGE-REQUIRED-001"].source_location or "")
        self.assertNotIn("第7.5.9条", common_by_id["GEN-FML-EXPORTED-ELECTRICITY-001"].source_location or "")
        self.assertNotIn("第7.5.10条", common_by_id["GEN-FML-EXPORTED-HEAT-001"].source_location or "")
        self.assertEqual(
            common_by_id["GEN-FML-TOTAL-001"].relation,
            RuleRelation.CONFLICT_REVIEW,
        )
        self.assertEqual(
            common_by_id["GEN-FML-FUGITIVE-AGG-001"].evidence_status,
            RuleEvidenceStatus.CONFLICT,
        )
        self.assertEqual(
            set(industry_by_id["CAR-RULE-TOTAL-001"].supersedes_rule_ids),
            {"GEN-RULE-TOTAL-001", "GEN-FML-TOTAL-001"},
        )
        self.assertEqual(
            set(industry_by_id["CAR-RULE-FUGITIVE-COVERAGE-001"].supersedes_rule_ids),
            {
                "GEN-RULE-FUGITIVE-EXECUTION-BLOCK-001",
                "GEN-FML-FUGITIVE-AGG-001",
                "GEN-AGG-FUGITIVE-REVIEW-001",
            },
        )
        self.assertEqual(
            industry_by_id["CAR-RULE-FUGITIVE-COVERAGE-001"].origin,
            RuleOrigin.SOFTWARE_DERIVED,
        )
        nonfossil = industry_by_id["CAR-RULE-NONFOSSIL-POWER-001"]
        self.assertEqual(nonfossil.relation, RuleRelation.OVERRIDE)
        self.assertEqual(set(nonfossil.supersedes_rule_ids), {"GEN-RULE-ELECTRICITY-001"})
        self.assertEqual(nonfossil.selection_policy, ParameterSelectionPolicy.STANDARD_REQUIRED)
        self.assertEqual(nonfossil.parameter_id, "electricity_emission_factor_nonfossil")
        self.assertEqual(nonfossil.required_factor_ids, ("electricity_nonfossil_zero_gbt32151_34_2024",))
        self.assertEqual(nonfossil.applicability.conditions, (("electricity_attribute", "NONFOSSIL"),))
        self.assertEqual(nonfossil.source_location, "GB/T 32151.34—2024 第5.2.6.1条、附录D.1.1；PDF第30页；印刷页22")
        self.assertEqual(industry_by_id["CAR-RULE-FUEL-001"].source_location,
            "GB/T 32151.34—2024 第5.2.1条；附录C；PDF12；印刷页4")
        self.assertEqual(industry_by_id["CAR-RULE-PROCESS-001"].source_location,
            "GB/T 32151.34—2024 第5.2.2～5.2.5条；PDF12～14；印刷页4～6")
        self.assertEqual(industry_by_id["CAR-RULE-FUGITIVE-COVERAGE-001"].source_location,
            "GB/T 32151.34—2024 第4.2、5.2条；SM01-DECISION-001")
        power_heat = industry_by_id["CAR-RULE-POWER-HEAT-001"]
        self.assertEqual(
            set(power_heat.parameter_ids),
            {"electricity_emission_factor_national", "electricity_emission_factor_nonfossil", "heat_emission_factor_default"},
        )
        self.assertEqual(
            set(power_heat.applicability.parameter_types),
            {ParameterType.ELECTRICITY_EMISSION_FACTOR, ParameterType.HEAT_EMISSION_FACTOR},
        )
        self.assertIn(
            ("specializes", "GEN-RULE-ELECTRICITY-001|GEN-RULE-HEAT-001"),
            power_heat.payload,
        )
        self.assertIn("第5.2.6条", power_heat.source_location or "")
        self.assertNotIn("第5.2.7.1条", power_heat.source_location or "")

        generic = EffectiveRuleResolver().resolve(
            common,
            (),
            RuleContext(standard_id=COMMON_ID),
        )
        self.assertTrue(generic.blocked)
        self.assertTrue(
            {"GEN-FML-TOTAL-001", "GEN-FML-FUGITIVE-AGG-001"}.issubset(
                {item.field_id for item in generic.problems}
            )
        )
        carbon = EffectiveRuleResolver().resolve(
            common,
            industry,
            RuleContext(
                standard_id=STANDARD_ID,
                parameter_type=ParameterType.ELECTRICITY_EMISSION_FACTOR,
            ),
        )
        self.assertFalse(carbon.blocked)
        self.assertTrue(
            {
                "GEN-RULE-TOTAL-001",
                "GEN-FML-TOTAL-001",
                "GEN-RULE-FUGITIVE-EXECUTION-BLOCK-001",
                "GEN-FML-FUGITIVE-AGG-001",
                "GEN-AGG-FUGITIVE-REVIEW-001",
            }.issubset(set(carbon.overridden_rule_ids))
        )
        self.assertNotIn("GEN-RULE-ELECTRICITY-001", carbon.overridden_rule_ids)
        self.assertTrue(
            any(
                trace.rule_id == "CAR-RULE-POWER-HEAT-001"
                and trace.action.value == "SELECTED"
                for trace in carbon.traces
            )
        )
        self.assertTrue(
            any(
                trace.rule_id == "GEN-RULE-ELECTRICITY-001"
                and trace.action.value == "INHERITED"
                for trace in carbon.traces
            )
        )

    def test_official_latest_ignores_fixed_old_factor_anchor(self) -> None:
        parameter_id = "electricity_emission_factor_national"
        parameter = Parameter(
            parameter_id,
            "purchased_electricity",
            ParameterType.ELECTRICITY_EMISSION_FACTOR,
            "全国电力因子",
            "tCO2/MWh",
            "2024",
        )
        old = replace(
            factor(
                "electricity_factor_2023",
                parameter_id,
                "0.5306",
                ValueType.GOVERNMENT_PUBLISHED,
                version="2023",
                factor_year=2023,
                applicable_standard_ids=(COMMON_ID,),
                subject_id=parameter.subject_id,
            ),
            parameter_type=ParameterType.ELECTRICITY_EMISSION_FACTOR,
        )
        new = replace(
            factor(
                "electricity_factor_2024",
                parameter_id,
                "0.5100",
                ValueType.GOVERNMENT_PUBLISHED,
                version="2024",
                factor_year=2024,
                applicable_standard_ids=(COMMON_ID,),
                subject_id=parameter.subject_id,
            ),
            parameter_type=ParameterType.ELECTRICITY_EMISSION_FACTOR,
        )
        selection_rule = RuleDefinition(
            rule_id="GEN-RULE-OFFICIAL-LATEST-TEST",
            rule_domain="parameter_selection",
            target_id=parameter_id,
            parameter_id=parameter_id,
            relation=RuleRelation.BASE,
            description="官方最新回归规则",
            applicability=RuleApplicability(
                standard_ids=(COMMON_ID,),
                parameter_types=(ParameterType.ELECTRICITY_EMISSION_FACTOR,),
            ),
            selection_policy=ParameterSelectionPolicy.OFFICIAL_LATEST,
            required_factor_id=old.factor_id,
        )
        result = ParameterResolver(
            MemoryParameterRepository((parameter,), (old, new)),
            common_rules=(selection_rule,),
        ).resolve(
            ParameterResolutionContext(
                parameter_id=parameter_id,
                standard_id=COMMON_ID,
                subject_id=parameter.subject_id,
                parameter_type=parameter.parameter_type,
            )
        )
        self.assertIsNotNone(result.recommended)
        assert result.recommended is not None
        self.assertEqual(result.recommended.factor.factor_id, new.factor_id)
        self.assertEqual(result.selection_method, ParameterSelectionMethod.SYSTEM_RECOMMENDED)

    def test_confirmed_candidate_cannot_bypass_rule_conflict_or_snapshot_block(self) -> None:
        parameter_id = "gwp_co2_ar6_100"
        parameter = Parameter(
            parameter_id,
            "co2",
            ParameterType.GWP,
            "CO2 GWP100",
            "ratio",
            "2026",
        )
        candidate = factor(
            "gwp_co2_ar6",
            parameter_id,
            "1",
            ValueType.SCIENTIFIC_REFERENCE,
            subject_id="co2",
            applicable_standard_ids=(STANDARD_ID,),
        )
        selection_rule = RuleDefinition(
            rule_id="GEN-RULE-GWP-CONFIRMATION-TEST",
            rule_domain="parameter_selection",
            target_id=parameter_id,
            parameter_id=parameter_id,
            relation=RuleRelation.BASE,
            description="冲突阻断回归规则",
            applicability=RuleApplicability(
                standard_ids=(STANDARD_ID,),
                parameter_types=(ParameterType.GWP,),
            ),
            selection_policy=ParameterSelectionPolicy.SYSTEM_GWP,
        )
        unresolved = rule(
            "GEN-RULE-CONFLICT-CONFIRMATION-TEST",
            RuleRelation.CONFLICT_REVIEW,
            domain="formula",
            target_id="formula.conflicted",
            standard_id=STANDARD_ID,
        )
        result = ParameterResolver(
            MemoryParameterRepository((parameter,), (candidate,)),
            common_rules=(selection_rule, unresolved),
        ).resolve(
            ParameterResolutionContext(
                parameter_id=parameter_id,
                standard_id=STANDARD_ID,
                subject_id="co2",
                parameter_type=ParameterType.GWP,
                confirmed_factor_id=candidate.factor_id,
                confirmation_reason="用户确认来源，但规则冲突仍需处理。",
            )
        )
        self.assertTrue(result.blocked)
        self.assertIsNone(result.recommended)
        self.assertTrue(any(item.code == "GEN-PAR-CONFLICT-BLOCKED" for item in result.warnings))
        with self.assertRaises(ValueError):
            result.to_snapshot("snapshot.g05.conflict", NOW)

    def test_invalid_override_requires_complete_non_dangling_supersedes(self) -> None:
        base = rule(
            "GEN-RULE-OVERRIDE-BASE-A",
            RuleRelation.BASE,
            domain="coverage",
            target_id="coverage.total",
        )
        second_base = rule(
            "GEN-RULE-OVERRIDE-BASE-B",
            RuleRelation.BASE,
            domain="coverage",
            target_id="coverage.total",
        )

        missing = EffectiveRuleResolver().resolve(
            (base,),
            (
                rule(
                    "CAR-RULE-OVERRIDE-MISSING",
                    RuleRelation.OVERRIDE,
                    domain="coverage",
                    target_id="coverage.total",
                    standard_id=STANDARD_ID,
                ),
            ),
            RuleContext(standard_id=STANDARD_ID),
        )
        self.assertTrue(missing.blocked)
        self.assertIn(base.rule_id, missing.rule_ids)
        self.assertTrue(
            any(item.code == "GEN-RULE-OVERRIDE-SUPERSEDES-MISSING" for item in missing.problems)
        )

        dangling = EffectiveRuleResolver().resolve(
            (base,),
            (
                rule(
                    "CAR-RULE-OVERRIDE-DANGLING",
                    RuleRelation.OVERRIDE,
                    domain="coverage",
                    target_id="coverage.total",
                    standard_id=STANDARD_ID,
                    supersedes=("GEN-RULE-NOT-IN-COMMON",),
                ),
            ),
            RuleContext(standard_id=STANDARD_ID),
        )
        self.assertTrue(dangling.blocked)
        self.assertIn(base.rule_id, dangling.rule_ids)
        self.assertTrue(
            any(item.code == "GEN-RULE-OVERRIDE-SUPERSEDES-UNKNOWN" for item in dangling.problems)
        )

        partial = EffectiveRuleResolver().resolve(
            (base, second_base),
            (
                rule(
                    "CAR-RULE-OVERRIDE-PARTIAL",
                    RuleRelation.OVERRIDE,
                    domain="coverage",
                    target_id="coverage.total",
                    standard_id=STANDARD_ID,
                    supersedes=(base.rule_id,),
                ),
            ),
            RuleContext(standard_id=STANDARD_ID),
        )
        self.assertTrue(partial.blocked)
        self.assertIn(base.rule_id, partial.rule_ids)
        self.assertIn(second_base.rule_id, partial.rule_ids)
        self.assertTrue(
            any(item.code == "GEN-RULE-OVERRIDE-SUPERSEDES-INCOMPLETE" for item in partial.problems)
        )

    def test_activity_source_level_rejects_raw_enum_strings(self) -> None:
        with self.assertRaises(ValueError):
            ActivityData(
                "activity.energy",
                "10",
                "MWh",
                ActivityDataSource.ENERGY_BILL,
                source_level="PROXY",  # type: ignore[arg-type]
            )

    def test_activity_validation_and_aggregation_contracts(self) -> None:
        contract = ActivityDataContract(
            contract_id="GEN-ACTIVITY-001",
            activity_id="activity.energy",
            expected_unit="MWh",
            evidence_required=True,
        )
        value = ActivityData(
            "activity.energy",
            "10",
            "MWh",
            ActivityDataSource.ENERGY_BILL,
            source_level=ActivitySourceLevel.PROXY,
        )
        problems = contract.validate(value)
        self.assertTrue(any(item.code == "GEN-VAL-PROXY-DATA" for item in problems))
        self.assertTrue(any(item.code == "GEN-VAL-SOURCE-EVIDENCE" for item in problems))

        aggregation = AggregationContract(
            "GEN-AGG-001",
            (
                AggregationLine("source.add", AggregationOperation.ADD),
                AggregationLine("source.subtract", AggregationOperation.SUBTRACT),
                AggregationLine("source.report", AggregationOperation.REPORT_ONLY),
            ),
        )
        self.assertEqual(
            aggregation.aggregate({"source.add": "10", "source.subtract": "2"}),
            Decimal("8"),
        )
        coverage = aggregation.validate_coverage(("source.add", "source.subtract", "source.report"))
        self.assertEqual(coverage, ())
        self.assertTrue(
            any(
                item.code == "GEN-VAL-TOTAL-SOURCE-COVERAGE-001"
                for item in aggregation.validate_coverage(("source.unknown",))
            )
        )


if __name__ == "__main__":
    unittest.main()

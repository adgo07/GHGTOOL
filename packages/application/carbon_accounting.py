"""Application services for catalog access and carbon-accounting workflows."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import replace
from datetime import datetime
from typing import Any
from uuid import uuid4

from packages.core.errors import contains_warnings
from packages.core.models import AccountingRecord, Factor, Parameter, ParameterType, RecordStatus, ReviewStatus, ValueType
from packages.core.parameter_resolution import (
    FactorApplicability,
    ParameterResolver,
    default_g05_rules,
)
from packages.core.rules import (
    ParameterSelectionPolicy,
    RuleApplicability,
    RuleDefinition,
    RuleEvidenceStatus,
    RuleOrigin,
    RuleRelation,
)
from packages.core.repositories import DetailedRecordRepository, ParameterRepository, RecordRepository
from packages.standards.catalog import CatalogRepository

from packages.standards.carbon_material import (
    CarbonMaterialCalculationOutcome,
    CarbonMaterialCalculator,
    CarbonMaterialInput,
)


class RecordRepositoryConfigurationError(ValueError):
    """Raised when a formal calculation has no detail-capable record store."""


class RecordPersistenceError(RuntimeError):
    """Raised when a successful calculation could not be saved as a formal record."""


class CatalogParameterRepository(ParameterRepository):
    """Convert read-only G04 catalog rows into G05 Domain objects."""

    def __init__(self, repository: CatalogRepository) -> None:
        catalog_parameters = tuple(repository.list_parameters())
        parameter_types = {item.parameter_id: item.parameter_type for item in catalog_parameters}
        self._parameters = tuple(
            Parameter(
                parameter_id=item.parameter_id,
                subject_id=item.subject_id,
                parameter_type=item.parameter_type,
                name=item.name,
                default_unit=item.canonical_unit,
                version="catalog",
                description=item.notes,
            )
            for item in catalog_parameters
        )
        self._factors = tuple(
            Factor(
                factor_id=item.factor_id,
                parameter_id=item.parameter_id,
                subject_id=item.subject_id,
                parameter_type=parameter_types[item.parameter_id],
                value=item.normalized_value,
                unit=item.normalized_unit,
                version=f"{item.factor_year}",
                value_type=item.value_type,
                review_status=item.review_status,
                source_id=item.source_id,
                source_location=item.source_location,
                applicable_standard_ids=item.applicable_standard_ids,
                valid_from=item.valid_from,
                valid_to=item.valid_to,
                factor_year=item.factor_year,
                notes=item.notes,
            )
            for item in repository.list_factors()
        )

    def get_parameter(self, parameter_id: str) -> Parameter | None:
        return next((item for item in self._parameters if item.parameter_id == parameter_id), None)

    def get_factor(self, factor_id: str) -> Factor | None:
        return next((item for item in self._factors if item.factor_id == factor_id), None)

    def list_factors(self, parameter_id: str) -> Sequence[Factor]:
        return tuple(item for item in self._factors if item.parameter_id == parameter_id)


def _catalog_parameter_rules(repository: CatalogRepository) -> tuple[RuleDefinition, ...]:
    """Build standard-default rules only from verified C.1/C.2 source bindings."""

    from packages.standards.carbon_material import STANDARD_ID

    tables = tuple(repository.list_source_tables())
    standard = next(
        (item for item in repository.list_standards() if item.standard_id == STANDARD_ID),
        None,
    )
    if standard is None:
        return ()
    standard_source_id = standard.official_source_id
    table_by_id = {
        item.source_table_id: item
        for item in tables
        if item.source_id == standard_source_id and item.display_number in {"C.1", "C.2"}
    }
    if not table_by_id:
        return ()
    assets = {item.asset_id: item for item in repository.list_reference_data_assets()}
    parameters = {item.parameter_id: item for item in repository.list_parameters()}
    factors = {item.factor_id: item for item in repository.list_factors()}
    sources = {item.source_id: item for item in repository.list_sources()}
    accepted_reviews = {ReviewStatus.VERIFIED, ReviewStatus.VERIFIED_WITH_INTERPRETATION}
    common, industry = default_g05_rules()
    policy_covered = {
        parameter_id
        for rule in (*common, *industry)
        if rule.selection_policy is not None
        for parameter_id in rule.parameter_ids
    }
    bindings = tuple(repository.list_reference_data_bindings())
    grouped: dict[tuple[str, str, str, str], set[str]] = {}
    binding_locations: dict[tuple[str, str], str] = {}
    for binding in bindings:
        table = table_by_id.get(binding.source_table_id)
        asset = assets.get(binding.asset_id)
        factor = factors.get(binding.factor_id) if binding.factor_id else None
        source = sources.get(factor.source_id) if factor else None
        if (
            table is None
            or binding.binding_type != "FACTOR_SOURCE"
            or binding.review_status not in {ReviewStatus.VERIFIED, ReviewStatus.VERIFIED_WITH_INTERPRETATION}
            or asset is None
            or factor is None
            or factor.review_status not in accepted_reviews
            or source is None
            or source.review_status not in accepted_reviews
            or table.source_id != factor.source_id
            or binding.factor_year != factor.factor_year
            or factor.normalized_value != asset.normalized_value
            or factor.normalized_unit != asset.normalized_unit
            or binding.applicable_standard_ids and STANDARD_ID not in binding.applicable_standard_ids
            or factor.applicable_standard_ids and STANDARD_ID not in factor.applicable_standard_ids
            or asset.parameter_id != factor.parameter_id
            or asset.subject_id != factor.subject_id
            or factor.value_type not in {ValueType.STANDARD_DEFAULT, ValueType.STANDARD_SPECIFIED}
        ):
            continue
        parameter = parameters.get(factor.parameter_id)
        if parameter is None or parameter.subject_id != factor.subject_id:
            continue
        group = (table.display_number, factor.parameter_id, factor.subject_id, parameter.parameter_type.value)
        grouped.setdefault(group, set()).add(factor.factor_id)
        binding_locations[(table.display_number, factor.factor_id)] = binding.source_location

    rules: list[RuleDefinition] = []
    for (table_number, parameter_id, subject_id, _), factor_ids in sorted(grouped.items()):
        if parameter_id in policy_covered:
            continue
        parameter = parameters[parameter_id]
        table = next(item for item in table_by_id.values() if item.display_number == table_number)
        location = next(
            (binding_locations.get((table_number, factor_id)) for factor_id in sorted(factor_ids)
             if binding_locations.get((table_number, factor_id))),
            table.source_location,
        )
        rules.append(
            RuleDefinition(
                rule_id=f"CAR-RULE-CATALOG-{table_number.replace('.', '')}-{parameter_id}",
                rule_domain="parameter_selection",
                relation=RuleRelation.BASE,
                description=f"依据 GB/T 32151.34—2024 附录 {table_number} 的已核验目录绑定选择标准参数。",
                standard_id=STANDARD_ID,
                target_id=f"catalog.{parameter_id}",
                applicability=RuleApplicability(
                    standard_ids=(STANDARD_ID,),
                    subject_ids=(subject_id,),
                    parameter_types=(parameter.parameter_type,),
                ),
                origin=RuleOrigin.SOFTWARE_DERIVED,
                evidence_status=RuleEvidenceStatus.VERIFIED,
                parameter_id=parameter_id,
                selection_policy=ParameterSelectionPolicy.STANDARD_REQUIRED,
                applies_to_parameter_ids=(parameter_id,),
                required_factor_ids=tuple(sorted(factor_ids)),
                source_location=location or table.source_location,
                evidence_source_id=table.source_id,
            )
        )
    return tuple(rules)


def create_g06_parameter_resolver(repository: CatalogRepository) -> ParameterResolver:
    """Create the G06 resolver from catalog bindings and standard rules."""

    from packages.core.parameter_resolution import PROVINCIAL_ELECTRICITY_PARAMETER_ID
    from packages.standards.carbon_material import STANDARD_ID

    common, industry = default_g05_rules()
    applicability: list[FactorApplicability] = []
    assets = {item.asset_id: item for item in repository.list_reference_data_assets()}
    parameters = {item.parameter_id: item for item in repository.list_parameters()}
    catalog_factors = {item.factor_id: item for item in repository.list_factors()}
    tables = {item.source_table_id: item for item in repository.list_source_tables()}
    sources = {item.source_id: item for item in repository.list_sources()}
    accepted_reviews = {ReviewStatus.VERIFIED, ReviewStatus.VERIFIED_WITH_INTERPRETATION}
    seen_applicability: dict[str, FactorApplicability] = {}
    for binding in repository.list_reference_data_bindings():
        asset = assets.get(binding.asset_id)
        factor_record = catalog_factors.get(binding.factor_id) if binding.factor_id else None
        table = tables.get(binding.source_table_id)
        source = sources.get(factor_record.source_id) if factor_record else None
        parameter = parameters.get(factor_record.parameter_id) if factor_record else None
        if (
            binding.binding_type != "FACTOR_SOURCE"
            or binding.region is None
            or not binding.region.strip()
            or binding.review_status not in accepted_reviews
            or asset is None
            or asset.parameter_id != PROVINCIAL_ELECTRICITY_PARAMETER_ID
            or factor_record is None
            or factor_record.parameter_id != asset.parameter_id
            or factor_record.subject_id != asset.subject_id
            or factor_record.value_type is not asset.value_type
            or binding.factor_year != factor_record.factor_year
            or factor_record.normalized_value != asset.normalized_value
            or factor_record.normalized_unit != asset.normalized_unit
            or factor_record.review_status not in accepted_reviews
            or source is None
            or source.review_status not in accepted_reviews
            or table is None
            or table.source_id != factor_record.source_id
            or parameter is None
            or parameter.subject_id != factor_record.subject_id
            or parameter.parameter_type is not ParameterType.ELECTRICITY_EMISSION_FACTOR
            or binding.applicable_standard_ids and STANDARD_ID not in binding.applicable_standard_ids
            or factor_record.applicable_standard_ids and STANDARD_ID not in factor_record.applicable_standard_ids
        ):
            continue
        candidate = FactorApplicability(
            factor_id=factor_record.factor_id,
            standard_id=STANDARD_ID,
            region=binding.region,
            subject_id=factor_record.subject_id,
            parameter_type=ParameterType.ELECTRICITY_EMISSION_FACTOR,
            applicable_period_from=binding.valid_from,
            applicable_period_to=binding.valid_to,
        )
        previous = seen_applicability.get(factor_record.factor_id)
        if previous is not None and previous != candidate:
            raise ValueError(
                f"catalog factor {factor_record.factor_id} has conflicting verified region applicability bindings"
            )
        if previous is None:
            seen_applicability[factor_record.factor_id] = candidate
            applicability.append(candidate)
    return ParameterResolver(
        CatalogParameterRepository(repository),
        common_rules=common,
        industry_rules=(*industry, *_catalog_parameter_rules(repository)),
        applicability=applicability,
        required_applicability_parameter_ids=(PROVINCIAL_ELECTRICITY_PARAMETER_ID,),
    )


def _decode_evidence_snapshot(value: str, label: str) -> Any:
    if not isinstance(value, str):
        raise RecordPersistenceError(f"核算器未提供有效的{label}快照，未保存正式记录。")
    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        raise RecordPersistenceError(f"{label}快照格式无效，未保存正式记录。") from exc


def _copy_ingress_provenance(value: Mapping[str, object] | None) -> dict[str, object] | None:
    """Freeze adapter evidence as JSON without float or implicit type coercion."""
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise ValueError("导入来源证据必须是JSON对象。")

    def copy(item: object) -> object:
        if item is None or type(item) in (str, int, bool):
            return item
        if isinstance(item, Mapping):
            if any(type(key) is not str for key in item):
                raise ValueError("导入来源证据字段名必须是字符串。")
            return {key: copy(child) for key, child in item.items()}
        if type(item) is list:
            return [copy(child) for child in item]
        raise ValueError("导入来源证据必须使用JSON原始类型；十进制证据请保留原始字符串。")

    return copy(value)


class CarbonAccountingUseCase:
    """Persist successful Domain outcomes as append-only formal records."""

    def __init__(
        self,
        calculator: CarbonMaterialCalculator,
        record_repository: DetailedRecordRepository,
    ) -> None:
        if calculator is None:
            raise RecordRepositoryConfigurationError("正式核算必须配置计算器。")
        if record_repository is None:
            raise RecordRepositoryConfigurationError("正式核算必须配置记录仓库。")
        create_with_details = getattr(record_repository, "create_with_details", None)
        if not callable(create_with_details):
            raise RecordRepositoryConfigurationError(
                "正式核算要求支持详细证据快照的记录仓库（create_with_details）。"
            )
        self.calculator = calculator
        self.record_repository = record_repository
        self._create_with_details = create_with_details

    def calculate(
        self,
        input_value: CarbonMaterialInput,
        *,
        calculated_at: datetime | None = None,
        ingress_provenance: Mapping[str, object] | None = None,
    ) -> CarbonMaterialCalculationOutcome:
        frozen_ingress = _copy_ingress_provenance(ingress_provenance)
        outcome = self.calculator.calculate(input_value, calculated_at=calculated_at)
        if outcome.blocked or not outcome.successful:
            return outcome

        evidence = outcome.evidence
        result = outcome.result
        if evidence is None or result is None:
            raise RecordPersistenceError("计算器未返回完整正式记录证据，未保存正式记录。")

        status = (
            RecordStatus.COMPLETED_WITH_WARNINGS
            if contains_warnings((*outcome.problems, *result.problems))
            else RecordStatus.COMPLETED
        )
        record = AccountingRecord(
            record_id=f"record.{evidence.input_snapshot.input_id}.{uuid4().hex}",
            standard_id=evidence.input_snapshot.standard_id,
            algorithm_version=outcome.algorithm_version,
            created_at=result.calculated_at,
            input_snapshot=evidence.input_snapshot,
            calculation_result=result,
            status=status,
            parameter_snapshots=outcome.parameter_snapshots,
            problems=outcome.problems,
            standard_version=evidence.standard_version,
        )

        try:
            raw_input = _decode_evidence_snapshot(evidence.raw_input_snapshot_json, "原始输入")
            if frozen_ingress is not None:
                if not isinstance(raw_input, dict) or "ingress_provenance" in raw_input:
                    raise RecordPersistenceError("原始输入快照无法安全附加导入来源证据，未保存正式记录。")
                raw_input["ingress_provenance"] = frozen_ingress
            self._create_with_details(
                record,
                raw_input=raw_input,
                effective_rule_set=evidence.effective_rule_ids,
                trace_snapshot=_decode_evidence_snapshot(evidence.trace_snapshot_json, "计算追溯"),
                provenance_snapshot=_decode_evidence_snapshot(evidence.provenance_snapshot_json, "参数来源"),
                reporting_snapshot=_decode_evidence_snapshot(evidence.reporting_snapshot_json, "报告信息"),
                report_qualification=_decode_evidence_snapshot(evidence.report_qualification_json, "报告周期资格"),
            )
        except RecordPersistenceError:
            raise
        except Exception as exc:
            raise RecordPersistenceError(
                "计算结果未能保存为正式记录；请重试，或联系管理员检查记录存储。"
            ) from exc
        return replace(outcome, record=record)


def resolve_formal_record_repository(
    calculation_use_case: CarbonAccountingUseCase | None,
    record_repository: RecordRepository | None,
) -> RecordRepository | None:
    """Use the same repository for formal calculation and record browsing."""
    if calculation_use_case is None:
        return record_repository
    bound_repository = calculation_use_case.record_repository
    if record_repository is not None and record_repository is not bound_repository:
        raise RecordRepositoryConfigurationError("正式核算与记录查看必须使用同一记录仓库。")
    return bound_repository


class CarbonAccountingPreviewUseCase:
    """Run a preview using only the pure calculator, without a record store."""

    def __init__(self, calculator: CarbonMaterialCalculator) -> None:
        self.calculator = calculator

    def calculate(
        self,
        input_value: CarbonMaterialInput,
        *,
        calculated_at: datetime | None = None,
    ) -> CarbonMaterialCalculationOutcome:
        return self.calculator.calculate(input_value, calculated_at=calculated_at)


__all__ = [
    "CarbonAccountingPreviewUseCase",
    "CarbonAccountingUseCase",
    "CatalogParameterRepository",
    "RecordPersistenceError",
    "RecordRepositoryConfigurationError",
    "create_g06_parameter_resolver",
    "resolve_formal_record_repository",
]

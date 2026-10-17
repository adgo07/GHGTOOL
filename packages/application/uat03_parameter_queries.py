"""Catalog- and Resolver-backed parameter choices for UAT03 screens."""

from __future__ import annotations

from dataclasses import dataclass

from packages.application.catalog_queries import CatalogQueryService
from packages.core.errors import IssueLevel
from packages.core.models import AccountingPeriod, ElectricityAttribute, ParameterType, ReviewStatus
from packages.core.parameter_resolution import (
    NATIONAL_ELECTRICITY_PARAMETER_ID,
    NONFOSSIL_ELECTRICITY_PARAMETER_ID,
    ParameterResolutionContext,
    ParameterResolver,
)
from packages.standards.carbon_material import FuelType, STANDARD_ID
from packages.standards.carbon_material_business_policy import electricity_catalogue_parameters
from packages.standards.catalog import FactorCatalogRecord, ReferenceDataBindingCatalogRecord


@dataclass(frozen=True, slots=True)
class UAT03FuelOption:
    subject_id: str
    label: str
    aliases: tuple[str, ...]
    fuel_type: FuelType | None


@dataclass(frozen=True, slots=True)
class UAT03ResolvedFactor:
    factor: FactorCatalogRecord
    selection_reason: str


@dataclass(frozen=True, slots=True)
class UAT03FuelDefaults:
    lower_heating_value: UAT03ResolvedFactor | None
    carbon_content_per_heat: UAT03ResolvedFactor | None
    oxidation_rate: UAT03ResolvedFactor | None


@dataclass(frozen=True, slots=True)
class UAT03FactorOption:
    subject_id: str
    label: str
    factor: FactorCatalogRecord
    selection_reason: str
    region: str | None = None
    aliases: tuple[str, ...] = ()
    selectable: bool = True
    unavailable_reason: str | None = None
    table_number: str | None = None
    source_document_name: str | None = None


class UAT03ParameterQueries:
    """Expose only catalog-bound factors accepted by the shared parameter Resolver."""

    _PARAMETER_TYPES = (
        ParameterType.LOWER_HEATING_VALUE,
        ParameterType.CARBON_CONTENT_PER_HEAT,
        ParameterType.OXIDATION_RATE,
    )

    def __init__(self, catalog_service: CatalogQueryService, resolver: ParameterResolver) -> None:
        self.catalog_service = catalog_service
        self.resolver = resolver
        repository = catalog_service.repository
        self._parameters = {item.parameter_id: item for item in repository.list_parameters()}
        self._subjects = {item.subject_id: item for item in catalog_service.list_subjects()}
        self._factors = {item.factor_id: item for item in repository.list_factors()}
        self._assets = {item.asset_id: item for item in catalog_service.list_reference_data_assets()}
        self._bindings = tuple(catalog_service.list_reference_data_bindings())
        standard = next(
            (item for item in repository.list_standards() if item.standard_id == STANDARD_ID),
            None,
        )
        self._standard_source_id = standard.official_source_id if standard else None
        self._tables = tuple(catalog_service.list_source_tables())
        self._table_by_id = {item.source_table_id: item for item in self._tables}
        self._sources = {item.source_id: item for item in catalog_service.list_sources()}

    def _verified(self, binding: ReferenceDataBindingCatalogRecord, factor: FactorCatalogRecord) -> bool:
        asset = self._assets.get(binding.asset_id)
        table = self._table_by_id.get(binding.source_table_id)
        return (
            binding.review_status in {ReviewStatus.VERIFIED, ReviewStatus.VERIFIED_WITH_INTERPRETATION}
            and factor.review_status in {ReviewStatus.VERIFIED, ReviewStatus.VERIFIED_WITH_INTERPRETATION}
            and self._standard_applies(binding.applicable_standard_ids)
            and self._standard_applies(factor.applicable_standard_ids)
            and asset is not None
            and asset.parameter_id == factor.parameter_id
            and asset.subject_id == factor.subject_id
            and asset.value_type is factor.value_type
            and asset.normalized_value == factor.normalized_value
            and asset.normalized_unit == factor.normalized_unit
            and table is not None
            and table.source_id == factor.source_id
            and (source := self._sources.get(factor.source_id)) is not None
            and source.review_status in {ReviewStatus.VERIFIED, ReviewStatus.VERIFIED_WITH_INTERPRETATION}
            and binding.factor_year == factor.factor_year
        )

    def _standard_applies(self, standard_ids: tuple[str, ...]) -> bool:
        return not standard_ids or STANDARD_ID in standard_ids

    def _table_bindings(self, display_number: str) -> tuple[ReferenceDataBindingCatalogRecord, ...]:
        table_ids = {
            table.source_table_id
            for table in self._tables
            if table.display_number == display_number
            and table.source_id == self._standard_source_id
        }
        return tuple(
            binding for binding in self._bindings
            if binding.source_table_id in table_ids
            and binding.binding_type == "FACTOR_SOURCE"
            and binding.factor_id in self._factors
            and binding.asset_id in self._assets
            and self._verified(binding, self._factors[binding.factor_id])
        )

    def _electricity_table_bindings(self, display_number: str) -> tuple[ReferenceDataBindingCatalogRecord, ...]:
        """Join catalog rows; production qualification comes from the Resolver."""
        return tuple(
            binding for binding in self._bindings
            if binding.binding_type == "FACTOR_SOURCE"
            and (factor := self._factors.get(binding.factor_id)) is not None
            and self._verified(binding, factor)
            and (table := self._table_by_id.get(binding.source_table_id)) is not None
            and table.display_number == display_number
        )

    def _bound_factor_ids(
        self,
        *,
        table_number: str | None = None,
        parameter_id: str | None = None,
        subject_id: str | None = None,
        region: str | None | object = ...,
    ) -> frozenset[str]:
        bindings = self._table_bindings(table_number) if table_number else self._bindings
        factor_ids: set[str] = set()
        for binding in bindings:
            if (
                binding.binding_type != "FACTOR_SOURCE"
                or binding.factor_id not in self._factors
                or not self._verified(binding, self._factors[binding.factor_id])
            ):
                continue
            asset = self._assets.get(binding.asset_id)
            if asset is None:
                continue
            if parameter_id is not None and asset.parameter_id != parameter_id:
                continue
            if subject_id is not None and asset.subject_id != subject_id:
                continue
            if region is not ... and binding.region != region:
                continue
            factor_ids.add(binding.factor_id)
        return frozenset(factor_ids)

    def _resolve(
        self,
        parameter_id: str,
        subject_id: str,
        period: AccountingPeriod,
        *,
        region: str | None = None,
        allowed_factor_ids: frozenset[str] | None = None,
    ):
        parameter = self._parameters.get(parameter_id)
        if parameter is None:
            return None
        resolution = self.resolver.resolve(
            ParameterResolutionContext(
                parameter_id=parameter_id,
                standard_id=STANDARD_ID,
                accounting_period=period,
                region=region,
                subject_id=subject_id,
                parameter_type=parameter.parameter_type,
            )
        )
        errors = tuple(problem for problem in resolution.warnings if problem.level is IssueLevel.ERROR)
        if any(problem.code != "GEN-PAR-CONFIRMATION-REQUIRED" for problem in errors):
            return None
        values = (*((resolution.recommended,) if resolution.recommended else ()), *resolution.alternatives)
        by_id: dict[str, UAT03ResolvedFactor] = {}
        for value in values:
            factor_id = value.factor.factor_id
            if allowed_factor_ids is not None and factor_id not in allowed_factor_ids:
                continue
            factor = self._factors.get(factor_id)
            if factor is None:
                continue
            reason = resolution.selection_reason if resolution.recommended and factor_id == resolution.recommended.factor_id else "；".join(value.match_reasons)
            by_id[factor_id] = UAT03ResolvedFactor(factor, reason or "当前规则下可选的目录因子。")
        return resolution, tuple(by_id.values())

    def fuel_options(self) -> tuple[UAT03FuelOption, ...]:
        bindings = self._table_bindings("C.1")
        subject_ids = {
            self._assets[binding.asset_id].subject_id
            for binding in bindings
            if binding.factor_id in self._factors
            and self._verified(binding, self._factors[binding.factor_id])
        }
        options: list[UAT03FuelOption] = []
        for subject_id in sorted(subject_ids, key=lambda item: (self._subjects.get(item).name if item in self._subjects else item, item)):
            subject = self._subjects.get(subject_id)
            if subject is None:
                continue
            options.append(
                UAT03FuelOption(
                    subject_id=subject_id,
                    label=subject.name,
                    aliases=subject.aliases,
                    fuel_type=FuelType.__members__.get(subject_id.upper()),
                )
            )
        return tuple(options)

    def _subject_parameter_id(self, subject_id: str, parameter_type: ParameterType) -> str | None:
        candidates = {
            self._assets[binding.asset_id].parameter_id
            for binding in self._table_bindings("C.1")
            if binding.factor_id in self._factors
            and self._assets[binding.asset_id].subject_id == subject_id
            and self._parameters.get(self._assets[binding.asset_id].parameter_id) is not None
            and self._parameters[self._assets[binding.asset_id].parameter_id].parameter_type is parameter_type
        }
        return next(iter(candidates)) if len(candidates) == 1 else None

    def fuel_defaults(self, subject_id: str, period: AccountingPeriod) -> UAT03FuelDefaults:
        resolved: dict[ParameterType, UAT03ResolvedFactor | None] = {}
        for parameter_type in self._PARAMETER_TYPES:
            parameter_id = self._subject_parameter_id(subject_id, parameter_type)
            allowed = self._bound_factor_ids(
                table_number="C.1", parameter_id=parameter_id, subject_id=subject_id
            ) if parameter_id else frozenset()
            answer = self._resolve(parameter_id, subject_id, period, allowed_factor_ids=allowed) if parameter_id else None
            if answer is None:
                resolved[parameter_type] = None
                continue
            resolution, values = answer
            recommended_id = resolution.recommended.factor_id if resolution.recommended else None
            selected = next((item for item in values if item.factor.factor_id == recommended_id), None)
            resolved[parameter_type] = selected if not resolution.blocked else None
        return UAT03FuelDefaults(
            lower_heating_value=resolved.get(ParameterType.LOWER_HEATING_VALUE),
            carbon_content_per_heat=resolved.get(ParameterType.CARBON_CONTENT_PER_HEAT),
            oxidation_rate=resolved.get(ParameterType.OXIDATION_RATE),
        )

    def carbonate_options(self, period: AccountingPeriod) -> tuple[UAT03FactorOption, ...]:
        options: list[UAT03FactorOption] = []
        bindings = self._table_bindings("C.2")
        groups: dict[tuple[str, str], set[str]] = {}
        for binding in bindings:
            asset = self._assets[binding.asset_id]
            factor = self._factors[binding.factor_id]
            groups.setdefault((asset.parameter_id, asset.subject_id), set()).add(factor.factor_id)
        for (parameter_id, subject_id), factor_ids in sorted(groups.items()):
            answer = self._resolve(
                parameter_id,
                subject_id,
                period,
                allowed_factor_ids=frozenset(factor_ids),
            )
            if answer is None:
                continue
            resolution, values = answer
            if resolution.blocked or resolution.recommended is None:
                continue
            recommended_id = resolution.recommended.factor_id
            selected = next((item for item in values if item.factor.factor_id == recommended_id), None)
            subject = self._subjects.get(subject_id)
            if selected is None:
                continue
            options.append(
                UAT03FactorOption(
                    subject_id=subject_id,
                    label=subject.name if subject else subject_id,
                    factor=selected.factor,
                    selection_reason=selected.selection_reason,
                    aliases=subject.aliases if subject else (),
                )
            )
        return tuple(options)

    @staticmethod
    def _electricity_parameters_for_level(geographic_level: str) -> tuple[tuple[str, str], ...]:
        geography_tags = {"全国": None, "区域": "region", "省级": "province"}
        if geographic_level not in geography_tags:
            return ()
        return tuple(
            (f"表{table}", parameter_id)
            for table, parameter_id, tag in electricity_catalogue_parameters()
            if tag == geography_tags[geographic_level]
        )

    def electricity_regions(
        self,
        period: AccountingPeriod,
        geographic_level: str = "省级",
    ) -> tuple[str, ...]:
        """Keep the provincial default; group identities come from adopted policy."""
        if geographic_level not in {"区域", "省级"}:
            return ()
        regions = dict.fromkeys(
            binding.region
            for table, parameter_id in self._electricity_parameters_for_level(geographic_level)
            for binding in self._electricity_table_bindings(table)
            if binding.region
            and (asset := self._assets.get(binding.asset_id)) is not None
            and asset.parameter_id == parameter_id
        )
        return tuple(
            region for region in regions
            if self.electricity_catalog_options(geographic_level, region, period)
        )

    def electricity_regions_by_level(self, period: AccountingPeriod) -> dict[str, tuple[str, ...]]:
        """Expose current geography choices in the UI's national/region/province order."""
        return {
            "全国": ("全国",) if self.electricity_catalog_options("全国", None, period) else (),
            "区域": self.electricity_regions(period, "区域"),
            "省级": self.electricity_regions(period, "省级"),
        }

    def preferred_electricity_region(self, period: AccountingPeriod) -> str | None:
        regions = self.electricity_regions(period)
        if "宁夏" in regions:
            return "宁夏"
        return regions[0] if regions else None

    def electricity_options(
        self,
        region: str | None,
        period: AccountingPeriod,
    ) -> tuple[UAT03FactorOption, ...]:
        """Compatibility default choices; special national bases never fill a gap."""
        if region in (None, "全国"):
            return tuple(
                option for option in self.electricity_catalog_options("全国", None, period)
                if option.factor.parameter_id == NATIONAL_ELECTRICITY_PARAMETER_ID
            )
        regional = self.electricity_catalog_options("区域", region, period)
        provincial = self.electricity_catalog_options("省级", region, period)
        if bool(regional) == bool(provincial):
            return ()
        return regional or provincial

    def electricity_catalog_options(
        self,
        geographic_level: str,
        region: str | None,
        period: AccountingPeriod,
    ) -> tuple[UAT03FactorOption, ...]:
        """Return only verified table bindings that the formal Resolver accepts."""
        table_parameters = self._electricity_parameters_for_level(geographic_level)
        if not table_parameters:
            return ()
        if geographic_level == "全国":
            if region not in (None, "全国"):
                return ()
            resolver_region = None
            binding_regions = {None, "全国"}
        else:
            if region is None or not region.strip():
                return ()
            resolver_region = region.strip()
            binding_regions = {resolver_region}

        options: list[UAT03FactorOption] = []
        for table_number, parameter_id in table_parameters:
            bindings = tuple(
                binding for binding in self._electricity_table_bindings(table_number)
                if binding.region in binding_regions
                and (asset := self._assets.get(binding.asset_id)) is not None
                and asset.parameter_id == parameter_id
            )
            factor_ids = tuple(dict.fromkeys(binding.factor_id for binding in bindings if binding.factor_id))
            if not factor_ids:
                continue
            for factor_id in factor_ids:
                resolution = self.resolver.resolve(ParameterResolutionContext(
                    parameter_id=parameter_id,
                    standard_id=STANDARD_ID,
                    accounting_period=period,
                    region=resolver_region,
                    subject_id="purchased_electricity",
                    parameter_type=ParameterType.ELECTRICITY_EMISSION_FACTOR,
                    electricity_attribute=ElectricityAttribute.ORDINARY,
                    confirmed_factor_id=factor_id,
                    confirmation_reason="核对本条目录候选的实际适用绑定。",
                ))
                binding = self.resolver.reference_binding_for(resolution).binding
                if binding is None or binding.factor_id != factor_id:
                    continue
                factor = self._factors.get(binding.factor_id)
                table = self._table_by_id.get(binding.source_table_id)
                if factor is None or table is None:
                    continue
                item = UAT03ResolvedFactor(factor, resolution.selection_reason)
                source = self._sources.get(item.factor.source_id)
                options.append(
                    UAT03FactorOption(
                        subject_id=item.factor.subject_id,
                        label=f"{table.display_number} · {table.title}",
                        factor=item.factor,
                        selection_reason=item.selection_reason,
                        region=resolver_region,
                        selectable=True,
                        table_number=table.display_number,
                        source_document_name=source.document_name if source is not None else None,
                    )
                )
        return tuple(options)

    def nonfossil_electricity_factor(self, period: AccountingPeriod) -> UAT03ResolvedFactor | None:
        allowed = self._bound_factor_ids(parameter_id=NONFOSSIL_ELECTRICITY_PARAMETER_ID)
        resolution = self.resolver.resolve(ParameterResolutionContext(
            parameter_id=NONFOSSIL_ELECTRICITY_PARAMETER_ID,
            standard_id=STANDARD_ID,
            accounting_period=period,
            subject_id="purchased_electricity",
            parameter_type=ParameterType.ELECTRICITY_EMISSION_FACTOR,
            electricity_attribute=ElectricityAttribute.NONFOSSIL,
        ))
        if self.resolver.reference_binding_for(resolution).binding is None:
            return None
        factor_id = resolution.recommended.factor_id
        factor = self._factors.get(factor_id)
        if factor_id not in allowed or factor is None:
            return None
        return UAT03ResolvedFactor(factor, resolution.selection_reason)


__all__ = [
    "UAT03FactorOption",
    "UAT03FuelDefaults",
    "UAT03FuelOption",
    "UAT03ParameterQueries",
    "UAT03ResolvedFactor",
]

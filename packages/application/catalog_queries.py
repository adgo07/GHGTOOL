"""Application-level read services for the G04 catalog screens."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, is_dataclass
from datetime import date
from decimal import Decimal
from enum import Enum
import hashlib
import json
from pathlib import Path

from packages.core.models import OfficialStatus, ParameterType, ReviewStatus, SourceType, ValueType
from packages.standards.catalog import (
    CatalogRepository,
    CatalogStatus,
    CatalogValueCategory,
    FactorCatalogRecord,
    ParameterCatalogRecord,
    ParameterFactorResult,
    ParameterViewMode,
    ReferenceLibrarySearchResult,
    ReferenceDataAssetCatalogRecord,
    ReferenceDataBindingCatalogRecord,
    SourceTableCatalogRecord,
    SourceCatalogRecord,
    StandardCatalogRecord,
    StandardDetail,
    SubjectCatalogRecord,
)


STANDARD_STATUS_LABELS = {
    CatalogStatus.CURRENT: "现行",
    CatalogStatus.UPCOMING: "即将实施",
    CatalogStatus.ABOLISHED: "已废止",
    CatalogStatus.UNKNOWN: "待核对",
}

SOURCE_TYPE_LABELS = {
    SourceType.OFFICIAL_STANDARD: "国家标准",
    SourceType.GOVERNMENT_PUBLICATION: "部门公告",
    SourceType.SCIENTIFIC_REFERENCE: "科学参考",
    SourceType.OTHER: "其他权威来源",
}

REVIEW_STATUS_LABELS = {
    ReviewStatus.VERIFIED: "已核对",
    ReviewStatus.VERIFIED_WITH_INTERPRETATION: "已核对（含规则解释）",
    ReviewStatus.PENDING_SOURCE: "待核对来源",
    ReviewStatus.DEPRECATED: "已弃用",
}

PARAMETER_TYPE_LABELS = {
    ParameterType.EMISSION_FACTOR: "排放因子",
    ParameterType.GWP: "全球变暖潜势",
    ParameterType.LOWER_HEATING_VALUE: "低位发热量",
    ParameterType.CARBON_CONTENT_PER_HEAT: "单位热值含碳量",
    ParameterType.OXIDATION_RATE: "碳氧化率",
    ParameterType.COMPOSITION: "组分/含量",
    ParameterType.PROCESS_CO2_FACTOR: "过程 CO₂ 因子",
    ParameterType.ELECTRICITY_EMISSION_FACTOR: "电力排放因子",
    ParameterType.HEAT_EMISSION_FACTOR: "热力排放因子",
    ParameterType.PROCESS_DEFAULT_PARAMETER: "行业过程缺省参数",
    ParameterType.STEAM_ENTHALPY: "蒸汽焓值",
    ParameterType.SYSTEM_CONVERSION: "系统换算",
}

VALUE_TYPE_LABELS = {
    ValueType.STANDARD_SPECIFIED: "标准直接规定",
    ValueType.STANDARD_DEFAULT: "标准缺省值",
    ValueType.GOVERNMENT_PUBLISHED: "政府发布值",
    ValueType.SCIENTIFIC_REFERENCE: "科学参考值",
    ValueType.MEASURED: "实测值",
    ValueType.DERIVED: "派生值",
    ValueType.SYSTEM_CONSTANT: "系统常数",
    ValueType.HISTORICAL: "历史值",
}

VALUE_CATEGORY_LABELS = {
    CatalogValueCategory.RECOMMENDED: "推荐值（标准缺省）",
    CatalogValueCategory.OTHER_APPLICABLE: "其他适用值",
    CatalogValueCategory.HISTORICAL: "历史值",
}


def _normalized_text(value: object) -> str:
    return "".join(str(value).casefold().split())


def _matches(query: str, values: Iterable[object]) -> bool:
    normalized_query = _normalized_text(query)
    if not normalized_query:
        return True
    return any(normalized_query in _normalized_text(value) for value in values)


def status_for(standard: StandardCatalogRecord, as_of: date) -> CatalogStatus:
    """Calculate the visible status from the official status and effective dates."""

    if standard.official_status is OfficialStatus.ABOLISHED:
        return CatalogStatus.ABOLISHED
    if standard.abolition_date is not None and as_of >= standard.abolition_date:
        return CatalogStatus.ABOLISHED
    if standard.official_status is OfficialStatus.UPCOMING:
        return CatalogStatus.UPCOMING
    if as_of < standard.implementation_date:
        return CatalogStatus.UPCOMING
    if standard.official_status is OfficialStatus.ACTIVE:
        return CatalogStatus.CURRENT
    return CatalogStatus.UNKNOWN


def value_category_for(factor: FactorCatalogRecord) -> CatalogValueCategory:
    """Map only source-declared metadata to a display category.

    This is not a context-driven recommendation resolver. It keeps
    coexisting values visibly distinct without selecting a value for a
    calculation context.
    """

    if factor.value_type is ValueType.HISTORICAL or factor.review_status is ReviewStatus.DEPRECATED:
        return CatalogValueCategory.HISTORICAL
    if factor.value_type is ValueType.STANDARD_DEFAULT:
        return CatalogValueCategory.RECOMMENDED
    return CatalogValueCategory.OTHER_APPLICABLE


class CatalogQueryService:
    """Application service that exposes read-only, user-oriented catalog queries."""

    def __init__(self, repository: CatalogRepository, *, as_of: date | None = None) -> None:
        self._repository = repository
        self._as_of = as_of or date.today()

    @classmethod
    def empty(cls) -> CatalogQueryService:
        from packages.persistence.catalog_repository import EmptyCatalogRepository

        return cls(EmptyCatalogRepository())

    @property
    def as_of(self) -> date:
        return self._as_of

    @property
    def has_data(self) -> bool:
        return bool(self._repository.list_standards() or self._repository.list_parameters())

    @property
    def repository(self) -> CatalogRepository:
        """Expose the read-only repository to application adapters."""

        return self._repository

    def reference_data_identity(self) -> dict[str, object]:
        """Capture a stable identity for the reference data used by a new Record."""
        datasets: dict[str, object] = {}
        for name in ("list_standards", "list_sources", "list_subjects", "list_parameters", "list_factors",
                     "list_source_tables", "list_reference_data_assets", "list_reference_data_bindings",
                     "list_conversion_rules"):
            reader = getattr(self._repository, name, None)
            if callable(reader):
                datasets[name.removeprefix("list_")] = tuple(reader())

        def encode(value: object) -> object:
            if isinstance(value, Enum):
                return value.value
            if isinstance(value, (date,)):
                return value.isoformat()
            if isinstance(value, Decimal):
                return str(value)
            if is_dataclass(value) and not isinstance(value, type):
                return {key: encode(item) for key, item in asdict(value).items()}
            if isinstance(value, dict):
                return {str(key): encode(item) for key, item in value.items()}
            if isinstance(value, (tuple, list)):
                return [encode(item) for item in value]
            return value

        serialized = json.dumps(encode(datasets), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        manifest_reader = getattr(self._repository, "manifest", None)
        manifest = manifest_reader() if callable(manifest_reader) else None
        return {
            "identity_schema_version": 1,
            "catalog_id": getattr(manifest, "catalog_id", None),
            "data_version": getattr(manifest, "data_version", None),
            "content_sha256": hashlib.sha256(serialized.encode("utf-8")).hexdigest(),
            "record_counts": {key: len(value) for key, value in datasets.items()},
        }

    def standard_version(self, standard_id: str) -> str | None:
        """Return the controlled catalog version for a stable standard ID."""

        standard = next(
            (item for item in self._repository.list_standards() if item.standard_id == standard_id),
            None,
        )
        return standard.version if standard is not None else None

    def list_parameter_factors(self, parameter_id: str) -> tuple[FactorCatalogRecord, ...]:
        """Return immutable factor candidates for a G06 parameter selector."""

        return tuple(
            factor
            for factor in self._repository.list_factors()
            if factor.parameter_id == parameter_id
        )

    def list_sources(self) -> tuple[SourceCatalogRecord, ...]:
        return tuple(self._repository.list_sources())

    def list_subjects(self) -> tuple[SubjectCatalogRecord, ...]:
        return tuple(self._repository.list_subjects())

    def standard_status(self, standard: StandardCatalogRecord) -> CatalogStatus:
        return status_for(standard, self._as_of)

    @staticmethod
    def status_label(status: CatalogStatus) -> str:
        return STANDARD_STATUS_LABELS[status]

    @staticmethod
    def source_type_label(source_type: SourceType) -> str:
        return SOURCE_TYPE_LABELS[source_type]

    @staticmethod
    def review_status_label(review_status: ReviewStatus) -> str:
        return REVIEW_STATUS_LABELS[review_status]

    @staticmethod
    def parameter_type_label(parameter_type: ParameterType) -> str:
        return PARAMETER_TYPE_LABELS[parameter_type]

    @staticmethod
    def value_type_label(value_type: ValueType) -> str:
        return VALUE_TYPE_LABELS[value_type]

    @staticmethod
    def value_category(factor: FactorCatalogRecord) -> CatalogValueCategory:
        return value_category_for(factor)

    @staticmethod
    def value_category_label(category: CatalogValueCategory) -> str:
        return VALUE_CATEGORY_LABELS[category]

    def industry_options(self) -> tuple[str, ...]:
        """Expose only verified industry metadata.

        The current canonical catalog has no approved structured industry field.
        Returning only the neutral option prevents standard titles from becoming
        an implicit classification source.
        """

        return ("全部",)

    def publication_years(self) -> tuple[int, ...]:
        return tuple(
            sorted(
                {standard.publication_date.year for standard in self._repository.list_standards()},
                reverse=True,
            )
        )

    def factor_years(self) -> tuple[int, ...]:
        return tuple(
            sorted(
                {factor.factor_year for factor in self._repository.list_factors()},
                reverse=True,
            )
        )

    def search_standards(
        self,
        query: str = "",
        *,
        status: CatalogStatus = CatalogStatus.ALL,
        industry: str = "全部",
        publication_year: int | None = None,
    ) -> tuple[tuple[StandardCatalogRecord, CatalogStatus, str], ...]:
        if industry != "全部":
            return ()

        results: list[tuple[StandardCatalogRecord, CatalogStatus, str]] = []
        for standard in self._repository.list_standards():
            current_status = self.standard_status(standard)
            source_text = (
                standard.standard_number,
                standard.standard_name,
                standard.notes,
            )
            if not _matches(query, source_text):
                continue
            if status is not CatalogStatus.ALL and current_status is not status:
                continue
            if publication_year is not None and standard.publication_date.year != publication_year:
                continue
            # The third tuple item is retained for the existing page adapter,
            # but it is not an inferred or user-visible industry classification.
            results.append((standard, current_status, "—"))
        results.sort(key=lambda item: (item[0].standard_number, item[0].standard_id))
        return tuple(results)

    def get_standard_detail(self, standard_id: str) -> StandardDetail | None:
        standards = tuple(self._repository.list_standards())
        standard = next((item for item in standards if item.standard_id == standard_id), None)
        if standard is None:
            return None
        sources = {item.source_id: item for item in self._repository.list_sources()}
        standards_by_id = {item.standard_id: item for item in standards}
        parameters_by_id = {item.parameter_id: item for item in self._repository.list_parameters()}
        parameters = tuple(
            parameters_by_id[parameter_id]
            for parameter_id in standard.parameter_refs
            if parameter_id in parameters_by_id
        )
        parameter_ids = {parameter.parameter_id for parameter in parameters}
        factors = tuple(
            factor
            for factor in self._repository.list_factors()
            if factor.parameter_id in parameter_ids and standard_id in factor.applicable_standard_ids
        )
        base_standards = tuple(
            standards_by_id[base_id]
            for base_id in standard.base_standard_ids
            if base_id in standards_by_id
        )
        return StandardDetail(
            standard=standard,
            status=self.standard_status(standard),
            source=sources.get(standard.official_source_id),
            base_standards=base_standards,
            parameters=parameters,
            factors=factors,
        )

    def search_parameter_factors(
        self,
        query: str = "",
        *,
        view_mode: ParameterViewMode = ParameterViewMode.BY_SUBJECT,
        subject_id: str | None = None,
        source_id: str | None = None,
        parameter_type: ParameterType | None = None,
        review_status: ReviewStatus | None = None,
        factor_year: int | None = None,
    ) -> tuple[ParameterFactorResult, ...]:
        subjects = {item.subject_id: item for item in self._repository.list_subjects()}
        sources = {item.source_id: item for item in self._repository.list_sources()}
        standards = {item.standard_id: item for item in self._repository.list_standards()}
        factors_by_parameter: dict[str, list[FactorCatalogRecord]] = {}
        for factor in self._repository.list_factors():
            factors_by_parameter.setdefault(factor.parameter_id, []).append(factor)

        results: list[ParameterFactorResult] = []
        for parameter in self._repository.list_parameters():
            if parameter.parameter_type is not parameter_type and parameter_type is not None:
                continue
            if parameter.review_status is not review_status and review_status is not None:
                continue
            if subject_id is not None and parameter.subject_id != subject_id:
                continue
            subject = subjects.get(parameter.subject_id)
            if subject is None:
                continue
            factors = factors_by_parameter.get(parameter.parameter_id, [])
            if source_id is not None:
                factors = [factor for factor in factors if factor.source_id == source_id]
                if not factors and parameter.source_id != source_id:
                    continue
            if factor_year is not None:
                factors = [factor for factor in factors if factor.factor_year == factor_year]
            if not factors:
                if factor_year is not None:
                    continue
                factors = [None]
            for factor in factors:
                source = sources.get(factor.source_id if factor else parameter.source_id)
                related_standards = tuple(
                    standards[standard_id]
                    for standard_id in (factor.applicable_standard_ids if factor else parameter.applicable_standard_ids)
                    if standard_id in standards
                )
                factor_values = () if factor is None else (
                    factor.factor_id,
                    factor.value,
                    factor.unit,
                    factor.source_location,
                    factor.factor_year,
                    factor.notes,
                    factor.value_type,
                    factor.review_status,
                )
                query_values = (
                    parameter.name,
                    parameter.canonical_unit,
                    parameter.source_location,
                    parameter.notes,
                    subject.name,
                    *subject.aliases,
                    *((source.document_no, source.document_name, source.publisher, source.notes) if source else ()),
                    *(standard.standard_number for standard in related_standards),
                    *(standard.standard_name for standard in related_standards),
                    *factor_values,
                )
                if not _matches(query, query_values):
                    continue
                if factor is not None and factor.review_status is not review_status and review_status is not None:
                    continue
                results.append(ParameterFactorResult(parameter, factor, subject, source))

        if view_mode is ParameterViewMode.BY_SOURCE:
            results.sort(
                key=lambda item: (
                    item.source.document_no if item.source else "",
                    item.parameter.name,
                    -(item.factor.factor_year if item.factor else 0),
                )
            )
        else:
            results.sort(
                key=lambda item: (
                    item.subject.name,
                    item.parameter.name,
                    -(item.factor.factor_year if item.factor else 0),
                )
            )
        return tuple(results)

    def list_source_tables(self, source_id: str | None = None) -> tuple[SourceTableCatalogRecord, ...]:
        reader = getattr(self._repository, "list_source_tables", None)
        if not callable(reader):
            return ()
        values = tuple(reader())
        if source_id is not None:
            values = tuple(item for item in values if item.source_id == source_id)
        return values

    def list_reference_data_assets(self) -> tuple[ReferenceDataAssetCatalogRecord, ...]:
        reader = getattr(self._repository, "list_reference_data_assets", None)
        return tuple(reader()) if callable(reader) else ()

    def list_reference_data_bindings(self) -> tuple[ReferenceDataBindingCatalogRecord, ...]:
        reader = getattr(self._repository, "list_reference_data_bindings", None)
        return tuple(reader()) if callable(reader) else ()

    def get_source_table_view(self, source_table_id: str) -> tuple[tuple[str, ...], tuple[tuple[str, ...], ...], str] | None:
        table = next((item for item in self.list_source_tables() if item.source_table_id == source_table_id), None)
        if table is None:
            return None
        source = next((item for item in self._repository.list_sources() if item.source_id == table.source_id), None)
        source_label = source.document_no if source else "标准资料"
        if table.provider_id in {"CARBON_MATERIAL_C4", "CARBON_MATERIAL_C5"}:
            from packages.standards.carbon_material import ALGORITHM_VERSION, steam_reference_table_rows

            table_code = table.display_number
            values = steam_reference_table_rows(table_code)
            if table.provider_id == "CARBON_MATERIAL_C4":
                rows = tuple((format(pressure, "f"), format(enthalpy, "f")) for pressure, enthalpy in values)
                headers = tuple(column.label for column in table.columns)
            else:
                temperatures = tuple(sorted({row[0] for row in values}))
                pressures = tuple(sorted({row[1] for row in values}))
                lookup = {(temperature, pressure): enthalpy for temperature, pressure, enthalpy in values}
                headers = (table.columns[0].label, *(f"{pressure:g} MPa" for pressure in pressures))
                rows = tuple(
                    (format(temperature, "f"), *(format(lookup[(temperature, pressure)], "f") for pressure in pressures))
                    for temperature in temperatures
                )
            note = f"来源：{source_label} {table.source_location}。只读数据来自版本化计算器（{ALGORITHM_VERSION}）。{table.notes}"
            return headers, rows, note
        if table.provider_id == "CANONICAL_CONVERSION_RULES":
            reader = getattr(self._repository, "list_conversion_rules", None)
            rules = tuple(reader()) if callable(reader) else ()
            headers = tuple(column.label for column in table.columns)
            rows = tuple(
                (f"{rule.from_unit} → {rule.to_unit}", f"× {rule.multiplier}；+ {rule.offset}", rule.source_location)
                for rule in rules
            )
            return headers, rows, f"来源：{source_label}。单位换算只读自正式目录。"

        assets_by_id = {item.asset_id: item for item in self.list_reference_data_assets()}
        parameters = {item.parameter_id: item for item in self._repository.list_parameters()}
        subjects = {item.subject_id: item for item in self._repository.list_subjects()}
        bindings = tuple(
            item for item in self.list_reference_data_bindings()
            if item.source_table_id == table.source_table_id
        )
        grouped: dict[str, list[ReferenceDataBindingCatalogRecord]] = {}
        for binding in bindings:
            if binding.binding_type == "FACTOR_SOURCE":
                grouped.setdefault(binding.asset_id, []).append(binding)
        columns = table.columns
        headers = tuple(column.label for column in columns)
        table_assets = [
            (assets_by_id[asset_id], tuple(group_bindings))
            for asset_id, group_bindings in grouped.items() if asset_id in assets_by_id
        ]
        if table.layout == "parameter_matrix":
            by_subject: dict[str, dict[str, tuple[ReferenceDataAssetCatalogRecord, tuple[ReferenceDataBindingCatalogRecord, ...]]]] = {}
            for asset, asset_bindings in table_assets:
                parameter = parameters.get(asset.parameter_id)
                if parameter is not None:
                    by_subject.setdefault(asset.subject_id, {})[parameter.parameter_type.value] = (asset, asset_bindings)
            output_rows: list[tuple[str, ...]] = []
            for subject_id, values_by_type in sorted(
                by_subject.items(), key=lambda pair: subjects.get(pair[0]).name if pair[0] in subjects else pair[0]
            ):
                subject = subjects.get(subject_id)
                row_values: list[str] = []
                for column in columns:
                    if column.key == "subject":
                        row_values.append(subject.name if subject else "—")
                        continue
                    match_key = column.parameter_type.value if column.parameter_type else column.key
                    value = values_by_type.get(match_key)
                    if value is None and column.key == "activity_unit":
                        value = values_by_type.get("LOWER_HEATING_VALUE")
                    if value is None:
                        row_values.append("—")
                    elif column.key == "activity_unit":
                        unit = value[0].unit
                        row_values.append(unit.split("/", 1)[-1] if "/" in unit else unit)
                    else:
                        row_values.append(format(value[0].value, "f"))
                output_rows.append(tuple(row_values))
            rows = tuple(output_rows)
        else:
            output_rows = []
            for asset, asset_bindings in sorted(
                table_assets,
                key=lambda pair: (
                    subjects.get(pair[0].subject_id).name if pair[0].subject_id in subjects else "",
                    parameters.get(pair[0].parameter_id).name if pair[0].parameter_id in parameters else "",
                    pair[0].asset_id,
                ),
            ):
                parameter = parameters.get(asset.parameter_id)
                subject = subjects.get(asset.subject_id)
                location = "；".join(dict.fromkeys(item.source_location for item in asset_bindings))
                value_by_key = {
                    "subject": subject.name if subject else "—",
                    "parameter": parameter.name if parameter else "—",
                    "value": format(asset.value, "f"),
                    "unit": asset.unit,
                    "source_location": location,
                    "source": source_label,
                }
                output_rows.append(tuple(value_by_key.get(column.key, "—") for column in columns))
            rows = tuple(output_rows)
        note = f"来源：{source_label} {table.source_location}。{table.notes}".strip()
        return headers, rows, note

    def search_reference_library(
        self, query: str = "", *, source_id: str | None = None
    ) -> tuple[ReferenceLibrarySearchResult, ...]:
        sources = {item.source_id: item for item in self._repository.list_sources()}
        tables = self.list_source_tables(source_id)
        table_by_id = {item.source_table_id: item for item in self.list_source_tables()}
        parameters = {item.parameter_id: item for item in self._repository.list_parameters()}
        subjects = {item.subject_id: item for item in self._repository.list_subjects()}
        all_bindings = self.list_reference_data_bindings()
        bindings_by_asset: dict[str, list[ReferenceDataBindingCatalogRecord]] = {}
        for binding in all_bindings:
            if source_id is None or table_by_id.get(binding.source_table_id, None) is not None and table_by_id[binding.source_table_id].source_id == source_id:
                bindings_by_asset.setdefault(binding.asset_id, []).append(binding)
        results: list[ReferenceLibrarySearchResult] = []
        for standard in self._repository.list_standards():
            if source_id is not None and standard.official_source_id != source_id:
                continue
            source = sources.get(standard.official_source_id)
            status = self.status_label(self.standard_status(standard))
            if _matches(query, (
                standard.standard_number, standard.standard_name, standard.version, status,
                standard.issuing_authority, standard.competent_authority,
                standard.technical_committee, standard.notes,
                source.document_no if source else "", source.document_name if source else "",
                source.publisher if source else "",
            )):
                results.append(ReferenceLibrarySearchResult(
                    "standard", standard.standard_id,
                    f"{standard.standard_number} · {standard.standard_name}",
                    f"标准目录 · {status}", "", "", standard=standard,
                ))
        for source in sources.values():
            if source_id is not None and source.source_id != source_id:
                continue
            if _matches(query, (
                source.document_no, source.document_name, source.publisher,
                source.publication_date, source.effective_from, source.effective_to,
                source.region, source.version, self.source_type_label(source.source_type),
                self.review_status_label(source.review_status), source.notes, source.official_url or "",
            )):
                results.append(ReferenceLibrarySearchResult(
                    "source", source.source_id,
                    f"{source.document_no} · {source.document_name}",
                    f"{self.source_type_label(source.source_type)} · {source.publisher}",
                    "", "", source=source,
                ))
        for table in tables:
            source = sources.get(table.source_id)
            table_content: tuple[object, ...] = ()
            if query.strip():
                table_view = self.get_source_table_view(table.source_table_id)
                if table_view is not None:
                    headers, rows, note = table_view
                    table_content = (*headers, *(value for row in rows for value in row), note)
            if _matches(query, (table.display_number, table.title, table.source_location, table.notes,
                                ((source.document_no, source.document_name, source.publisher) if source else ()),
                                *table_content)):
                results.append(ReferenceLibrarySearchResult(
                    "table", table.source_table_id, f"{table.display_number} · {table.title}",
                    source.document_no if source else "标准资料", "", "", table=table,
                ))
        for asset in self.list_reference_data_assets():
            asset_bindings = tuple(bindings_by_asset.get(asset.asset_id, ()))
            if not asset_bindings:
                continue
            parameter = parameters.get(asset.parameter_id)
            subject = subjects.get(asset.subject_id)
            source_text: list[object] = []
            for binding in asset_bindings:
                table = table_by_id.get(binding.source_table_id)
                source = sources.get(table.source_id) if table else None
                source_text.extend((binding.source_location, binding.notes, table.title if table else "", table.display_number if table else ""))
                if source:
                    source_text.extend((source.document_no, source.document_name, source.publisher))
            if not _matches(query, (
                parameter.name if parameter else "", parameter.canonical_unit if parameter else "",
                subject.name if subject else "", *(subject.aliases if subject else ()),
                asset.value, asset.unit, asset.value_type.value, asset.notes, *source_text,
            )):
                continue
            source_labels = tuple(dict.fromkeys(
                sources[table_by_id[b.source_table_id].source_id].document_no
                for b in asset_bindings if b.source_table_id in table_by_id and table_by_id[b.source_table_id].source_id in sources
            ))
            title = f"{subject.name if subject else '参数'} · {parameter.name if parameter else ''}".strip(" ·")
            subtitle = "、".join(source_labels) or "已登记来源"
            if len(asset_bindings) > 1:
                subtitle += f" · {len(asset_bindings)} 处依据"
            results.append(ReferenceLibrarySearchResult(
                "asset", f"{asset.asset_id}@{asset.asset_version}", title, subtitle,
                format(asset.value, "f"), asset.unit, asset=asset, bindings=asset_bindings,
            ))
        type_order = {"standard": 0, "source": 1, "table": 2, "asset": 3}
        results.sort(key=lambda item: (type_order.get(item.result_type, 9), item.title, item.key))
        return tuple(results)

    def get_factor_detail(self, factor_id: str) -> ParameterFactorResult | None:
        for result in self.search_parameter_factors():
            if result.factor is not None and result.factor.factor_id == factor_id:
                return result
        return None


def create_catalog_query_service(path: str | Path | None) -> CatalogQueryService:
    """Create a query service, degrading safely when the optional catalog is absent."""

    from packages.persistence.catalog_repository import (
        CatalogRepositoryError,
        EmptyCatalogRepository,
        SQLiteCatalogRepository,
    )

    if path is None:
        return CatalogQueryService(EmptyCatalogRepository())
    try:
        repository = SQLiteCatalogRepository(path)
    except CatalogRepositoryError:
        return CatalogQueryService(EmptyCatalogRepository())
    return CatalogQueryService(repository)

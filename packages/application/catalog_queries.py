"""Application-level read services for the G04 catalog screens."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date
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


def infer_industry(standard: StandardCatalogRecord) -> str:
    """Return a conservative filter label derived only from the official title."""

    title = standard.standard_name
    if "钢铁" in title or "焦化" in title:
        return "钢铁"
    if "铝" in title or "工业硅" in title:
        return "有色"
    if "玻璃" in title or "水泥" in title:
        return "建材"
    if "发电" in title:
        return "能源"
    return "其他"


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
        preferred = ("全部", "钢铁", "有色", "建材", "化工", "能源", "机械制造", "交通运输", "轻工", "其他")
        discovered = {
            infer_industry(standard)
            for standard in self._repository.list_standards()
        }
        return tuple(option for option in preferred if option == "全部" or option in discovered or option in {"化工", "机械制造", "交通运输", "轻工"})

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
        results: list[tuple[StandardCatalogRecord, CatalogStatus, str]] = []
        for standard in self._repository.list_standards():
            current_status = self.standard_status(standard)
            current_industry = infer_industry(standard)
            source_text = (
                standard.standard_number,
                standard.standard_name,
                standard.notes,
                current_industry,
            )
            if not _matches(query, source_text):
                continue
            if status is not CatalogStatus.ALL and current_status is not status:
                continue
            if industry != "全部" and current_industry != industry:
                continue
            if publication_year is not None and standard.publication_date.year != publication_year:
                continue
            results.append((standard, current_status, current_industry))
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

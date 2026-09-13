"""Application adapters for the G06 carbon-material calculation module."""

from __future__ import annotations

from collections.abc import Sequence

from packages.core.models import Factor, Parameter
from packages.core.parameter_resolution import ParameterResolver
from packages.core.repositories import ParameterRepository
from packages.standards.catalog import CatalogRepository


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


def create_g06_parameter_resolver(repository: CatalogRepository) -> ParameterResolver:
    """Create the G05 resolver from the read-only catalog boundary."""

    return ParameterResolver.with_default_g05_rules(CatalogParameterRepository(repository))


__all__ = ["CatalogParameterRepository", "create_g06_parameter_resolver"]

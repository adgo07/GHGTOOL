"""Small local standard dispatch; no discovery framework or business fallbacks."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from collections.abc import Callable

@dataclass(frozen=True)
class StandardImplementation:
    standard_id: str
    version: str
    title: str
    editor_key: str
    calculator_factory: Callable[[Any], Any]
    excel_factory: Callable[[Any, Any], Any]
    reference_providers: tuple[tuple[str, Callable], ...] = ()
    report_factory: Callable | None = None
    accepts_input: Callable | None = None
    input_codec_factory: Callable | None = None

class StandardRegistry:
    def __init__(self, implementations):
        self._items = {}
        for item in implementations:
            if item.standard_id in self._items:
                raise ValueError("标准实现重复登记。")
            self._items[item.standard_id] = item

    def require(self, standard_id: str, version: str | None = None) -> StandardImplementation:
        item = self._items.get(standard_id)
        if item is None or version is not None and item.version != version:
            raise ValueError("此标准或版本尚未开放正式核算。")
        return item

    def supports(self, standard_id: str, version: str | None = None) -> bool:
        try:
            self.require(standard_id, version)
        except ValueError:
            return False
        return True

    @property
    def implementations(self):
        return tuple(self._items.values())

    @property
    def default_standard_id(self) -> str:
        if len(self._items) != 1:
            raise ValueError("请明确选择核算标准。")
        return next(iter(self._items))

    def reference_view(self, table, source_label):
        for item in self._items.values():
            for provider_id, provider in item.reference_providers:
                if table.provider_id == provider_id:
                    return provider(table, source_label)
        return None

def default_standard_registry() -> StandardRegistry:
    from .carbon_material_implementation import CARBON_MATERIAL_IMPLEMENTATION
    return StandardRegistry((CARBON_MATERIAL_IMPLEMENTATION,))

class StandardRuntime:
    """Construct a standard's services only when a business page needs them."""
    def __init__(self, catalog, record_repository=None, calculation_use_case=None, registry=None):
        self.catalog = catalog
        self.records = record_repository
        self.registry = registry or default_standard_registry()
        self._services = {}
        self._injected_use_case = calculation_use_case

    def services(self, standard_id):
        implementation = self.registry.require(standard_id)
        if standard_id not in self._services:
            from .carbon_accounting import CarbonAccountingUseCase, CarbonAccountingPreviewUseCase
            formal = self._injected_use_case
            if formal is not None and standard_id != self.registry.default_standard_id:
                raise ValueError("注入的核算服务不属于所选标准。")
            calculator = formal.calculator if formal is not None else implementation.calculator_factory(self.catalog)
            if formal is None and callable(getattr(self.records, "create_with_details", None)):
                formal = CarbonAccountingUseCase(calculator, self.records)
            self._services[standard_id] = (calculator, formal, CarbonAccountingPreviewUseCase(calculator))
        return self._services[standard_id]

    def excel(self, standard_id):
        implementation = self.registry.require(standard_id)
        return implementation.excel_factory(self.catalog, self.services(standard_id)[2])

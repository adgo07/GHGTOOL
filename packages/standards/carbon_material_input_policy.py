"""Local input policy for GB/T 32151.34—2024; not a public platform contract."""
from dataclasses import dataclass
from enum import Enum
from typing import Mapping


class InputOrigin(str, Enum):
    CATALOG = "CATALOG"
    CUSTOM = "CUSTOM"
    LEGACY_UNSPECIFIED = "LEGACY_UNSPECIFIED"


@dataclass(frozen=True, slots=True)
class FuelInputPolicy:
    required_parameters: tuple[str, ...]
    default_parameters_allowed: bool
    fch_editable: bool


def fuel_input_policy(origin: InputOrigin, *, direct_carbon: bool, heat_activity: bool = False) -> FuelInputPolicy:
    required = ("carbon_content", "oxidation_rate")
    if not direct_carbon and not heat_activity:
        required = ("lower_heating_value", *required)
    return FuelInputPolicy(required, origin is InputOrigin.CATALOG, origin is InputOrigin.CUSTOM)


def infer_fuel_origin(fuel_type: str | None, explicit: InputOrigin | None = None) -> InputOrigin:
    if explicit is not None:
        return explicit
    if fuel_type == "OTHER":
        return InputOrigin.CUSTOM
    if fuel_type is not None:
        return InputOrigin.CATALOG
    return InputOrigin.LEGACY_UNSPECIFIED


def fuel_source_violations(origin: InputOrigin, *, direct_carbon: bool,
                           sources: Mapping[str, str | None], heat_activity: bool = False
                           ) -> tuple[tuple[str, str, str], ...]:
    policy = fuel_input_policy(origin, direct_carbon=direct_carbon, heat_activity=heat_activity)
    issues = []
    if origin is InputOrigin.CUSTOM:
        for field in policy.required_parameters:
            if sources.get(field) in {"STANDARD_DEFAULT", "STANDARD_SPECIFIED"}:
                issues.append((field, "CAR-VAL-CUSTOM-FUEL-DEFAULT",
                               "自定义燃料不适用目录缺省参数，请填写当前路径需要的值并确认来源。"))
    elif not direct_carbon and sources.get("carbon_content") is not None:
        source = sources["carbon_content"]
        if origin is InputOrigin.CATALOG and source != "STANDARD_DEFAULT":
            issues.append(("carbon_content", "CAR-VAL-CATALOG-FCH-READONLY",
                           "目录燃料的单位热值含碳量采用适用缺省值；如需自行填写，请明确使用自定义燃料。"))
        elif origin is InputOrigin.LEGACY_UNSPECIFIED and source in {"USER_DEFINED", "MEASURED", "CALCULATED"}:
            issues.append(("carbon_content", "CAR-VAL-FUEL-IDENTITY-REQUIRED",
                           "历史燃料身份不明确，请确认目录燃料或自定义燃料后重新核算；原记录保持不变。"))
    return tuple(issues)


STEAM_KIND_LABELS = {"饱和蒸汽":"SATURATED", "过热蒸汽":"SUPERHEATED"}
SUPPORTED_STEAM_KINDS = tuple(STEAM_KIND_LABELS.values())


def catalog_defaults_allowed(origin: InputOrigin) -> bool:
    return origin is InputOrigin.CATALOG


def carbonate_source_violations(origin: InputOrigin | None, sources: Mapping[str,str|None]):
    if origin is not InputOrigin.CUSTOM:
        return ()
    return tuple(
        (field,"CAR-VAL-CUSTOM-CARBONATE-DEFAULT","自定义碳酸盐不适用目录缺省参数，请填写必要参数并确认来源。")
        for field, source in sources.items() if source in {"STANDARD_DEFAULT","STANDARD_SPECIFIED"}
    )

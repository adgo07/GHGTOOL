"""Issue015/017 热力专属领域辅助：边界分类与独立已知焓。

已知焓仅消费明确提供的值，不查询旧表、自动物性、目录或其他输入。
本地比焓单位注册不改变公共 Unit Contract；自动 IF97 实现/分发另行决策。
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from packages.core.decimal_policy import DecimalPolicy
from packages.core.errors import DomainValidationError
from packages.core.units import UnitDefinition, UnitService
from packages.standards.carbon_material import HeatInput, SteamEnthalpyEvaluation

KNOWN_ENTHALPY_METHOD_VERSION = "CAR-HEAT-KNOWN-017.1"

_SPECIFIC_ENERGY_UNITS = (
    UnitDefinition("heat_kj_per_kg", "kJ/kg", "specific_energy", Decimal("1")),
    UnitDefinition("heat_gj_per_kg", "GJ/kg", "specific_energy", Decimal("1000000")),
    UnitDefinition("heat_gj_per_t", "GJ/t", "specific_energy", Decimal("1000")),
)


def evaluate_known_enthalpy(
    line: HeatInput, *, policy: DecimalPolicy, numeric_profile_id: str,
) -> SteamEnthalpyEvaluation:
    """按声明 Profile 归一独立已知焓，保留原输入且不求自动参考。

    有限的零/负值沿既有口径交调用方提醒，不在此改为致命校验。
    正式调用方负责将 Profile、方法版本和原/采用值冻结到 trace。
    """
    if not isinstance(policy, DecimalPolicy):
        raise DomainValidationError("已知焓必须显式提供 DecimalPolicy")
    if (not isinstance(numeric_profile_id, str) or not numeric_profile_id.strip()
            or numeric_profile_id != numeric_profile_id.strip()):
        raise DomainValidationError("已知焓必须声明有效 Numeric Profile 身份")
    if numeric_profile_id == "GHGTOOL_CARBON_DECIMAL40_CURRENT" and (
            policy.precision != 40 or policy.rounding != ROUND_HALF_UP):
        raise DomainValidationError("声明的 Carbon Profile 与数值配置不一致")
    if not isinstance(line, HeatInput):
        raise DomainValidationError("已知焓必须使用既有 HeatInput")
    if line.manual_enthalpy is not True:
        raise DomainValidationError("已知焓求值要求明确选择独立已知焓路径")
    if line.enthalpy is None:
        raise DomainValidationError("独立已知焓缺少必要数值")
    if line.enthalpy.unit not in ("kJ/kg", "GJ/kg", "GJ/t"):
        raise DomainValidationError("已知焓单位仅支持kJ/kg、GJ/kg或GJ/t")
    units = UnitService(policy, _SPECIFIC_ENERGY_UNITS)
    try:
        value = units.convert(policy.parse(line.enthalpy.value), line.enthalpy.unit, "kJ/kg")
    except (ValueError, ArithmeticError) as exc:
        raise DomainValidationError(f"已知焓数值或单位非法：{exc}") from exc
    return SteamEnthalpyEvaluation(
        value=value, reference_value=None, source="USER_MANUAL", table_id=None,
        interpolated=False, pressure_bounds=None, temperature_bounds=None,
    )


def classify_heat_boundary(
    *, energy_direction: str, source_boundary: str,
    fuel_emissions_accounted: bool | None,
) -> str:
    """仅按明确边界事实执行 Issue015，不猜测燃料或生成零排放。

    内部已计返回分派标识，调用方保留原燃料排放并退出重复购热核算；
    外送仍按既有抵扣规则处理，不要求购入热力专属资格。
    """
    if energy_direction not in ("purchased_heat", "exported_heat"):
        raise DomainValidationError("热力方向必须为购入或外送")
    if energy_direction == "exported_heat":
        return "EXPORTED"
    if fuel_emissions_accounted is not None and type(fuel_emissions_accounted) is not bool:
        raise DomainValidationError("供热燃料是否已计必须为明确布尔值或待核实")
    if source_boundary == "OUTSIDE_ENTERPRISE":
        if fuel_emissions_accounted is True:
            raise DomainValidationError("外部热源与同一企业燃料已计声明冲突，需澄清")
        return "PURCHASED"
    if source_boundary == "INSIDE_ENTERPRISE" and fuel_emissions_accounted is True:
        return "INTERNAL_ALREADY_ACCOUNTED"
    raise DomainValidationError("热源边界或供热燃料已计情况不明确，需澄清后核算")


__all__ = ["KNOWN_ENTHALPY_METHOD_VERSION", "evaluate_known_enthalpy", "classify_heat_boundary"]

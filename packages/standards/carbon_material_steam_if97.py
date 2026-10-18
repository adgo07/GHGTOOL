"""Issue017：固定 Python CoolProp IF97 后端的蒸汽焓提供者。

物性工作表示为 IEEE-754 binary64，不是 Carbon Decimal40。输入由声明的
DecimalPolicy 归一为 Pa/K，再通过 float(str(decimal)) 进入库；库的 J/kg
输出按 repr(binary64) 转为 Decimal 后除1000，得到 kJ/kg。无显示修约、
业务epsilon、旧表或其他后端回退。actual_phase 是真实库相态，不是IF97区号。
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from importlib import import_module
import math

from packages.core.decimal_policy import DecimalPolicy
from packages.core.errors import DomainValidationError
from packages.standards.carbon_material import SteamKind

METHOD_VERSION = "CAR-HEAT-IF97-017.1"
PROPERTY_PROFILE_ID = "GHGTOOL_COOLPROP_IF97_PROPERTY_V1"
IMPLEMENTATION = "Python CoolProp IF97 backend"
IMPLEMENTATION_VERSION = "8.0.0"
IMPLEMENTATION_REVISION = "ae81610e7d23efc57f9d051c8e70a4d66e87537f"
DEPENDENCY_VERSIONS = (("CoolProp", "8.0.0"), ("numpy", "2.3.3"))
BACKEND = "IF97"
FLUID = "Water"
# Mapping9.7/IAPWS R7-97(2012)常数；本产品仅干饱和/单相过热蒸汽。
CRITICAL_PRESSURE_MPA = Decimal("22.064")
# 同一临界常量的精确SI表示，不经调用方工作舍入改变物理边界。
CRITICAL_PRESSURE_PA = Decimal("22064000")
KELVIN_OFFSET = Decimal("273.15")
MPA_TO_PA = Decimal("1000000")
J_PER_KJ = Decimal("1000")


@dataclass(frozen=True, slots=True)
class IF97SteamEvaluation:
    enthalpy_kj_per_kg: Decimal
    pressure_mpa: Decimal
    temperature_c: Decimal | None
    declared_state: str
    actual_phase: str
    implementation: str
    implementation_version: str
    numeric_profile_id: str
    input_pressure_lexeme: str
    input_temperature_lexeme: str | None
    output_enthalpy_lexeme: str
    method_version: str
    implementation_revision: str
    dependency_versions: tuple[tuple[str, str], ...]
    working_pressure_pa_lexeme: str
    working_temperature_k_lexeme: str | None
    library_output_j_per_kg_lexeme: str
    quality_lexeme: str | None


def _decimal(value: object, name: str, policy: DecimalPolicy) -> Decimal:
    if not isinstance(value, Decimal):
        raise DomainValidationError(f"自动焓 {name} 必须为已规范化的有限Decimal")
    try:
        return policy.parse(value)
    except ValueError as exc:
        raise DomainValidationError(f"自动焓 {name} 必须为有限Decimal") from exc


def _binary64(value: Decimal, name: str) -> float:
    converted = float(str(value))
    if not math.isfinite(converted) or converted <= 0:
        raise DomainValidationError(f"自动焓 {name} 无法形成正的有限binary64输入")
    return converted


def _runtime():
    """运行身份不符即拒绝；不改用HEOS、旧表或其他实现。"""
    try:
        package = import_module("CoolProp")
        cp = import_module("CoolProp.CoolProp")
        numpy = import_module("numpy")
        revision = cp.get_global_param_string("gitrevision")
        if (package.__version__ != IMPLEMENTATION_VERSION
                or numpy.__version__ != "2.3.3" or revision != IMPLEMENTATION_REVISION):
            raise DomainValidationError("自动焓实现或依赖版本与固定物性Profile不一致")
        return cp
    except DomainValidationError:
        raise
    except Exception as exc:
        raise DomainValidationError("固定CoolProp/NumPy物性实现不可用，无旧表回退") from exc


def evaluate_if97_steam(
    *, steam_kind: SteamKind, pressure_mpa: Decimal,
    temperature_c: Decimal | None, policy: DecimalPolicy, numeric_profile_id: str,
) -> IF97SteamEvaluation:
    """消费绝压MPa和温度℃；返回独立物性子Profile及真实库相态。

    SATURATED仅P+Q=1，拒绝多余温度定义；SUPERHEATED为P<Pcrit且
    T>同P饱和温度的单相气体。高于临界温度、但低于临界压力的气态
    仍可作为过热汽；不将超临界流体或临界点扩为产品允许相态。
    """
    if not isinstance(policy, DecimalPolicy):
        raise DomainValidationError("自动焓必须显式提供DecimalPolicy")
    if (not isinstance(numeric_profile_id, str) or not numeric_profile_id.strip()
            or numeric_profile_id != numeric_profile_id.strip()):
        raise DomainValidationError("自动焓必须声明调用方Numeric Profile")
    if numeric_profile_id == PROPERTY_PROFILE_ID:
        raise DomainValidationError("调用方排放Profile与物性子Profile不得混同")
    if numeric_profile_id == "GHGTOOL_CARBON_DECIMAL40_CURRENT" and (
            policy.precision != 40 or policy.rounding != ROUND_HALF_UP):
        raise DomainValidationError("声明的Carbon Profile与配置不一致")
    if not isinstance(steam_kind, SteamKind):
        raise DomainValidationError("自动焓只支持明确干饱和或过热蒸汽")
    pressure = _decimal(pressure_mpa, "绝压", policy)
    if not Decimal("0") < pressure < CRITICAL_PRESSURE_MPA:
        raise DomainValidationError("自动蒸汽绝压须为正且低于临界压力，不支持超临界流体")
    if steam_kind is SteamKind.SATURATED and temperature_c is not None:
        raise DomainValidationError("干饱和路径仅使用绝压与Q=1，不接受额外温度定义")
    temperature = None
    kelvin = None
    if steam_kind is SteamKind.SUPERHEATED:
        temperature = _decimal(temperature_c, "温度", policy)
        # 原摄氏值直接精确比较，单位归一的工作修约不得隐藏微小超域。
        if not Decimal("0") <= temperature <= Decimal("2000"):
            raise DomainValidationError("自动过热蒸汽温度超出IF97有效域")
        kelvin = policy.add(temperature, KELVIN_OFFSET)
    p_pa = _binary64(policy.multiply(pressure, MPA_TO_PA), "绝压Pa")
    if Decimal(repr(p_pa)) >= CRITICAL_PRESSURE_PA:
        raise DomainValidationError(f"自动蒸汽工作绝压达到临界点（{repr(p_pa)} Pa），当前物性精度不能安全求值。")
    cp = _runtime()
    working_temperature = None
    try:
        state = cp.AbstractState(BACKEND, FLUID)
        if state.backend_name() != "IF97Backend":
            raise DomainValidationError("自动焓未使用指定IF97后端")
        if steam_kind is SteamKind.SATURATED:
            state.update(cp.PQ_INPUTS, p_pa, 1.0)
            if state.phase() != cp.iphase_twophase or state.Q() != 1.0:
                raise DomainValidationError("自动干饱和蒸汽未得到明确Q=1状态")
        else:
            saturation = cp.AbstractState(BACKEND, FLUID)
            saturation.update(cp.PQ_INPUTS, p_pa, 1.0)
            tsat = Decimal(repr(float(saturation.T())))
            if not tsat.is_finite() or kelvin <= tsat:
                raise DomainValidationError("声明过热但温度未高于同一绝压的饱和温度")
            working_temperature = _binary64(kelvin, "温度K")
            if Decimal(repr(working_temperature)) <= tsat:
                raise DomainValidationError(f"工作温度{repr(working_temperature)} K未高于同压饱和温度{tsat} K，当前物性精度不能确认过热蒸汽。")
            state.update(cp.PT_INPUTS, p_pa, working_temperature)
            if state.phase() not in (cp.iphase_gas, cp.iphase_supercritical_gas):
                raise DomainValidationError("声明过热与实际库相态不一致")
        raw_enthalpy = float(state.hmass())
        if not math.isfinite(raw_enthalpy):
            raise DomainValidationError("物性库返回非有限焓")
        raw_lexeme = repr(raw_enthalpy)
        enthalpy = policy.divide(Decimal(raw_lexeme), J_PER_KJ)
        phase = "IF97Backend:" + str(state.phase())
    except DomainValidationError:
        raise
    except Exception as exc:
        raise DomainValidationError("IF97状态超域、不相容或求值失败，无旧表/其他后端回退") from exc
    return IF97SteamEvaluation(
        enthalpy, pressure, temperature, steam_kind.value, phase,
        IMPLEMENTATION, IMPLEMENTATION_VERSION, PROPERTY_PROFILE_ID,
        str(pressure), None if temperature is None else str(temperature),
        str(enthalpy), METHOD_VERSION, IMPLEMENTATION_REVISION, DEPENDENCY_VERSIONS,
        repr(p_pa), None if working_temperature is None else repr(working_temperature),
        raw_lexeme, "1" if steam_kind is SteamKind.SATURATED else None,
    )


__all__ = ["IF97SteamEvaluation", "evaluate_if97_steam", "METHOD_VERSION",
           "PROPERTY_PROFILE_ID", "IMPLEMENTATION", "IMPLEMENTATION_VERSION",
           "IMPLEMENTATION_REVISION", "DEPENDENCY_VERSIONS"]

"""Issue020 烟气监测分段；正式 Calculator 复用的配对、覆盖与逐段原式求值。

区间为同一报告时钟的无时区 datetime、半开 [start, end)。不推测时区、
停机或全年覆盖；调用方提供真实源/计量边界身份及独立报告窗口。
仅核验配对、单位、数值和覆盖，不新增焦油参数来源规则或目录绑定。
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Sequence

from packages.core.decimal_policy import DecimalPolicy
from packages.core.errors import DomainValidationError
from packages.core.units import UnitDefinition, UnitService
from packages.standards._numeric_authority import declared_numeric_profile
from packages.standards.carbon_material import (
    FumeIncinerationInput, InputValue, ParameterValue, fume_incineration_emission,
)

CALCULATOR_ID = "CAR-FUME-SEGMENTS"
CALCULATOR_VERSION = "CAR-FUME-SEGMENTS-020.2"
FORMULA_ID = "CAR-FML-FUME-INCINERATION-001"
STANDARD_ISSUE_ID = "GHG-STD-32151-34-020"


def _identity(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise DomainValidationError(f"{name} 必须为非空、无首尾空白的稳定身份")


def _interval(start: datetime, end: datetime) -> None:
    if (not isinstance(start, datetime) or not isinstance(end, datetime)
            or start.tzinfo is not None or end.tzinfo is not None):
        raise DomainValidationError("区间必须为同一报告时钟的无时区 datetime")
    if start >= end:
        raise DomainValidationError("区间起点必须早于终点")


@dataclass(frozen=True, slots=True)
class FumeReportingWindow:
    source_instance_id: str
    metering_boundary_id: str
    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        _identity(self.source_instance_id, "source_instance_id")
        _identity(self.metering_boundary_id, "metering_boundary_id")
        _interval(self.start, self.end)


@dataclass(frozen=True, slots=True)
class FumeMonitoringSegment:
    source_instance_id: str
    metering_boundary_id: str
    segment_id: str
    start: datetime
    end: datetime
    measurements: FumeIncinerationInput

    def __post_init__(self) -> None:
        _identity(self.source_instance_id, "source_instance_id")
        _identity(self.metering_boundary_id, "metering_boundary_id")
        _identity(self.segment_id, "segment_id")
        _interval(self.start, self.end)
        if not isinstance(self.measurements, FumeIncinerationInput):
            raise DomainValidationError("measurements 必须使用既有 FumeIncinerationInput")
        if self.measurements.instance_id != self.source_instance_id:
            raise DomainValidationError("烟气段与测量值的源实例身份不一致")


@dataclass(frozen=True, slots=True)
class FumeSegmentResult:
    segment: FumeMonitoringSegment
    duration_days: Decimal
    q: Decimal
    qvar: Decimal
    hm: Decimal
    fch: Decimal
    fox: Decimal
    amount_tco2: Decimal


@dataclass(frozen=True, slots=True)
class FumeCoverageResult:
    reporting_window: FumeReportingWindow
    segments: tuple[FumeSegmentResult, ...]
    uncovered_intervals: tuple[tuple[datetime, datetime], ...]
    covered_duration_days: Decimal
    covered_amount_tco2: Decimal

    @property
    def complete(self) -> bool:
        return not self.uncovered_intervals


@dataclass(frozen=True, slots=True)
class FumeSegmentsResult:
    coverage: tuple[FumeCoverageResult, ...]
    covered_amount_tco2: Decimal
    numeric_profile_id: str
    policy: DecimalPolicy
    calculator_id: str = CALCULATOR_ID
    calculator_version: str = CALCULATOR_VERSION
    numeric_contract_version: str = "v1"
    formula_id: str = FORMULA_ID
    standard_issue_id: str = STANDARD_ISSUE_ID
    time_precision: str = "HOUR"
    duration_normalization: str = "INTEGER_HOURS_TO_DAYS_DECLARED_PROFILE"

    @property
    def complete(self) -> bool:
        # 无窗口不构成已证明覆盖；调用方不得据此声称全年完整。
        return bool(self.coverage) and all(item.complete for item in self.coverage)


def _elapsed_microseconds(start: datetime, end: datetime) -> int:
    delta = end - start
    return (delta.days * 86400 + delta.seconds) * 1000000 + delta.microseconds


def _quantity(value: InputValue | ParameterValue | None, unit: str,
              field: str, policy: DecimalPolicy, units: UnitService) -> Decimal:
    if value is None:
        raise DomainValidationError(f"烟气段缺少必要值：{field}")
    try:
        raw = policy.parse(value.value)
        if raw < 0:
            raise DomainValidationError(f"烟气段 {field} 不得为负数")
        normalized = raw if value.unit == unit else units.convert(raw, value.unit, unit)
    except ValueError as exc:
        raise DomainValidationError(f"烟气段 {field} 数值或单位非法：{exc}") from exc
    if normalized < 0:
        raise DomainValidationError(f"烟气段 {field} 不得为负数")
    return normalized


def evaluate_fume_segments(
    segments: Sequence[FumeMonitoringSegment],
    reporting_windows: Sequence[FumeReportingWindow],
    *, policy: DecimalPolicy, numeric_profile_id: str,
) -> FumeSegmentsResult:
    """逐段复用式(9)，返回已覆盖合计及真实缺口；任一非法段整体抛错。

    duration 保留原录入值；正式起止须为整小时，h与整数小时精确核对，
    d与声明Profile下整数小时/24的规范化日值全值核对，两路采用同一日值。
    不从报告期回填。所有运算使用调用者声明的 Profile，结果保留其身份
    和配置。参数资格及真实 Resolver 仍由正式公共入口负责。
    """
    if not isinstance(policy, DecimalPolicy):
        raise DomainValidationError("必须显式声明 DecimalPolicy")
    _identity(numeric_profile_id, "numeric_profile_id")
    if numeric_profile_id == "GHGTOOL_CARBON_DECIMAL40_CURRENT" and (
            policy.precision != 40 or policy.rounding != ROUND_HALF_UP):
        raise DomainValidationError("声明的 Carbon Profile 与数值配置不一致")
    segments, reporting_windows = tuple(segments), tuple(reporting_windows)
    if any(not isinstance(item, FumeMonitoringSegment) for item in segments):
        raise DomainValidationError("segments 必须为 FumeMonitoringSegment")
    if any(not isinstance(item, FumeReportingWindow) for item in reporting_windows):
        raise DomainValidationError("reporting_windows 必须为 FumeReportingWindow")
    windows = {}
    for window in reporting_windows:
        key = (window.source_instance_id, window.metering_boundary_id)
        if key in windows:
            raise DomainValidationError("同一源实例和计量边界不得重复声明报告窗口")
        windows[key] = window
    grouped = {key: [] for key in windows}
    identities = set()
    for segment in segments:
        key = (segment.source_instance_id, segment.metering_boundary_id)
        identity = (*key, segment.segment_id)
        if identity in identities:
            raise DomainValidationError("同一源实例和计量边界的监测段身份重复")
        identities.add(identity)
        if key not in windows:
            raise DomainValidationError("烟气段缺少对应源实例和计量边界的报告窗口")
        window = windows[key]
        if segment.start < window.start or segment.end > window.end:
            raise DomainValidationError("烟气段超出对应报告窗口，不允许裁剪或外推")
        grouped[key].append(segment)

    # h/d 是本标准专属时长单位，复用 UnitService；不改公共单位注册库。
    time_units = UnitService(policy, (
        UnitDefinition("h", "h", "time", Decimal("1")),
        UnitDefinition("d", "d", "time", Decimal("24")),
    ))
    units = UnitService(policy)
    coverage = []
    with declared_numeric_profile(policy):
        for key, window in windows.items():
            cursor = window.start
            gaps, results = [], []
            covered_days, total = Decimal("0"), Decimal("0")
            for segment in sorted(grouped[key], key=lambda item: (item.start, item.end, item.segment_id)):
                if segment.start < cursor:
                    raise DomainValidationError("同一源实例和计量边界的烟气段重叠")
                if segment.start > cursor:
                    gaps.append((cursor, segment.start))
                values = segment.measurements
                _quantity(values.duration, "h", "T", policy, time_units)
                # Owner整小时产品精度决定；只限制正式新算，不限制旧对象解码/保存。
                if any((point.minute, point.second, point.microsecond) != (0, 0, 0)
                       for point in (segment.start, segment.end)):
                    raise DomainValidationError(
                        "当前烟气分段核算只支持整小时起止时间，分钟、秒和微秒必须为0；"
                        "原时间不会自动截断或改写，请核实真实监测区间。")
                hours = Decimal(_elapsed_microseconds(segment.start, segment.end) // 3600000000)
                duration = policy.divide(hours, Decimal("24"))
                expected = hours if values.duration.unit == "h" else duration
                if values.duration.value != expected:
                    raise DomainValidationError(
                        f"烟气段时长与起止区间不一致；请优先选择小时并填写{hours}。"
                        "天值须与软件采用的小时转天规范化值全值一致，不能填写显示近似值。")
                q = _quantity(values.q, "Nm3/h", "Q", policy, units)
                qvar = _quantity(values.qvar, "mg/Nm3", "QVar", policy, units)
                hm = _quantity(values.hm, "GJ/t", "HM", policy, units)
                fch = _quantity(values.fch, "tC/GJ", "FCh", policy, units)
                fox = _quantity(values.fox, "ratio", "FOx", policy, units)
                if values.fox.value > units.convert("1", "ratio", values.fox.unit):
                    raise DomainValidationError("烟气段 FOx 必须处于0%到100%")
                amount = fume_incineration_emission(q, qvar, hm, fch, fox, duration)
                results.append(FumeSegmentResult(segment, duration, q, qvar, hm, fch, fox, amount))
                covered_days = policy.add(covered_days, duration)
                total = policy.add(total, amount)
                cursor = segment.end
            if cursor < window.end:
                gaps.append((cursor, window.end))
            coverage.append(FumeCoverageResult(window, tuple(results), tuple(gaps), covered_days, total))
        total = Decimal("0")
        for item in coverage:
            total = policy.add(total, item.covered_amount_tco2)
    return FumeSegmentsResult(tuple(coverage), total, numeric_profile_id, policy)

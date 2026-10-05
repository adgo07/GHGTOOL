"""Shared, platform-independent normalization for carbon process materials.

The public input rows describe physical materials.  This module maps those
rows to the existing GB/T 32151.34 equation variables so the desktop UI and
future import adapters use the same aggregation semantics.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Iterable

from packages.core.decimal_policy import DecimalPolicy, DecimalPolicyError


MATERIAL_NORMALIZATION_VERSION = "CAR-MATERIAL-NORMALIZATION-V1"


class MaterialRole(str, Enum):
    CALCINATION_FEED = "calcination_feed"
    CALCINED_PRODUCT = "calcined_product"
    UNDERBURN_RECOVERED = "underburn_recovered"
    CARBON_DUST = "carbon_dust"
    BAKING_FILLER = "baking_filler"
    GREEN_BAKING_PRODUCT = "green_baking_product"
    BAKED_PRODUCT = "baked_product"
    BAKING_BYPRODUCT = "baking_byproduct"
    GRAPHITIZATION_PACKING = "graphitization_packing"
    GREEN_GRAPHITIZATION_PRODUCT = "green_graphitization_product"
    GRAPHITIZED_PRODUCT = "graphitized_product"
    GRAPHITIZATION_BYPRODUCT = "graphitization_byproduct"


class MaterialDataSource(str, Enum):
    STANDARD_DEFAULT = "STANDARD_DEFAULT"
    MEASURED = "MEASURED"
    CHEMICAL_CALCULATION = "CHEMICAL_CALCULATION"


@dataclass(frozen=True, slots=True)
class MaterialAmount:
    """Common material quantity shape shared with non-GUI adapters."""

    mass: Decimal
    fixed_carbon: Decimal | None = None
    volatile_matter: Decimal | None = None

    def __post_init__(self) -> None:
        policy = DecimalPolicy()
        object.__setattr__(self, "mass", policy.parse(self.mass))
        if self.fixed_carbon is not None:
            object.__setattr__(self, "fixed_carbon", policy.parse(self.fixed_carbon))
        if self.volatile_matter is not None:
            object.__setattr__(self, "volatile_matter", policy.parse(self.volatile_matter))


def total_mass(rows: Iterable[MaterialAmount], *, policy: DecimalPolicy | None = None) -> Decimal:
    profile = policy or DecimalPolicy()
    total = Decimal("0")
    for row in rows:
        total = profile.add(total, row.mass)
    return total


def weighted_fraction(
    rows: Iterable[MaterialAmount],
    field: str,
    *,
    policy: DecimalPolicy | None = None,
) -> Decimal:
    """Return a mass-weighted fixed-carbon or volatile-matter fraction."""

    profile = policy or DecimalPolicy()
    material_rows = tuple(rows)
    total = total_mass(material_rows, policy=profile)
    if total == 0:
        return Decimal("0")
    numerator = Decimal("0")
    for row in material_rows:
        fraction = getattr(row, field)
        if fraction is None:
            if row.mass == 0:
                continue
            raise ValueError(f"positive material mass requires {field}")
        numerator = profile.add(numerator, profile.multiply(row.mass, fraction))
    return profile.divide(numerator, total)


def carbon_mass(rows: Iterable[MaterialAmount], *, policy: DecimalPolicy | None = None) -> Decimal:
    """Sum material mass × fixed-carbon fraction into tC."""

    profile = policy or DecimalPolicy()
    total = Decimal("0")
    for row in rows:
        if row.fixed_carbon is None:
            if row.mass == 0:
                continue
            raise ValueError("positive material mass requires fixed_carbon")
        total = profile.add(total, profile.multiply(row.mass, row.fixed_carbon))
    return total


@dataclass(frozen=True, slots=True)
class MaterialInputLine:
    line_id: str
    role: MaterialRole
    name: str
    mass_t: object | None
    fixed_carbon_percent: object | None = None
    fixed_carbon_source: MaterialDataSource = MaterialDataSource.MEASURED
    volatile_matter_percent: object | None = None
    volatile_matter_source: MaterialDataSource = MaterialDataSource.MEASURED

    def __post_init__(self) -> None:
        if not isinstance(self.line_id, str) or not self.line_id.strip():
            raise ValueError("line_id is required")
        if not isinstance(self.role, MaterialRole):
            raise ValueError("role must be a MaterialRole")
        if not isinstance(self.fixed_carbon_source, MaterialDataSource):
            raise ValueError("fixed_carbon_source must be a MaterialDataSource")
        if not isinstance(self.volatile_matter_source, MaterialDataSource):
            raise ValueError("volatile_matter_source must be a MaterialDataSource")


@dataclass(frozen=True, slots=True)
class MaterialNormalizationProblem:
    code: str
    message: str
    field_id: str


@dataclass(frozen=True, slots=True)
class NormalizedMaterialProcess:
    process: str
    values: tuple[tuple[str, Decimal], ...]
    problems: tuple[MaterialNormalizationProblem, ...]
    included_lines: tuple[MaterialInputLine, ...]

    def value(self, name: str) -> Decimal:
        return dict(self.values)[name]


@dataclass(frozen=True, slots=True)
class _ParsedLine:
    line: MaterialInputLine
    mass: Decimal
    fixed_carbon: Decimal | None
    volatile_matter: Decimal | None


_PROCESS_ROLES: dict[str, set[MaterialRole]] = {
    "calcination": {
        MaterialRole.CALCINATION_FEED,
        MaterialRole.CALCINED_PRODUCT,
        MaterialRole.UNDERBURN_RECOVERED,
        MaterialRole.CARBON_DUST,
    },
    "baking": {
        MaterialRole.BAKING_FILLER,
        MaterialRole.GREEN_BAKING_PRODUCT,
        MaterialRole.BAKED_PRODUCT,
        MaterialRole.BAKING_BYPRODUCT,
    },
    "graphitization": {
        MaterialRole.GRAPHITIZATION_PACKING,
        MaterialRole.GREEN_GRAPHITIZATION_PRODUCT,
        MaterialRole.GRAPHITIZED_PRODUCT,
        MaterialRole.GRAPHITIZATION_BYPRODUCT,
    },
}

_REQUIRED_ROLES: dict[str, tuple[MaterialRole, ...]] = {
    "calcination": (MaterialRole.CALCINATION_FEED, MaterialRole.CALCINED_PRODUCT),
    "baking": (MaterialRole.GREEN_BAKING_PRODUCT, MaterialRole.BAKED_PRODUCT),
    "graphitization": (MaterialRole.GREEN_GRAPHITIZATION_PRODUCT, MaterialRole.GRAPHITIZED_PRODUCT),
}

_FIXED_CARBON_ROLES = {
    MaterialRole.CALCINATION_FEED,
    MaterialRole.CALCINED_PRODUCT,
    MaterialRole.UNDERBURN_RECOVERED,
    MaterialRole.CARBON_DUST,
    MaterialRole.BAKING_FILLER,
    MaterialRole.GREEN_BAKING_PRODUCT,
    MaterialRole.BAKED_PRODUCT,
    MaterialRole.BAKING_BYPRODUCT,
    MaterialRole.GRAPHITIZATION_PACKING,
    MaterialRole.GREEN_GRAPHITIZATION_PRODUCT,
    MaterialRole.GRAPHITIZED_PRODUCT,
    MaterialRole.GRAPHITIZATION_BYPRODUCT,
}

_VOLATILE_MATTER_ROLES = {
    MaterialRole.CALCINATION_FEED,
    MaterialRole.CALCINED_PRODUCT,
    MaterialRole.BAKING_FILLER,
    MaterialRole.GREEN_BAKING_PRODUCT,
    MaterialRole.GRAPHITIZATION_PACKING,
}


def _field(line: MaterialInputLine, field: str) -> str:
    return f"{line.line_id}.{field}"


def _present(value: object | None) -> bool:
    return value is not None and str(value).strip() != ""


def _parse_percent(
    value: object | None,
    source: MaterialDataSource,
    *,
    field_id: str,
    label: str,
    required: bool,
    policy: DecimalPolicy,
    problems: list[MaterialNormalizationProblem],
) -> Decimal | None:
    if not _present(value):
        if required:
            problems.append(MaterialNormalizationProblem(
                "CAR-VAL-MATERIAL-COMPONENT-MISSING",
                f"{label}未填写，请补充该物料的{label}。",
                field_id,
            ))
        return None
    if source is MaterialDataSource.STANDARD_DEFAULT:
        problems.append(MaterialNormalizationProblem(
            "CAR-VAL-MATERIAL-DEFAULT-MISSING",
            f"当前没有可用的{label}标准缺省值，请改用实测值或化学计算并填写数值。",
            field_id,
        ))
        return None
    try:
        parsed = policy.parse(str(value))
    except (DecimalPolicyError, ValueError):
        problems.append(MaterialNormalizationProblem(
            "GEN-VAL-NUMERIC-INVALID",
            f"{label}必须填写有效数字。",
            field_id,
        ))
        return None
    if not Decimal("0") <= parsed <= Decimal("100"):
        problems.append(MaterialNormalizationProblem(
            "CAR-VAL-PERCENT-RANGE",
            f"{label}应在0%到100%之间。",
            field_id,
        ))
        return None
    return policy.divide(parsed, Decimal("100"))


def normalize_material_inputs(
    process: str,
    rows: Iterable[MaterialInputLine],
    *,
    policy: DecimalPolicy,
) -> NormalizedMaterialProcess:
    """Aggregate physical material lines into the frozen formula variables.

    Percentages are entered as 0..100 values and normalized to ratios.  An
    absent optional role contributes zero.  A zero mass is explicit valid
    data, and does not require composition values because its contribution is
    exactly zero.
    """
    if process not in _PROCESS_ROLES:
        raise ValueError(f"unsupported carbon process: {process}")

    problems: list[MaterialNormalizationProblem] = []
    parsed_rows: list[_ParsedLine] = []
    included_lines: list[MaterialInputLine] = []
    for line in rows:
        if not isinstance(line, MaterialInputLine):
            raise TypeError("rows must contain MaterialInputLine values")
        if line.role not in _PROCESS_ROLES[process]:
            problems.append(MaterialNormalizationProblem(
                "CAR-VAL-MATERIAL-ROLE-PROCESS",
                "物料类别与当前过程不匹配，请检查该行类别。",
                _field(line, "role"),
            ))
            continue
        active = any((_present(line.name), _present(line.mass_t), _present(line.fixed_carbon_percent), _present(line.volatile_matter_percent)))
        if not active:
            continue
        included_lines.append(line)
        if not line.name.strip():
            problems.append(MaterialNormalizationProblem(
                "GEN-VAL-REQUIRED-MISSING", "请填写物料名称。", _field(line, "name"),
            ))
        if not _present(line.mass_t):
            problems.append(MaterialNormalizationProblem(
                "GEN-VAL-REQUIRED-MISSING", "请填写物料数量。", _field(line, "mass"),
            ))
            continue
        try:
            mass = policy.parse(str(line.mass_t))
        except (DecimalPolicyError, ValueError):
            problems.append(MaterialNormalizationProblem(
                "GEN-VAL-NUMERIC-INVALID", "物料数量必须填写有效数字。", _field(line, "mass"),
            ))
            continue
        if mass < 0:
            problems.append(MaterialNormalizationProblem(
                "CAR-VAL-NONNEGATIVE", "物料数量不能为负数。", _field(line, "mass"),
            ))
            continue
        needs_fixed = line.role in _FIXED_CARBON_ROLES
        needs_volatile = line.role in _VOLATILE_MATTER_ROLES
        fixed = _parse_percent(
            line.fixed_carbon_percent,
            line.fixed_carbon_source,
            field_id=_field(line, "fixed_carbon"),
            label="固定碳含量",
            required=needs_fixed and mass > 0,
            policy=policy,
            problems=problems,
        )
        volatile = _parse_percent(
            line.volatile_matter_percent,
            line.volatile_matter_source,
            field_id=_field(line, "volatile_matter"),
            label="挥发分",
            required=needs_volatile and mass > 0,
            policy=policy,
            problems=problems,
        )
        parsed_rows.append(_ParsedLine(line, mass, fixed, volatile))

    present_roles = {line.line.role for line in parsed_rows}
    for role in _REQUIRED_ROLES[process]:
        if role not in present_roles:
            problems.append(MaterialNormalizationProblem(
                "GEN-VAL-REQUIRED-MISSING",
                f"缺少{_role_label(role)}物料；如本期数量为0，请明确填写0。",
                f"{process}.{role.value}",
            ))

    def aggregate(roles: set[MaterialRole], component: str | None = None) -> tuple[Decimal, Decimal, Decimal]:
        selected = tuple(
            MaterialAmount(item.mass, item.fixed_carbon, item.volatile_matter)
            for item in parsed_rows
            if item.line.role in roles
        )
        mass = total_mass(selected, policy=policy)
        if component is None:
            return mass, Decimal("0"), Decimal("0")
        try:
            fraction = weighted_fraction(selected, component, policy=policy)
        except ValueError:
            # Keep returning a problem report for incomplete lines; the caller
            # blocks the calculation before using these placeholder aggregates.
            fraction = Decimal("0")
        if component == "fixed_carbon":
            try:
                component_mass = carbon_mass(selected, policy=policy)
            except ValueError:
                component_mass = Decimal("0")
        else:
            component_mass = Decimal("0")
        return mass, fraction, component_mass

    if process == "calcination":
        gc, wfc, _ = aggregate({MaterialRole.CALCINATION_FEED}, "fixed_carbon")
        _, wvar, _ = aggregate({MaterialRole.CALCINATION_FEED}, "volatile_matter")
        cc, wvar_c, _ = aggregate({MaterialRole.CALCINED_PRODUCT}, "volatile_matter")
        _, wfc_c, _ = aggregate({
            MaterialRole.CALCINED_PRODUCT,
            MaterialRole.UNDERBURN_RECOVERED,
            MaterialRole.CARBON_DUST,
        }, "fixed_carbon")
        ucc, _, _ = aggregate({MaterialRole.UNDERBURN_RECOVERED})
        du, _, _ = aggregate({MaterialRole.CARBON_DUST})
        values = {"gc": gc, "wfc": wfc, "cc": cc, "ucc": ucc, "du": du, "wfc_c": wfc_c, "wvar": wvar, "wvar_c": wvar_c}
    elif process == "baking":
        bpm, bpmfc, _ = aggregate({MaterialRole.BAKING_FILLER}, "fixed_carbon")
        _, bpmvar, _ = aggregate({MaterialRole.BAKING_FILLER}, "volatile_matter")
        bg, bgfc, _ = aggregate({MaterialRole.GREEN_BAKING_PRODUCT}, "fixed_carbon")
        _, bgvar, _ = aggregate({MaterialRole.GREEN_BAKING_PRODUCT}, "volatile_matter")
        bp, bpfc, _ = aggregate({MaterialRole.BAKED_PRODUCT}, "fixed_carbon")
        _, _, bwt = aggregate({MaterialRole.BAKING_BYPRODUCT}, "fixed_carbon")
        values = {"bpm": bpm, "bpmfc": bpmfc, "bg": bg, "bgfc": bgfc, "bwt": bwt, "bp": bp, "bpfc": bpfc, "bpmvar": bpmvar, "bgvar": bgvar}
    else:
        gpm, gpmfc, _ = aggregate({MaterialRole.GRAPHITIZATION_PACKING}, "fixed_carbon")
        _, gpmvar, _ = aggregate({MaterialRole.GRAPHITIZATION_PACKING}, "volatile_matter")
        gta, gtafc, _ = aggregate({MaterialRole.GREEN_GRAPHITIZATION_PRODUCT}, "fixed_carbon")
        gp, gpfc, _ = aggregate({MaterialRole.GRAPHITIZED_PRODUCT}, "fixed_carbon")
        _, _, gwt = aggregate({MaterialRole.GRAPHITIZATION_BYPRODUCT}, "fixed_carbon")
        values = {"gpm": gpm, "gpmfc": gpmfc, "gta": gta, "gtafc": gtafc, "gwt": gwt, "gp": gp, "gpfc": gpfc, "gpmvar": gpmvar}

    return NormalizedMaterialProcess(
        process=process,
        values=tuple(values.items()),
        problems=tuple(problems),
        included_lines=tuple(included_lines),
    )


def _role_label(role: MaterialRole) -> str:
    return {
        MaterialRole.CALCINATION_FEED: "原料",
        MaterialRole.CALCINED_PRODUCT: "煅后料",
        MaterialRole.UNDERBURN_RECOVERED: "欠烧煅料",
        MaterialRole.CARBON_DUST: "碳粉尘",
        MaterialRole.BAKING_FILLER: "填充料",
        MaterialRole.GREEN_BAKING_PRODUCT: "待焙烧/炭化品",
        MaterialRole.BAKED_PRODUCT: "焙烧/炭化产品",
        MaterialRole.BAKING_BYPRODUCT: "粉尘/碎屑/副产品",
        MaterialRole.GRAPHITIZATION_PACKING: "保温料/电阻料",
        MaterialRole.GREEN_GRAPHITIZATION_PRODUCT: "待石墨化品",
        MaterialRole.GRAPHITIZED_PRODUCT: "石墨化产品",
        MaterialRole.GRAPHITIZATION_BYPRODUCT: "粉尘/碎屑/残块/副产品",
    }[role]


__all__ = [
    "MATERIAL_NORMALIZATION_VERSION",
    "MaterialAmount",
    "MaterialDataSource",
    "MaterialInputLine",
    "MaterialNormalizationProblem",
    "MaterialRole",
    "NormalizedMaterialProcess",
    "carbon_mass",
    "normalize_material_inputs",
    "total_mass",
    "weighted_fraction",
]

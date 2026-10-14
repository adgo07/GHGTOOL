"""Local input policy for GB/T 32151.34—2024; not a public platform contract."""
from dataclasses import dataclass
from enum import Enum
import unicodedata


class InputOrigin(str, Enum):
    CATALOG = "CATALOG"
    CUSTOM = "CUSTOM"
    LEGACY_UNSPECIFIED = "LEGACY_UNSPECIFIED"


# Stable values shared with ParameterSourceKind and the UI. USER_DEFINED is
# intentionally absent: it is a legacy read value, never a new source choice.
STANDARD_DEFAULT = "STANDARD_DEFAULT"
CALCULATED = "CALCULATED"
MEASURED = "MEASURED"


@dataclass(frozen=True, slots=True)
class CarbonateFactorIdentity:
    """Canonical identity binding for one registered C.2 carbonate species."""

    label: str
    subject_id: str
    parameter_id: str
    aliases: tuple[str, ...] = ()


# Identity only. These 11 tuples mirror the C.2 entries and their registered
# subject names/aliases in data-source/carbon_accounting/catalog.json; factor
# values and source metadata always come from the repository and Resolver.
CARBONATE_C2_IDENTITIES = (
    CarbonateFactorIdentity("CaCO3", "carbonate_caco3", "car-par-c2-caco3"),
    CarbonateFactorIdentity("MgCO3", "carbonate_mgco3", "car-par-c2-mgco3"),
    CarbonateFactorIdentity("Na2CO3", "carbonate_na2co3", "car-par-c2-na2co3"),
    CarbonateFactorIdentity("NaHCO3", "carbonate_nahco3", "car-par-c2-nahco3"),
    CarbonateFactorIdentity("FeCO3", "carbonate_feco3", "car-par-c2-feco3"),
    CarbonateFactorIdentity("MnCO3", "carbonate_mnco3", "car-par-c2-mnco3"),
    CarbonateFactorIdentity("BaCO3", "carbonate_baco3", "car-par-c2-baco3"),
    CarbonateFactorIdentity("Li2CO3", "carbonate_li2co3", "car-par-c2-li2co3"),
    CarbonateFactorIdentity("K2CO3", "carbonate_k2co3", "car-par-c2-k2co3"),
    CarbonateFactorIdentity("SrCO3", "carbonate_srco3", "car-par-c2-srco3"),
    CarbonateFactorIdentity("CaMg(CO3)2", "carbonate_camgco3_2", "car-par-c2-camgco3-2"),
)


def carbonate_c2_identity(value: str | None) -> CarbonateFactorIdentity | None:
    """Match only an exact registered C.2 label/alias after NFKC normalization."""
    if not isinstance(value, str) or not value.strip():
        return None
    target = unicodedata.normalize("NFKC", value).strip().casefold()
    matches = tuple(
        item for item in CARBONATE_C2_IDENTITIES
        if target in {
            unicodedata.normalize("NFKC", name).strip().casefold()
            for name in (item.label, *item.aliases)
        }
    )
    return matches[0] if len(matches) == 1 else None


@dataclass(frozen=True, slots=True)
class ParameterSourcePolicy:
    field_id: str
    allowed_sources: tuple[str, ...]
    default_source: str | None
    default_locked: bool
    binding_required: bool
    context: str
    basis: str | None
    short_label: str
    resolver_bound: bool


_SOURCE_POLICY_FIELDS = {
    "fuel.direct_carbon",
    "fuel.lhv",
    "fuel.fch",
    "fuel.oxidation",
    "material.fixed_carbon",
    "material.volatile_matter",
    "fgd.ratio",
    "fgd.factor",
    "fgd.conversion",
}


def parameter_source_policy(
    field_id: str,
    *,
    origin: InputOrigin | str | None = None,
    has_resolver_binding: bool = False,
    carbonate_component_count: int = 1,
    input_basis: str | None = None,
) -> ParameterSourcePolicy:
    """Return the approved per-field source choices, defaults, and binding scope.

    ``has_resolver_binding`` means the exact applicable subject/parameter binding
    (or, for FGD I/TR only, the general standard parameter binding) was found.
    It must not be inferred from a non-empty source ID.
    """
    if field_id not in _SOURCE_POLICY_FIELDS:
        raise ValueError(f"unknown carbon-material source-policy field: {field_id}")
    origin_value = origin.value if isinstance(origin, InputOrigin) else origin
    if origin_value is None:
        origin_value = InputOrigin.LEGACY_UNSPECIFIED.value
    if origin_value not in {item.value for item in InputOrigin}:
        raise ValueError(f"unknown input origin: {origin_value}")
    if carbonate_component_count < 1:
        raise ValueError("carbonate_component_count must be at least one")
    bound = bool(has_resolver_binding)

    if field_id == "fuel.direct_carbon":
        allowed, default, locked, binding, context, basis, label = (
            (MEASURED,), MEASURED, False, False, origin_value, "DIRECT", "直接含碳量",
        )
    elif field_id == "fuel.lhv":
        catalog = origin_value == InputOrigin.CATALOG.value
        allowed = ((STANDARD_DEFAULT, CALCULATED, MEASURED) if catalog and bound
                   else (CALCULATED, MEASURED))
        default = STANDARD_DEFAULT if catalog and bound else None
        locked = default == STANDARD_DEFAULT
        binding = catalog
        context, basis, label = origin_value, "HEAT_CONTENT", "低位发热量"
    elif field_id == "fuel.fch":
        catalog = origin_value == InputOrigin.CATALOG.value
        if origin_value == InputOrigin.LEGACY_UNSPECIFIED.value:
            allowed, default = (), None
        elif catalog and bound:
            allowed, default = (STANDARD_DEFAULT, CALCULATED, MEASURED), STANDARD_DEFAULT
        elif catalog:
            allowed, default = (CALCULATED, MEASURED), None
        else:
            allowed, default = (CALCULATED, MEASURED), None
        locked = default == STANDARD_DEFAULT
        binding = catalog
        context, basis, label = origin_value, "HEAT_CONTENT", "单位热值含碳量 FCh"
    elif field_id == "fuel.oxidation":
        catalog = origin_value == InputOrigin.CATALOG.value
        allowed = ((STANDARD_DEFAULT, MEASURED) if catalog and bound else (MEASURED,))
        default = STANDARD_DEFAULT if catalog and bound else MEASURED
        locked = default == STANDARD_DEFAULT
        binding = catalog
        context, basis, label = origin_value, None, "碳氧化率 FOx"
    elif field_id in {"material.fixed_carbon", "material.volatile_matter"}:
        allowed, default, locked, binding = (MEASURED,), MEASURED, False, False
        context = "APPENDIX_B_MEASURED_SOURCE"
        basis = input_basis
        label = "固定碳含量" if field_id.endswith("fixed_carbon") else "挥发分含量"
    elif field_id == "fgd.ratio":
        single_component = carbonate_component_count == 1
        allowed = ((STANDARD_DEFAULT, MEASURED) if single_component and bound else (MEASURED,))
        default = STANDARD_DEFAULT if single_component and bound else MEASURED
        locked = default == STANDARD_DEFAULT
        binding = single_component
        context = "SINGLE_COMPONENT" if single_component else "MULTI_COMPONENT"
        basis, label = None, "碳酸盐含量 I"
    elif field_id == "fgd.factor":
        allowed = (STANDARD_DEFAULT,) if bound else (MEASURED,)
        default = STANDARD_DEFAULT if bound else None
        locked = bound
        binding = bound
        context = "EXACT_C2_MATCH" if bound else "NO_EXACT_C2_BINDING"
        basis, label = None, "碳酸盐排放因子 EF1"
    else:  # fgd.conversion: a general default, independent of C.2 species.
        allowed = (STANDARD_DEFAULT, MEASURED) if bound else (MEASURED,)
        default = STANDARD_DEFAULT if bound else MEASURED
        locked = bound
        binding = True
        context = "GENERAL_STANDARD_PARAMETER"
        basis, label = None, "脱硫转化率 TR"

    return ParameterSourcePolicy(
        field_id=field_id,
        allowed_sources=tuple(allowed),
        default_source=default,
        default_locked=locked,
        binding_required=binding,
        context=context,
        basis=basis,
        short_label=label,
        resolver_bound=bound,
    )


def validate_parameter_source_policy(
    field_id: str,
    source_kind: str | None,
    *,
    origin: InputOrigin | str | None = None,
    has_resolver_binding: bool = False,
    carbonate_component_count: int = 1,
    input_basis: str | None = None,
) -> tuple[str, str, str] | None:
    """Return a stable validation tuple when a selected source is inapplicable.

    Canonical STANDARD_SPECIFIED is a persisted catalog classification of a
    standard-selected factor. It maps to the user-facing STANDARD_DEFAULT
    choice only for eligibility; the immutable source kind is left unchanged.
    """
    if source_kind is None:
        return None
    policy = parameter_source_policy(
        field_id,
        origin=origin,
        has_resolver_binding=has_resolver_binding,
        carbonate_component_count=carbonate_component_count,
        input_basis=input_basis,
    )
    normalized = STANDARD_DEFAULT if source_kind == "STANDARD_SPECIFIED" else source_kind
    if field_id == "fuel.fch" and origin in {InputOrigin.LEGACY_UNSPECIFIED, InputOrigin.LEGACY_UNSPECIFIED.value}:
        code, message = "CAR-VAL-FUEL-IDENTITY-REQUIRED", "燃料身份尚未确认，不能按当前来源政策重新核算；请确认目录燃料或自定义燃料。"
    elif field_id.startswith("fgd.") and origin in {None, InputOrigin.LEGACY_UNSPECIFIED, InputOrigin.LEGACY_UNSPECIFIED.value}:
        code, message = "CAR-VAL-CARBONATE-IDENTITY-REQUIRED", "碳酸盐身份尚未确认，不能按当前来源政策重新核算；请确认目录种类或自定义种类。"
    elif normalized in policy.allowed_sources:
        return None
    elif normalized == STANDARD_DEFAULT and policy.binding_required and not has_resolver_binding:
        code, message = "CAR-VAL-PARAMETER-BINDING-REQUIRED", f"{policy.short_label}缺少当前适用的精确Resolver绑定，不能采用标准缺省值。"
    elif field_id == "fgd.factor":
        code, message = "CAR-VAL-CARBONATE-FACTOR-SOURCE", "碳酸盐EF1仅可采用精确匹配的C.2标准因子，或在无精确匹配时填写实测因子。"
    else:
        code, message = "CAR-VAL-PARAMETER-SOURCE-INAPPLICABLE", f"{policy.short_label}来源不适用于当前字段或身份；请按允许来源重新确认。"
    return field_id, code, message


@dataclass(frozen=True, slots=True)
class FuelInputPolicy:
    required_parameters: tuple[str, ...]
    default_parameters_allowed: bool
    fch_editable: bool


def fuel_input_policy(origin: InputOrigin, *, direct_carbon: bool, heat_activity: bool = False,
                      carbon_source_kind: str | None = None) -> FuelInputPolicy:
    required = ("carbon_content", "oxidation_rate")
    if not direct_carbon and not heat_activity:
        required = ("lower_heating_value", *required)
    explicit_fch = carbon_source_kind in {"CALCULATED", "MEASURED", "USER_DEFINED"}
    fch_editable = origin is InputOrigin.CUSTOM or (not direct_carbon and explicit_fch)
    return FuelInputPolicy(required, origin is InputOrigin.CATALOG, fch_editable)


def infer_fuel_origin(fuel_type: str | None, explicit: InputOrigin | None = None) -> InputOrigin:
    if explicit is not None:
        return explicit
    if fuel_type == "OTHER":
        return InputOrigin.CUSTOM
    if fuel_type is not None:
        return InputOrigin.CATALOG
    return InputOrigin.LEGACY_UNSPECIFIED


STEAM_KIND_LABELS = {"饱和蒸汽":"SATURATED", "过热蒸汽":"SUPERHEATED"}
SUPPORTED_STEAM_KINDS = tuple(STEAM_KIND_LABELS.values())


def catalog_defaults_allowed(origin: InputOrigin) -> bool:
    return origin is InputOrigin.CATALOG


@dataclass(frozen=True)
class FuelQuantitySpec:
    activity_unit: str
    display_unit: str
    lhv_unit: str
    direct_carbon_unit: str
    direct_carbon_name: str

FUEL_QUANTITIES = {
    "MASS": FuelQuantitySpec("t", "t", "GJ/t", "tC/t", "单位质量含碳量"),
    "VOLUME": FuelQuantitySpec("ten_thousand_Nm3", "10⁴Nm³", "GJ/10⁴Nm³", "tC/10^4Nm3", "单位体积含碳量"),
    # Read-only compatibility for previously saved projects.
    "HEAT": FuelQuantitySpec("GJ", "GJ", "GJ/GJ", "tC/GJ", "单位热量含碳量"),
}

def match_fuel_option(options, label):
    """Aliases search an existing identity; they never create catalog identities."""
    import unicodedata
    def normalize(value):
        return unicodedata.normalize("NFKC", str(value)).strip().casefold()
    target = normalize(label)
    matches = [item for item in options if target in {normalize(item.label), *(normalize(a) for a in item.aliases)}]
    return matches[0] if len(matches) == 1 else None


def fuel_path_for_unit(unit):
    import unicodedata
    normalized = unicodedata.normalize("NFKC", str(unit or "")).replace(" ", "").casefold()
    if normalized in {"t", "吨"}:
        return "MASS"
    if normalized in {"104nm3", "10^4nm3", "104m3", "10^4m3", "万立方米", "万nm3"}:
        return "VOLUME"
    return None

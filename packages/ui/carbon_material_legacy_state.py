"""Old Qt selection indices, isolated from current business input identities."""
from packages.standards.carbon_material import FuelType

_FUEL_TYPE_OPTIONS = (
    ("柴油", FuelType.DIESEL),
    ("天然气", FuelType.NATURAL_GAS),
    ("焦炉煤气", FuelType.COKE_OVEN_GAS),
    ("煤（需选择具体煤种）", FuelType.COAL),
    ("其他 / 手动输入", FuelType.OTHER),
    ("无烟煤", FuelType.ANTHRACITE),
    ("烟煤", FuelType.BITUMINOUS_COAL),
    ("褐煤", FuelType.LIGNITE),
    ("洗精煤", FuelType.CLEANED_COAL),
    ("其他洗煤", FuelType.OTHER_CLEANED_COAL),
    ("型煤", FuelType.BRIQUETTE),
    ("其他煤制品", FuelType.OTHER_COAL_PRODUCTS),
    ("焦炭", FuelType.COKE),
    ("石油焦", FuelType.PETROLEUM_COKE),
    ("原油", FuelType.CRUDE_OIL),
    ("燃料油", FuelType.FUEL_OIL),
    ("汽油", FuelType.GASOLINE),
    ("一般煤油", FuelType.KEROSENE),
    ("液化天然气", FuelType.LIQUEFIED_NATURAL_GAS),
    ("液化石油气", FuelType.LIQUEFIED_PETROLEUM_GAS),
    ("石脑油", FuelType.NAPHTHA),
    ("焦油", FuelType.TAR),
    ("粗苯", FuelType.CRUDE_BENZENE),
    ("其他石油制品", FuelType.OTHER_PETROLEUM_PRODUCTS),
    ("高炉煤气", FuelType.BLAST_FURNACE_GAS),
    ("转炉煤气", FuelType.CONVERTER_GAS),
    ("炼厂干气", FuelType.REFINERY_DRY_GAS),
    ("其他煤气", FuelType.OTHER_GAS),
)

def legacy_fuel_type(index):
    return _FUEL_TYPE_OPTIONS[index][1] if type(index) is int and 0<=index<len(_FUEL_TYPE_OPTIONS) else None

def legacy_fuel_path(index):
    values=("VOLUME","MASS","HEAT")
    return values[index] if type(index) is int and 0<=index<len(values) else None

def legacy_carbon_basis(index):
    values=("HEAT_CONTENT","DIRECT")
    return values[index] if type(index) is int and 0<=index<len(values) else None

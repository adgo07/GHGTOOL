"""Carbon-material process identity and category rules shared by input channels."""
from .carbon_material_normalization import MaterialRole

PROCESS_MATERIAL_ROLES: dict[str, tuple[tuple[str, MaterialRole], ...]] = {
    "calcination": (
        ("原料", MaterialRole.CALCINATION_FEED),
        ("煅后料", MaterialRole.CALCINED_PRODUCT),
        ("欠煅烧料", MaterialRole.UNDERBURN_RECOVERED),
        ("碳粉尘", MaterialRole.CARBON_DUST),
    ),
    "baking": (
        ("填充料", MaterialRole.BAKING_FILLER),
        ("待焙烧/炭化品", MaterialRole.GREEN_BAKING_PRODUCT),
        ("焙烧/炭化产品", MaterialRole.BAKED_PRODUCT),
        # Keep the former combined category at its persisted index for saved
        # project form state; new default rows use the three V4 subcategories.
        ("粉尘/碎屑/副产品", MaterialRole.BAKING_BYPRODUCT),
        ("待焙烧（炭化）品", MaterialRole.GREEN_BAKING_PRODUCT),
        ("焙烧（炭化）品", MaterialRole.BAKED_PRODUCT),
        ("粉尘", MaterialRole.BAKING_BYPRODUCT),
        ("碎屑", MaterialRole.BAKING_BYPRODUCT),
        ("副产品", MaterialRole.BAKING_BYPRODUCT),
    ),
    "graphitization": (
        ("保温料/电阻料", MaterialRole.GRAPHITIZATION_PACKING),
        ("待石墨化品", MaterialRole.GREEN_GRAPHITIZATION_PRODUCT),
        ("石墨化产品", MaterialRole.GRAPHITIZED_PRODUCT),
        # Keep the former combined category at its persisted index for saved
        # project form state; new default rows use the four V4 subcategories.
        ("粉尘/碎屑/残块/副产品", MaterialRole.GRAPHITIZATION_BYPRODUCT),
        ("保温料", MaterialRole.GRAPHITIZATION_PACKING),
        ("电阻料", MaterialRole.GRAPHITIZATION_PACKING),
        ("石墨化品", MaterialRole.GRAPHITIZED_PRODUCT),
        ("粉尘", MaterialRole.GRAPHITIZATION_BYPRODUCT),
        ("碎屑", MaterialRole.GRAPHITIZATION_BYPRODUCT),
        ("残块", MaterialRole.GRAPHITIZATION_BYPRODUCT),
        ("副产品", MaterialRole.GRAPHITIZATION_BYPRODUCT),
    ),
}
PROCESS_MATERIAL_DEFAULT_CATEGORY_INDICES = {
    "calcination": (0, 1, 2, 3),
    "baking": (0, 4, 5, 6, 7, 8),
    "graphitization": (4, 5, 1, 6, 7, 8, 9, 10),
}
PROCESS_MATERIAL_DEFAULT_ROLE = {
    "calcination": MaterialRole.CALCINATION_FEED,
    "baking": MaterialRole.GREEN_BAKING_PRODUCT,
    "graphitization": MaterialRole.GREEN_GRAPHITIZATION_PRODUCT,
}


def _normalize(value):
    import unicodedata
    return "".join(unicodedata.normalize("NFKC",str(value or "")).split())

_EXCEL_ALIASES = {
    "calcination": {"待煅烧原料": MaterialRole.CALCINATION_FEED,"欠烧煅料":MaterialRole.UNDERBURN_RECOVERED,"炭粉尘":MaterialRole.CARBON_DUST},
    "baking": {"待焙烧(炭化)品":MaterialRole.GREEN_BAKING_PRODUCT,"焙烧(炭化)品":MaterialRole.BAKED_PRODUCT,"粉尘、碎屑、副产品等":MaterialRole.BAKING_BYPRODUCT},
    "graphitization": {"保温料和电阻料":MaterialRole.GRAPHITIZATION_PACKING,"粉尘、碎屑、残块(渣)、副产品等":MaterialRole.GRAPHITIZATION_BYPRODUCT},
}
_GROUPS = {
    "B.3": {"进入煅烧炉的碳":("fixed",(MaterialRole.CALCINATION_FEED,)),"进入煅烧炉的挥发分":("volatile",(MaterialRole.CALCINATION_FEED,)),"输出煅烧炉的碳":("fixed",(MaterialRole.CALCINED_PRODUCT,MaterialRole.UNDERBURN_RECOVERED,MaterialRole.CARBON_DUST)),"输出煅烧炉的挥发分":("volatile",(MaterialRole.CALCINED_PRODUCT,))},
    "B.4": {"进入焙烧(炭化)的碳a":("fixed",(MaterialRole.BAKING_FILLER,MaterialRole.GREEN_BAKING_PRODUCT)),"进入焙烧(炭化)的挥发分":("volatile",(MaterialRole.BAKING_FILLER,MaterialRole.GREEN_BAKING_PRODUCT)),"输出焙烧(炭化)炉的碳":("fixed",(MaterialRole.BAKING_BYPRODUCT,MaterialRole.BAKED_PRODUCT))},
    "B.5": {"进入石墨化炉的碳":("fixed",(MaterialRole.GRAPHITIZATION_PACKING,MaterialRole.GREEN_GRAPHITIZATION_PRODUCT)),"进入石墨化炉的挥发分":("volatile",(MaterialRole.GRAPHITIZATION_PACKING,)),"输出石墨化炉的碳":("fixed",(MaterialRole.GRAPHITIZATION_BYPRODUCT,MaterialRole.GRAPHITIZED_PRODUCT))},
}


def process_role_component(sheet, group, category):
    prefix={"B.3":"calcination","B.4":"baking","B.5":"graphitization"}[sheet]
    categories={_normalize(label):role for label,role in PROCESS_MATERIAL_ROLES[prefix]}
    categories.update({_normalize(label):role for label,role in _EXCEL_ALIASES[prefix].items()})
    role=categories.get(_normalize(category))
    group_info={_normalize(label):item for label,item in _GROUPS[sheet].items()}.get(_normalize(group))
    if group_info is None or role not in group_info[1]:
        return None
    return role,group_info[0]

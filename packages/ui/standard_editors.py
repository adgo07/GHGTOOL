"""UI composition for registered standard editors; domain stays Qt-free."""
def _carbon_material_editor(runtime, standard_id, **kwargs):
    from .carbon_material_page import CarbonMaterialAccountingPage
    calculator, formal, _preview = runtime.services(standard_id)
    return CarbonMaterialAccountingPage(calculator=calculator, calculation_use_case=formal, standard_id=standard_id, **kwargs)

STANDARD_EDITORS = {"carbon_material": _carbon_material_editor}

def create_standard_editor(runtime, standard_id, **kwargs):
    implementation = runtime.registry.require(standard_id)
    factory = STANDARD_EDITORS.get(implementation.editor_key)
    if factory is None:
        raise ValueError("所选标准尚未配置核算界面。")
    return factory(runtime, standard_id, **kwargs)

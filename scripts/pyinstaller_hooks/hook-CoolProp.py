"""固定CoolProp Windows wheel：保留实际delvewheel DLL，不收开发/绘图库。"""
from PyInstaller.utils.hooks import collect_delvewheel_libs_directory

datas, binaries = collect_delvewheel_libs_directory("CoolProp", datas=[], binaries=[])
# These optional developer utilities are never used by the explicit IF97 provider.
excludedimports = ["CoolProp.tests", "CoolProp.Plots", "CoolProp.GUI", "CoolProp.BibtexParser"]

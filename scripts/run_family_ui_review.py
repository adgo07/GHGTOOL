"""Launch/capture this UI candidate with an explicit isolated data directory.

Desktop use is reserved for the coordinator's serial acceptance session.
"""
import argparse
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir',required=True,type=Path)
    parser.add_argument('--capture-dir',type=Path)
    parser.add_argument('--only-home',action='store_true')
    args=parser.parse_args()
    root=args.data_dir.resolve(); root.mkdir(parents=True,exist_ok=True)
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QFontDatabase
    from apps.carbon_accounting_desktop.app import create_main_window
    from apps.carbon_accounting_desktop.config import AppConfig
    from packages.application.project_workspaces import ProjectWorkspaceService
    from packages.persistence import build_catalog_database, SQLiteRecordRepository, SQLiteProjectWorkspaceRepository, SQLiteSettingsRepository
    from packages.reference_data import DEFAULT_SOURCE_PATH
    from packages.ui.export_location import ExportLocationService
    from packages.ui.view_models import AppRoute
    app=QApplication([])
    if app.platformName()=='offscreen':
        for name in ('msyh.ttc','msyhbd.ttc','seguisym.ttf'):
            assert QFontDatabase.addApplicationFont(str(Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts'/name))>=0
    catalog=root/'catalog.sqlite'
    if not catalog.exists(): build_catalog_database(DEFAULT_SOURCE_PATH,catalog)
    config=AppConfig(catalog_database=catalog,records_database=root/'records.sqlite',projects_database=root/'projects.sqlite',user_database=root/'user.sqlite',log_directory=root/'logs')
    records=SQLiteRecordRepository(config.records_database)
    # Clearly synthetic review fixture, only in this explicit QA data directory.
    qpa = os.environ.get("QT_QPA_PLATFORM")
    from tests.test_g07_records import _record
    if qpa is None: os.environ.pop("QT_QPA_PLATFORM", None)
    else: os.environ["QT_QPA_PLATFORM"] = qpa
    if records.get('record.family-ui-review') is None: records.create(_record('record.family-ui-review',warning=True))
    window=create_main_window(config,record_repository=records,
        project_service=ProjectWorkspaceService(SQLiteProjectWorkspaceRepository(config.projects_database)),
        export_location_service=ExportLocationService(SQLiteSettingsRepository(config.user_database)))
    window.show()
    if args.capture_dir:
        target=args.capture_dir.resolve(); target.mkdir(parents=True,exist_ok=False)
        for _ in range(3): app.processEvents()
        window.resize(1280,800)
        shell=window.centralWidget()
        scenes=[(AppRoute.HOME,'home'),(AppRoute.STANDARDS,'standards'),(AppRoute.NEW_ACCOUNTING,'new-accounting'),(AppRoute.RECORDS,'record-detail')]
        summary=[]
        for route,name in scenes[:1] if args.only_home else scenes:
            shell.navigate(route)
            if route is AppRoute.RECORDS: shell.pages[route].open_record('record.family-ui-review')
            for _ in range(4): app.processEvents()
            pixmap=window.grab(); assert pixmap.save(str(target/(name+'.png')))
            summary.append({'scene':name,'client':[window.width(),window.height()],'dpr':window.devicePixelRatioF(),'pixels':[pixmap.width(),pixmap.height()]})
        (target/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
        window.hide()
        return 0
    return app.exec()

if __name__=='__main__': raise SystemExit(main())

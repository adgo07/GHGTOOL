"""Shared visual tokens for the Windows desktop shell."""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path


_COMBOBOX_ARROW = Path(files("resources").joinpath("icons", "chevron-down.svg")).as_posix()

SIDEBAR_WIDTH = 242
BRAND_AREA_HEIGHT = 111
NAV_ITEM_HEIGHT = 46
NAV_ITEM_RADIUS = 9
MAIN_CONTENT_MAX_WIDTH = 1440
HOME_CONTENT_MAX_WIDTH = 1480
HOME_PAGE_SIDE_MARGIN = 54
COMPACT_HOME_PAGE_SIDE_MARGIN = 30
HOME_CANVAS_GRADIENT = (
    "qlineargradient(x1:0, y1:0, x2:0, y2:1, "
    "stop:0 #eaf5fd, stop:0.289 #f4f9fd, stop:0.456 #f5f8fb, stop:1 #f5f8fb)"
)
COMPACT_PAGE_MARGIN = 22
WIDE_PAGE_MARGIN = 48

SIDEBAR_BACKGROUND = (
    "qlineargradient(x1:0, y1:0, x2:0, y2:1, "
    "stop:0 #E6F2FC, stop:0.48 #EDF6FD, stop:1 #E6F2FB)"
)
PRIMARY_BRAND = "#197CC2"
SIDEBAR_ICON_ACTIVE = PRIMARY_BRAND
SIDEBAR_ICON_INACTIVE = "#516F86"
PAGE_BACKGROUND = "#F5F8FC"
CARD_BACKGROUND = "#FFFFFF"
PRIMARY_TEXT = "#213A4F"
SECONDARY_TEXT = "#526A7D"
BORDER = "#DAE7F1"
CARD_BORDER = "#DAE7F1"
SURFACE_MUTED = "#F7FAFD"
DISABLED_TEXT = "#8798A6"
STATUS_CURRENT = "#168268"
STATUS_UPCOMING = "#956420"
STATUS_ABOLISHED = "#B9484A"
STATUS_UNKNOWN = SECONDARY_TEXT


# 核算页面专用；保持现有色值，不影响全局样式或其他页面。
ACCOUNTING_COLORS = {'choice_selected_text': '#075985',
 'source_active_text': '#075D88',
 'directory_selected_text': '#096C9F',
 'source_hover_border': '#126DAA',
 'radio_selected': '#147BB5',
 'brand': '#197CC2',
 'primary_text': '#213A4F',
 'radio_text': '#344E61',
 'inactive_text': '#425F74',
 'choice_text': '#486A80',
 'single_choice_text': '#526A7A',
 'state_text': '#597187',
 'switch_border': '#71869A',
 'pending_text': '#80520A',
 'pending_glyph': '#805213',
 'choice_notice': '#92651A',
 'radio_notice': '#936026',
 'radio_border': '#93A8B6',
 'choice_disabled_text': '#9AA9B3',
 'radio_disabled_text': '#9BA8B0',
 'pending_border': '#A46A11',
 'switch_inactive': '#B8C8D4',
 'choice_border': '#C8DCEB',
 'radio_selected_border': '#CEE5F3',
 'directory_border': '#DCE8F1',
 'source_selected': '#DDEEF9',
 'source_active_surface': '#E6F4FB',
 'source_inactive_hover': '#E7EDF2',
 'choice_disabled_surface': '#F3F6F8',
 'switch_surface': '#F3F6F9',
 'directory_surface': '#F3F8FC',
 'pending_indicator': '#F8E3B5',
 'pending_hover': '#FCEBC1',
 'pending_surface': '#FFF4DA',
 'white': '#FFFFFF'}


def responsive_page_margin(viewport_width: int) -> int:
    """Match the V4 page padding clamp in CSS viewport units."""

    return min(48, max(22, round(viewport_width * 0.034)))


def application_stylesheet() -> str:
    """Single source for shared desktop dimensions and interaction states.

    QSS heights are content boxes: 36 + two 2-DIP borders = 40 DIP.
    """
    return f"""
        QWidget {{ font-family:"Microsoft YaHei UI", "Microsoft YaHei", sans-serif; color:#213A4F; font-size:14px; }}
        QFrame#mainContent, QScrollArea#mainScrollArea {{ background:#F5F8FC; }}
        QScrollArea#mainScrollArea {{ border:none; }}
        QFrame#card, QFrame#settingsSurface, QFrame#standardRequirementCard {{ background:#FFFFFF; border:1px solid #DAE7F1; border-radius:10px; }}
        QLabel#pageTitle {{ color:#18364F; font-size:24px; font-weight:600; }}
        QLabel#cardTitle, QLabel#sectionTitle {{ color:#18364F; font-size:16px; font-weight:600; }}
        QLabel#pageDescription, QLabel#secondaryText, QLabel#emptyStateDescription,
        QLabel#detailFieldLabel, QLabel#fieldUnitHint {{ color:#526A7D; font-size:13px; }}
        QLabel#detailFieldValue, QLabel#bodyText {{ color:#213A4F; font-size:14px; }}
        QLabel#emptyStateTitle {{ font-size:16px; font-weight:600; }}
        QLabel#standardDetailNumber {{ color:#116FAE; font-size:14px; font-weight:600; }}
        QLabel#standardDetailName, QLabel#parameterDetailName {{ color:#18364F; font-size:20px; font-weight:600; }}
        QScrollBar:vertical {{ width:10px; margin:0; background:transparent; }}
        QScrollBar::handle:vertical {{ min-height:26px; border-radius:5px; background:#C7D7E2; }}
        QScrollBar::handle:vertical:hover {{ background:#A9C1D1; }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height:0; }}
        QScrollBar:horizontal {{ height:10px; margin:0; background:transparent; }}
        QScrollBar::handle:horizontal {{ min-width:26px; border-radius:5px; background:#C7D7E2; }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width:0; }}
        QPushButton[sourceState] {{ min-height:62px; padding:10px 12px; border-radius:10px; text-align:left; font-size:13px; font-weight:600; }}
        QPushButton[sourceState="已启用"], QPushButton[sourceState="部分启用"] {{ border-color:#9DCCE8; background:#ECF7FF; color:#155C88; }}
        QTableWidget {{ background:#FFFFFF; border:1px solid #DAE7F1; border-radius:10px; gridline-color:#EDF2F6; selection-color:#213A4F; font-size:14px; selection-background-color:#D6EBF9; }}
        QTableWidget QHeaderView::section {{ background:#F7FAFD; border:none; border-bottom:1px solid #DAE7F1; font-size:13px; font-weight:600; padding:8px 10px; color:#526A7D; }}
        QTabWidget::pane {{ border:1px solid #DAE7F1; border-radius:10px; background:#FFFFFF; }}
        QCheckBox, QRadioButton {{ font-size:14px; spacing:8px; }}
        QCheckBox:disabled, QRadioButton:disabled {{ color:#8798A6; }}
        QToolButton {{ font-size:13px; }}
        QFrame[businessSurface="true"] {{ background:#FFFFFF; border:1px solid #DAE7F1; border-radius:10px; }}
        QLineEdit, QComboBox, QAbstractSpinBox {{
            min-height:36px; max-height:36px; padding:0 10px;
            border:2px solid #DAE7F1; border-radius:6px; background:#FFFFFF; color:#213A4F; font-size:14px;
            selection-background-color:#D6EBF9;
        }}
        QComboBox {{ padding-right:30px; }}
        QComboBox::drop-down {{ subcontrol-origin:padding; subcontrol-position:right center; width:26px; border:none; }}
        QComboBox::down-arrow {{ image:url("{_COMBOBOX_ARROW}"); width:12px; height:12px; }}
        QComboBox QLineEdit, QAbstractSpinBox QLineEdit {{ min-height:0; max-height:16777215px; padding:0; border:none; background:transparent; }}
        QTextEdit, QPlainTextEdit {{ padding:8px 10px; border:2px solid #DAE7F1; border-radius:6px; background:#FFFFFF; font-size:14px; }}
        QLineEdit:hover, QComboBox:hover, QAbstractSpinBox:hover {{ border-color:#A9CDE5; }}
        QLineEdit:focus, QComboBox:focus, QAbstractSpinBox:focus, QTextEdit:focus, QPlainTextEdit:focus {{ border-color:#197CC2; }}
        QLineEdit[readOnly="true"] {{ background:#F7FAFD; color:#213A4F; }}
        QLineEdit:disabled, QComboBox:disabled, QAbstractSpinBox:disabled, QTextEdit:disabled, QPlainTextEdit:disabled {{ background:#F3F5F7; color:#8798A6; border-color:#DAE7F1; }}
        QPushButton {{ min-height:36px; padding:0 14px; border:2px solid #DAE7F1; border-radius:6px; background:#FFFFFF; color:#213A4F; font-size:14px; font-weight:400; }}
        QPushButton:hover {{ background:#EDF6FD; border-color:#A9CDE5; }}
        QPushButton:pressed {{ background:#D6EBF9; }}
        QPushButton[visualRole="primary"], QPushButton#primaryButton, QPushButton#exportWordReportButton, QPushButton#startAccountingButton, QPushButton#calculateAccountingButton, QPushButton#saveAccountingProjectButton {{ background:#116FAE; border-color:#116FAE; color:#FFFFFF; font-weight:600; }}
        QPushButton[visualRole="primary"]:hover, QPushButton#primaryButton:hover, QPushButton#exportWordReportButton:hover, QPushButton#startAccountingButton:hover, QPushButton#calculateAccountingButton:hover, QPushButton#saveAccountingProjectButton:hover {{ background:#0D6097; border-color:#0D6097; }}
        QPushButton[visualRole="primary"]:pressed, QPushButton#primaryButton:pressed, QPushButton#exportWordReportButton:pressed, QPushButton#startAccountingButton:pressed, QPushButton#calculateAccountingButton:pressed, QPushButton#saveAccountingProjectButton:pressed {{ background:#0A527F; border-color:#0A527F; }}
        QPushButton[visualRole="danger"], QPushButton#deleteRecordButton, QPushButton#deleteAccountingProjectButton, QPushButton#deleteAccountingUnitButton {{ color:#B9484A; }}
        QPushButton[visualRole="danger"]:hover, QPushButton#deleteRecordButton:hover, QPushButton#deleteAccountingProjectButton:hover, QPushButton#deleteAccountingUnitButton:hover {{ background:#FFF1F1; border-color:#B9484A; }}
        QPushButton[visualRole="light"], QPushButton#openRecordRowButton {{ min-height:24px; padding:0 6px; background:transparent; border-color:transparent; color:#116FAE; font-size:13px; }}
        QPushButton[visualRole="light"]:hover, QPushButton#openRecordRowButton:hover {{ background:#EDF6FD; }}
        QPushButton:focus, QPushButton[visualRole="primary"]:focus, QPushButton#primaryButton:focus, QPushButton#exportWordReportButton:focus, QPushButton#startAccountingButton:focus, QPushButton#calculateAccountingButton:focus, QPushButton#saveAccountingProjectButton:focus, QPushButton[visualRole="danger"]:focus, QPushButton#deleteRecordButton:focus, QPushButton#deleteAccountingProjectButton:focus, QPushButton#deleteAccountingUnitButton:focus, QPushButton#openRecordRowButton:focus {{ border-color:#197CC2; }}
        QPushButton:disabled, QPushButton[visualRole="primary"]:disabled, QPushButton#primaryButton:disabled, QPushButton#exportWordReportButton:disabled, QPushButton#startAccountingButton:disabled, QPushButton#calculateAccountingButton:disabled, QPushButton#saveAccountingProjectButton:disabled, QPushButton[visualRole="danger"]:disabled, QPushButton#deleteRecordButton:disabled, QPushButton#deleteAccountingProjectButton:disabled, QPushButton#deleteAccountingUnitButton:disabled, QPushButton[busy="true"] {{ background:#F3F5F7; color:#8798A6; border-color:#DAE7F1; }}
        QTabBar::tab {{ min-height:33px; max-height:33px; padding:0 16px; border:0; border-bottom:3px solid transparent; font-size:13px; font-weight:600; color:#526A7D; }}
        QTabBar::tab:selected {{ color:#116FAE; border-bottom:2px solid #197CC2; padding-bottom:1px; }}
        QTabBar::tab:hover {{ background:#EDF6FD; }}
        QTableWidget::item {{ padding:8px 10px; }}
        QLabel#recordFrozenTotal {{ font-size:26px; font-weight:600; }}
        QLabel#recordFrozenIdentity, QLabel#recordResultCount, QLabel#exportDirectoryStatus {{ font-size:13px; color:#526A7D; }}
        QLabel#recordDetailHeading {{ font-size:16px; font-weight:600; }}
        QLabel#recordStatusBadge {{ border-radius:5px; padding:4px 7px; font-size:12px; background:#E7F6F0; color:#168268; }}
        QLabel#recordStatusBadge[warning="true"] {{ background:#FFF5E1; color:#956420; }}
        QLabel#detailParagraph {{ font-size:14px; }}
        QLabel#savedImportContext {{ padding:8px; background:#F7FAFD; border-radius:6px; }}

    """


def message_button_stylesheet() -> str:
    return "QMessageBox QPushButton { min-height:36px; padding:0 14px; border:2px solid #DAE7F1; border-radius:6px; font-size:14px; } QMessageBox QPushButton:focus { border-color:#197CC2; }"


def accounting_sample_stylesheet() -> str:
    """Only structural accounting styles; shared controls inherit the application theme."""
    return "QFrame#projectUnitControlsCard { background:white; border:1px solid #DAE7F1; border-radius:10px; } QPushButton#projectUnitControlsToggle { text-align:left; font-weight:600; }"

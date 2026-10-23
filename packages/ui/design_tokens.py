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
SECONDARY_TEXT = "#698198"
BORDER = "#DAE7F1"
CARD_BORDER = "#DAE7F1"
SURFACE_MUTED = "#F7FAFD"
DISABLED_TEXT = "#8798A6"
STATUS_CURRENT = "#168268"
STATUS_UPCOMING = "#956420"
STATUS_ABOLISHED = "#B9484A"
STATUS_UNKNOWN = SECONDARY_TEXT


def responsive_page_margin(viewport_width: int) -> int:
    """Match the V4 page padding clamp in CSS viewport units."""

    return min(48, max(22, round(viewport_width * 0.034)))


def application_stylesheet() -> str:
    """Return the single stylesheet shared by the desktop shell and pages."""

    return f"""
        QWidget {{
            font-family: "Microsoft YaHei UI", "Microsoft YaHei", sans-serif;
            color: {PRIMARY_TEXT};
        }}
        QFrame#sidebar {{ background: {SIDEBAR_BACKGROUND}; }}
        QFrame#mainContent, QScrollArea#mainScrollArea {{ background: {PAGE_BACKGROUND}; }}
        QScrollArea#mainScrollArea {{ border: none; }}
        QLabel#brandLogo, QLabel#sidebarProductName {{ background: transparent; }}
        QLabel#sidebarProductName {{ color: #537891; font-size: 11px; font-weight: 650; }}
        QPushButton#navButton {{
            background: transparent; border: none; border-radius: {NAV_ITEM_RADIUS}px;
            color: #516F86; font-size: 13px; font-weight: 600;
            padding: 0 13px; text-align: left;
        }}
        QPushButton#navButton:hover {{ background: rgba(255, 255, 255, 0.78); color: #0F6DA7; }}
        QPushButton#navButton:checked {{
            background: #D6EBF9; border-left: 3px solid #298CCB;
            color: #116FAE; font-weight: 700; padding-left: 10px;
        }}
        QPushButton#navButton[reserved="true"] {{ color: #91A3B2; }}
        QPushButton#navButton[reserved="true"]:hover {{ background: rgba(255, 255, 255, 0.45); color: #91A3B2; }}
        QPushButton#navButton[reserved="true"]:checked {{ color: #698198; }}
        QPushButton#primaryButton, QPushButton#secondaryButton, QPushButton#reservedButton {{
            min-height: 36px; border-radius: 6px; padding: 0 16px; font-size: 14px;
        }}
        QPushButton#primaryButton {{ min-height: 40px; background: {PRIMARY_BRAND}; border: 1px solid {PRIMARY_BRAND}; color: #FFFFFF; font-weight: 600; }}
        QPushButton#primaryButton:hover {{ background: #076C9F; border-color: #076C9F; }}
        QPushButton#secondaryButton {{ background: #FFFFFF; border: 1px solid {BORDER}; color: {PRIMARY_TEXT}; }}
        QPushButton#secondaryButton:hover {{ background: #F8FAFC; border-color: {PRIMARY_BRAND}; }}
        QPushButton#reservedButton {{ background: #F8FAFC; border: 1px dashed {BORDER}; color: {SECONDARY_TEXT}; }}
        QPushButton#reservedButton:hover {{ background: #F8FAFC; border-color: {BORDER}; color: {SECONDARY_TEXT}; }}
        QFrame#card {{ background: {CARD_BACKGROUND}; border: 1px solid {CARD_BORDER}; border-radius: 14px; }}
        QFrame#settingsSurface, QFrame#standardRequirementCard {{
            background: #F7FBFE; border: 1px solid #E4EEF5; border-radius: 10px;
        }}
        QLineEdit, QComboBox, QDateEdit, QDateTimeEdit, QSpinBox, QDoubleSpinBox,
        QTextEdit, QPlainTextEdit {{
            min-height: 38px; border: 1px solid #D6E4EE; border-radius: 8px;
            padding: 8px 11px; background: #FFFFFF; color: #213A4F; font-size: 13px;
            selection-background-color: #DCEFFC;
        }}
        QLineEdit:hover, QComboBox:hover, QDateEdit:hover, QDateTimeEdit:hover,
        QSpinBox:hover, QDoubleSpinBox:hover, QTextEdit:hover, QPlainTextEdit:hover {{
            border-color: #A9CDE5;
        }}
        QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QDateTimeEdit:focus,
        QSpinBox:focus, QDoubleSpinBox:focus, QTextEdit:focus, QPlainTextEdit:focus {{
            border: 1px solid #4A9FD5; background: #FFFFFF;
        }}
        QComboBox {{ padding-right: 30px; }}
        QComboBox::drop-down {{
            subcontrol-origin: padding; subcontrol-position: right center;
            width: 28px; border-left: 1px solid #E5EDF3;
            border-top-right-radius: 8px; border-bottom-right-radius: 8px;
            background: #F8FBFD;
        }}
        QComboBox::down-arrow {{
            image: url("{_COMBOBOX_ARROW}"); width: 12px; height: 12px;
        }}
        QPushButton {{
            min-height: 37px; border: 1px solid #D4E4F0; border-radius: 8px;
            padding: 8px 13px; background: #FFFFFF; color: #3C617B;
            font-size: 12px; font-weight: 700;
        }}
        QPushButton:hover {{ background: #F3F9FE; border-color: #8CBDDD; }}
        QPushButton:focus {{ border: 2px solid #4A9FD5; }}
        QPushButton:disabled {{ background: #F5F7F9; border-color: #E4E7EC; color: #98A2B3; }}
        QPushButton[sourceState] {{
            min-height: 62px; border: 1px solid #DBE8F0; border-radius: 10px;
            padding: 10px 12px; background: #FFFFFF; color: #697E91;
            text-align: left; font-size: 13px; font-weight: 650;
        }}
        QPushButton[sourceState]:hover {{ border-color: #9DCBE7; background: #F7FBFE; }}
        QPushButton[sourceState="已启用"], QPushButton[sourceState="部分启用"] {{
            border-color: #9DCCE8; background: #ECF7FF; color: #155C88;
        }}
        QPushButton[sourceState="已启用"]:hover,
        QPushButton[sourceState="部分启用"]:hover {{ background: #E5F3FC; }}
        QTableWidget {{
            background: #FFFFFF; border: 1px solid #DAE7F1; border-radius: 10px;
            gridline-color: #EDF2F6; alternate-background-color: #FBFDFF;
            selection-background-color: #E8F4FB; selection-color: #213A4F;
        }}
        QTableWidget QHeaderView::section {{
            background: #F4F8FC; color: #597187; border: none;
            border-bottom: 1px solid #DAE7F1; padding: 12px 13px;
            font-size: 12px; font-weight: 700;
        }}
        QTableWidget::item {{ padding: 12px 13px; border-bottom: 1px solid #E8F0F6; }}
        QTableWidget::item:selected {{ background: #E8F4FB; color: #213A4F; }}
        QTabWidget::pane {{ border: 1px solid #DAE7F1; border-radius: 9px; background: #FFFFFF; }}
        QTabBar::tab {{
            min-height: 38px; padding: 10px 16px; border: 1px solid transparent;
            border-bottom: 2px solid transparent; color: #698198; background: transparent;
            font-size: 13px; font-weight: 600;
        }}
        QTabBar::tab:hover {{ color: #12649A; background: #F1F8FC; }}
        QTabBar::tab:selected {{ color: #12649A; border-bottom-color: #197CC2; background: #FFFFFF; }}
        QCheckBox {{ spacing: 8px; color: #425F74; font-size: 13px; }}
        QCheckBox::indicator {{ width: 17px; height: 17px; border: 1px solid #B8CBD9; border-radius: 4px; background: #FFFFFF; }}
        QCheckBox::indicator:hover {{ border-color: #4A9FD5; }}
        QCheckBox::indicator:checked {{ background: #197CC2; border-color: #197CC2; }}
        QScrollBar:vertical {{ width: 10px; margin: 3px 2px; background: transparent; }}
        QScrollBar::handle:vertical {{ min-height: 26px; border-radius: 5px; background: #C7D7E2; }}
        QScrollBar::handle:vertical:hover {{ background: #A9C1D1; }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        QScrollBar:horizontal {{ height: 10px; margin: 2px 3px; background: transparent; }}
        QScrollBar::handle:horizontal {{ min-width: 26px; border-radius: 5px; background: #C7D7E2; }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
        QLineEdit#standardSearch, QLineEdit#parameterSearch,
        QComboBox#standardStatusFilter, QComboBox#standardIndustryFilter,
        QComboBox#standardYearFilter, QComboBox#parameterViewModeFilter,
        QComboBox#parameterSubjectFilter, QComboBox#parameterSourceFilter,
        QComboBox#parameterTypeFilter, QComboBox#parameterReviewFilter,
        QComboBox#parameterYearFilter {{
            min-height: 38px; border: 1px solid {BORDER}; border-radius: 8px;
            padding: 8px 11px; background: {CARD_BACKGROUND};
        }}
        QTableWidget#catalogTable {{
            background: {CARD_BACKGROUND}; border: 1px solid {BORDER};
            gridline-color: {BORDER}; selection-background-color: #E6F4FB;
            selection-color: {PRIMARY_TEXT};
        }}
        QTableWidget#catalogTable QHeaderView::section {{
            background: {SURFACE_MUTED}; color: {SECONDARY_TEXT};
            border: none; border-bottom: 1px solid {BORDER};
            padding: 8px; font-weight: 600;
        }}
        QLabel#detailFieldLabel {{ color: {SECONDARY_TEXT}; font-size: 12px; }}
        QLabel#detailFieldValue {{ color: {PRIMARY_TEXT}; font-size: 12px; }}
        QLabel#standardDetailNumber {{ color: {PRIMARY_BRAND}; font-size: 14px; font-weight: 600; }}
        QLabel#standardDetailName, QLabel#parameterDetailName {{ color: {PRIMARY_TEXT}; font-size: 20px; font-weight: 600; }}
        QLabel#standardSummaryName {{ color: #18364F; font-size: 20px; font-weight: 700; }}
        QLabel#standardRequirementTitle {{ color: #28516E; font-size: 13px; font-weight: 700; }}
        QLabel#standardRequirementText {{ color: #5E7A90; font-size: 12px; }}
        QLabel#standardSourceNote {{ color: #637F92; font-size: 11px; }}
        QLabel#standardSupportBadge {{
            background: #F4F8FC; color: #698198; border-radius: 8px;
            padding: 3px 8px; font-size: 11px; font-weight: 650;
        }}
        QLabel#standardSupportBadge[implemented="true"] {{ background: #E7F6F0; color: #168268; }}
        QLabel#statusBadge {{
            background: {STATUS_UNKNOWN}; color: #FFFFFF; border-radius: 10px;
            padding: 3px 10px; font-size: 12px; font-weight: 600;
        }}
        QLabel#statusBadge[catalogStatus="CURRENT"] {{ background: {STATUS_CURRENT}; }}
        QLabel#statusBadge[catalogStatus="UPCOMING"] {{ background: {STATUS_UPCOMING}; }}
        QLabel#statusBadge[catalogStatus="ABOLISHED"] {{ background: {STATUS_ABOLISHED}; }}
        QPushButton#viewOfficialSourceButton, QPushButton#viewFactorSourceButton,
        QPushButton#viewFactorsButton {{
            min-height: 34px; border: 1px solid {BORDER}; border-radius: 6px;
            padding: 0 14px; color: {PRIMARY_BRAND}; background: {CARD_BACKGROUND};
        }}
        QPushButton#viewOfficialSourceButton:hover, QPushButton#viewFactorSourceButton:hover,
        QPushButton#viewFactorsButton:hover {{
            background: {SURFACE_MUTED}; border-color: {PRIMARY_BRAND};
        }}
        QPushButton#startAccountingButton {{
            min-height: 34px; border: 1px solid {PRIMARY_BRAND}; border-radius: 6px;
            padding: 0 14px; color: #FFFFFF; background: {PRIMARY_BRAND};
        }}
        QPushButton#startAccountingButton:disabled {{
            color: {DISABLED_TEXT}; background: #F2F4F7; border-color: #E4E7EC;
        }}
        QLabel#pageTitle {{ color: #18364F; font-size: 25px; font-weight: 700; }}
        QLabel#pageDescription {{ color: {SECONDARY_TEXT}; font-size: 13px; }}
        QLabel#sectionTitle {{ color: #18364F; font-size: 16px; font-weight: 700; }}
        QLabel#cardTitle {{ color: #18364F; font-size: 16px; font-weight: 700; }}
        QLabel#bodyText {{ color: {PRIMARY_TEXT}; font-size: 14px; }}
        QLabel#secondaryText, QLabel#emptyStateDescription {{ color: {SECONDARY_TEXT}; font-size: 13px; }}
        QLabel#emptyStateTitle {{ color: {PRIMARY_TEXT}; font-size: 16px; font-weight: 600; }}
        QLineEdit#reservedInput, QComboBox#reservedInput {{ min-height: 36px; border: 1px solid {BORDER}; border-radius: 6px; padding: 0 10px; background: #FFFFFF; }}
        QLineEdit#reservedInput:disabled, QComboBox#reservedInput:disabled, QPushButton#reservedControl:disabled {{ color: #98A2B3; background: #F2F4F7; border-color: #E4E7EC; }}
        QPushButton#reservedControl {{ min-height: 36px; border: 1px solid {BORDER}; border-radius: 6px; padding: 0 16px; color: {SECONDARY_TEXT}; background: #FFFFFF; }}
        QFrame#calculationStatusBar {{
            background: {SURFACE_MUTED}; border: 1px solid {BORDER}; border-radius: 8px;
        }}
        QLabel#confirmedSourceCount, QLabel#calculationErrorCount,
        QLabel#calculationReminderCount, QLabel#calculationStatusHint {{
            color: {SECONDARY_TEXT}; font-size: 13px;
        }}
        QLabel#calculationStatus {{
            color: {PRIMARY_TEXT}; font-size: 14px; font-weight: 600;
        }}
        QPushButton#calculateAccountingButton {{
            min-height: 38px; border: 1px solid {PRIMARY_BRAND}; border-radius: 6px;
            padding: 0 18px; color: #FFFFFF; background: {PRIMARY_BRAND}; font-weight: 600;
        }}
        QPushButton#calculateAccountingButton:hover {{
            background: #076C9F; border-color: #076C9F;
        }}
        QPushButton#viewBreakdownButton, QPushButton#viewProcessButton {{
            min-height: 32px; border: 1px solid {BORDER}; border-radius: 6px;
            padding: 0 12px; color: {PRIMARY_BRAND}; background: {CARD_BACKGROUND};
        }}
    """


def message_button_stylesheet() -> str:
    """Instance-only message buttons; retain native default/focus feedback."""
    return "QMessageBox QPushButton { font-size: 14px; font-weight: normal; min-height: 24px; min-width: 72px; padding: 5px 10px; }"


def accounting_sample_stylesheet() -> str:
    """PR-B sample roles, applied once by the accounting page only."""
    return f"""
        QWidget[layoutSample="true"] QLabel {{ font-size: 14px; }}
        QWidget[layoutSample="true"] QLabel#cardTitle {{ font-size: 18px; font-weight: 600; }}
        QWidget[layoutSample="true"] QLineEdit,
        QWidget[layoutSample="true"] QComboBox,
        QWidget[layoutSample="true"] QSpinBox,
        QWidget[layoutSample="true"] QDateEdit {{
            min-height: 28px; padding: 4px 8px; border: 1px solid {BORDER};
            border-radius: 6px; font-size: 14px; font-weight: normal;
        }}
        QWidget[layoutSample="true"] QComboBox QLineEdit,
        QWidget[layoutSample="true"] QAbstractSpinBox QLineEdit {{
            min-height: 0px; padding: 0px; border: none; background: transparent;
        }}
        QWidget[layoutSample="true"] QPushButton {{
            min-height: 28px; padding: 4px 12px; font-size: 14px; font-weight: normal;
        }}
        QPushButton#projectUnitControlsToggle {{
            min-height: 28px; padding: 4px 12px; text-align: left;
            font-size: 14px; font-weight: 600;
        }}
        QWidget[layoutSample="true"] QPushButton#saveAccountingProjectButton {{
            background: {PRIMARY_BRAND}; color: white; border-color: {PRIMARY_BRAND};
        }}
        QWidget[layoutSample="true"] QPushButton#deleteAccountingProjectButton,
        QWidget[layoutSample="true"] QPushButton#deleteAccountingUnitButton {{
            color: {SECONDARY_TEXT}; background: transparent;
        }}
        QFrame[dfActivityRegion="true"] QPushButton[sourceState] {{
            min-height: 54px; padding: 0px; font-weight: normal;
        }}
    """

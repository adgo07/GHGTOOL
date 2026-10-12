"""Shared visual tokens for the Windows desktop shell."""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path


_COMBOBOX_ARROW = Path(files("resources").joinpath("icons", "chevron-down.svg")).as_posix()

SIDEBAR_WIDTH = 242
BRAND_AREA_HEIGHT = 120
NAV_ITEM_HEIGHT = 44
NAV_ITEM_RADIUS = 6
MAIN_CONTENT_MAX_WIDTH = 1360
HOME_CONTENT_MAX_WIDTH = 1480
HOME_PAGE_SIDE_MARGIN = 54
COMPACT_HOME_PAGE_SIDE_MARGIN = 30
HOME_CANVAS_GRADIENT = (
    "qlineargradient(x1:0, y1:0, x2:0, y2:1, "
    "stop:0 #eaf5fd, stop:0.289 #f4f9fd, stop:0.456 #f5f8fb, stop:1 #f5f8fb)"
)
COMPACT_PAGE_MARGIN = 24
WIDE_PAGE_MARGIN = 32

SIDEBAR_BACKGROUND = "#103554"
PRIMARY_BRAND = "#087FBE"
SIDEBAR_ICON_ACTIVE = PRIMARY_BRAND
SIDEBAR_ICON_INACTIVE = "#FFFFFF"
PAGE_BACKGROUND = "#F5F7FA"
CARD_BACKGROUND = "#FFFFFF"
PRIMARY_TEXT = "#1F2937"
SECONDARY_TEXT = "#667085"
BORDER = "#D9E0E7"
CARD_BORDER = "#E2E8F0"
SURFACE_MUTED = "#F8FAFC"
DISABLED_TEXT = "#98A2B3"
STATUS_CURRENT = "#027A48"
STATUS_UPCOMING = "#B54708"
STATUS_ABOLISHED = "#B42318"
STATUS_UNKNOWN = SECONDARY_TEXT


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
        QLabel#sidebarProductName {{ color: #FFFFFF; font-size: 16px; font-weight: 600; }}
        QPushButton#navButton {{
            background: transparent; border: none; border-radius: {NAV_ITEM_RADIUS}px;
            color: rgba(255, 255, 255, 0.78); font-size: 14px; font-weight: 400;
            padding: 0 12px; text-align: left;
        }}
        QPushButton#navButton:hover {{ background: rgba(255, 255, 255, 0.08); color: rgba(255, 255, 255, 0.96); }}
        QPushButton#navButton:checked {{
            background: rgba(255, 255, 255, 0.12); border-left: 3px solid {PRIMARY_BRAND};
            color: #FFFFFF; font-weight: 600; padding-left: 9px;
        }}
        QPushButton#navButton[reserved="true"] {{ color: rgba(255, 255, 255, 0.38); }}
        QPushButton#navButton[reserved="true"]:hover {{ background: rgba(255, 255, 255, 0.05); color: rgba(255, 255, 255, 0.55); }}
        QPushButton#navButton[reserved="true"]:checked {{ color: rgba(255, 255, 255, 0.82); }}
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
        QLineEdit, QComboBox, QDateEdit, QDateTimeEdit, QSpinBox, QDoubleSpinBox,
        QTextEdit, QPlainTextEdit {{
            min-height: 36px; border: 1px solid #D6E4EE; border-radius: 8px;
            padding: 7px 10px; background: #FFFFFF; color: #213A4F;
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
            min-height: 36px; border: 1px solid #D4E4F0; border-radius: 8px;
            padding: 0 14px; background: #FFFFFF; color: #3C617B;
            font-size: 13px; font-weight: 600;
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
            border-bottom: 1px solid #DAE7F1; padding: 9px 8px;
            font-size: 12px; font-weight: 650;
        }}
        QTableWidget::item {{ padding: 7px 8px; border-bottom: 1px solid #EDF2F6; }}
        QTableWidget::item:selected {{ background: #E8F4FB; color: #213A4F; }}
        QTabWidget::pane {{ border: 1px solid #DAE7F1; border-radius: 9px; background: #FFFFFF; }}
        QTabBar::tab {{
            min-height: 36px; padding: 0 18px; border: 1px solid transparent;
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
            min-height: 36px; border: 1px solid {BORDER}; border-radius: 6px;
            padding: 0 10px; background: {CARD_BACKGROUND};
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
        QLabel#detailFieldLabel {{ color: {SECONDARY_TEXT}; font-size: 13px; }}
        QLabel#detailFieldValue {{ color: {PRIMARY_TEXT}; font-size: 13px; }}
        QLabel#standardDetailNumber {{ color: {PRIMARY_BRAND}; font-size: 14px; font-weight: 600; }}
        QLabel#standardDetailName, QLabel#parameterDetailName {{ color: {PRIMARY_TEXT}; font-size: 20px; font-weight: 600; }}
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
        QLabel#pageTitle {{ color: {PRIMARY_TEXT}; font-size: 24px; font-weight: 600; }}
        QLabel#pageDescription {{ color: {SECONDARY_TEXT}; font-size: 14px; }}
        QLabel#sectionTitle {{ color: {PRIMARY_TEXT}; font-size: 18px; font-weight: 600; }}
        QLabel#cardTitle {{ color: {PRIMARY_TEXT}; font-size: 16px; font-weight: 600; }}
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

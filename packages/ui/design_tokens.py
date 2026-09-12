"""Shared visual tokens for the Windows desktop shell."""

from __future__ import annotations


SIDEBAR_WIDTH = 248
BRAND_AREA_HEIGHT = 120
NAV_ITEM_HEIGHT = 44
NAV_ITEM_RADIUS = 6
MAIN_CONTENT_MAX_WIDTH = 1360
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
        QFrame#card {{ background: {CARD_BACKGROUND}; border: 1px solid {CARD_BORDER}; border-radius: 8px; }}
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
        QLabel#secondaryText, QLabel#emptyStateDescription, QLabel#statusSummary {{ color: {SECONDARY_TEXT}; font-size: 13px; }}
        QLabel#emptyStateTitle {{ color: {PRIMARY_TEXT}; font-size: 16px; font-weight: 600; }}
        QLineEdit#reservedInput, QComboBox#reservedInput {{ min-height: 36px; border: 1px solid {BORDER}; border-radius: 6px; padding: 0 10px; background: #FFFFFF; }}
        QLineEdit#reservedInput:disabled, QComboBox#reservedInput:disabled, QPushButton#reservedControl:disabled {{ color: #98A2B3; background: #F2F4F7; border-color: #E4E7EC; }}
        QPushButton#reservedControl {{ min-height: 36px; border: 1px solid {BORDER}; border-radius: 6px; padding: 0 16px; color: {SECONDARY_TEXT}; background: #FFFFFF; }}
    """

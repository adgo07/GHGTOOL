"""Business-neutral G03 pages and safe empty/placeholder states."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QSizePolicy,
)

from .design_tokens import WIDE_PAGE_MARGIN
from .view_models import AppRoute, ShellViewModel


Navigate = Callable[[AppRoute], None]


class BasePage(QWidget):
    """Page base with the common title/body layout and responsive margin hook."""

    def __init__(self, route: AppRoute, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.route = route
        self.setObjectName(f"page_{route.value}")
        self.body_layout = QVBoxLayout(self)
        self.body_layout.setContentsMargins(
            WIDE_PAGE_MARGIN,
            WIDE_PAGE_MARGIN,
            WIDE_PAGE_MARGIN,
            WIDE_PAGE_MARGIN,
        )
        self.body_layout.setSpacing(24)

    def set_page_margin(self, margin: int) -> None:
        self.body_layout.setContentsMargins(margin, margin, margin, margin)

    def add_header(self, title: str, description: str) -> None:
        header = QWidget(self)
        header.setObjectName("pageHeader")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)

        title_label = QLabel(title, header)
        title_label.setObjectName("pageTitle")
        title_label.setWordWrap(True)
        header_layout.addWidget(title_label)

        description_label = QLabel(description, header)
        description_label.setObjectName("pageDescription")
        description_label.setWordWrap(True)
        header_layout.addWidget(description_label)
        self.body_layout.addWidget(header)


def _card(title: str, parent: QWidget) -> tuple[QFrame, QVBoxLayout]:
    card = QFrame(parent)
    card.setObjectName("card")
    card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    layout = QVBoxLayout(card)
    layout.setContentsMargins(20, 20, 20, 20)
    layout.setSpacing(12)
    title_label = QLabel(title, card)
    title_label.setObjectName("cardTitle")
    layout.addWidget(title_label)
    return card, layout


class HomePage(BasePage):
    """Professional workbench home with safe empty recent-work sections."""

    def __init__(
        self,
        view_model: ShellViewModel,
        navigate: Navigate,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(AppRoute.HOME, parent)
        self.add_header(view_model.home_title, view_model.home_description)

        workspace = QWidget(self)
        workspace.setObjectName("primaryWorkspace")
        workspace_layout = QHBoxLayout(workspace)
        workspace_layout.setContentsMargins(0, 0, 0, 0)
        workspace_layout.setSpacing(24)

        start_panel, start_layout = _card("开始", workspace)
        start_panel.setObjectName("startPanel")
        start_panel.setFixedWidth(320)

        primary_button = QPushButton(view_model.primary_action_label, start_panel)
        primary_button.setObjectName("primaryButton")
        primary_button.setCursor(Qt.CursorShape.PointingHandCursor)
        primary_button.clicked.connect(lambda: navigate(AppRoute.NEW_ACCOUNTING))
        start_layout.addWidget(primary_button)

        standards_button = QPushButton(view_model.standards_action_label, start_panel)
        standards_button.setObjectName("secondaryButton")
        standards_button.setCursor(Qt.CursorShape.PointingHandCursor)
        standards_button.clicked.connect(lambda: navigate(AppRoute.STANDARDS))
        start_layout.addWidget(standards_button)

        excel_button = QPushButton(view_model.excel_action_label, start_panel)
        excel_button.setObjectName("reservedButton")
        excel_button.setProperty("reserved", True)
        excel_button.setCursor(Qt.CursorShape.ArrowCursor)
        excel_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        excel_button.clicked.connect(lambda: navigate(AppRoute.EXCEL_IMPORT))
        start_layout.addWidget(excel_button)
        start_layout.addStretch(1)

        recent_work, recent_layout = _card("最近核算记录", workspace)
        recent_work.setObjectName("recentWorkCard")
        if view_model.recent_records:
            for record in view_model.recent_records[:8]:
                row = QLabel(
                    f"{record.company_name} · {record.period} · {record.standard} · "
                    f"{record.emissions} · {record.status}",
                    recent_work,
                )
                row.setObjectName("bodyText")
                row.setWordWrap(True)
                recent_layout.addWidget(row)
        else:
            empty_title = QLabel("尚无核算记录", recent_work)
            empty_title.setObjectName("emptyStateTitle")
            recent_layout.addWidget(empty_title)
            empty_description = QLabel(
                "可以通过“新建核算”手工开始。\nExcel 导入功能将在后续版本开放。",
                recent_work,
            )
            empty_description.setObjectName("emptyStateDescription")
            empty_description.setWordWrap(True)
            recent_layout.addWidget(empty_description)
            recent_layout.addStretch(1)

        workspace_layout.addWidget(start_panel)
        workspace_layout.addWidget(recent_work, 1)
        self.body_layout.addWidget(workspace)

        recent_standards, standards_layout = _card("最近使用标准", self)
        recent_standards.setObjectName("recentStandardsCard")
        if view_model.recent_standards:
            for standard in view_model.recent_standards[:5]:
                row = QLabel(f"{standard.standard_id}\n{standard.title}", recent_standards)
                row.setObjectName("bodyText")
                row.setWordWrap(True)
                standards_layout.addWidget(row)
        else:
            empty_standards = QLabel("暂无最近使用标准", recent_standards)
            empty_standards.setObjectName("emptyStateDescription")
            standards_layout.addWidget(empty_standards)
        self.body_layout.addWidget(recent_standards)

        status = QLabel(view_model.status_summary, self)
        status.setObjectName("statusSummary")
        status.setWordWrap(True)
        self.body_layout.addWidget(status)
        self.body_layout.addStretch(1)


class PlaceholderPage(BasePage):
    """Reachable G03 route with no later-stage business implementation."""

    def __init__(
        self,
        route: AppRoute,
        title: str,
        description: str,
        message: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(route, parent)
        self.add_header(title, description)
        card, layout = _card("当前版本", self)
        message_label = QLabel(message, card)
        message_label.setObjectName("emptyStateDescription")
        message_label.setWordWrap(True)
        layout.addWidget(message_label)
        layout.addStretch(1)
        self.body_layout.addWidget(card)
        self.body_layout.addStretch(1)


class ExcelImportPage(BasePage):
    """Non-interactive Excel placeholder; no file or import action is wired."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(AppRoute.EXCEL_IMPORT, parent)
        self.add_header("Excel 导入", "通过标准化模板快速导入核算数据")

        card, layout = _card("功能预留，当前版本暂未开放。", self)
        controls = QWidget(card)
        controls.setObjectName("disabledImportControls")
        controls_layout = QVBoxLayout(controls)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(12)

        file_input = QLineEdit(controls)
        file_input.setObjectName("reservedInput")
        file_input.setPlaceholderText("文件选择将在后续版本开放")
        file_input.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        controls_layout.addWidget(file_input)
        self.file_input = file_input

        standard_input = QComboBox(controls)
        standard_input.setObjectName("reservedInput")
        standard_input.addItem("标准选择将在后续版本开放")
        standard_input.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        controls_layout.addWidget(standard_input)
        self.standard_input = standard_input

        button_row = QHBoxLayout()
        button_row.setSpacing(12)
        for object_name, label in (
            ("selectFileButton", "选择文件"),
            ("templateButton", "模板下载"),
            ("nextButton", "下一步"),
            ("importButton", "导入"),
        ):
            button = QPushButton(label, controls)
            button.setObjectName("reservedControl")
            button.setProperty("controlName", object_name)
            button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            button.setCursor(Qt.CursorShape.ArrowCursor)
            button_row.addWidget(button)
            setattr(self, object_name, button)
        controls_layout.addLayout(button_row)
        controls.setEnabled(False)
        layout.addWidget(controls)
        layout.addStretch(1)
        self.body_layout.addWidget(card)
        self.body_layout.addStretch(1)


def create_page(
    route: AppRoute,
    view_model: ShellViewModel,
    navigate: Navigate,
    parent: QWidget | None = None,
) -> QWidget:
    """Create exactly one G03 page for a validated public route."""

    if route is AppRoute.HOME:
        return HomePage(view_model, navigate, parent)
    if route is AppRoute.EXCEL_IMPORT:
        return ExcelImportPage(parent)

    placeholders = {
        AppRoute.STANDARDS: (
            "标准库",
            "查看 GB/T 32151 系列标准及核算要求",
            "标准库详细查询将在后续阶段实现。当前版本仅提供公共导航入口。",
        ),
        AppRoute.NEW_ACCOUNTING: (
            "新建核算",
            "按照适用标准完成企业温室气体排放核算",
            "核算输入、校验与计算将在后续阶段实现。",
        ),
        AppRoute.RECORDS: (
            "核算记录",
            "查看历史核算结果",
            "核算记录台账将在后续阶段实现。",
        ),
        AppRoute.FACTORS: (
            "参数与因子库",
            "查看核算参数、缺省值及排放因子",
            "参数与排放因子查询将在后续阶段实现。",
        ),
        AppRoute.SETTINGS: (
            "设置",
            "管理软件级低频功能",
            "设置项将在后续阶段按统一规范实现。",
        ),
    }
    try:
        title, description, message = placeholders[route]
    except KeyError as exc:
        raise ValueError(f"unsupported G03 route: {route!r}") from exc
    return PlaceholderPage(route, title, description, message, parent)

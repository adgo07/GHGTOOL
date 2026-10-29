"""Presentation-only directory: navigation never changes source participation."""
from .design_tokens import ACCOUNTING_COLORS
from PySide6.QtCore import Qt, Signal, QTimer, QPoint, QEvent, QSize
from .source_cards import SourceHeaderSwitch
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QFrame, QLabel, QPushButton, QSizePolicy, QScrollArea, QComboBox, QBoxLayout


class ContentStack(QWidget):
    """A visible-only layout: hidden long editors never impose their minimum."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._pages = []
        self._index = -1
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignTop)

    def addWidget(self, page):
        self._pages.append(page)
        self._layout.addWidget(page)
        page.hide()

    def currentWidget(self):
        return self._pages[self._index] if self._index >= 0 else None

    def currentIndex(self):
        return self._index

    def setCurrentIndex(self, index):
        for i, page in enumerate(self._pages):
            page.setVisible(i == index)
        self._index = index
        self._layout.invalidate()
        self.updateGeometry()


class EditorScrollArea(QScrollArea):
    """Keep narrow controls reachable in a bounded viewport; wide pages scroll outside."""
    def sizeHint(self):
        child = self.widget()
        height = max(child.sizeHint().height(), child.minimumSizeHint().height()) if child else 0
        extra = self.horizontalScrollBar().sizeHint().height() if child and child.minimumWidth() > self.viewport().width() else 0
        return QSize(0, height + extra)

    def minimumSizeHint(self):
        return QSize(0, 0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.updateGeometry()


class SourceDirectory(QWidget):
    enable_requested = Signal(str)
    results_requested = Signal()

    def __init__(self, entries, parent=None):
        super().__init__(parent)
        self.setObjectName("accountingSourceDirectory")
        self.cards = dict((key, card) for key, title, card in entries)
        self.buttons, self.placeholders, self.indices = {}, {}, {}
        self.placeholder_labels = {}
        self.enable_buttons = {}
        self._scroll_positions = {}
        self._selected = None
        self._selection_revision = 0
        self.titles = {key: title for key, title, card in entries}
        layout = QBoxLayout(QBoxLayout.Direction.LeftToRight, self)
        self._directory_layout = layout
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)
        nav = QFrame(self)
        nav.setObjectName("sourceDirectoryNavigation")
        nav.setFixedWidth(170)
        self.navigation_panel = nav
        self.compact_selector = QComboBox(self)
        self.compact_selector.setObjectName("compactSourceDirectory")
        self.compact_selector.setAccessibleName("选择排放源分区")
        self.compact_selector.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.compact_selector.setMinimumContentsLength(6)
        self.compact_selector.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        for key, title, card in entries:
            self.compact_selector.addItem(title, key)
        self.compact_selector.activated.connect(
            lambda index: self.select(self.compact_selector.itemData(index)))
        self.compact_selector.hide()
        layout.addWidget(self.compact_selector)
        nav.setStyleSheet(f"QFrame#sourceDirectoryNavigation {{background:{ACCOUNTING_COLORS['directory_surface']};border:1px solid {ACCOUNTING_COLORS['directory_border']};border-radius:9px;}}")
        links = QVBoxLayout(nav)
        links.setContentsMargins(10, 16, 10, 16)
        links.addWidget(QLabel("排放源目录", nav))
        self.stack = ContentStack(self)
        self.stack.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.stack.setObjectName("sourceDirectoryEditor")
        for i, (key, title, card) in enumerate(entries):
            button = QPushButton(title, nav)
            button.setObjectName("sourceDirectory_" + key)
            button.setCheckable(True)
            button.installEventFilter(self)
            button.setStyleSheet(f"QPushButton {{text-align:left;font-size:14px;padding:10px 8px;border:0;background:transparent;}} QPushButton:checked {{background:{ACCOUNTING_COLORS['source_selected']};color:{ACCOUNTING_COLORS['directory_selected_text']};font-weight:600;}} QPushButton:focus {{border:1px solid {ACCOUNTING_COLORS['brand']};}}")
            button.clicked.connect(lambda checked=False, group=key: self.select(group))
            links.addWidget(button)
            self.buttons[key], self.indices[key] = button, i
            panel = QWidget(self.stack)
            panel.setStyleSheet("background:white;")
            contents = QVBoxLayout(panel)
            contents.setContentsMargins(0, 0, 0, 0)
            contents.setAlignment(Qt.AlignmentFlag.AlignTop)
            placeholder = QWidget(panel)
            empty = QVBoxLayout(placeholder)
            text = QLabel(title + "尚未启用，已有输入仍保留。", placeholder)
            text.setWordWrap(True)
            empty.addWidget(text)
            self.placeholder_labels[key] = text
            enable = SourceHeaderSwitch(title, placeholder)
            enable.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

            self.enable_buttons[key] = enable
            enable.clicked.connect(lambda checked=False, group=key: self.enable_requested.emit(group))
            placeholder_header = QHBoxLayout()
            caption = QLabel(title, placeholder)
            caption.setWordWrap(True)
            placeholder_header.addWidget(caption, 1)
            placeholder_header.addWidget(enable)
            empty.insertLayout(0, placeholder_header)
            contents.addWidget(placeholder)
            contents.addWidget(card, 0, Qt.AlignmentFlag.AlignTop)
            self.placeholders[key] = placeholder
            self.stack.addWidget(panel)
        results = QPushButton("问题与结果 ↓", nav)
        results.clicked.connect(self.results_requested.emit)
        links.addWidget(results)
        links.addSpacing(12)
        tip = QLabel("切换目录仅查看；启用状态与输入分别保留。", nav)
        tip.setWordWrap(True)
        links.addWidget(tip)
        layout.addWidget(nav, 0, Qt.AlignmentFlag.AlignTop)
        self.editor_scroll = EditorScrollArea(self)
        self.editor_scroll.setObjectName("sourceDirectoryEditorScroll")
        self.editor_scroll.setWidgetResizable(True)
        self.editor_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.editor_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.editor_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.editor_scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.editor_scroll.setWidget(self.stack)
        layout.addWidget(self.editor_scroll, 1, Qt.AlignmentFlag.AlignTop)
        self.select(entries[0][0])
        self._adapt_width()

    def _adapt_width(self):
        compact = self.width() < 640
        self.navigation_panel.setVisible(not compact)
        self.compact_selector.setVisible(compact)
        self.stack.setMinimumWidth(420 if compact else 0)
        self.editor_scroll.setMaximumHeight(max(240, self.window().height() - 120) if compact else 16777215)
        self.editor_scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded if compact else Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        direction = QBoxLayout.Direction.TopToBottom if compact else QBoxLayout.Direction.LeftToRight
        if self._directory_layout.direction() != direction:
            self._directory_layout.setDirection(direction)
            self.updateGeometry()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._adapt_width()

    def _outer_scroll(self):
        ancestor = self.parentWidget()
        while ancestor is not None:
            if isinstance(ancestor, QScrollArea):
                return ancestor
            ancestor = ancestor.parentWidget()
        return None

    def select(self, key, *, restore_scroll=True):
        if key not in self.indices:
            return
        if key != self._selected:
            self._selection_revision += 1
        scroll = self._outer_scroll()
        reading_editor = False
        if scroll is not None and self._selected is not None:
            top = self.mapTo(scroll.widget(), QPoint(0, 0)).y()
            reading_editor = scroll.verticalScrollBar().value() >= top - 20
            if reading_editor:
                self._scroll_positions[self._selected] = max(0, scroll.verticalScrollBar().value() - top)
        self.stack.setCurrentIndex(self.indices[key])
        self._selected = key
        self.compact_selector.setCurrentIndex(self.compact_selector.findData(key))
        for group, button in self.buttons.items():
            button.setChecked(group == key)
        self.stack.updateGeometry()
        self.editor_scroll.updateGeometry()
        self.updateGeometry()
        if scroll is not None and reading_editor and restore_scroll:
            def restore():
                if self._selected == key:
                    top = self.mapTo(scroll.widget(), QPoint(0, 0)).y()
                    scroll.verticalScrollBar().setValue(top + self._scroll_positions.get(key, 0))
            QTimer.singleShot(0, self, restore)

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.KeyPress and watched in self.buttons.values():
            keys = list(self.buttons)
            index = list(self.buttons.values()).index(watched)
            if event.key() in (Qt.Key.Key_Up, Qt.Key.Key_Down, Qt.Key.Key_Home, Qt.Key.Key_End):
                if event.key() == Qt.Key.Key_Home:
                    index = 0
                elif event.key() == Qt.Key.Key_End:
                    index = len(keys) - 1
                else:
                    index = (index + (1 if event.key() == Qt.Key.Key_Down else -1)) % len(keys)
                self.select(keys[index])
                self.buttons[keys[index]].setFocus()
                return True
        return super().eventFilter(watched, event)

    def reveal(self, widget):
        for group, card in self.cards.items():
            if widget is card or card.isAncestorOf(widget):
                self.select(group, restore_scroll=False)
                return

    def set_state(self, group, state):
        self.buttons[group].setText(self.titles[group] + "\n" + state)
        self.buttons[group].setAccessibleDescription(state)
        self.compact_selector.setItemText(self.compact_selector.findData(group), self.titles[group] + " · " + state)
        self.enable_buttons[group].set_source_state(state)
        self.placeholder_labels[group].setText(self.titles[group] + "：" + state + "，已有输入仍保留。")

    def refresh(self):
        for group, card in self.cards.items():
            self.placeholders[group].setVisible(card.isHidden())
        self.stack.updateGeometry()
        self.editor_scroll.updateGeometry()
        self.updateGeometry()

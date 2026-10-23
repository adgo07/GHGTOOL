"""Presentation-only directory: navigation never changes source participation."""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QFrame, QLabel, QPushButton, QStackedWidget, QScrollArea


class SourceDirectory(QWidget):
    enable_requested = Signal(str)

    def __init__(self, entries, parent=None):
        super().__init__(parent)
        self.setObjectName("accountingSourceDirectory")
        self.cards = dict((key, card) for key, title, card in entries)
        self.buttons, self.placeholders, self.indices, self.scrollers = {}, {}, {}, {}
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)
        nav = QFrame(self)
        nav.setObjectName("sourceDirectoryNavigation")
        nav.setFixedWidth(170)
        nav.setMinimumHeight(850)
        nav.setStyleSheet("QFrame#sourceDirectoryNavigation {background:#F3F8FC;border:1px solid #DCE8F1;border-radius:9px;}")
        links = QVBoxLayout(nav)
        links.setContentsMargins(10, 16, 10, 16)
        links.addWidget(QLabel("排放源目录", nav))
        self.stack = QStackedWidget(self)
        self.stack.setFixedHeight(850)
        self.stack.setObjectName("sourceDirectoryEditor")
        for i, (key, title, card) in enumerate(entries):
            button = QPushButton(title, nav)
            button.setObjectName("sourceDirectory_" + key)
            button.setCheckable(True)
            button.setStyleSheet("QPushButton {text-align:left;font-size:14px;padding:10px 8px;border:0;background:transparent;} QPushButton:checked {background:#DDEEF9;color:#096C9F;font-weight:600;} QPushButton:focus {border:1px solid #197CC2;}")
            button.clicked.connect(lambda checked=False, group=key: self.select(group))
            links.addWidget(button)
            self.buttons[key], self.indices[key] = button, i
            scroll = QScrollArea(self.stack)
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.Shape.NoFrame)
            self.scrollers[key] = scroll
            panel = QWidget(scroll)
            panel.setStyleSheet("background:white;")
            contents = QVBoxLayout(panel)
            contents.setContentsMargins(0, 0, 0, 0)
            contents.setAlignment(Qt.AlignmentFlag.AlignTop)
            placeholder = QWidget(panel)
            empty = QVBoxLayout(placeholder)
            text = QLabel(title + "尚未启用，已有输入仍保留。", placeholder)
            text.setWordWrap(True)
            empty.addWidget(text)
            enable = QPushButton("启用" + title, placeholder)
            enable.clicked.connect(lambda checked=False, group=key: self.enable_requested.emit(group))
            empty.addWidget(enable, 0, Qt.AlignmentFlag.AlignLeft)
            contents.addWidget(placeholder)
            contents.addWidget(card, 0, Qt.AlignmentFlag.AlignTop)
            self.placeholders[key] = placeholder
            contents.addStretch(1)
            scroll.setWidget(panel)
            self.stack.addWidget(scroll)
        links.addStretch(1)
        tip = QLabel("切换目录仅查看；启用状态与输入分别保留。", nav)
        tip.setWordWrap(True)
        links.addWidget(tip)
        layout.addWidget(nav, 0, Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.stack, 1, Qt.AlignmentFlag.AlignTop)
        self.select(entries[0][0])

    def select(self, key):
        if key not in self.indices:
            return
        self.stack.setCurrentIndex(self.indices[key])
        for group, button in self.buttons.items():
            button.setChecked(group == key)
        self.stack.updateGeometry()
        self.updateGeometry()

    def reveal(self, widget):
        for group, card in self.cards.items():
            if widget is card or card.isAncestorOf(widget):
                self.select(group)
                if widget is not card:
                    self.scrollers[group].ensureWidgetVisible(widget)
                return

    def refresh(self):
        for group, card in self.cards.items():
            self.placeholders[group].setVisible(card.isHidden())
        self.stack.updateGeometry()
        self.updateGeometry()

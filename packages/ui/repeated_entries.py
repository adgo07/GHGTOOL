"""Page-local repeat-item framing; presentation only, retaining original widgets."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget
from .design_tokens import ACCOUNTING_COLORS as C, STATUS_ABOLISHED


def frame_entry(host, title, remove, *, toolbar=None, inner=False):
    """Move existing layout items into a disclosed body without copying inputs."""
    outer = host.layout()
    layout_enabled, updates_enabled = outer.isEnabled(), host.updatesEnabled()
    outer.setEnabled(False)
    host.setUpdatesEnabled(False)
    try:
        return _frame_entry(host, title, remove, toolbar=toolbar, inner=inner)
    finally:
        outer.setEnabled(layout_enabled)
        host.setUpdatesEnabled(updates_enabled)


def _frame_entry(host, title, remove, *, toolbar=None, inner=False):
    host.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    host.setProperty('repeatEntryLevel', 'inner' if inner else 'outer')
    outer = host.layout()
    body = QWidget(host)
    contents = QVBoxLayout(body)
    contents.setContentsMargins(10, 10, 10, 10)
    contents.setSpacing(12)
    body.setObjectName("repeatEntryBody")
    while outer.count():
        item = outer.itemAt(0)
        layout, widget = item.layout(), item.widget()
        if layout is not None:
            outer.takeAt(0)
            layout.setParent(None)
            if toolbar is None or layout is not toolbar:
                contents.addLayout(layout)
        elif widget is not None:
            # Remove the old QWidgetItem before creating its new layout item.
            # Keeping both items alive leaves the old size cache attached.
            outer.removeWidget(widget)
            contents.addWidget(widget)
        else:
            contents.addItem(outer.takeAt(0))
    if toolbar is None:
        toolbar = QHBoxLayout()
        toolbar.addWidget(title, 1)
        # The old row can contain the remove button in a nested grid/footer.
        def detach(layout):
            layout.removeWidget(remove)
            for index in range(layout.count()):
                child = layout.itemAt(index).layout()
                if child is not None:
                    detach(child)
        detach(contents)
        toolbar.addWidget(remove)
    # Existing toolbars used a stretch spacer after the title. Give their
    # available width to the label itself, so long object identities can wrap.
    for index in reversed(range(toolbar.count())):
        if toolbar.itemAt(index).spacerItem() is not None:
            toolbar.takeAt(index)
    title.setWordWrap(True)
    title.setMinimumWidth(0)
    title.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    toolbar.setStretch(toolbar.indexOf(title), 1)
    header = QFrame(host)
    header.setObjectName('repeatEntryHeader')
    header_layout = QVBoxLayout(header)
    header_layout.setContentsMargins(10, 7, 10, 7)
    header_layout.addLayout(toolbar)
    toggle = QPushButton('收起', header)
    toggle.setCheckable(True)
    toggle.setChecked(True)
    toggle.setAccessibleName(title.text() + '：展开或收起')
    toolbar.insertWidget(max(0, toolbar.count() - 1), toggle)
    toggle.toggled.connect(body.setVisible)
    toggle.toggled.connect(lambda expanded: toggle.setText('收起' if expanded else '展开'))
    body._disclosure_button = toggle
    host._entry_body, host._entry_toggle, host._entry_header = body, toggle, header
    outer.setContentsMargins(1, 1, 1, 1)
    outer.setSpacing(0)
    outer.addWidget(header)
    outer.addWidget(body)
    remove.setProperty('danger', True)
    remove.setProperty('repeatEntryDelete', True)
    # Reuse the page stylesheet; recompiling a sheet for every nested object
    # repolishes its entire subtree during bulk restore/add operations.
    for widget in (host, remove):
        widget.style().unpolish(widget)
        widget.style().polish(widget)
    return body


def repeat_entry_stylesheet():
    """One page-local rule set for all repeated objects, using family tokens."""
    return f"""
        QWidget[repeatEntryLevel="outer"] {{background:{C['white']};border:1px solid {C['choice_border']};border-radius:7px;}}
        QWidget[repeatEntryLevel="inner"] {{background:{C['directory_surface']};border:1px solid {C['directory_border']};border-radius:5px;}}
        QWidget#repeatEntryBody {{background:{C['white']};border:0;}}
        QWidget[repeatEntryLevel="inner"] > QWidget#repeatEntryBody {{background:{C['directory_surface']};}}
        QFrame#repeatEntryHeader {{background:{C['source_active_surface']};border:0;border-radius:5px;}}
        QWidget[repeatEntryLevel="inner"] > QFrame#repeatEntryHeader {{background:{C['directory_surface']};}}
        QFrame#repeatEntryHeader QLabel {{color:{C['primary_text']};font-weight:600;border:0;background:transparent;}}
        QPushButton[repeatEntryDelete="true"] {{color:{STATUS_ABOLISHED};background:transparent;border:0;padding:5px;}}
        QPushButton[repeatEntryDelete="true"]:focus {{border:1px solid {STATUS_ABOLISHED};}}
    """

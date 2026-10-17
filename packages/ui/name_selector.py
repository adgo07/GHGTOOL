"""Editable name selection separates typing from committed business identity."""
import unicodedata
from PySide6.QtCore import Qt, Signal, QSignalBlocker
from PySide6.QtWidgets import QComboBox, QCompleter


def normalized_name(value):
    return unicodedata.normalize("NFKC", str(value)).strip().casefold()


def chemical_label(value):
    return str(value).translate(str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉"))


class NameSelector(QComboBox):
    name_confirmed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self._search_names = ()
        self._last_confirmed = ""
        self.activated.connect(lambda *_: self.confirm_name(force=True))
        self.currentIndexChanged.connect(self._index_selected)
        self.lineEdit().editingFinished.connect(self.confirm_name)

    def _index_selected(self, index):
        if index >= 0:
            self.confirm_name(force=True)

    def set_search_names(self, names):
        self._search_names = tuple(names)
        values = tuple(dict.fromkeys(value for canonical, aliases in self._search_names for value in (canonical, *aliases)))
        completer = QCompleter(values, self)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.activated[str].connect(self._accept_alias)
        self.setCompleter(completer)

    def _accept_alias(self, text):
        self.setEditText(text)
        self.confirm_name(force=True)

    def confirm_name(self, force=False):
        text = self.currentText().strip()
        if not force and text == self._last_confirmed:
            return
        matches = [canonical for canonical, aliases in self._search_names
                   if normalized_name(text) in {normalized_name(value) for value in (canonical, *aliases)}]
        if len(set(matches)) == 1:
            text = matches[0]
            blocker = QSignalBlocker(self)
            index = self.findText(text)
            if index >= 0:self.setCurrentIndex(index)
            else:self.setEditText(text)
            del blocker
        self._last_confirmed = text
        self.name_confirmed.emit(text)

    def restore_confirmation(self, text):
        self._last_confirmed = str(text)

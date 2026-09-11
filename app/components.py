"""Reusable PySide6 presentation components."""

from collections.abc import Iterable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout,
    QWidget,
)

from app.styles import CARD, apply_glow


class Card(QFrame):
    def __init__(self, parent: QWidget | None = None, glow: bool = True) -> None:
        super().__init__(parent)
        self.setObjectName("card")
        if glow:
            apply_glow(self)


class TitleLabel(QLabel):
    def __init__(self, text: str, parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setObjectName("title")
        apply_glow(self, blur=10, opacity=90)


class MetricCard(Card):
    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent, glow=False)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        label = QLabel(title.upper())
        label.setObjectName("eyebrow")
        self.value_label = QLabel("--")
        self.value_label.setObjectName("metricValue")
        layout.addWidget(label)
        layout.addWidget(self.value_label)


class DataTable(QTableWidget):
    def __init__(self, headers: Iterable[str], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        labels = list(headers)
        self.setColumnCount(len(labels))
        self.setHorizontalHeaderLabels(labels)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setStretchLastSection(True)

    def replace_rows(self, rows: list[list[str]]) -> None:
        self.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for column_index, value in enumerate(row):
                self.setItem(row_index, column_index, QTableWidgetItem(str(value)))
        self.resizeColumnsToContents()


def form_row(*widgets: QWidget) -> QHBoxLayout:
    layout = QHBoxLayout()
    layout.setSpacing(8)
    for widget in widgets:
        layout.addWidget(widget, 1)
    return layout
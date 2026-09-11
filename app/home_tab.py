"""Home tab for Tethys."""

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from app.components import Card, TitleLabel


class HomeTab(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)

        intro = Card()
        intro_layout = QVBoxLayout(intro)
        intro_layout.setContentsMargins(20, 18, 20, 18)
        intro_layout.addWidget(TitleLabel("Tethys"))
        subtitle = QLabel("Motor de dano local para testar rotações, equipes e execução prática.")
        subtitle.setObjectName("muted")
        intro_layout.addWidget(subtitle)
        root.addWidget(intro)
        note = Card()
        note_layout = QVBoxLayout(note)
        note_layout.setContentsMargins(20, 18, 20, 20)
        note_layout.addWidget(TitleLabel("Fluxo de cálculo"))
        note_layout.addWidget(QLabel("Carregue uma ID para ajustar manualmente stats, build e multiplicadores na aba do personagem."))
        root.addWidget(note)
        root.addStretch(1)

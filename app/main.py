"""PySide6 application entry point."""

from __future__ import annotations

import sys
import re
import unicodedata
from pathlib import Path

from PySide6.QtCore import QSettings, Qt, QUrl
from PySide6.QtGui import QDesktopServices, QPixmap, QResizeEvent
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QFormLayout, QFrame,
    QHBoxLayout, QFileDialog, QLabel, QLineEdit, QMainWindow, QMessageBox,
    QPushButton, QTabWidget, QVBoxLayout, QWidget,
)

from app.components import Card, TitleLabel
from app.history_tab import HistoryTab
from app.home_tab import HomeTab
from app.multimedia_tab import MultimediaTab
from app.resonator_tab import ResonatorTab
from app.styles import application_qss, refresh_glows
from app.teams_tab import TeamsTab
from data.characters_elements import CHARACTER_ELEMENTS
from data.characters_ids import KNOWN_CHARACTER_IDS


class PlaceholderTab(QWidget):
    def __init__(self, title: str, description: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        card = Card()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.addWidget(TitleLabel(title))
        text = QLabel(description)
        text.setObjectName("muted")
        card_layout.addWidget(text)
        card_layout.addStretch(1)
        layout.addWidget(card)


class SettingsTab(QWidget):
    def __init__(self, parent: QWidget | None = None, host: QWidget | None = None) -> None:
        super().__init__(parent)
        self.host = host
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        appearance_card = Card()
        appearance_layout = QVBoxLayout(appearance_card)
        appearance_layout.setContentsMargins(20, 20, 20, 20)
        appearance_layout.addWidget(TitleLabel("Aparência e janela"))
        appearance_form = QFormLayout()
        appearance_form.setVerticalSpacing(12)
        self.background_box = QCheckBox("Usar imagem de fundo")
        self.background_box.setChecked(True)
        appearance_form.addRow("Fundo", self.background_box)
        self.resolution_box = QComboBox()
        self.resolution_box.addItems(["1440 x 900", "1280 x 800", "1024 x 720"])
        appearance_form.addRow("Resolução", self.resolution_box)
        self.confirm_exit_box = QCheckBox("Confirmar antes de fechar o programa")
        self.confirm_exit_box.setChecked(True)
        appearance_form.addRow("Encerramento", self.confirm_exit_box)
        appearance_layout.addLayout(appearance_form)
        layout.addWidget(appearance_card)

        wallpaper_card = Card()
        wallpaper_layout = QVBoxLayout(wallpaper_card)
        wallpaper_layout.setContentsMargins(20, 20, 20, 20)
        wallpaper_layout.addWidget(TitleLabel("Wallpaper personalizado"))
        wallpaper_info = QLabel(
            "Use uma imagem entre 1024 x 640 e 1440 x 900 px, na proporção 16:10. "
            "O tamanho ideal é 1440 x 900 px para preencher o programa sem deformar."
        )
        wallpaper_info.setObjectName("muted")
        wallpaper_info.setWordWrap(True)
        wallpaper_layout.addWidget(wallpaper_info)
        self.wallpaper_label = QLabel("Fundo padrão do programa")
        self.wallpaper_label.setObjectName("muted")
        self.wallpaper_label.setWordWrap(True)
        wallpaper_layout.addWidget(self.wallpaper_label)
        wallpaper_actions = QHBoxLayout()
        choose_wallpaper_button = QPushButton("Escolher wallpaper")
        choose_wallpaper_button.clicked.connect(self._choose_wallpaper)
        wallpaper_actions.addWidget(choose_wallpaper_button)
        reset_wallpaper_button = QPushButton("Usar fundo padrão")
        reset_wallpaper_button.clicked.connect(self._reset_wallpaper)
        wallpaper_actions.addWidget(reset_wallpaper_button)
        wallpaper_actions.addStretch(1)
        wallpaper_layout.addLayout(wallpaper_actions)
        layout.addWidget(wallpaper_card)

        data_card = Card()
        data_layout = QVBoxLayout(data_card)
        data_layout.setContentsMargins(20, 20, 20, 20)
        data_layout.addWidget(TitleLabel("Dados da sessão"))
        data_text = QLabel("Remova as abas de personagens carregadas sem apagar arquivos salvos.")
        data_text.setObjectName("muted")
        data_layout.addWidget(data_text)
        clear_button = QPushButton("Limpar personagens carregados")
        clear_button.clicked.connect(self._clear_characters)
        data_layout.addWidget(clear_button, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(data_card)

        actions = QHBoxLayout()
        defaults_button = QPushButton("Restaurar padrões")
        defaults_button.clicked.connect(self._restore_defaults)
        actions.addWidget(defaults_button)
        actions.addStretch(1)
        layout.addLayout(actions)
        layout.addStretch(1)

        self.background_box.toggled.connect(self._background_changed)
        self.resolution_box.currentTextChanged.connect(self._resolution_changed)
        self.confirm_exit_box.toggled.connect(self._confirm_exit_changed)
        self._load_preferences()

    @property
    def preferences(self) -> QSettings:
        return QSettings("Tethys", "Tethys")

    def _load_preferences(self) -> None:
        settings = self.preferences
        self.background_box.setChecked(settings.value("background", True, type=bool))
        resolution = settings.value("resolution", "1440 x 900", type=str)
        index = self.resolution_box.findText(resolution)
        self.resolution_box.setCurrentIndex(max(0, index))
        self.confirm_exit_box.setChecked(settings.value("confirm_exit", True, type=bool))
        wallpaper = settings.value("wallpaper", "", type=str)
        self._set_wallpaper_label(wallpaper)

    def _choose_wallpaper(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Escolher wallpaper do programa",
            "",
            "Imagens (*.png *.jpg *.jpeg *.webp);;Todos os arquivos (*)",
        )
        if not path:
            return
        from PySide6.QtGui import QPixmap

        size = QPixmap(path).size()
        minimum_width, minimum_height = 1024, 640
        maximum_width, maximum_height = 1440, 900
        ratio = size.width() / size.height() if size.height() else 0
        if (
            size.width() < minimum_width
            or size.height() < minimum_height
            or size.width() > maximum_width
            or size.height() > maximum_height
            or abs(ratio - 1.6) > 0.01
        ):
            QMessageBox.warning(
                self,
                "Tamanho de wallpaper inválido",
                "Escolha uma imagem entre 1024 x 640 e 1440 x 900 px, "
                "com proporção 16:10. O tamanho recomendado é 1440 x 900 px.",
            )
            return
        wallpaper = str(QUrl.fromLocalFile(path).toString())
        self.preferences.setValue("wallpaper", wallpaper)
        self.preferences.sync()
        self._set_wallpaper_label(path)
        window = self.host or self.window()
        if isinstance(window, WuwaQtWindow):
            window.apply_preferences()

    def _reset_wallpaper(self) -> None:
        self.preferences.remove("wallpaper")
        self.preferences.sync()
        self._set_wallpaper_label("")
        window = self.host or self.window()
        if isinstance(window, WuwaQtWindow):
            window.apply_preferences()

    def _set_wallpaper_label(self, wallpaper: str) -> None:
        self.wallpaper_label.setText(
            f"Wallpaper atual: {wallpaper}"
            if wallpaper
            else "Wallpaper atual: app_background_reference.png"
        )

    def _background_changed(self, enabled: bool) -> None:
        self.preferences.setValue("background", enabled)
        window = self.host or self.window()
        if isinstance(window, WuwaQtWindow):
            window.apply_preferences()

    def _resolution_changed(self, resolution: str) -> None:
        self.preferences.setValue("resolution", resolution)
        window = self.host or self.window()
        if isinstance(window, WuwaQtWindow):
            width, height = (int(value) for value in resolution.split(" x "))
            window.setFixedSize(width, height)

    def _confirm_exit_changed(self, enabled: bool) -> None:
        self.preferences.setValue("confirm_exit", enabled)

    def _clear_characters(self) -> None:
        window = self.host or self.window()
        if not isinstance(window, WuwaQtWindow):
            return
        for character_tab in window.character_tabs.values():
            tab_index = window.tabs.indexOf(character_tab)
            if tab_index >= 0:
                window.tabs.removeTab(tab_index)
            character_tab.deleteLater()
        window.character_tabs.clear()
        while window.character_sidebar_layout.count():
            item = window.character_sidebar_layout.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()
        window.tabs.setCurrentIndex(0)
        window._set_sidebar_active("⌂   Home")

    def _restore_defaults(self) -> None:
        self.preferences.clear()
        self.background_box.setChecked(True)
        self.resolution_box.setCurrentText("1440 x 900")
        self.confirm_exit_box.setChecked(True)
        self._reset_wallpaper()
        window = self.host or self.window()
        if isinstance(window, WuwaQtWindow):
            window.setFixedSize(1440, 900)
            window.apply_preferences()


class SettingsDialog(QDialog):
    def __init__(self, host: QWidget) -> None:
        super().__init__(host)
        self.setWindowTitle("Configurações | Tethys")
        self.setModal(True)
        self.setMinimumSize(760, 620)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.addWidget(SettingsTab(self, host=host), 1)
        close_button = QPushButton("Fechar")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button, 0, Qt.AlignmentFlag.AlignRight)


class AboutDialog(QDialog):
    VERSION = "1.0.0"

    def __init__(self, host: QWidget) -> None:
        super().__init__(host)
        self.setWindowTitle("Sobre | Tethys")
        self.setModal(True)
        self.setMinimumSize(560, 430)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 20)
        layout.setSpacing(12)
        layout.addWidget(TitleLabel("Tethys"))

        description = QLabel(
            "Laboratório local para análise de dano, personagens, equipes e rotações "
            "de Wuthering Waves."
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        info = QLabel(
            f"Versão: {self.VERSION}\n"
            "Tecnologia: Python + PySide6\n"
            "Mídia: Qt Multimedia\n"
            "Licença: MIT\n"
            f"Projeto: {Path.cwd()}"
        )
        info.setObjectName("muted")
        info.setWordWrap(True)
        layout.addWidget(info)

        notes = QLabel(
            "Os dados carregados nesta aplicação são usados localmente. "
            "Consulte o README para instruções, limitações e informações do projeto."
        )
        notes.setObjectName("muted")
        notes.setWordWrap(True)
        layout.addWidget(notes)
        layout.addStretch(1)

        actions = QHBoxLayout()
        readme_button = QPushButton("Abrir README")
        readme_button.clicked.connect(self._open_readme)
        actions.addWidget(readme_button)
        copy_button = QPushButton("Copiar diagnóstico")
        copy_button.clicked.connect(self._copy_diagnostic)
        actions.addWidget(copy_button)
        actions.addStretch(1)
        close_button = QPushButton("Fechar")
        close_button.clicked.connect(self.accept)
        actions.addWidget(close_button)
        layout.addLayout(actions)

    def _open_readme(self) -> None:
        readme = Path(__file__).resolve().parent.parent / "README.md"
        if readme.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(readme)))
            return
        QMessageBox.information(self, "README não encontrado", "O arquivo README.md não foi encontrado.")

    def _copy_diagnostic(self) -> None:
        diagnostic = (
            f"Tethys {self.VERSION}\n"
            "Python + PySide6\n"
            f"Diretório: {Path.cwd()}"
        )
        QApplication.clipboard().setText(diagnostic)
        QMessageBox.information(self, "Diagnóstico copiado", "As informações foram copiadas para a área de transferência.")


class WuwaQtWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.preferences = QSettings("Tethys", "Tethys")
        self.setWindowTitle("Tethys | PySide6")
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowCloseButtonHint
            | Qt.WindowType.WindowMinimizeButtonHint
        )
        self.setFixedSize(1440, 900)
        self.background_label = QLabel(self)
        self.background_label.setObjectName("appBackground")
        self.background_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.background_label.lower()
        shell = QWidget()
        shell.setObjectName("appShell")
        shell_layout = QVBoxLayout(shell)
        shell_layout.setContentsMargins(12, 10, 12, 12)
        shell_layout.setSpacing(10)

        header = Card()
        header.setObjectName("appHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 10, 16, 10)
        header_layout.addWidget(TitleLabel("Tethys"))
        header_layout.addStretch(1)
        header_layout.addWidget(QLabel("CHARACTER ID"))
        self.character_id_entry = QLineEdit()
        self.character_id_entry.setPlaceholderText("ex.: suisui")
        self.character_id_entry.setFixedWidth(210)
        self.character_load_button = QPushButton("Carregar Personagem / ID")
        self.character_load_button.setObjectName("primaryAction")
        header_layout.addWidget(self.character_id_entry)
        header_layout.addWidget(self.character_load_button)
        self.character_status = QLabel("Pronto")
        self.character_status.setObjectName("onlineStatus")
        header_layout.addWidget(self.character_status)
        shell_layout.addWidget(header)

        tabs = QTabWidget()
        tabs.setObjectName("mainTabs")
        tabs.tabBar().hide()
        home_tab = HomeTab()
        history_tab = HistoryTab()
        tabs.addTab(home_tab, "Home")
        tabs.addTab(TeamsTab(), "Teams")
        tabs.addTab(history_tab, "Histórico")
        tabs.addTab(MultimediaTab(), "Multimídia")
        tabs.addTab(PlaceholderTab("Fontes de dados", "Tela preparada para exibir fontes, cache e estado das integrações."), "Fontes de dados")
        self.tabs = tabs
        self.character_tabs: dict[str, ResonatorTab] = {}
        self.sidebar_buttons: dict[str, QPushButton] = {}
        workspace = QHBoxLayout()
        workspace.setContentsMargins(0, 0, 0, 0)
        workspace.setSpacing(0)
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(184)
        self.sidebar_layout = QVBoxLayout(sidebar)
        self.sidebar_layout.setContentsMargins(14, 18, 14, 18)
        self.sidebar_layout.setSpacing(8)
        for index, label in enumerate(("⌂   Home", "♣   Teams", "◷   Histórico", "▣   Multimídia")):
            self._add_sidebar_button(self.sidebar_layout, label, index)
        self.sidebar_layout.addSpacing(10)
        self.character_sidebar_layout = QVBoxLayout()
        self.character_sidebar_layout.setSpacing(8)
        self.sidebar_layout.addLayout(self.character_sidebar_layout)
        self.sidebar_layout.addSpacing(10)
        self.sidebar_layout.addStretch(1)
        settings_button = self._add_sidebar_button(self.sidebar_layout, "⚙   Configurações", None)
        settings_button.clicked.connect(self.open_settings)
        about_button = self._add_sidebar_button(self.sidebar_layout, "ⓘ   Sobre", None)
        about_button.clicked.connect(self.open_about)
        workspace.addWidget(sidebar)
        workspace.addWidget(tabs, 1)
        shell_layout.addLayout(workspace, 1)
        self._set_sidebar_active("Home")
        self.setCentralWidget(shell)
        self._update_background(
            self.preferences.value("background", True, type=bool),
            self.preferences.value("wallpaper", "", type=str),
        )
        self.character_load_button.clicked.connect(self.open_character_tab)
        self.character_id_entry.returnPressed.connect(self.open_character_tab)

    def apply_preferences(self) -> None:
        self.preferences.sync()
        background = self.preferences.value("background", True, type=bool)
        wallpaper = self.preferences.value("wallpaper", "", type=str)
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(application_qss(show_background=background, wallpaper=wallpaper))
        refresh_glows(self)
        self._update_background(background, wallpaper)

    def _update_background(self, enabled: bool, wallpaper: str) -> None:
        self.background_label.setVisible(enabled)
        if not enabled:
            return
        source = QUrl.fromUserInput(wallpaper).toLocalFile() if wallpaper else ""
        project_root = Path(__file__).resolve().parent.parent
        default_background = project_root / "Assets" / "app_background_reference.png"
        pixmap = QPixmap(source or str(default_background))
        if pixmap.isNull():
            pixmap = QPixmap(str(default_background))
        if pixmap.isNull():
            return
        scaled = pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        left = max(0, (scaled.width() - self.width()) // 2)
        top = max(0, (scaled.height() - self.height()) // 2)
        self.background_label.setGeometry(self.rect())
        self.background_label.setPixmap(scaled.copy(left, top, self.width(), self.height()))
        self.background_label.lower()

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self._update_background(
            self.preferences.value("background", True, type=bool),
            self.preferences.value("wallpaper", "", type=str),
        )

    def closeEvent(self, event) -> None:
        if self.preferences.value("confirm_exit", True, type=bool):
            answer = QMessageBox.question(
                self,
                "Fechar programa",
                "Deseja realmente fechar o Tethys?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
        event.accept()

    def _add_sidebar_button(
        self,
        layout: QVBoxLayout,
        label: str,
        tab_index: int | None,
        element: str | None = None,
    ) -> QPushButton:
        button = QPushButton(label)
        button.setObjectName("nav")
        if element:
            button.setProperty("element", element)
        if tab_index is not None:
            button.clicked.connect(lambda: self._select_main_tab(tab_index, label))
            self.sidebar_buttons[label] = button
        layout.addWidget(button)
        return button

    def open_settings(self) -> None:
        SettingsDialog(self).exec()

    def open_about(self) -> None:
        AboutDialog(self).exec()

    def _select_main_tab(self, index: int, label: str) -> None:
        self.tabs.setCurrentIndex(index)
        self._set_sidebar_active(label)

    def _set_sidebar_active(self, active_label: str) -> None:
        for label, button in self.sidebar_buttons.items():
            button.setObjectName("navActive" if label == active_label else "nav")
            button.style().unpolish(button)
            button.style().polish(button)
            button.update()

    @staticmethod
    def _normalize_character_id(value: str) -> str:
        folded = "".join(char for char in unicodedata.normalize("NFKD", value.casefold()) if not unicodedata.combining(char))
        return re.sub(r"[^a-z0-9]+", "", folded)

    def open_character_tab(self) -> None:
        target = self._normalize_character_id(self.character_id_entry.text())
        character_id = next((item for item in KNOWN_CHARACTER_IDS if self._normalize_character_id(item) == target), None)
        if character_id is None:
            self.character_status.setText("ID inválida")
            return

        character_tab = self.character_tabs.get(character_id)
        if character_tab is None:
            character_tab = ResonatorTab(initial_id=character_id)
            self.character_tabs[character_id] = character_tab
            sources_index = self.tabs.count() - 1
            self.tabs.insertTab(sources_index, character_tab, f"◆ {character_id.replace(':', ' ').title()}")
            label = character_id.replace(":", " ").title()
            self._add_sidebar_button(
                self.character_sidebar_layout,
                f"◆   {label}",
                self.tabs.indexOf(character_tab),
                CHARACTER_ELEMENTS.get(character_id),
            )

        self.tabs.setCurrentWidget(character_tab)
        self._set_sidebar_active(f"◆   {character_id.replace(':', ' ').title()}")
        self.character_status.setText(f"{character_id} carregado")


def main() -> int:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    settings = QSettings("Tethys", "Tethys")
    background = settings.value("background", True, type=bool)
    wallpaper = settings.value("wallpaper", "", type=str)
    app.setStyleSheet(application_qss(show_background=background, wallpaper=wallpaper))
    window = WuwaQtWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
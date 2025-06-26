import sys
import os
import json
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPlainTextEdit, QTextEdit, QWidget,
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QDialog, QFileDialog,
    QFontComboBox, QSpinBox, QCheckBox, QLineEdit, QMenu, QMessageBox
)
from PySide6.QtGui import (
    QAction, QKeySequence, QFont, QColor, QPainter, QIcon, QTextFormat, QShortcut, QPixmap
)
from PySide6.QtCore import Qt, QRect, QPoint

CONFIG_FILE = os.path.expanduser("~/.arknotes_config.json")
DEFAULT_CONFIG = {
    "font_family": "Arial",
    "font_size": 17,
    "menu_button_size": 22,
    "dark_mode": True,
    "save_hotkey": "Ctrl+S",
    "exit_hotkey": "Ctrl+Q"
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

class RoundedBox(QWidget):
    def __init__(self, color="#232323", radius=12, border="#333333", parent=None):
        super().__init__(parent)
        self.bgcolor = QColor(color)
        self.radius = radius
        self.border = QColor(border)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAutoFillBackground(False)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()
        painter.setBrush(self.bgcolor)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect, self.radius, self.radius)
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QColor(self.border))
        painter.drawRoundedRect(rect.adjusted(1,1,-1,-1), self.radius, self.radius)

class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return self.line_number_width(), 0

    def line_number_width(self):
        digits = len(str(max(1, self.editor.blockCount())))
        return 16 + self.editor.fontMetrics().horizontalAdvance('9') * digits

    def paintEvent(self, event):
        painter = QPainter(self)
        config = self.editor.config
        if config.get("dark_mode", True):
            painter.fillRect(event.rect(), QColor("#292929"))
            painter.setPen(QColor("#888"))
        else:
            painter.fillRect(event.rect(), QColor("#f0f0f0"))
            painter.setPen(QColor("#444"))
        painter.setFont(self.editor.font())
        block = self.editor.firstVisibleBlock()
        block_number = block.blockNumber()
        offset = self.editor.contentOffset()
        top = int(self.editor.blockBoundingGeometry(block).translated(offset).top())
        bottom = top + int(self.editor.blockBoundingRect(block).height())
        height = self.editor.fontMetrics().height()
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                painter.drawText(0, top, self.width() - 4, height,
                                 Qt.AlignRight | Qt.AlignVCenter, str(block_number + 1))
            block = block.next()
            top = bottom
            bottom = top + int(self.editor.blockBoundingRect(block).height())
            block_number += 1

class ArkTextEdit(QPlainTextEdit):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.update_font()
        self.setStyleSheet(self._build_stylesheet())
        self.line_number_area = LineNumberArea(self)
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.update_line_number_area_width(0)
        self.highlight_current_line()
        self.textChanged.connect(self._on_text_changed)
        self._unsaved = False

        # --- FIX: Disable wrap, enable horizontal scrollbar ---
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

    def update_font(self):
        font = QFont(self.config["font_family"], self.config["font_size"])
        self.setFont(font)
        self.setTabStopDistance(4 * self.fontMetrics().horizontalAdvance(' '))

    def _build_stylesheet(self):
        if self.config["dark_mode"]:
            return ("QPlainTextEdit { background: transparent; color: #ededed; border: none;"
                    "border-radius: 8px; selection-background-color: #444; font-size: %dpx; }"
                    % self.config["font_size"])
        else:
            return ("QPlainTextEdit { background: transparent; color: #232323; border: none;"
                    "border-radius: 8px; selection-background-color: #b6d7ff; font-size: %dpx; }"
                    % self.config["font_size"])

    def set_dark_mode(self, dark):
        self.config["dark_mode"] = dark
        self.setStyleSheet(self._build_stylesheet())
        self.line_number_area.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        width = self.line_number_area.line_number_width()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), width, cr.height()))
        self.line_number_area.update()

    def update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area.line_number_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def highlight_current_line(self):
        extraSelections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            if self.config["dark_mode"]:
                selection.format.setBackground(QColor("#2d2d2d"))
            else:
                selection.format.setBackground(QColor("#d3e3f8"))
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extraSelections.append(selection)
        self.setExtraSelections(extraSelections)

    def _on_text_changed(self):
        self._unsaved = True

    def set_unsaved(self, unsaved: bool):
        self._unsaved = unsaved

    def is_unsaved(self):
        return self._unsaved

    def keyPressEvent(self, event):
        # Intercept Shift+Enter and insert a real newline instead
        if event.key() in (Qt.Key_Return, Qt.Key_Enter) and event.modifiers() & Qt.ShiftModifier:
            self.insertPlainText('\n')
            return
        super().keyPressEvent(event)

class PreferencesDialog(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Preferences")
        self.config = config
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Save Hotkey:"))
        self.save_hotkey = QLineEdit(self)
        self.save_hotkey.setText(self.config.get("save_hotkey", "Ctrl+S"))
        layout.addWidget(self.save_hotkey)

        layout.addWidget(QLabel("Exit Hotkey:"))
        self.exit_hotkey = QLineEdit(self)
        self.exit_hotkey.setText(self.config.get("exit_hotkey", "Ctrl+Q"))
        layout.addWidget(self.exit_hotkey)

        layout.addWidget(QLabel("Font Family:"))
        self.font_family = QFontComboBox(self)
        self.font_family.setCurrentFont(QFont(self.config.get("font_family", "Arial")))
        layout.addWidget(self.font_family)

        layout.addWidget(QLabel("Font Size:"))
        self.font_size = QSpinBox(self)
        self.font_size.setRange(8, 32)
        self.font_size.setValue(self.config.get("font_size", 17))
        layout.addWidget(self.font_size)

        layout.addWidget(QLabel("Menu Button Size:"))
        self.menu_button_size = QSpinBox(self)
        self.menu_button_size.setRange(12, 48)
        self.menu_button_size.setValue(self.config.get("menu_button_size", 22))
        layout.addWidget(self.menu_button_size)

        self.dark_mode_check = QCheckBox("Enable Dark Mode")
        self.dark_mode_check.setChecked(self.config.get("dark_mode", True))
        layout.addWidget(self.dark_mode_check)

        self.apply_button = QPushButton("Apply", self)
        self.apply_button.clicked.connect(self.apply_changes)
        layout.addWidget(self.apply_button)

    def apply_changes(self):
        self.config["save_hotkey"] = self.save_hotkey.text()
        self.config["exit_hotkey"] = self.exit_hotkey.text()
        self.config["font_family"] = self.font_family.currentFont().family()
        self.config["font_size"] = self.font_size.value()
        self.config["menu_button_size"] = self.menu_button_size.value()
        self.config["dark_mode"] = self.dark_mode_check.isChecked()
        save_config(self.config)
        self.accept()

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About ArkNotes")
        layout = QVBoxLayout(self)

        image_label = QLabel()
        image_path = os.path.join(os.path.dirname(__file__), "icon.png")
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            image_label.setPixmap(pixmap.scaledToWidth(96, Qt.SmoothTransformation))
            layout.addWidget(image_label, alignment=Qt.AlignHCenter)
        else:
            image_label.setText("[Image not found]")
            layout.addWidget(image_label, alignment=Qt.AlignHCenter)

        layout.addWidget(QLabel("<b>ArkNotes</b> - Stylish Minimal Text Editor<br>Made with PySide6"), alignment=Qt.AlignHCenter)
        layout.addWidget(QLabel("By Arc360"), alignment=Qt.AlignHCenter)
        ok_btn = QPushButton("OK", self)
        ok_btn.clicked.connect(self.accept)
        layout.addWidget(ok_btn, alignment=Qt.AlignHCenter)

class MenuBarWidget(QWidget):
    def __init__(self, parent, main_window):
        super().__init__(parent)
        self.main_window = main_window
        self.config = main_window.config
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(18, 0, 0, 0)
        self.layout.setSpacing(0)
        self.build_buttons()

    def build_buttons(self):
        for i in reversed(range(self.layout.count())):
            item = self.layout.itemAt(i)
            if item is not None:
                widget = item.widget()
                if widget is not None:
                    widget.setParent(None)
                else:
                    self.layout.removeItem(item)
        font_size = self.config.get("menu_button_size", 22)
        font = QFont("Arial", font_size)
        self.file_btn = QPushButton("File")
        self.edit_btn = QPushButton("Preferences")
        self.about_btn = QPushButton("About")
        for btn in (self.file_btn, self.edit_btn, self.about_btn):
            btn.setFont(font)
            btn.setFlat(True)
            btn.setStyleSheet(self.menu_button_style())
            self.layout.addWidget(btn)
        self.layout.addStretch(1)
        self.file_menu = QMenu(self)
        self.file_menu.addAction(self.main_window.new_action)
        self.file_menu.addAction(self.main_window.open_action)
        self.file_menu.addAction(self.main_window.save_action)
        self.file_menu.addAction(self.main_window.saveas_action)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.main_window.exit_action)

        self.edit_menu = QMenu(self)
        self.edit_menu.addAction(self.main_window.toggle_theme_action)
        self.edit_menu.addAction(self.main_window.preferences_action)

        self.about_menu = QMenu(self)
        self.about_menu.addAction(self.main_window.about_action)

        self.file_btn.clicked.connect(lambda: self.file_menu.exec(self.file_btn.mapToGlobal(QPoint(0, self.file_btn.height()))))
        self.edit_btn.clicked.connect(lambda: self.edit_menu.exec(self.edit_btn.mapToGlobal(QPoint(0, self.edit_btn.height()))))
        self.about_btn.clicked.connect(lambda: self.about_menu.exec(self.about_btn.mapToGlobal(QPoint(0, self.about_btn.height()))))

    def menu_button_style(self):
        dark = self.config.get("dark_mode", True)
        fg = "#ededed" if dark else "#232323"
        font_size = self.config.get("menu_button_size", 22)
        pad = int(font_size * 0.8)
        return f"""
            QPushButton {{ background: transparent; color: {fg}; border: none; padding: 4px {pad}px; font-size: {font_size}px; }}
            QPushButton:hover {{ color: #b6d7ff; }}
        """

    def update_menu_size(self):
        self.build_buttons()

class ArkNotesMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ArkNotes")
        self.setWindowIcon(QIcon.fromTheme("document-edit"))
        self.resize(1200, 800)  # Start at a bigger size
        self.config = load_config()
        self.file_path = None

        self.new_action = QAction("New", self)
        self.new_action.triggered.connect(self.new_file)
        self.open_action = QAction("Open", self)
        self.open_action.triggered.connect(self.open_file)
        self.save_action = QAction("Save", self)
        self.save_action.setShortcut(QKeySequence(self.config.get("save_hotkey", "Ctrl+S")))
        self.save_action.triggered.connect(self.save_file)
        self.saveas_action = QAction("Save As", self)
        self.saveas_action.triggered.connect(self.save_file_as)
        self.toggle_theme_action = QAction("Toggle Dark/Light Mode", self)
        self.toggle_theme_action.triggered.connect(self.toggle_theme)
        self.preferences_action = QAction("Preferences", self)
        self.preferences_action.triggered.connect(self.open_preferences)
        self.about_action = QAction("About", self)
        self.about_action.triggered.connect(self.open_about)
        self.exit_action = QAction("Exit", self)
        self.exit_action.setShortcut(QKeySequence(self.config.get("exit_hotkey", "Ctrl+Q")))
        self.exit_action.triggered.connect(self.close)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(12)

        self.centralWidget().setStyleSheet("background: #18191a;")

        self.menu_bar_box = RoundedBox(
            color="#232323" if self.config["dark_mode"] else "#ededed",
            border="#333333" if self.config["dark_mode"] else "#cccccc",
            radius=12)
        self.menu_bar_box.setFixedHeight(58 + int(self.config.get("menu_button_size", 22) * 0.5))
        menu_bar_layout = QVBoxLayout(self.menu_bar_box)
        menu_bar_layout.setContentsMargins(0,0,0,0)
        self.menu_widget = MenuBarWidget(self.menu_bar_box, self)
        menu_bar_layout.addWidget(self.menu_widget)
        main_layout.addWidget(self.menu_bar_box)

        self.text_box = RoundedBox(
            color="#232323" if self.config["dark_mode"] else "#ededed",
            border="#333333" if self.config["dark_mode"] else "#cccccc",
            radius=12)
        text_layout = QVBoxLayout(self.text_box)
        text_layout.setContentsMargins(8, 8, 8, 8)
        self.text_edit = ArkTextEdit(self.config)
        text_layout.addWidget(self.text_edit)
        main_layout.addWidget(self.text_box, 1)

        # Only create shortcuts ONCE and update their keys later
        self.exit_shortcut = QShortcut(QKeySequence(self.config.get("exit_hotkey", "Ctrl+Q")), self)
        self.exit_shortcut.setContext(Qt.ApplicationShortcut)
        self.exit_shortcut.activated.connect(self.close)
        self.save_shortcut = QShortcut(QKeySequence(self.config.get("save_hotkey", "Ctrl+S")), self)
        self.save_shortcut.setContext(Qt.ApplicationShortcut)
        self.save_shortcut.activated.connect(self.save_file)

        # Add hardcoded zoom in/out shortcuts (unchangeable)
        self.zoom_in_shortcut = QShortcut(QKeySequence("Ctrl++"), self)
        self.zoom_in_shortcut.setContext(Qt.ApplicationShortcut)
        self.zoom_in_shortcut.activated.connect(self.zoom_in)
        self.zoom_in_shortcut2 = QShortcut(QKeySequence("Ctrl+="), self)  # for some keyboards, = is on same key as +
        self.zoom_in_shortcut2.setContext(Qt.ApplicationShortcut)
        self.zoom_in_shortcut2.activated.connect(self.zoom_in)
        self.zoom_out_shortcut = QShortcut(QKeySequence("Ctrl+-"), self)
        self.zoom_out_shortcut.setContext(Qt.ApplicationShortcut)
        self.zoom_out_shortcut.activated.connect(self.zoom_out)

        self._set_unsaved(False)
        self.apply_theme()

    def apply_theme(self):
        dark = self.config["dark_mode"]
        box_bg = "#232323" if dark else "#ededed"
        box_border = "#333333" if dark else "#cccccc"
        fg = "#ededed" if dark else "#232323"
        self.menu_bar_box.bgcolor = QColor(box_bg)
        self.menu_bar_box.border = QColor(box_border)
        self.text_box.bgcolor = QColor(box_bg)
        self.text_box.border = QColor(box_border)
        self.menu_bar_box.setFixedHeight(58 + int(self.config.get("menu_button_size", 22) * 0.5))
        self.menu_bar_box.update()
        self.text_box.update()
        self.text_edit.set_dark_mode(dark)
        self.menu_widget.config = self.config
        self.menu_widget.update_menu_size()
        self._update_hotkeys()
        self.centralWidget().setStyleSheet(
            "background: #18191a;" if dark else "background: #fafbfc;"
        )
        menu_fg = "#ededed" if dark else "#232323"
        menu_bg = "#232323" if dark else "#ededed"
        menu_sel_bg = "#3a7bd5" if dark else "#b6d7ff"
        menu_sel_fg = "#ffffff" if dark else "#232323"
        self.setStyleSheet(self.styleSheet() + f"""
            QMenu {{
                background-color: {menu_bg};
                color: {menu_fg};
                border: 1px solid #555;
                selection-background-color: {menu_sel_bg};
                selection-color: {menu_sel_fg};
                font-size: {self.config.get("menu_button_size",22)}px;
            }}
            QMenu::item:selected {{
                background-color: {menu_sel_bg};
                color: {menu_sel_fg};
            }}
        """)

    def _update_hotkeys(self):
        self.save_action.setShortcut(QKeySequence(self.config.get("save_hotkey", "Ctrl+S")))
        self.save_action.setShortcutContext(Qt.ApplicationShortcut)
        self.save_shortcut.setKey(QKeySequence(self.config.get("save_hotkey", "Ctrl+S")))
        self.exit_action.setShortcut(QKeySequence(self.config.get("exit_hotkey", "Ctrl+Q")))
        self.exit_shortcut.setKey(QKeySequence(self.config.get("exit_hotkey", "Ctrl+Q")))

    def zoom_in(self):
        max_font_size = 72
        if self.config["font_size"] < max_font_size:
            self.config["font_size"] += 1
            save_config(self.config)
            self.text_edit.update_font()
            self.apply_theme()

    def zoom_out(self):
        min_font_size = 8
        if self.config["font_size"] > min_font_size:
            self.config["font_size"] -= 1
            save_config(self.config)
            self.text_edit.update_font()
            self.apply_theme()

    def _set_unsaved(self, unsaved):
        self.text_edit.set_unsaved(unsaved)
        if unsaved:
            if not self.windowTitle().endswith(" *"):
                self.setWindowTitle(self.windowTitle() + " *")
        else:
            self.setWindowTitle("ArkNotes")

    def new_file(self):
        if not self._maybe_save():
            return
        self.file_path = None
        self.text_edit.setPlainText("")
        self._set_unsaved(False)

    def open_file(self):
        if not self._maybe_save():
            return
        file_path, _ = QFileDialog.getOpenFileName(self, "Open File", "",
            "ArkNotes Files (*.arc);;Text Files (*.txt)")
        if file_path:
            with open(file_path, "r", encoding="utf-8") as f:
                self.text_edit.setPlainText(f.read())
            self.file_path = file_path
            self._set_unsaved(False)

    def save_file(self):
        if self.file_path:
            self._save_to_path(self.file_path)
        else:
            self.save_file_as()

    def save_file_as(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save File As", "",
            "ArkNotes Files (*.arc);;Text Files (*.txt)")
        if file_path:
            if not (file_path.endswith(".arc") or file_path.endswith(".txt")):
                file_path += ".arc"
            self._save_to_path(file_path)
            self.file_path = file_path

    def _save_to_path(self, path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.text_edit.toPlainText())
        self._set_unsaved(False)

    def toggle_theme(self):
        self.config["dark_mode"] = not self.config["dark_mode"]
        save_config(self.config)
        self.apply_theme()

    def open_preferences(self):
        dlg = PreferencesDialog(self.config, self)
        if dlg.exec():
            self.text_edit.update_font()
            self.apply_theme()

    def open_about(self):
        dlg = AboutDialog(self)
        dlg.exec()

    def closeEvent(self, event):
        if self._maybe_save():
            event.accept()
        else:
            event.ignore()

    def _maybe_save(self):
        if self.text_edit.is_unsaved():
            msg = QMessageBox(self)
            msg.setWindowTitle("Unsaved Changes")
            msg.setText("You have unsaved changes. Do you want to save before closing?")
            msg.setStandardButtons(QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
            msg.setDefaultButton(QMessageBox.Save)
            ret = msg.exec()
            if ret == QMessageBox.Save:
                self.save_file()
                return not self.text_edit.is_unsaved()  # Only proceed if save succeeded
            elif ret == QMessageBox.Cancel:
                return False
            elif ret == QMessageBox.Discard:
                return True
        return True

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("ArkNotes")
    win = ArkNotesMainWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

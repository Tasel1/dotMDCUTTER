import io
import os
import sys
from typing import List, Optional
from PIL import Image

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor, QFont, QIcon, QKeySequence, QPalette, QPixmap, QShortcut
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListView,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QSplitter,
    QStatusBar,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from .models import PageConfig
from .renderer import MarkdownRenderer
from .themes import THEMES


GLOBAL_DARK_STYLESHEET = """
QMainWindow, QDialog, QFileDialog, QMessageBox {
    background-color: #121214;
    color: #F4F4F5;
}

QWidget {
    color: #F4F4F5;
    font-family: 'Inter', 'Segoe UI', 'Cantarell', 'Noto Sans', sans-serif;
    selection-background-color: #2563EB;
    selection-color: #FFFFFF;
}

QGroupBox {
    border: 1px solid #27272A;
    border-radius: 6px;
    margin-top: 8px;
    font-weight: bold;
    font-size: 11px;
    color: #93C5FD;
    padding-top: 10px;
    background-color: #18181B;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 8px;
    padding: 0 4px;
}

QPushButton, QToolButton {
    background-color: #27272A;
    border: 1px solid #3F3F46;
    color: #F4F4F5;
    border-radius: 5px;
    padding: 6px 12px;
    font-size: 12px;
}
QPushButton:hover, QToolButton:hover {
    background-color: #3F3F46;
    border-color: #52525B;
}
QPushButton:pressed, QToolButton:pressed {
    background-color: #18181B;
    border-color: #3B82F6;
}
QPushButton:disabled, QToolButton:disabled {
    background-color: #1C1C1F;
    color: #52525B;
    border-color: #27272A;
}

QComboBox, QSpinBox, QLineEdit {
    background-color: #18181B;
    border: 1px solid #3F3F46;
    color: #F4F4F5;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 12px;
}
QComboBox:focus, QSpinBox:focus, QLineEdit:focus {
    border-color: #3B82F6;
}
QComboBox QAbstractItemView {
    background-color: #18181B;
    border: 1px solid #3F3F46;
    color: #F4F4F5;
    selection-background-color: #2563EB;
    selection-color: #FFFFFF;
}

QListView, QTreeView, QTableView {
    background-color: #18181B;
    color: #F4F4F5;
    border: 1px solid #27272A;
    border-radius: 4px;
    selection-background-color: #2563EB;
    selection-color: #FFFFFF;
    outline: none;
}
QListView::item, QTreeView::item {
    padding: 4px;
    border-radius: 3px;
    color: #F4F4F5;
}
QListView::item:hover, QTreeView::item:hover {
    background-color: #27272A;
}
QListView::item:selected, QTreeView::item:selected {
    background-color: #2563EB;
    color: #FFFFFF;
}

QHeaderView::section {
    background-color: #27272A;
    color: #93C5FD;
    padding: 5px;
    font-size: 11px;
    font-weight: bold;
    border: 1px solid #18181B;
}

QCheckBox {
    font-size: 11px;
    color: #D4D4D8;
    spacing: 6px;
}
QCheckBox::indicator {
    width: 14px;
    height: 14px;
    border: 1px solid #52525B;
    border-radius: 3px;
    background-color: #18181B;
}
QCheckBox::indicator:checked {
    background-color: #2563EB;
    border-color: #3B82F6;
}

QSlider::groove:horizontal {
    height: 4px;
    background: #27272A;
    border-radius: 2px;
}
QSlider::sub-page:horizontal {
    background: #3B82F6;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    background: #60A5FA;
    border: 1px solid #2563EB;
    width: 14px;
    margin-top: -5px;
    margin-bottom: -5px;
    border-radius: 7px;
}

QScrollBar:vertical {
    background: #18181B;
    width: 10px;
    margin: 0px;
    border-radius: 5px;
}
QScrollBar::handle:vertical {
    background: #3F3F46;
    min-height: 20px;
    border-radius: 5px;
}
QScrollBar::handle:vertical:hover {
    background: #52525B;
}
QScrollBar:horizontal {
    background: #18181B;
    height: 10px;
    margin: 0px;
    border-radius: 5px;
}
QScrollBar::handle:horizontal {
    background: #3F3F46;
    min-width: 20px;
    border-radius: 5px;
}
QScrollBar::handle:horizontal:hover {
    background: #52525B;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
    height: 0px;
}

QToolTip {
    background-color: #27272A;
    color: #F4F4F5;
    border: 1px solid #3F3F46;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 11px;
}

QStatusBar {
    background-color: #18181B;
    color: #A1A1AA;
    border-top: 1px solid #27272A;
}

QMenu {
    background-color: #18181B;
    color: #F4F4F5;
    border: 1px solid #27272A;
    padding: 4px;
}
QMenu::item:selected {
    background-color: #2563EB;
    color: #FFFFFF;
}
"""


def apply_global_dark_theme(app: QApplication):
    """Sets up the Fusion style, full dark QPalette, and comprehensive dark stylesheet."""
    app.setStyle("Fusion")

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#121214"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#F4F4F5"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#18181B"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#202024"))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#27272A"))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#F4F4F5"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#F4F4F5"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#27272A"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#F4F4F5"))
    palette.setColor(QPalette.ColorRole.BrightText, QColor("#EF4444"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#2563EB"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor("#71717A"))
    palette.setColor(QPalette.ColorRole.Dark, QColor("#09090B"))
    palette.setColor(QPalette.ColorRole.Mid, QColor("#27272A"))
    palette.setColor(QPalette.ColorRole.Shadow, QColor("#000000"))

    app.setPalette(palette)
    app.setStyleSheet(GLOBAL_DARK_STYLESHEET)


class MarkdownCutterWindow(QMainWindow):
    def __init__(self, initial_file: Optional[str] = None):
        super().__init__()
        self.setWindowTitle("dotMDCUTTER — Markdown 320x240 Slicer")
        self.resize(1080, 750)
        self.setMinimumSize(850, 600)
        self.setAcceptDrops(True)

        self.current_file_path: Optional[str] = None
        self.markdown_text: str = ""
        self.rendered_pages: List[Image.Image] = []
        self.current_page_idx: int = 0
        self.zoom_factor: int = 2

        self._init_ui()

        if initial_file and os.path.isfile(initial_file):
            self.load_file(initial_file)
        else:
            self._load_sample_markdown()

    def _init_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        # Left control panel
        left_panel = QWidget()
        left_panel.setFixedWidth(340)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)

        # App Title & Version
        title_box = QHBoxLayout()
        title_label = QLabel("dotMDCUTTER")
        title_label.setFont(QFont("Inter, Segoe UI, sans-serif", 16, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #60A5FA;")
        version_label = QLabel("v1.2.0 • Ultra-Crisp & HiDPI")
        version_label.setStyleSheet(
            "color: #71717A; font-size: 11px; padding-top: 5px;"
        )
        title_box.addWidget(title_label)
        title_box.addWidget(version_label)
        title_box.addStretch()
        left_layout.addLayout(title_box)

        # 1. File Input Box
        file_group = QGroupBox("1. Документ Markdown")
        file_layout = QVBoxLayout(file_group)
        file_layout.setSpacing(6)

        self.file_label = QLabel("Файл не выбран (перетащите .md)")
        self.file_label.setStyleSheet("color: #A1A1AA; font-size: 11px;")
        self.file_label.setWordWrap(True)
        file_layout.addWidget(self.file_label)

        btn_browse = QPushButton("Выбрать .md файл...")
        btn_browse.clicked.connect(self._on_browse_file)
        file_layout.addWidget(btn_browse)
        left_layout.addWidget(file_group)

        # 2. Display & Presets
        display_group = QGroupBox("2. Экран и разрешение")
        disp_layout = QVBoxLayout(display_group)
        disp_layout.setSpacing(8)

        preset_row = QHBoxLayout()
        preset_row.addWidget(QLabel("Пресет:"))
        self.combo_preset = QComboBox()
        self.combo_preset.addItems(
            ["320×240 (Альбомная)", "240×320 (Портретная)", "Пользовательское"]
        )
        self.combo_preset.currentIndexChanged.connect(self._on_preset_changed)
        preset_row.addWidget(self.combo_preset)
        disp_layout.addLayout(preset_row)

        dim_row = QHBoxLayout()
        dim_row.addWidget(QLabel("Ширина:"))
        self.spin_width = QSpinBox()
        self.spin_width.setRange(128, 1920)
        self.spin_width.setValue(320)
        self.spin_width.valueChanged.connect(self._on_dimension_changed)
        dim_row.addWidget(self.spin_width)

        dim_row.addWidget(QLabel("Высота:"))
        self.spin_height = QSpinBox()
        self.spin_height.setRange(128, 1920)
        self.spin_height.setValue(240)
        self.spin_height.valueChanged.connect(self._on_dimension_changed)
        dim_row.addWidget(self.spin_height)
        disp_layout.addLayout(dim_row)

        theme_row = QHBoxLayout()
        theme_row.addWidget(QLabel("Тема оформления:"))
        self.combo_theme = QComboBox()
        for t_name in THEMES.keys():
            self.combo_theme.addItem(t_name.capitalize(), t_name)
        self.combo_theme.currentIndexChanged.connect(self._render_preview)
        theme_row.addWidget(self.combo_theme)
        disp_layout.addLayout(theme_row)

        format_row = QHBoxLayout()
        format_row.addWidget(QLabel("Формат фото:"))
        self.combo_format = QComboBox()
        self.combo_format.addItems(["PNG", "JPG", "BMP"])
        format_row.addWidget(self.combo_format)
        disp_layout.addLayout(format_row)

        scale_row = QHBoxLayout()
        scale_row.addWidget(QLabel("Четкость / Масштаб:"))
        self.combo_scale = QComboBox()
        self.combo_scale.addItem("1x — Исходное (320×240, микро-четкость)", 1)
        self.combo_scale.addItem("2x — HiDPI (640×480, повышенная четкость)", 2)
        self.combo_scale.addItem("3x — Ultra (960×720, бритвенная резкость)", 3)
        self.combo_scale.addItem("4x — Retina (1280×960)", 4)
        self.combo_scale.currentIndexChanged.connect(self._render_preview)
        scale_row.addWidget(self.combo_scale)
        disp_layout.addLayout(scale_row)

        left_layout.addWidget(display_group)

        # 3. Typography & Paging
        typo_group = QGroupBox("3. Типографика и поля")
        typo_layout = QVBoxLayout(typo_group)
        typo_layout.setSpacing(8)

        font_row = QHBoxLayout()
        font_row.addWidget(QLabel("Шрифт:"))
        self.spin_font_size = QSpinBox()
        self.spin_font_size.setRange(9, 28)
        self.spin_font_size.setValue(13)
        self.spin_font_size.valueChanged.connect(self._on_font_size_changed)
        font_row.addWidget(self.spin_font_size)
        typo_layout.addLayout(font_row)

        self.slider_font_size = QSlider(Qt.Orientation.Horizontal)
        self.slider_font_size.setRange(9, 28)
        self.slider_font_size.setValue(13)
        self.slider_font_size.valueChanged.connect(self.spin_font_size.setValue)
        typo_layout.addWidget(self.slider_font_size)

        self.chk_footer = QCheckBox("Показывать номер страницы внизу (1/N)")
        self.chk_footer.setChecked(True)
        self.chk_footer.stateChanged.connect(self._render_preview)
        typo_layout.addWidget(self.chk_footer)

        self.chk_hr_pagebreak = QCheckBox("Считать '---' разделителем страниц")
        self.chk_hr_pagebreak.setChecked(False)
        self.chk_hr_pagebreak.stateChanged.connect(self._render_preview)
        typo_layout.addWidget(self.chk_hr_pagebreak)

        left_layout.addWidget(typo_group)

        # 4. Export Group
        export_group = QGroupBox("4. Экспорт")
        export_layout = QVBoxLayout(export_group)
        export_layout.setSpacing(6)

        prefix_row = QHBoxLayout()
        prefix_row.addWidget(QLabel("Префикс:"))
        self.edit_prefix = QLineEdit("page_")
        prefix_row.addWidget(self.edit_prefix)
        export_layout.addLayout(prefix_row)

        self.btn_export = QPushButton("Сохранить все страницы")
        self.btn_export.setStyleSheet(
            "background-color: #2563EB; color: white; font-weight: bold; padding: 10px; border-radius: 6px;"
        )
        self.btn_export.clicked.connect(self._on_export_clicked)
        export_layout.addWidget(self.btn_export)

        left_layout.addWidget(export_group)
        left_layout.addStretch()

        main_layout.addWidget(left_panel)

        # Right Panel: Preview & Navigation
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        # Top toolbar of preview
        top_bar = QHBoxLayout()

        top_bar.addWidget(QLabel("Масштаб:"))
        self.combo_zoom = QComboBox()
        self.combo_zoom.addItems(
            ["100% (1:1 Реальный размер)", "200% (2x Увеличение)", "300% (3x Четко)"]
        )
        self.combo_zoom.setCurrentIndex(1)
        self.combo_zoom.currentIndexChanged.connect(self._on_zoom_changed)
        top_bar.addWidget(self.combo_zoom)

        top_bar.addStretch()

        self.btn_prev = QPushButton("◀ Пред")
        self.btn_prev.clicked.connect(self._prev_page)
        top_bar.addWidget(self.btn_prev)

        self.lbl_page_info = QLabel("Страница 0 из 0")
        self.lbl_page_info.setStyleSheet(
            "font-weight: bold; color: #E4E4E7; padding: 0 8px;"
        )
        top_bar.addWidget(self.lbl_page_info)

        self.btn_next = QPushButton("След ▶")
        self.btn_next.clicked.connect(self._next_page)
        top_bar.addWidget(self.btn_next)

        right_layout.addLayout(top_bar)

        # Screen preview container
        self.scroll_area = QScrollArea()
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_area.setStyleSheet(
            "background-color: #09090B; border: 1px solid #27272A; border-radius: 8px;"
        )

        self.preview_image_label = QLabel()
        self.preview_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_image_label.setStyleSheet(
            "border: 2px solid #3F3F46; border-radius: 4px; background-color: #000000;"
        )
        self.scroll_area.setWidget(self.preview_image_label)
        self.scroll_area.setWidgetResizable(True)

        right_layout.addWidget(self.scroll_area)

        # Page slider at bottom
        slider_row = QHBoxLayout()
        slider_row.addWidget(QLabel("Страница:"))
        self.slider_page = QSlider(Qt.Orientation.Horizontal)
        self.slider_page.setRange(1, 1)
        self.slider_page.setValue(1)
        self.slider_page.valueChanged.connect(self._on_page_slider_changed)
        slider_row.addWidget(self.slider_page)
        right_layout.addLayout(slider_row)

        main_layout.addWidget(right_panel, stretch=1)

        self.statusBar().showMessage(
            "Готово к работе. Выберите файл Markdown для нарезки."
        )

        # Shortcuts
        QShortcut(QKeySequence("Left"), self, self._prev_page)
        QShortcut(QKeySequence("Right"), self, self._next_page)
        QShortcut(QKeySequence("Ctrl+O"), self, self._on_browse_file)
        QShortcut(QKeySequence("Ctrl+S"), self, self._on_export_clicked)

    def _load_sample_markdown(self):
        sample = """# dotMDCUTTER 320x240 🚀
Универсальный инструмент нарезки Markdown на экранчики 320×240.

## Поддержка LaTeX формул 🧮
- Формула Эйнштейна: $E = mc^2$
- Корни квадратного уравнения: $x = \\frac{-b \\pm \\sqrt{D}}{2a}$

Блочный интеграл:
$$
\\int_0^\\infty e^{-x^2} dx = \\frac{\\sqrt{\\pi}}{2}
$$

## Юникод символы и знаки 🔥
- Стрелки: $A \\to B \\implies C$ ✅
- Сравнения: $x \\le 10 \\ne 5 \\pm 0.1$, $\\pi \\approx 3.14159$
- Эмодзи: 💡 ⚡ ⚠️ ⚙️

---page---

## Второй раздел
1. Удобная навигация стрелками клавиатуры
2. Выбор тем: Dark, Light, E-Ink, Amber, Matrix
3. Экспорт в PNG, JPG или BMP

```python
# Пример для микроконтроллера ESP32
import time
print("Экран 320x240 готов!")
```

Перетащите любой свой `.md` файл в это окно!
"""
        self.markdown_text = sample
        self.file_label.setText("Демо-документ (перетащите свой .md файл)")
        self._render_preview()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().lower().endswith((".md", ".markdown", ".txt")):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            filepath = url.toLocalFile()
            if os.path.isfile(filepath):
                self.load_file(filepath)
                break

    def _on_browse_file(self):
        # Open file dialog with internal Qt renderer to enforce dark theme
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите Markdown файл",
            "",
            "Markdown Files (*.md *.markdown *.txt);;All Files (*)",
            options=QFileDialog.Option.DontUseNativeDialog,
        )
        if filepath:
            self.load_file(filepath)

    def load_file(self, filepath: str):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                self.markdown_text = f.read()
            self.current_file_path = filepath
            self.file_label.setText(f"Файл: {os.path.basename(filepath)}")
            self.file_label.setToolTip(filepath)
            self.current_page_idx = 0
            self._render_preview()
            self.statusBar().showMessage(f"Загружен файл: {filepath}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка чтения файла", str(e))

    def _on_preset_changed(self, idx: int):
        if idx == 0:  # 320x240 Landscape
            self.spin_width.setValue(320)
            self.spin_height.setValue(240)
        elif idx == 1:  # 240x320 Portrait
            self.spin_width.setValue(240)
            self.spin_height.setValue(320)

    def _on_dimension_changed(self):
        w = self.spin_width.value()
        h = self.spin_height.value()
        if w == 320 and h == 240:
            self.combo_preset.setCurrentIndex(0)
        elif w == 240 and h == 320:
            self.combo_preset.setCurrentIndex(1)
        else:
            self.combo_preset.setCurrentIndex(2)
        self._render_preview()

    def _on_font_size_changed(self, val: int):
        self.slider_font_size.setValue(val)
        self._render_preview()

    def _on_zoom_changed(self, idx: int):
        self.zoom_factor = idx + 1
        self._update_display_image()

    def _get_current_config(self) -> PageConfig:
        scale_val = (
            self.combo_scale.currentData() if hasattr(self, "combo_scale") else 1
        )
        return PageConfig(
            width=self.spin_width.value(),
            height=self.spin_height.value(),
            base_font_size=self.spin_font_size.value(),
            show_footer=self.chk_footer.isChecked(),
            theme_name=self.combo_theme.currentData() or "dark",
            output_format=self.combo_format.currentText().lower(),
            scale=scale_val or 1,
            hr_as_pagebreak=self.chk_hr_pagebreak.isChecked(),
        )

    def _render_preview(self):
        if not self.markdown_text:
            return

        cfg = self._get_current_config()
        renderer = MarkdownRenderer(cfg)

        from .parser import parse_markdown

        blocks = parse_markdown(
            self.markdown_text, hr_as_pagebreak=self.chk_hr_pagebreak.isChecked()
        )
        pages = renderer.layout_engine.layout_blocks(blocks)
        total = len(pages)

        self.rendered_pages = [renderer.render_page(p, total) for p in pages]

        if self.current_page_idx >= len(self.rendered_pages):
            self.current_page_idx = max(0, len(self.rendered_pages) - 1)

        self.slider_page.blockSignals(True)
        self.slider_page.setRange(1, max(1, total))
        self.slider_page.setValue(self.current_page_idx + 1)
        self.slider_page.blockSignals(False)

        self.btn_export.setText(f"Сохранить все страницы ({total} шт)")
        self._update_display_image()

    def _update_display_image(self):
        if not self.rendered_pages:
            self.preview_image_label.setText("Нет страниц для отображения")
            self.lbl_page_info.setText("Страница 0 из 0")
            return

        total = len(self.rendered_pages)
        self.current_page_idx = max(0, min(self.current_page_idx, total - 1))
        self.lbl_page_info.setText(f"Страница {self.current_page_idx + 1} из {total}")

        pil_img = self.rendered_pages[self.current_page_idx]

        buf = io.BytesIO()
        pil_img.save(buf, format="PNG")
        pix = QPixmap()
        pix.loadFromData(buf.getvalue())

        scale_val = (
            self.combo_scale.currentData() if hasattr(self, "combo_scale") else 1
        )
        scale_val = max(1, scale_val or 1)
        target_w = int(pil_img.width * self.zoom_factor / scale_val)
        target_h = int(pil_img.height * self.zoom_factor / scale_val)
        scaled_pix = pix.scaled(
            target_w,
            target_h,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        self.preview_image_label.setPixmap(scaled_pix)
        self.preview_image_label.setFixedSize(target_w, target_h)

        self.btn_prev.setEnabled(self.current_page_idx > 0)
        self.btn_next.setEnabled(self.current_page_idx < total - 1)

    def _prev_page(self):
        if self.current_page_idx > 0:
            self.current_page_idx -= 1
            self.slider_page.setValue(self.current_page_idx + 1)
            self._update_display_image()

    def _next_page(self):
        if self.current_page_idx < len(self.rendered_pages) - 1:
            self.current_page_idx += 1
            self.slider_page.setValue(self.current_page_idx + 1)
            self._update_display_image()

    def _on_page_slider_changed(self, val: int):
        new_idx = val - 1
        if 0 <= new_idx < len(self.rendered_pages) and new_idx != self.current_page_idx:
            self.current_page_idx = new_idx
            self._update_display_image()

    def _on_export_clicked(self):
        if not self.markdown_text:
            QMessageBox.warning(self, "Нет данных", "Сначала откройте Markdown файл.")
            return

        # Open directory chooser with internal Qt renderer to enforce dark theme
        out_dir = QFileDialog.getExistingDirectory(
            self,
            "Выберите папку для сохранения нарезанных фото",
            os.path.dirname(self.current_file_path) if self.current_file_path else "",
            options=QFileDialog.Option.DontUseNativeDialog,
        )
        if not out_dir:
            return

        cfg = self._get_current_config()
        renderer = MarkdownRenderer(cfg)

        try:
            prefix = self.edit_prefix.text().strip() or "page_"
            saved = renderer.export_images(self.markdown_text, out_dir, prefix=prefix)
            self.statusBar().showMessage(
                f"Экспорт завершен: {len(saved)} фото сохранены в {out_dir}"
            )
            QMessageBox.information(
                self,
                "Экспорт успешно завершен",
                f"Успешно нарезано и сохранено {len(saved)} изображений {cfg.width}×{cfg.height} в папку:\n{out_dir}",
            )
        except Exception as e:
            QMessageBox.critical(
                self, "Ошибка экспорта", f"Не удалось сохранить изображения:\n{e}"
            )


def run_gui(initial_file: Optional[str] = None) -> int:
    app = QApplication(sys.argv)
    apply_global_dark_theme(app)
    window = MarkdownCutterWindow(initial_file)
    window.show()
    return app.exec()

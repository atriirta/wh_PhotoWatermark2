import sys
import os
import json

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QListWidget, QLineEdit, QFrame, QFileDialog,
    QSlider, QColorDialog, QFontComboBox, QSpinBox, QGridLayout, QFormLayout,
    QMessageBox, QSizePolicy, QGroupBox, QRadioButton, QCheckBox, QListWidgetItem,
    QDialog
)
from PyQt6.QtGui import (
    QPixmap, QPainter, QColor, QFont, QScreen, QIcon, QDragEnterEvent, QDropEvent,
    QPainterPath, QPainterPathStroker, QBrush, QPen
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QRectF, QSize

class InteractiveLabel(QLabel):
    mouse_drag_signal = pyqtSignal(int, int)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_dragging = False
        self.last_pos = None
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
            self.last_pos = event.pos()
    def mouseMoveEvent(self, event):
        if self.is_dragging:
            delta = event.pos() - self.last_pos
            self.last_pos = event.pos()
            self.mouse_drag_signal.emit(delta.x(), delta.y())
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = False
            self.last_pos = None

class TemplateManagerDialog(QDialog):
    template_selected = pyqtSignal(dict)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("模板管理")
        self.setMinimumSize(400, 300)
        
        self.templates_file = "templates.json"
        self.templates = self.load_templates_from_file()

        layout = QVBoxLayout(self)
        self.template_list = QListWidget()
        self.populate_template_list()
        layout.addWidget(self.template_list)
        
        save_group = QGroupBox("保存当前设置为新模板")
        save_layout = QHBoxLayout()
        self.template_name_input = QLineEdit()
        self.template_name_input.setPlaceholderText("输入新模板名称...")
        btn_save = QPushButton("保存")
        save_layout.addWidget(self.template_name_input)
        save_layout.addWidget(btn_save)
        save_group.setLayout(save_layout)
        layout.addWidget(save_group)

        buttons_layout = QHBoxLayout()
        btn_load = QPushButton("加载选中模板")
        btn_delete = QPushButton("删除选中模板")
        buttons_layout.addStretch()
        buttons_layout.addWidget(btn_load)
        buttons_layout.addWidget(btn_delete)
        layout.addLayout(buttons_layout)
        
        btn_save.clicked.connect(self.save_current_template)
        btn_load.clicked.connect(self.load_selected_template)
        btn_delete.clicked.connect(self.delete_selected_template)
        self.template_list.itemDoubleClicked.connect(self.load_selected_template)

    def load_templates_from_file(self):
        if os.path.exists(self.templates_file):
            try:
                with open(self.templates_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载模板文件失败: {e}")
        return {}

    def save_templates_to_file(self):
        try:
            with open(self.templates_file, 'w', encoding='utf-8') as f:
                json.dump(self.templates, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"保存模板文件失败: {e}")

    def populate_template_list(self):
        self.template_list.clear()
        self.template_list.addItems(sorted(self.templates.keys()))

    def save_current_template(self):
        name = self.template_name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "名称无效", "请输入一个模板名称。")
            return
        if name in self.templates:
            reply = QMessageBox.question(self, "模板已存在", f"名为 '{name}' 的模板已存在。要覆盖它吗？")
            if reply == QMessageBox.StandardButton.No:
                return
        
        main_window = self.parent()
        current_settings = main_window.get_current_settings_as_dict()
        
        self.templates[name] = current_settings
        self.save_templates_to_file()
        self.populate_template_list()
        self.template_name_input.clear()
        QMessageBox.information(self, "成功", f"模板 '{name}' 已保存。")

    def load_selected_template(self):
        selected_item = self.template_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "未选择", "请先从列表中选择一个模板。")
            return
        
        name = selected_item.text()
        settings_dict = self.templates.get(name)
        
        if settings_dict:
            self.template_selected.emit(settings_dict)
            self.accept()

    def delete_selected_template(self):
        selected_item = self.template_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "未选择", "请先从列表中选择一个模板。")
            return
        
        name = selected_item.text()
        reply = QMessageBox.question(self, "确认删除", f"确定要删除模板 '{name}' 吗？此操作无法撤销。")
        
        if reply == QMessageBox.StandardButton.Yes:
            if name in self.templates:
                del self.templates[name]
                self.save_templates_to_file()
                self.populate_template_list()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("图片加水印工具 WatermarkApp")
        self.setAcceptDrops(True)
        self.init_ui_size()
        self.settings_file = "settings.json"
        self.current_image_path = None
        self.original_pixmap = None
        self.SUPPORTED_FORMATS = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff')

        # Default state variables
        self.watermark_position = (Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight)
        self.watermark_offset = QPoint(0, 0)
        self.watermark_rotation = 0
        self.watermark_mode = "text"
        self.text_watermark_text = "© Your Name"
        self.text_watermark_font = QFont("Arial", 32)
        self.text_watermark_color = QColor(255, 255, 255, 128)
        self.text_watermark_shadow_enabled = True
        self.text_watermark_outline_enabled = False
        self.image_watermark_pixmap = None
        self.image_watermark_path = ""
        self.image_watermark_opacity = 0.5
        self.image_watermark_scale = 15
        self.export_naming_mode = "suffix"
        self.export_naming_text = "_watermarked"
        self.export_format = "PNG"
        self.export_jpeg_quality = 95
        self.export_resize_enabled = False
        self.export_resize_mode = "percentage"
        self.export_resize_value = 100

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        left_panel = self.create_left_panel()
        center_panel = self.create_center_panel()
        right_panel = self.create_right_panel()
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(center_panel, 3)
        main_layout.addWidget(right_panel, 2)
        
        self.load_settings()

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls(): event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        paths = []
        for url in urls:
            path = url.toLocalFile()
            if os.path.isdir(path):
                for entry in os.scandir(path):
                    if entry.is_file() and entry.name.lower().endswith(self.SUPPORTED_FORMATS):
                        paths.append(entry.path)
            elif os.path.isfile(path) and path.lower().endswith(self.SUPPORTED_FORMATS):
                paths.append(path)
        if paths: self.add_images_to_list(paths)

    def closeEvent(self, event):
        self.save_settings()
        event.accept()

    def get_current_settings_as_dict(self):
        return {
            "watermark_mode": self.watermark_mode,
            "text_watermark": {
                "text": self.text_watermark_text, "font_family": self.text_watermark_font.family(),
                "font_size": self.text_watermark_font.pointSize(), "font_bold": self.text_watermark_font.bold(),
                "font_italic": self.text_watermark_font.italic(), "color_hex_argb": self.text_watermark_color.name(QColor.NameFormat.HexArgb),
                "shadow_enabled": self.text_watermark_shadow_enabled, "outline_enabled": self.text_watermark_outline_enabled,
            },
            "image_watermark": { "path": self.image_watermark_path, "opacity": self.image_watermark_opacity, "scale": self.image_watermark_scale, },
            "general": { "position_flag": int(self.watermark_position), "rotation": self.watermark_rotation, },
            "export": {
                "naming_mode": self.export_naming_mode, "naming_text": self.export_naming_text,
                "format": self.export_format, "jpeg_quality": self.export_jpeg_quality,
                "resize_enabled": self.export_resize_enabled, "resize_mode": self.export_resize_mode, "resize_value": self.export_resize_value
            }
        }
    
    def apply_settings_from_dict(self, settings):
        try:
            self.watermark_mode = settings.get("watermark_mode", self.watermark_mode)
            text_settings = settings.get("text_watermark", {})
            self.text_watermark_text = text_settings.get("text", self.text_watermark_text)
            self.text_watermark_font = QFont(text_settings.get("font_family", self.text_watermark_font.family()), text_settings.get("font_size", self.text_watermark_font.pointSize()))
            self.text_watermark_font.setBold(text_settings.get("font_bold", self.text_watermark_font.bold()))
            self.text_watermark_font.setItalic(text_settings.get("font_italic", self.text_watermark_font.italic()))
            self.text_watermark_color = QColor(text_settings.get("color_hex_argb", self.text_watermark_color.name(QColor.NameFormat.HexArgb)))
            self.text_watermark_shadow_enabled = text_settings.get("shadow_enabled", self.text_watermark_shadow_enabled)
            self.text_watermark_outline_enabled = text_settings.get("outline_enabled", self.text_watermark_outline_enabled)

            image_settings = settings.get("image_watermark", {})
            self.image_watermark_path = image_settings.get("path", self.image_watermark_path)
            if self.image_watermark_path and os.path.exists(self.image_watermark_path): self.image_watermark_pixmap = QPixmap(self.image_watermark_path)
            else: self.image_watermark_pixmap = None
            self.image_watermark_opacity = image_settings.get("opacity", self.image_watermark_opacity)
            self.image_watermark_scale = image_settings.get("scale", self.image_watermark_scale)

            general_settings = settings.get("general", {})
            self.watermark_position = Qt.AlignmentFlag(general_settings.get("position_flag", int(self.watermark_position)))
            self.watermark_rotation = general_settings.get("rotation", self.watermark_rotation)

            export_settings = settings.get("export", {})
            self.export_naming_mode = export_settings.get("naming_mode", self.export_naming_mode)
            self.export_naming_text = export_settings.get("naming_text", self.export_naming_text)
            self.export_format = export_settings.get("format", self.export_format)
            self.export_jpeg_quality = export_settings.get("jpeg_quality", self.export_jpeg_quality)
            self.export_resize_enabled = export_settings.get("resize_enabled", self.export_resize_enabled)
            self.export_resize_mode = export_settings.get("resize_mode", self.export_resize_mode)
            self.export_resize_value = export_settings.get("resize_value", self.export_resize_value)
        except Exception as e:
            print(f"应用设置时出错: {e}")

        self.update_ui_from_settings()
        self.update_display()

    def save_settings(self):
        settings = self.get_current_settings_as_dict()
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f: json.dump(settings, f, indent=4, ensure_ascii=False)
        except Exception as e: print(f"无法保存设置: {e}")

    def load_settings(self):
        if not os.path.exists(self.settings_file):
            self.update_ui_from_settings()
            return
        
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f: settings = json.load(f)
            self.apply_settings_from_dict(settings)
        except Exception as e:
            print(f"无法加载设置: {e}")
            self.update_ui_from_settings()
    
    def update_ui_from_settings(self):
        self.radio_mode_text.setChecked(self.watermark_mode == "text")
        self.radio_mode_image.setChecked(self.watermark_mode == "image")
        self.watermark_text_input.setText(self.text_watermark_text)
        self.font_combo.setCurrentFont(self.text_watermark_font)
        self.check_bold.setChecked(self.text_watermark_font.bold())
        self.check_italic.setChecked(self.text_watermark_font.italic())
        self.check_shadow.setChecked(self.text_watermark_shadow_enabled)
        self.check_outline.setChecked(self.text_watermark_outline_enabled)
        self.font_size_spinbox.setValue(self.text_watermark_font.pointSize())
        self.opacity_slider.setValue(self.text_watermark_color.alpha())
        self.update_color_preview()
        if self.image_watermark_pixmap and not self.image_watermark_pixmap.isNull(): self.image_path_label.setText(os.path.basename(self.image_watermark_path))
        else: self.image_path_label.setText("未选择图片")
        self.image_scale_slider.setValue(self.image_watermark_scale)
        self.image_opacity_slider.setValue(int(self.image_watermark_opacity * 100))
        self.rotation_slider.setValue(self.watermark_rotation)
        if self.export_naming_mode == "suffix": self.radio_name_suffix.setChecked(True)
        elif self.export_naming_mode == "prefix": self.radio_name_prefix.setChecked(True)
        else: self.radio_name_original.setChecked(True)
        self.export_naming_input.setText(self.export_naming_text)
        self.radio_format_png.setChecked(self.export_format == "PNG")
        self.radio_format_jpeg.setChecked(self.export_format == "JPEG")
        self.jpeg_quality_slider.setValue(self.export_jpeg_quality)
        self.resize_group.setChecked(self.export_resize_enabled)
        if self.export_resize_mode == "percentage": self.radio_resize_percent.setChecked(True)
        elif self.export_resize_mode == "width": self.radio_resize_width.setChecked(True)
        elif self.export_resize_mode == "height": self.radio_resize_height.setChecked(True)
        self.resize_value_spinbox.setValue(self.export_resize_value)
        self.on_watermark_mode_changed()
        self.on_format_changed()
        self.on_naming_changed()
        self.on_resize_enabled_toggled(self.export_resize_enabled)
        
    def init_ui_size(self):
        screen = QApplication.primaryScreen()
        if not screen: self.setGeometry(100, 100, 1200, 700); return
        available_size = screen.availableGeometry(); DEFAULT_WIDTH, DEFAULT_HEIGHT = 1280, 720
        initial_width = min(DEFAULT_WIDTH, int(available_size.width() * 0.9)); initial_height = min(DEFAULT_HEIGHT, int(available_size.height() * 0.9))
        self.resize(initial_width, initial_height)
        frame_geom = self.frameGeometry(); center_point = available_size.center(); frame_geom.moveCenter(center_point); self.move(frame_geom.topLeft())
    
    def create_left_panel(self):
        left_frame = QFrame(); left_frame.setFrameShape(QFrame.Shape.StyledPanel); layout = QVBoxLayout(left_frame); button_layout = QHBoxLayout()
        self.btn_import_images = QPushButton("导入图片"); self.btn_import_folder = QPushButton("导入文件夹")
        button_layout.addWidget(self.btn_import_images); button_layout.addWidget(self.btn_import_folder)
        list_label = QLabel("图片列表"); self.image_list_widget = QListWidget(); self.image_list_widget.setIconSize(QSize(80, 80)); self.image_list_widget.setSpacing(5)
        layout.addLayout(button_layout); layout.addWidget(list_label); layout.addWidget(self.image_list_widget)
        self.btn_import_images.clicked.connect(self.open_image_files); self.btn_import_folder.clicked.connect(self.open_image_folder)
        self.image_list_widget.currentItemChanged.connect(self.on_current_item_changed)
        return left_frame
    
    def create_center_panel(self):
        center_frame = QFrame(); center_frame.setFrameShape(QFrame.Shape.StyledPanel); layout = QVBoxLayout(center_frame)
        self.preview_label = InteractiveLabel("图片预览区"); self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("border: 2px dashed #aaa;"); self.preview_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self.preview_label.mouse_drag_signal.connect(self.on_watermark_drag); layout.addWidget(self.preview_label)
        return center_frame
    
    def create_right_panel(self):
        right_frame = QFrame(); right_frame.setFrameShape(QFrame.Shape.StyledPanel); main_layout = QVBoxLayout(right_frame)
        mode_group = QGroupBox("水印类型"); mode_layout = QHBoxLayout(); self.radio_mode_text = QRadioButton("文字"); self.radio_mode_text.setChecked(True)
        self.radio_mode_image = QRadioButton("图片"); self.radio_mode_text.toggled.connect(self.on_watermark_mode_changed); mode_layout.addWidget(self.radio_mode_text); mode_layout.addWidget(self.radio_mode_image)
        mode_group.setLayout(mode_layout); main_layout.addWidget(mode_group)
        self.text_watermark_group = QGroupBox("文字水印设置"); text_form_layout = QFormLayout()
        self.watermark_text_input = QLineEdit(self.text_watermark_text); self.watermark_text_input.textChanged.connect(self.on_text_changed); text_form_layout.addRow("文本内容:", self.watermark_text_input)
        self.font_combo = QFontComboBox(); self.font_combo.setCurrentFont(self.text_watermark_font); self.font_combo.currentFontChanged.connect(self.on_font_changed); text_form_layout.addRow("字体:", self.font_combo)
        style_layout = QHBoxLayout(); self.check_bold = QCheckBox("粗体"); self.check_italic = QCheckBox("斜体"); self.check_shadow = QCheckBox("阴影"); self.check_outline = QCheckBox("描边")
        self.check_bold.toggled.connect(self.on_font_style_changed); self.check_italic.toggled.connect(self.on_font_style_changed); self.check_shadow.toggled.connect(self.on_shadow_changed); self.check_outline.toggled.connect(self.on_outline_changed)
        style_layout.addWidget(self.check_bold); style_layout.addWidget(self.check_italic); style_layout.addWidget(self.check_shadow); style_layout.addWidget(self.check_outline)
        text_form_layout.addRow("样式:", style_layout)
        self.font_size_spinbox = QSpinBox(); self.font_size_spinbox.setRange(8, 200); self.font_size_spinbox.setValue(self.text_watermark_font.pointSize()); self.font_size_spinbox.valueChanged.connect(self.on_font_size_changed); text_form_layout.addRow("大小:", self.font_size_spinbox)
        color_layout = QHBoxLayout(); self.btn_color = QPushButton("选择颜色"); self.btn_color.clicked.connect(self.on_color_clicked); self.color_preview = QFrame(); self.color_preview.setFixedSize(24, 24); self.color_preview.setFrameShape(QFrame.Shape.Box); self.color_preview.setAutoFillBackground(True); color_layout.addWidget(self.btn_color); color_layout.addWidget(self.color_preview); text_form_layout.addRow("颜色:", color_layout)
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal); self.opacity_slider.setRange(0, 255); self.opacity_slider.setValue(self.text_watermark_color.alpha()); self.opacity_slider.valueChanged.connect(self.on_opacity_changed); text_form_layout.addRow("透明度:", self.opacity_slider)
        self.text_watermark_group.setLayout(text_form_layout); main_layout.addWidget(self.text_watermark_group)
        self.image_watermark_group = QGroupBox("图片水印设置"); image_form_layout = QFormLayout()
        self.btn_select_image = QPushButton("选择图片..."); self.btn_select_image.clicked.connect(self.on_select_image_watermark); self.image_path_label = QLabel("未选择图片"); self.image_path_label.setStyleSheet("color: gray;")
        self.image_scale_label = QLabel(f"缩放: {self.image_watermark_scale}%"); self.image_scale_slider = QSlider(Qt.Orientation.Horizontal); self.image_scale_slider.setRange(1, 100); self.image_scale_slider.setValue(self.image_watermark_scale); self.image_scale_slider.valueChanged.connect(self.on_image_scale_changed)
        self.image_opacity_label = QLabel(f"透明度: {int(self.image_watermark_opacity * 100)}%"); self.image_opacity_slider = QSlider(Qt.Orientation.Horizontal); self.image_opacity_slider.setRange(0, 100); self.image_opacity_slider.setValue(int(self.image_watermark_opacity * 100)); self.image_opacity_slider.valueChanged.connect(self.on_image_opacity_changed)
        image_form_layout.addRow(self.btn_select_image, self.image_path_label); image_form_layout.addRow(self.image_scale_label, self.image_scale_slider); image_form_layout.addRow(self.image_opacity_label, self.image_opacity_slider)
        self.image_watermark_group.setLayout(image_form_layout); main_layout.addWidget(self.image_watermark_group)
        position_group = QGroupBox("通用设置"); position_layout = QVBoxLayout(); position_layout.addWidget(QLabel("位置:"))
        position_grid = QGridLayout(); positions = [(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft, "↖"), (Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter, "↑"), (Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight, "↗"),(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, "←"), (Qt.AlignmentFlag.AlignCenter, "■"), (Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, "→"),(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft, "↙"), (Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter, "↓"), (Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight, "↘"),]
        for i, (pos, text) in enumerate(positions):
            row, col = i // 3, i % 3; btn = QPushButton(text); btn.clicked.connect(lambda _, p=pos: self.set_grid_position(p)); position_grid.addWidget(btn, row, col)
        position_layout.addLayout(position_grid)
        rotation_layout = QHBoxLayout(); self.rotation_label = QLabel(f"旋转: {self.watermark_rotation}°"); self.rotation_slider = QSlider(Qt.Orientation.Horizontal); self.rotation_slider.setRange(-180, 180); self.rotation_slider.setValue(self.watermark_rotation); self.rotation_slider.valueChanged.connect(self.on_rotation_changed)
        btn_reset_rotation = QPushButton("归零"); btn_reset_rotation.clicked.connect(self.on_rotation_reset); rotation_layout.addWidget(self.rotation_label); rotation_layout.addWidget(self.rotation_slider); rotation_layout.addWidget(btn_reset_rotation)
        position_layout.addLayout(rotation_layout)
        btn_manage_templates = QPushButton("管理模板..."); btn_manage_templates.clicked.connect(self.open_template_manager)
        position_layout.addWidget(btn_manage_templates)
        position_group.setLayout(position_layout); main_layout.addWidget(position_group)
        main_layout.addStretch()
        export_group = QGroupBox("导出设置"); export_layout = QVBoxLayout()
        naming_layout = QFormLayout(); self.radio_name_suffix = QRadioButton("添加后缀"); self.radio_name_suffix.setChecked(True); self.radio_name_prefix = QRadioButton("添加前缀"); self.radio_name_original = QRadioButton("保留原名"); self.export_naming_input = QLineEdit(self.export_naming_text)
        self.radio_name_suffix.toggled.connect(self.on_naming_changed); self.radio_name_prefix.toggled.connect(self.on_naming_changed); self.radio_name_original.toggled.connect(self.on_naming_changed); self.export_naming_input.textChanged.connect(self.on_naming_text_changed)
        naming_layout.addRow(self.radio_name_suffix, self.export_naming_input); naming_layout.addRow(self.radio_name_prefix); naming_layout.addRow(self.radio_name_original); export_layout.addLayout(naming_layout)
        format_layout = QHBoxLayout(); self.radio_format_png = QRadioButton("PNG (推荐)"); self.radio_format_png.setChecked(True); self.radio_format_jpeg = QRadioButton("JPEG"); self.radio_format_png.toggled.connect(self.on_format_changed)
        format_layout.addWidget(QLabel("格式:")); format_layout.addWidget(self.radio_format_png); format_layout.addWidget(self.radio_format_jpeg); export_layout.addLayout(format_layout)
        self.jpeg_quality_widget = QWidget(); jpeg_layout = QHBoxLayout(self.jpeg_quality_widget); jpeg_layout.setContentsMargins(0, 0, 0, 0); self.jpeg_quality_label = QLabel(f"质量: {self.export_jpeg_quality}")
        self.jpeg_quality_slider = QSlider(Qt.Orientation.Horizontal); self.jpeg_quality_slider.setRange(0, 100); self.jpeg_quality_slider.setValue(self.export_jpeg_quality); self.jpeg_quality_slider.valueChanged.connect(self.on_jpeg_quality_changed)
        jpeg_layout.addWidget(self.jpeg_quality_label); jpeg_layout.addWidget(self.jpeg_quality_slider); export_layout.addWidget(self.jpeg_quality_widget)
        self.resize_group = QGroupBox("调整尺寸 (可选)"); self.resize_group.setCheckable(True); self.resize_group.setChecked(self.export_resize_enabled)
        self.resize_group.toggled.connect(self.on_resize_enabled_toggled)
        resize_layout = QVBoxLayout(); self.radio_resize_percent = QRadioButton("按百分比"); self.radio_resize_percent.setChecked(True); self.radio_resize_width = QRadioButton("按宽度 (像素)"); self.radio_resize_height = QRadioButton("按高度 (像素)")
        self.radio_resize_percent.toggled.connect(self.on_resize_mode_changed); self.radio_resize_width.toggled.connect(self.on_resize_mode_changed); self.radio_resize_height.toggled.connect(self.on_resize_mode_changed)
        self.resize_value_spinbox = QSpinBox(); self.resize_value_spinbox.setRange(1, 10000); self.resize_value_spinbox.setValue(self.export_resize_value); self.resize_value_spinbox.valueChanged.connect(self.on_resize_value_changed)
        resize_options_layout = QHBoxLayout(); resize_options_layout.addWidget(self.radio_resize_percent); resize_options_layout.addWidget(self.radio_resize_width); resize_options_layout.addWidget(self.radio_resize_height)
        resize_layout.addLayout(resize_options_layout); resize_layout.addWidget(self.resize_value_spinbox)
        self.resize_group.setLayout(resize_layout); export_layout.addWidget(self.resize_group)
        export_group.setLayout(export_layout); main_layout.addWidget(export_group)
        self.btn_export = QPushButton("导出所有图片"); self.btn_export.clicked.connect(self.export_images); main_layout.addWidget(self.btn_export)
        return right_frame
    
    def open_template_manager(self):
        dialog = TemplateManagerDialog(self)
        dialog.template_selected.connect(self.apply_settings_from_dict)
        dialog.exec()

    def on_watermark_mode_changed(self):
        self.watermark_mode = "image" if self.radio_mode_image.isChecked() else "text"
        self.text_watermark_group.setVisible(self.watermark_mode == "text")
        self.image_watermark_group.setVisible(self.watermark_mode == "image")
        self.update_display()
    
    def on_text_changed(self, text):
        self.text_watermark_text = text
        self.update_display()
    
    def on_font_changed(self, font):
        self.text_watermark_font.setFamily(font.family())
        self.update_display()

    def on_font_style_changed(self):
        self.text_watermark_font.setBold(self.check_bold.isChecked())
        self.text_watermark_font.setItalic(self.check_italic.isChecked())
        self.update_display()
        
    def on_shadow_changed(self, is_checked):
        self.text_watermark_shadow_enabled = is_checked
        self.update_display()

    def on_outline_changed(self, is_checked):
        self.text_watermark_outline_enabled = is_checked
        self.update_display()
    
    def on_font_size_changed(self, size):
        self.text_watermark_font.setPointSize(size)
        self.update_display()

    def on_color_clicked(self):
        color = QColorDialog.getColor(self.text_watermark_color, self, "选择水印颜色")
        if color.isValid():
            alpha = self.text_watermark_color.alpha()
            color.setAlpha(alpha)
            self.text_watermark_color = color
            self.update_color_preview()
            self.update_display()
    
    def on_opacity_changed(self, value):
        self.text_watermark_color.setAlpha(value)
        self.update_color_preview()
        self.update_display()
    
    def on_select_image_watermark(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择水印图片", "", "图片文件 (*.png *.jpg *.jpeg)")
        if file_path:
            self.image_watermark_path = file_path
            pixmap = QPixmap(file_path)
            if pixmap.isNull():
                self.image_path_label.setText("加载失败!")
                self.image_watermark_pixmap = None
            else:
                self.image_watermark_pixmap = pixmap
                self.image_path_label.setText(os.path.basename(file_path))
            self.update_display()
    
    def on_image_scale_changed(self, value):
        self.image_watermark_scale = value
        self.image_scale_label.setText(f"缩放: {value}%")
        self.update_display()

    def on_image_opacity_changed(self, value):
        self.image_watermark_opacity = value / 100.0
        self.image_opacity_label.setText(f"透明度: {value}%")
        self.update_display()

    def on_rotation_changed(self, angle):
        self.watermark_rotation = angle
        self.rotation_label.setText(f"旋转: {angle}°")
        self.update_display()
    
    def on_rotation_reset(self):
        self.rotation_slider.setValue(0)
    
    def set_grid_position(self, position):
        self.watermark_position = position
        self.watermark_offset = QPoint(0, 0)
        self.update_display()
    
    def on_watermark_drag(self, dx, dy):
        if self.original_pixmap is None or self.preview_label.pixmap() is None or self.preview_label.pixmap().isNull():
            return
        
        scaled_pixmap_size = self.preview_label.pixmap().size()
        original_pixmap_size = self.original_pixmap.size()
        
        if scaled_pixmap_size.width() == 0 or scaled_pixmap_size.height() == 0:
            return

        scale_ratio_x = original_pixmap_size.width() / scaled_pixmap_size.width()
        scale_ratio_y = original_pixmap_size.height() / scaled_pixmap_size.height()

        self.watermark_offset += QPoint(int(dx * scale_ratio_x), int(dy * scale_ratio_y))
        self.update_display()

    def update_color_preview(self):
        palette = self.color_preview.palette()
        palette.setColor(self.color_preview.backgroundRole(), self.text_watermark_color)
        self.color_preview.setPalette(palette)

    def open_image_files(self, *args, **kwargs):
        file_filter = f"图片文件 ({' '.join(['*' + ext for ext in self.SUPPORTED_FORMATS])})"
        file_paths, _ = QFileDialog.getOpenFileNames(self, "选择一个或多个图片文件", "", file_filter)
        if file_paths:
            self.add_images_to_list(file_paths)

    def open_image_folder(self, *args, **kwargs):
        folder_path = QFileDialog.getExistingDirectory(self, "选择包含图片的文件夹")
        if folder_path:
            image_paths = [entry.path for entry in os.scandir(folder_path) if entry.is_file() and entry.name.lower().endswith(self.SUPPORTED_FORMATS)]
            if image_paths:
                self.add_images_to_list(image_paths)
            else:
                QMessageBox.information(self, "没有图片", "选择的文件夹中没有找到支持的图片格式。")

    def add_images_to_list(self, file_paths):
        current_items_paths = set(self.image_list_widget.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.image_list_widget.count()))
        new_paths = [path for path in file_paths if path not in current_items_paths]
        for path in new_paths:
            try:
                pixmap = QPixmap(path)
                thumbnail = pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                icon = QIcon(thumbnail)
                list_item = QListWidgetItem(icon, os.path.basename(path))
                list_item.setData(Qt.ItemDataRole.UserRole, path)
                self.image_list_widget.addItem(list_item)
            except Exception as e:
                print(f"为 {path} 创建缩略图失败: {e}")

    def on_current_item_changed(self, current_item, previous_item):
        if current_item is None:
            self.preview_label.clear()
            self.preview_label.setText("图片预览区")
            self.current_image_path = None
            self.original_pixmap = None
            return
        self.current_image_path = current_item.data(Qt.ItemDataRole.UserRole)
        self.original_pixmap = QPixmap(self.current_image_path)
        if self.original_pixmap.isNull():
            self.preview_label.clear()
            self.preview_label.setText("无法加载图片")
            self.original_pixmap = None
            return
        self.watermark_offset = QPoint(0, 0)
        self.update_display()
    
    def apply_watermark(self, pixmap):
        if pixmap.isNull(): return pixmap
        watermarked_pixmap = pixmap.copy()
        painter = QPainter(watermarked_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        padding = 10
        base_x, base_y = 0, 0
        
        painter.save()
        try:
            if self.watermark_mode == "text":
                painter.setFont(self.text_watermark_font)
                metrics = painter.fontMetrics()
                text_rect = metrics.boundingRect(self.text_watermark_text)
                text_width, text_height = text_rect.width(), text_rect.height()
                if self.watermark_position & Qt.AlignmentFlag.AlignLeft: base_x = padding
                elif self.watermark_position & Qt.AlignmentFlag.AlignRight: base_x = pixmap.width() - text_width - padding
                elif self.watermark_position & Qt.AlignmentFlag.AlignHCenter: base_x = (pixmap.width() - text_width) // 2
                if self.watermark_position & Qt.AlignmentFlag.AlignTop: base_y = padding
                elif self.watermark_position & Qt.AlignmentFlag.AlignBottom: base_y = pixmap.height() - text_height - padding
                elif self.watermark_position & Qt.AlignmentFlag.AlignVCenter: base_y = (pixmap.height() - text_height) // 2
                final_x, final_y = base_x + self.watermark_offset.x(), base_y + self.watermark_offset.y()
                center_x, center_y = final_x + text_width / 2, final_y + text_height / 2
                painter.translate(center_x, center_y)
                painter.rotate(self.watermark_rotation)
                text_path = QPainterPath()
                text_path.addText(int(-text_width/2), int(text_height/2 - metrics.descent()), self.text_watermark_font, self.text_watermark_text)
                if self.text_watermark_shadow_enabled:
                    shadow_offset = QPoint(2, 2)
                    shadow_color = QColor(0, 0, 0, 70)
                    painter.save()
                    painter.translate(shadow_offset)
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.setBrush(shadow_color)
                    painter.drawPath(text_path)
                    painter.restore()
                if self.text_watermark_outline_enabled:
                    stroker = QPainterPathStroker()
                    stroker.setWidth(2)
                    stroker.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
                    outline_path = stroker.createStroke(text_path)
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.setBrush(QColor(0,0,0))
                    painter.drawPath(outline_path)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(self.text_watermark_color)
                painter.drawPath(text_path)
            elif self.watermark_mode == "image" and self.image_watermark_pixmap:
                wm_target_width = int(pixmap.width() * self.image_watermark_scale / 100)
                scaled_wm = self.image_watermark_pixmap.scaledToWidth(wm_target_width, Qt.TransformationMode.SmoothTransformation)
                wm_width, wm_height = scaled_wm.width(), scaled_wm.height()
                if self.watermark_position & Qt.AlignmentFlag.AlignLeft: base_x = padding
                elif self.watermark_position & Qt.AlignmentFlag.AlignRight: base_x = pixmap.width() - wm_width - padding
                elif self.watermark_position & Qt.AlignmentFlag.AlignHCenter: base_x = (pixmap.width() - wm_width) // 2
                if self.watermark_position & Qt.AlignmentFlag.AlignTop: base_y = padding
                elif self.watermark_position & Qt.AlignmentFlag.AlignBottom: base_y = pixmap.height() - wm_height - padding
                elif self.watermark_position & Qt.AlignmentFlag.AlignVCenter: base_y = (pixmap.height() - wm_height) // 2
                final_x, final_y = base_x + self.watermark_offset.x(), base_y + self.watermark_offset.y()
                center_x, center_y = final_x + wm_width / 2, final_y + wm_height / 2
                painter.setOpacity(self.image_watermark_opacity)
                painter.translate(center_x, center_y)
                painter.rotate(self.watermark_rotation)
                painter.drawPixmap(int(-wm_width/2), int(-wm_height/2), scaled_wm)
        finally:
            painter.restore()
        return watermarked_pixmap
    
    def update_display(self):
        if self.original_pixmap is None: self.preview_label.clear(); self.preview_label.setText("图片预览区"); return
        pixmap_with_watermark = self.apply_watermark(self.original_pixmap)
        scaled_pixmap = pixmap_with_watermark.scaled(self.preview_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.preview_label.setPixmap(scaled_pixmap)

    def resizeEvent(self, event): super().resizeEvent(event); self.update_display()
    
    # --- BUG FIX: This is the definitive fix for the sender() issue ---
    def on_naming_changed(self):
        radio = self.sender()
        # Only update state if the sender is one of the actual radio buttons
        if radio in (self.radio_name_suffix, self.radio_name_prefix, self.radio_name_original):
            if radio.isChecked():
                if radio == self.radio_name_suffix: self.export_naming_mode = "suffix"
                elif radio == self.radio_name_prefix: self.export_naming_mode = "prefix"
                elif radio == self.radio_name_original: self.export_naming_mode = "original"
        # Always update the UI based on the current state, regardless of caller
        self.export_naming_input.setEnabled(self.export_naming_mode != "original")
    
    def on_naming_text_changed(self, text): self.export_naming_text = text
    def on_format_changed(self): self.export_format = "JPEG" if self.radio_format_jpeg.isChecked() else "PNG"; self.jpeg_quality_widget.setVisible(self.export_format == "JPEG")
    def on_jpeg_quality_changed(self, value): self.export_jpeg_quality = value; self.jpeg_quality_label.setText(f"质量: {value}")
    def on_resize_enabled_toggled(self, checked):
        self.export_resize_enabled = checked
        widgets_to_toggle = [self.radio_resize_percent, self.radio_resize_width, self.radio_resize_height, self.resize_value_spinbox]
        for widget in widgets_to_toggle:
            widget.setEnabled(checked)
    def on_resize_mode_changed(self):
        if self.radio_resize_percent.isChecked():
            self.export_resize_mode = "percentage"; self.resize_value_spinbox.setSuffix(" %"); self.resize_value_spinbox.setRange(1, 200)
        elif self.radio_resize_width.isChecked():
            self.export_resize_mode = "width"; self.resize_value_spinbox.setSuffix(" px"); self.resize_value_spinbox.setRange(10, 10000)
        elif self.radio_resize_height.isChecked():
            self.export_resize_mode = "height"; self.resize_value_spinbox.setSuffix(" px"); self.resize_value_spinbox.setRange(10, 10000)
    def on_resize_value_changed(self, value): self.export_resize_value = value
    def export_images(self):
        if self.image_list_widget.count() == 0: QMessageBox.warning(self, "没有图片", "请先导入图片后再执行导出操作。"); return
        output_dir = QFileDialog.getExistingDirectory(self, "选择导出文件夹");
        if not output_dir: return
        
        input_dirs = set()
        for i in range(self.image_list_widget.count()):
            path = self.image_list_widget.item(i).data(Qt.ItemDataRole.UserRole)
            input_dirs.add(os.path.dirname(path))

        if output_dir in input_dirs: QMessageBox.critical(self, "错误", "不能选择原始图片所在的文件夹作为导出目录，以防覆盖原图！"); return
        exported_count = 0
        for i in range(self.image_list_widget.count()):
            try:
                original_path = self.image_list_widget.item(i).data(Qt.ItemDataRole.UserRole); pixmap = QPixmap(original_path)
                if pixmap.isNull(): continue
                watermarked_pixmap = self.apply_watermark(pixmap)
                final_pixmap = watermarked_pixmap
                if self.export_resize_enabled:
                    if self.export_resize_mode == "percentage":
                        new_width = int(final_pixmap.width() * self.export_resize_value / 100)
                        final_pixmap = final_pixmap.scaledToWidth(new_width, Qt.TransformationMode.SmoothTransformation)
                    elif self.export_resize_mode == "width":
                        final_pixmap = final_pixmap.scaledToWidth(self.export_resize_value, Qt.TransformationMode.SmoothTransformation)
                    elif self.export_resize_mode == "height":
                        final_pixmap = final_pixmap.scaledToHeight(self.export_resize_value, Qt.TransformationMode.SmoothTransformation)
                base_name = os.path.basename(original_path); file_name, _ = os.path.splitext(base_name)
                if self.export_naming_mode == "suffix": new_file_name = file_name + self.export_naming_text
                elif self.export_naming_mode == "prefix": new_file_name = self.export_naming_text + file_name
                else: new_file_name = file_name
                save_format_upper = self.export_format.upper(); file_ext = "." + self.export_format.lower()
                quality = self.export_jpeg_quality if save_format_upper == "JPEG" else -1
                output_path = os.path.join(output_dir, new_file_name + file_ext)
                if final_pixmap.save(output_path, save_format_upper, quality): exported_count += 1
                else: print(f"保存失败: {output_path}")
            except Exception as e: print(f"处理文件时发生错误 {original_path}: {e}")
        QMessageBox.information(self, "导出完成", f"成功导出了 {exported_count} 张带水印的图片到:\n{output_dir}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
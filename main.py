import sys
import os

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QListWidget, QLineEdit, QFrame, QFileDialog,
    QSlider, QColorDialog, QFontComboBox, QSpinBox, QGridLayout, QFormLayout,
    QMessageBox, QSizePolicy, QGroupBox, QRadioButton
)
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont, QScreen
from PyQt6.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("图片加水印工具 WatermarkApp")
        self.init_ui_size()

        self.current_image_path = None
        self.original_pixmap = None
        self.SUPPORTED_FORMATS = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff')

        # 水印通用设置
        self.watermark_position = (Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight)
        
        # 模式选择
        self.watermark_mode = "text"  # "text" or "image"

        # 文本水印状态变量
        self.text_watermark_text = "© Your Name"
        self.text_watermark_font = QFont("Arial", 32)
        self.text_watermark_color = QColor(255, 255, 255, 128)

        # 图片水印状态变量
        self.image_watermark_pixmap = None
        self.image_watermark_path = ""
        self.image_watermark_opacity = 0.5  # 0.0 to 1.0
        self.image_watermark_scale = 15     # % of the main image width

        # 导出设置的状态变量
        self.export_naming_mode = "suffix"
        self.export_naming_text = "_watermarked"
        self.export_format = "PNG"
        self.export_jpeg_quality = 95

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        left_panel = self.create_left_panel()
        center_panel = self.create_center_panel()
        right_panel = self.create_right_panel()

        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(center_panel, 3)
        main_layout.addWidget(right_panel, 2)

        self.update_color_preview()
        self.on_format_changed()
        self.on_watermark_mode_changed() # 初始化UI状态

    def init_ui_size(self):
        screen = QApplication.primaryScreen()
        if not screen:
            self.setGeometry(100, 100, 1200, 700)
            return
        available_size = screen.availableGeometry()
        DEFAULT_WIDTH, DEFAULT_HEIGHT = 1280, 720
        initial_width = min(DEFAULT_WIDTH, int(available_size.width() * 0.9))
        initial_height = min(DEFAULT_HEIGHT, int(available_size.height() * 0.9))
        self.resize(initial_width, initial_height)
        frame_geom = self.frameGeometry()
        center_point = available_size.center()
        frame_geom.moveCenter(center_point)
        self.move(frame_geom.topLeft())

    def create_left_panel(self):
        left_frame = QFrame()
        left_frame.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(left_frame)
        button_layout = QHBoxLayout()
        self.btn_import_images = QPushButton("导入图片")
        self.btn_import_folder = QPushButton("导入文件夹")
        button_layout.addWidget(self.btn_import_images)
        button_layout.addWidget(self.btn_import_folder)
        list_label = QLabel("图片列表")
        self.image_list_widget = QListWidget()
        layout.addLayout(button_layout)
        layout.addWidget(list_label)
        layout.addWidget(self.image_list_widget)
        self.btn_import_images.clicked.connect(self.open_image_files)
        self.btn_import_folder.clicked.connect(self.open_image_folder)
        self.image_list_widget.currentItemChanged.connect(self.on_current_item_changed)
        return left_frame

    def create_center_panel(self):
        center_frame = QFrame()
        center_frame.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(center_frame)
        self.preview_label = QLabel("图片预览区")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("border: 2px dashed #aaa;")
        self.preview_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        layout.addWidget(self.preview_label)
        return center_frame

    def create_right_panel(self):
        right_frame = QFrame()
        right_frame.setFrameShape(QFrame.Shape.StyledPanel)
        main_layout = QVBoxLayout(right_frame)

        # 水印模式切换
        mode_group = QGroupBox("水印类型")
        mode_layout = QHBoxLayout()
        self.radio_mode_text = QRadioButton("文字")
        self.radio_mode_text.setChecked(True)
        self.radio_mode_image = QRadioButton("图片")
        self.radio_mode_text.toggled.connect(self.on_watermark_mode_changed)
        mode_layout.addWidget(self.radio_mode_text)
        mode_layout.addWidget(self.radio_mode_image)
        mode_group.setLayout(mode_layout)
        main_layout.addWidget(mode_group)

        # 文字水印设置组
        self.text_watermark_group = QGroupBox("文字水印设置")
        text_form_layout = QFormLayout()
        self.watermark_text_input = QLineEdit(self.text_watermark_text)
        self.watermark_text_input.textChanged.connect(self.on_text_changed)
        text_form_layout.addRow("文本内容:", self.watermark_text_input)
        self.font_combo = QFontComboBox()
        self.font_combo.setCurrentFont(self.text_watermark_font)
        self.font_combo.currentFontChanged.connect(self.on_font_changed)
        text_form_layout.addRow("字体:", self.font_combo)
        self.font_size_spinbox = QSpinBox()
        self.font_size_spinbox.setRange(8, 200)
        self.font_size_spinbox.setValue(self.text_watermark_font.pointSize())
        self.font_size_spinbox.valueChanged.connect(self.on_font_size_changed)
        text_form_layout.addRow("大小:", self.font_size_spinbox)
        color_layout = QHBoxLayout()
        self.btn_color = QPushButton("选择颜色")
        self.btn_color.clicked.connect(self.on_color_clicked)
        self.color_preview = QFrame()
        self.color_preview.setFixedSize(24, 24)
        self.color_preview.setFrameShape(QFrame.Shape.Box)
        self.color_preview.setAutoFillBackground(True)
        color_layout.addWidget(self.btn_color)
        color_layout.addWidget(self.color_preview)
        text_form_layout.addRow("颜色:", color_layout)
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(0, 255)
        self.opacity_slider.setValue(self.text_watermark_color.alpha())
        self.opacity_slider.valueChanged.connect(self.on_opacity_changed)
        text_form_layout.addRow("透明度:", self.opacity_slider)
        self.text_watermark_group.setLayout(text_form_layout)
        main_layout.addWidget(self.text_watermark_group)
        
        # 图片水印设置组
        self.image_watermark_group = QGroupBox("图片水印设置")
        image_form_layout = QFormLayout()
        self.btn_select_image = QPushButton("选择图片...")
        self.btn_select_image.clicked.connect(self.on_select_image_watermark)
        self.image_path_label = QLabel("未选择图片")
        self.image_path_label.setStyleSheet("color: gray;")
        self.image_scale_label = QLabel(f"缩放: {self.image_watermark_scale}%")
        self.image_scale_slider = QSlider(Qt.Orientation.Horizontal)
        self.image_scale_slider.setRange(1, 100)
        self.image_scale_slider.setValue(self.image_watermark_scale)
        self.image_scale_slider.valueChanged.connect(self.on_image_scale_changed)
        self.image_opacity_label = QLabel(f"透明度: {int(self.image_watermark_opacity * 100)}%")
        self.image_opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.image_opacity_slider.setRange(0, 100)
        self.image_opacity_slider.setValue(int(self.image_watermark_opacity * 100))
        self.image_opacity_slider.valueChanged.connect(self.on_image_opacity_changed)
        image_form_layout.addRow(self.btn_select_image, self.image_path_label)
        image_form_layout.addRow(self.image_scale_label, self.image_scale_slider)
        image_form_layout.addRow(self.image_opacity_label, self.image_opacity_slider)
        self.image_watermark_group.setLayout(image_form_layout)
        main_layout.addWidget(self.image_watermark_group)

        # 通用设置 (位置)
        position_group = QGroupBox("通用设置")
        position_layout = QVBoxLayout()
        position_layout.addWidget(QLabel("位置:"))
        position_grid = QGridLayout()
        positions = [
            (Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft, "↖"), (Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter, "↑"), (Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight, "↗"),
            (Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, "←"), (Qt.AlignmentFlag.AlignCenter, "■"), (Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, "→"),
            (Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft, "↙"), (Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter, "↓"), (Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight, "↘"),
        ]
        for i, (pos, text) in enumerate(positions):
            row, col = i // 3, i % 3
            btn = QPushButton(text)
            btn.clicked.connect(lambda _, p=pos: self.on_position_changed(p))
            position_grid.addWidget(btn, row, col)
        position_layout.addLayout(position_grid)
        position_group.setLayout(position_layout)
        main_layout.addWidget(position_group)

        main_layout.addStretch()
        
        # 导出设置
        export_group = QGroupBox("导出设置")
        export_layout = QVBoxLayout()
        naming_layout = QFormLayout()
        self.radio_name_suffix = QRadioButton("添加后缀"); self.radio_name_suffix.setChecked(True)
        self.radio_name_prefix = QRadioButton("添加前缀"); self.radio_name_original = QRadioButton("保留原名")
        self.export_naming_input = QLineEdit(self.export_naming_text)
        self.radio_name_suffix.toggled.connect(self.on_naming_changed); self.radio_name_prefix.toggled.connect(self.on_naming_changed); self.radio_name_original.toggled.connect(self.on_naming_changed)
        self.export_naming_input.textChanged.connect(self.on_naming_text_changed)
        naming_layout.addRow(self.radio_name_suffix, self.export_naming_input); naming_layout.addRow(self.radio_name_prefix); naming_layout.addRow(self.radio_name_original)
        export_layout.addLayout(naming_layout)
        format_layout = QHBoxLayout()
        self.radio_format_png = QRadioButton("PNG (推荐)"); self.radio_format_png.setChecked(True)
        self.radio_format_jpeg = QRadioButton("JPEG"); self.radio_format_png.toggled.connect(self.on_format_changed)
        format_layout.addWidget(QLabel("格式:")); format_layout.addWidget(self.radio_format_png); format_layout.addWidget(self.radio_format_jpeg)
        export_layout.addLayout(format_layout)
        self.jpeg_quality_widget = QWidget()
        jpeg_layout = QHBoxLayout(self.jpeg_quality_widget); jpeg_layout.setContentsMargins(0, 0, 0, 0)
        self.jpeg_quality_label = QLabel(f"质量: {self.export_jpeg_quality}")
        self.jpeg_quality_slider = QSlider(Qt.Orientation.Horizontal); self.jpeg_quality_slider.setRange(0, 100); self.jpeg_quality_slider.setValue(self.export_jpeg_quality)
        self.jpeg_quality_slider.valueChanged.connect(self.on_jpeg_quality_changed)
        jpeg_layout.addWidget(self.jpeg_quality_label); jpeg_layout.addWidget(self.jpeg_quality_slider)
        export_layout.addWidget(self.jpeg_quality_widget)
        export_group.setLayout(export_layout)
        main_layout.addWidget(export_group)

        self.btn_export = QPushButton("导出所有图片"); self.btn_export.clicked.connect(self.export_images)
        main_layout.addWidget(self.btn_export)
        return right_frame

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

    def on_position_changed(self, position):
        self.watermark_position = position
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
        current_items = set(self.image_list_widget.item(i).text() for i in range(self.image_list_widget.count()))
        new_paths = [path for path in file_paths if path not in current_items]
        if new_paths:
            self.image_list_widget.addItems(new_paths)

    def on_current_item_changed(self, current_item, previous_item):
        if current_item is None:
            self.preview_label.clear(); self.preview_label.setText("图片预览区")
            self.current_image_path = None; self.original_pixmap = None; return
        self.current_image_path = current_item.text()
        self.original_pixmap = QPixmap(self.current_image_path)
        if self.original_pixmap.isNull():
            self.preview_label.clear(); self.preview_label.setText("无法加载图片")
            self.original_pixmap = None; return
        self.update_display()

    def apply_watermark(self, pixmap):
        if pixmap.isNull(): return pixmap
        watermarked_pixmap = pixmap.copy()
        painter = QPainter(watermarked_pixmap)
        padding = 10

        if self.watermark_mode == "text":
            painter.setFont(self.text_watermark_font)
            painter.setPen(self.text_watermark_color)
            metrics = painter.fontMetrics()
            text_width = metrics.horizontalAdvance(self.text_watermark_text)
            text_height = metrics.height()
            
            x, y = 0, 0
            if self.watermark_position & Qt.AlignmentFlag.AlignLeft: x = padding
            elif self.watermark_position & Qt.AlignmentFlag.AlignRight: x = pixmap.width() - text_width - padding
            elif self.watermark_position & Qt.AlignmentFlag.AlignHCenter: x = (pixmap.width() - text_width) // 2
            if self.watermark_position & Qt.AlignmentFlag.AlignTop: y = padding + text_height
            elif self.watermark_position & Qt.AlignmentFlag.AlignBottom: y = pixmap.height() - padding
            elif self.watermark_position & Qt.AlignmentFlag.AlignVCenter: y = (pixmap.height() + text_height) // 2 - metrics.descent()
            
            painter.drawText(x, y, self.text_watermark_text)

        elif self.watermark_mode == "image" and self.image_watermark_pixmap:
            wm_target_width = int(pixmap.width() * self.image_watermark_scale / 100)
            scaled_wm = self.image_watermark_pixmap.scaledToWidth(wm_target_width, Qt.TransformationMode.SmoothTransformation)
            wm_width, wm_height = scaled_wm.width(), scaled_wm.height()
            
            x, y = 0, 0
            if self.watermark_position & Qt.AlignmentFlag.AlignLeft: x = padding
            elif self.watermark_position & Qt.AlignmentFlag.AlignRight: x = pixmap.width() - wm_width - padding
            elif self.watermark_position & Qt.AlignmentFlag.AlignHCenter: x = (pixmap.width() - wm_width) // 2
            if self.watermark_position & Qt.AlignmentFlag.AlignTop: y = padding
            elif self.watermark_position & Qt.AlignmentFlag.AlignBottom: y = pixmap.height() - wm_height - padding
            elif self.watermark_position & Qt.AlignmentFlag.AlignVCenter: y = (pixmap.height() - wm_height) // 2

            painter.setOpacity(self.image_watermark_opacity)
            painter.drawPixmap(x, y, scaled_wm)

        painter.end()
        return watermarked_pixmap

    def update_display(self):
        if self.original_pixmap is None:
            self.preview_label.clear(); self.preview_label.setText("图片预览区"); return
        pixmap_with_watermark = self.apply_watermark(self.original_pixmap)
        scaled_pixmap = pixmap_with_watermark.scaled(self.preview_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.preview_label.setPixmap(scaled_pixmap)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_display()

    def on_naming_changed(self):
        radio = self.sender()
        if radio.isChecked():
            if radio == self.radio_name_suffix: self.export_naming_mode = "suffix"
            elif radio == self.radio_name_prefix: self.export_naming_mode = "prefix"
            elif radio == self.radio_name_original: self.export_naming_mode = "original"
        self.export_naming_input.setEnabled(self.export_naming_mode != "original")

    def on_naming_text_changed(self, text):
        self.export_naming_text = text

    def on_format_changed(self):
        self.export_format = "JPEG" if self.radio_format_jpeg.isChecked() else "PNG"
        self.jpeg_quality_widget.setVisible(self.export_format == "JPEG")

    def on_jpeg_quality_changed(self, value):
        self.export_jpeg_quality = value
        self.jpeg_quality_label.setText(f"质量: {value}")
        
    def export_images(self):
        if self.image_list_widget.count() == 0:
            QMessageBox.warning(self, "没有图片", "请先导入图片后再执行导出操作。"); return
        output_dir = QFileDialog.getExistingDirectory(self, "选择导出文件夹")
        if not output_dir: return
        input_dirs = set(os.path.dirname(self.image_list_widget.item(i).text()) for i in range(self.image_list_widget.count()))
        if output_dir in input_dirs:
            QMessageBox.critical(self, "错误", "不能选择原始图片所在的文件夹作为导出目录，以防覆盖原图！"); return
        
        exported_count = 0
        for i in range(self.image_list_widget.count()):
            try:
                original_path = self.image_list_widget.item(i).text()
                pixmap = QPixmap(original_path)
                if pixmap.isNull(): continue
                watermarked_pixmap = self.apply_watermark(pixmap)
                base_name = os.path.basename(original_path); file_name, _ = os.path.splitext(base_name)
                new_file_name = ""
                if self.export_naming_mode == "suffix": new_file_name = file_name + self.export_naming_text
                elif self.export_naming_mode == "prefix": new_file_name = self.export_naming_text + file_name
                else: new_file_name = file_name
                save_format_upper = self.export_format.upper()
                file_ext = "." + self.export_format.lower()
                quality = self.export_jpeg_quality if save_format_upper == "JPEG" else -1
                output_path = os.path.join(output_dir, new_file_name + file_ext)
                if watermarked_pixmap.save(output_path, save_format_upper, quality):
                    exported_count += 1
                else:
                    print(f"保存失败: {output_path}")
            except Exception as e:
                print(f"处理文件时发生错误 {original_path}: {e}")
        
        QMessageBox.information(self, "导出完成", f"成功导出了 {exported_count} 张带水印的图片到:\n{output_dir}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
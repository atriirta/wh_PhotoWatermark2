import sys
import os

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QListWidget, QLineEdit, QFrame, QFileDialog,
    QSlider, QColorDialog, QFontComboBox, QSpinBox, QGridLayout, QFormLayout,
    QMessageBox, QSizePolicy
)
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont, QScreen
from PyQt6.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        # ... __init__ 和其他方法保持不变 ...
        super().__init__()
        self.setWindowTitle("图片加水印工具 WatermarkApp")
        self.init_ui_size()
        self.current_image_path = None
        self.original_pixmap = None
        self.watermark_text = "© Your Name"
        self.watermark_font = QFont("Arial", 32)
        self.watermark_color = QColor(255, 255, 255, 128)
        self.watermark_position = (Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight)
        
        # NEW: 定义支持的图片格式，方便复用
        self.SUPPORTED_FORMATS = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff')

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        left_panel = self.create_left_panel()
        center_panel = self.create_center_panel()
        right_panel = self.create_right_panel()
        main_layout.addWidget(left_panel, 1); main_layout.addWidget(center_panel, 3); main_layout.addWidget(right_panel, 2)
        self.update_color_preview()

    # ... 省略了其他未改变的方法，请保留你文件中的这些方法 ...

    # --- MODIFIED: open_image_files 现在调用新的辅助方法 ---
    def open_image_files(self, *args, **kwargs):
        file_filter = f"图片文件 ({' '.join(['*' + ext for ext in self.SUPPORTED_FORMATS])})"
        file_paths, _ = QFileDialog.getOpenFileNames(self, "选择一个或多个图片文件", "", file_filter)
        if file_paths:
            self.add_images_to_list(file_paths)

    # --- MODIFIED: 实现了 open_image_folder 的逻辑 ---
    def open_image_folder(self, *args, **kwargs):
        folder_path = QFileDialog.getExistingDirectory(self, "选择包含图片的文件夹")
        if folder_path:
            image_paths = []
            # 使用 os.scandir() 效率更高
            for entry in os.scandir(folder_path):
                if entry.is_file() and entry.name.lower().endswith(self.SUPPORTED_FORMATS):
                    image_paths.append(entry.path)
            
            if image_paths:
                self.add_images_to_list(image_paths)
            else:
                QMessageBox.information(self, "没有图片", "选择的文件夹中没有找到支持的图片格式。")

    # --- NEW: 提取出的公共辅助方法 ---
    def add_images_to_list(self, file_paths):
        """将文件路径列表添加到 QListWidget，并过滤掉重复项。"""
        current_items = set(self.image_list_widget.item(i).text() for i in range(self.image_list_widget.count()))
        new_paths = [path for path in file_paths if path not in current_items]
        if new_paths:
            self.image_list_widget.addItems(new_paths)

# ... 省略了其他所有未改变的方法，请在你的文件中保留它们 ...
    def init_ui_size(self):
        screen = QApplication.primaryScreen()
        if not screen: self.setGeometry(100, 100, 1200, 700); return
        available_size = screen.availableGeometry()
        DEFAULT_WIDTH, DEFAULT_HEIGHT = 1280, 720
        initial_width = min(DEFAULT_WIDTH, int(available_size.width() * 0.9)); initial_height = min(DEFAULT_HEIGHT, int(available_size.height() * 0.9))
        self.resize(initial_width, initial_height)
        frame_geom = self.frameGeometry(); center_point = available_size.center(); frame_geom.moveCenter(center_point); self.move(frame_geom.topLeft())
    def create_left_panel(self):
        left_frame = QFrame(); left_frame.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(left_frame)
        button_layout = QHBoxLayout()
        self.btn_import_images = QPushButton("导入图片"); self.btn_import_folder = QPushButton("导入文件夹")
        button_layout.addWidget(self.btn_import_images); button_layout.addWidget(self.btn_import_folder)
        list_label = QLabel("图片列表")
        self.image_list_widget = QListWidget()
        layout.addLayout(button_layout); layout.addWidget(list_label); layout.addWidget(self.image_list_widget)
        self.btn_import_images.clicked.connect(self.open_image_files)
        self.btn_import_folder.clicked.connect(self.open_image_folder)
        self.image_list_widget.currentItemChanged.connect(self.on_current_item_changed)
        return left_frame
    def create_center_panel(self):
        center_frame = QFrame(); center_frame.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(center_frame)
        self.preview_label = QLabel("图片预览区"); self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("border: 2px dashed #aaa;")
        self.preview_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        layout.addWidget(self.preview_label)
        return center_frame
    def create_right_panel(self):
        right_frame = QFrame(); right_frame.setFrameShape(QFrame.Shape.StyledPanel)
        main_layout = QVBoxLayout(right_frame)
        settings_label = QLabel("水印设置"); settings_label.setAlignment(Qt.AlignmentFlag.AlignCenter); main_layout.addWidget(settings_label)
        form_layout = QFormLayout()
        self.watermark_text_input = QLineEdit(self.watermark_text); self.watermark_text_input.textChanged.connect(self.on_text_changed); form_layout.addRow("文本内容:", self.watermark_text_input)
        self.font_combo = QFontComboBox(); self.font_combo.setCurrentFont(self.watermark_font); self.font_combo.currentFontChanged.connect(self.on_font_changed); form_layout.addRow("字体:", self.font_combo)
        self.font_size_spinbox = QSpinBox(); self.font_size_spinbox.setRange(8, 200); self.font_size_spinbox.setValue(self.watermark_font.pointSize()); self.font_size_spinbox.valueChanged.connect(self.on_font_size_changed); form_layout.addRow("大小:", self.font_size_spinbox)
        color_layout = QHBoxLayout()
        self.btn_color = QPushButton("选择颜色"); self.btn_color.clicked.connect(self.on_color_clicked)
        self.color_preview = QFrame(); self.color_preview.setFixedSize(24, 24); self.color_preview.setFrameShape(QFrame.Shape.Box); self.color_preview.setAutoFillBackground(True)
        color_layout.addWidget(self.btn_color); color_layout.addWidget(self.color_preview); form_layout.addRow("颜色:", color_layout)
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal); self.opacity_slider.setRange(0, 255); self.opacity_slider.setValue(self.watermark_color.alpha()); self.opacity_slider.valueChanged.connect(self.on_opacity_changed); form_layout.addRow("透明度:", self.opacity_slider)
        main_layout.addLayout(form_layout)
        main_layout.addWidget(QLabel("位置:"))
        position_grid = QGridLayout()
        positions = [(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft, "↖"), (Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter, "↑"), (Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight, "↗"),(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, "←"), (Qt.AlignmentFlag.AlignCenter, "■"), (Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, "→"),(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft, "↙"), (Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter, "↓"), (Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight, "↘"),]
        for i, (pos, text) in enumerate(positions):
            row, col = i // 3, i % 3
            btn = QPushButton(text); btn.clicked.connect(lambda _, p=pos: self.on_position_changed(p)); position_grid.addWidget(btn, row, col)
        main_layout.addLayout(position_grid)
        main_layout.addStretch()
        self.btn_export = QPushButton("导出所有图片"); self.btn_export.clicked.connect(self.export_images); main_layout.addWidget(self.btn_export)
        return right_frame
    def on_text_changed(self, text): self.watermark_text = text; self.update_display()
    def on_font_changed(self, font): self.watermark_font.setFamily(font.family()); self.update_display()
    def on_font_size_changed(self, size): self.watermark_font.setPointSize(size); self.update_display()
    def on_color_clicked(self):
        color = QColorDialog.getColor(self.watermark_color, self, "选择水印颜色")
        if color.isValid():
            alpha = self.watermark_color.alpha(); color.setAlpha(alpha); self.watermark_color = color; self.update_color_preview(); self.update_display()
    def on_opacity_changed(self, value): self.watermark_color.setAlpha(value); self.update_color_preview(); self.update_display()
    def on_position_changed(self, position): self.watermark_position = position; self.update_display()
    def update_color_preview(self):
        palette = self.color_preview.palette(); palette.setColor(self.color_preview.backgroundRole(), self.watermark_color); self.color_preview.setPalette(palette)
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
        painter.setFont(self.watermark_font); painter.setPen(self.watermark_color)
        metrics = painter.fontMetrics()
        text_width = metrics.horizontalAdvance(self.watermark_text); text_height = metrics.height()
        padding = 10; x, y = 0, 0
        if self.watermark_position & Qt.AlignmentFlag.AlignLeft: x = padding
        elif self.watermark_position & Qt.AlignmentFlag.AlignRight: x = pixmap.width() - text_width - padding
        elif self.watermark_position & Qt.AlignmentFlag.AlignHCenter: x = (pixmap.width() - text_width) // 2
        if self.watermark_position & Qt.AlignmentFlag.AlignTop: y = padding + text_height
        elif self.watermark_position & Qt.AlignmentFlag.AlignBottom: y = pixmap.height() - padding
        elif self.watermark_position & Qt.AlignmentFlag.AlignVCenter: y = (pixmap.height() + text_height) // 2
        painter.drawText(x, y, self.watermark_text); painter.end()
        return watermarked_pixmap
    def update_display(self):
        if self.original_pixmap is None: self.preview_label.clear(); self.preview_label.setText("图片预览区"); return
        pixmap_with_watermark = self.apply_watermark(self.original_pixmap)
        scaled_pixmap = pixmap_with_watermark.scaled(self.preview_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.preview_label.setPixmap(scaled_pixmap)
    def resizeEvent(self, event): super().resizeEvent(event); self.update_display()
    def export_images(self):
        if self.image_list_widget.count() == 0: QMessageBox.warning(self, "没有图片", "请先导入图片后再执行导出操作。"); return
        output_dir = QFileDialog.getExistingDirectory(self, "选择导出文件夹")
        if not output_dir: return
        input_dirs = set()
        for i in range(self.image_list_widget.count()): input_dirs.add(os.path.dirname(self.image_list_widget.item(i).text()))
        if output_dir in input_dirs: QMessageBox.critical(self, "错误", "不能选择原始图片所在的文件夹作为导出目录，以防覆盖原图！"); return
        exported_count = 0
        for i in range(self.image_list_widget.count()):
            try:
                original_path = self.image_list_widget.item(i).text()
                pixmap = QPixmap(original_path)
                if pixmap.isNull(): continue
                watermarked_pixmap = self.apply_watermark(pixmap)
                base_name = os.path.basename(original_path); file_name, _ = os.path.splitext(base_name)
                output_path = os.path.join(output_dir, f"{file_name}_watermarked.png")
                if watermarked_pixmap.save(output_path, "PNG"): exported_count += 1
                else: print(f"保存失败: {output_path}")
            except Exception as e: print(f"处理文件时发生错误 {original_path}: {e}")
        QMessageBox.information(self, "导出完成", f"成功导出了 {exported_count} 张带水印的图片到:\n{output_dir}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
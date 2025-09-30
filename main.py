import sys
import os

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QListWidget, QLineEdit, QFrame, QFileDialog,
    QSlider, QColorDialog, QFontComboBox, QSpinBox, QGridLayout, QFormLayout,
    QMessageBox
)
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont
from PyQt6.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # ... (这部分代码没有变化) ...
        self.setWindowTitle("图片加水印工具 WatermarkApp")
        self.setGeometry(100, 100, 1200, 700) 
        self.current_image_path = None
        self.original_pixmap = None
        self.watermark_text = "© Your Name"
        self.watermark_font = QFont("Arial", 32)
        self.watermark_color = QColor(255, 255, 255, 128)
        self.watermark_position = (Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight)
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

    # ... create_left_panel 无变化 ...
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

    # --- MODIFIED: 关键修改点 1 ---
    def create_center_panel(self):
        center_frame = QFrame()
        center_frame.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(center_frame)
        self.preview_label = QLabel("图片预览区")
        
        # --- NEW: 告诉 QLabel 自动缩放其内容以填充可用空间 ---
        self.preview_label.setScaledContents(True) 
        
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("border: 2px dashed #aaa;")
        layout.addWidget(self.preview_label)
        return center_frame

    # ... create_right_panel 无变化 ...
    def create_right_panel(self):
        right_frame = QFrame()
        right_frame.setFrameShape(QFrame.Shape.StyledPanel)
        main_layout = QVBoxLayout(right_frame)
        settings_label = QLabel("水印设置")
        settings_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(settings_label)
        form_layout = QFormLayout()
        self.watermark_text_input = QLineEdit(self.watermark_text)
        self.watermark_text_input.textChanged.connect(self.on_text_changed)
        form_layout.addRow("文本内容:", self.watermark_text_input)
        self.font_combo = QFontComboBox()
        self.font_combo.setCurrentFont(self.watermark_font)
        self.font_combo.currentFontChanged.connect(self.on_font_changed)
        form_layout.addRow("字体:", self.font_combo)
        self.font_size_spinbox = QSpinBox()
        self.font_size_spinbox.setRange(8, 200)
        self.font_size_spinbox.setValue(self.watermark_font.pointSize())
        self.font_size_spinbox.valueChanged.connect(self.on_font_size_changed)
        form_layout.addRow("大小:", self.font_size_spinbox)
        color_layout = QHBoxLayout()
        self.btn_color = QPushButton("选择颜色")
        self.btn_color.clicked.connect(self.on_color_clicked)
        self.color_preview = QFrame()
        self.color_preview.setFixedSize(24, 24)
        self.color_preview.setFrameShape(QFrame.Shape.Box)
        self.color_preview.setAutoFillBackground(True)
        color_layout.addWidget(self.btn_color)
        color_layout.addWidget(self.color_preview)
        form_layout.addRow("颜色:", color_layout)
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(0, 255)
        self.opacity_slider.setValue(self.watermark_color.alpha())
        self.opacity_slider.valueChanged.connect(self.on_opacity_changed)
        form_layout.addRow("透明度:", self.opacity_slider)
        main_layout.addLayout(form_layout)
        main_layout.addWidget(QLabel("位置:"))
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
        main_layout.addLayout(position_grid)
        main_layout.addStretch()
        self.btn_export = QPushButton("导出所有图片")
        self.btn_export.clicked.connect(self.export_images)
        main_layout.addWidget(self.btn_export)
        return right_frame

    # ... 其他槽函数无变化 ...
    def on_text_changed(self, text): self.watermark_text = text; self.update_display()
    def on_font_changed(self, font): self.watermark_font.setFamily(font.family()); self.update_display()
    def on_font_size_changed(self, size): self.watermark_font.setPointSize(size); self.update_display()
    def on_color_clicked(self):
        color = QColorDialog.getColor(self.watermark_color, self, "选择水印颜色")
        if color.isValid():
            alpha = self.watermark_color.alpha()
            color.setAlpha(alpha)
            self.watermark_color = color
            self.update_color_preview()
            self.update_display()
    def on_opacity_changed(self, value): self.watermark_color.setAlpha(value); self.update_color_preview(); self.update_display()
    def on_position_changed(self, position): self.watermark_position = position; self.update_display()
    def update_color_preview(self):
        palette = self.color_preview.palette()
        palette.setColor(self.color_preview.backgroundRole(), self.watermark_color)
        self.color_preview.setPalette(palette)
    def open_image_files(self, *args, **kwargs):
        file_paths, _ = QFileDialog.getOpenFileNames(self, "选择一个或多个图片文件", "", "图片文件 (*.jpg *.jpeg *.png *.bmp *.tiff)")
        if file_paths:
            current_items = set(self.image_list_widget.item(i).text() for i in range(self.image_list_widget.count()))
            new_paths = [path for path in file_paths if path not in current_items]
            self.image_list_widget.addItems(new_paths)
    def open_image_folder(self, *args, **kwargs): print("导入文件夹功能待实现")
    def on_current_item_changed(self, current_item, previous_item):
        if current_item is None:
            self.preview_label.clear() # clear() is better than setText() here
            self.preview_label.setText("图片预览区")
            self.current_image_path = None
            self.original_pixmap = None
            return
        self.current_image_path = current_item.text()
        self.original_pixmap = QPixmap(self.current_image_path)
        if self.original_pixmap.isNull():
            self.preview_label.clear()
            self.preview_label.setText("无法加载图片")
            self.original_pixmap = None
            return
        self.update_display()
    def apply_watermark(self, pixmap):
        if pixmap.isNull(): return pixmap
        watermarked_pixmap = pixmap.copy()
        painter = QPainter(watermarked_pixmap)
        painter.setFont(self.watermark_font)
        painter.setPen(self.watermark_color)
        metrics = painter.fontMetrics()
        text_width = metrics.horizontalAdvance(self.watermark_text)
        text_height = metrics.height()
        padding = 10
        x, y = 0, 0
        if self.watermark_position & Qt.AlignmentFlag.AlignLeft: x = padding
        elif self.watermark_position & Qt.AlignmentFlag.AlignRight: x = pixmap.width() - text_width - padding
        elif self.watermark_position & Qt.AlignmentFlag.AlignHCenter: x = (pixmap.width() - text_width) // 2
        if self.watermark_position & Qt.AlignmentFlag.AlignTop: y = padding + text_height
        elif self.watermark_position & Qt.AlignmentFlag.AlignBottom: y = pixmap.height() - padding
        elif self.watermark_position & Qt.AlignmentFlag.AlignVCenter: y = (pixmap.height() + text_height) // 2
        painter.drawText(x, y, self.watermark_text)
        painter.end()
        return watermarked_pixmap
    
    # --- MODIFIED: 关键修改点 2 ---
    def update_display(self):
        if self.original_pixmap is None: return
        
        # 1. 应用水印 (这一步不变)
        pixmap_with_watermark = self.apply_watermark(self.original_pixmap)
        
        # 2. 直接将完整的、未经缩放的 pixmap 设置给 label
        #    因为我们设置了 setScaledContents(True)，label 会自动处理缩放
        self.preview_label.setPixmap(pixmap_with_watermark)

    # --- REMOVED: 关键修改点 3 ---
    # resizeEvent 不再需要，可以安全删除
    # def resizeEvent(self, event):
    #     super().resizeEvent(event)
    #     self.update_display()
        
    def export_images(self):
        if self.image_list_widget.count() == 0:
            QMessageBox.warning(self, "没有图片", "请先导入图片后再执行导出操作。")
            return
        output_dir = QFileDialog.getExistingDirectory(self, "选择导出文件夹")
        if not output_dir: return
        input_dirs = set()
        for i in range(self.image_list_widget.count()):
            item_path = self.image_list_widget.item(i).text()
            input_dirs.add(os.path.dirname(item_path))
        if output_dir in input_dirs:
            QMessageBox.critical(self, "错误", "不能选择原始图片所在的文件夹作为导出目录，以防覆盖原图！")
            return
        exported_count = 0
        for i in range(self.image_list_widget.count()):
            try:
                original_path = self.image_list_widget.item(i).text()
                pixmap = QPixmap(original_path)
                if pixmap.isNull(): continue
                watermarked_pixmap = self.apply_watermark(pixmap)
                base_name = os.path.basename(original_path)
                file_name, _ = os.path.splitext(base_name)
                output_path = os.path.join(output_dir, f"{file_name}_watermarked.png")
                if watermarked_pixmap.save(output_path, "PNG"):
                    exported_count += 1
                else: print(f"保存失败: {output_path}")
            except Exception as e: print(f"处理文件时发生错误 {original_path}: {e}")
        QMessageBox.information(self, "导出完成", f"成功导出了 {exported_count} 张带水印的图片到:\n{output_dir}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QListWidget, QLineEdit, QFrame, QFileDialog
)
# NEW: 导入 QPainter 和其他绘图相关的类
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont
from PyQt6.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("图片加水印工具 WatermarkApp")
        self.setGeometry(100, 100, 1200, 700) 

        self.current_image_path = None
        # NEW: 用于存储原始的、未添加水印的 QPixmap，避免重复从磁盘加载
        self.original_pixmap = None

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        left_panel = self.create_left_panel()
        center_panel = self.create_center_panel()
        right_panel = self.create_right_panel()

        main_layout.addWidget(left_panel, 1) 
        main_layout.addWidget(center_panel, 3)
        main_layout.addWidget(right_panel, 2)

    def create_left_panel(self):
        # ... (这部分代码没有变化) ...
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
        # ... (这部分代码没有变化) ...
        center_frame = QFrame()
        center_frame.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(center_frame)
        
        self.preview_label = QLabel("图片预览区")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("border: 2px dashed #aaa;")
        
        layout.addWidget(self.preview_label)
        return center_frame

    def create_right_panel(self):
        right_frame = QFrame()
        right_frame.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(right_frame)
        
        settings_label = QLabel("水印设置")
        settings_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        text_label = QLabel("水印文本:")
        self.watermark_text_input = QLineEdit("© Your Name")
        self.btn_export = QPushButton("导出所有图片")

        # --- NEW: 连接文本框的 textChanged 信号 ---
        self.watermark_text_input.textChanged.connect(self.update_display)

        layout.addWidget(settings_label)
        layout.addSpacing(20)
        layout.addWidget(text_label)
        layout.addWidget(self.watermark_text_input)
        layout.addStretch()
        layout.addWidget(self.btn_export)

        return right_frame

    def open_image_files(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "选择一个或多个图片文件", "", "图片文件 (*.jpg *.jpeg *.png *.bmp *.tiff)"
        )
        if file_paths:
            current_items = set(self.image_list_widget.item(i).text() for i in range(self.image_list_widget.count()))
            new_paths = [path for path in file_paths if path not in current_items]
            self.image_list_widget.addItems(new_paths)

    def open_image_folder(self):
        print("导入文件夹功能待实现")
        pass

    # MODIFIED: 重命名为 on_current_item_changed，职责更清晰
    def on_current_item_changed(self, current_item, previous_item):
        if current_item is None:
            self.preview_label.setText("图片预览区")
            self.current_image_path = None
            self.original_pixmap = None
            return

        self.current_image_path = current_item.text()
        self.original_pixmap = QPixmap(self.current_image_path)
        if self.original_pixmap.isNull():
            self.preview_label.setText("无法加载图片")
            self.original_pixmap = None
            return
        
        self.update_display()

    # NEW: 应用水印的核心逻辑
    def apply_watermark(self, pixmap):
        """在一个 QPixmap 副本上应用当前设置的水印并返回它"""
        if pixmap.isNull():
            return pixmap

        # 创建一个副本进行绘制
        watermarked_pixmap = pixmap.copy()
        
        painter = QPainter(watermarked_pixmap)
        
        # --- 设置 painter 的属性 ---
        font = QFont("Arial", 32) # 字体和大小（暂为硬编码）
        painter.setFont(font)
        # 颜色和透明度 (R, G, B, Alpha: 0-255)
        color = QColor(255, 255, 255, 128) # 半透明白色（暂为硬编码）
        painter.setPen(color)
        
        text = self.watermark_text_input.text()
        
        # --- 计算绘制位置 ---
        # 简单地放在右下角，留出 10px 边距 (暂为硬编码)
        padding = 10
        # Qt 6.2+ has pixelMetric, older versions don't, so we use boundingRect as a fallback
        try:
            metrics = painter.fontMetrics()
            text_width = metrics.horizontalAdvance(text)
            text_height = metrics.height()
        except Exception: # Fallback for older Qt versions if needed
            rect = painter.boundingRect(0,0,0,0, 0, text)
            text_width = rect.width()
            text_height = rect.height()


        x = watermarked_pixmap.width() - text_width - padding
        y = watermarked_pixmap.height() - padding
        
        # --- 绘制文本 ---
        painter.drawText(x, y, text)
        painter.end()
        
        return watermarked_pixmap

    # MODIFIED: display_image 被重构为 update_display
    def update_display(self):
        """
        核心更新函数。它获取原始图片，应用水印，然后缩放并显示在预览区。
        由多种信号触发（选择新图片、文本改变、窗口缩放等）。
        """
        if self.original_pixmap is None:
            return

        # 1. 应用水印
        pixmap_with_watermark = self.apply_watermark(self.original_pixmap)
        
        # 2. 缩放以适应预览区
        scaled_pixmap = pixmap_with_watermark.scaled(
            self.preview_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.preview_label.setPixmap(scaled_pixmap)

    def resizeEvent(self, event):
        """当窗口大小改变时，重新调用主更新函数"""
        super().resizeEvent(event)
        self.update_display()

# --- 应用程序入口 ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
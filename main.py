import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QListWidget, QLineEdit, QFrame, QFileDialog
)
from PyQt6.QtGui import QPixmap # NEW: 导入 QPixmap 用于图像显示
from PyQt6.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("图片加水印工具 WatermarkApp")
        self.setGeometry(100, 100, 1200, 700) 

        # NEW: 用于存储当前显示的图片路径，方便窗口缩放时重绘
        self.current_image_path = None

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
        
        # MODIFIED: 连接列表项变化信号到新的槽函数
        self.image_list_widget.currentItemChanged.connect(self.update_image_preview)
        
        return left_frame

    def create_center_panel(self):
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

    # --- NEW: 更新图片预览的槽函数 ---
    def update_image_preview(self, current_item, previous_item):
        """当列表选择变化时，更新中央的图片预览"""
        if current_item is None:
            self.preview_label.setText("图片预览区")
            self.current_image_path = None
            return

        self.current_image_path = current_item.text()
        self.display_image(self.current_image_path)

    # --- NEW: 封装的图片显示逻辑 ---
    def display_image(self, image_path):
        """加载并按比例缩放图片以适应预览区"""
        if not image_path:
            return
            
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            self.preview_label.setText("无法加载图片")
            return
        
        # 按比例缩放图片以适应 a_label 的尺寸
        scaled_pixmap = pixmap.scaled(
            self.preview_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.preview_label.setPixmap(scaled_pixmap)

    # --- NEW: 覆盖窗口的 resizeEvent ---
    def resizeEvent(self, event):
        """当窗口大小改变时，重新缩放并显示图片"""
        super().resizeEvent(event) # 调用父类的实现
        self.display_image(self.current_image_path) # 使用当前图片路径重新显示

# --- 应用程序入口 ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
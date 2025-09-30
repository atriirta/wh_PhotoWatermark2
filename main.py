import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QListWidget, QLineEdit, QFrame, QFileDialog # NEW: 导入QFileDialog
)
from PyQt6.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # --- 1. 窗口基本设置 ---
        self.setWindowTitle("图片加水印工具 WatermarkApp")
        self.setGeometry(100, 100, 1200, 700) 

        # --- 2. 主布局 ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)

        # --- 3. 创建三个垂直的功能区域 ---
        left_panel = self.create_left_panel()
        center_panel = self.create_center_panel()
        right_panel = self.create_right_panel()

        # --- 4. 将功能区域添加到主布局 ---
        main_layout.addWidget(left_panel, 1) 
        main_layout.addWidget(center_panel, 3)
        main_layout.addWidget(right_panel, 2)

    def create_left_panel(self):
        """创建左侧面板，包含文件导入和列表"""
        left_frame = QFrame()
        left_frame.setFrameShape(QFrame.Shape.StyledPanel)
        
        layout = QVBoxLayout(left_frame)

        button_layout = QHBoxLayout()
        # MODIFIED: 将按钮赋值给实例变量，方便连接信号
        self.btn_import_images = QPushButton("导入图片")
        self.btn_import_folder = QPushButton("导入文件夹")
        button_layout.addWidget(self.btn_import_images)
        button_layout.addWidget(self.btn_import_folder)
        
        list_label = QLabel("图片列表")
        self.image_list_widget = QListWidget()

        layout.addLayout(button_layout)
        layout.addWidget(list_label)
        layout.addWidget(self.image_list_widget)

        # --- NEW: 信号与槽连接 ---
        self.btn_import_images.clicked.connect(self.open_image_files)
        self.btn_import_folder.clicked.connect(self.open_image_folder)
        
        return left_frame

    def create_center_panel(self):
        """创建中间面板，用于图片预览"""
        center_frame = QFrame()
        center_frame.setFrameShape(QFrame.Shape.StyledPanel)
        
        layout = QVBoxLayout(center_frame)
        
        self.preview_label = QLabel("图片预览区")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("border: 2px dashed #aaa;")
        
        layout.addWidget(self.preview_label)
        
        return center_frame

    def create_right_panel(self):
        """创建右侧面板，用于水印设置"""
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

    # --- NEW: 新增的槽函数 ---
    def open_image_files(self):
        """打开文件对话框以选择一个或多个图片文件"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "选择一个或多个图片文件",
            "", # 默认打开的目录
            "图片文件 (*.jpg *.jpeg *.png *.bmp *.tiff)" # 文件过滤器
        )
        
        if file_paths:
            # 获取当前列表中已有的项，防止重复添加
            current_items = set(self.image_list_widget.item(i).text() for i in range(self.image_list_widget.count()))
            new_paths = [path for path in file_paths if path not in current_items]
            self.image_list_widget.addItems(new_paths)

    # --- NEW: 为“导入文件夹”准备的槽函数 (暂未实现) ---
    def open_image_folder(self):
        """打开文件夹对话框以选择包含图片的文件夹"""
        # 这个功能我们将在后续步骤中实现
        print("导入文件夹功能待实现")
        pass


# --- 应用程序入口 ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
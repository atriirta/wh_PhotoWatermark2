import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QListWidget, QLineEdit, QFrame
)
from PyQt6.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # --- 1. 窗口基本设置 ---
        self.setWindowTitle("图片加水印工具 WatermarkApp")
        self.setGeometry(100, 100, 1200, 700) # x, y, width, height

        # --- 2. 主布局 ---
        # 创建一个 central widget，所有的其他控件都放在它上面
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建一个水平主布局
        main_layout = QHBoxLayout(central_widget)

        # --- 3. 创建三个垂直的功能区域 ---
        # 左侧区域：文件列表
        left_panel = self.create_left_panel()
        
        # 中间区域：图片预览
        center_panel = self.create_center_panel()

        # 右侧区域：水印设置
        right_panel = self.create_right_panel()

        # --- 4. 将功能区域添加到主布局 ---
        # addWidget(widget, stretch_factor) stretch_factor决定了控件在布局中的伸缩比例
        main_layout.addWidget(left_panel, 1) # 占 1/6
        main_layout.addWidget(center_panel, 3) # 占 3/6
        main_layout.addWidget(right_panel, 2) # 占 2/6

    def create_left_panel(self):
        """创建左侧面板，包含文件导入和列表"""
        # 使用 QFrame 提供视觉边界
        left_frame = QFrame()
        left_frame.setFrameShape(QFrame.Shape.StyledPanel)
        
        # 垂直布局
        layout = QVBoxLayout(left_frame)

        # 按钮水平布局
        button_layout = QHBoxLayout()
        btn_import_images = QPushButton("导入图片")
        btn_import_folder = QPushButton("导入文件夹")
        button_layout.addWidget(btn_import_images)
        button_layout.addWidget(btn_import_folder)
        
        # 文件列表
        list_label = QLabel("图片列表")
        self.image_list_widget = QListWidget() # 使用 self，使其成为实例变量

        layout.addLayout(button_layout)
        layout.addWidget(list_label)
        layout.addWidget(self.image_list_widget)
        
        return left_frame

    def create_center_panel(self):
        """创建中间面板，用于图片预览"""
        center_frame = QFrame()
        center_frame.setFrameShape(QFrame.Shape.StyledPanel)
        
        layout = QVBoxLayout(center_frame)
        
        self.preview_label = QLabel("图片预览区")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("border: 2px dashed #aaa;") # 添加一点样式方便看清范围
        
        layout.addWidget(self.preview_label)
        
        return center_frame

    def create_right_panel(self):
        """创建右侧面板，用于水印设置"""
        right_frame = QFrame()
        right_frame.setFrameShape(QFrame.Shape.StyledPanel)
        
        layout = QVBoxLayout(right_frame)
        
        # --- 水印设置控件 (当前为占位) ---
        settings_label = QLabel("水印设置")
        settings_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        text_label = QLabel("水印文本:")
        self.watermark_text_input = QLineEdit("© Your Name")

        # ... 这里未来会添加字体、颜色、透明度等更多控件 ...
        
        # 导出按钮
        self.btn_export = QPushButton("导出所有图片")

        layout.addWidget(settings_label)
        layout.addSpacing(20) # 添加一些间距
        layout.addWidget(text_label)
        layout.addWidget(self.watermark_text_input)
        layout.addStretch() # 添加一个伸缩弹簧，将下面的按钮推到底部
        layout.addWidget(self.btn_export)

        return right_frame

# --- 应用程序入口 ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
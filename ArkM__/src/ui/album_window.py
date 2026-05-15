"""专辑封面浏览窗口"""
import os

from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QScrollArea, QGridLayout, QMessageBox)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QIcon


class AlbumCard(QWidget):
    """单张专辑封面卡片"""

    def __init__(self, album: dict, parent=None):
        """初始化卡片：加载封面图和专辑名。"""
        super().__init__(parent)
        self.album = album
        self.setFixedSize(220, 280)
        self.setStyleSheet("""
            AlbumCard {
                background: rgba(40, 40, 40, 0.8);
                border: 1px solid #555555;
                border-radius: 8px;
            }
            AlbumCard:hover {
                border: 1px solid #888888;
                background: rgba(50, 50, 50, 0.8);
            }
        """)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        # 封面图
        self.image_label = QLabel()
        self.image_label.setFixedSize(200, 200)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setScaledContents(False)

        local_path = album.get("local_path", "")
        if local_path and os.path.exists(local_path):
            pixmap = QPixmap(local_path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.image_label.setPixmap(scaled)
            else:
                self.image_label.setText("封面损坏")
        else:
            self.image_label.setText("暂无封面")

        layout.addWidget(self.image_label, alignment=Qt.AlignCenter)

        # 专辑名
        name_label = QLabel(album.get("name", "未知专辑"))
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setWordWrap(True)
        name_label.setStyleSheet("""
            QLabel {
                color: #e0e0e0;
                font-size: 11px;
                font-weight: bold;
                background: transparent;
                border: none;
            }
        """)
        layout.addWidget(name_label)

    def mouseDoubleClickEvent(self, event):
        """双击放大查看"""
        local_path = self.album.get("local_path", "")
        if local_path and os.path.exists(local_path):
            dlg = PreviewDialog(self.album, self)
            dlg.exec()


class PreviewDialog(QMainWindow):
    """封面预览窗口"""

    def __init__(self, album: dict, parent=None):
        """初始化预览窗口：展示大尺寸封面图。"""
        super().__init__(parent)
        self.setWindowTitle(f"专辑封面: {album.get('name', '')}")
        self.setWindowIcon(QIcon("prts.ico"))
        self.setMinimumSize(600, 600)
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                           stop:0 #1a1a1a, stop:0.5 #2a2a2a, stop:1 #1a1a1a);
            }
        """)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        image_label = QLabel()
        image_label.setAlignment(Qt.AlignCenter)

        local_path = album.get("local_path", "")
        if local_path and os.path.exists(local_path):
            pixmap = QPixmap(local_path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(560, 560, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                image_label.setPixmap(scaled)
            else:
                image_label.setText("封面损坏")
        else:
            image_label.setText("暂无封面")

        layout.addWidget(image_label)

        name_label = QLabel(album.get("name", "未知专辑"))
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setStyleSheet("color: #e0e0e0; font-size: 16px; font-weight: bold;")
        layout.addWidget(name_label)


class AlbumWindow(QMainWindow):
    """专辑封面浏览窗口"""

    def __init__(self, controller, parent=None):
        """初始化专辑浏览窗口：网格布局展示所有专辑封面。"""
        super().__init__(parent)
        self._controller = controller

        self.setWindowTitle("专辑封面浏览")
        self.setWindowIcon(QIcon("prts.ico"))
        self.setMinimumSize(800, 600)
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                           stop:0 #1a1a1a, stop:0.5 #2a2a2a, stop:1 #1a1a1a);
            }
        """)

        central = QWidget()
        self.setCentralWidget(central)
        outer_layout = QVBoxLayout(central)

        # 标题
        title = QLabel("专辑封面一览")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #e0e0e0; font-size: 18px; font-weight: bold; padding: 10px;")
        outer_layout.addWidget(title)

        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        scroll.setWidget(container)

        self.grid = QGridLayout(container)
        self.grid.setSpacing(12)
        self.grid.setContentsMargins(20, 10, 20, 10)

        outer_layout.addWidget(scroll)

        # 加载封面
        self._load_albums()

    def _load_albums(self):
        """从后端加载所有专辑封面"""
        albums = self._controller.get_all_albums()
        cols = 3
        for i, album in enumerate(albums):
            card = AlbumCard(album)
            row = i // cols
            col = i % cols
            self.grid.addWidget(card, row, col, Qt.AlignCenter)

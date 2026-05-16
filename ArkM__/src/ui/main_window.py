"""主窗口 — 网易云风格布局：无边框 + 自绘标题栏 + 系统托盘"""
import json
import os
import sys
import signal

from PySide6.QtWidgets import (
    QMainWindow, QApplication, QMessageBox, QListWidgetItem,
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLineEdit, QPushButton, QListWidget, QLabel,
    QSlider, QTextBrowser, QSystemTrayIcon, QMenu,
)
from PySide6.QtCore import QTimer, QTime, Signal, QThread, Qt
from PySide6.QtGui import QKeySequence, QShortcut, QIcon, QPixmap, QAction

from ark_style import ARK_STYLESHEET
from utils.logger import EnhancedLogger
from core.music_player import MusicPlayer
from core.api_client import ArkMApiClient


# ---- 线程 ----

class DownloadThread(QThread):
    finished = Signal(bool, str)
    progress = Signal(str, int, int)

    def __init__(self, music_name: str):
        super().__init__()
        self.music_name = music_name

    def run(self):
        try:
            api = ArkMApiClient()
            resp = api.download(self.music_name)
            for line in resp.iter_lines(decode_unicode=True):
                if not line or not line.startswith("data: "):
                    continue
                data = json.loads(line[6:])
                if data["type"] == "progress":
                    self.progress.emit(data["filename"], data["downloaded"], data["total"])
                elif data["type"] == "result":
                    self.finished.emit(data["success"], data["message"])
                    return
            self.finished.emit(False, f"下载失败: {self.music_name}")
        except Exception as e:
            self.finished.emit(False, f"下载出错: {str(e)}")


class DeleteThread(QThread):
    finished = Signal(bool, str)

    def __init__(self, music_name: str):
        super().__init__()
        self.music_name = music_name

    def run(self):
        try:
            api = ArkMApiClient()
            data = api.delete(self.music_name)
            self.finished.emit(data["success"], data["message"])
        except Exception as e:
            self.finished.emit(False, f"删除出错: {str(e)}")


# ---- 主窗口 ----

from .main_handlers import MainHandlersMixin

class MainWindow(QMainWindow, MainHandlersMixin):
    def __init__(self, dr_name: str = "", on_quit=None):
        super().__init__(None, Qt.WindowType.FramelessWindowHint)
        self._dr_name = dr_name
        self._on_quit = on_quit
        self.setMinimumSize(1100, 650)
        self.setWindowIcon(QIcon("prts.ico"))
        self.setStyleSheet(ARK_STYLESHEET)
        self.setWindowOpacity(0.88)

        self._download_thread = None
        self._delete_thread = None
        self._drag_pos = None
        self._play_queue: list[str] = []
        self._download_queue: list[str] = []

        self._build_ui()
        self._init_data()
        self._setup_tray()
        self._wire_signals()
        self._setup_shortcuts()
        self._center_window()

    # ======================== UI 构建 ========================

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ---- 自绘标题栏 ----
        title_bar = QWidget()
        title_bar.setObjectName("titleBar")
        title_bar.setFixedHeight(32)
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(10, 0, 4, 0)
        title_bar_layout.setSpacing(0)

        self.titleLabel = QLabel(f"  ArkM - 欢迎, Dr.{self._dr_name}")
        self.titleLabel.setObjectName("titleLabel")
        self.titleLabel.setStyleSheet("border:none;background:transparent;color:#ddd;font-size:12px;font-weight:bold;")
        title_bar_layout.addWidget(self.titleLabel)
        title_bar_layout.addStretch()

        # 最小化按钮
        min_btn = QPushButton("—")
        min_btn.setObjectName("titleMinBtn")
        min_btn.setFixedSize(28, 24)
        min_btn.clicked.connect(self.showMinimized)
        title_bar_layout.addWidget(min_btn)

        # 关闭按钮
        close_btn = QPushButton("✕")
        close_btn.setObjectName("titleCloseBtn")
        close_btn.setFixedSize(28, 24)
        close_btn.clicked.connect(self._on_close_click)
        title_bar_layout.addWidget(close_btn)

        root_layout.addWidget(title_bar)

        # ---- 主区：左侧标签页 + 右侧封面区 ----
        body_wrapper = QWidget()
        body_wrapper.setContentsMargins(6, 4, 6, 4)
        body_layout = QVBoxLayout(body_wrapper)
        body_layout.setContentsMargins(6, 4, 6, 4)
        body_layout.setSpacing(4)
        body = QHBoxLayout()
        body.setSpacing(8)

        # 左侧面板 (固定宽度)
        left = QWidget()
        left.setFixedWidth(340)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("musicTabs")
        left_layout.addWidget(self.tabs)

        # 标签页1：待下载
        download_tab, dl_ctrls = self._make_list_tab("download", "下载")
        self.downloadSearchInput, self.downloadSearchButton, self.downloadlistWidget, self.downloadButton, self.downloadRefreshButton = dl_ctrls
        self.tabs.addTab(download_tab, "📥 待下载")

        # 标签页2：已下载
        music_tab, mu_ctrls = self._make_list_tab("music", "删除")
        self.musicSearchInput, self.musicSearchButton, self.musicListWidget, self.deletButton, self.musicRefreshButton = mu_ctrls
        self.tabs.addTab(music_tab, "📀 本机曲库")

        body.addWidget(left)

        # 右侧封面 + 播放控制区
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(4, 4, 4, 4)
        right_layout.setSpacing(8)

        # 封面图
        self.albumImage = QLabel()
        self.albumImage.setObjectName("albumImage")
        self.albumImage.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.albumImage.setMinimumSize(320, 320)
        self.albumImage.setText("点击歌曲查看封面")
        self.albumImage.setStyleSheet("""
            QLabel#albumImage {
                background: rgba(30,30,30,0.8);
                border: 1px solid #444;
                border-radius: 8px;
                color: #999;
                font-size: 14px;
            }
        """)
        right_layout.addWidget(self.albumImage, stretch=3)

        # 歌曲信息
        self.songInfoLabel = QLabel("未在播放")
        self.songInfoLabel.setObjectName("songInfoLabel")
        self.songInfoLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.songInfoLabel.setStyleSheet("font-size: 13px; font-weight: bold; color: #ddd; border: none; background: transparent;")
        right_layout.addWidget(self.songInfoLabel)

        # 进度条 + 时间
        progress_row = QHBoxLayout()
        self.label_3 = QLabel("00:00 / 00:00")
        self.label_3.setObjectName("label_3")
        self.label_3.setStyleSheet("color: #aaa; font-size: 10px; border: none; background: transparent;")
        progress_row.addWidget(self.label_3)

        self.progressSlider = QSlider(Qt.Orientation.Horizontal)
        self.progressSlider.setObjectName("progressSlider")
        progress_row.addWidget(self.progressSlider, stretch=1)
        right_layout.addLayout(progress_row)

        # 播放按钮行
        btn_row = QHBoxLayout()
        btn_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.playButton = QPushButton("▶ 播放")
        self.playButton.setObjectName("playButton")
        self.pauseButton = QPushButton("⏸ 暂停")
        self.pauseButton.setObjectName("pauseButton")
        self.stopButton = QPushButton("⏹ 停止")
        self.stopButton.setObjectName("stopButton")
        for btn in (self.playButton, self.pauseButton, self.stopButton):
            btn.setFixedWidth(90)
            btn_row.addWidget(btn)
        right_layout.addLayout(btn_row)

        # 音量行
        vol_row = QHBoxLayout()
        vol_label = QLabel("🔊")
        vol_label.setStyleSheet("border: none; background: transparent;")
        vol_row.addWidget(vol_label)
        self.volumeSlider = QSlider(Qt.Orientation.Horizontal)
        self.volumeSlider.setObjectName("volumeSlider")
        self.volumeSlider.setMaximumWidth(200)
        self.volumeSlider.setValue(50)
        vol_row.addWidget(self.volumeSlider)
        vol_row.addStretch()
        right_layout.addLayout(vol_row)

        # 状态栏
        self.statusLabel = QLabel("")
        self.statusLabel.setObjectName("statusLabel")
        self.statusLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.statusLabel.setStyleSheet("color: #888; font-size: 11px; border: none; background: transparent; padding: 4px;")
        right_layout.addWidget(self.statusLabel)

        right_layout.addStretch()

        body.addWidget(right, stretch=1)
        body_layout.addLayout(body, stretch=1)
        root_layout.addWidget(body_wrapper, stretch=1)

        # ---- 底部折叠区 (日志 + 下载进度) ----
        bottom = QWidget()
        bottom_layout = QVBoxLayout(bottom)
        bottom_layout.setContentsMargins(0, 2, 0, 0)
        bottom_layout.setSpacing(2)

        # 折叠按钮
        self.toggleLogBtn = QPushButton("▲ 日志")
        self.toggleLogBtn.setObjectName("toggleLogBtn")
        self.toggleLogBtn.setFixedHeight(22)
        bottom_layout.addWidget(self.toggleLogBtn)

        # 日志区域 (默认隐藏)
        self.logArea = QWidget()
        log_area_layout = QVBoxLayout(self.logArea)
        log_area_layout.setContentsMargins(0, 0, 0, 0)
        log_area_layout.setSpacing(2)

        self.logBrowser = QTextBrowser()
        self.logBrowser.setObjectName("logBrowser")
        self.logBrowser.setMaximumHeight(120)
        log_area_layout.addWidget(self.logBrowser)

        log_btn_row = QHBoxLayout()
        self.clearLogButton = QPushButton("清空日志")
        self.clearLogButton.setObjectName("clearLogButton")
        log_btn_row.addWidget(self.clearLogButton)
        log_btn_row.addStretch()
        log_area_layout.addLayout(log_btn_row)
        bottom_layout.addWidget(self.logArea)
        self.logArea.setVisible(False)

        # 下载进度
        self.downloadBrowser = QTextBrowser()
        self.downloadBrowser.setObjectName("downloadBrowser")
        self.downloadBrowser.setMaximumHeight(28)
        bottom_layout.addWidget(self.downloadBrowser)

        root_layout.addWidget(bottom)

    def _make_list_tab(self, prefix: str, primary_label: str) -> tuple[QWidget, tuple]:
        """创建标签页内容。返回 (tab_widget, (search_input, search_btn, list_widget, primary_btn, refresh_btn))"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        search_input = QLineEdit()
        search_input.setPlaceholderText("搜索歌曲...")
        search_btn = QPushButton("搜索")
        list_widget = QListWidget()
        list_widget.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        primary_btn = QPushButton(primary_label)
        refresh_btn = QPushButton("刷新")

        search_row = QHBoxLayout()
        search_row.addWidget(search_input, stretch=1)
        search_row.addWidget(search_btn)
        layout.addLayout(search_row)
        layout.addWidget(list_widget, stretch=1)
        btn_row = QHBoxLayout()
        btn_row.addWidget(primary_btn)
        btn_row.addWidget(refresh_btn)
        layout.addLayout(btn_row)

        return tab, (search_input, search_btn, list_widget, primary_btn, refresh_btn)

    # ======================== 信号连接 ========================

    def _wire_signals(self):
        # 下载标签页
        self.downloadSearchInput.textChanged.connect(lambda: self._download_timer.start(500))
        self.downloadSearchButton.clicked.connect(self._on_download_search)
        self.downloadRefreshButton.clicked.connect(self._refresh_download_view)
        self.downloadlistWidget.itemDoubleClicked.connect(self._on_download_double_click)
        self.downloadlistWidget.currentItemChanged.connect(self._on_download_selected)
        self.downloadButton.clicked.connect(self._on_download_button)

        # 音乐标签页
        self.musicSearchInput.textChanged.connect(lambda: self._music_timer.start(500))
        self.musicSearchButton.clicked.connect(self._on_music_search)
        self.musicRefreshButton.clicked.connect(self._refresh_music_view)
        self.musicListWidget.itemDoubleClicked.connect(self._on_music_double_click)
        self.musicListWidget.currentItemChanged.connect(self._on_music_selected)
        self.deletButton.clicked.connect(self._on_delete_button)

        # 播放
        self.playButton.clicked.connect(self._on_play_button)
        self.pauseButton.clicked.connect(self._on_pause)
        self.stopButton.clicked.connect(self._on_stop)
        self.progressSlider.sliderMoved.connect(self._player.set_position)
        self.volumeSlider.valueChanged.connect(self._player.set_volume)

        # 底部折叠
        self.toggleLogBtn.clicked.connect(self._toggle_log)

        # 日志
        self.clearLogButton.clicked.connect(self._on_clear_log)

        # 播放器信号
        self._player.player.positionChanged.connect(self._on_position_changed)
        self._player.player.durationChanged.connect(self._on_duration_changed)
        self._player.player.playbackStateChanged.connect(self._on_state_changed)
        self._player._progress_timer.timeout.connect(self._update_time_label)

        # 搜索防抖定时器
        self._download_timer = QTimer(singleShot=True)
        self._download_timer.timeout.connect(self._on_download_search)
        self._music_timer = QTimer(singleShot=True)
        self._music_timer.timeout.connect(self._on_music_search)

    def _setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+F"), self).activated.connect(self.downloadSearchInput.setFocus)
        QShortcut(QKeySequence("Ctrl+G"), self).activated.connect(self.musicSearchInput.setFocus)
        QShortcut(QKeySequence("Ctrl+D"), self).activated.connect(self._on_download_button)
        QShortcut(QKeySequence("Ctrl+Delete"), self).activated.connect(self._on_delete_button)
        QShortcut(QKeySequence("Ctrl+L"), self).activated.connect(self._on_clear_log)

    # ======================== 窗口拖动（必须在 MainWindow 本体，Mixin MRO 不命中） ========================

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and event.position().y() <= 32:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if getattr(self, '_drag_pos', None) is not None:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        super().mouseReleaseEvent(event)

    # ======================== 初始化 ========================

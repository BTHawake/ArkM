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
from core.music_controller import MusicController
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

class MainWindow(QMainWindow):
    def __init__(self, dr_name: str = "", on_quit=None):
        super().__init__(None, Qt.WindowType.FramelessWindowHint)
        self._dr_name = dr_name
        self._on_quit = on_quit
        self.setMinimumSize(1100, 650)
        self.setWindowIcon(QIcon("prts.ico"))
        self.setStyleSheet(ARK_STYLESHEET)

        self._download_thread = None
        self._delete_thread = None
        self._drag_pos = None

        self._build_ui()
        self._init_data()
        self._setup_tray()
        self._wire_signals()
        self._setup_shortcuts()
        self._setup_menubar()
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
        self.albumImage.setMinimumSize(280, 280)
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

    def _setup_menubar(self):
        pass

    # ======================== 初始化 ========================

    def _init_data(self):
        self._logger = EnhancedLogger(self.logBrowser, self.downloadBrowser)
        self._player = MusicPlayer(self._logger.log)
        self._controller = MusicController(self._logger.log)
        self._controller.init()
        self._refresh_download_view()
        self._refresh_music_view()
        self._logger.clear()
        self._logger.log("ArkM 音乐系统初始化完成", "SUCCESS")
        self._logger.log(f"您好, Dr.{self._dr_name}", "SUCCESS")

    # ======================== 列表刷新 ========================

    def _refresh_download_view(self):
        keyword = self.downloadSearchInput.text()
        items = self._controller.filter_download_items(keyword)
        self.downloadlistWidget.clear()
        for name in items:
            self.downloadlistWidget.addItem(QListWidgetItem(name))
        self._logger.log(f"待下载: {len(items)} 首", "INFO")

    def _refresh_music_view(self):
        keyword = self.musicSearchInput.text()
        items = self._controller.filter_music_items(keyword)
        self.musicListWidget.clear()
        for name in items:
            self.musicListWidget.addItem(QListWidgetItem(name))
        self._logger.log(f"已下载: {len(items)} 首", "INFO")

    # ======================== 搜索 ========================

    def _on_download_search(self):
        self._refresh_download_view()

    def _on_music_search(self):
        self._refresh_music_view()

    # ======================== 下载 ========================

    def _on_download_double_click(self, item):
        music_name = item.text()
        reply = QMessageBox.question(self, "ArkM", f"确定下载《{music_name}》吗？",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.Yes)
        if reply == QMessageBox.StandardButton.Yes:
            self._start_download(music_name)

    def _on_download_button(self):
        row = self.downloadlistWidget.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选择一首歌曲")
            return
        self._start_download(self.downloadlistWidget.item(row).text())

    def _start_download(self, music_name: str):
        if self._download_thread and self._download_thread.isRunning():
            self._logger.log("下载任务进行中，请稍候", "WARNING")
            return
        self._download_thread = DownloadThread(music_name)
        self._download_thread.finished.connect(self._on_download_done)
        self._download_thread.progress.connect(self._logger.update_progress)
        self._download_thread.start()
        self.downloadButton.setEnabled(False)
        self._logger.log(f"开始下载: {music_name}", "INFO")

    def _on_download_done(self, success: bool, message: str):
        self.downloadButton.setEnabled(True)
        self._logger.clear_progress()
        if success:
            self._controller.on_download_done(success, message)
            self._refresh_download_view()
            self._refresh_music_view()
            QMessageBox.information(self, "ArkM", f"下载成功！")
        else:
            self._logger.log(message, "ERROR")

    # ======================== 删除 ========================

    def _on_delete_button(self):
        row = self.musicListWidget.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选择一首歌曲")
            return
        music_name = self.musicListWidget.item(row).text()
        reply = QMessageBox.question(self, "ArkM", f"确定删除《{music_name}》？此操作不可撤销！",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            if self._delete_thread and self._delete_thread.isRunning():
                self._logger.log("删除任务进行中，请稍候", "WARNING")
                return
            self._delete_thread = DeleteThread(music_name)
            self._delete_thread.finished.connect(self._on_delete_done)
            self._delete_thread.start()

    def _on_delete_done(self, success: bool, message: str):
        if success:
            self._controller.on_download_done(success, message)
            self._refresh_download_view()
            self._refresh_music_view()
            QMessageBox.information(self, "成功", "删除成功！")
        else:
            self._logger.log(message, "ERROR")

    # ======================== 播放 ========================

    def _on_music_double_click(self, item):
        name = item.text()
        self._player.play(name)
        self._load_album_image(name)
        self._highlight_playing(name)

    def _on_play_button(self):
        row = self.musicListWidget.currentRow()
        if row >= 0:
            name = self.musicListWidget.item(row).text()
            self._player.play(name)
            self._load_album_image(name)
            self._highlight_playing(name)
        else:
            self._player.resume()

    def _on_pause(self):
        self._player.pause()

    def _on_stop(self):
        self._player.stop()
        self.progressSlider.setValue(0)
        self.label_3.setText("00:00 / 00:00")
        self.songInfoLabel.setText("未在播放")
        self.statusLabel.setText("")
        self._clear_highlight()

    def _on_position_changed(self, position: int):
        if not self.progressSlider.isSliderDown():
            self.progressSlider.setValue(position)

    def _on_duration_changed(self, duration: int):
        self.progressSlider.setRange(0, duration)

    def _on_state_changed(self, state):
        from PySide6.QtMultimedia import QMediaPlayer
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.playButton.setText("▶ 播放中")
            music = self._player.current_music
            if music:
                self.songInfoLabel.setText(music)
                self.statusLabel.setText(f"正在播放: {music}")
        elif state == QMediaPlayer.PlaybackState.PausedState:
            self.playButton.setText("▶ 播放")
            self.statusLabel.setText("已暂停")
        elif state == QMediaPlayer.PlaybackState.StoppedState:
            self.playButton.setText("▶ 播放")
            self.progressSlider.setValue(0)
            self.label_3.setText("00:00 / 00:00")
            self.songInfoLabel.setText("未在播放")
            self.statusLabel.setText("")
            self._clear_highlight()

    def _update_time_label(self):
        player = self._player.player
        if player.duration() > 0:
            c = QTime(0, 0).addMSecs(player.position())
            t = QTime(0, 0).addMSecs(player.duration())
            self.label_3.setText(f"{c.toString('mm:ss')} / {t.toString('mm:ss')}")

    # ======================== 封面 ========================

    def _on_download_selected(self, current, previous):
        if current:
            self._load_album_image(current.text())

    def _on_music_selected(self, current, previous):
        if current:
            self._load_album_image(current.text())

    def _load_album_image(self, music_name: str):
        try:
            album = self._controller.get_album_cover(music_name)
            if album and album.get("cover_path") and os.path.exists(album["cover_path"]):
                pixmap = QPixmap(album["cover_path"])
                if not pixmap.isNull():
                    self.albumImage.clear()
                    self.albumImage.setPixmap(pixmap)
                    return
            self.albumImage.clear()
            self.albumImage.setText("点击歌曲查看封面")
        except Exception as e:
            self._logger.log(f"封面加载失败: {e}", "ERROR")

    def _open_album_window(self):
        from ui.album_window import AlbumWindow
        w = AlbumWindow(self._controller)
        w.show()

    # ======================== 播放高亮 ========================

    def _highlight_playing(self, music_name: str):
        """在已下载列表中高亮当前播放歌曲"""
        self._clear_highlight()
        for i in range(self.musicListWidget.count()):
            item = self.musicListWidget.item(i)
            if item.text() == music_name:
                font = item.font()
                font.setBold(True)
                item.setFont(font)
                item.setText(f"▶ {music_name}")
                item.setForeground(Qt.GlobalColor("#00cc88"))
                break

    def _clear_highlight(self):
        """清除所有高亮"""
        for lst in (self.musicListWidget,):
            for i in range(lst.count()):
                item = lst.item(i)
                text = item.text()
                if text.startswith("▶ "):
                    item.setText(text[2:])
                font = item.font()
                font.setBold(False)
                item.setFont(font)
                item.setData(Qt.ItemDataRole.ForegroundRole, None)

    # ======================== 键盘事件 ========================

    def keyPressEvent(self, event):
        key = event.key()

        # 判断哪个列表有焦点或当前标签页
        current_tab = self.tabs.currentIndex()
        if current_tab == 1:  # 已下载标签页
            lst = self.musicListWidget
        else:
            lst = self.downloadlistWidget

        if key == Qt.Key.Key_Up:
            row = lst.currentRow()
            if row > 0:
                lst.setCurrentRow(row - 1)
        elif key == Qt.Key.Key_Down:
            row = lst.currentRow()
            if row < lst.count() - 1:
                lst.setCurrentRow(row + 1)
        elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            row = lst.currentRow()
            if row >= 0:
                if current_tab == 1:
                    name = lst.item(row).text().replace("▶ ", "")
                    self._player.play(name)
                    self._load_album_image(name)
                    self._highlight_playing(name)
                else:
                    self._start_download(lst.item(row).text())
        elif key == Qt.Key.Key_Space:
            state = self._player.playback_state()
            from PySide6.QtMultimedia import QMediaPlayer as QMP
            if state == QMP.PlaybackState.PlayingState:
                self._player.pause()
            else:
                self._player.resume()
        else:
            super().keyPressEvent(event)

    # ======================== 底部折叠 ========================

    def _toggle_log(self):
        visible = not self.logArea.isVisible()
        self.logArea.setVisible(visible)
        self.toggleLogBtn.setText("▼ 日志" if visible else "▲ 日志")

    def _on_clear_log(self):
        self._logger.clear()

    # ======================== 窗口 ========================

    def _center_window(self):
        screen = QApplication.primaryScreen().availableGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)

    # ======================== 系统托盘 ========================

    def _setup_tray(self):
        self.tray = QSystemTrayIcon(QIcon("prts.ico"), self)
        menu = QMenu()
        show_act = QAction("显示窗口", self)
        show_act.triggered.connect(self._show_from_tray)
        menu.addAction(show_act)

        toggle_act = QAction("播放/暂停", self)
        toggle_act.triggered.connect(self._tray_play_pause)
        menu.addAction(toggle_act)

        menu.addSeparator()
        quit_act = QAction("退出", self)
        quit_act.triggered.connect(self._force_quit)
        menu.addAction(quit_act)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._show_from_tray()

    def _show_from_tray(self):
        self.showNormal()
        self.activateWindow()

    def _tray_play_pause(self):
        from PySide6.QtMultimedia import QMediaPlayer
        if self._player.playback_state() == QMediaPlayer.PlaybackState.PlayingState:
            self._player.pause()
        else:
            self._player.resume()

    # ======================== 关闭 / 退出 ========================

    def _on_close_click(self):
        """点击关闭按钮 → 隐藏到托盘"""
        self.hide()

    def _force_quit(self):
        """从托盘菜单退出"""
        self.tray.hide()
        if self._on_quit:
            self._on_quit()
        QApplication.quit()

    def closeEvent(self, event):
        event.ignore()
        self.hide()

    # ======================== 窗口拖动 ========================

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # 只在标题栏区域拖动
            title_bar = self.findChild(QWidget, "titleBar")
            if title_bar and title_bar.geometry().contains(event.pos()):
                self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            else:
                self._drag_pos = None
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        super().mouseReleaseEvent(event)

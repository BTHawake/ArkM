"""主窗口：UI事件响应，委托给 MusicController（业务）和 MusicPlayer（播放）"""
import json
import os

import requests
from PySide6.QtWidgets import (QMainWindow, QApplication, QMessageBox, QListWidgetItem)
from PySide6.QtGui import QAction
from PySide6.QtCore import QTimer, QTime, Signal, QThread, Qt
from PySide6.QtGui import QKeySequence, QShortcut, QIcon, QPixmap

from widgets.ArkM import Ui_MainWindow
from ark_style import ARK_STYLESHEET
from utils.logger import EnhancedLogger
from core.music_player import MusicPlayer
from core.music_controller import MusicController
from core.api_client import ArkMApiClient


class DownloadThread(QThread):
    """下载线程：通过 HTTP SSE 调后端下载，不阻塞UI"""
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
                    self.progress.emit(
                        data["filename"], data["downloaded"], data["total"]
                    )
                elif data["type"] == "result":
                    self.finished.emit(data["success"], data["message"])
                    return

            self.finished.emit(False, f"下载失败: {self.music_name}")
        except Exception as e:
            self.finished.emit(False, f"下载过程中出错: {str(e)}")


class DeleteThread(QThread):
    """删除线程：通过 HTTP 调后端删除，不阻塞UI"""
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
            self.finished.emit(False, f"删除过程中出错: {str(e)}")


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, dr_name: str = ""):
        super().__init__()
        self.setupUi(self)
        self._dr_name = dr_name

        # 样式和图标
        self.setWindowIcon(QIcon("prts.ico"))
        self.setStyleSheet(ARK_STYLESHEET)
        self.setWindowTitle(f"ArkM音乐系统 - 音乐终端 - 欢迎,Dr.{dr_name}")
        self.setMinimumSize(1000, 700)
        self._center_window()

        # 日志
        self._logger = EnhancedLogger(self.logBrowser, self.downloadBrowser)

        # 播放器
        self._player = MusicPlayer(self._logger.log)
        self._wire_player_signals()

        # 业务控制器
        self._controller = MusicController(self._logger.log)
        self._controller.init()

        # 搜索防抖定时器
        self._download_timer = QTimer(singleShot=True)
        self._download_timer.timeout.connect(self._on_download_search)
        self._music_timer = QTimer(singleShot=True)
        self._music_timer.timeout.connect(self._on_music_search)

        # 线程引用
        self._download_thread = None
        self._delete_thread = None

        # 快捷键
        self._setup_shortcuts()

        # 菜单栏
        self._setup_menubar()

        # 连接信号
        self._wire_ui_signals()

        # 初始化列表
        self._refresh_download_view()
        self._refresh_music_view()

        # 初始化媒体控制
        self.volumeSlider.setValue(50)

        # 初始封面
        self.albumImage.setText("点击歌曲查看专辑封面")
        self.albumImage.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._logger.clear()
        self._logger.log("ArkM音乐系统初始化完成", "SUCCESS")
        self._logger.log(f"您好,Dr.{dr_name}", "SUCCESS")
        self._logger.log("欢迎使用终端音乐管理系统", "INFO")

    # ---- UI 信号接线 ----

    def _wire_ui_signals(self):
        self.downloadSearchInput.textChanged.connect(lambda: self._download_timer.start(500))
        self.downloadSearchButton.clicked.connect(self._on_download_search)
        self.musicSearchInput.textChanged.connect(lambda: self._music_timer.start(500))
        self.musicSearchButton.clicked.connect(self._on_music_search)

        self.downloadRefreshButton.clicked.connect(self._refresh_download_view)
        self.musicRefreshButton.clicked.connect(self._refresh_music_view)

        self.downloadlistWidget.itemDoubleClicked.connect(self._on_download_double_click)
        self.downloadlistWidget.currentItemChanged.connect(self._on_download_selected)
        self.musicListWidget.itemDoubleClicked.connect(self._on_music_double_click)
        self.musicListWidget.currentItemChanged.connect(self._on_music_selected)

        self.downloadButton.clicked.connect(self._on_download_button)
        self.deletButton.clicked.connect(self._on_delete_button)
        self.clearLogButton.clicked.connect(self._on_clear_log)

        self.playButton.clicked.connect(self._on_play_button)
        self.pauseButton.clicked.connect(self._on_pause)
        self.stopButton.clicked.connect(self._on_stop)

        self.progressSlider.sliderMoved.connect(self._player.set_position)
        self.volumeSlider.valueChanged.connect(self._player.set_volume)

    def _wire_player_signals(self):
        self._player.player.positionChanged.connect(self._on_position_changed)
        self._player.player.durationChanged.connect(self._on_duration_changed)
        self._player.player.playbackStateChanged.connect(self._on_state_changed)
        self._player._progress_timer.timeout.connect(self._update_time_label)

    # ---- 快捷键 ----

    def _setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+F"), self).activated.connect(self.downloadSearchInput.setFocus)
        QShortcut(QKeySequence("Ctrl+G"), self).activated.connect(self.musicSearchInput.setFocus)
        QShortcut(QKeySequence("Ctrl+D"), self).activated.connect(self._on_download_button)
        QShortcut(QKeySequence("Ctrl+Delete"), self).activated.connect(self._on_delete_button)
        QShortcut(QKeySequence("Ctrl+L"), self).activated.connect(self._on_clear_log)

    # ---- 列表刷新 ----

    def _refresh_download_view(self):
        keyword = self.downloadSearchInput.text()
        items = self._controller.filter_download_items(keyword)
        self.downloadlistWidget.clear()
        for name in items:
            self.downloadlistWidget.addItem(QListWidgetItem(name))
        self._logger.log(f"刷新待下载列表: 显示 {len(items)} 首歌曲", "INFO")

    def _refresh_music_view(self):
        keyword = self.musicSearchInput.text()
        items = self._controller.filter_music_items(keyword)
        self.musicListWidget.clear()
        for name in items:
            self.musicListWidget.addItem(QListWidgetItem(name))
        self._logger.log(f"刷新已下载列表: 显示 {len(items)} 首歌曲", "INFO")

    # ---- 搜索事件 ----

    def _on_download_search(self):
        self._logger.log(f"搜索待下载曲目: '{self.downloadSearchInput.text().strip()}'", "INFO")
        self._refresh_download_view()

    def _on_music_search(self):
        self._logger.log(f"搜索本地曲库: '{self.musicSearchInput.text().strip()}'", "INFO")
        self._refresh_music_view()

    # ---- 下载相关 ----

    def _on_download_double_click(self, item):
        music_name = item.text()
        self._logger.log(f"准备下载: {music_name}", "INFO")
        reply = QMessageBox.question(
            self, "ArkM", f"Dr.{self._dr_name},您确定要下载《{music_name}》吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._start_download(music_name)

    def _on_download_button(self):
        row = self.downloadlistWidget.currentRow()
        if row < 0:
            self._logger.log("请先在待下载列表中选择一首歌曲", "WARNING")
            QMessageBox.warning(self, "提示", "请先在待下载列表中选择一首歌曲")
            return
        self._start_download(self.downloadlistWidget.item(row).text())

    def _start_download(self, music_name: str):
        if self._download_thread and self._download_thread.isRunning():
            self._logger.log("当前有下载任务正在进行，请稍候", "WARNING")
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
            QMessageBox.information(self, "ArkM", f"Dr.{self._dr_name},下载成功啦！")
        else:
            self._logger.log(message, "ERROR")
            QMessageBox.warning(self, "失败", message)

    # ---- 删除相关 ----

    def _on_delete_button(self):
        row = self.musicListWidget.currentRow()
        if row < 0:
            self._logger.log("请先在已下载列表中选择一首歌曲", "WARNING")
            QMessageBox.warning(self, "提示", "请先在已下载列表中选择一首歌曲")
            return
        music_name = self.musicListWidget.item(row).text()
        reply = QMessageBox.question(
            self, "ArkM", f"Dr.{self._dr_name},您确定要删除《{music_name}》吗？此操作不可撤销！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._start_delete(music_name)

    def _start_delete(self, music_name: str):
        if self._delete_thread and self._delete_thread.isRunning():
            self._logger.log("当前有删除任务正在进行，请稍候", "WARNING")
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
            QMessageBox.warning(self, "失败", message)

    # ---- 播放相关 ----

    def _on_music_double_click(self, item):
        music_name = item.text()
        self._player.play(music_name)
        self._load_album_image(music_name)

    def _on_play_button(self):
        row = self.musicListWidget.currentRow()
        if row >= 0:
            music_name = self.musicListWidget.item(row).text()
            self._player.play(music_name)
            self._load_album_image(music_name)
        else:
            self._player.resume()

    def _on_pause(self):
        self._player.pause()

    def _on_stop(self):
        self._player.stop()
        self.progressSlider.setValue(0)
        self._update_time_label()
        self.label_3.setText("播放进度: 00:00/00:00")

    def _on_position_changed(self, position: int):
        if not self.progressSlider.isSliderDown():
            self.progressSlider.setValue(position)

    def _on_duration_changed(self, duration: int):
        self.progressSlider.setRange(0, duration)

    def _on_state_changed(self, state):
        from PySide6.QtMultimedia import QMediaPlayer
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.playButton.setText("播放中")
        elif state == QMediaPlayer.PlaybackState.PausedState:
            self.playButton.setText("播放")
        elif state == QMediaPlayer.PlaybackState.StoppedState:
            self.playButton.setText("播放")
            self.progressSlider.setValue(0)

    def _update_time_label(self):
        player = self._player.player
        if player.duration() > 0:
            c = QTime(0, 0).addMSecs(player.position())
            t = QTime(0, 0).addMSecs(player.duration())
            self.label_3.setText(f"播放进度: {c.toString('mm:ss')}/{t.toString('mm:ss')}")

    # ---- 封面图片 ----

    def _on_download_selected(self, current, previous):
        """选中待下载列表中的歌曲时显示封面"""
        if current:
            self._load_album_image(current.text())

    def _on_music_selected(self, current, previous):
        """选中已下载列表中的歌曲时显示封面"""
        if current:
            self._load_album_image(current.text())

    def _load_album_image(self, music_name: str):
        """根据歌名加载专辑封面到 albumImage"""
        try:
            album = self._controller.get_album_cover(music_name)
            if album and album.get("cover_path") and os.path.exists(album["cover_path"]):
                pixmap = QPixmap(album["cover_path"])
                if not pixmap.isNull():
                    self.albumImage.clear()
                    self.albumImage.setPixmap(pixmap)
                    return
            self.albumImage.clear()
            self.albumImage.setText(f"暂无封面: {music_name}")
        except Exception as e:
            self._logger.log(f"加载封面失败: {e}", "ERROR")

    def _setup_menubar(self):
        """设置菜单栏"""
        menubar = self.menuBar()
        view_menu = menubar.addMenu("查看")
        album_action = QAction("专辑封面浏览", self)
        album_action.triggered.connect(self._open_album_window)
        view_menu.addAction(album_action)

    def _open_album_window(self):
        """打开专辑封面浏览窗口"""
        from ui.album_window import AlbumWindow
        self._album_window = AlbumWindow(self._controller)
        self._album_window.show()

    # ---- 日志 ----

    def _on_clear_log(self):
        self._logger.clear()

    # ---- 窗口 ----

    def _center_window(self):
        screen = QApplication.primaryScreen().availableGeometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.height()) // 2,
        )

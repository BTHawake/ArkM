"""事件处理 Mixin：所有下载/删除/播放/队列/封面/键盘/托盘逻辑"""
import json
import os

from PySide6.QtWidgets import (
    QMainWindow, QApplication, QMessageBox, QListWidgetItem,
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLineEdit, QPushButton, QListWidget, QLabel,
    QSlider, QTextBrowser, QSystemTrayIcon, QMenu,
)
from PySide6.QtCore import QTimer, QTime, Signal, QThread, Qt
from PySide6.QtGui import QKeySequence, QShortcut, QIcon, QPixmap, QAction

from utils.logger import EnhancedLogger
from core.music_player import MusicPlayer
from core.music_controller import MusicController
from core.api_client import ArkMApiClient


class MainHandlersMixin:
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
        keyword = self.downloadSearchInput.text().strip()
        items = self._controller.filter_download_items(keyword)
        self.downloadlistWidget.clear()
        for name in items:
            item = QListWidgetItem()
            self._set_item_highlight(item, name, keyword)
            self.downloadlistWidget.addItem(item)
        self._logger.log(f"待下载: {len(items)} 首", "INFO")

    def _refresh_music_view(self):
        keyword = self.musicSearchInput.text().strip()
        items = self._controller.filter_music_items(keyword)
        self.musicListWidget.clear()
        for name in items:
            item = QListWidgetItem()
            self._set_item_highlight(item, name, keyword)
            self.musicListWidget.addItem(item)
        self._logger.log(f"已下载: {len(items)} 首", "INFO")

    @staticmethod
    def _set_item_highlight(item: QListWidgetItem, name: str, keyword: str):
        """搜索关键词高亮：匹配时加绿色前景色"""
        item.setText(name)
        if keyword and keyword.lower() in name.lower():
            item.setForeground(Qt.GlobalColor("#00cc88"))
        else:
            item.setData(Qt.ItemDataRole.ForegroundRole, None)

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
        selected = self.downloadlistWidget.selectedItems()
        if not selected:
            QMessageBox.warning(self, "提示", "请先选择歌曲")
            return
        names = [it.text() for it in selected]
        if len(names) > 1:
            reply = QMessageBox.question(self, "ArkM", f"确定下载 {len(names)} 首歌曲吗？",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.Yes)
            if reply != QMessageBox.StandardButton.Yes:
                return
        self._download_queue = names
        self._process_download_queue()

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

    def _process_download_queue(self):
        """批量下载：从队列取下一首开始"""
        if not self._download_queue:
            self.downloadButton.setEnabled(True)
            return
        name = self._download_queue.pop(0)
        self._start_download(name)

    def _on_download_done(self, success: bool, message: str):
        self._logger.clear_progress()
        if success:
            self._controller.on_download_done(success, message)
            self._refresh_download_view()
            self._refresh_music_view()
        else:
            self._logger.log(message, "ERROR")
        if self._download_queue:
            self._process_download_queue()
        else:
            self.downloadButton.setEnabled(True)
            if success:
                QMessageBox.information(self, "ArkM", "下载完成！")

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
        name = item.text().replace("▶ ", "")
        self._play_queue.insert(0, name)
        self._play_next()

    def _play_next(self):
        if not self._play_queue:
            return
        name = self._play_queue.pop(0)
        self._player.play(name)
        self._load_album_image(name)
        self._highlight_playing(name)

    def _on_play_button(self):
        row = self.musicListWidget.currentRow()
        if row >= 0:
            name = self.musicListWidget.item(row).text().replace("▶ ", "")
            self._play_queue.insert(0, name)
            self._play_next()
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
            if self._play_queue:
                self._play_next()
            else:
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
                    self._fade_in_cover(pixmap)
                    return
            self.albumImage.clear()
            self.albumImage.setText("点击歌曲查看封面")
        except Exception as e:
            self._logger.log(f"封面加载失败: {e}", "ERROR")

    def _fade_in_cover(self, pixmap: QPixmap):
        """封面淡入动画 — 用 QVariantAnimation 驱动 QWidget 重绘 alpha"""
        scaled = pixmap.scaled(
            self.albumImage.width(), self.albumImage.height(),
            Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation,
        )
        self._cover_pixmap = scaled
        self._cover_target = pixmap.scaled(
            self.albumImage.width(), self.albumImage.height(),
            Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation,
        )
        self._cover_alpha = 0

        from PySide6.QtCore import QVariantAnimation, QEasingCurve
        self._cover_anim = QVariantAnimation()
        self._cover_anim.setDuration(400)
        self._cover_anim.setStartValue(0)
        self._cover_anim.setEndValue(255)
        self._cover_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._cover_anim.valueChanged.connect(self._on_cover_frame)
        self._cover_anim.start()

    def _on_cover_frame(self, alpha):
        self._cover_alpha = alpha
        pix = QPixmap(self._cover_target.size())
        pix.fill(Qt.GlobalColor.transparent)
        from PySide6.QtGui import QPainter
        p = QPainter(pix)
        p.setOpacity(alpha / 255.0)
        p.drawPixmap(0, 0, self._cover_target)
        p.end()
        self.albumImage.setPixmap(pix)

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
                item.setForeground(Qt.GlobalColor.darkCyan)
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
                    self._play_queue.insert(0, name)
                    self._play_next()
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

    def _enable_acrylic(self):
        """启用 Windows Acrylic/Mica 模糊背景"""
        try:
            import ctypes
            hwnd = int(self.winId())
            DWMWA_SYSTEMBACKDROP_TYPE = 38
            DWMSBT_MAINWINDOW = 2
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, DWMWA_SYSTEMBACKDROP_TYPE,
                ctypes.byref(ctypes.c_int(DWMSBT_MAINWINDOW)),
                ctypes.sizeof(ctypes.c_int),
            )
        except Exception:
            pass

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

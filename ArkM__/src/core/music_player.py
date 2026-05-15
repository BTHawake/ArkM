"""音乐播放控制模块"""
import os

from PySide6.QtCore import QObject, QTime, QUrl, QTimer
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput


class MusicPlayer(QObject):
    """封装所有播放逻辑：播放、暂停、停止、进度、音量"""

    def __init__(self, log_callback, parent=None):
        super().__init__(parent)
        self._log = log_callback

        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(0.5)

        self._current_music = None
        self._last_music = "114514"

        # 播放器信号连接
        self.player.positionChanged.connect(self._on_position_changed)
        self.player.durationChanged.connect(self._on_duration_changed)
        self.player.playbackStateChanged.connect(self._on_playback_state_changed)

        # 进度定时器
        self._progress_timer = QTimer()
        self._progress_timer.timeout.connect(self._update_progress)

    # ---- 公共接口 ----

    def play(self, music_name: str) -> bool:
        """播放指定音乐。返回 False 如果失败。"""
        try:
            if music_name == self._last_music and \
               self.player.playbackState() == QMediaPlayer.PlaybackState.PausedState:
                self.player.play()
                return True

            if self._current_music and self._current_music != music_name:
                self.stop()

            music_dir = "../songs/"
            if not os.path.exists(music_dir):
                self._log("音乐目录不存在", "ERROR")
                return False

            found_files = [
                f for f in os.listdir(music_dir)
                if music_name in f and f.endswith(('.mp3', '.wav', '.ogg', '.flac'))
            ]
            if not found_files:
                self._log(f"未找到歌曲文件: {music_name}", "WARNING")
                return False

            file_path = os.path.join(music_dir, found_files[0])
            self.player.setSource(QUrl.fromLocalFile(file_path))
            self._current_music = music_name
            self._last_music = music_name
            self.player.play()
            self._progress_timer.start(100)
            self._log(f"正在播放: {music_name}", "SUCCESS")
            return True

        except Exception as e:
            self._log(f"播放失败: {str(e)}", "ERROR")
            return False

    def resume(self):
        """从暂停状态恢复播放。"""
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PausedState:
            self.player.play()
            self._log("继续播放", "INFO")

    def pause(self):
        """暂停播放。"""
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
            self._log("暂停播放", "INFO")

    def stop(self):
        """停止播放并释放资源。"""
        if self.player.playbackState() != QMediaPlayer.PlaybackState.StoppedState:
            self.player.pause()
            self.player.setSource(QUrl())
            import PySide6.QtWidgets
            PySide6.QtWidgets.QApplication.processEvents()
            self.player.stop()
            self._current_music = None
            self._progress_timer.stop()
            self._log("停止播放并释放资源", "INFO")

    def set_position(self, position: int):
        """设置播放位置（毫秒）。"""
        self.player.setPosition(position)

    def set_volume(self, volume_pct: int):
        """设置音量（0-100）。"""
        self.audio_output.setVolume(volume_pct / 100.0)
        self._log(f"音量设置为: {volume_pct}%", "INFO")

    # ---- 查询 ----

    @property
    def current_music(self):
        return self._current_music

    @property
    def last_music(self):
        return self._last_music

    def playback_state(self):
        return self.player.playbackState()

    def position(self) -> int:
        return self.player.position()

    def duration(self) -> int:
        return self.player.duration()

    # ---- 内部回调 ----

    def _on_position_changed(self, position: int):
        """仅用于更新滑块（由 main_window 连接）"""
        pass  # 子类或外部通过信号覆盖

    def _on_duration_changed(self, duration: int):
        pass

    def _on_playback_state_changed(self, state):
        pass

    def _update_progress(self):
        """更新进度时间文字。"""
        pass

"""音乐业务逻辑控制器"""
from PySide6.QtCore import QObject, Signal

from .api_client import ArkMApiClient


class MusicController(QObject):
    """音乐下载/删除/查询的业务层，委托 API 调用给 ArkMApiClient"""

    download_finished = Signal(bool, str)
    download_progress = Signal(str, int, int)

    def __init__(self, log_callback, parent=None):
        super().__init__(parent)
        self._log = log_callback
        self._api = ArkMApiClient()
        self.download_items: list[str] = []
        self.music_items: list[str] = []

    # ---- 初始化 ----

    def init(self):
        try:
            self.refresh_download_list()
            self.refresh_music_list()
            self._log(
                f"系统就绪: 待下载 {len(self.download_items)} 首, 已下载 {len(self.music_items)} 首",
                "SUCCESS",
            )
        except Exception as e:
            self._log(f"数据初始化失败: {str(e)}", "ERROR")

    # ---- 列表 ----

    def refresh_download_list(self):
        self.download_items = self._api.get_undownloaded()

    def refresh_music_list(self):
        self.music_items = self._api.get_downloaded()

    def filter_download_items(self, keyword: str) -> list[str]:
        kw = keyword.strip().lower()
        return list(self.download_items) if not kw else [x for x in self.download_items if kw in x.lower()]

    def filter_music_items(self, keyword: str) -> list[str]:
        kw = keyword.strip().lower()
        return list(self.music_items) if not kw else [x for x in self.music_items if kw in x.lower()]

    # ---- 删除 ----

    def delete(self, music_name: str) -> tuple[bool, str]:
        data = self._api.delete(music_name)
        if data["success"]:
            self.refresh_music_list()
            self.refresh_download_list()
            self._log(data["message"], "SUCCESS")
        else:
            self._log(data["message"], "ERROR")
        return data["success"], data["message"]

    # ---- 下载后刷新 ----

    def on_download_done(self, success: bool, message: str):
        if success:
            self.refresh_download_list()
            self.refresh_music_list()
            self._log(message, "SUCCESS")
        else:
            self._log(message, "ERROR")

    # ---- 封面 ----

    def get_album_cover(self, music_name: str) -> dict | None:
        return self._api.get_album_cover(music_name)

    def get_all_albums(self) -> list[dict]:
        return self._api.get_all_albums()

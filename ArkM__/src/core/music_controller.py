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
        """初始化数据：刷新下载列表和已下载列表。"""
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
        """从后端拉取待下载歌曲列表。"""
        self.download_items = self._api.get_undownloaded()

    def refresh_music_list(self):
        """从后端拉取已下载歌曲列表。"""
        self.music_items = self._api.get_downloaded()

    def filter_download_items(self, keyword: str) -> list[str]:
        """根据关键字过滤待下载歌曲列表。"""
        kw = keyword.strip().lower()
        return list(self.download_items) if not kw else [x for x in self.download_items if kw in x.lower()]

    def filter_music_items(self, keyword: str) -> list[str]:
        """根据关键字过滤已下载歌曲列表。"""
        kw = keyword.strip().lower()
        return list(self.music_items) if not kw else [x for x in self.music_items if kw in x.lower()]

    # ---- 删除 ----

    def delete(self, music_name: str) -> tuple[bool, str]:
        """删除指定歌曲并刷新列表。"""
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
        """下载完成回调：刷新列表并记录日志。"""
        if success:
            self.refresh_download_list()
            self.refresh_music_list()
            self._log(message, "SUCCESS")
        else:
            self._log(message, "ERROR")

    # ---- 封面 ----

    def get_album_cover(self, music_name: str) -> dict | None:
        """委托 API 获取单曲专辑封面。"""
        return self._api.get_album_cover(music_name)

    def get_all_albums(self) -> list[dict]:
        """委托 API 获取全部专辑列表。"""
        return self._api.get_all_albums()

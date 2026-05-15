"""音乐业务逻辑控制器：通过 HTTP 调后端 API（下载/删除/查询/状态管理）"""
import requests
from PySide6.QtCore import QObject, Signal

BACKEND_URL = "http://localhost:8585"


class MusicController(QObject):
    """管理音乐下载/删除/查询的业务逻辑层"""

    download_finished = Signal(bool, str)
    download_progress = Signal(str, int, int)

    def __init__(self, log_callback, parent=None):
        super().__init__(parent)
        self._log = log_callback
        self.download_items = []
        self.music_items = []

    def init(self):
        """初始化：从后端加载列表。"""
        try:
            self.refresh_download_list()
            self.refresh_music_list()
            self._log(
                f"系统就绪: 待下载 {len(self.download_items)} 首, 已下载 {len(self.music_items)} 首",
                "SUCCESS",
            )
        except Exception as e:
            self._log(f"数据初始化失败: {str(e)}", "ERROR")

    def refresh_download_list(self):
        """从后端刷新待下载列表。"""
        resp = requests.get(f"{BACKEND_URL}/music/undownloaded", timeout=5)
        resp.raise_for_status()
        self.download_items = resp.json()["songs"]

    def refresh_music_list(self):
        """从后端刷新已下载列表。"""
        resp = requests.get(f"{BACKEND_URL}/music/downloaded", timeout=5)
        resp.raise_for_status()
        self.music_items = resp.json()["songs"]

    def filter_download_items(self, keyword: str) -> list[str]:
        kw = keyword.strip().lower()
        if not kw:
            return list(self.download_items)
        return [item for item in self.download_items if kw in item.lower()]

    def filter_music_items(self, keyword: str) -> list[str]:
        kw = keyword.strip().lower()
        if not kw:
            return list(self.music_items)
        return [item for item in self.music_items if kw in item.lower()]

    def delete(self, music_name: str) -> tuple[bool, str]:
        """删除已下载的音乐。返回 (成功, 消息)。"""
        resp = requests.post(
            f"{BACKEND_URL}/music/delete",
            json={"music_name": music_name},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        if data["success"]:
            self.refresh_music_list()
            self.refresh_download_list()
            self._log(data["message"], "SUCCESS")
        else:
            self._log(data["message"], "ERROR")
        return data["success"], data["message"]

    def on_download_done(self, success: bool, message: str):
        """下载完成后刷新数据。"""
        if success:
            self.refresh_download_list()
            self.refresh_music_list()
            self._log(message, "SUCCESS")
        else:
            self._log(message, "ERROR")

    def get_album_cover(self, music_name: str) -> dict | None:
        """获取歌曲对应的专辑封面信息。返回 {album_cid, cover_path} 或 None。"""
        try:
            resp = requests.get(f"{BACKEND_URL}/music/{music_name}/album", timeout=5)
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return None

    def get_all_albums(self) -> list[dict]:
        """获取所有专辑列表。返回 [{cid, name, cover_url, local_path}, ...]。"""
        try:
            resp = requests.get(f"{BACKEND_URL}/album/list", timeout=10)
            resp.raise_for_status()
            return resp.json()["albums"]
        except Exception:
            return []

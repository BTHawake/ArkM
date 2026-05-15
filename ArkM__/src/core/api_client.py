"""后端 API 客户端：封装所有 HTTP 调用"""
import requests

from config import BACKEND_URL


class ArkMApiClient:
    """后端 REST API 统一封装"""

    def __init__(self, base_url: str = BACKEND_URL):
        self.base_url = base_url

    # ---- 音乐列表 ----

    def get_undownloaded(self) -> list[str]:
        resp = requests.get(f"{self.base_url}/music/undownloaded", timeout=5)
        resp.raise_for_status()
        return resp.json()["songs"]

    def get_downloaded(self) -> list[str]:
        resp = requests.get(f"{self.base_url}/music/downloaded", timeout=5)
        resp.raise_for_status()
        return resp.json()["songs"]

    # ---- 下载（返回原始 response 给调用方读 SSE） ----

    def download(self, music_name: str) -> requests.Response:
        resp = requests.post(
            f"{self.base_url}/music/download",
            json={"music_name": music_name},
            stream=True,
            timeout=(10, 300),
        )
        resp.raise_for_status()
        return resp

    # ---- 删除 ----

    def delete(self, music_name: str) -> dict:
        resp = requests.post(
            f"{self.base_url}/music/delete",
            json={"music_name": music_name},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    # ---- 专辑 ----

    def get_album_cover(self, music_name: str) -> dict | None:
        resp = requests.get(f"{self.base_url}/music/{music_name}/album", timeout=5)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()

    def get_all_albums(self) -> list[dict]:
        resp = requests.get(f"{self.base_url}/album/list", timeout=10)
        resp.raise_for_status()
        return resp.json()["albums"]

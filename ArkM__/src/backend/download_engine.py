"""明日方舟音乐下载引擎"""
import os
import json
import random
import logging
from time import sleep
from typing import Any, Callable, Optional

from requests import get

from config import (
    API_SONGS,
    DOWNLOADED_FILE,
    UNDOWNLOADED_FILE,
    SUFFIX_MAPPING_FILE,
    MUSIC_PATH,
    ALBUM_PATH,
)
from core.result import (
    Result, Ok, Err,
    is_ok, is_err,
    noexcept_get, get_response_json,
    format_size,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

ProgressCallback = Optional[Callable[[str, int, int], None]]


def format_size(size_bytes):
    """格式化文件大小"""
# ---- 下载引擎 ----

class DownloadEngine:
    """音乐下载引擎（实例化，状态自包含）"""

    def __init__(self):
        self.cid2name: dict[str, str] = {}
        self.name2cid: dict[str, str] = {}
        self.cid2album: dict[str, str] = {}
        self.cid2suffix: dict[str, str] = {}
        self.downloaded: dict[str, bool] = {}
        self.undownloaded: dict[str, bool] = {}
        self.all_song_info: Any = None

    # ---- 初始化 ----

    def init(self):
        """初始化引擎"""
        logger.info("下载引擎初始化中...")
        directories = [MUSIC_PATH, os.path.dirname(DOWNLOADED_FILE), ALBUM_PATH]
        for d in directories:
            os.makedirs(d, exist_ok=True)

        self._load_suffix_mapping()
        self._init_all_song_info()
        self._init_download()
        logger.info(f"下载引擎初始化完成，共 {len(self.cid2name)} 首歌曲")

    def _init_all_song_info(self):
        response = noexcept_get(url=API_SONGS)
        if is_err(response):
            raise RuntimeError("获取歌曲信息失败")
        self.all_song_info = get_response_json(response.value)
        if is_err(self.all_song_info):
            raise RuntimeError("解析歌曲信息失败")
        self.all_song_info = self.all_song_info.value

    def _init_download(self):
        for item in self.all_song_info["data"]["list"]:
            cid = item["cid"]
            name = item["name"]
            album_cid = item.get("albumCid", "")
            self.cid2name[cid] = name
            self.name2cid[name] = cid
            self.cid2album[cid] = album_cid

        self.downloaded = self._load_json(DOWNLOADED_FILE, {})
        if not self.downloaded:
            self.downloaded = {item["cid"]: False for item in self.all_song_info["data"]["list"]}
            self._save_json(DOWNLOADED_FILE, self.downloaded)

        self.undownloaded = {
            cid: True
            for cid in self.cid2name
            if not self.downloaded.get(cid, False)
        }
        self._save_json(UNDOWNLOADED_FILE, self.undownloaded)

    def _load_suffix_mapping(self):
        self.cid2suffix = self._load_json(SUFFIX_MAPPING_FILE, {})
        logger.info(f"已加载后缀映射，共 {len(self.cid2suffix)} 条记录")

    # ---- 下载 ----

    def download_music(self, music_name: str, progress_callback: ProgressCallback = None) -> bool:
        """下载单首音乐（接受歌名或CID）"""
        cid = self.name2cid.get(music_name, music_name)
        song_url = f"https://monster-siren.hypergryph.com/api/song/{cid}"

        response = noexcept_get(url=song_url)
        if is_err(response):
            logger.error(f"获取歌曲信息失败: {response.error}")
            return False

        song_json = get_response_json(response.unwrap())
        if is_err(song_json):
            logger.error(f"解析歌曲信息失败")
            return False

        result = self._download_file(song_json.unwrap(), progress_callback)
        if is_ok(result):
            self.downloaded[cid] = True
            self.undownloaded.pop(cid, None)
            self._save_downloaded()
            self._save_suffix_mapping()
            return True
        return False

    def _download_file(self, song_json: dict, progress_callback: ProgressCallback = None) -> Result:
        try:
            url = song_json["data"]["sourceUrl"]
            cid = song_json["data"]["cid"]
            suffix = url.split(".")[-1]
            self.cid2suffix[cid] = suffix
            filename = song_json["data"]["name"]

            response = noexcept_get(url, stream=True, timeout=(10, 10))
            if is_err(response):
                return response

            response = response.unwrap()
            sleep(random.uniform(0.5, 2))

            total_size = int(response.headers.get("content-length", 0))
            downloaded_size = 0

            os.makedirs(MUSIC_PATH, exist_ok=True)
            filepath = os.path.join(MUSIC_PATH, f"{filename}.{suffix}")

            with open(filepath, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        if progress_callback:
                            progress_callback(filename, downloaded_size, total_size)

            sleep(random.uniform(0.5, 2))
            return Ok(filepath)

        except Exception as e:
            logger.error(f"下载失败: {e}")
            return Err(e)

    # ---- 删除 ----

    def delete_music(self, music_name: str) -> tuple[bool, str]:
        """删除已下载的音乐"""
        if music_name not in self.name2cid:
            return False, "歌曲不存在"

        cid = self.name2cid[music_name]
        if not self.downloaded.get(cid, False):
            return False, "歌曲未下载"

        suffix = self.cid2suffix.get(cid, "wav")
        filename = f"{music_name}.{suffix}"
        filepath = os.path.join(MUSIC_PATH, filename)

        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                logger.info(f"成功删除文件: {filepath}")

            self.downloaded[cid] = False
            self.undownloaded[cid] = True
            self._save_downloaded()

            return True, f"成功删除 {filename}"
        except Exception as e:
            logger.error(f"删除文件失败: {e}")
            return False, f"删除文件失败: {e}"

    # ---- 查询 ----

    def get_downloaded_music(self) -> list[str]:
        return [
            self.cid2name[cid]
            for cid, is_dl in self.downloaded.items()
            if is_dl and cid in self.cid2name
        ]

    def get_undownloaded_music(self) -> list[str]:
        return [
            self.cid2name[cid]
            for cid, need_dl in self.undownloaded.items()
            if need_dl and cid in self.cid2name
        ]

    # ---- 持久化 ----

    def save_downloaded(self):
        self._save_downloaded()

    def save_suffix_mapping(self):
        self._save_suffix_mapping()

    def _save_downloaded(self):
        self._save_json(DOWNLOADED_FILE, self.downloaded)
        self._save_json(UNDOWNLOADED_FILE, self.undownloaded)
        logger.info("已保存下载记录")

    def _save_suffix_mapping(self):
        self._save_json(SUFFIX_MAPPING_FILE, self.cid2suffix)
        logger.info("已保存后缀映射")

    @staticmethod
    def _load_json(filepath: str, default: Any) -> Any:
        try:
            if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                with open(filepath, "r", encoding="utf-8") as f:
                    return json.load(f)
            return default
        except Exception as e:
            logger.warning(f"加载文件 {filepath} 失败: {e}")
            return default

    @staticmethod
    def _save_json(filepath: str, data: Any):
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logger.error(f"保存文件 {filepath} 失败: {e}")
            raise



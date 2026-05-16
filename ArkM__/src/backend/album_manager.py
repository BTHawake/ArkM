"""专辑封面管理器：下载并缓存专辑封面到本地（懒加载）"""
import os
import json
import logging

from config import API_ALBUMS, ALBUM_PATH, ALBUM_COVERS_FILE

logger = logging.getLogger(__name__)


class AlbumCoverManager:
    """管理专辑封面元数据和缓存。"""

    def __init__(self, engine):
        self._engine = engine
        self._album_list: list[dict] = []
        self._album_map: dict[str, dict] = {}

    # ---- 初始化 ----

    def init_metadata(self):
        """拉取专辑元数据，不下载图片。"""
        from core.result import noexcept_get
        logger.info("初始化专辑封面元数据...")
        try:
            resp = noexcept_get(API_ALBUMS, timeout=30)
            from core.result import is_ok
            if not is_ok(resp):
                logger.error(f"获取专辑列表失败: {resp.error}")
                return
            albums = resp.unwrap().json().get("data", [])
        except Exception as e:
            logger.error(f"获取专辑列表失败: {e}")
            return

        covers = self._load_covers()

        self._album_list = []
        self._album_map = {}

        for album in albums:
            cid = album["cid"]
            info = {
                "cid": cid,
                "name": album["name"],
                "cover_url": album.get("coverUrl", ""),
                "local_path": covers.get(cid, {}).get("local_path", ""),
            }
            self._album_list.append(info)
            self._album_map[cid] = info

        logger.info(f"专辑元数据加载完成，共 {len(self._album_list)} 张专辑")

    # ---- 查询 ----

    def get_all_albums(self) -> list[dict]:
        return self._album_list

    def get_cover(self, music_name: str) -> dict | None:
        """根据歌名获取封面信息。未缓存时即时下载。"""
        song_cid = self._engine.name2cid.get(music_name)
        if not song_cid:
            return None

        album_cid = self._engine.cid2album.get(song_cid)
        if not album_cid:
            return None

        album_info = self._album_map.get(album_cid)
        if not album_info:
            return {"album_cid": album_cid, "cover_path": ""}

        local_path = album_info.get("local_path", "")
        cover_url = album_info.get("cover_url", "")

        # 已有本地文件
        if local_path and os.path.exists(local_path):
            return {"album_cid": album_cid, "cover_path": local_path}

        # 按命名规则查找
        for ext in ('jpg', 'png', 'webp'):
            path = os.path.join(ALBUM_PATH, f"{album_cid}.{ext}")
            if os.path.exists(path):
                album_info["local_path"] = path
                self._save_covers()
                return {"album_cid": album_cid, "cover_path": path}

        # 需要下载
        if cover_url:
            downloaded = self._download_cover(album_cid, cover_url)
            if downloaded:
                album_info["local_path"] = downloaded
                self._save_covers()
                return {"album_cid": album_cid, "cover_path": downloaded}

        return {"album_cid": album_cid, "cover_path": ""}

    # ---- 下载 ----

    def _download_cover(self, album_cid: str, cover_url: str) -> str:
        """下载一张封面到本地。统一使用 noexcept_get。"""
        ext = cover_url.split('.')[-1].split('?')[0]
        if ext not in ('jpg', 'png', 'webp'):
            ext = 'jpg'
        save_path = os.path.join(ALBUM_PATH, f"{album_cid}.{ext}")

        if os.path.exists(save_path):
            return save_path

        from core.result import noexcept_get, is_ok, is_err
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        resp = noexcept_get(cover_url, timeout=30)
        if is_err(resp):
            logger.warning(f"下载封面失败 {album_cid}: {resp.error}")
            return ""
        try:
            with open(save_path, 'wb') as f:
                f.write(resp.unwrap().content)
            logger.info(f"封面已缓存: {album_cid}")
            return save_path
        except Exception as e:
            logger.warning(f"写入封面失败 {album_cid}: {e}")
            return ""

    # ---- 持久化 ----

    def _load_covers(self) -> dict:
        try:
            if os.path.exists(ALBUM_COVERS_FILE) and os.path.getsize(ALBUM_COVERS_FILE) > 0:
                with open(ALBUM_COVERS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"加载专辑封面缓存失败: {e}")
        return {}

    def _save_covers(self):
        os.makedirs(os.path.dirname(ALBUM_COVERS_FILE), exist_ok=True)
        with open(ALBUM_COVERS_FILE, 'w', encoding='utf-8') as f:
            json.dump({cid: {"name": i["name"], "cover_url": i["cover_url"], "local_path": i["local_path"]}
                       for cid, i in self._album_map.items()}, f, ensure_ascii=False, indent=4)

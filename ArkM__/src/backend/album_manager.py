"""专辑封面管理器：下载并缓存专辑封面到本地（懒加载）"""
import os
import json
import logging

from requests import get

from config import API_ALBUMS, ALBUM_PATH, ALBUM_COVERS_FILE

logger = logging.getLogger(__name__)

# 内存缓存：专辑列表（启动时初始化一次）
_album_list: list[dict] = []
_album_map: dict[str, dict] = {}  # album_cid -> {name, cover_url, local_path}


def _load_album_covers() -> dict:
    """加载已缓存的封面记录。"""
    try:
        if os.path.exists(ALBUM_COVERS_FILE) and os.path.getsize(ALBUM_COVERS_FILE) > 0:
            with open(ALBUM_COVERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"加载专辑封面缓存失败: {e}")
    return {}


def _save_album_covers(data: dict):
    """保存封面记录到文件。"""
    os.makedirs(os.path.dirname(ALBUM_COVERS_FILE), exist_ok=True)
    with open(ALBUM_COVERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def _download_single_cover(album_cid: str, cover_url: str) -> str:
    """下载一张封面到本地。返回本地路径或空字符串。"""
    try:
        ext = cover_url.split('.')[-1].split('?')[0]
        if ext not in ('jpg', 'png', 'webp'):
            ext = 'jpg'
        save_path = os.path.join(ALBUM_PATH, f"{album_cid}.{ext}")

        # 已存在则跳过
        if os.path.exists(save_path):
            return save_path

        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        resp = get(cover_url, timeout=30)
        resp.raise_for_status()
        with open(save_path, 'wb') as f:
            f.write(resp.content)
        logger.info(f"封面已缓存: {album_cid}")
        return save_path
    except Exception as e:
        logger.warning(f"下载封面失败 {album_cid}: {e}")
        return ""


def init_album_covers():
    """启动时初始化：只拉取元数据，不下载图片。"""
    global _album_list, _album_map
    logger.info("初始化专辑封面元数据...")

    try:
        resp = get(API_ALBUMS, timeout=30)
        resp.raise_for_status()
        albums = resp.json().get("data", [])
    except Exception as e:
        logger.error(f"获取专辑列表失败: {e}")
        return

    covers = _load_album_covers()

    _album_list = []
    _album_map = {}

    for album in albums:
        cid = album["cid"]
        name = album["name"]
        cover_url = album.get("coverUrl", "")

        # 查缓存
        cached = covers.get(cid, {}).get("local_path", "")

        info = {"cid": cid, "name": name, "cover_url": cover_url, "local_path": cached}
        _album_list.append(info)
        _album_map[cid] = info

    logger.info(f"专辑元数据加载完成，共 {len(_album_list)} 张专辑")


def get_all_albums() -> list[dict]:
    """返回所有专辑列表（只含元数据，不保证封面已下载）。"""
    return _album_list


def get_album_cover(music_name: str) -> dict | None:
    """根据歌名获取封面，未缓存时即时下载。"""
    from .download_engine import name2cid
    from .download_engine import cid2album as _cid2album

    song_cid = name2cid.get(music_name)
    if not song_cid:
        return None

    album_cid = _cid2album.get(song_cid)
    if not album_cid:
        return None

    album_info = _album_map.get(album_cid)
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
            _save_album_covers({cid: info for cid, info in _album_map.items()})
            return {"album_cid": album_cid, "cover_path": path}

    # 需要下载
    if cover_url:
        local_path = _download_single_cover(album_cid, cover_url)
        if local_path:
            album_info["local_path"] = local_path
            _save_album_covers({cid: info for cid, info in _album_map.items()})
            return {"album_cid": album_cid, "cover_path": local_path}

    return {"album_cid": album_cid, "cover_path": ""}

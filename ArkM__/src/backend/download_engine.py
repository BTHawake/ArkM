import os
from dataclasses import dataclass
from time import sleep
from typing import Any, TypeAlias, TypeGuard, Callable, Optional
from abc import ABC
import random
import json
from requests import Response, get, RequestException
import logging
'''
以后这里更新图片下载然后合成到音乐里

'''

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# 下载引擎内置日志
logger = logging.getLogger(__name__)

API_SONGS = "https://monster-siren.hypergryph.com/api/songs"
API_ALBUMS = "https://monster-siren.hypergryph.com/api/albums"

DOWNLOADED_FILE = "../Persistence/downloaded.json"
UNDOWNLOADED_FILE = "../Persistence/undownloaded.json"
SUFFIX_MAPPING_FILE = "../Persistence/suffix_mapping.json"

MUSIC_PATH = "../songs/"
ALBUM_PATH = "../albums/"

cid2name = {}
name2cid = {}
cid2album = {}  # song_cid -> album_cid
cid2suffix = {}

# 进度回调函数类型
ProgressCallback = Optional[Callable[[str, int, int], None]]


# 清理函数改由 FastAPI shutdown 事件调用

# IKUN_111友情赞助
class _Result(ABC):
    def unwrap_or(self, default: Any) -> Any: ...

    def unwrap(self) -> Any: ...


@dataclass
class Ok(_Result):
    value: Any

    def unwrap_or(self, default: Any) -> Any:
        return self.value

    def unwrap(self) -> Any:
        return self.value


@dataclass
class Err(_Result):
    error: Any

    def unwrap_or(self, default: Any) -> Any:
        return default

    def unwrap(self) -> None:
        raise self.error


Result: TypeAlias = Ok | Err


def is_ok(result: Result) -> TypeGuard[Ok]:
    return isinstance(result, Ok)


def is_err(result: Result) -> TypeGuard[Err]:
    return isinstance(result, Err)


def noexcept_get(*args, **kwargs) -> Result:
    """安全的GET请求，包含重试机制"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = get(*args, **kwargs)
            response.raise_for_status()
            return Ok(response)
        except RequestException as e:
            if attempt == max_retries - 1:
                return Err(e)
            logger.warning(f"请求失败，第{attempt + 1}次重试: {e}")
            sleep(2 ** attempt)  # 指数退避
    return Err(Exception("所有重试都失败了"))


def get_response_json(response: Response) -> Result:
    try:
        return Ok(response.json())
    except Exception as e:
        return Err(e)


class Info:
    all_song_info: Any = None
    cid_list: Any = None
    downloaded = {}
    undownloaded = {}


    @classmethod
    def init_all_song_info(cls):
        """初始化所有歌曲信息"""
        response = noexcept_get(url=API_SONGS)
        if is_err(response):
            logger.error('获取歌曲信息失败')
            raise RuntimeError('获取歌曲信息失败')
        response = response.value
        cls.all_song_info = get_response_json(response)
        if is_err(cls.all_song_info):
            logger.error('解析歌曲信息失败')
            raise RuntimeError('解析歌曲信息失败')
        cls.all_song_info = cls.all_song_info.value

    @classmethod
    def init_download(cls):
        """初始化已下载歌曲记录"""
        # 获取cid、name、albumCid的映射
        for item in cls.all_song_info["data"]["list"]:
            cid = item['cid']
            name = item['name']
            album_cid = item.get('albumCid', '')
            cid2name[cid] = name
            name2cid[name] = cid
            cid2album[cid] = album_cid

        # 读取已下载歌曲记录
        cls.downloaded = cls._load_json_file(DOWNLOADED_FILE, {})

        # 如果下载记录为空，初始化所有歌曲为未下载状态
        if not cls.downloaded:
            cls.downloaded = {item["cid"]: False for item in cls.all_song_info["data"]["list"]}
            cls._save_json_file(DOWNLOADED_FILE, cls.downloaded)

        # 初始化未下载列表
        cls.undownloaded = {
            item["cid"]: True
            for item in cls.all_song_info["data"]["list"]
            if not cls.downloaded.get(item["cid"], False)
        }

        cls._save_json_file(UNDOWNLOADED_FILE, cls.undownloaded)

    @classmethod
    def init_cid_list(cls):
        """初始化cid_list"""
        songs_list = cls.all_song_info['data']['list']
        cls.cid_list = [li['cid'] for li in songs_list]
        logger.info(f"获取CID成功，共 {len(cls.cid_list)} 首歌曲")

    @staticmethod
    def _load_json_file(filepath: str, default: Any) -> Any:
        """加载JSON文件，如果文件不存在或为空则返回默认值"""
        try:
            if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                with open(filepath, 'r', encoding='utf-8') as file:
                    return json.load(file)
            return default
        except Exception as e:
            logger.warning(f"加载文件 {filepath} 失败: {e}")
            return default

    @staticmethod
    def _save_json_file(filepath: str, data: Any):
        """保存数据到JSON文件"""
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
        except Exception as e:
            logger.error(f"保存文件 {filepath} 失败: {e}")
            raise


def format_size(size_bytes):
    """格式化文件大小"""
    if size_bytes == 0:
        return "0B"
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.2f} {size_names[i]}"


def download(song_json, progress_callback: ProgressCallback = None) -> Result:
    """下载歌曲文件"""
    try:
        url = song_json['data']['sourceUrl']
        cid = song_json['data']['cid']
        suffix = url.split('.')[-1]
        cid2suffix[cid] = suffix
        filename = song_json['data']['name']

        response = noexcept_get(url, stream=True, timeout=(10, 10))
        if is_err(response):
            return response

        response = response.unwrap()
        sleep(random.uniform(0.5, 2))

        total_size = int(response.headers.get('content-length', 0))
        downloaded_size = 0

        os.makedirs(MUSIC_PATH, exist_ok=True)

        filepath = os.path.join(MUSIC_PATH, f"{filename}.{suffix}")
        with open(filepath, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)
                    downloaded_size += len(chunk)

                    # 返回已下载的文件大小，前面emit()检测数据变化，然后更新
                    if progress_callback:
                        progress_callback(filename, downloaded_size, total_size)

        sleep(random.uniform(0.5, 2))

        return Ok(filepath)

    except Exception as e:
        logger.error(f"下载失败: {e}")
        return Err(e)


def get_music(cids, progress_callback: ProgressCallback = None):
    """获取并下载音乐"""
    success_count = 0
    fail_count = 0

    for i, cid in enumerate(cids, start=1):
        if Info.downloaded.get(cid, False):
            logger.info(f"检测到歌曲 {cid2name[cid]} 已下载，已跳过")
            continue

        song_url = f'https://monster-siren.hypergryph.com/api/song/{cid}'
        response = noexcept_get(url=song_url)
        if is_err(response):
            logger.error(f'{cid2name[cid]} 获取信息失败: {response.error}')
            fail_count += 1
            continue

        song_json = get_response_json(response.unwrap())
        if is_err(song_json):
            logger.error(f'{cid2name[cid]} 解析信息失败')
            fail_count += 1
            continue

        # 创建包装的进度回调
        def create_wrapped_callback(original_callback, song_name):
            if not original_callback:
                return None

            def wrapped_callback(filename, downloaded, total):
                original_callback(song_name, downloaded, total)

            return wrapped_callback

        wrapped_callback = create_wrapped_callback(progress_callback, cid2name[cid])

        result = download(song_json.unwrap(), wrapped_callback)
        if is_ok(result):
            path = result.unwrap()
            Info.downloaded[cid] = True
            if cid in Info.undownloaded:
                del Info.undownloaded[cid]
            success_count += 1
            logger.info(f"文件保存在 {path}，进度为 {i}/{len(cids)}")
        else:
            logger.error(f'{cid2name[cid]} 下载失败: {result.error}')
            fail_count += 1

    return success_count, fail_count


def save_downloaded():
    """保存已下载歌曲记录"""
    try:
        Info._save_json_file(DOWNLOADED_FILE, Info.downloaded)
        Info._save_json_file(UNDOWNLOADED_FILE, Info.undownloaded)
        logger.info(f"已下载文件已保存")
    except Exception as e:
        logger.error(f"保存已下载歌曲失败: {e}")


def save_suffix_mapping():
    """保存后缀映射"""
    try:
        Info._save_json_file(SUFFIX_MAPPING_FILE, cid2suffix)
        logger.info(f"后缀映射已保存")
    except Exception as e:
        logger.error(f"保存后缀映射失败: {e}")


def load_suffix_mapping():
    """加载后缀映射"""
    global cid2suffix
    cid2suffix = Info._load_json_file(SUFFIX_MAPPING_FILE, {})
    logger.info(f"已加载后缀映射，共 {len(cid2suffix)} 条记录")


def download_engine_init():
    """主函数"""
    logger.info("加载中...")

    # 必需开辟的目录
    directories = [ "../songs/", "../Persistence/"]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

    load_suffix_mapping()

    Info.init_all_song_info()
    Info.init_download()
    Info.init_cid_list()
    logger.info("下载引擎初始化完成")


def download_music(music_name, progress_callback: ProgressCallback = None):
    """下载单首音乐（接受歌名或CID）"""
    # 如果是歌名则转为CID
    cid = name2cid.get(music_name, music_name)
    success_count, fail_count = get_music([cid], progress_callback)
    save_downloaded()
    save_suffix_mapping()
    return success_count > 0


def get_downloaded_music():
    """获取已下载的音乐"""
    return [cid2name[cid] for cid, is_downloaded in Info.downloaded.items()
            if is_downloaded and cid in cid2name]


def get_undownloaded_music():
    """获取未下载的音乐"""
    return [cid2name[cid] for cid, need_download in Info.undownloaded.items()
            if need_download and cid in cid2name]


def delete_music(music_name):
    """删除已下载的音乐"""
    if music_name not in name2cid:
        return False, "歌曲不存在"

    cid = name2cid[music_name]
    if not Info.downloaded.get(cid, False):
        return False, "歌曲未下载"

    # 查找并删除文件
    suffix = cid2suffix.get(cid, "wav")
    filename = f"{music_name}.{suffix}"
    filepath = os.path.join(MUSIC_PATH, filename)

    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.info(f"成功删除文件: {filepath}")

        Info.downloaded[cid] = False
        Info.undownloaded[cid] = True
        save_downloaded()

        return True, f"成功删除 {filename}"

    except Exception as e:
        logger.error(f"删除文件失败: {e}")
        return False, f"删除文件失败: {e}"
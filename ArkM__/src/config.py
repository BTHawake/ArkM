"""全局配置常量"""
import os
import sys

# 数据目录：开发模式用相对路径，打包后用 exe 所在目录
if getattr(sys, 'frozen', False):
    _base = os.path.dirname(sys.executable)
    MUSIC_PATH = os.path.join(_base, 'songs') + os.sep
    ALBUM_PATH = os.path.join(_base, 'albums') + os.sep
    PERSISTENCE_PATH = os.path.join(_base, 'Persistence') + os.sep
else:
    MUSIC_PATH = "../songs/"
    ALBUM_PATH = "../albums/"
    PERSISTENCE_PATH = "../Persistence/"

NAME_PATH = "../name/"

# 明日方舟 API
API_SONGS = "https://monster-siren.hypergryph.com/api/songs"
API_ALBUMS = "https://monster-siren.hypergryph.com/api/albums"

# 持久化文件
DOWNLOADED_FILE = os.path.join(PERSISTENCE_PATH, 'downloaded.json')
UNDOWNLOADED_FILE = os.path.join(PERSISTENCE_PATH, 'undownloaded.json')
SUFFIX_MAPPING_FILE = os.path.join(PERSISTENCE_PATH, 'suffix_mapping.json')
ALBUM_COVERS_FILE = os.path.join(PERSISTENCE_PATH, 'album_covers.json')

# 后端服务
BACKEND_HOST = "localhost"
BACKEND_PORT = 8585
BACKEND_URL = f"http://{BACKEND_HOST}:{BACKEND_PORT}"

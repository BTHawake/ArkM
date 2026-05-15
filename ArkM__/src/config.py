"""全局配置常量"""

# 明日方舟 API
API_SONGS = "https://monster-siren.hypergryph.com/api/songs"
API_ALBUMS = "https://monster-siren.hypergryph.com/api/albums"

# 本地路径
MUSIC_PATH = "../songs/"
ALBUM_PATH = "../albums/"
PERSISTENCE_PATH = "../Persistence/"
NAME_PATH = "../name/"

# 持久化文件
DOWNLOADED_FILE = f"{PERSISTENCE_PATH}downloaded.json"
UNDOWNLOADED_FILE = f"{PERSISTENCE_PATH}undownloaded.json"
SUFFIX_MAPPING_FILE = f"{PERSISTENCE_PATH}suffix_mapping.json"
ALBUM_COVERS_FILE = f"{PERSISTENCE_PATH}album_covers.json"

# 后端服务
BACKEND_HOST = "localhost"
BACKEND_PORT = 8585
BACKEND_URL = f"http://{BACKEND_HOST}:{BACKEND_PORT}"

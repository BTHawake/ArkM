"""FastAPI 后端服务：包装 download_engine 为 REST API"""
import json
import os
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel

from .download_engine import (
    download_engine_init,
    download_music,
    delete_music,
    get_downloaded_music,
    get_undownloaded_music,
    save_downloaded,
    save_suffix_mapping,
    logger,
)
from .album_manager import init_album_covers, get_all_albums, get_album_cover


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时初始化，关闭时保存"""
    logger.info("后端服务启动中...")
    download_engine_init()
    init_album_covers()
    logger.info("后端服务已就绪")
    yield
    logger.info("后端服务关闭中，保存数据...")
    save_downloaded()
    save_suffix_mapping()
    logger.info("数据已保存")


app = FastAPI(title="ArkM Backend", lifespan=lifespan)


# ---- 模型 ----

class DownloadRequest(BaseModel):
    music_name: str


class DeleteRequest(BaseModel):
    music_name: str


class MessageResponse(BaseModel):
    success: bool
    message: str


# ---- 端点 ----

@app.get("/music/undownloaded")
async def undownloaded_list():
    """获取待下载歌曲列表"""
    songs = get_undownloaded_music()
    return {"songs": songs, "count": len(songs)}


@app.get("/music/downloaded")
async def downloaded_list():
    """获取已下载歌曲列表"""
    songs = get_downloaded_music()
    return {"songs": songs, "count": len(songs)}


@app.post("/music/download")
async def download(req: DownloadRequest):
    """下载一首歌，SSE 流式返回进度"""
    music_name = req.music_name

    async def event_stream():
        loop = asyncio.get_event_loop()

        progress_queue = asyncio.Queue()

        def progress_callback(filename, downloaded, total):
            data = json.dumps({
                "type": "progress",
                "filename": filename,
                "downloaded": downloaded,
                "total": total,
            })
            loop.call_soon_threadsafe(progress_queue.put_nowait, data)

        # 在后台线程执行下载（不阻塞事件循环）
        result = await loop.run_in_executor(None, download_music, music_name, progress_callback)

        # 排空进度队列
        while not progress_queue.empty():
            data = await progress_queue.get()
            yield f"data: {data}\n\n"

        # 发送最终结果
        final = json.dumps({
            "type": "result",
            "success": result,
            "message": f"下载{'成功' if result else '失败'}: {music_name}",
        })
        yield f"data: {final}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/music/delete")
async def delete(req: DeleteRequest):
    """删除一首歌"""
    success, message = delete_music(req.music_name)
    return {"success": success, "message": message}


# ---- 音乐流媒体端点 ----

@app.get("/stream/{music_name}")
async def stream_music(music_name: str):
    """根据歌名流式返回音频文件"""
    from .download_engine import MUSIC_PATH, name2cid, cid2suffix

    music_dir = MUSIC_PATH
    if not os.path.exists(music_dir):
        raise HTTPException(status_code=404, detail="音乐目录不存在")

    # 按文件名前缀匹配
    found = None
    for f in sorted(os.listdir(music_dir)):
        if music_name in f and f.endswith(('.mp3', '.wav', '.ogg', '.flac')):
            found = f
            break
    if not found:
        raise HTTPException(status_code=404, detail=f"未找到歌曲: {music_name}")

    path = os.path.join(music_dir, found)
    ext = found.rsplit('.', 1)[-1]
    mime_map = {"mp3": "audio/mpeg", "wav": "audio/wav", "ogg": "audio/ogg", "flac": "audio/flac"}
    media_type = mime_map.get(ext, "audio/mpeg")
    return FileResponse(path, media_type=media_type)


# ---- 专辑封面端点 ----

@app.get("/album/list")
async def album_list():
    """获取所有专辑列表"""
    albums = get_all_albums()
    return {"albums": albums, "count": len(albums)}


@app.get("/album/{album_cid}/cover")
async def album_cover(album_cid: str):
    """返回封面图片文件"""
    from .album_manager import ALBUM_PATH

    for ext in ('jpg', 'png', 'webp'):
        path = os.path.join(ALBUM_PATH, f"{album_cid}.{ext}")
        if os.path.exists(path):
            return FileResponse(path, media_type=f"image/{ext}")

    raise HTTPException(status_code=404, detail="封面未找到")


@app.get("/music/{music_name}/album")
async def music_album(music_name: str):
    """根据歌名返回专辑封面信息"""
    result = get_album_cover(music_name)
    if result is None:
        raise HTTPException(status_code=404, detail="歌曲或专辑不存在")
    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8585)

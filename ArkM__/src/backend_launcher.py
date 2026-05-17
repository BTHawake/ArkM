"""PyInstaller onedir 入口：启动 uvicorn 后端"""
import sys, os

if getattr(sys, 'frozen', False):
    sys.path.insert(0, os.path.dirname(sys.executable))

import uvicorn

if __name__ == "__main__":
    from backend.server import app
    port = 8586 if getattr(sys, 'frozen', False) else 8585
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")

"""后端进程管理：启动、健康检查、停止。"""
import subprocess
import time
import sys
import os

import requests

from config import BACKEND_HOST, BACKEND_PORT

BACKEND_SCRIPT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "src")


class BackendProcess:
    """管理 FastAPI 后端子进程的完整生命周期。"""

    def __init__(self, host: str = BACKEND_HOST, port: int = BACKEND_PORT):
        self.host = host
        self.port = port
        self._proc = None

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"

    def start(self):
        """启动后端子进程。"""
        self._proc = subprocess.Popen(
            [
                sys.executable, "-m", "uvicorn", "backend.server:app",
                "--host", self.host, "--port", str(self.port),
            ],
            cwd=BACKEND_SCRIPT_DIR,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def stop(self):
        """停止后端子进程。"""
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._proc.kill()
            self._proc = None

    def wait_ready(self, timeout: int = 20) -> bool:
        """等待后端就绪。返回 True 如果成功。"""
        for _ in range(timeout * 2):
            try:
                r = requests.get(f"{self.url}/music/downloaded", timeout=2)
                if r.status_code == 200:
                    return True
            except requests.ConnectionError:
                pass
            time.sleep(0.5)
        return False

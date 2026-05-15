"""ArkM 音乐系统入口"""
import os
import sys
import time
import signal
import subprocess
import atexit

from PySide6.QtWidgets import QApplication, QMessageBox

from ui.start_window import StartMusic
from ui.main_window import MainWindow


BACKEND_SCRIPT = os.path.join(os.path.dirname(__file__), "backend", "server.py")


def _start_backend():
    """启动后端子进程。"""
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.server:app", "--host", "localhost", "--port", "8585"],
        cwd=os.path.dirname(__file__),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return proc


_backend_proc = None


def _kill_backend():
    global _backend_proc
    if _backend_proc and _backend_proc.poll() is None:
        _backend_proc.terminate()
        try:
            _backend_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _backend_proc.kill()


atexit.register(_kill_backend)


class ApplicationController:
    """应用程序控制器：管理窗口切换路由"""

    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setStyle('Fusion')
        self._current_window = None
        self._dr_name = ""

    def start(self) -> int:
        """启动应用。返回 exit code。"""
        # 读取已保存的用户名
        os.makedirs('../name/', exist_ok=True)
        filename = "../name/name.txt"
        if not os.path.exists(filename):
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("")

        with open(filename, 'r', encoding='utf-8') as f:
            self._dr_name = f.read().strip()

        if not self._dr_name:
            self._open_start()
        else:
            self._open_main()

        return self.app.exec()

    def _open_start(self):
        self._close_current()
        self._current_window = StartMusic(self._on_start_complete)
        self._current_window.show()

    def _open_main(self):
        self._close_current()
        self._current_window = MainWindow(self._dr_name)
        self._current_window.show()

    def _close_current(self):
        if self._current_window:
            self._current_window.close()
            self._current_window = None

    def _on_start_complete(self, result: str, dr_name: str):
        if result == "Yes":
            self._dr_name = dr_name
            self._open_main()
        else:
            QApplication.quit()


def main():
    """主函数"""
    global _backend_proc
    try:
        print("正在启动后端服务...")
        _backend_proc = _start_backend()
        # 等待后端就绪
        import requests
        for _ in range(20):
            try:
                requests.get("http://localhost:8585/music/downloaded", timeout=2)
                print("后端服务已就绪")
                break
            except requests.ConnectionError:
                time.sleep(0.5)
        else:
            print("警告: 后端服务启动超时")

        controller = ApplicationController()
        sys.exit(controller.start())
    except Exception as e:
        print(f"系统启动失败: {e}")
        QMessageBox.critical(None, "启动错误", f"ArkM系统启动失败: {e}")


if __name__ == '__main__':
    main()

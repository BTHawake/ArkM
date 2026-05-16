"""ArkM 音乐系统入口 (PySide6)"""
import os
import sys
import atexit

from PySide6.QtWidgets import QApplication, QMessageBox

from ui.start_window import StartMusic
from ui.main_window import MainWindow
from core.backend_process import BackendProcess

_backend = BackendProcess()


def _on_quit():
    _backend.stop()


atexit.register(_on_quit)


class ApplicationController:
    """应用程序控制器：管理窗口切换路由"""

    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setStyle('Fusion')
        self._current_window = None
        self._dr_name = ""

    def start(self) -> int:
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
        self._current_window = MainWindow(self._dr_name, on_quit=_on_quit)
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
    try:
        print("正在启动后端服务...")
        _backend.start()
        if _backend.wait_ready():
            print("后端服务已就绪")
        else:
            print("警告: 后端服务启动超时")
        controller = ApplicationController()
        sys.exit(controller.start())
    except Exception as e:
        print(f"系统启动失败: {e}")
        QMessageBox.critical(None, "启动错误", f"ArkM系统启动失败: {e}")


if __name__ == '__main__':
    main()

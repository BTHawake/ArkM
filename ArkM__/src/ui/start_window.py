"""启动/唤醒窗口"""
from PySide6.QtWidgets import QMainWindow, QApplication
from PySide6.QtGui import QIcon

from widgets.Start import Ui_StartWindow
from ark_style import START_STYLESHEET


class StartMusic(QMainWindow, Ui_StartWindow):
    def __init__(self, on_complete_callback):
        super().__init__()
        self.on_complete_callback = on_complete_callback
        self.setupUi(self)

        self.setWindowTitle("ArkM音乐系统 - 唤醒界面")
        self.setWindowIcon(QIcon("prts.ico"))
        self.setStyleSheet(START_STYLESHEET)
        self._setup_connection()

    def _setup_connection(self):
        self.okButton.clicked.connect(self._on_ok)
        self.noButton.clicked.connect(self._on_no)

    def _on_ok(self):
        dr_name = self.InputEdit.text().strip()
        filename = "../name/name.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(dr_name)
        self.on_complete_callback("Yes", dr_name)
        self.close()

    def _on_no(self):
        self.on_complete_callback("No", "")
        QApplication.quit()

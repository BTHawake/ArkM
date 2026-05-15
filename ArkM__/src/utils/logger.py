# enhanced_logger.py
import datetime
from PySide6.QtGui import QTextCursor, QFont


class EnhancedLogger:
    def __init__(self, text_browser,download_browser):
        self.text_browser = text_browser
        self.download_browser = download_browser
        self.max_lines = 1000

        # 等宽字体
        font = QFont("Consolas", 9)
        self.text_browser.setFont(font)

    def log(self, message, level="INFO"):
        """添加日志消息"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")

        if level == "INFO":
            prefix = "🔵 [INFO]"
            color = "#00aaff"
        elif level == "WARNING":
            prefix = "🟡 [WARN]"
            color = "#ffaa00"
        elif level == "ERROR":
            prefix = "🔴 [ERROR]"
            color = "#ff4444"
        elif level == "SUCCESS":
            prefix = "🟢 [SUCCESS]"
            color = "#00cc88"
        else:
            prefix = "⚪ [DEBUG]"
            color = "#8888ff"

        log_message = f'<font color="{color}"><b>{prefix}</b> [{timestamp}] {message}</font>'
        self.text_browser.append(log_message)

        # 限制日志行数
        if self.text_browser.document().lineCount() > self.max_lines:
            cursor = self.text_browser.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            cursor.select(QTextCursor.SelectionType.LineUnderCursor)
            cursor.removeSelectedText()

        # 自动滚动到底部
        self.text_browser.moveCursor(QTextCursor.MoveOperation.End)

    def update_progress(self, filename, downloaded, total):
        """更新下载进度显示"""
        if total > 0:
            percent = (downloaded / total) * 100
            progress_text = f'<font color="#00cc88"><b>📥 [下载进度]</b> {filename}: {self.format_size(downloaded)} / {self.format_size(total)} ({percent:.1f}%)</font>'
        else:
            progress_text = f'<font color="#00cc88"><b>📥 [下载进度]</b> {filename}: 正在连接...</font>'
        self.download_browser.clear()
        self.download_browser.append(progress_text)

    def clear_progress(self):
        """清除进度消息标记"""
        self.progress_message_id = None

    def clear(self):
        """清空日志"""
        self.text_browser.clear()
        self.clear_progress()

    @staticmethod
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

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QThread
from PySide6.QtGui import QAction, QDesktopServices
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.gui.worker import CrawlWorker
from app.utils.config import APP_NAME, APP_VERSION
from app.utils.logger import setup_logger


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.resize(900, 640)

        self.thread: QThread | None = None
        self.worker: CrawlWorker | None = None
        self.selected_html_files: list[Path] = []
        self.protected_urls: list[str] = []

        self.logger = setup_logger()

        self.url_input = QTextEdit()
        self.url_input.setPlaceholderText("每行一个URL，可直接粘贴多条")

        self.template_path_input = QLineEdit()
        self.template_path_input.setReadOnly(True)

        self.html_files_input = QLineEdit()
        self.html_files_input.setReadOnly(True)
        self.html_files_input.setPlaceholderText("未选择HTML文件")

        self.output_path_input = QLineEdit()
        self.output_path_input.setReadOnly(True)

        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)

        self.protected_urls_view = QTextEdit()
        self.protected_urls_view.setReadOnly(True)
        self.protected_urls_view.setPlaceholderText("运行后会在这里显示被保护链接")

        self.import_txt_btn = QPushButton("导入TXT中的URL")
        self.import_html_btn = QPushButton("导入HTML文件(反爬备用)")
        self.pick_template_btn = QPushButton("选择Excel模板")
        self.run_btn = QPushButton("开始更新")
        self.open_protected_btn = QPushButton("一键打开被保护链接")
        self.open_protected_btn.setEnabled(False)

        self._build_ui()
        self._wire_events()

    def _build_ui(self) -> None:
        root = QWidget()
        main_layout = QVBoxLayout(root)

        title = QLabel("微信推文名单采集（V1）")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        main_layout.addWidget(title)

        main_layout.addWidget(QLabel("URL列表"))
        main_layout.addWidget(self.url_input)

        row1 = QHBoxLayout()
        row1.addWidget(self.import_txt_btn)
        row1.addWidget(self.import_html_btn)
        row1.addStretch(1)
        main_layout.addLayout(row1)

        main_layout.addWidget(QLabel("已导入HTML文件"))
        main_layout.addWidget(self.html_files_input)

        main_layout.addWidget(QLabel("Excel模板路径"))
        row2 = QHBoxLayout()
        row2.addWidget(self.template_path_input)
        row2.addWidget(self.pick_template_btn)
        main_layout.addLayout(row2)

        row3 = QHBoxLayout()
        row3.addWidget(self.run_btn)
        row3.addWidget(self.open_protected_btn)
        row3.addStretch(1)
        main_layout.addLayout(row3)

        main_layout.addWidget(QLabel("被保护链接清单"))
        main_layout.addWidget(self.protected_urls_view)

        main_layout.addWidget(QLabel("更新后文件路径"))
        main_layout.addWidget(self.output_path_input)

        main_layout.addWidget(QLabel("运行日志"))
        main_layout.addWidget(self.log_view)

        self.setCentralWidget(root)

        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        self.menuBar().addAction(about_action)

    def _wire_events(self) -> None:
        self.import_txt_btn.clicked.connect(self.import_urls_from_txt)
        self.import_html_btn.clicked.connect(self.import_html_files)
        self.pick_template_btn.clicked.connect(self.pick_template)
        self.run_btn.clicked.connect(self.start_job)
        self.open_protected_btn.clicked.connect(self.open_protected_urls)

    def show_about(self) -> None:
        QMessageBox.information(
            self,
            "关于",
            "用于采集微信公众号推文末尾名单并更新Excel模板。\n高级功能: 历史消息批量抓取（开发中）",
        )

    def import_urls_from_txt(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "选择TXT文件", str(Path.cwd()), "Text Files (*.txt)")
        if not path:
            return
        file_text = Path(path).read_text(encoding="utf-8", errors="ignore")
        urls = [line.strip() for line in file_text.splitlines() if line.strip()]
        self.url_input.setPlainText("\n".join(urls))
        self.append_log(f"已导入 {len(urls)} 条URL")

    def pick_template(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "选择Excel模板", str(Path.cwd()), "Excel Files (*.xlsx)")
        if not path:
            return
        self.template_path_input.setText(path)

    def import_html_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "选择HTML文件",
            str(Path.cwd()),
            "HTML Files (*.html *.htm)",
        )
        if not paths:
            return
        self.selected_html_files = [Path(p) for p in paths]
        self.html_files_input.setText(f"已选择 {len(self.selected_html_files)} 个HTML文件")
        self.append_log(f"已导入 {len(self.selected_html_files)} 个HTML文件")

    def start_job(self) -> None:
        urls = [line.strip() for line in self.url_input.toPlainText().splitlines() if line.strip()]
        template_path = self.template_path_input.text().strip()

        if not urls and not self.selected_html_files:
            QMessageBox.warning(self, "提示", "请先输入URL，或导入至少1个HTML文件")
            return
        if not template_path:
            QMessageBox.warning(self, "提示", "请先选择Excel模板")
            return

        self.run_btn.setEnabled(False)
        self.output_path_input.setText("")
        self.protected_urls = []
        self.protected_urls_view.clear()
        self.open_protected_btn.setEnabled(False)
        self.append_log("任务开始")

        self.thread = QThread(self)
        self.worker = CrawlWorker(
            urls=urls,
            template_path=Path(template_path),
            html_files=self.selected_html_files,
        )
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.log_signal.connect(self.append_log)
        self.worker.done_signal.connect(self.on_done)
        self.worker.error_signal.connect(self.on_error)
        self.worker.protected_urls_signal.connect(self.on_protected_urls)

        self.worker.done_signal.connect(self.thread.quit)
        self.worker.error_signal.connect(self.thread.quit)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(self.on_thread_finished)

        self.thread.start()

    def on_done(self, message: str) -> None:
        self.append_log(message)
        marker = "输出文件: "
        if marker in message:
            self.output_path_input.setText(message.split(marker, 1)[1].strip())
        QMessageBox.information(self, "完成", message)

    def on_error(self, message: str) -> None:
        self.append_log(message)
        QMessageBox.critical(self, "错误", message)

    def on_thread_finished(self) -> None:
        self.run_btn.setEnabled(True)
        self.worker = None

    def on_protected_urls(self, urls: list[str]) -> None:
        self.protected_urls = urls
        if not urls:
            self.protected_urls_view.setPlainText("本次没有遇到被保护链接")
            self.open_protected_btn.setEnabled(False)
            return

        self.protected_urls_view.setPlainText("\n".join(urls))
        self.open_protected_btn.setEnabled(True)
        self.append_log(f"本次共 {len(urls)} 条链接被保护，可点击一键打开")

    def open_protected_urls(self) -> None:
        if not self.protected_urls:
            QMessageBox.information(self, "提示", "当前没有被保护链接")
            return

        opened = 0
        for url in self.protected_urls:
            if QDesktopServices.openUrl(QUrl(url)):
                opened += 1
        self.append_log(f"已尝试打开 {opened}/{len(self.protected_urls)} 条被保护链接")

    def append_log(self, message: str) -> None:
        self.logger.info(message)
        self.log_view.append(message)


def run_app() -> None:
    try:
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        sys.exit(app.exec())
    except Exception as exc:  # noqa: BLE001
        # Keep a visible error message in GUI mode executables.
        fallback_app = QApplication.instance() or QApplication(sys.argv)
        QMessageBox.critical(None, "启动失败", f"程序启动失败: {exc}")
        raise

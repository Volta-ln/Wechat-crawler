from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Signal

from app.core.crawler import CrawlProtectedError, fetch_article, fetch_article_from_html_file
from app.core.excel_mgr import write_records
from app.core.extractor import extract_credit_records


class CrawlWorker(QObject):
    log_signal = Signal(str)
    done_signal = Signal(str)
    error_signal = Signal(str)
    protected_urls_signal = Signal(list)

    def __init__(self, urls: list[str], template_path: Path, html_files: list[Path] | None = None) -> None:
        super().__init__()
        self.urls = urls
        self.template_path = template_path
        self.html_files = html_files or []

    def run(self) -> None:
        try:
            all_records = []
            protected_urls: list[str] = []
            total = len(self.urls)
            for idx, url in enumerate(self.urls, start=1):
                self.log_signal.emit(f"[{idx}/{total}] 正在抓取: {url}")
                try:
                    article = fetch_article(url, log=self.log_signal.emit)
                except CrawlProtectedError:
                    protected_urls.append(url)
                    self.log_signal.emit(
                        f"[{idx}/{total}] 链接被保护，已跳过: {url}。"
                        "请在浏览器打开该链接后另存为网页(.html)，再通过‘导入HTML文件’补抓。"
                    )
                    continue
                records = extract_credit_records(article)
                self.log_signal.emit(f"[{idx}/{total}] 抽取到 {len(records)} 条名单记录")
                all_records.extend(records)

            if self.html_files:
                html_total = len(self.html_files)
                for idx, html_file in enumerate(self.html_files, start=1):
                    self.log_signal.emit(f"[HTML {idx}/{html_total}] 正在解析: {html_file.name}")
                    try:
                        article = fetch_article_from_html_file(html_file)
                    except CrawlProtectedError:
                        self.log_signal.emit(
                            f"[HTML {idx}/{html_total}] 该HTML仍是微信保护页: {html_file.name}。"
                            "请先在浏览器完成验证并确认页面含正文后，再另存为HTML导入。"
                        )
                        continue
                    records = extract_credit_records(article)
                    self.log_signal.emit(f"[HTML {idx}/{html_total}] 抽取到 {len(records)} 条名单记录")
                    all_records.extend(records)

                    self.protected_urls_signal.emit(protected_urls)

            if not all_records:
                self.error_signal.emit("未抽取到任何名单记录，请检查URL/HTML内容是否正确")
                return

            output_path, appended = write_records(self.template_path, all_records)
            done_text = f"更新完成。新增 {appended} 条，输出文件: {output_path}"
            if protected_urls:
                done_text += f"；被保护链接 {len(protected_urls)} 条"
            self.done_signal.emit(done_text)
        except Exception as exc:  # noqa: BLE001
            self.error_signal.emit(f"执行失败: {exc}")

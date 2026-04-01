from __future__ import annotations

import random
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable

import httpx
from bs4 import BeautifulSoup

from app.utils.config import DEFAULT_TIMEOUT_SECONDS


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edg/124.0.0.0",
]


@dataclass
class Article:
    title: str
    url: str
    publish_date: str
    content_lines: list[str]


class CrawlError(RuntimeError):
    pass


class CrawlProtectedError(CrawlError):
    pass


def _extract_publish_date(html: str) -> str:
    # WeChat page often has yyyy-mm-dd in scripts or metadata.
    date_patterns = [
        r"(20\d{2}-\d{2}-\d{2})",
        r"(20\d{2}/\d{1,2}/\d{1,2})",
    ]
    for pattern in date_patterns:
        match = re.search(pattern, html)
        if match:
            return match.group(1).replace("/", "-")
    return datetime.now().strftime("%Y-%m-%d")


def _is_wechat_protected(html: str) -> bool:
    markers = [
        "当前环境异常",
        "访问过于频繁",
        "为了保护公众号",
        "Weixin110",
        "环境存在异常",
    ]
    return any(marker in html for marker in markers)


def _parse_article_html(html: str, url: str) -> Article:
    if _is_wechat_protected(html):
        raise CrawlProtectedError(f"链接被微信保护: {url}")

    # Use built-in parser to avoid external parser wheel compatibility issues.
    soup = BeautifulSoup(html, "html.parser")

    title = ""
    if soup.title and soup.title.text:
        title = soup.title.text.strip()
    if not title:
        title_node = soup.select_one("#activity-name")
        title = title_node.get_text(strip=True) if title_node else "未命名推文"

    content_root = soup.select_one("#js_content")
    if not content_root:
        # fallback to body if selector changed.
        content_root = soup.body
    if not content_root:
        raise CrawlError("未找到正文区域")

    raw_lines = [
        line.strip()
        for line in content_root.get_text("\n").splitlines()
        if line.strip()
    ]

    publish_date = _extract_publish_date(html)
    return Article(
        title=title,
        url=url,
        publish_date=publish_date,
        content_lines=raw_lines,
    )


def fetch_article_from_html_file(file_path: Path, source_url: str | None = None) -> Article:
    html = file_path.read_text(encoding="utf-8", errors="ignore")
    return _parse_article_html(html, source_url or f"local-html://{file_path.name}")


def fetch_article(url: str, retry: int = 2, log: Callable[[str], None] | None = None) -> Article:
    if not url.strip():
        raise CrawlError("URL为空")

    last_error: Exception | None = None
    for attempt in range(1, retry + 2):
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.7",
            "Referer": "https://mp.weixin.qq.com/",
            "Cache-Control": "no-cache",
        }
        try:
            with httpx.Client(timeout=DEFAULT_TIMEOUT_SECONDS, follow_redirects=True) as client:
                response = client.get(url, headers=headers)
                response.raise_for_status()

            html = response.text
            return _parse_article_html(html, url)
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if log:
                log(f"抓取失败(第{attempt}次): {url} | {exc}")

    raise CrawlError(f"抓取失败: {url} | {last_error}")

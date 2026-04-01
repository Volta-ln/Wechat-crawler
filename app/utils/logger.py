from __future__ import annotations

import logging
import os
import tempfile
from datetime import datetime
from pathlib import Path

from app.utils.config import APP_NAME


def _candidate_log_dirs() -> list[Path]:
    local_appdata = os.environ.get("LOCALAPPDATA")
    candidates: list[Path] = []
    if local_appdata:
        candidates.append(Path(local_appdata) / "WechatPostCrawler" / "logs")
    candidates.append(Path.cwd() / "logs")
    candidates.append(Path(tempfile.gettempdir()) / "WechatPostCrawler" / "logs")
    return candidates


def _resolve_log_dir() -> Path:
    for directory in _candidate_log_dirs():
        try:
            directory.mkdir(parents=True, exist_ok=True)
            test_file = directory / ".write_test"
            test_file.write_text("ok", encoding="utf-8")
            test_file.unlink(missing_ok=True)
            return directory
        except Exception:
            continue
    raise RuntimeError("无法创建日志目录")


def setup_logger(log_dir: Path | None = None) -> logging.Logger:
    final_log_dir = log_dir or _resolve_log_dir()
    log_path = final_log_dir / f"{datetime.now():%Y%m%d}.log"

    logger = logging.getLogger(APP_NAME)
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    return logger

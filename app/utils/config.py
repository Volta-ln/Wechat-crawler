from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


APP_NAME = "微信推文名单采集工具"
APP_VERSION = "0.1.0"
LOG_DIR = Path("logs")

REQUIRED_FIELDS = [
    "推文标题",
    "推文URL",
    "发布日期",
    "姓名",
    "工作内容/角色",
    "备注",
]

ROLE_KEYWORDS = [
    "文案",
    "摄影",
    "拍摄",
    "剪辑",
    "排版",
    "美编",
    "设计",
    "审核",
    "审校",
    "编辑",
    "责编",
    "出镜",
    "策划",
    "视觉",
    "制作者",
    "采编",
    "校对",
    "指导老师",
    "指导",
    "监制",
    "统筹",
    "记者",
    "文字",
]

# Header aliases for auto mapping; users can still map manually if needed.
HEADER_ALIASES = {
    "推文标题": ["推文标题", "标题", "文章标题"],
    "推文URL": ["推文URL", "URL", "链接", "文章链接"],
    "发布日期": ["发布日期", "日期", "发布时间", "发文日期"],
    "姓名": ["姓名", "成员", "参与人员", "人员"],
    "工作内容/角色": ["工作内容/角色", "角色", "工作内容", "职责"],
    "备注": ["备注", "说明", "附注"],
}

DEFAULT_TIMEOUT_SECONDS = 18
DEFAULT_REMARK = "自动采集"


@dataclass
class AppPaths:
    base_dir: Path

    @property
    def logs_dir(self) -> Path:
        return self.base_dir / LOG_DIR

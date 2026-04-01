from __future__ import annotations

import re
from dataclasses import dataclass

from app.core.crawler import Article
from app.utils.config import DEFAULT_REMARK, ROLE_KEYWORDS


@dataclass
class CreditRecord:
    title: str
    url: str
    publish_date: str
    name: str
    role: str
    remark: str = DEFAULT_REMARK


ROLE_PATTERN = "|".join(re.escape(role) for role in ROLE_KEYWORDS)
PAIR_REGEX = re.compile(
    rf"(?P<role>{ROLE_PATTERN})\s*[|：:/｜丨]\s*(?P<people>.+?)(?=(?:{ROLE_PATTERN})\s*[|：:/｜丨]|$)",
    re.IGNORECASE,
)
ROLE_ONLY_REGEX = re.compile(rf"^(?P<role>{ROLE_PATTERN})\s*[：:|｜丨]?$", re.IGNORECASE)
CHINESE_NAME_REGEX = re.compile(r"^[\u4e00-\u9fa5·]{2,8}$")
ORG_HINTS = ["大学", "学院", "团委", "宣传", "融媒体", "学生会", "中心", "部门", "工作室", "办公室"]
ORG_SUFFIXES = ["书院", "学院", "大学", "团委", "宣传部", "中心", "部门", "工作室", "办公室"]
EXCLUDED_ROLES = {"责编", "审核"}


def _clean_name(raw: str) -> str:
    text = re.sub(r"\s+", "", raw)
    text = re.sub(r"^[\u4e00-\u9fa5A-Za-z0-9]+部", "", text)
    text = text.strip("，,、;；。.")
    return text


def _maybe_extract_name_from_org_text(token: str) -> str:
    if any(hint in token for hint in ORG_HINTS):
        match = re.search(r"([\u4e00-\u9fa5·]{2,4})$", token)
        if match:
            candidate = match.group(1)
            # If the tail still looks like an organization word, discard it.
            if any(hint in candidate for hint in ORG_HINTS):
                return ""
            if any(candidate.endswith(suffix) for suffix in ORG_SUFFIXES):
                return ""
            return candidate
    return token


def _split_people(people_text: str) -> list[str]:
    # Normalize common separators and conjunctions.
    normalized = people_text.replace("以及", "、").replace("和", "、").replace("与", "、")
    chunks = re.split(r"[，,、/；;\s]+", normalized)
    names: list[str] = []
    for chunk in chunks:
        name = _clean_name(chunk)
        if not name:
            continue

        name = _maybe_extract_name_from_org_text(name)
        if not name:
            continue
        if not CHINESE_NAME_REGEX.match(name):
            continue
        if any(hint in name for hint in ORG_HINTS):
            continue
        if any(name.endswith(suffix) for suffix in ORG_SUFFIXES):
            continue
        names.append(name)
    return list(dict.fromkeys(names))


def _tail_lines(lines: list[str], max_count: int = 120) -> list[str]:
    if not lines:
        return []
    return lines[-max_count:]


def _extract_pair_records_from_line(line: str, article: Article) -> list[CreditRecord]:
    records: list[CreditRecord] = []
    for match in PAIR_REGEX.finditer(line):
        role = match.group("role").strip()
        people_text = match.group("people").strip()
        names = _split_people(people_text)
        for name in names:
            records.append(
                CreditRecord(
                    title=article.title,
                    url=article.url,
                    publish_date=article.publish_date,
                    name=name,
                    role=role,
                )
            )
    return records


def _extract_role_only_block(lines: list[str], idx: int, article: Article) -> list[CreditRecord]:
    current = lines[idx]
    role_match = ROLE_ONLY_REGEX.match(current)
    if not role_match:
        return []

    role = role_match.group("role").strip()
    collected: list[str] = []
    for offset in range(1, 4):
        if idx + offset >= len(lines):
            break
        nxt = lines[idx + offset].strip()
        if not nxt:
            break
        if ROLE_ONLY_REGEX.match(nxt):
            break
        if PAIR_REGEX.search(nxt):
            break
        collected.append(nxt)

    if not collected:
        return []

    names = _split_people(" ".join(collected))
    return [
        CreditRecord(
            title=article.title,
            url=article.url,
            publish_date=article.publish_date,
            name=name,
            role=role,
        )
        for name in names
    ]


def extract_credit_records(article: Article) -> list[CreditRecord]:
    records: list[CreditRecord] = []
    tail = _tail_lines(article.content_lines)
    for idx, line in enumerate(tail):
        records.extend(_extract_pair_records_from_line(line, article))
        records.extend(_extract_role_only_block(tail, idx, article))

    # Business rule: ignore all names under excluded roles.
    records = [r for r in records if r.role not in EXCLUDED_ROLES]

    # Dedup inside one article in case multiple matching lines overlap.
    unique = {(r.url, r.publish_date, r.name, r.role): r for r in records}
    return list(unique.values())

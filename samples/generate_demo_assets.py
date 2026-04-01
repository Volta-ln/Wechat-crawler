from __future__ import annotations

import sys
from pathlib import Path

from openpyxl import Workbook

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.core.excel_mgr import write_records
from app.core.extractor import CreditRecord


def create_template(template_path: Path) -> None:
    template_path.parent.mkdir(parents=True, exist_ok=True)
    wb = Workbook()
    ws = wb.active
    ws.title = "统计表"
    ws.append(["推文标题", "推文URL", "发布日期", "姓名", "工作内容/角色", "备注"])
    wb.save(template_path)
    wb.close()


def create_demo_output(template_path: Path, output_dir: Path) -> Path:
    demo_records = [
        CreditRecord(
            title="学院活动推文示例",
            url="https://mp.weixin.qq.com/s/demo-url-1",
            publish_date="2026-03-20",
            name="刘念",
            role="排版",
            remark="自动采集",
        ),
        CreditRecord(
            title="学院活动推文示例",
            url="https://mp.weixin.qq.com/s/demo-url-1",
            publish_date="2026-03-20",
            name="张三",
            role="摄影",
            remark="自动采集",
        ),
    ]
    output_path, _ = write_records(template_path, demo_records, output_dir=output_dir)
    return output_path


def main() -> None:
    repo_root = REPO_ROOT
    template_path = repo_root / "template" / "采集模板.xlsx"
    demo_output_dir = repo_root / "samples"

    create_template(template_path)
    output_path = create_demo_output(template_path, demo_output_dir)

    print(f"模板已生成: {template_path}")
    print(f"演示输出已生成: {output_path}")


if __name__ == "__main__":
    main()

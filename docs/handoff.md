# 交接说明（给后续同学）

## 目录说明

- `app/core/crawler.py`: 微信文章抓取与正文提取。
- `app/core/extractor.py`: 名单文本规则抽取。
- `app/core/excel_mgr.py`: 模板识别、去重、写入新文件。
- `app/gui/main_window.py`: 主界面。
- `app/gui/worker.py`: 后台线程任务。
- `app/utils/config.py`: 角色关键词、字段映射配置。
- `logs/`: 运行日志目录。

## 维护步骤

1. 创建并使用虚拟环境：`python -m venv .venv`
2. 安装依赖：`.venv\Scripts\python.exe -m pip install -r requirements.txt`
3. 启动：`.venv\Scripts\python.exe main.py`
4. 生成示例模板和演示输出：`.venv\Scripts\python.exe samples/generate_demo_assets.py`
5. 测试：用 `samples/sample_urls.txt` 的URL列表跑一遍。
6. 打包：`.venv\Scripts\python.exe -m PyInstaller --noconfirm --onefile --windowed --name WechatPostCrawler main.py`

## 可扩展点

1. `extractor.py` 增加更多名单格式规则。
2. `config.py` 增加字段别名与角色关键词。
3. 在UI中新增设置页（角色关键词编辑）。
4. 新增公众号历史消息批量抓取模块（当前仅预留说明）。

## 问题定位

- 程序报错时，先看 `logs/YYYYMMDD.log`。
- 抓取失败通常是网络或反爬限制。
- 写入失败通常是Excel文件被占用或模板缺字段。

## 当前交付产物

- 模板文件：`template/采集模板.xlsx`
- 演示写入文件：`samples/采集模板_updated_*.xlsx`
- 可执行程序：`dist/WechatPostCrawler.exe`

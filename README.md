# 微信推文名单采集工具（V1）

面向学院媒体部的桌面工具：输入微信推文URL，导入Excel模板，自动抽取文末参与人员与工作角色，去重后生成更新文件。

## 功能

- 支持多URL粘贴输入（每行一个）。
- 支持从TXT导入URL列表。
- 支持导入现有Excel模板（.xlsx）。
- 支持文末名单抽取（示例: `排版 | 同济大学团委宣传部 刘念`）。
- 按 `推文URL + 姓名 + 工作内容/角色 + 发布日期` 去重。
- 一次性写入新文件，不覆盖原模板。

## 环境

- Windows 10/11
- Python 3.10+

## 强烈建议: 只用项目虚拟环境

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

如果你不想激活虚拟环境，也可以始终使用显式解释器路径：

```bash
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 安装与运行

```bash
.venv\Scripts\python.exe main.py
```

## 生成模板与演示输出

```bash
.venv\Scripts\python.exe samples/generate_demo_assets.py
```

执行后会生成：
- `template/采集模板.xlsx`（可直接导入UI）
- `samples/采集模板_updated_时间戳.xlsx`（演示写入结果）

## Excel模板要求

模板首行或前10行内，需要包含以下字段中的中文表头（可同义名）:

- 推文标题
- 推文URL
- 发布日期
- 姓名
- 工作内容/角色
- 备注

若字段不完整，程序会报错并提示缺失字段。

## 打包为 .exe（建议）

```bash
.venv\Scripts\python.exe -m pip install pyinstaller
.venv\Scripts\python.exe -m PyInstaller --noconfirm --onefile --windowed --name WechatPostCrawler main.py
```

打包后可执行文件位于 `dist/WechatPostCrawler.exe`。

## 常见问题

1. 抽取结果为0
- 可能是推文末尾格式不匹配，可在 `app/utils/config.py` 扩展角色关键词。

2. Excel写入失败
- 请先关闭已打开的Excel文件再重试。

3. 微信链接抓取失败
- 可能是网络或风控问题，稍后重试，或改用其他网络。

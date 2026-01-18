# 行业标准信息爬虫 (Industry Standard Scraper) 

![GUI Screenshot](assets/gui_screenshot.png)

## 📌 项目简介

这是一个功能强大的行业标准信息爬取工具，专为从 [行业标准信息服务平台](https://hbba.sacinfo.org.cn/) 抓取最新的标准列表、详情以及**自动下载 PDF 全文**而设计。

v2.1 版本集成了 **PySide6 可视化界面** 和 **ddddocr / EasyOCR 自动验证码识别**，实现了全自动化的一键爬取，无需人工干预即可批量下载标准文件。

## ✨ 核心功能

*   **GUI 可视化操作**：提供现代化的 Qt 界面，支持实时日志监控、进度显示和一键打开结果目录。
*   **智能验证码识别**：
    *   **ddddocr (推荐)**: 内置深度学习模型，无需配置，识别成功率接近 100%（需 Python < 3.14 或使用打包版）。
    *   **EasyOCR**: 强大的备选方案，兼容性好，支持多种环境。
    *   **人工模式**: 当自动识别失败时的兜底方案。
*   **精准筛选**：支持按**部委**（如应急管理部）、**行业代码**（如 AQ, HG）、**标准状态**（现行/废止）进行组合筛选。
*   **全自动 PDF 下载**：自动处理详情页跳转、验证码输入，下载标准全文 PDF 并自动重命名（格式：`标准号-标准名.pdf`）。
*   **断点续传**：意外中断后，支持从检查点恢复，不丢失已爬取数据。
*   **反爬策略**：内置随机延迟、User-Agent 轮询和行为模拟，安全稳定。

---

## 🚀 快速开始

### 方式一：使用安装包 (推荐普通用户)

无需安装 Python 环境，下载即用。

*   **MacOS**: 下载 release 中的 `.dmg` 文件，双击安装。
    > **⚠️ 注意**: 由于安装包未内置浏览器内核（以减小体积），首次运行若报错 "Executable doesn't exist"，请在终端运行：
    > `pip install playwright && playwright install chromium`
*   **Windows**: 目前暂未提供预编译包，请参考下方的 **"方式二：源码运行"**，或在 Windows 环境下运行 `python build_win.py` 自行构建。

### 方式二：源码运行 (推荐开发者)

#### 1. 环境准备

推荐使用 Python 3.10 - 3.13 版本 (Python 3.14 暂未完全兼容 ddddocr)。

```bash
# 1. 克隆项目
git clone https://github.com/cikorsky/industry_standard_scraper.git
cd industry_standard_scraper

# 2. 创建并激活虚拟环境 (强烈推荐)
python3.13 -m venv venv
source venv/bin/activate  # MacOS/Linux
# venv\Scripts\activate   # Windows

# 3. 安装依赖 (会自动安装 Python 库和 浏览器内核)
pip install -r requirements.txt
playwright install chromium
```

#### 2. 启动程序

**启动可视化界面 (GUI):**
```bash
python gui_app.py
# 或使用脚本
./run_gui.sh
```

**启动命令行模式 (CLI):**
```bash
# 仅爬取清单 (极快)
python scraper_list_only.py

# 完整爬取 (含 PDF 下载)
python scraper.py
```

---

## ⚙️ 配置指南

绝大部分配置可通过 GUI 界面的 **"高级选项"** 直接设置。如使用命令行或需深度定制，请修改 `config.py`。

### 1. 验证码与 OCR

在 `config.py` 中 `CAPTCHA_CONFIG` 控制 OCR 行为：

```python
CAPTCHA_CONFIG = {
    "ocr_engine": "ddddocr",   # 选项: 'ddddocr', 'easyocr', 'tesseract', 'manual'
    "retry": 3,                # 自动重试次数
    "easyocr_langs": ['en'],   # EasyOCR 语言
    "confidence_threshold": 0.6 # 置信度阈值
}
```

*   **ddddocr**: 速度快，准确率高，首选。
*   **EasyOCR**: 需要下载模型（首次运行自动下载），准确率不错。
*   **Manual**: 终端弹出图片，人工输入，100% 准确。

### 2. 爬虫策略

```python
DELAY_CONFIG = {
    "list_page": (1, 2),      # 列表翻页随机延迟 (秒)
    "download": (3, 5),       # 下载间隔随机延迟 (秒)
}

BROWSER_CONFIG = {
    "headless": False,        # True=后台运行, False=显示浏览器窗口(便于调试)
    "timeout": 30000,
}
```

---

## ❓ 常见问题 (FAQ)

### Q1: 运行报错 `No module named ddddocr` 或安装失败？
**A**: `ddddocr` 目前对 Python 3.14+ 支持不佳。
*   **解决**: 请使用 Python 3.13 或更低版本创建虚拟环境。
*   **替代**: 在配置中切换为 `ocr_engine: "easyocr"`。

### Q2: PDF 下载失败或验证码一直错误？
**A**: 
1. 网站可能更新了验证码机制，请在 GUI 开启 "显示浏览器窗口" 观察情况。
2. 尝试增加 `DELAY_CONFIG` 中的延迟时间。
3. 切换 OCR 引擎或暂时使用 "Manual" 人工模式。

### Q3: 程序运行一半中断了怎么办？
**A**: 程序会自动保存进度到 `output/checkpoint.json` (或类似机制)。重新运行程序，它会自动跳过已下载的标准。

### Q4: 报错 `Executable doesn't exist` 或 `BrowserType.launch: ...`？
**A**: 这是因为 Playwright 找不到浏览器内核（Chromium）。
*   如果您使用的是安装包，请在终端（Terminal）运行：
    ```bash
    pip install playwright
    playwright install chromium
    ```
*   如果您是源码运行，请确保执行了 `playwright install chromium`。

---

## 📂 输出文件

所有结果保存在 `output/` 目录：
*   **Excel 清单**: `output/standards.xlsx` (包含标准号、名称、状态、起草单位等详细信息)
*   **PDF 原文**: `output/pdfs/` (自动重命名的标准文件)
*   **运行日志**: `logs/scraper.log`

---

## ❤️ 致谢

本项目使用了以下优秀的开源库：
*   [ddddocr](https://github.com/sml2h3/ddddocr): 极其优秀的通用验证码识别库。
*   [Playwright](https://playwright.dev/): 稳定高效的新一代浏览器自动化工具。
*   [PySide6](https://doc.qt.io/qtforpython/): 用于构建漂亮的跨平台 GUI。
*   [EasyOCR](https://github.com/JaidedAI/EasyOCR): 强大的多语言 OCR 库。
*   [Pandas](https://pandas.pydata.org/): 强大的数据分析和处理库。
*   [OpenCV](https://opencv.org/): 计算机视觉库，用于验证码图像预处理。
*   [Pillow](https://python-pillow.org/): Python 图像处理库。
*   [NumPy](https://numpy.org/): 科学计算基础库。

## ⚠️ 免责声明

本工具仅供技术学习和科研归档使用，请勿用于商业用途或非法用途。使用本工具时请严格遵守目标网站的 `robots.txt` 协议，合理控制爬取频率，避免对目标服务器造成压力。

## 📄 许可证

[MIT License](LICENSE)

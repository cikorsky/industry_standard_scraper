"""
配置文件 - 行业标准爬虫
"""

# ==================== 筛选条件配置 ====================
FILTER_CONFIG = {
    # 部委筛选 (None表示不筛选)
    "department": "国家市场监督管理总局",  # 示例: "应急管理部", None
    
    # 行业代码筛选 (None表示不筛选)
    "industry_code": None,  # 示例: "AQ", "GA", None
    
    # 标准状态筛选
    "status": "现行",  # 示例: "现行", "废止", None
}

# ==================== 爬取控制配置 ====================
# 并发控制
MAX_CONCURRENT = 3  # 同时处理的详情页数量(建议1-5)

# 延迟控制(秒)
DELAY_CONFIG = {
    "list_page": (1, 2),      # 列表页翻页延迟
    "detail_page": (2, 4),    # 详情页访问延迟
    "download": (3, 5),       # PDF下载延迟
}

# 分页配置
PAGE_SIZE = 100  # 每页显示数量: 15, 25, 50, 100

# ==================== 验证码识别配置 ====================
CAPTCHA_CONFIG = {
    "retry": 3,                    # 验证码识别失败重试次数
    "use_manual": False,           # 是否启用人工输入
    "ocr_engine": "ddddocr",       # OCR引擎: "easyocr", "tesseract", "ddddocr", "manual"
    "confidence_threshold": 0.4,   # 识别置信度阈值(彩色验证码建议0.3-0.5)
    
    # EasyOCR配置
    "easyocr_langs": ['en'],       # 识别语言: ['en'], ['ch_sim', 'en']
    "easyocr_gpu": False,          # 是否使用GPU加速
    
    # Tesseract配置
    "tesseract_config": "--psm 7 --oem 3",  # Tesseract配置参数
}

# ==================== 浏览器配置 ====================
BROWSER_CONFIG = {
    "headless": False,  # 是否无头模式(调试时建议False)
    "timeout": 60000,   # 页面加载超时(毫秒)
    "viewport": {
        "width": 1920,
        "height": 1080,
    },
}

# ==================== 路径配置 ====================
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
PDF_DIR = os.path.join(OUTPUT_DIR, "pdfs")
LOG_DIR = os.path.join(BASE_DIR, "logs")

# 输出文件名
EXCEL_OUTPUT = os.path.join(OUTPUT_DIR, "standards.xlsx")
LOG_FILE = os.path.join(LOG_DIR, "scraper.log")

# ==================== URL配置 ====================
BASE_URL = "https://hbba.sacinfo.org.cn"
LIST_URL = f"{BASE_URL}/stdList"
DETAIL_URL_TEMPLATE = f"{BASE_URL}/stdDetail/{{hash_id}}"
ONLINE_URL_TEMPLATE = f"{BASE_URL}/portal/online/{{hash_id}}"

# ==================== User-Agent池 ====================
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
]

# ==================== 日志配置 ====================
LOG_CONFIG = {
    "level": "INFO",  # DEBUG, INFO, WARNING, ERROR
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "date_format": "%Y-%m-%d %H:%M:%S",
}

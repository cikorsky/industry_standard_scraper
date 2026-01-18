"""
工具函数模块
"""
import re
import time
import random
import logging
from pathlib import Path
from typing import Tuple
from config import LOG_CONFIG, LOG_FILE

def setup_logger(name: str = "scraper") -> logging.Logger:
    """设置日志记录器"""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LOG_CONFIG["level"]))
    
    # 避免重复添加handler
    if logger.handlers:
        return logger
    
    # 文件处理器
    Path(LOG_FILE).parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 格式化
    formatter = logging.Formatter(
        LOG_CONFIG["format"],
        datefmt=LOG_CONFIG["date_format"]
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def sanitize_filename(filename: str) -> str:
    """
    清理文件名中的非法字符
    
    Args:
        filename: 原始文件名
        
    Returns:
        清理后的安全文件名
    """
    # 替换Windows和Unix系统中的非法字符
    illegal_chars = r'[\\/:*?"<>|]'
    safe_name = re.sub(illegal_chars, '_', filename)
    
    # 移除首尾空格和点
    safe_name = safe_name.strip('. ')
    
    # 限制文件名长度(Windows最大255字符)
    if len(safe_name) > 200:
        safe_name = safe_name[:200]
    
    return safe_name

def random_delay(delay_range: Tuple[float, float]) -> None:
    """
    随机延迟
    
    Args:
        delay_range: 延迟范围(最小值, 最大值)
    """
    delay = random.uniform(*delay_range)
    time.sleep(delay)

def format_pdf_filename(std_code: str, std_name: str, extension: str = "pdf") -> str:
    """
    格式化PDF文件名: 标准代码-标准名称.pdf
    
    Args:
        std_code: 标准代码
        std_name: 标准名称
        extension: 文件扩展名
        
    Returns:
        格式化后的文件名
    """
    # 清理标准代码和名称
    safe_code = sanitize_filename(std_code)
    safe_name = sanitize_filename(std_name)
    
    # 组合文件名
    filename = f"{safe_code}-{safe_name}.{extension}"
    
    return filename

def extract_hash_id_from_url(url: str) -> str:
    """
    从详情页URL中提取hash_id
    
    Args:
        url: 详情页URL
        
    Returns:
        hash_id
    """
    # URL格式: https://hbba.sacinfo.org.cn/stdDetail/{hash_id}
    match = re.search(r'/stdDetail/([a-f0-9]+)', url)
    if match:
        return match.group(1)
    return ""

def get_random_user_agent() -> str:
    """获取随机User-Agent"""
    from config import USER_AGENTS
    return random.choice(USER_AGENTS)

def ensure_dir(directory: str) -> None:
    """确保目录存在"""
    Path(directory).mkdir(parents=True, exist_ok=True)

def parse_date(date_str: str) -> str:
    """
    解析日期字符串,统一格式
    
    Args:
        date_str: 日期字符串
        
    Returns:
        格式化后的日期(YYYY-MM-DD)
    """
    if not date_str or date_str.strip() == "":
        return ""
    
    # 移除空格
    date_str = date_str.strip()
    
    # 已经是标准格式
    if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
        return date_str
    
    # 其他格式转换(根据实际情况扩展)
    return date_str

def clean_text(text: str) -> str:
    """
    清理文本中的多余空白字符
    
    Args:
        text: 原始文本
        
    Returns:
        清理后的文本
    """
    if not text:
        return ""
    
    # 替换多个空白字符为单个空格
    cleaned = re.sub(r'\s+', ' ', text)
    
    # 移除首尾空格
    cleaned = cleaned.strip()
    
    return cleaned

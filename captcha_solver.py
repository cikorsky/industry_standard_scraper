"""
验证码识别模块 - 支持多种OCR引擎
"""
import base64
import io
import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image
from playwright.sync_api import Page
from utils import setup_logger
from config import CAPTCHA_CONFIG

# 修复 Pillow 10.0+ 移除 ANTIALIAS 的问题,以兼容 ddddocr
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.LANCZOS

logger = setup_logger("captcha_solver")

class CaptchaSolver:
    """验证码识别器 - 支持多种OCR引擎"""
    
    def __init__(self, ocr_engine: str = None, use_manual: bool = False):
        """
        初始化验证码识别器
        
        Args:
            ocr_engine: OCR引擎类型 ("easyocr", "tesseract", "ddddocr", "manual")
            use_manual: 是否强制使用人工输入
        """
        self.use_manual = use_manual
        self.ocr_engine_type = ocr_engine or CAPTCHA_CONFIG.get("ocr_engine", "easyocr")
        self.ocr = None
        
        if not use_manual:
            self._init_ocr_engine()
    
    def _init_ocr_engine(self):
        """初始化OCR引擎"""
        try:
            if self.ocr_engine_type == "easyocr":
                self._init_easyocr()
            elif self.ocr_engine_type == "tesseract":
                self._init_tesseract()
            elif self.ocr_engine_type == "ddddocr":
                self._init_ddddocr()
            else:
                logger.warning(f"未知的OCR引擎: {self.ocr_engine_type},将使用人工输入模式")
                self.use_manual = True
        except Exception as e:
            logger.error(f"OCR引擎初始化失败: {e},将使用人工输入模式")
            self.use_manual = True
    
    def _init_easyocr(self):
        """初始化EasyOCR"""
        try:
            import easyocr
            langs = CAPTCHA_CONFIG.get("easyocr_langs", ['en'])
            gpu = CAPTCHA_CONFIG.get("easyocr_gpu", False)
            
            logger.info(f"正在初始化EasyOCR (语言: {langs}, GPU: {gpu})...")
            self.ocr = easyocr.Reader(langs, gpu=gpu)
            logger.info("EasyOCR初始化成功")
        except ImportError:
            logger.error("EasyOCR未安装,请运行: pip install easyocr")
            raise
        except Exception as e:
            logger.error(f"EasyOCR初始化失败: {e}")
            raise
    
    def _init_tesseract(self):
        """初始化Tesseract OCR"""
        try:
            import pytesseract
            # 测试Tesseract是否可用
            pytesseract.get_tesseract_version()
            self.ocr = pytesseract
            logger.info("Tesseract OCR初始化成功")
        except ImportError:
            logger.error("pytesseract未安装,请运行: pip install pytesseract")
            raise
        except Exception as e:
            logger.error(f"Tesseract OCR初始化失败: {e}")
            logger.error("请确保已安装Tesseract: brew install tesseract (Mac) 或访问 https://github.com/tesseract-ocr/tesseract")
            raise
    
    def _init_ddddocr(self):
        """初始化ddddocr"""
        try:
            import ddddocr
            self.ocr = ddddocr.DdddOcr()  # 新版本不需要show_ad参数
            logger.info("ddddocr初始化成功")
        except ImportError:
            logger.error("ddddocr未安装或不兼容当前Python版本")
            raise
        except Exception as e:
            logger.error(f"ddddocr初始化失败: {e}")
            raise
    
    def extract_captcha_image(self, page: Page) -> Optional[bytes]:
        """
        从页面提取验证码图片
        
        Args:
            page: Playwright页面对象
            
        Returns:
            验证码图片的字节数据
        """
        try:
            # 等待验证码图片加载(使用正确的选择器)
            page.wait_for_selector("#validate-code", timeout=10000)
            
            # 获取验证码图片元素
            captcha_img = page.query_selector("#validate-code")
            if not captcha_img:
                logger.error("未找到验证码图片元素")
                return None
            
            # 获取图片的src属性
            img_src = captcha_img.get_attribute("src")
            
            if img_src and img_src.startswith("data:image"):
                # Base64编码的图片
                base64_data = img_src.split(",")[1]
                img_bytes = base64.b64decode(base64_data)
            else:
                # URL图片,截取元素
                img_bytes = captcha_img.screenshot()
            
            logger.info("验证码图片提取成功")
            return img_bytes
            
        except Exception as e:
            logger.error(f"提取验证码图片失败: {e}")
            return None
    
    def preprocess_image(self, img_bytes: bytes) -> np.ndarray:
        """
        预处理验证码图片(针对彩色字符和干扰线优化)
        
        Args:
            img_bytes: 原始图片字节数据
            
        Returns:
            预处理后的图片(numpy数组)
        """
        try:
            # 转换为PIL Image
            img = Image.open(io.BytesIO(img_bytes))
            
            # 转换为numpy数组
            img_array = np.array(img)
            
            # 如果是RGBA,转换为RGB
            if len(img_array.shape) == 3 and img_array.shape[2] == 4:
                img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB)
            
            # 转换为灰度图
            if len(img_array.shape) == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array
            
            # 放大图片(提高识别率)
            scale_factor = 3
            height, width = gray.shape
            gray = cv2.resize(gray, (width * scale_factor, height * scale_factor), 
                            interpolation=cv2.INTER_CUBIC)
            
            # 高斯模糊(去除噪点)
            blurred = cv2.GaussianBlur(gray, (3, 3), 0)
            
            # 自适应阈值二值化(对不均匀光照更有效)
            binary = cv2.adaptiveThreshold(
                blurred, 255, 
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 
                11, 2
            )
            
            # 反转颜色(如果背景是白色,字符是黑色)
            # 检查平均亮度,如果背景较暗则反转
            if np.mean(binary) < 127:
                binary = cv2.bitwise_not(binary)
            
            # 形态学操作(去除小噪点,连接断裂字符)
            kernel = np.ones((2, 2), np.uint8)
            
            # 先腐蚀(去除小噪点)
            eroded = cv2.erode(binary, kernel, iterations=1)
            
            # 再膨胀(恢复字符大小)
            dilated = cv2.dilate(eroded, kernel, iterations=1)
            
            # 中值滤波(进一步降噪)
            cleaned = cv2.medianBlur(dilated, 3)
            
            logger.debug("图片预处理完成(增强版)")
            return cleaned
            
        except Exception as e:
            logger.error(f"图片预处理失败: {e}")
            # 返回原始图片
            img = Image.open(io.BytesIO(img_bytes))
            return np.array(img)
    
    def solve_captcha(self, img_bytes: bytes) -> Optional[str]:
        """
        识别验证码
        
        Args:
            img_bytes: 验证码图片字节数据
            
        Returns:
            识别结果
        """
        if self.use_manual:
            return self._manual_input(img_bytes)
        
        try:
            if self.ocr_engine_type == "easyocr":
                return self._solve_with_easyocr(img_bytes)
            elif self.ocr_engine_type == "tesseract":
                return self._solve_with_tesseract(img_bytes)
            elif self.ocr_engine_type == "ddddocr":
                return self._solve_with_ddddocr(img_bytes)
            else:
                return self._manual_input(img_bytes)
                
        except Exception as e:
            logger.error(f"验证码识别失败: {e}")
            return self._manual_input(img_bytes)
    
    def _solve_with_easyocr(self, img_bytes: bytes) -> Optional[str]:
        """使用EasyOCR识别"""
        try:
            # 预处理图片
            img_array = self.preprocess_image(img_bytes)
            
            # 识别
            results = self.ocr.readtext(img_array, detail=1)
            
            if not results:
                logger.warning("EasyOCR未识别到文本")
                return None
            
            # 提取置信度最高的结果
            best_result = max(results, key=lambda x: x[2])
            text, confidence = best_result[1], best_result[2]
            
            # 清理结果
            text = text.strip().replace(" ", "").replace("-", "")
            
            logger.info(f"EasyOCR识别结果: {text} (置信度: {confidence:.2f})")
            
            # 检查置信度
            threshold = CAPTCHA_CONFIG.get("confidence_threshold", 0.6)
            if confidence < threshold:
                logger.warning(f"识别置信度过低 ({confidence:.2f} < {threshold})")
                return None
            
            return text
            
        except Exception as e:
            logger.error(f"EasyOCR识别失败: {e}")
            return None
    
    def _solve_with_tesseract(self, img_bytes: bytes) -> Optional[str]:
        """使用Tesseract OCR识别"""
        try:
            # 预处理图片
            img_array = self.preprocess_image(img_bytes)
            
            # 转换为PIL Image
            img = Image.fromarray(img_array)
            
            # 获取配置
            config = CAPTCHA_CONFIG.get("tesseract_config", "--psm 7 --oem 3")
            
            # 识别
            text = self.ocr.image_to_string(img, config=config)
            
            # 清理结果
            text = text.strip().replace(" ", "").replace("\n", "")
            
            logger.info(f"Tesseract识别结果: {text}")
            
            if not text:
                logger.warning("Tesseract未识别到文本")
                return None
            
            return text
            
        except Exception as e:
            logger.error(f"Tesseract识别失败: {e}")
            return None
    
    def _solve_with_ddddocr(self, img_bytes: bytes) -> Optional[str]:
        """使用ddddocr识别"""
        try:
            # ddddocr不需要预处理
            result = self.ocr.classification(img_bytes)
            
            # 清理结果
            result = result.strip().replace(" ", "")
            
            logger.info(f"ddddocr识别结果: {result}")
            return result
            
        except Exception as e:
            logger.error(f"ddddocr识别失败: {e}")
            return None
    
    def _manual_input(self, img_bytes: bytes) -> Optional[str]:
        """
        人工输入验证码
        
        Args:
            img_bytes: 验证码图片字节数据
            
        Returns:
            用户输入的验证码
        """
        try:
            # 保存验证码图片到临时文件
            temp_path = Path("temp_captcha.png")
            with open(temp_path, "wb") as f:
                f.write(img_bytes)
            
            logger.info(f"验证码图片已保存到: {temp_path.absolute()}")
            print(f"\n请查看验证码图片: {temp_path.absolute()}")
            
            # 等待用户输入
            captcha_text = input("请输入验证码: ").strip()
            
            # 删除临时文件
            temp_path.unlink(missing_ok=True)
            
            return captcha_text
            
        except Exception as e:
            logger.error(f"人工输入验证码失败: {e}")
            return None
    
    def refresh_captcha(self, page: Page) -> bool:
        """
        刷新验证码
        
        Args:
            page: Playwright页面对象
            
        Returns:
            是否刷新成功
        """
        try:
            # 查找刷新按钮(使用正确的选择器)
            refresh_btn = page.query_selector(".fa-refresh")
            
            if refresh_btn:
                refresh_btn.click()
                page.wait_for_timeout(1000) # 等待新验证码加载
                logger.info("验证码已刷新")
                return True
            else:
                logger.warning("未找到验证码刷新按钮")
                return False
                
        except Exception as e:
            logger.error(f"刷新验证码失败: {e}")
            return False
    
    def verify_and_download(
        self, 
        page: Page, 
        download_btn_selector: str = "#download-btn",
        max_retry: int = 3
    ) -> Tuple[Optional[object], Optional[str]]:  # 使用object避免循环导入，或者确保已导入Download
        """
        验证验证码并下载文件
        
        Args:
            page: Playwright页面对象
            download_btn_selector: 下载按钮选择器
            max_retry: 最大重试次数
            
        Returns:
            (Download对象, 错误信息)
        """
        for attempt in range(max_retry):
            try:
                logger.info(f"验证码识别尝试 {attempt + 1}/{max_retry}")
                
                # 提取验证码图片
                img_bytes = self.extract_captcha_image(page)
                if not img_bytes:
                    logger.error("无法提取验证码图片")
                    continue
                
                # 识别验证码
                captcha_text = self.solve_captcha(img_bytes)
                if not captcha_text:
                    logger.error("验证码识别失败")
                    # 刷新验证码重试
                    self.refresh_captcha(page)
                    continue
                
                # 输入验证码
                captcha_input = page.query_selector("#captcha-input")
                if not captcha_input:
                    logger.error("未找到验证码输入框")
                    return None, "未找到验证码输入框"
                
                captcha_input.fill(captcha_text)
                logger.info(f"已输入验证码: {captcha_text}")
                
                # 等待一下
                page.wait_for_timeout(500)
                
                # 点击下载按钮
                download_btn = page.query_selector(download_btn_selector)
                if not download_btn:
                    logger.error(f"未找到下载按钮: {download_btn_selector}")
                    return None, "未找到下载按钮"
                
                # 监听下载事件
                with page.expect_download(timeout=30000) as download_info:
                    download_btn.click()
                    logger.info("已点击下载按钮,等待下载...")
                
                download = download_info.value
                logger.info(f"下载成功: {download.suggested_filename}")
                return download, None
                
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"第 {attempt + 1} 次尝试失败: {error_msg}")
                
                # 检查是否是验证码错误
                if "验证码" in error_msg or "captcha" in error_msg.lower():
                    # 刷新验证码重试
                    self.refresh_captcha(page)
                    continue
                else:
                    # 其他错误,直接返回
                    return None, error_msg
        
        return None, f"验证码识别失败,已重试{max_retry}次"

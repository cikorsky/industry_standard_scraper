"""
验证码识别测试脚本
"""
from playwright.sync_api import sync_playwright
from captcha_solver import CaptchaSolver
from utils import setup_logger
from config import BROWSER_CONFIG, CAPTCHA_CONFIG
import sys

logger = setup_logger("test_captcha")

def test_captcha_recognition(ocr_engine: str = None):
    """
    测试验证码识别
    
    Args:
        ocr_engine: OCR引擎类型 ("easyocr", "tesseract", "manual")
    """
    # 测试URL
    test_url = "https://hbba.sacinfo.org.cn/portal/online/382b9507ac5297f5f36cbc51e67d71418fe1d92996727162f185eeff93ceaea7"
    
    logger.info("="*60)
    logger.info("验证码识别测试")
    logger.info("="*60)
    logger.info(f"OCR引擎: {ocr_engine or CAPTCHA_CONFIG.get('ocr_engine')}")
    logger.info(f"测试URL: {test_url}")
    
    with sync_playwright() as p:
        # 启动浏览器
        browser = p.chromium.launch(headless=BROWSER_CONFIG["headless"])
        context = browser.new_context(viewport=BROWSER_CONFIG["viewport"])
        page = context.new_page()
        page.set_default_timeout(BROWSER_CONFIG["timeout"])
        
        try:
            # 初始化验证码识别器
            logger.info("\n初始化验证码识别器...")
            solver = CaptchaSolver(ocr_engine=ocr_engine)
            
            # 访问页面
            logger.info("\n访问验证码页面...")
            page.goto(test_url)
            page.wait_for_timeout(3000)
            
            # 等待验证码弹窗
            logger.info("\n等待验证码弹窗...")
            page.wait_for_selector("#captcha-input", timeout=10000)
            
            # 截图
            screenshot_path = "test_captcha_page.png"
            page.screenshot(path=screenshot_path)
            logger.info(f"页面截图已保存: {screenshot_path}")
            
            # 测试验证码识别(3次)
            success_count = 0
            total_tests = 3
            
            for i in range(total_tests):
                logger.info(f"\n{'='*60}")
                logger.info(f"第 {i+1}/{total_tests} 次测试")
                logger.info(f"{'='*60}")
                
                # 提取验证码图片
                logger.info("提取验证码图片...")
                img_bytes = solver.extract_captcha_image(page)
                
                if not img_bytes:
                    logger.error("提取验证码图片失败")
                    continue
                
                # 保存验证码图片
                captcha_img_path = f"test_captcha_{i+1}.png"
                with open(captcha_img_path, "wb") as f:
                    f.write(img_bytes)
                logger.info(f"验证码图片已保存: {captcha_img_path}")
                
                # 识别验证码
                logger.info("识别验证码...")
                result = solver.solve_captcha(img_bytes)
                
                if result:
                    logger.info(f"✅ 识别成功: {result}")
                    success_count += 1
                else:
                    logger.warning("❌ 识别失败")
                
                # 刷新验证码(除了最后一次)
                if i < total_tests - 1:
                    logger.info("刷新验证码...")
                    solver.refresh_captcha(page)
                    page.wait_for_timeout(2000)
            
            # 统计结果
            logger.info(f"\n{'='*60}")
            logger.info("测试结果统计")
            logger.info(f"{'='*60}")
            logger.info(f"总测试次数: {total_tests}")
            logger.info(f"识别成功: {success_count}")
            logger.info(f"识别失败: {total_tests - success_count}")
            logger.info(f"成功率: {success_count/total_tests*100:.1f}%")
            logger.info(f"{'='*60}")
            
        except Exception as e:
            logger.error(f"测试失败: {e}", exc_info=True)
            
        finally:
            browser.close()

def main():
    """主函数"""
    print("\n验证码识别测试工具")
    print("="*60)
    print("支持的OCR引擎:")
    print("1. easyocr   - 深度学习OCR(推荐)")
    print("2. tesseract - 传统OCR")
    print("3. manual    - 人工输入")
    print("="*60)
    
    # 从命令行参数获取OCR引擎
    if len(sys.argv) > 1:
        ocr_engine = sys.argv[1]
    else:
        choice = input("\n请选择OCR引擎(1-3,默认1): ").strip() or "1"
        engine_map = {
            "1": "easyocr",
            "2": "tesseract",
            "3": "manual"
        }
        ocr_engine = engine_map.get(choice, "easyocr")
    
    print(f"\n使用OCR引擎: {ocr_engine}")
    print("="*60)
    
    test_captcha_recognition(ocr_engine)

if __name__ == "__main__":
    main()

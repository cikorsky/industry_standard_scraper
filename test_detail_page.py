"""
测试脚本 - 测试单个详情页爬取
"""
from playwright.sync_api import sync_playwright
from utils import setup_logger, clean_text
from config import BROWSER_CONFIG

logger = setup_logger("test")

def test_detail_page():
    """测试详情页爬取"""
    
    # 测试URL
    test_url = "https://hbba.sacinfo.org.cn/stdDetail/382b9507ac5297f5f36cbc51e67d71418fe1d92996727162f185eeff93ceaea7"
    
    logger.info("开始测试详情页爬取...")
    logger.info(f"测试URL: {test_url}")
    
    with sync_playwright() as p:
        # 启动浏览器
        browser = p.chromium.launch(headless=BROWSER_CONFIG["headless"])
        context = browser.new_context(viewport=BROWSER_CONFIG["viewport"])
        page = context.new_page()
        page.set_default_timeout(BROWSER_CONFIG["timeout"])
        
        try:
            # 访问详情页
            logger.info("正在访问详情页...")
            page.goto(test_url)
            page.wait_for_load_state("networkidle")
            
            # 等待内容加载(使用正确的选择器)
            page.wait_for_selector(".basic-info", timeout=10000)
            
            # 提取标准号
            std_code = extract_field_value(page, "标准号")
            logger.info(f"标准号: {std_code}")
            
            # 提取基础信息
            logger.info("\n基础信息:")
            fields = [
                "发布日期",
                "实施日期",
                "制修订",
                "代替标准",
                "中国标准分类号",
                "国际标准分类号",
                "批准发布部门",
                "行业分类",
                "标准类别",
            ]
            
            for field in fields:
                value = extract_field_value(page, field)
                logger.info(f"  {field}: {value}")
            
            # 提取备案信息
            logger.info("\n备案信息:")
            backup_fields = ["备案号", "备案日期"]
            for field in backup_fields:
                value = extract_field_value(page, field)
                logger.info(f"  {field}: {value}")
            
            # 提取起草信息
            logger.info("\n起草信息:")
            draft_fields = ["起草单位", "起草人"]
            for field in draft_fields:
                value = extract_field_value(page, field)
                logger.info(f"  {field}: {value}")
            
            # 截图
            screenshot_path = "test_detail_page.png"
            page.screenshot(path=screenshot_path, full_page=True)
            logger.info(f"\n页面截图已保存: {screenshot_path}")
            
            logger.info("\n测试完成!")
            
        except Exception as e:
            logger.error(f"测试失败: {e}", exc_info=True)
            
        finally:
            browser.close()

def extract_field_value(page, field_name: str) -> str:
    """
    提取字段值
    
    Args:
        page: Playwright页面对象
        field_name: 字段名称
        
    Returns:
        字段值
    """
    try:
        # 方法1: 通过dt/dd结构查找(基础信息区域)
        result = page.evaluate(f"""
            () => {{
                // 查找所有dt元素
                const dts = Array.from(document.querySelectorAll('dt.basicInfo-item.name'));
                const dt = dts.find(el => el.textContent.trim() === '{field_name}');
                
                if (dt && dt.nextElementSibling) {{
                    return dt.nextElementSibling.textContent.trim();
                }}
                
                // 方法2: 查找包含字段名的p标签(备案信息区域)
                const paragraphs = Array.from(document.querySelectorAll('p'));
                for (const p of paragraphs) {{
                    const text = p.textContent;
                    if (text.includes('{field_name}')) {{
                        // 提取冒号后的内容
                        const match = text.match(/{field_name}[:\\s：]+(.+)/);
                        if (match) {{
                            return match[1].trim();
                        }}
                    }}
                }}
                
                return '';
            }}
        """)
        
        return clean_text(str(result))
        
    except Exception as e:
        logger.debug(f"提取字段 {field_name} 失败: {e}")
        return ""

if __name__ == "__main__":
    test_detail_page()

"""
行业标准爬虫 - 主模块
"""
import asyncio
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from playwright.sync_api import sync_playwright, Page, Browser, Download
from utils import (
    setup_logger, 
    random_delay, 
    format_pdf_filename, 
    extract_hash_id_from_url,
    clean_text,
    ensure_dir
)
from config import (
    FILTER_CONFIG,
    DELAY_CONFIG,
    BROWSER_CONFIG,
    LIST_URL,
    DETAIL_URL_TEMPLATE,
    ONLINE_URL_TEMPLATE,
    PDF_DIR,
    PAGE_SIZE,
    CAPTCHA_CONFIG,
)
from captcha_solver import CaptchaSolver
from data_processor import DataProcessor

logger = setup_logger("scraper")

class IndustryStandardScraper:
    """行业标准爬虫"""
    
    def __init__(self):
        """初始化爬虫"""
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.data_processor = DataProcessor()
        self.captcha_solver = CaptchaSolver(use_manual=CAPTCHA_CONFIG["use_manual"])
        
        # 确保输出目录存在
        ensure_dir(PDF_DIR)
    
    def start_browser(self) -> None:
        """启动浏览器"""
        logger.info("正在启动浏览器...")
        
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=BROWSER_CONFIG["headless"]
        )
        
        context = self.browser.new_context(
            viewport=BROWSER_CONFIG["viewport"],
            user_agent=None,  # 使用默认User-Agent
        )
        
        self.page = context.new_page()
        self.page.set_default_timeout(BROWSER_CONFIG["timeout"])
        
        logger.info("浏览器启动成功")
    
    def close_browser(self) -> None:
        """关闭浏览器"""
        if self.page:
            self.page.close()
        if self.browser:
            self.browser.close()
        if hasattr(self, 'playwright'):
            self.playwright.stop()
        
        logger.info("浏览器已关闭")
    
    def apply_filters(self) -> bool:
        """
        应用筛选条件
        
        Returns:
            是否应用成功
        """
        try:
            # 等待页面加载完成
            self.page.wait_for_load_state("networkidle")
            
            # 应用部委筛选
            if FILTER_CONFIG.get("department"):
                dept = FILTER_CONFIG["department"]
                logger.info(f"应用部委筛选: {dept}")
                
                # 优先尝试通过 onclick 代码查找 (更准确)
                dept_link = self.page.query_selector(f"[onclick*=\"searchByDept('{dept}')\"]")
                
                # 如果没找到，尝试通过文本查找
                if not dept_link:
                    dept_link = self.page.query_selector(f"text={dept}")
                
                if dept_link:
                    dept_link.click()
                    self.page.wait_for_timeout(2000)
                    logger.info(f"已选择部委: {dept}")
                else:
                    logger.warning(f"未找到部委: {dept} (尝试了代码和文本匹配)")
            
            # 应用行业代码筛选
            if FILTER_CONFIG.get("industry_code"):
                code = FILTER_CONFIG["industry_code"]
                logger.info(f"应用行业代码筛选: {code}")
                
                # 优先尝试通过 onclick 代码查找
                # 行业代码的 onclick 通常是 searchByIndustry('AQ')
                code_link = self.page.query_selector(f"[onclick*=\"searchByIndustry('{code}')\"]")
                
                if not code_link:
                     # 回退到文本匹配
                     # 尝试2: 使用正则匹配开头的代码 (放宽条件,不强制空格)
                     code_link = self.page.query_selector(f"text=/^{code}/")
                
                if not code_link:
                     # 尝试3: 查找 .industry-code 元素 (最稳健的方式)
                     # 直接点击这个代码元素通常也能触发（事件冒泡）
                     code_link = self.page.query_selector(f".industry-code:text-is('{code}')")

                if code_link:
                    code_link.click()
                    self.page.wait_for_timeout(2000)
                    logger.info(f"已选择行业代码: {code}")
                else:
                    logger.warning(f"未找到行业代码: {code}")
            
            # 应用状态筛选
            if FILTER_CONFIG.get("status"):
                status = FILTER_CONFIG["status"]
                logger.info(f"应用状态筛选: {status}")
                
                # 状态可能有 onclick="searchByStatus('xxx')"
                # 注意: 状态可能传的是中文 "现行" 或代码 "active" (假设)
                # 我们先看文本
                status_link = self.page.query_selector(f"text={status}")
                
                # 如果没找到，尝试代码匹配 (假设 status 也是代码)
                if not status_link:
                     status_link = self.page.query_selector(f"[onclick*=\"searchByStatus('{status}')\"]")
                
                if status_link:
                    status_link.click()
                    self.page.wait_for_timeout(2000)
                    logger.info(f"已选择状态: {status}")
                else:
                    logger.warning(f"未找到状态: {status}")
            
            # 等待列表更新
            self.page.wait_for_timeout(2000)
            
            # 设置每页显示数量
            self.set_page_size()
            
            return True
            
        except Exception as e:
            logger.error(f"应用筛选条件失败: {e}")
            return False

    def set_page_size(self) -> None:
        """设置每页显示数量"""
        try:
            target_size = str(PAGE_SIZE)
            logger.info(f"正在设置每页显示数量为: {target_size}")
            
            # 查找每页显示数量下拉框
            # 页面结构: .pull-right.pagination-detail .dropdown-toggle
            dropdown = self.page.query_selector(".pagination-detail .dropdown-toggle")
            if dropdown:
                dropdown.click()
                self.page.wait_for_timeout(500)
                
                # 选择对应的选项: .dropdown-menu li a (text=100)
                option = self.page.query_selector(f".dropdown-menu li a:text-is('{target_size}')")
                if option:
                    option.click()
                    self.page.wait_for_timeout(2000) # 等待页面刷新
                    logger.info(f"已设置每页显示 {target_size} 条")
                else:
                    logger.warning(f"未找到每页显示 {target_size} 条的选项")
            else:
                logger.warning("未找到每页显示数量下拉框")
                
        except Exception as e:
            logger.error(f"设置每页显示数量失败: {e}")
    
    def get_total_pages(self) -> int:
        """
        获取总页数
        
        Returns:
            总页数
        """
        try:
            # 优先从分页信息中获取总条数 (显示第 x 到第 y 条记录，总共 z 条记录)
            info_elem = self.page.query_selector(".pagination-info")
            if info_elem:
                text = info_elem.inner_text()
                import re
                match = re.search(r'总共\s*(\d+)\s*条', text)
                if match:
                    total_records = int(match.group(1))
                    import math
                    # 总是使用实际设置的 PAGE_SIZE (默认为15,除非成功设置了100)
                    # 这里假设 set_page_size 已经成功执行，或者我们需要重新获取当前的 page size
                    # 为简单起见，我们使用配置的 PAGE_SIZE，因为我们已经尝试设置它了
                    total_pages = math.ceil(total_records / PAGE_SIZE)
                    logger.info(f"总记录数: {total_records},每页: {PAGE_SIZE}, 总页数: {total_pages}")
                    return total_pages

            # 备用方法: 查找分页组件
            pagination = self.page.query_selector(".pagination, .el-pagination")
            if not pagination:
                logger.warning("未找到分页组件,假设只有1页")
                return 1
            
            # 尝试获取总页数
            # 方法1: 查找"共X页"文本
            total_text = pagination.inner_text()
            match = re.search(r'共\s*(\d+)\s*页', total_text)
            if match:
                total = int(match.group(1))
                logger.info(f"总页数(从文本): {total}")
                return total
            
            # 方法2: 查找最后一页的页码
            page_numbers = pagination.query_selector_all(".number, .el-pager li, .page-number a")
            if page_numbers:
                # 过滤出数字页码
                pages = []
                for p in page_numbers:
                    txt = p.inner_text().strip()
                    if txt.isdigit():
                        pages.append(int(txt))
                
                if pages:
                    last_page = max(pages)
                    logger.info(f"总页数(从页码): {last_page}")
                    return last_page
            
            logger.warning("无法获取总页数,假设只有1页")
            return 1
            
        except Exception as e:
            logger.error(f"获取总页数失败: {e}")
            return 1
    
    def scrape_list_page(self, page_num: int = 1) -> List[Dict]:
        """
        爬取列表页
        
        Args:
            page_num: 页码
            
        Returns:
            标准列表
        """
        standards = []
        
        try:
            logger.info(f"正在爬取第 {page_num} 页...")
            
            # 如果不是第一页,需要翻页
            if page_num > 1:
                self.goto_page(page_num)
            
            # 等待表格加载
            self.page.wait_for_selector("table#hbtable tbody tr", timeout=10000)
            
            # 获取所有行 (更精确的选择器，排除表头)
            rows = self.page.query_selector_all("table#hbtable tbody tr")
            logger.info(f"找到 {len(rows)} 条记录")
            
            for idx, row in enumerate(rows, 1):
                try:
                    # 提取单元格
                    cells = row.query_selector_all("td")
                    
                    if len(cells) < 4:
                        # 可能是空行或加载行
                        continue
                    
                    # 提取数据
                    std_code = clean_text(cells[1].inner_text())  # 标准号
                    std_name_cell = cells[2].query_selector("a")  # 标准名称(带链接)
                    std_name = clean_text(std_name_cell.inner_text()) if std_name_cell else clean_text(cells[2].inner_text())
                    industry = clean_text(cells[3].inner_text())  # 行业领域
                    status = clean_text(cells[4].inner_text()) if len(cells) > 4 else ""  # 状态
                    
                    # 提取详情页链接
                    detail_link = std_name_cell.get_attribute("href") if std_name_cell else ""
                    if detail_link and not detail_link.startswith("http"):
                        detail_link = f"https://hbba.sacinfo.org.cn{detail_link}"
                    
                    # 提取hash_id
                    hash_id = extract_hash_id_from_url(detail_link)
                    
                    standard = {
                        "序号": (page_num - 1) * PAGE_SIZE + idx,
                        "标准号": std_code,
                        "标准名称": std_name,
                        "行业领域": industry,
                        "状态": status,
                        "详情页链接": detail_link,
                        "hash_id": hash_id,
                    }
                    
                    standards.append(standard)
                    logger.debug(f"已提取: {std_code} - {std_name}")
                    
                except Exception as e:
                    logger.error(f"提取第 {idx} 行数据失败: {e}")
                    continue
            
            logger.info(f"第 {page_num} 页爬取完成,共 {len(standards)} 条")
            
        except Exception as e:
            logger.error(f"爬取第 {page_num} 页失败: {e}")
        
        return standards
    
    def goto_page(self, page_num: int) -> bool:
        """
        跳转到指定页
        
        Args:
            page_num: 页码
            
        Returns:
            是否跳转成功
        """
        try:
            # 等待翻页控件可见
            # bootstrap table 翻页: .pagination .page-number a (text) 或者是 "下一页" 按钮
            
            # 1. 尝试直接点击页码
            # 注意: 如果页码被省略(如 ...),可能需要先点附近的页码或点下一页
            page_link = self.page.query_selector(f".pagination li.page-number a:text-is('{page_num}')")
            if page_link:
                page_link.click()
                self.page.wait_for_timeout(2000)
                logger.info(f"已跳转到第 {page_num} 页 (直接点击)")
                return True

            # 2. 如果没有直接的页码按钮，尝试逐页点击"下一页"直到到达目标页
            # 这通常发生在直接跳转失败时。但更简单的逻辑是: 如果是顺序爬取，总是点"下一页"
            
            # 查找当前活动页
            active_page_elem = self.page.query_selector(".pagination li.page-number.active a")
            current_page = int(active_page_elem.inner_text()) if active_page_elem else 0
            
            if current_page < page_num:
                # 需要往后翻
                next_btn = self.page.query_selector(".pagination li.page-next a")
                if next_btn:
                    next_btn.click()
                    self.page.wait_for_timeout(2000)
                    logger.info(f"已点击下一页")
                    return True
            
            logger.warning(f"无法跳转到第 {page_num} 页")
            return False
            
        except Exception as e:
            logger.error(f"跳转页面失败: {e}")
            return False
    
    def scrape_detail_page(self, detail_url: str) -> Dict:
        """
        爬取详情页
        
        Args:
            detail_url: 详情页URL
            
        Returns:
            详情信息字典
        """
        detail_info = {}
        
        try:
            logger.info(f"正在爬取详情页: {detail_url}")
            
            # 访问详情页
            self.page.goto(detail_url)
            self.page.wait_for_load_state("networkidle")
            
            # 等待内容加载(使用正确的选择器)
            self.page.wait_for_selector(".basic-info", timeout=10000)
            
            # 提取基础信息
            detail_info.update(self._extract_basic_info())
            
            # 提取备案信息
            detail_info.update(self._extract_record_info())
            
            # 提取起草信息
            detail_info.update(self._extract_draft_info())
            
            logger.info(f"详情页爬取完成")
            
        except Exception as e:
            logger.error(f"爬取详情页失败: {e}")
        
        return detail_info
    
    def _extract_basic_info(self) -> Dict:
        """提取基础信息"""
        info = {}
        
        try:
            # 查找基础信息区域
            basic_section = self.page.query_selector("text=基础信息")
            if not basic_section:
                logger.warning("未找到基础信息区域")
                return info
            
            # 获取父容器
            container = basic_section.evaluate("el => el.closest('.info-section, .detail-section')")
            
            # 提取字段(根据实际页面结构调整)
            fields_map = {
                "发布日期": "发布日期",
                "实施日期": "实施日期",
                "制修订": "制修订",
                "代替标准": "代替标准",
                "中国标准分类号": "CCS分类号",
                "国际标准分类号": "ICS分类号",
                "批准发布部门": "批准发布部门",
                "行业分类": "行业领域",  # 可能与列表页重复
                "标准类别": "标准类别",
            }
            
            for field_name, output_name in fields_map.items():
                value = self._extract_field_value(field_name)
                if value:
                    info[output_name] = value
            
        except Exception as e:
            logger.error(f"提取基础信息失败: {e}")
        
        return info
    
    def _extract_record_info(self) -> Dict:
        """提取备案信息"""
        info = {}
        
        try:
            fields_map = {
                "备案号": "备案号",
                "备案日期": "备案日期",
            }
            
            for field_name, output_name in fields_map.items():
                value = self._extract_field_value(field_name)
                if value:
                    info[output_name] = value
            
        except Exception as e:
            logger.error(f"提取备案信息失败: {e}")
        
        return info
    
    def _extract_draft_info(self) -> Dict:
        """提取起草信息"""
        info = {}
        
        try:
            fields_map = {
                "起草单位": "起草单位",
                "起草人": "起草人",
            }
            
            for field_name, output_name in fields_map.items():
                value = self._extract_field_value(field_name)
                if value:
                    info[output_name] = value
            
        except Exception as e:
            logger.error(f"提取起草信息失败: {e}")
        
        return info
    
    def _extract_field_value(self, field_name: str) -> str:
        """
        提取字段值
        
        Args:
            field_name: 字段名称
            
        Returns:
            字段值
        """
        try:
            # 使用JavaScript提取字段值(支持dt/dd结构和p标签)
            result = self.page.evaluate(f"""
                () => {{
                    // 方法1: 通过dt/dd结构查找(基础信息区域)
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
    

    def download_pdf(self, hash_id: str, std_code: str, std_name: str) -> Tuple[Optional[str], Optional[str]]:
        """
        下载标准PDF
        
        Args:
            hash_id: 标准hash ID
            std_code: 标准代码
            std_name: 标准名称
            
        Returns:
            (下载的文件路径, 备注信息) - 失败时路径为None,备注包含原因
        """
        try:
            logger.info(f"正在下载PDF: {std_code}")
            
            # 构建在线预览URL
            online_url = ONLINE_URL_TEMPLATE.format(hash_id=hash_id)
            
            # 访问在线预览页面
            self.page.goto(online_url)
            self.page.wait_for_timeout(2000)
            
            # 1. 检查是否存在不可下载提示(如: 未公开、采标标准等)
            # 查找提示标题
            tip_header = self.page.query_selector(".tip h3")
            if tip_header:
                header_text = tip_header.inner_text()
                if "未公开" in header_text or "不公开" in header_text:
                    # 获取具体原因(通常在p标签中)
                    reason_elem = self.page.query_selector(".tip p")
                    reason = reason_elem.inner_text().strip() if reason_elem else "未公开(原因未知)"
                    
                    # 简化原因文本
                    if reason == "无":
                        reason = "未公开(无原因)"
                    elif "采标标准" in reason:
                        reason = "未公开(采标标准)"
                        
                    logger.warning(f"无法下载 {std_code}: {reason}")
                    return None, reason
            
            # 2. 正常下载流程: 等待验证码弹窗出现
            try:
                self.page.wait_for_selector("#captcha-input", timeout=5000)
            except Exception:
                # 如果没有验证码框且没有显式提示,可能是其他情况
                logger.warning(f"未找到验证码输入框，也无明确提示: {std_code}")
                # 截图留证
                self.page.screenshot(path=str(Path(OUTPUT_DIR) / f"error_{std_code}.png"))
                return None, "未找到验证码框且无提示"
            
            # 使用验证码识别器下载
            download, error = self.captcha_solver.verify_and_download(
                self.page,
                max_retry=CAPTCHA_CONFIG["retry"]
            )
            
            if not download:
                logger.error(f"下载失败: {error}")
                return None, f"下载失败: {error}"
            
            # 生成文件名
            filename = format_pdf_filename(std_code, std_name)
            filepath = Path(PDF_DIR) / filename
            
            # 保存文件 (关键步骤: 从临时目录移动到目标目录)
            try:
                download.save_as(filepath)
                
                # 验证文件是否有效
                if not filepath.exists():
                    return None, "文件保存失败: 文件不存在"
                
                # 检查文件大小 (小于1KB可能是错误页面)
                file_size = filepath.stat().st_size
                if file_size < 1024:
                    # 读取内容看是否包含错误信息
                    try:
                        with open(filepath, 'rb') as f:
                            content = f.read().decode('utf-8', errors='ignore')
                            if "验证码" in content:
                                return None, "下载失败: 验证码错误(服务器返回HTML)"
                    except:
                        pass
                    
                    # 重命名为HTML以便排查
                    error_path = filepath.with_suffix('.html')
                    filepath.rename(error_path)
                    return None, f"下载文件过小 ({file_size} bytes), 可能不是PDF"
                
                # 检查文件头 (PDF文件通常以 %PDF 开头)
                with open(filepath, 'rb') as f:
                    header = f.read(4)
                    if header != b'%PDF':
                        # 如果不是PDF, 可能是HTML或其他格式
                        error_path = filepath.with_suffix('.unknown')
                        filepath.rename(error_path)
                        return None, f"文件格式错误: 文件头为 {header}, 预期为 %PDF"
                
                logger.info(f"PDF下载成功并保存: {filename} (大小: {file_size/1024:.1f} KB)")
                return str(filepath), None
                
            except Exception as e:
                logger.error(f"保存PDF文件失败: {e}")
                return None, f"保存文件失败: {e}"
            
        except Exception as e:
            logger.error(f"下载PDF出错: {e}")
            return None, f"下载出错: {e}"
    
    def run(self) -> None:
        """运行爬虫"""
        try:
            logger.info("="*60)
            logger.info("行业标准爬虫启动")
            logger.info("="*60)
            
            # 启动浏览器
            self.start_browser()
            
            # 访问列表页
            logger.info(f"正在访问列表页: {LIST_URL}")
            self.page.goto(LIST_URL)
            
            # 应用筛选条件
            self.apply_filters()
            
            # 获取总页数
            total_pages = self.get_total_pages()
            logger.info(f"共 {total_pages} 页数据")
            
            # 爬取所有列表页
            all_standards = []
            for page_num in range(1, total_pages + 1):
                standards = self.scrape_list_page(page_num)
                all_standards.extend(standards)
                
                # 添加到数据处理器
                for std in standards:
                    self.data_processor.add_standard(std)
                
                # 保存检查点
                self.data_processor.save_checkpoint()
                
                # 延迟
                if page_num < total_pages:
                    random_delay(DELAY_CONFIG["list_page"])
            
            logger.info(f"列表页爬取完成,共 {len(all_standards)} 条标准")
            
            # 爬取详情页
            logger.info("开始爬取详情页...")
            for idx, std in enumerate(all_standards, 1):
                logger.info(f"进度: {idx}/{len(all_standards)}")
                
                detail_url = std.get("详情页链接")
                if not detail_url:
                    logger.warning(f"标准 {std.get('标准号')} 没有详情页链接,跳过")
                    continue
                
                # 爬取详情页
                detail_info = self.scrape_detail_page(detail_url)
                
                # 下载PDF
                pdf_path, note = self.download_pdf(
                    std.get("hash_id"), 
                    std.get("标准号"),
                    std.get("标准名称")
                )
                
                if pdf_path:
                    detail_info["PDF文件名"] = pdf_path
                    detail_info["下载状态"] = "成功"
                    detail_info["备注"] = ""
                else:
                    detail_info["下载状态"] = "失败"
                    detail_info["备注"] = note # 记录失败原因(如: 未公开)
                
                # 合并信息
                self.data_processor.merge_detail_info(std.get("标准号"), detail_info)
                
                # 保存检查点
                if idx % 5 == 0:  # 完整爬取时建议更频繁保存
                    self.data_processor.save_checkpoint()
                
                # 延迟
                random_delay(DELAY_CONFIG["download"]) # 使用下载延迟配置
            
            logger.info("详情页爬取完成")
            
            # 导出数据
            logger.info("正在导出数据...")
            self.data_processor.export_to_excel()
            self.data_processor.print_statistics()
            
            logger.info("="*60)
            logger.info("爬虫任务完成!")
            logger.info("="*60)
            
        except KeyboardInterrupt:
            logger.warning("用户中断爬虫")
            self.data_processor.save_checkpoint()
            self.data_processor.export_to_excel()
            
        except Exception as e:
            logger.error(f"爬虫运行失败: {e}", exc_info=True)
            
        finally:
            self.close_browser()

def main():
    """主函数"""
    scraper = IndustryStandardScraper()
    scraper.run()

if __name__ == "__main__":
    main()

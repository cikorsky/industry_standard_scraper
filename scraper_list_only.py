"""
简化版爬虫 - 仅爬取标准清单(不下载PDF)
"""
from scraper import IndustryStandardScraper
from utils import setup_logger, random_delay
from config import DELAY_CONFIG, LIST_URL

logger = setup_logger("scraper_list_only")

class ListOnlyScraper(IndustryStandardScraper):
    """仅爬取清单的爬虫"""
    
    def run(self) -> None:
        """运行爬虫(仅爬取清单)"""
        try:
            logger.info("="*60)
            logger.info("行业标准清单爬虫启动(仅爬取清单)")
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
            
            logger.info(f"列表页爬取完成,共 {len(all_standards)} 条标准")
            
            # (已优化) 仅爬取清单模式不进入详情页
            # 导出数据
            
            # 导出数据
            logger.info("正在导出数据...")
            self.data_processor.export_to_excel()
            self.data_processor.export_to_csv()
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
    scraper = ListOnlyScraper()
    scraper.run()

if __name__ == "__main__":
    main()

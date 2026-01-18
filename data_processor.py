"""
数据处理模块
"""
import pandas as pd
from pathlib import Path
from typing import List, Dict
from utils import setup_logger, ensure_dir
from config import EXCEL_OUTPUT, OUTPUT_DIR

logger = setup_logger("data_processor")

class DataProcessor:
    """数据处理器"""
    
    def __init__(self):
        """初始化数据处理器"""
        self.standards_data = []
        ensure_dir(OUTPUT_DIR)
    
    def add_standard(self, data: Dict) -> None:
        """
        添加标准数据
        
        Args:
            data: 标准数据字典
        """
        self.standards_data.append(data)
        logger.debug(f"已添加标准: {data.get('标准号', 'N/A')}")
    
    def merge_detail_info(self, std_code: str, detail_info: Dict) -> bool:
        """
        合并详情页信息到已有数据
        
        Args:
            std_code: 标准号
            detail_info: 详情页信息
            
        Returns:
            是否合并成功
        """
        for standard in self.standards_data:
            if standard.get("标准号") == std_code:
                standard.update(detail_info)
                logger.debug(f"已合并详情信息: {std_code}")
                return True
        
        logger.warning(f"未找到标准 {std_code},无法合并详情信息")
        return False
    
    def export_to_excel(self, filename: str = None) -> bool:
        """
        导出数据到Excel
        
        Args:
            filename: 输出文件名(可选)
            
        Returns:
            是否导出成功
        """
        if not self.standards_data:
            logger.warning("没有数据可导出")
            return False
        
        try:
            output_file = filename or EXCEL_OUTPUT
            
            # 定义列顺序
            columns = [
                "序号",
                "标准号",
                "标准名称",
                "行业领域",
                "状态",
                "发布日期",
                "实施日期",
                "制修订",
                "代替标准",
                "CCS分类号",
                "ICS分类号",
                "批准发布部门",
                "标准类别",
                "备案号",
                "备案日期",
                "起草单位",
                "起草人",
                "PDF文件名",
                "详情页链接",
                "备注",
            ]
            
            # 创建DataFrame
            df = pd.DataFrame(self.standards_data)
            
            # 确保所有列都存在
            for col in columns:
                if col not in df.columns:
                    df[col] = ""
            
            # 按指定顺序排列列
            df = df[columns]
            
            # 导出到Excel
            df.to_excel(output_file, index=False, engine='openpyxl')
            
            logger.info(f"数据已导出到: {output_file}")
            logger.info(f"共导出 {len(df)} 条标准记录")
            
            return True
            
        except Exception as e:
            logger.error(f"导出Excel失败: {e}")
            return False
    
    def export_to_csv(self, filename: str = None) -> bool:
        """
        导出数据到CSV
        
        Args:
            filename: 输出文件名(可选)
            
        Returns:
            是否导出成功
        """
        if not self.standards_data:
            logger.warning("没有数据可导出")
            return False
        
        try:
            output_file = filename or EXCEL_OUTPUT.replace('.xlsx', '.csv')
            
            df = pd.DataFrame(self.standards_data)
            df.to_csv(output_file, index=False, encoding='utf-8-sig')
            
            logger.info(f"数据已导出到: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"导出CSV失败: {e}")
            return False
    
    def save_checkpoint(self, checkpoint_file: str = None) -> bool:
        """
        保存检查点(用于断点续爬)
        
        Args:
            checkpoint_file: 检查点文件路径
            
        Returns:
            是否保存成功
        """
        try:
            checkpoint_file = checkpoint_file or Path(OUTPUT_DIR) / "checkpoint.xlsx"
            
            if self.standards_data:
                df = pd.DataFrame(self.standards_data)
                df.to_excel(checkpoint_file, index=False, engine='openpyxl')
                logger.info(f"检查点已保存: {checkpoint_file}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"保存检查点失败: {e}")
            return False
    
    def load_checkpoint(self, checkpoint_file: str = None) -> bool:
        """
        加载检查点
        
        Args:
            checkpoint_file: 检查点文件路径
            
        Returns:
            是否加载成功
        """
        try:
            checkpoint_file = checkpoint_file or Path(OUTPUT_DIR) / "checkpoint.xlsx"
            
            if not Path(checkpoint_file).exists():
                logger.info("检查点文件不存在")
                return False
            
            df = pd.read_excel(checkpoint_file, engine='openpyxl')
            self.standards_data = df.to_dict('records')
            
            logger.info(f"已加载检查点: {checkpoint_file}")
            logger.info(f"已加载 {len(self.standards_data)} 条记录")
            
            return True
            
        except Exception as e:
            logger.error(f"加载检查点失败: {e}")
            return False
    
    def get_downloaded_standards(self) -> List[str]:
        """
        获取已下载PDF的标准号列表
        
        Returns:
            标准号列表
        """
        downloaded = []
        for standard in self.standards_data:
            if standard.get("PDF文件名"):
                downloaded.append(standard.get("标准号"))
        
        return downloaded
    
    def get_statistics(self) -> Dict:
        """
        获取统计信息
        
        Returns:
            统计信息字典
        """
        total = len(self.standards_data)
        
        if total == 0:
            return {
                "总数": 0,
                "已下载PDF": 0,
                "未下载PDF": 0,
            }
        
        downloaded = len([s for s in self.standards_data if s.get("PDF文件名")])
        
        # 统计状态分布
        status_count = {}
        for standard in self.standards_data:
            status = standard.get("状态", "未知")
            status_count[status] = status_count.get(status, 0) + 1
        
        return {
            "总数": total,
            "已下载PDF": downloaded,
            "未下载PDF": total - downloaded,
            "状态分布": status_count,
        }
    
    def print_statistics(self) -> None:
        """打印统计信息"""
        stats = self.get_statistics()
        
        print("\n" + "="*50)
        print("数据统计")
        print("="*50)
        print(f"标准总数: {stats['总数']}")
        print(f"已下载PDF: {stats['已下载PDF']}")
        print(f"未下载PDF: {stats['未下载PDF']}")
        
        if "状态分布" in stats:
            print("\n状态分布:")
            for status, count in stats["状态分布"].items():
                print(f"  {status}: {count}")
        
        print("="*50 + "\n")

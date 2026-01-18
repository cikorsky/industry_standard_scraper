import sys
import os
# 设置 Playwright 使用系统全局浏览器缓存 (避免打包后的路径错误)
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "0"

import logging
import time
from pathlib import Path
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLabel, QComboBox, QPushButton, 
                               QTextEdit, QGroupBox, QFormLayout, QMessageBox, 
                               QStyleFactory, QRadioButton, QButtonGroup, QCheckBox, 
                               QSpinBox, QDoubleSpinBox)
from PySide6.QtCore import QThread, Signal, Slot, Qt, QObject
from PySide6.QtGui import QFont, QIcon, QDesktopServices
from PySide6.QtCore import QThread, Signal, Slot, Qt, QObject, QUrl

import config
from scraper import IndustryStandardScraper
from scraper_list_only import ListOnlyScraper as ListScraper
from constants import DEPARTMENTS, INDUSTRIES, STATUSES, RECORD_DATES

# ==========================================
# 日志处理
# ==========================================
class SignaledLogHandler(logging.Handler, QObject):
    log_signal = Signal(str)

    def __init__(self):
        logging.Handler.__init__(self)
        QObject.__init__(self)

    def emit(self, record):
        msg = self.format(record)
        self.log_signal.emit(msg)

# ==========================================
# 爬虫工作线程
# ==========================================
class ScraperWorker(QThread):
    finished_signal = Signal(bool, str)
    
    def __init__(self, mode, filter_config, advanced_config):
        super().__init__()
        self.mode = mode
        self.filter_config = filter_config
        self.advanced_config = advanced_config
        self._is_running = True

    def run(self):
        try:
            # 1. 动态更新全局配置
            config.FILTER_CONFIG.update(self.filter_config)
            
            # 更新高级配置
            # 浏览器配置
            if "headless" in self.advanced_config:
                config.BROWSER_CONFIG["headless"] = self.advanced_config["headless"]
            
            # OCR配置
            if "ocr_engine" in self.advanced_config:
                config.CAPTCHA_CONFIG["ocr_engine"] = self.advanced_config["ocr_engine"]
                
            # 延迟配置
            if "list_delay" in self.advanced_config:
                # 假设用户设置的是最小延迟，最大延迟+1秒
                min_d = self.advanced_config["list_delay"]
                config.DELAY_CONFIG["list_page"] = (min_d, min_d + 1.0)
                
            if "download_delay" in self.advanced_config:
                min_d = self.advanced_config["download_delay"]
                config.DELAY_CONFIG["download"] = (min_d, min_d + 2.0)
            
            # 2. 选择爬虫类
            if self.mode == 'list':
                crawler = ListScraper()
            else:
                crawler = IndustryStandardScraper()
            
            # 3. 运行爬虫
            crawler.run()
            
            if self._is_running:
                self.finished_signal.emit(True, "爬取任务完成！")
                
        except Exception as e:
            if self._is_running:
                self.finished_signal.emit(False, str(e))
                
    def stop(self):
        self._is_running = False
        self.terminate()

# ==========================================
# 主窗口
# ==========================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("行业标准爬虫 GUI")
        self.resize(1100, 750)
        self.init_ui()
        self.init_logger()
        self.worker = None

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # ==================== 左侧设置区 ====================
        left_scroll = QWidget() # 使用Widget作为容器
        left_layout = QVBoxLayout(left_scroll)
        left_scroll.setFixedWidth(380)
        
        # 1. 筛选条件组
        filter_group = QGroupBox("筛选条件")
        filter_layout = QVBoxLayout()
        
        # 互斥单选按钮
        radio_layout = QHBoxLayout()
        self.rb_dept = QRadioButton("按部委筛选")
        self.rb_industry = QRadioButton("按行业筛选")
        self.rb_dept.setChecked(True) # 默认按部委
        
        # 分组以互斥
        self.filter_bg = QButtonGroup()
        self.filter_bg.addButton(self.rb_dept)
        self.filter_bg.addButton(self.rb_industry)
        
        radio_layout.addWidget(self.rb_dept)
        radio_layout.addWidget(self.rb_industry)
        filter_layout.addLayout(radio_layout)
        
        # 选择表单
        form_layout = QFormLayout()
        
        # 部委下拉
        self.dept_combo = QComboBox()
        for name, code in DEPARTMENTS:
            value = name if code is not None else None
            self.dept_combo.addItem(name, value)
        self.dept_combo.setCurrentText("应急管理部")
        form_layout.addRow("选择部委:", self.dept_combo)
        
        # 行业下拉
        self.industry_combo = QComboBox()
        for name, code in INDUSTRIES:
            self.industry_combo.addItem(name, code)
        self.industry_combo.setCurrentText("AQ - 安全生产")
        self.industry_combo.setEnabled(False) # 初始禁用
        form_layout.addRow("选择行业:", self.industry_combo)
        
        # 状态下拉
        self.status_combo = QComboBox()
        for name, code in STATUSES:
            self.status_combo.addItem(name, code)
        self.status_combo.setCurrentText("现行")
        form_layout.addRow("标准状态:", self.status_combo)
        
        filter_layout.addLayout(form_layout)
        filter_group.setLayout(filter_layout)
        left_layout.addWidget(filter_group)
        
        # 绑定互斥事件
        self.rb_dept.toggled.connect(self.on_filter_mode_changed)
        
        # 2. 运行模式组
        mode_group = QGroupBox("运行模式")
        mode_layout = QVBoxLayout()
        self.mode_combo = QComboBox()
        self.mode_combo.addItem("📋 仅爬取清单 (极快, 无PDF)", 'list')
        self.mode_combo.addItem("📥 完整爬取 (含详情 + PDF下载)", 'full')
        mode_layout.addWidget(self.mode_combo)
        mode_group.setLayout(mode_layout)
        left_layout.addWidget(mode_group)
        
        # 3. 高级设置 (默认折叠/使用CheckBox控制开启)
        self.adv_group = QGroupBox("高级选项")
        self.adv_group.setCheckable(True)
        self.adv_group.setChecked(False) # 默认不展开
        
        adv_layout = QFormLayout()
        
        # 浏览器显示
        self.chk_browser = QCheckBox("显示浏览器窗口 (推荐调试用)")
        self.chk_browser.setChecked(True)
        adv_layout.addRow(self.chk_browser)
        
        # OCR引擎
        self.ocr_combo = QComboBox()
        self.ocr_combo.addItem("ddddocr (推荐, 100%成功率)", "ddddocr")
        self.ocr_combo.addItem("EasyOCR (较慢)", "easyocr")
        self.ocr_combo.addItem("Tesseract (不推荐)", "tesseract")
        adv_layout.addRow("验证码引擎:", self.ocr_combo)
        
        # 延迟设置
        self.spin_list_delay = QDoubleSpinBox()
        self.spin_list_delay.setRange(0.5, 10.0)
        self.spin_list_delay.setValue(1.5)
        self.spin_list_delay.setSuffix(" 秒")
        adv_layout.addRow("翻页最小延迟:", self.spin_list_delay)
        
        self.spin_download_delay = QDoubleSpinBox()
        self.spin_download_delay.setRange(1.0, 20.0)
        self.spin_download_delay.setValue(3.0)
        self.spin_download_delay.setSuffix(" 秒")
        adv_layout.addRow("下载最小延迟:", self.spin_download_delay)
        
        self.adv_group.setLayout(adv_layout)
        left_layout.addWidget(self.adv_group)
        
        # 4. 控制按钮
        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("开始爬取")
        self.start_btn.setMinimumHeight(45)
        self.start_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; font-size: 14px; border-radius: 4px;")
        self.start_btn.clicked.connect(self.start_crawling)
        
        self.stop_btn = QPushButton("停止")
        self.stop_btn.setMinimumHeight(45)
        self.stop_btn.setStyleSheet("background-color: #f44336; color: white; font-weight: bold; font-size: 14px; border-radius: 4px;")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_crawling)
        
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        left_layout.addLayout(btn_layout)
        
        left_layout.addStretch()
        main_layout.addWidget(left_scroll)
        
        # ==================== 右侧日志区 ====================
        main_layout.addWidget(left_scroll)
        
        # ==================== 右侧日志区 ====================
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # 1. 日志显示
        log_label = QLabel("运行日志监控")
        log_label.setFont(QFont("Arial", 10, QFont.Bold))
        right_layout.addWidget(log_label)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e; 
                color: #d4d4d4; 
                font-family: Menlo, Monaco, Consolas, 'Courier New', monospace;
                font-size: 12px;
                border: 1px solid #333;
                border-radius: 4px;
            }
        """)
        right_layout.addWidget(self.log_text)
        
        # 2. 成果管理区 (新增)
        result_group = QGroupBox("爬取成果")
        result_layout = QHBoxLayout()
        
        # 清单
        self.excel_status = QLabel("清单: 未检测")
        self.btn_open_excel = QPushButton("📂 打开清单")
        self.btn_open_excel.clicked.connect(self.open_excel)
        
        # PDF
        self.pdf_status = QLabel("PDF: 0 个")
        self.btn_open_pdf = QPushButton("📂 打开PDF目录")
        self.btn_open_pdf.clicked.connect(self.open_pdf_dir)
        
        # 刷新按钮
        btn_refresh = QPushButton("🔄")
        btn_refresh.setFixedWidth(30)
        btn_refresh.setToolTip("刷新状态")
        btn_refresh.clicked.connect(self.update_result_status)
        
        result_layout.addWidget(self.excel_status)
        result_layout.addWidget(self.btn_open_excel)
        result_layout.addSpacing(15)
        result_layout.addWidget(self.pdf_status)
        result_layout.addWidget(self.btn_open_pdf)
        result_layout.addWidget(btn_refresh)
        result_layout.addStretch()
        
        result_group.setLayout(result_layout)
        right_layout.addWidget(result_group)
        
        main_layout.addWidget(right_panel)
        
        # 初始化状态
        self.update_result_status()

    def update_result_status(self):
        # 检查Excel
        excel_path = Path(config.EXCEL_OUTPUT)
        if excel_path.exists():
            size_kb = excel_path.stat().st_size / 1024
            mod_time = time.strftime("%H:%M", time.localtime(excel_path.stat().st_mtime))
            self.excel_status.setText(f"清单: {size_kb:.1f}KB ({mod_time})")
            self.btn_open_excel.setEnabled(True)
        else:
            self.excel_status.setText("清单: 未找到")
            self.btn_open_excel.setEnabled(False)
            
        # 检查PDF
        pdf_dir = Path(config.PDF_DIR)
        if pdf_dir.exists():
            count = len(list(pdf_dir.glob("*.pdf")))
            self.pdf_status.setText(f"PDF文件: {count} 个")
            self.btn_open_pdf.setEnabled(True)
        else:
            self.pdf_status.setText("PDF目录: 未创建")
            self.btn_open_pdf.setEnabled(False)

    def open_excel(self):
        url = QUrl.fromLocalFile(config.EXCEL_OUTPUT)
        QDesktopServices.openUrl(url)

    def open_pdf_dir(self):
        url = QUrl.fromLocalFile(config.PDF_DIR)
        QDesktopServices.openUrl(url)

    def on_filter_mode_changed(self):
        is_dept_mode = self.rb_dept.isChecked()
        self.dept_combo.setEnabled(is_dept_mode)
        self.industry_combo.setEnabled(not is_dept_mode)
        
        # 视觉反馈
        if is_dept_mode:
            self.dept_combo.setStyleSheet("background-color: #fff;")
            self.industry_combo.setStyleSheet("background-color: #f0f0f0; color: #999;")
        else:
            self.dept_combo.setStyleSheet("background-color: #f0f0f0; color: #999;")
            self.industry_combo.setStyleSheet("background-color: #fff;")

    def init_logger(self):
        self.log_handler = SignaledLogHandler()
        self.log_handler.log_signal.connect(self.append_log)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')
        self.log_handler.setFormatter(formatter)
        logging.getLogger().addHandler(self.log_handler)
        logging.getLogger().setLevel(logging.INFO)

    @Slot(str)
    def append_log(self, msg):
        self.log_text.append(msg)
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())

    def start_crawling(self):
        # 1. 获取筛选条件
        dept_code = None
        industry_code = None
        
        # 根据选中模式取值
        if self.rb_dept.isChecked():
            dept_code = self.dept_combo.currentData()
        else:
            industry_code = self.industry_combo.currentData()
            
        status_code = self.status_combo.currentData()
        mode = self.mode_combo.currentData()
        
        filter_config = {
            "department": dept_code,
            "industry_code": industry_code,
            "status": status_code
        }
        
        # 2. 获取高级配置
        advanced_config = {}
        if self.adv_group.isChecked():
            advanced_config["headless"] = not self.chk_browser.isChecked() # check=显示 -> headless=False
            advanced_config["ocr_engine"] = self.ocr_combo.currentData()
            advanced_config["list_delay"] = self.spin_list_delay.value()
            advanced_config["download_delay"] = self.spin_download_delay.value()
        else:
            # 默认配置
            advanced_config["headless"] = False # 默认显示浏览器
        
        # 3. UI 冻结
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.adv_group.setEnabled(False)
        self.dept_combo.setEnabled(False)
        self.industry_combo.setEnabled(False)
        self.status_combo.setEnabled(False)
        self.rb_dept.setEnabled(False)
        self.rb_industry.setEnabled(False)
        
        self.log_text.clear()
        target_info = f"部委: {self.dept_combo.currentText()}" if self.rb_dept.isChecked() \
                      else f"行业: {self.industry_combo.currentText()}"
        self.log_text.append(f">>> 启动任务 | {target_info} | 模式: {self.mode_combo.currentText()}")
        
        # 4. 启动线程
        self.worker = ScraperWorker(mode, filter_config, advanced_config)
        self.worker.finished_signal.connect(self.on_finished)
        self.worker.start()

    def stop_crawling(self):
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(self, '确认停止', 
                                         "确定要强制停止爬取任务吗？", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.worker.stop()
                self.log_text.append("!!! 任务已强制停止 !!!")
                self.reset_ui()

    @Slot(bool, str)
    def on_finished(self, success, message):
        self.update_result_status()
        if success:
            QMessageBox.information(self, "完成", message)
        else:
            QMessageBox.critical(self, "错误", f"任务失败:\n{message}")
        self.reset_ui()

    def reset_ui(self):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.adv_group.setEnabled(True)
        self.status_combo.setEnabled(True)
        self.rb_dept.setEnabled(True)
        self.rb_industry.setEnabled(True)
        self.mode_combo.setEnabled(True)
        
        # 恢复互斥状态
        self.on_filter_mode_changed()

def main():
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("Fusion"))
    
    # 设置通用字体
    font = QFont("Segoe UI", 10)
    if sys.platform == "darwin": # macOS
        font = QFont(".AppleSystemUIFont", 12)
    app.setFont(font)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

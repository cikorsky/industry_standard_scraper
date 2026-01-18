#!/bin/bash
# 行业标准爬虫 - 演示脚本

echo "================================"
echo "行业标准信息爬虫 - 演示脚本"
echo "================================"
echo ""

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在,请先运行:"
    echo "   python3 -m venv venv"
    echo "   source venv/bin/activate"
    echo "   pip install -r requirements.txt"
    echo "   playwright install chromium"
    exit 1
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境 (Python 3.13 for ddddocr)..."
if [ -d "venv_py313" ]; then
    source venv_py313/bin/activate
else
    source venv/bin/activate
fi

# 显示菜单
echo ""
echo "请选择运行模式:"
echo "1. 测试单个详情页(推荐首次使用)"
echo "2. 测试验证码识别(NEW!)"
echo "3. 爬取清单(仅基础信息,极快)"
echo "4. 完整爬取(含详情+PDF下载,较慢)"
echo "5. 查看配置"
echo "6. 查看日志"
echo "7. 退出"
echo ""

read -p "请输入选项(1-7): " choice

case $choice in
    1)
        echo ""
        echo "🧪 运行测试脚本..."
        python test_detail_page.py
        echo ""
        echo "✅ 测试完成!截图已保存到: test_detail_page.png"
        ;;
    2)
        echo ""
        echo "🔍 测试验证码识别..."
        echo "请选择OCR引擎:"
        echo "1. ddddocr (强烈推荐 - 成功率100%)"
        echo "2. EasyOCR (备选 - 成功率~40%)"
        echo "3. Tesseract (传统 - 成功率较低)"
        echo "4. 人工输入 (保底)"
        read -p "请选择(1-4): " ocr_choice
        
        case $ocr_choice in
            1) ocr_engine="ddddocr" ;;
            2) ocr_engine="easyocr" ;;
            3) ocr_engine="tesseract" ;;
            4) ocr_engine="manual" ;;
            *) ocr_engine="ddddocr" ;;
        esac
        
        echo ""
        echo "使用OCR引擎: $ocr_engine"
        python test_captcha.py $ocr_engine
        echo ""
        echo "✅ 测试完成!查看日志了解识别成功率"
        ;;
    3)
        echo ""
        echo "📋 开始爬取标准清单..."
        echo "⚠️  注意:这将仅爬取列表页的基础信息(无详情,无PDF)"
        read -p "确认继续?(y/n): " confirm
        if [ "$confirm" = "y" ]; then
            python scraper_list_only.py
            echo ""
            echo "✅ 爬取完成!结果已保存到: output/standards.xlsx"
        fi
        ;;
    4)
        echo ""
        echo "📥 开始完整爬取(包含PDF下载)..."
        echo "⚠️  注意:将使用配置文件中设置的OCR引擎"
        read -p "确认继续?(y/n): " confirm
        if [ "$confirm" = "y" ]; then
            python scraper.py
            echo ""
            echo "✅ 爬取完成!"
            echo "   - 标准清单: output/standards.xlsx"
            echo "   - PDF文件: output/pdfs/"
        fi
        ;;
    5)
        echo ""
        echo "📝 当前配置:"
        echo "-----------------------------------"
        grep -A 10 "CAPTCHA_CONFIG" config.py
        echo "-----------------------------------"
        ;;
    6)
        echo ""
        echo "📄 查看最新日志(按Ctrl+C退出):"
        echo "-----------------------------------"
        tail -f logs/scraper.log
        ;;
    7)
        echo ""
        echo "👋 再见!"
        exit 0
        ;;
    *)
        echo ""
        echo "❌ 无效选项,请重新运行脚本"
        exit 1
        ;;
esac

echo ""
echo "================================"
echo "脚本执行完成"
echo "================================"

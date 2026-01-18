#!/bin/bash
# 使用Python 3.13测试ddddocr

echo "================================"
echo "使用Python 3.13测试ddddocr"
echo "================================"
echo ""

# 激活Python 3.13虚拟环境
source venv_py313/bin/activate

# 显示Python版本
echo "Python版本:"
python --version
echo ""

# 测试ddddocr
echo "测试ddddocr验证码识别..."
python test_captcha.py ddddocr

echo ""
echo "================================"
echo "测试完成"
echo "================================"

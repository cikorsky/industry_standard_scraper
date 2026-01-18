#!/bin/bash
# 进入脚本所在目录
cd "$(dirname "$0")"

# 检查虚拟环境是否存在
if [ ! -d "venv_py313" ]; then
    echo "❌ 错误: 未找到虚拟环境 venv_py313"
    echo "请先运行 ./demo.sh 安装环境"
    exit 1
fi

# 激活环境
source venv_py313/bin/activate

# 运行GUI
echo "🚀 正在启动可视化界面..."
python gui_app.py

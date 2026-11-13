#!/bin/bash
# VulnLab 靶机启动脚本

echo "=========================================="
echo "    VulnLab 模拟靶机启动脚本"
echo "=========================================="

# 切换到靶机目录
cd "$(dirname "$0")"

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 python3"
    exit 1
fi

# 检查Flask
if ! python3 -c "import flask" &> /dev/null; then
    echo "安装 Flask..."
    pip install flask
fi

# 启动靶机
echo ""
echo "靶机地址: http://127.0.0.1:5000"
echo "默认用户: admin / admin123"
echo ""
echo "按 Ctrl+C 停止运行"
echo "=========================================="

python3 app.py

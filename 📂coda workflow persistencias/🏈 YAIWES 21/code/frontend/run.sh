#!/bin/bash
# 前端启动脚本 - 完整的依赖检查和管理

set -e  # 遇到错误立即退出

cd "$(dirname "$0")"

echo "=================================================================================="
echo "🚀 H-Pentest Frontend 启动脚本"
echo "=================================================================================="
echo ""

# 检查Node.js和npm
echo "📋 检查Node.js环境..."
if ! command -v node &> /dev/null; then
    echo "❌ 未找到Node.js，请先安装Node.js 16+"
    echo "   推荐使用: https://nodejs.org/"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo "❌ 未找到npm，请确认Node.js安装完整"
    exit 1
fi

NODE_VERSION=$(node -v)
NPM_VERSION=$(npm -v)
echo "   Node.js版本: $NODE_VERSION"
echo "   npm版本: $NPM_VERSION"

# 检查Node.js版本
NODE_MAJOR=$(node -v | cut -d'.' -f1 | sed 's/v//')
if [ "$NODE_MAJOR" -lt 16 ]; then
    echo "   ⚠️  Node.js版本过低，推荐使用16或更高版本"
fi

echo "   ✅ Node.js环境正常"
echo ""

# 检查并安装依赖
echo "📦 检查npm依赖..."
if [ ! -d "node_modules" ]; then
    echo "   📥 首次运行，安装所有依赖..."
    echo "   使用镜像: https://registry.npmmirror.com"
    echo ""
    
    npm install --registry=https://registry.npmmirror.com
    
    if [ $? -ne 0 ]; then
        echo "   ❌ 依赖安装失败"
        echo "   💡 尝试: rm -rf node_modules package-lock.json && npm install"
        exit 1
    fi
    
    echo ""
    echo "   ✅ 依赖安装完成"
elif [ "package.json" -nt "node_modules" ]; then
    echo "   🔄 检测到package.json更新，重新安装依赖..."
    echo ""
    
    npm install --registry=https://registry.npmmirror.com
    
    if [ $? -ne 0 ]; then
        echo "   ❌ 依赖更新失败"
        exit 1
    fi
    
    echo ""
    echo "   ✅ 依赖更新完成"
else
    echo "   ✅ 依赖已就绪"
    
    # 检查关键依赖是否完整
    echo "   🔍 验证关键依赖..."
    MISSING_DEPS=0
    
    for pkg in "vue" "element-plus" "pinia" "vue-router" "axios" "vite"; do
        if [ ! -d "node_modules/$pkg" ]; then
            echo "      ⚠️  缺少: $pkg"
            MISSING_DEPS=1
        fi
    done
    
    if [ $MISSING_DEPS -eq 1 ]; then
        echo "   🔄 检测到缺失依赖，重新安装..."
        npm install --registry=https://registry.npmmirror.com
        
        if [ $? -ne 0 ]; then
            echo "   ❌ 依赖安装失败"
            exit 1
        fi
    else
        echo "   ✅ 关键依赖完整"
    fi
fi

echo ""

# 检查端口占用
echo "🔍 检查端口占用..."
if lsof -Pi :5173 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "   ⚠️  端口5173已被占用"
    read -p "   是否停止现有进程并重启? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "   🔄 停止现有进程..."
        pkill -f "vite" 2>/dev/null || true
        sleep 2
    else
        echo "   ❌ 启动取消"
        exit 0
    fi
fi

echo "   ✅ 端口5173可用"
echo ""

echo "=================================================================================="
echo "🌐 启动Vite开发服务器"
echo "=================================================================================="
echo ""
echo "   📍 前端地址:    http://localhost:5173"
echo "   🔌 后端API:     http://localhost:8000"
echo "   🔥 热重载:      已启用"
echo ""
echo "   💡 提示: 按 Ctrl+C 停止服务器"
echo "=================================================================================="
echo ""

# 启动开发服务器
npm run dev

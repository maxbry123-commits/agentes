#!/bin/bash
# H-Pentest 2.0 清理脚本
# 清理临时文件、缓存和日志，但保留数据库和配置

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "🧹 =========================================="
echo "   H-Pentest 2.0 清理脚本"
echo "=========================================="
echo ""

echo -e "${YELLOW}⚠️  此操作将清理以下内容：${NC}"
echo ""
echo "  1. 🔑 config.json 中的 API Keys (替换为占位符)"
echo "  2. 🔧 .env 文件中的敏感信息"
echo "  3. 📦 Python 缓存文件 (__pycache__, *.pyc, *.pyo)"
echo "  4. 📦 Node.js 缓存 (.vite, dist)"
echo "  5. 📊 日志文件 (logs/*.json)"
echo "  6. 🔧 临时文件 (temp/*, *.tmp)"
echo "  7. 🧠 向量 JSON 缓存 (cache/*.json)"
echo "  8. 🧪 测试缓存 (.pytest_cache, .coverage)"
echo ""
echo -e "${GREEN}✅ 保留的内容：${NC}"
echo "  - config.json (配置文件结构，API Key被清空)"
echo "  - .env (文件结构保留，敏感信息被清空)"
echo "  - data/h-pentest.db (数据库)"
echo "  - knowledge/ (知识库)"
echo "  - Docker 容器和镜像"
echo ""

read -p "确认清理？(y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}❌ 已取消清理${NC}"
    exit 0
fi

echo ""
echo -e "${BLUE}🚀 开始清理...${NC}"
echo ""

# 1. 清理 config.json 中的 API Keys
echo -e "${YELLOW}[1/8] 🔑 清理 config.json 中的 API Keys...${NC}"
if [ -f "config.json" ]; then
    # 使用 sed 替换 API Keys（支持多种格式）
    sed -i 's/"api_key": "[^"]*"/"api_key": "your-api-key-here"/g' config.json

    echo -e "${GREEN}  ✅ API Keys 已清理${NC}"
    echo -e "${BLUE}  ℹ️  请重新配置 config.json 中的 API Keys${NC}"
else
    echo -e "${YELLOW}  ⚠️  未找到 config.json${NC}"
fi

# 2. 清理 .env 文件
echo ""
echo -e "${YELLOW}[2/8] 🔧 清理 .env 文件...${NC}"
if [ -f ".env" ]; then
    # 清理敏感信息但保留结构
    sed -i 's/=.*/=/g' .env
    echo -e "${GREEN}  ✅ .env 文件已清理${NC}"
else
    echo -e "${BLUE}  ℹ️  未找到 .env 文件${NC}"
fi

# 3. 清理 Python 缓存
echo ""
echo -e "${YELLOW}[3/8] 🐍 清理 Python 缓存文件...${NC}"
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
find . -type f -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
echo -e "${GREEN}  ✅ Python 缓存已清理${NC}"

# 4. 清理 Node.js 缓存（保留 node_modules）
echo ""
echo -e "${YELLOW}[4/8] 📦 清理 Node.js 构建缓存...${NC}"
if [ -d "frontend/.vite" ]; then
    rm -rf frontend/.vite
    echo -e "${GREEN}  ✅ Vite 缓存已清理${NC}"
fi

if [ -d "frontend/dist" ]; then
    rm -rf frontend/dist
    echo -e "${GREEN}  ✅ 前端构建产物已清理${NC}"
fi

# 5. 清理日志文件（只清理 .json 日志，保留目录）
echo ""
echo -e "${YELLOW}[5/8] 📊 清理日志文件...${NC}"
if [ -d "logs" ]; then
    rm -f logs/*.json 2>/dev/null || true
    rm -f logs/*.log 2>/dev/null || true
    echo -e "${GREEN}  ✅ 日志文件已清理${NC}"
else
    echo -e "${BLUE}  ℹ️  logs 目录不存在${NC}"
fi

# 6. 清理临时文件
echo ""
echo -e "${YELLOW}[6/8] 🔧 清理临时文件...${NC}"
if [ -d "temp" ]; then
    rm -rf temp/* 2>/dev/null || true
    echo -e "${GREEN}  ✅ temp/ 目录已清理${NC}"
fi

# 清理根目录临时文件
rm -f *.tmp 2>/dev/null || true
rm -f *.log 2>/dev/null || true
echo -e "${GREEN}  ✅ 临时文件已清理${NC}"

# 7. 清理向量缓存（只清理 .json 文件，保留 .pkl 文件）
echo ""
echo -e "${YELLOW}[7/8] 🧠 清理向量缓存...${NC}"
if [ -d "cache" ]; then
    rm -f cache/*.json 2>/dev/null || true
    echo -e "${GREEN}  ✅ 向量 JSON 缓存已清理${NC}"
else
    echo -e "${BLUE}  ℹ️  cache 目录不存在${NC}"
fi

# 8. 清理测试缓存
echo ""
echo -e "${YELLOW}[8/8] 🧪 清理测试缓存...${NC}"
rm -rf .pytest_cache 2>/dev/null || true
rm -rf .coverage 2>/dev/null || true
rm -rf htmlcov 2>/dev/null || true
rm -rf build dist *.egg-info 2>/dev/null || true
echo -e "${GREEN}  ✅ 测试缓存已清理${NC}"



echo ""
echo "🎉 =========================================="
echo "   清理完成！"
echo "=========================================="
echo ""
echo -e "${GREEN}✅ 已清理：${NC}"
echo "  - config.json 中的 API Keys"
echo "  - .env 文件中的敏感信息"
echo "  - Python 缓存文件"
echo "  - Node.js 构建缓存"
echo "  - 日志文件"
echo "  - 临时文件"
echo "  - 向量 JSON 缓存"
echo "  - 测试缓存"
echo ""
echo -e "${BLUE}📝 保留的内容：${NC}"
echo "  - data/h-pentest.db (数据库)"
echo "  - knowledge/ (知识库)"
echo "  - Docker 容器和镜像"
echo "  - frontend/node_modules"
echo ""
echo -e "${RED}⚠️  重要提示：${NC}"
echo -e "${YELLOW}  1. 请重新配置 config.json 中的 API Keys${NC}"
echo -e "${YELLOW}  2. 请重新配置 .env 文件中的敏感信息${NC}"
echo -e "${YELLOW}  3. 配置完成后运行: docker-compose restart backend${NC}"
echo ""

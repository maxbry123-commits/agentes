#!/bin/bash
# H-Pentest 2.0 快速部署脚本

set -e

echo "🚀 =========================================="
echo "   H-Pentest 2.0 快速部署脚本"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker未安装！请先安装Docker${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose未安装！请先安装Docker Compose${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker环境检查通过${NC}"
echo ""

# 检查配置文件
if [ ! -f "config.json" ]; then
    echo -e "${RED}❌ 未找到 config.json 配置文件！${NC}"
    echo ""
    echo -e "${YELLOW}⚠️  请先配置 config.json 文件${NC}"
    echo ""
    echo "配置说明："
    echo "  1. 修改 config.json 中的 LLM 配置"
    echo "  2. 主要配置项:"
    echo "     - openai.api_key: 你的 API Key"
    echo "     - openai.base_url: API 地址"
    echo "     - openai.model: 主模型名称 (如 GLM-4.6, gpt-4o)"
    echo "     - embedding.api_key: 向量模型 API Key"
    echo ""
    echo "示例："
    echo '  "openai": {'
    echo '    "api_key": "your-api-key-here",'
    echo '    "base_url": "https://api.openai.com/v1",'
    echo '    "model": "gpt-4o"'
    echo '  }'
    echo ""
    exit 1
else
    echo -e "${GREEN}✅ 找到 config.json 配置文件${NC}"
    
    # 提取并显示当前配置（简化版）
    if command -v jq &> /dev/null; then
        echo ""
        echo -e "${BLUE}📋 当前配置：${NC}"
        echo "  模型: $(jq -r '.openai.model' config.json)"
        echo "  API: $(jq -r '.openai.base_url' config.json)"
        echo ""
    fi
    
    echo -e "${YELLOW}💡 提示: 如需修改配置，请编辑 config.json 文件${NC}"
    echo ""
    
    # 🔥 添加确认步骤
    read -p "配置是否已修改完成？(y/n) " -n 1 -r
    echo ""
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        echo -e "${YELLOW}⚠️  请先修改 config.json 配置文件：${NC}"
        echo ""
        echo "  主要配置项："
        echo "  1. openai.api_key - 你的 API Key"
        echo "  2. openai.base_url - API 地址"
        echo "  3. openai.model - 主模型名称"
        echo "  4. embedding.api_key - 向量模型 API Key"
        echo ""
        echo "  编辑命令: vim config.json 或 nano config.json"
        echo ""
        echo -e "${BLUE}修改完成后，请重新运行: ./deploy.sh${NC}"
        echo ""
        exit 0
    fi
fi

echo ""
echo "📦 =========================================="
echo "   开始构建和启动Docker容器"
echo "=========================================="
echo ""

# 创建必要目录
mkdir -p data logs reports temp

# 停止并删除旧容器
echo -e "${BLUE}🧹 清理旧容器...${NC}"
docker-compose down 2>/dev/null || true

# 构建镜像
echo ""
echo -e "${BLUE}🔨 构建Docker镜像（这可能需要几分钟）...${NC}"
docker-compose build

# 启动服务
echo ""
echo -e "${BLUE}🚀 启动服务...${NC}"
docker-compose up -d

# 等待服务启动
echo ""
echo -e "${BLUE}⏳ 等待服务启动...${NC}"
sleep 10

# 检查服务状态
echo ""
echo -e "${BLUE}📊 检查服务状态...${NC}"
docker-compose ps

echo ""
echo "🎉 =========================================="
echo "   部署完成！"
echo "=========================================="
echo ""
echo -e "${GREEN}✅ 后端服务: http://localhost:8000${NC}"
echo -e "${GREEN}✅ 前端服务: http://localhost:5173${NC}"
echo -e "${GREEN}✅ API文档: http://localhost:8000/docs${NC}"
echo ""
echo "📝 常用命令："
echo "  查看日志: docker-compose logs -f"
echo "  停止服务: docker-compose down"
echo "  重启服务: docker-compose restart"
echo "  查看状态: docker-compose ps"
echo ""
echo -e "${YELLOW}⚠️  首次启动可能需要下载Nuclei模板，请稍等...${NC}"
echo ""

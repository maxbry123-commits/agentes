"""
配置管理 API 端点
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import json
from pathlib import Path

router = APIRouter()


class AgentConfigUpdate(BaseModel):
    """Agent配置更新"""
    max_rounds: Optional[int] = None
    timeout: Optional[int] = None
    verbose: Optional[bool] = None
    debug: Optional[bool] = None
    preprocessing_enabled: Optional[bool] = None
    knowledge_base_enabled: Optional[bool] = None
    rerank_enabled: Optional[bool] = None
    search_top_k: Optional[int] = None


class APIConfigUpdate(BaseModel):
    """API配置更新"""
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None


class ToolConfigUpdate(BaseModel):
    """工具配置更新"""
    tool_name: str
    description: Optional[str] = None
    priority: Optional[int] = None
    timeout: Optional[int] = None
    enabled: Optional[bool] = None
    path: Optional[str] = None


# 配置文件路径
CONFIG_DIR = Path("/home/H-pentest/H-pentest/backend/config")


def load_json_config(filename: str) -> Dict[str, Any]:
    """加载JSON配置文件"""
    config_path = CONFIG_DIR / filename
    if not config_path.exists():
        return {}
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ 加载配置文件失败 {filename}: {e}")
        return {}


def save_json_config(filename: str, data: Dict[str, Any]):
    """保存JSON配置文件"""
    config_path = CONFIG_DIR / filename
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


@router.get("/config/all")
async def get_all_configs():
    """获取所有配置"""
    try:
        # 加载配置
        agent_config = load_json_config("agent_config.json")
        tools_config = load_json_config("tools_config.json")
        api_config = load_json_config("api_config.json")
        
        # 统计工具
        tools_stats = {
            'total': len(tools_config),
            'enabled': sum(1 for t in tools_config.values() if t.get('enabled', False)),
            'disabled': sum(1 for t in tools_config.values() if not t.get('enabled', False))
        }
        
        return {
            "data": {
                "agent": agent_config,
                "tools": {
                    "config": tools_config,
                    "stats": tools_stats
                },
                "api": api_config
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"加载配置失败: {str(e)}")


@router.put("/config/agent")
async def update_agent_config(config: AgentConfigUpdate):
    """更新Agent配置"""
    try:
        current_config = load_json_config("agent_config.json")
        
        # 更新配置
        update_data = config.model_dump(exclude_none=True)
        current_config.update(update_data)
        
        save_json_config("agent_config.json", current_config)
        
        return {"message": "Agent配置已更新", "data": current_config}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新配置失败: {str(e)}")


@router.put("/config/api")
async def update_api_config(config: APIConfigUpdate):
    """更新API配置"""
    try:
        current_config = load_json_config("api_config.json")
        
        # 更新配置（跳过空的api_key）
        update_data = config.model_dump(exclude_none=True)
        if 'api_key' in update_data and not update_data['api_key']:
            del update_data['api_key']
        
        current_config.update(update_data)
        
        save_json_config("api_config.json", current_config)
        
        return {"message": "API配置已更新", "data": current_config}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新配置失败: {str(e)}")


@router.put("/config/tools/{tool_name}")
async def update_tool_config(tool_name: str, config: ToolConfigUpdate):
    """更新工具配置"""
    try:
        tools_config = load_json_config("tools_config.json")
        
        if tool_name not in tools_config:
            raise HTTPException(status_code=404, detail=f"工具 {tool_name} 不存在")
        
        # 更新配置
        update_data = config.model_dump(exclude_none=True, exclude={'tool_name'})
        tools_config[tool_name].update(update_data)
        
        save_json_config("tools_config.json", tools_config)
        
        return {"message": f"工具 {tool_name} 配置已更新", "data": tools_config[tool_name]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新配置失败: {str(e)}")


@router.post("/config/tools")
async def create_tool_config(config: ToolConfigUpdate):
    """创建工具配置"""
    try:
        tools_config = load_json_config("tools_config.json")
        
        if config.tool_name in tools_config:
            raise HTTPException(status_code=400, detail=f"工具 {config.tool_name} 已存在")
        
        # 创建工具配置
        tool_data = config.model_dump(exclude={'tool_name'}, exclude_none=True)
        tools_config[config.tool_name] = tool_data
        
        save_json_config("tools_config.json", tools_config)
        
        return {"message": f"工具 {config.tool_name} 已创建", "data": tool_data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建工具失败: {str(e)}")


@router.delete("/config/tools/{tool_name}")
async def delete_tool_config(tool_name: str):
    """删除工具配置"""
    try:
        tools_config = load_json_config("tools_config.json")
        
        if tool_name not in tools_config:
            raise HTTPException(status_code=404, detail=f"工具 {tool_name} 不存在")
        
        del tools_config[tool_name]
        save_json_config("tools_config.json", tools_config)
        
        return {"message": f"工具 {tool_name} 已删除"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除工具失败: {str(e)}")

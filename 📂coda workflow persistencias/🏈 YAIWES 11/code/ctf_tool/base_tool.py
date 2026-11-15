# -*- coding: utf-8 -*-
# 工具基类
from abc import ABC, abstractmethod
from typing import Dict
import logging

logger = logging.getLogger(__name__)


class BaseTool(ABC):
    # 适用模式: None = 全模式; {"ctf"} / {"pentest"} / {"ctf", "pentest"}
    modes: set = None

    @abstractmethod
    def execute(self, *args, **kwargs) -> str:
        """执行工具操作"""
        pass

    @property
    @abstractmethod
    def function_config(self) -> Dict:
        """返回工具的函数调用配置"""
        pass

    @property
    def tags(self) -> tuple:
        """工具的能力标签，用于工具推荐和分类。子类可覆盖。"""
        return ()

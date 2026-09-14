"""
FLAG检测器 - 自动识别和提取FLAG
"""
import re
from typing import List, Dict, Any


class FlagDetector:
    """FLAG检测器"""
    
    def __init__(self):
        # FLAG模式（支持多种格式）
        self.patterns = [
            # 标准CTF格式
            r'flag\{[^\}]{6,}\}',
            r'FLAG\{[^\}]{6,}\}',
            r'ctf\{[^\}]{6,}\}',
            r'CTF\{[^\}]{6,}\}',
            
            # 自定义格式
            r'flag:[a-zA-Z0-9_\-]{6,}',
            r'FLAG:[a-zA-Z0-9_\-]{6,}',
            
            # Hash格式
            r'flag_[a-f0-9]{32}',  # MD5
            r'flag_[a-f0-9]{40}',  # SHA1
            r'flag_[a-f0-9]{64}',  # SHA256
            
            # 特殊格式
            r'<flag>[^<]{6,}</flag>',
            r'<!-- flag:[^-]{6,} -->',
        ]
        
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.patterns]
    
    def detect(self, text: str) -> List[str]:
        """
        检测文本中的FLAG
        
        Args:
            text: 要检测的文本
        
        Returns:
            找到的FLAG列表
        """
        flags = []
        
        for pattern in self.compiled_patterns:
            matches = pattern.findall(text)
            flags.extend(matches)
        
        # 去重
        flags = list(set(flags))
        
        return flags
    
    def detect_in_response(self, response: Dict[str, Any]) -> List[str]:
        """
        在HTTP响应中检测FLAG
        
        Args:
            response: 响应字典 {'status': 200, 'headers': {...}, 'body': '...'}
        
        Returns:
            找到的FLAG列表
        """
        flags = []
        
        # 检测响应体
        if 'body' in response:
            flags.extend(self.detect(str(response['body'])))
        
        # 检测响应头
        if 'headers' in response:
            for key, value in response.get('headers', {}).items():
                flags.extend(self.detect(f"{key}: {value}"))
        
        # 检测Cookie
        if 'cookies' in response:
            for cookie in response.get('cookies', []):
                flags.extend(self.detect(str(cookie)))
        
        return list(set(flags))
    
    def validate_flag(self, flag: str) -> bool:
        """
        验证FLAG格式是否有效
        
        Args:
            flag: FLAG字符串
        
        Returns:
            是否有效
        """
        # 至少6个字符
        if len(flag) < 6:
            return False
        
        # 匹配任一模式
        for pattern in self.compiled_patterns:
            if pattern.search(flag):
                return True
        
        return False
    
    def extract_flag_value(self, flag: str) -> str:
        """
        提取FLAG的值部分
        
        Args:
            flag: 完整FLAG字符串，如 "flag{abc123}"
        
        Returns:
            FLAG值，如 "abc123"
        """
        # flag{...}格式
        match = re.search(r'(?:flag|ctf|FLAG|CTF)\{([^\}]+)\}', flag, re.IGNORECASE)
        if match:
            return match.group(1)
        
        # flag:...格式
        match = re.search(r'(?:flag|FLAG):([a-zA-Z0-9_\-]+)', flag, re.IGNORECASE)
        if match:
            return match.group(1)
        
        # <flag>...</flag>格式
        match = re.search(r'<flag>([^<]+)</flag>', flag, re.IGNORECASE)
        if match:
            return match.group(1)
        
        # 返回原值
        return flag

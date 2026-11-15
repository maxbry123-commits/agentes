#!/usr/bin/env python3
"""
🔥 智能Metadata生成器 v2.0 - 增量更新版本
支持缓存和增量更新，只解析新增/修改的文档
"""
import os
import json
import re
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from openai import OpenAI
from tqdm import tqdm
from datetime import datetime


class MetadataGenerator:
    """智能Metadata生成器 - 支持增量更新"""
    
    def __init__(self, knowledge_dir: str = "./knowledge/know"):
        self.knowledge_dir = Path(knowledge_dir)
        self.metadata_file = self.knowledge_dir / "knowledge_metadata.json"
        self.cache_file = self.knowledge_dir / ".metadata_cache.json"  # 文档哈希缓存
        
        # 使用 ConfigManager 加载LLM配置
        try:
            from config import ConfigManager
            config_manager = ConfigManager()
            api_config = config_manager.get('api', {})
        except ImportError:
            # 回退到直接读取文件
            config_path = Path("./config/api_config.json")
            with open(config_path, 'r') as f:
                api_config = json.load(f)
        
        llm_config = api_config.get('llm_config', {})
        self.client = OpenAI(
            api_key=api_config.get('api_key') or os.getenv('DASHSCOPE_API_KEY'),
            base_url=llm_config.get('base_url')
        )
        self.model = llm_config.get('model', 'kimi-k2-0905-preview')
        
        # 加载现有metadata和缓存
        self.existing_metadata = self._load_metadata()
        self.file_hashes = self._load_cache()
        
        print(f"✅ LLM初始化: {self.model}")
        print(f"📦 已加载 {len(self.existing_metadata)} 个已知文档的metadata")
        print(f"🔐 已加载 {len(self.file_hashes)} 个文件哈希缓存")
    
    def _load_metadata(self) -> Dict[str, Dict]:
        """加载现有的metadata文件"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ 加载metadata失败: {e}")
        return {}
    
    def _load_cache(self) -> Dict[str, str]:
        """加载文件哈希缓存"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ 加载缓存失败: {e}")
        return {}
    
    def _compute_file_hash(self, content: str) -> str:
        """计算文件内容的MD5哈希"""
        return hashlib.md5(content.encode()).hexdigest()
    
    def _needs_update(self, doc_id: str, file_path: Path) -> bool:
        """判断文档是否需要更新
        
        Returns:
            True: 需要更新（新文件或内容已改变）
            False: 无需更新（已在缓存中且内容未变）
        """
        # 如果在缓存中不存在，需要更新
        if doc_id not in self.file_hashes:
            return True
        
        # 计算当前文件哈希
        try:
            content = file_path.read_text(encoding='utf-8')
            current_hash = self._compute_file_hash(content)
            cached_hash = self.file_hashes.get(doc_id, "")
            
            # 如果哈希不同，需要更新
            if current_hash != cached_hash:
                print(f"  🔄 [{doc_id}] 检测到内容变化，需要重新分析")
                return True
            else:
                print(f"  ✓ [{doc_id}] 缓存有效，跳过分析")
                return False
        except Exception as e:
            print(f"  ⚠️ [{doc_id}] 计算哈希失败: {e}")
            return True
    
    def analyze_document(self, doc_id: str, content: str, title: str) -> Dict[str, Any]:
        """
        使用LLM分析单个文档
        返回：tags, summary, vuln_type, difficulty, key_techniques
        """
        # 🔥 结构化提示词 - 确保准确性
        prompt = f"""你是安全专家，分析以下渗透测试文档，提取准确的元数据。

文档标题：{title}
文档内容（前3000字符）：
{content[:3000]}

请严格按照以下JSON格式返回（不要有任何其他文字）：
{{
  "vuln_type": "主要漏洞类型（只选一个）: sql_injection/xss/ssti/lfi/rfi/ssrf/xxe/idor/command_injection/file_upload/jwt/auth_bypass/deserialization/other",
  "tags": ["技术标签1", "技术标签2", "技术标签3"],
  "summary": "一句话核心攻击思路（50字以内）",
  "difficulty": "easy/medium/hard",
  "key_techniques": ["关键技术1", "关键技术2", "关键技术3"],
  "frameworks": ["使用的框架，如Flask/Django/PHP/Java等"],
  "attack_chain": "攻击链简述（30字以内）"
}}

要求：
1. vuln_type必须从上述列表中选择最准确的一个
2. tags要包含具体技术关键词（如Jinja2、SQLMap、日志投毒等）
3. summary要突出核心利用点，不要泛泛而谈
4. difficulty基于利用难度判断
5. key_techniques要具体（如"双写绕过"、"Unicode编码"等）
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是安全专家，擅长分析渗透测试文档并提取结构化信息。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # 低温度确保准确性
                max_tokens=1000
            )
            
            content_str: str | None = response.choices[0].message.content
            result_text = content_str.strip() if content_str else ""
            
            # 提取JSON（可能包含代码块）
            json_match = re.search(r'``json\s*(.*?)\s*```', result_text, re.DOTALL)
            if json_match:
                result_text = json_match.group(1)
            
            metadata = json.loads(result_text)
            return metadata
            
        except Exception as e:
            print(f"  ⚠️ LLM分析失败: {e}，使用基础提取")
            return self._fallback_extract(content or "", title)
    
    def _fallback_extract(self, content: str, title: str) -> Dict[str, Any]:
        """回退方案：基于规则的提取"""
        content_lower = content.lower()
        
        # 漏洞类型检测
        vuln_type = "other"
        vuln_keywords = {
            'sql_injection': ['sql', 'sqlmap', 'union', 'injection'],
            'xss': ['xss', 'cross-site', '<script', 'alert('],
            'ssti': ['ssti', 'template', 'jinja2', 'flask', '{{'],
            'lfi': ['lfi', 'local file', 'file inclusion', '日志投毒', '../'],
            'ssrf': ['ssrf', 'request forgery'],
            'command_injection': ['command', 'rce', 'shell', 'exec'],
        }
        
        for vtype, keywords in vuln_keywords.items():
            if any(kw in content_lower for kw in keywords):
                vuln_type = vtype
                break
        
        # 提取标签
        tags = []
        if 'python' in content_lower:
            tags.append('Python')
        if 'flask' in content_lower:
            tags.append('Flask')
        if 'jinja2' in content_lower:
            tags.append('Jinja2')
        if 'php' in content_lower:
            tags.append('PHP')
        
        # 生成简单摘要
        first_lines = [line.strip() for line in content.split('\n') if line.strip() and not line.startswith('#')]
        summary = first_lines[0][:100] if first_lines else title
        
        return {
            'vuln_type': vuln_type,
            'tags': tags[:5],
            'summary': summary,
            'difficulty': 'medium',
            'key_techniques': [],
            'frameworks': [],
            'attack_chain': ''
        }
    
    def generate_all_metadata(self, force_update: bool = False) -> Tuple[Dict[str, Dict], int]:
        """生成所有文档的metadata（支持增量更新）
        
        Args:
            force_update: 是否强制更新所有文档
        
        Returns:
            (all_metadata, new_docs_count)
        """
        # 初始化：使用现有metadata
        all_metadata = dict(self.existing_metadata)
        
        # 获取所有markdown文件
        md_files = list(self.knowledge_dir.glob("*.md"))
        print(f"\n📚 发现 {len(md_files)} 个文档")
        
        # 分类：需要更新的 vs 可跳过的
        files_to_update = []
        files_to_skip = []
        new_docs = 0
        
        for md_file in md_files:
            doc_id = md_file.stem
            
            if force_update or self._needs_update(doc_id, md_file):
                files_to_update.append(md_file)
                if doc_id not in self.existing_metadata:
                    new_docs += 1
            else:
                files_to_skip.append(md_file)
        
        print(f"\n📊 分析结果:")
        print(f"  ✓ 缓存命中: {len(files_to_skip)} 个文档 (跳过分析)")
        print(f"  🆕 新增文档: {new_docs} 个")
        print(f"  🔄 需更新: {len(files_to_update) - new_docs} 个")
        print(f"  📋 总待处理: {len(files_to_update)} 个\n")
        
        if not files_to_update:
            print("⏭️  无需更新，跳过LLM分析")
            return all_metadata, 0
        
        print("🔄 开始LLM分析...\n")
        
        # 处理需要更新的文件
        for md_file in tqdm(files_to_update, desc="分析文档", colour='green'):
            doc_id = md_file.stem
            title = doc_id
            
            try:
                content = md_file.read_text(encoding='utf-8')
                
                # 提取标题
                title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
                if title_match:
                    title = title_match.group(1).strip()
                
                # 🔥 使用LLM分析（只分析新增/修改文件）
                metadata = self.analyze_document(doc_id, content, title)
                
                # 更新metadata
                all_metadata[doc_id] = {
                    'doc_id': doc_id,
                    'title': title,
                    'file_path': str(md_file),
                    'content_length': len(content),
                    'last_updated': datetime.now().isoformat(),
                    **metadata
                }
                
                # 更新文件哈希缓存
                self.file_hashes[doc_id] = self._compute_file_hash(content)
                
            except Exception as e:
                print(f"\n⚠️ 处理失败: {md_file.name} - {e}")
                continue
        
        return all_metadata, len(files_to_update)
    
    def save_metadata(self, metadata: Dict, output_file: Optional[str] = None):
        """保存metadata和缓存到JSON"""
        # 处理output_file的None情况
        save_path: Path = Path(output_file) if output_file else self.metadata_file
        
        # 保存metadata
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        # 保存文件哈希缓存
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.file_hashes, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ Metadata已保存: {save_path}")
        print(f"✅ 缓存已保存: {self.cache_file}")
        print(f"📊 总文档数: {len(metadata)}")
        print(f"🔐 缓存条目: {len(self.file_hashes)}")


def main():
    import sys
    
    print("="*80)
    print("🚀 智能Metadata生成器 v2.0 - 增量更新")
    print("="*80)
    
    # 检查命令行参数
    force_update = '--force' in sys.argv or '-f' in sys.argv
    
    if force_update:
        print("\n⚡ 强制更新模式: 所有文档都将重新分析")
    else:
        print("\n⚡ 增量更新模式: 只分析新增/修改的文档（推荐）")
        print("   使用 --force 参数强制更新所有文档")
    
    print("\n💾 智能缓存机制:")
    print("  • 计算每个文档的MD5哈希")
    print("  • 保存哈希值用于增量检测")
    print("  • 内容未变=直接跳过LLM分析")
    print("  • 首次运行会分析所有文档")
    print("  • 后续运行只分析变化文件\n")
    
    input("按Enter开始... (Ctrl+C取消)")
    
    generator = MetadataGenerator()
    
    # 生成metadata（支持增量更新）
    metadata, updated_count = generator.generate_all_metadata(force_update=force_update)
    
    # 保存metadata和缓存
    generator.save_metadata(metadata)
    
    print("\n" + "="*80)
    print("🎉 Metadata生成完成！")
    print("="*80)
    print(f"\n📈 本次更新统计:")
    print(f"  ✅ 已处理: {updated_count} 个文档")
    print(f"  📦 总文档: {len(metadata)} 个")
    print(f"  🔐 缓存保存: {generator.cache_file}")
    print(f"\n💡 下次运行将自动增量更新，无需重新分析所有文档！\n")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户取消")
    except Exception as e:
        print(f"\n\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()

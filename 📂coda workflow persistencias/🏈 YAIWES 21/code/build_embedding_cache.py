#!/usr/bin/env python3
"""
构建embedding缓存
"""
import sys
import time
from core.knowledge import KnowledgeBase

def main():
    print("=" * 80)
    print("🔨 开始构建Embedding缓存")
    print("=" * 80)
    print()
    print()
    
    try:
        # 初始化知识库
        kb = KnowledgeBase()
        
        # 🔥 强制构建embedding
        print("🔨 开始构建embedding缓存...")
        print(f"📚 总共 {len(kb.documents)} 个文档")
        print()
        
        kb.force_build_embeddings()
        
        # 强制构建embedding（即使缓存存在）
        if kb.embedding_loaded and kb.embeddings:
            print()
            print("=" * 80)
            print("✅ Embedding缓存构建成功！")
            print("=" * 80)
            print(f"📊 向量数量: {len(kb.embeddings)}")
            print(f"📂 缓存位置: {kb.embedding_cache_file}")
            print(f"💾 缓存大小: {kb.embedding_cache_file.stat().st_size / 1024 / 1024:.2f} MB")
            print()
            print("🎉 现在知识库搜索将使用高精度的embedding+rerank模式！")
            return 0
        else:
            print()
            print("⚠️ Embedding缓存未构建（可能API Key错误）")
            print("💡 将使用回退搜索模式（分词匹配）")
            return 1
            
    except KeyboardInterrupt:
        print()
        print("⚠️ 用户中断")
        return 1
    except Exception as e:
        print()
        print(f"❌ 构建失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())

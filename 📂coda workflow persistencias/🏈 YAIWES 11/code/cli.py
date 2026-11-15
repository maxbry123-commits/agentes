"""CTF Agent 命令行管理工具 — 知识库管理、数据导入导出。"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime

os.environ.setdefault("AGENT_NON_INTERACTIVE", "1")

logging.basicConfig(
    level=logging.WARNING,
    format="%(levelname)s - %(message)s",
)
logger = logging.getLogger("cli")
logger.setLevel(logging.INFO)


def cmd_stats(_args):
    """查看知识库统计信息。"""
    from rag.knowledge_base import KnowledgeBase
    from rag.memory_base import MemorySystem

    print("\n=== 知识库统计 ===\n")

    for label, cls, col_name in [
        ("CTF 知识库", KnowledgeBase, "ctf_knowledge"),
        ("Agent 记忆", MemorySystem, "agent_memory"),
    ]:
        try:
            instance = cls()
            count = instance.collection.count()
            metadata = instance.collection.metadata or {}

            print(f"[{label}]")
            print(f"  集合名称: {col_name}")
            print(f"  文档总数: {count}")
            if metadata.get("description"):
                print(f"  描述: {metadata['description']}")

            # 按类型统计
            if count > 0:
                try:
                    all_meta = instance.collection.get(include=["metadatas"])
                    type_counts = {}
                    for m in all_meta.get("metadatas", []):
                        if m:
                            item_type = m.get("type", "unknown")
                            type_counts[item_type] = type_counts.get(item_type, 0) + 1
                    if type_counts:
                        print(f"  类型分布:")
                        for t, c in sorted(type_counts.items(), key=lambda x: -x[1]):
                            print(f"    {t}: {c}")
                except Exception:
                    pass
            print()
        except Exception as e:
            print(f"[{label}] 无法访问: {e}\n")

    # 种子数据统计
    from rag.seed_knowledge import get_seed_stats
    try:
        seed = get_seed_stats()
        if seed:
            print("[种子数据 (seed_data/)]")
            for cat, info in sorted(seed.items()):
                if cat == "total":
                    continue
                print(f"  {cat}: {info['count']} 条")
            print(f"  ---")
            print(f"  总计: {seed['total']} 条\n")
    except Exception as e:
        print(f"种子数据统计失败: {e}\n")


def cmd_search(args):
    """搜索知识库。"""
    from rag.knowledge_base import KnowledgeBase

    query = args.query
    top = args.top

    if not query:
        print("错误: 请提供搜索关键词")
        return

    print(f"\n搜索: \"{query}\" (top {top})\n")

    try:
        kb = KnowledgeBase()
        results = kb.search_knowledge(query, n_results=top, hybrid=True)
    except Exception as e:
        print(f"搜索失败: {e}")
        return

    if not results:
        print("未找到相关知识。")
        return

    for i, r in enumerate(results, 1):
        content = r.get("content", "")[:300]
        meta = r.get("metadata", {})
        score = r.get("hybrid_score", r.get("relevance_score", 0))

        print(f"--- 结果 {i} (相关度: {score:.3f}) ---")
        print(content)
        if meta:
            tags = meta.get("tags", "")
            cat = meta.get("category", meta.get("type", ""))
            if cat:
                print(f"  分类: {cat}", end="")
            if tags:
                print(f"  标签: {tags}", end="")
            if cat or tags:
                print()
        print()


def cmd_add(args):
    """交互式添加知识条目。"""
    from rag.knowledge_base import KnowledgeBase

    print("\n=== 添加知识条目 ===\n")
    print("请输入知识内容（输入空行结束，Ctrl+C 取消）:")
    lines = []
    try:
        while True:
            line = input()
            if line == "" and lines:
                break
            lines.append(line)
    except (EOFError, KeyboardInterrupt):
        print("\n已取消")
        return

    content = "\n".join(lines).strip()
    if not content:
        print("内容为空，已取消")
        return

    tags_input = input("标签 (逗号分隔，可选): ").strip()
    tags = [t.strip() for t in tags_input.split(",") if t.strip()] if tags_input else []

    try:
        kb = KnowledgeBase()
        doc_id = kb.add_general_knowledge(content, tags)
        print(f"\n已添加 (ID: {doc_id})")
    except Exception as e:
        print(f"添加失败: {e}")


def cmd_list(args):
    """列出知识库文档（分页）。"""
    from rag.knowledge_base import KnowledgeBase
    from rag.memory_base import MemorySystem

    cols = {
        "knowledge": ("CTF 知识库", KnowledgeBase),
        "memory": ("Agent 记忆", MemorySystem),
    }
    col_name = args.collection or "knowledge"
    if col_name not in cols:
        print(f"错误: 未知集合 '{col_name}'，可选: {', '.join(cols.keys())}")
        return

    label, cls = cols[col_name]
    limit = args.limit or 20
    offset = args.offset or 0

    try:
        instance = cls()
        total = instance.collection.count()
        if total == 0:
            print(f"[{label}] 集合为空")
            return

        result = instance.collection.get(
            limit=limit, offset=offset, include=["documents", "metadatas"]
        )
        docs = result.get("documents", [])
        metas = result.get("metadatas", [])
        ids = result.get("ids", [])

        print(f"\n=== {label} (共 {total} 条, 显示 {offset+1}-{offset+len(docs)}) ===\n")
        for i, doc_id in enumerate(ids):
            meta = metas[i] if i < len(metas) else {}
            content = docs[i] if i < len(docs) else ""
            doc_type = meta.get("type", "unknown")
            tags = meta.get("tags", "")
            preview = content[:120].replace("\n", " ")
            print(f"  [{offset + i + 1}] ID: {doc_id}")
            print(f"      类型: {doc_type}  标签: {tags}")
            print(f"      内容: {preview}...")
            print()
        if offset + len(docs) < total:
            print(f"--- 还有 {total - offset - len(docs)} 条，使用 --offset {offset + limit} 查看更多 ---")
    except Exception as e:
        print(f"列出文档失败: {e}")


def cmd_delete(args):
    """从知识库删除文档。"""
    from rag.knowledge_base import KnowledgeBase
    from rag.memory_base import MemorySystem

    cols = {
        "knowledge": ("CTF 知识库", KnowledgeBase),
        "memory": ("Agent 记忆", MemorySystem),
    }
    col_name = args.collection or "knowledge"
    if col_name not in cols:
        print(f"错误: 未知集合 '{col_name}'，可选: {', '.join(cols.keys())}")
        return

    label, cls = cols[col_name]
    doc_ids = args.ids

    try:
        instance = cls()
        instance.collection.delete(ids=doc_ids)
        print(f"已从 [{label}] 删除 {len(doc_ids)} 条: {', '.join(doc_ids[:5])}{'...' if len(doc_ids) > 5 else ''}")
    except Exception as e:
        print(f"删除失败: {e}")


def cmd_export(args):
    """导出知识库到 JSON 文件。"""
    from rag.knowledge_base import KnowledgeBase
    from rag.memory_base import MemorySystem

    out_path = args.file or f"kb_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    export_data = {}
    for label, cls in [
        ("ctf_knowledge", KnowledgeBase),
        ("agent_memory", MemorySystem),
    ]:
        try:
            instance = cls()
            count = instance.collection.count()
            if count == 0:
                export_data[label] = {"count": 0, "documents": []}
                continue

            result = instance.collection.get(include=["documents", "metadatas"])
            docs = []
            for i in range(count):
                docs.append({
                    "content": result["documents"][i] if result.get("documents") and i < len(result["documents"]) else "",
                    "metadata": result["metadatas"][i] if result.get("metadatas") and i < len(result["metadatas"]) else {},
                    "id": result["ids"][i] if result.get("ids") and i < len(result["ids"]) else "",
                })
            export_data[label] = {"count": count, "documents": docs}
        except Exception as e:
            export_data[label] = {"error": str(e)}

    export_data["exported_at"] = datetime.now().isoformat()

    try:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        total = sum(v["count"] for v in export_data.values() if isinstance(v, dict) and "count" in v)
        print(f"已导出 {total} 条文档到: {os.path.abspath(out_path)}")
    except Exception as e:
        print(f"导出失败: {e}")


def cmd_import(args):
    """从 JSON 文件导入知识库。"""
    from rag.knowledge_base import KnowledgeBase
    from rag.memory_base import MemorySystem

    file_path = args.file
    if not os.path.exists(file_path):
        print(f"错误: 文件不存在: {file_path}")
        return

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"读取文件失败: {e}")
        return

    collection_map = {
        "ctf_knowledge": KnowledgeBase,
        "agent_memory": MemorySystem,
    }

    total = 0
    for col_name, cls in collection_map.items():
        col_data = data.get(col_name)
        if not col_data:
            continue
        docs = col_data.get("documents", [])
        if not docs:
            continue

        try:
            instance = cls()
            for doc in docs:
                content = doc.get("content", "")
                metadata = doc.get("metadata", {})
                if not content:
                    continue
                try:
                    instance._add(
                        contents=[content],
                        metadatas=[metadata],
                        ids=[doc.get("id", "")],
                    )
                    total += 1
                except Exception:
                    import uuid
                    fallback_id = doc.get("id") or f"import_{uuid.uuid4().hex[:12]}"
                    try:
                        instance._add(
                            contents=[content],
                            metadatas=[metadata],
                            ids=[fallback_id],
                        )
                        total += 1
                    except Exception as e2:
                        print(f"  警告: 导入文档失败 (ID={fallback_id}): {e2}")
        except Exception as e:
            print(f"导入 {col_name} 失败: {e}")

    print(f"已导入 {total} 条文档")


def cmd_reset(args):
    """重置知识库并重新种子。"""
    from rag.knowledge_base import KnowledgeBase
    from rag.memory_base import MemorySystem
    from rag.seed_knowledge import seed_knowledge_base

    # 确认
    if not args.force:
        print("警告: 此操作将删除所有知识库数据并重新种子！")
        try:
            response = input("确认重置? (输入 'yes' 确认): ").strip()
        except EOFError:
            print("非交互模式，使用 --force 强制执行")
            return
        if response.lower() != "yes":
            print("已取消")
            return

    print("\n重置中...")

    # 删除并重建集合
    for label, cls, col_name in [
        ("CTF 知识库", KnowledgeBase, "ctf_knowledge"),
        ("Agent 记忆", MemorySystem, "agent_memory"),
    ]:
        try:
            instance = cls()
            old_count = instance.collection.count()
            instance.delete_collection()
            instance._initialize_database()
            print(f"  {label}: 已清除 {old_count} 条，集合已重建")
        except Exception as e:
            print(f"  {label}: 重置失败 - {e}")
            return

    # 重新种子
    try:
        kb = KnowledgeBase()
        stats = seed_knowledge_base(kb)
        print(f"\n种子数据已重新导入:")
        for cat, count in sorted(stats.items()):
            if cat == "total":
                continue
            print(f"  {cat}: {count} 条")
        print(f"  总计: {stats.get('total', 0)} 条")
    except Exception as e:
        print(f"种子数据导入失败: {e}")


def main():
    parser = argparse.ArgumentParser(
        prog="python cli.py",
        description="CTF Agent 命令行管理工具",
    )
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # kb stats
    sp_stats = subparsers.add_parser("kb", help="知识库管理")
    kb_sub = sp_stats.add_subparsers(dest="kb_action", help="知识库操作")

    kb_sub.add_parser("stats", help="查看知识库统计信息").set_defaults(func=cmd_stats)

    sp_search = kb_sub.add_parser("search", help="搜索知识库")
    sp_search.add_argument("query", help="搜索关键词")
    sp_search.add_argument("-n", "--top", type=int, default=5, help="返回结果数 (默认 5)")
    sp_search.set_defaults(func=cmd_search)

    kb_sub.add_parser("add", help="交互式添加知识条目").set_defaults(func=cmd_add)

    sp_list = kb_sub.add_parser("list", help="列出知识库文档（分页）")
    sp_list.add_argument("collection", nargs="?", default="knowledge",
                         choices=["knowledge", "memory"],
                         help="集合名称: knowledge 或 memory (默认 knowledge)")
    sp_list.add_argument("-n", "--limit", type=int, default=20, help="每页条数 (默认 20)")
    sp_list.add_argument("--offset", type=int, default=0, help="起始偏移 (默认 0)")
    sp_list.set_defaults(func=cmd_list)

    sp_delete = kb_sub.add_parser("delete", help="从知识库删除文档（按 ID）")
    sp_delete.add_argument("collection", nargs="?", default="knowledge",
                           choices=["knowledge", "memory"],
                           help="集合名称: knowledge 或 memory (默认 knowledge)")
    sp_delete.add_argument("ids", nargs="+", help="要删除的文档 ID（可多个，空格分隔）")
    sp_delete.set_defaults(func=cmd_delete)

    sp_export = kb_sub.add_parser("export", help="导出知识库到 JSON 文件")
    sp_export.add_argument("file", nargs="?", default=None,
                           help="输出文件路径 (默认 kb_export_<时间戳>.json)")
    sp_export.set_defaults(func=cmd_export)

    sp_import = kb_sub.add_parser("import", help="从 JSON 文件导入知识库")
    sp_import.add_argument("file", help="要导入的 JSON 文件路径")
    sp_import.set_defaults(func=cmd_import)

    sp_reset = kb_sub.add_parser("reset", help="重置知识库并重新种子")
    sp_reset.add_argument("-f", "--force", action="store_true",
                          help="跳过确认提示")
    sp_reset.set_defaults(func=cmd_reset)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if not getattr(args, "kb_action", None):
        # User typed "python cli.py kb" without sub-action — show kb help
        for action in parser._actions:
            if isinstance(action, argparse._SubParsersAction) and action.dest == "command":
                for name, sub in action.choices.items():
                    if name == "kb":
                        sub.print_help()
                        return
        return

    args.func(args)


if __name__ == "__main__":
    main()

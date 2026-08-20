"""
CropWise 知识包批量导入脚本
==============================

使用方式：
  cd backend
  python import_knowledge_packs.py

将 10 个 P1 知识包导入 ChromaDB 向量库。
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))


def main():
    print("=" * 60)
    print("CropWise 知识包批量导入")
    print("=" * 60)

    # 1. 列出所有知识包
    from knowledge_pack_importer import KnowledgePackImporter
    from pathlib import Path

    packs_dir = Path(__file__).resolve().parent.parent / "data" / "knowledge-packs"
    importer = KnowledgePackImporter(packs_dir=packs_dir)
    packs = importer.get_pack_list()

    print(f"\n发现 {len(packs)} 个知识包:")
    total_chunks = 0
    for p in packs:
        total_chunks += p["chunk_count"]
        print(f"  {p['pack_id']:35s} | {p['chunk_count']:2d} 块 | v{p['version']:6s} | {p['evidence_level']}级")
    print(f"  总计: {total_chunks} 块")

    # 2. 导入到 ChromaDB
    print("\n导入到 ChromaDB...")
    try:
        from knowledge_base import knowledge_base
        stats = importer.import_all_packs(knowledge_base, force=True)
        print(f"  导入: {stats['packs_imported']} 个知识包")
        print(f"  块数: {stats['chunks_added']} 块")
        print(f"  跳过: {stats['packs_skipped']} 个")
        print(f"  错误: {stats['errors']} 个")

        # 3. 验证
        print("\n验证知识库状态:")
        status = knowledge_base.get_status()
        print(f"  总文档数: {status.get('total_documents', 0)}")
        print(f"  嵌入模式: {status.get('embedding_mode', 'unknown')}")
    except Exception as e:
        print(f"  ChromaDB 不可用: {e}")
        print("  仅完成解析，未实际导入")

    print("\n" + "=" * 60)
    print("完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()

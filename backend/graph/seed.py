# -*- coding: utf-8 -*-
"""
图谱种子脚本 — 从 evidence-packs 文档中抽取实体和关系并构建知识图谱。

用法:
    python -m graph.seed  # 从所有证据包文档构建图谱
    python -m graph.seed --stats  # 仅查看图谱统计
"""
from __future__ import annotations
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# 确保 backend 在 path 中
sys.path.insert(0, str(Path(__file__).parent.parent))

from graph.graph_store import GraphStore
from graph.entity_extractor import EntityExtractor
from graph.community_detection import CommunityDetector


def find_evidence_packs() -> List[Dict[str, Any]]:
    """发现所有证据包及其文档。"""
    packs_root = Path(__file__).parent.parent.parent / "data" / "evidence-packs"
    packs = []
    if not packs_root.exists():
        logger.warning("证据包目录不存在: %s", packs_root)
        return packs

    for pack_dir in sorted(packs_root.iterdir()):
        if not pack_dir.is_dir():
            continue
        manifest_path = pack_dir / "manifest.json"
        if not manifest_path.exists():
            continue
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            pack_id = manifest.get("pack_id", pack_dir.name)
            docs_dir = pack_dir / "documents"
            documents = []
            if docs_dir.exists():
                for doc_file in sorted(docs_dir.iterdir()):
                    if doc_file.suffix in (".md", ".txt"):
                        documents.append({
                            "path": str(doc_file),
                            "pack_id": pack_id,
                            "doc_id": doc_file.stem,
                        })
            packs.append({
                "pack_id": pack_id,
                "manifest": manifest,
                "documents": documents,
            })
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("跳过数据包 %s: %s", pack_dir, exc)

    return packs


def seed_graph() -> GraphStore:
    """从证据包文档构建知识图谱。

    Returns
    -------
    GraphStore
        构建完成的图谱存储实例。
    """
    graph = GraphStore()
    extractor = EntityExtractor(graph)

    # 统计
    total_docs = 0
    total_entities = 0
    total_triples = 0

    packs = find_evidence_packs()
    logger.info("发现 %d 个证据包", len(packs))

    for pack in packs:
        logger.info("处理数据包: %s", pack["pack_id"])
        for doc in pack["documents"]:
            result = extractor.ingest_to_graph(doc["path"], source=doc["doc_id"])
            total_docs += 1
            total_entities += result.get("entity_count", 0)
            total_triples += result.get("added_triples", 0)

    # 社区检测
    logger.info("运行社区检测...")
    detector = CommunityDetector(graph)
    communities = detector.detect()
    summaries = detector.generate_summaries()
    detector.save()
    logger.info("检测到 %d 个社区", len(communities))

    # 图谱统计
    stats = graph.stats()
    logger.info("=" * 40)
    logger.info("图谱构建完成!")
    logger.info("处理文档: %d", total_docs)
    logger.info("实体总数: %d", stats["entity_count"])
    logger.info("关系总数: %d", stats["relation_count"])
    logger.info("社区数量: %d", len(communities))
    logger.info("实体类型分布:")
    for etype, count in sorted(stats["entity_by_type"].items()):
        logger.info("  - %s: %d", etype, count)
    logger.info("=" * 40)

    return graph


def show_stats():
    """显示图谱统计信息。"""
    graph = GraphStore()
    graph.initialize()
    stats = graph.stats()
    print(f"实体总数: {stats['entity_count']}")
    print(f"关系总数: {stats['relation_count']}")
    print("实体类型分布:")
    for etype, count in sorted(stats["entity_by_type"].items()):
        print(f"  {etype}: {count}")
    print(f"数据目录: {graph.graph_dir}")


if __name__ == "__main__":
    if "--stats" in sys.argv:
        show_stats()
    else:
        seed_graph()
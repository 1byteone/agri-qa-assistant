"""
Neo4j 种子数据导入脚本
========================

使用方式：
  1. 确保 Neo4j 已启动（docker compose -f docker-compose.neo4j.yml up -d）
  2. 运行：python backend/kg/import_seeds.py

如果 Neo4j 不可用，脚本会跳过导入并输出统计信息。
"""

import sys
import os

# 确保 backend 目录在路径中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def main():
    print("=" * 60)
    print("CropWise 农业知识图谱 - 种子数据导入")
    print("=" * 60)

    # 1. 检查 Neo4j 连接
    print("\n[1/4] 检查 Neo4j 连接...")
    try:
        from kg.connection import neo4j_conn
        status = neo4j_conn.health_check()
        if status.get("status") == "healthy":
            print(f"  ✅ Neo4j 连接成功: {status.get('uri')}")
            print(f"     节点数: {status.get('total_nodes', 0)}")
            print(f"     关系数: {status.get('total_relations', 0)}")
        else:
            print(f"  ⚠️  Neo4j 不可用: {status.get('error', '未知错误')}")
            print("  → 跳过导入，请先启动 Neo4j")
            _print_stats_only()
            return
    except Exception as e:
        print(f"  ⚠️  Neo4j 连接失败: {e}")
        print("  → 跳过导入，请先启动 Neo4j")
        _print_stats_only()
        return

    # 2. 导入种子实体
    print("\n[2/4] 导入种子实体...")
    from kg.builder import kg_builder
    entity_stats = kg_builder.build_seed_data()
    print(f"  实体创建: {entity_stats.get('entities_created', 0)}")
    print(f"  错误: {entity_stats.get('errors', 0)}")

    # 3. 导入种子关系
    print("\n[3/4] 导入种子关系...")
    relation_stats = kg_builder.build_seed_relations()
    print(f"  关系创建: {relation_stats.get('relations_created', 0)}")
    print(f"  错误: {relation_stats.get('errors', 0)}")

    # 4. 验证查询
    print("\n[4/4] 验证 Cypher 查询...")
    _verify_queries()

    # 最终统计
    print("\n" + "=" * 60)
    print("导入完成！")
    total_entities = entity_stats.get("entities_created", 0)
    total_relations = relation_stats.get("relations_created", 0)
    print(f"  总实体: {total_entities}")
    print(f"  总关系: {total_relations}")
    print(f"  总错误: {entity_stats.get('errors', 0) + relation_stats.get('errors', 0)}")
    print("=" * 60)


def _print_stats_only():
    """仅打印种子数据统计（不连接 Neo4j）"""
    from kg.schema import (
        SEED_CROPS, SEED_DISEASES, SEED_PESTS, SEED_CHEMICALS,
        SEED_SYMPTOMS, SEED_GROWTH_STAGES, SEED_REGIONS,
        ENTITY_TYPES, RELATION_TYPES,
    )

    print("\n  种子数据统计（无需 Neo4j）:")
    print(f"    实体类型: {len(ENTITY_TYPES)}")
    print(f"    关系类型: {len(RELATION_TYPES)}")
    print(f"    作物: {len(SEED_CROPS)}")
    print(f"    病害: {len(SEED_DISEASES)}")
    print(f"    虫害: {len(SEED_PESTS)}")
    print(f"    农药: {len(SEED_CHEMICALS)}")
    print(f"    症状: {len(SEED_SYMPTOMS)}")
    print(f"    生育期: {len(SEED_GROWTH_STAGES)}")
    print(f"    地区: {len(SEED_REGIONS)}")

    # 估算关系数
    est_relations = (
        len(SEED_CROPS) * 2 +  # 每个作物约 2 个病虫害关系
        len(SEED_DISEASES) +    # 每个病害约 1 个防治关系
        len(SEED_CROPS) +       # 每个作物约 1 个地区关系
        len(SEED_CROPS) * 2 +   # 每个作物约 2 个生育期关系
        len(SEED_SYMPTOMS)      # 每个症状约 1 个指示关系
    )
    print(f"    预估关系: ~{est_relations}")


def _verify_queries():
    """验证 Cypher 查询"""
    from kg.connection import neo4j_conn
    from kg.schema import CypherTemplates

    queries_to_verify = [
        ("作物列表", "MATCH (c:Crop) RETURN c.name AS name LIMIT 5"),
        ("病害列表", "MATCH (d:Disease) RETURN d.name AS name LIMIT 5"),
        ("农药列表", "MATCH (c:Chemical) RETURN c.name AS name LIMIT 5"),
        ("水稻邻域", "MATCH (c:Crop {name: '水稻'})-[r]-(n) RETURN type(r) AS rel, labels(n)[0] AS type, n.name AS name LIMIT 10"),
        ("全文搜索", "CALL db.index.fulltext.queryNodes('entity_search', '水稻 病害') YIELD node, score RETURN labels(node)[0] AS type, node.name AS name, score LIMIT 5"),
    ]

    for name, query in queries_to_verify:
        try:
            results = neo4j_conn.run_query(query)
            if results:
                print(f"  ✅ {name}: {len(results)} 条结果")
                for r in results[:2]:
                    print(f"     {r}")
            else:
                print(f"  ⚠️  {name}: 无结果")
        except Exception as e:
            print(f"  ❌ {name}: {e}")


if __name__ == "__main__":
    main()

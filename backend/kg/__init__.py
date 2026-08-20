"""
CropWise 农业知识图谱模块
==========================

提供：
- Neo4j 连接管理
- 农业实体/关系 Schema
- 知识图谱构建器
- 知识图谱构建 Pipeline
- Graph RAG 检索接口

使用示例：
    from kg import neo4j_conn, kg_builder, get_entity_neighborhood

    # 检查连接
    status = neo4j_conn.health_check()

    # 构建知识图谱
    stats = kg_builder.build_full()

    # 查询实体邻域
    neighbors = get_entity_neighborhood("水稻", "Crop")
"""

from kg.connection import neo4j_conn, get_neo4j_status
from kg.schema import ENTITY_TYPES, RELATION_TYPES
from kg.builder import kg_builder, build_knowledge_graph
from kg.pipeline import KGBuildPipeline, get_kg_pipeline

__all__ = [
    "neo4j_conn",
    "get_neo4j_status",
    "ENTITY_TYPES",
    "RELATION_TYPES",
    "kg_builder",
    "build_knowledge_graph",
    "KGBuildPipeline",
    "get_kg_pipeline",
]

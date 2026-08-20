"""
CropWise Neo4j 连接管理器
===========================

提供 Neo4j 数据库连接、健康检查和基础 CRUD 操作。
支持连接池管理和重试机制。
"""

from __future__ import annotations
import os
import logging
from typing import Dict, List, Any, Optional, Tuple
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Neo4j 配置
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "cropwise2026")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")


class Neo4jConnection:
    """Neo4j 连接管理器（单例模式）"""

    _instance: Optional["Neo4jConnection"] = None
    _driver = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_driver(self):
        """获取 Neo4j 驱动（懒加载）"""
        if self._driver is None:
            try:
                from neo4j import GraphDatabase
                self._driver = GraphDatabase.driver(
                    NEO4J_URI,
                    auth=(NEO4J_USER, NEO4J_PASSWORD),
                    max_connection_pool_size=50,
                    connection_acquisition_timeout=30,
                )
                logger.info(f"Neo4j 连接成功: {NEO4J_URI}")
            except ImportError:
                logger.warning("neo4j 驱动未安装，知识图谱功能不可用。运行: pip install neo4j")
                return None
            except Exception as e:
                logger.error(f"Neo4j 连接失败: {e}")
                return None
        return self._driver

    def close(self):
        """关闭连接"""
        if self._driver:
            self._driver.close()
            self._driver = None
            logger.info("Neo4j 连接已关闭")

    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        driver = self.get_driver()
        if driver is None:
            return {"status": "unavailable", "error": "neo4j 驱动未安装或连接失败"}
        try:
            with driver.session(database=NEO4J_DATABASE) as session:
                result = session.run("RETURN 1 AS test")
                record = result.single()
                if record and record["test"] == 1:
                    # 获取统计信息
                    stats = self._get_stats(session)
                    return {"status": "healthy", "uri": NEO4J_URI, **stats}
                return {"status": "error", "error": "查询返回异常"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _get_stats(self, session) -> Dict[str, Any]:
        """获取图谱统计"""
        try:
            result = session.run("""
                MATCH (n)
                RETURN labels(n)[0] AS label, count(*) AS count
                ORDER BY count DESC
            """)
            labels = {record["label"]: record["count"] for record in result}

            result = session.run("MATCH ()-[r]->() RETURN type(r) AS type, count(*) AS count ORDER BY count DESC")
            relations = {record["type"]: record["count"] for record in result}

            total_nodes = sum(labels.values())
            total_relations = sum(relations.values())

            return {
                "total_nodes": total_nodes,
                "total_relations": total_relations,
                "node_labels": labels,
                "relation_types": relations,
            }
        except Exception as e:
            return {"stats_error": str(e)}

    def run_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """执行 Cypher 查询并返回结果"""
        driver = self.get_driver()
        if driver is None:
            return []
        try:
            with driver.session(database=NEO4J_DATABASE) as session:
                result = session.run(query, parameters or {})
                return [dict(record) for record in result]
        except Exception as e:
            logger.error(f"Cypher 查询失败: {e}")
            return []

    def run_write(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> bool:
        """执行写入操作"""
        driver = self.get_driver()
        if driver is None:
            return False
        try:
            with driver.session(database=NEO4J_DATABASE) as session:
                session.run(query, parameters or {})
                return True
        except Exception as e:
            logger.error(f"Cypher 写入失败: {e}")
            return False

    def batch_write(self, queries: List[Tuple[str, Dict[str, Any]]]) -> int:
        """批量写入，返回成功数量"""
        driver = self.get_driver()
        if driver is None:
            return 0
        success_count = 0
        try:
            with driver.session(database=NEO4J_DATABASE) as session:
                for query, params in queries:
                    try:
                        session.run(query, params)
                        success_count += 1
                    except Exception as e:
                        logger.warning(f"批量写入单条失败: {e}")
        except Exception as e:
            logger.error(f"批量写入会话失败: {e}")
        return success_count


# 全局连接实例
neo4j_conn = Neo4jConnection()


# ============================================================
# 便捷函数
# ============================================================

def get_neo4j_status() -> Dict[str, Any]:
    """获取 Neo4j 服务状态"""
    return neo4j_conn.health_check()


def create_entity(label: str, name: str, properties: Optional[Dict[str, Any]] = None) -> bool:
    """创建实体节点"""
    props = properties or {}
    props["name"] = name
    query = f"MERGE (n:{label} {{name: $name}}) SET n += $props RETURN n"
    return neo4j_conn.run_write(query, {"name": name, "props": props})


def create_relation(
    source_label: str, source_name: str,
    target_label: str, target_name: str,
    relation_type: str,
    properties: Optional[Dict[str, Any]] = None
) -> bool:
    """创建关系"""
    props = properties or {}
    query = f"""
    MATCH (a:{source_label} {{name: $source_name}})
    MATCH (b:{target_label} {{name: $target_name}})
    MERGE (a)-[r:{relation_type}]->(b)
    SET r += $props
    RETURN a, r, b
    """
    return neo4j_conn.run_write(query, {
        "source_name": source_name,
        "target_name": target_name,
        "props": props,
    })


def get_entity_neighborhood(entity_name: str, label: str, limit: int = 20) -> List[Dict[str, Any]]:
    """获取实体邻域子图"""
    query = f"""
    MATCH (e:{label} {{name: $name}})-[r]-(neighbor)
    RETURN type(r) AS relation, labels(neighbor)[0] AS neighbor_type,
           neighbor.name AS neighbor_name, properties(r) AS relation_props
    LIMIT $limit
    """
    return neo4j_conn.run_query(query, {"name": entity_name, "limit": limit})


def diagnose_by_symptoms(symptoms: List[str], limit: int = 5) -> List[Dict[str, Any]]:
    """根据症状推断病虫害"""
    from kg.schema import CypherTemplates
    return neo4j_conn.run_query(CypherTemplates.DIAGNOSE_BY_SYMPTOM, {
        "symptoms": symptoms,
        "limit": limit,
    })


def search_entities(query_text: str, limit: int = 10) -> List[Dict[str, Any]]:
    """全文搜索实体"""
    from kg.schema import CypherTemplates
    return neo4j_conn.run_query(CypherTemplates.SEARCH_ENTITIES, {
        "query": query_text,
        "limit": limit,
    })


def get_crop_info(crop_name: str) -> Dict[str, Any]:
    """获取作物完整信息"""
    from kg.schema import CypherTemplates
    pests = neo4j_conn.run_query(CypherTemplates.CROP_PESTS_DISEASES, {"crop_name": crop_name})
    return {
        "crop": crop_name,
        "pests_and_diseases": pests,
    }


def get_region_policies(region_name: str) -> List[Dict[str, Any]]:
    """获取地区政策"""
    from kg.schema import CypherTemplates
    return neo4j_conn.run_query(CypherTemplates.REGION_POLICIES, {"region_name": region_name})

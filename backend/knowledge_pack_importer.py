"""
CropWise 知识包导入器
======================

将 Markdown 格式的知识包导入 ChromaDB 向量库。

功能：
- 自动解析 Markdown 知识包（YAML 头部 + 正文分块）
- 增量导入（基于 content_hash 去重）
- 版本管理（manifest 跟踪）
- 元数据增强（crop/region/stage/evidence_level）

使用方式：
    from knowledge_pack_importer import KnowledgePackImporter
    importer = KnowledgePackImporter()
    stats = importer.import_all_packs()
"""

from __future__ import annotations
import os
import re
import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

# 知识包目录（相对于 backend 目录）
KNOWLEDGE_PACKS_DIR = Path(__file__).resolve().parent.parent / "data" / "knowledge-packs"
MANIFEST_PATH = KNOWLEDGE_PACKS_DIR / "manifest.json"


class KnowledgePackParser:
    """Markdown 知识包解析器"""

    @staticmethod
    def parse_file(filepath: Path) -> Optional[Dict[str, Any]]:
        """
        解析 Markdown 知识包文件。

        Returns:
            Dict with keys: metadata, chunks, content_hash
        """
        if not filepath.exists():
            logger.warning(f"知识包文件不存在: {filepath}")
            return None

        content = filepath.read_text(encoding="utf-8")
        if not content.strip():
            return None

        # 解析 YAML 头部
        metadata = {}
        body = content
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                yaml_content = parts[1].strip()
                body = parts[2].strip()
                metadata = KnowledgePackParser._parse_yaml_simple(yaml_content)

        # 补充文件级元数据
        metadata["filename"] = filepath.name
        metadata["filepath"] = str(filepath)
        metadata["file_size"] = filepath.stat().st_size
        metadata["last_modified"] = datetime.fromtimestamp(
            filepath.stat().st_mtime
        ).isoformat()

        # 分块
        chunks = KnowledgePackParser._split_markdown(body, metadata)

        # 计算内容哈希
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]

        return {
            "metadata": metadata,
            "chunks": chunks,
            "content_hash": content_hash,
        }

    @staticmethod
    def _parse_yaml_simple(yaml_text: str) -> Dict[str, Any]:
        """简单 YAML 解析（不依赖 pyyaml）"""
        result = {}
        for line in yaml_text.split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()
                # 解析列表
                if value.startswith("[") and value.endswith("]"):
                    value = [
                        v.strip().strip('"').strip("'")
                        for v in value[1:-1].split(",")
                        if v.strip()
                    ]
                # 解析字符串（去除引号）
                elif value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                # 解析布尔值
                elif value.lower() in ("true", "yes"):
                    value = True
                elif value.lower() in ("false", "no"):
                    value = False
                result[key] = value
        return result

    @staticmethod
    def _split_markdown(text: str, base_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """将 Markdown 文本分块"""
        chunks = []
        current_section = ""
        current_content = []
        section_level = 0

        for line in text.split("\n"):
            # 检测标题
            heading_match = re.match(r"^(#{1,4})\s+(.+)$", line)
            if heading_match:
                # 保存上一个段落
                if current_content:
                    content = "\n".join(current_content).strip()
                    if content:
                        chunks.append({
                            "content": content,
                            "section": current_section,
                            "section_level": section_level,
                            "metadata": dict(base_metadata),
                        })
                current_section = heading_match.group(2).strip()
                section_level = len(heading_match.group(1))
                current_content = [line]
            else:
                current_content.append(line)

        # 保存最后一个段落
        if current_content:
            content = "\n".join(current_content).strip()
            if content:
                chunks.append({
                    "content": content,
                    "section": current_section,
                    "section_level": section_level,
                    "metadata": dict(base_metadata),
                })

        # 如果没有分块成功，将整个文本作为一个块
        if not chunks and text.strip():
            chunks.append({
                "content": text.strip()[:2000],
                "section": "",
                "section_level": 0,
                "metadata": dict(base_metadata),
            })

        return chunks


class KnowledgePackImporter:
    """知识包导入器"""

    def __init__(self, packs_dir: Optional[Path] = None):
        self.packs_dir = packs_dir or KNOWLEDGE_PACKS_DIR
        self.parser = KnowledgePackParser()
        self._manifest = self._load_manifest()
        self._stats = {
            "packs_found": 0,
            "packs_imported": 0,
            "packs_skipped": 0,
            "chunks_added": 0,
            "chunks_skipped": 0,
            "errors": 0,
        }

    def import_all_packs(
        self,
        knowledge_base=None,
        force: bool = False,
    ) -> Dict[str, Any]:
        """
        导入所有知识包。

        Args:
            knowledge_base: KnowledgeBase 实例（可选，不传则仅解析）
            force: 强制重新导入（忽略版本检查）

        Returns:
            导入统计
        """
        if not self.packs_dir.exists():
            logger.warning(f"知识包目录不存在: {self.packs_dir}")
            return self._stats

        # 扫描所有 .md 文件
        pack_files = list(self.packs_dir.glob("*.md"))
        self._stats["packs_found"] = len(pack_files)
        logger.info(f"发现 {len(pack_files)} 个知识包文件")

        for pack_file in pack_files:
            try:
                self._import_single_pack(pack_file, knowledge_base, force)
            except Exception as e:
                logger.error(f"导入知识包失败 {pack_file.name}: {e}")
                self._stats["errors"] += 1

        # 保存 manifest
        self._save_manifest()

        return self._stats

    def _import_single_pack(
        self,
        pack_file: Path,
        knowledge_base=None,
        force: bool = False,
    ):
        """导入单个知识包"""
        parsed = self.parser.parse_file(pack_file)
        if not parsed:
            return

        metadata = parsed["metadata"]
        content_hash = parsed["content_hash"]
        pack_id = metadata.get("pack_id", pack_file.stem)

        # 版本检查
        if not force and pack_id in self._manifest:
            existing = self._manifest[pack_id]
            if existing.get("content_hash") == content_hash:
                self._stats["packs_skipped"] += 1
                logger.debug(f"知识包未变更，跳过: {pack_id}")
                return

        logger.info(f"导入知识包: {pack_id} ({len(parsed['chunks'])} 块)")

        # 导入到知识库
        if knowledge_base:
            for chunk in parsed["chunks"]:
                chunk_metadata = chunk["metadata"]
                chunk_metadata["pack_id"] = pack_id
                chunk_metadata["content_hash"] = content_hash
                chunk_metadata["section"] = chunk.get("section", "")
                chunk_metadata["import_time"] = datetime.now().isoformat()

                try:
                    knowledge_base.ingest_document(
                        chunk["content"],
                        metadata=chunk_metadata,
                    )
                    self._stats["chunks_added"] += 1
                except Exception as e:
                    logger.warning(f"块导入失败: {e}")
                    self._stats["errors"] += 1
        else:
            self._stats["chunks_added"] += len(parsed["chunks"])

        # 更新 manifest
        self._manifest[pack_id] = {
            "content_hash": content_hash,
            "version": metadata.get("version", "1.0"),
            "import_time": datetime.now().isoformat(),
            "chunk_count": len(parsed["chunks"]),
            "filename": pack_file.name,
        }
        self._stats["packs_imported"] += 1

    def get_pack_list(self) -> List[Dict[str, Any]]:
        """获取所有知识包信息"""
        packs = []
        if not self.packs_dir.exists():
            return packs

        for pack_file in sorted(self.packs_dir.glob("*.md")):
            parsed = self.parser.parse_file(pack_file)
            if parsed:
                packs.append({
                    "filename": pack_file.name,
                    "pack_id": parsed["metadata"].get("pack_id", pack_file.stem),
                    "version": parsed["metadata"].get("version", "unknown"),
                    "region": parsed["metadata"].get("region", ""),
                    "crops": parsed["metadata"].get("crops", []),
                    "evidence_level": parsed["metadata"].get("evidence_level", "C"),
                    "chunk_count": len(parsed["chunks"]),
                    "content_hash": parsed["content_hash"],
                })
        return packs

    def _load_manifest(self) -> Dict[str, Any]:
        """加载 manifest"""
        if MANIFEST_PATH.exists():
            try:
                return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}

    def _save_manifest(self):
        """保存 manifest"""
        try:
            MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
            MANIFEST_PATH.write_text(
                json.dumps(self._manifest, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception as e:
            logger.warning(f"保存 manifest 失败: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return dict(self._stats)


# ============================================================
# 便捷函数
# ============================================================

def import_knowledge_packs(
    knowledge_base=None,
    force: bool = False,
) -> Dict[str, Any]:
    """一键导入所有知识包"""
    importer = KnowledgePackImporter()
    return importer.import_all_packs(knowledge_base, force)


def list_knowledge_packs() -> List[Dict[str, Any]]:
    """列出所有知识包"""
    importer = KnowledgePackImporter()
    return importer.get_pack_list()

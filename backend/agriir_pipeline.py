"""Small, configurable AgriIR-style retrieval pipeline.

The module deliberately keeps orchestration deterministic. LLM-powered query
rewriting can be added later through the stage registry without changing the
retrieval and citation contract consumed by the API and UI.
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class StageConfig:
    name: str
    enabled: bool = True
    temperature: Optional[float] = None
    top_k: Optional[int] = None


@dataclass(frozen=True)
class PipelineConfig:
    version: str = "0.1"
    citation_threshold: float = 0.75
    citation_threshold_by_embedding: Dict[str, float] = field(default_factory=dict)
    max_subqueries: int = 4
    stages: tuple[StageConfig, ...] = field(default_factory=tuple)


def _default_config() -> PipelineConfig:
    return PipelineConfig(
        stages=(
            StageConfig("query_refinement", temperature=0.1),
            StageConfig("subquery_decomposition", temperature=0.5),
            StageConfig("parallel_retrieval", top_k=3),
            StageConfig("synthesis", temperature=0.2),
            StageConfig("citation_insertion"),
        )
    )


def load_pipeline_config(path: Optional[str] = None) -> PipelineConfig:
    """Load JSON config and fall back safely when a deployment omits it."""
    config_path = Path(path) if path else Path(__file__).with_name("agriir_pipeline.json")
    if not config_path.exists():
        return _default_config()
    try:
        raw = json.loads(config_path.read_text(encoding="utf-8"))
        stage_items = raw.get("stages", [])
        stages = tuple(
            StageConfig(
                name=str(item["name"]),
                enabled=bool(item.get("enabled", True)),
                temperature=item.get("temperature"),
                top_k=item.get("top_k"),
            )
            for item in stage_items
            if isinstance(item, dict) and item.get("name")
        ) or _default_config().stages
        return PipelineConfig(
            version=str(raw.get("version", "0.1")),
            citation_threshold=float(raw.get("citation_threshold", 0.75)),
            citation_threshold_by_embedding={str(key): float(value) for key, value in (raw.get("citation_threshold_by_embedding") or {}).items()},
            max_subqueries=max(1, min(int(raw.get("max_subqueries", 4)), 8)),
            stages=stages,
        )
    except (OSError, ValueError, TypeError, KeyError) as exc:
        logger.warning("AgriIR pipeline config invalid, using defaults: %s", exc)
        return _default_config()


def _stable_id(*parts: str) -> str:
    digest = hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()[:10]
    return f"S{digest.upper()}"


class AgriIRPipeline:
    """Deterministic stages shared by API diagnostics and the Agent."""

    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or load_pipeline_config()

    def describe(self) -> Dict[str, Any]:
        return {
            "version": self.config.version,
            "citation_threshold": self.config.citation_threshold,
            "citation_threshold_by_embedding": self.config.citation_threshold_by_embedding,
            "max_subqueries": self.config.max_subqueries,
            "stages": [
                {
                    "name": stage.name,
                    "enabled": stage.enabled,
                    "temperature": stage.temperature,
                    "top_k": stage.top_k,
                }
                for stage in self.config.stages
            ],
        }

    def refine_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> str:
        # 先使用 QueryTransformer 进行查询改写
        try:
            from retrieval.query_transformer import query_transformer
            refined = query_transformer.rewrite(query, context)
        except ImportError:
            refined = re.sub(r"\s+", " ", (query or "").strip())

        context = context or {}
        hints = [str(context.get(key, "")).strip() for key in ("crop", "region", "stage")]
        evidence_anchor = {
            "rice_fertilizer_recommendation": "水稻施肥 测土配方 目标产量 土壤肥力",
            "rapeseed_fertilizer_recommendation": "油菜施肥 测土配方 蕾薹期",
            "citrus_fertilizer_recommendation": "脐橙施肥 测土配方 膨果期",
            "vegetable_fertilizer_recommendation": "蔬菜施肥 测土配方 苗期",
        }.get(self.required_evidence_scope(refined))
        if evidence_anchor:
            hints.append(evidence_anchor)
        hints = [hint for hint in hints if hint and hint not in refined]
        return "；".join([refined, *hints]) if hints else refined

    def decompose_query(self, query: str) -> List[str]:
        parts = [part.strip(" ，,、；;。") for part in re.split(r"(?:并且|同时|以及|和|与|及|\?|？|。|；|;)", query or "")]
        parts = [part for part in parts if len(part) >= 2]
        if not parts:
            parts = [query.strip()]
        return list(dict.fromkeys(parts))[: self.config.max_subqueries]

    def retrieve(self, query: str, knowledge_base: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        refined = self.refine_query(query, context)
        subqueries = self.decompose_query(refined)
        strategy = knowledge_base.choose_strategy(refined)
        top_k = next((stage.top_k for stage in self.config.stages if stage.name == "parallel_retrieval" and stage.top_k), 3)
        required_scope = self.required_evidence_scope(refined)
        candidate_top_k = max(int(top_k), int(top_k) * 3) if required_scope else int(top_k)

        # ── QueryRouter 路由提示 ──
        search_hints = {}
        try:
            from retrieval.query_router import query_router
            route = query_router.route(query)
            scenario = query_router.classify_scenario(query)
            search_hints = query_router.get_search_hints(query, scenario)
            logger.info("QueryRouter: route=%s, scenario=%s, hints=%s", route.value, scenario, search_hints)
        except ImportError:
            pass

        # ── 并行检索 ──
        candidates: List[Dict[str, Any]] = []
        for subquery in subqueries:
            try:
                for item in knowledge_base.search(subquery, top_k=candidate_top_k, strategy=strategy):
                    item = dict(item)
                    item["subquery"] = subquery
                    candidates.append(item)
            except Exception as exc:
                logger.warning("AgriIR retrieval failed for subquery: %s", exc)

        # ── RRF 融合：将各子查询的检索结果通过 RRF 合并 ──
        try:
            from retrieval.rrf_fusion import rrf_fusion
            # 按子查询分组，每组是一个 ranked list
            subquery_groups: Dict[str, List[Dict[str, Any]]] = {}
            for item in candidates:
                sq = item.get("subquery", "")
                subquery_groups.setdefault(sq, []).append(item)
            if len(subquery_groups) > 1:
                ranked_lists = list(subquery_groups.values())
                ranked = rrf_fusion(ranked_lists, k=60)
                logger.info("RRF fusion applied: %d subqueries → %d ranked", len(ranked_lists), len(ranked))
            else:
                ranked = sorted(candidates, key=lambda x: float(x.get("relevance", 0.0)), reverse=True)
        except ImportError:
            # 回退到原有去重排序
            unique: Dict[str, Dict[str, Any]] = {}
            for item in candidates:
                metadata = item.get("metadata") or {}
                key = str(metadata.get("content_hash") or item.get("content") or "")
                if not key:
                    continue
                previous = unique.get(key)
                if previous is None or float(item.get("relevance", 0.0)) > float(previous.get("relevance", 0.0)):
                    unique[key] = item
            ranked = sorted(unique.values(), key=lambda item: float(item.get("relevance", 0.0)), reverse=True)

        # ── Parent-Child 上下文恢复 ──
        try:
            from retrieval.parent_child import ParentChildIndexer
            indexer = ParentChildIndexer()
            ranked = indexer.enrich_results(ranked, include_parent=True)
        except ImportError:
            pass

        result_limit = max(1, int(top_k))
        if required_scope:
            # A high-risk answer must retain an admissible official candidate
            # even when broad background chunks have a slightly higher vector score.
            ranked_citations = self.build_citations(ranked, query=refined, threshold=self.citation_threshold_for(knowledge_base))
            admissible = [item for item, citation in zip(ranked, ranked_citations) if citation.get("eligible")]
            if admissible:
                admissible_keys = {str((item.get("metadata") or {}).get("content_hash") or item.get("content") or "") for item in admissible}
                ranked = admissible + [
                    item for item in ranked
                    if str((item.get("metadata") or {}).get("content_hash") or item.get("content") or "") not in admissible_keys
                ]
        results = ranked[:result_limit]
        citations = self.build_citations(results, query=refined, threshold=self.citation_threshold_for(knowledge_base))
        return {
            "query": query,
            "refined_query": refined,
            "subqueries": subqueries,
            "strategy": strategy,
            "results": results,
            "citations": citations,
        }

    @staticmethod
    def requires_official_evidence(query: str) -> bool:
        return bool(re.search(r"农药|药剂|用药|剂量|安全间隔|肥料|施肥|追肥|石灰|有机肥|掺沙|(?:每亩|亩|多少|用量|剂量).{0,6}肥|(?:施|用).{0,6}肥|兽药|疫病|政策|补贴|标准|规范|登记", query or "", re.IGNORECASE))

    @staticmethod
    def required_evidence_scope(query: str) -> Optional[str]:
        text = query or ""
        if re.search(r"农药|药剂|用药|剂量|安全间隔", text):
            if re.search(r"剂量|用量|倍液|每亩|安全间隔|间隔期|喷施", text):
                return "pesticide_label"
            if "登记" in text:
                return "pesticide_registration"
            return "pesticide_governance"
        if re.search(r"肥料|施肥|追肥|石灰|有机肥|掺沙|(?:每亩|亩|多少|用量|剂量).{0,6}肥|(?:施|用).{0,6}肥", text):
            if "水稻" in text or "稻田" in text:
                return "rice_fertilizer_recommendation"
            if "油菜" in text:
                return "rapeseed_fertilizer_recommendation"
            if re.search(r"脐橙|柑橘|果树", text):
                return "citrus_fertilizer_recommendation"
            if re.search(r"蔬菜|叶菜|瓜果", text):
                return "vegetable_fertilizer_recommendation"
            return "fertilizer_recommendation"
        if re.search(r"政策|补贴", text):
            return "policy"
        if re.search(r"标准|规范", text):
            return "technical_standard"
        if re.search(r"兽药|疫病", text):
            return "animal_health_regulation"
        return None

    def citation_threshold_for(self, knowledge_base: Any) -> float:
        embedding_mode = str(getattr(knowledge_base, "embedding_mode", ""))
        return self.config.citation_threshold_by_embedding.get(embedding_mode, self.config.citation_threshold)

    def build_citations(self, results: Iterable[Dict[str, Any]], query: str = "", threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        official_only = self.requires_official_evidence(query)
        required_scope = self.required_evidence_scope(query)
        threshold = self.config.citation_threshold if threshold is None else threshold
        citations: List[Dict[str, Any]] = []
        for index, result in enumerate(results, start=1):
            metadata = result.get("metadata") or {}
            content = re.sub(r"\s+", " ", str(result.get("content", "")).strip())
            relevance = round(float(result.get("relevance", 0.0)), 4)
            source = str(metadata.get("source") or metadata.get("title") or "农业知识库")
            citation_id = _stable_id(source, content)
            evidence_level = str(metadata.get("evidence_level") or "C")
            evidence_scopes = {item.strip() for item in str(metadata.get("evidence_scope") or "").split("|") if item.strip()}
            scope_matches = not required_scope or required_scope in evidence_scopes
            eligible = relevance >= threshold and (not official_only or evidence_level == "A") and scope_matches
            citations.append({
                "id": citation_id,
                "label": f"S{index}",
                "title": source,
                "excerpt": content[:240],
                "relevance": relevance,
                "eligible": eligible,
                "evidence_level": evidence_level,
                "evidence_scope": sorted(evidence_scopes),
                "required_evidence_scope": required_scope,
                "eligibility_reason": "official-source-required" if official_only and evidence_level != "A" else ("evidence-scope-required" if not scope_matches else ("similarity-threshold" if relevance < threshold else "eligible")),
                "metadata": metadata,
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
            })
        return citations

    def citation_context(self, citations: Iterable[Dict[str, Any]]) -> str:
        lines = []
        for item in citations:
            lines.append(f"[{item['label']}] {item['excerpt']}（来源：{item['title']}，相关性 {item['relevance']:.2f}）")
        return "\n".join(lines)

    def append_citation_block(self, answer: str, citations: List[Dict[str, Any]]) -> str:
        eligible = [item for item in citations if item.get("eligible")]
        if not answer.strip() or not eligible or "## 参考来源" in answer:
            return answer
        lines = ["\n\n## 参考来源"]
        lines.extend(f"- [{item['label']}] {item['title']}：{item['excerpt']}" for item in eligible)
        return answer.rstrip() + "\n" + "\n".join(lines)


agriir_pipeline = AgriIRPipeline()

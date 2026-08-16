"""Small, auditable Query rewrite rules for the product-search lab."""

from __future__ import annotations

from dataclasses import dataclass

from .product_dataset import FAMILY_SPECS, QUERY_ONLY_PHRASES


@dataclass(frozen=True, slots=True)
class RewriteRule:
    source_phrase: str
    canonical_term: str
    family_id: str


@dataclass(frozen=True, slots=True)
class RewriteResult:
    original_query: str
    rewritten_query: str
    applied_rules: tuple[RewriteRule, ...]


def build_rewrite_rules() -> tuple[RewriteRule, ...]:
    rules: list[RewriteRule] = []
    for family in FAMILY_SPECS:
        for feature_index, (canonical_term, _) in enumerate(family.feature_sets):
            rules.append(
                RewriteRule(
                    source_phrase=QUERY_ONLY_PHRASES[family.family_id][feature_index],
                    canonical_term=canonical_term,
                    family_id=family.family_id,
                )
            )
    return tuple(rules)


REWRITE_RULES = build_rewrite_rules()


def rewrite_query(query: str) -> RewriteResult:
    """Append canonical attributes while preserving the user's original text."""

    rewritten = query
    applied: list[RewriteRule] = []
    for rule in REWRITE_RULES:
        if rule.source_phrase in query:
            rewritten = f"{rewritten} {rule.canonical_term}"
            applied.append(rule)
    return RewriteResult(
        original_query=query,
        rewritten_query=rewritten,
        applied_rules=tuple(applied),
    )

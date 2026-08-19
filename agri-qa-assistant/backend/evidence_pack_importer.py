"""Fetch and materialize pre-approved official evidence-pack documents."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List

import requests
from bs4 import BeautifulSoup

from source_registry import build_evidence_metadata


MAX_DOCUMENT_BYTES = 3 * 1024 * 1024


def extract_official_article(html: str) -> Dict[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    title = (soup.find("meta", attrs={"name": "ArticleTitle"}) or {}).get("content") or (soup.title.string if soup.title else "官方资料")
    published_at = (soup.find("meta", attrs={"name": "PubDate"}) or {}).get("content", "")
    body = soup.select_one(".sj_arc_body") or soup.select_one(".TRS_Editor") or soup.select_one(".article-content-body") or soup.select_one("#zoomcon") or soup.body
    text = "\n".join(line.strip() for line in body.get_text("\n").splitlines() if line.strip()) if body else ""
    if len(text) < 100:
        raise ValueError("官方页面未包含可用正文")
    return {"title": title.strip(), "published_at": published_at[:10], "text": text}


def materialize_pack(manifest_path: Path) -> List[Dict[str, Any]]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    pack_id = manifest["pack_id"]
    version = manifest["version"]
    updated = []
    for document in manifest.get("documents", []):
        source_url = document["source_url"]
        response = requests.get(source_url, headers={"User-Agent": "CropWise evidence-pack importer/0.1"}, timeout=20)
        response.raise_for_status()
        if len(response.content) > MAX_DOCUMENT_BYTES:
            raise ValueError(f"官方页面超过 {MAX_DOCUMENT_BYTES} 字节限制：{source_url}")
        # Government pages can send an incorrect HTTP charset despite declaring
        # UTF-8 in the document. Decode the bytes explicitly so evidence text
        # never enters the pack in a lossy representation.
        article = extract_official_article(response.content.decode("utf-8", errors="strict"))
        if document.get("published_at") and article["published_at"] and document["published_at"] != article["published_at"]:
            raise ValueError(f"发布日期不匹配：{source_url}")
        local_path = manifest_path.parent / document["local_path"]
        local_path.parent.mkdir(parents=True, exist_ok=True)
        content = f"# {article['title']}\n\n来源：{source_url}\n发布日期：{article['published_at']}\n\n{article['text']}\n"
        local_path.write_text(content, encoding="utf-8")
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        previous_content_hash = document.get("content_hash")
        metadata = build_evidence_metadata(
            filename=local_path.name,
            content_hash=content_hash,
            content_type="text/markdown",
            source_id=document["source_id"],
            source_url=source_url,
            published_at=article["published_at"] or document["published_at"],
            region=document.get("region"),
            pack_id=pack_id,
            pack_version=version,
            evidence_scope=document.get("evidence_scope"),
        )
        document.update({"title": article["title"], "published_at": metadata["published_at"], "content_hash": content_hash, "evidence_id": metadata["evidence_id"], "status": "materialized"})
        updated.append({"path": local_path, "content": content, "metadata": metadata, "previous_content_hash": previous_content_hash})
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return updated


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--ingest", action="store_true")
    args = parser.parse_args()
    documents = materialize_pack(args.manifest)
    if args.ingest:
        from knowledge_base import knowledge_base
        for document in documents:
            previous_hash = document.get("previous_content_hash")
            if previous_hash and previous_hash != document["metadata"]["content_hash"]:
                knowledge_base.remove_by_content_hash(previous_hash)
            knowledge_base.ingest_document(document["content"], metadata=document["metadata"])
    print(json.dumps({"pack": str(args.manifest), "documents": len(documents), "ingested": args.ingest}, ensure_ascii=False))


if __name__ == "__main__":
    main()

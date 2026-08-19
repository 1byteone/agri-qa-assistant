import requests
from bs4 import BeautifulSoup
import logging
from typing import List, Dict
import time

logger = logging.getLogger(__name__)

# 简单内存缓存（5分钟TTL）
_news_cache: Dict[str, tuple[List, float]] = {}

_FALLBACK_NEWS = [
    {"title": "曾勇军教授团队获国家科技进步二等奖", "tag": "国家奖"},
    {"title": "12项成果获2024年度江西省科学技术奖", "tag": "省科技奖"},
    {"title": "贺浩华教授获江西省科技进步特等奖", "tag": "省特等奖"},
    {"title": "双季超级稻高产栽培技术实现突破", "tag": "技术创新"},
    {"title": "三亚南繁育种基地持续产出优质水稻品种", "tag": "南繁育种"},
    {"title": "超级杂交晚稻·淞鑫688荣获省科技进步一等奖", "tag": "省一等奖"},
]


def fetch_jxau_news(max_items: int = 6) -> List[Dict]:
    """从江西农业大学官网抓取最新新闻/成就"""
    cache_key = "jxau_news"
    now = time.time()
    
    if cache_key in _news_cache:
        items, cached_at = _news_cache[cache_key]
        if now - cached_at < 300:  # 5分钟TTL
            return items[:max_items]
    
    try:
        resp = requests.get(
            "https://www.jxau.edu.cn/info/1491/306801.htm",
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # 提取新闻标题和摘要
        articles = []
        for item in soup.select("div.article, div.news-list li, table tr")[:max_items]:
            title = item.get_text(strip=True)[:80]
            if title and len(title) > 10:
                articles.append({"title": title, "tag": "官方新闻"})
        
        if not articles:
            articles = _FALLBACK_NEWS
        
        _news_cache[cache_key] = (articles, now)
        return articles[:max_items]
    except Exception as e:
        logger.warning(f"抓取江农新闻失败: {e}")
        return _FALLBACK_NEWS[:max_items]
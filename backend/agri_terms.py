"""Curated, source-backed agriculture terminology for optional UI annotations."""
from __future__ import annotations

from typing import Dict, Any


AGRI_TERMS: Dict[str, Dict[str, Any]] = {
    "稻飞虱": {
        "term": "稻飞虱",
        "title": "稻飞虱（planthopper）",
        "summary": "水稻重要刺吸式害虫，常见类型包括褐飞虱、白背飞虱和灰飞虱。识别与防治应结合田间虫口密度和生育期，不能仅凭单张图片下结论。",
        "source_name": "农业农村部全国农业技术推广服务中心",
        "source_url": "https://www.natesc.org.cn/",
        "source_label": "全国农技推广信息",
    },
    "条锈病": {
        "term": "条锈病",
        "title": "小麦条锈病",
        "summary": "小麦重要真菌病害，典型夏孢子堆沿叶脉呈条状排列。田间判断需结合病斑、孢子堆、天气和发病范围，并请植保人员复核。",
        "source_name": "农业农村部全国农业技术推广服务中心",
        "source_url": "https://www.natesc.org.cn/",
        "source_label": "全国农技推广信息",
    },
    "分蘖期": {
        "term": "分蘖期",
        "title": "水稻分蘖期",
        "summary": "水稻营养生长阶段，植株形成分蘖并决定有效穗基础。水肥和晒田管理需结合品种、苗情、土壤和当地农技规程。",
        "source_name": "中国农业科学院作物科学研究所",
        "source_url": "https://www.caas.cn/",
        "source_label": "中国农业科学院",
    },
    "双季稻": {
        "term": "双季稻",
        "title": "双季稻（早稻与晚稻）",
        "summary": "同一稻田一年种植早稻和晚稻的制度。江西播期受积温、无霜期、水源、品种熟期和天气影响，应采用区域化农时判断。",
        "source_name": "江西农业农村厅",
        "source_url": "https://nync.jiangxi.gov.cn/",
        "source_label": "江西农业农村信息",
    },
    "赣南脐橙": {
        "term": "赣南脐橙",
        "title": "赣南脐橙",
        "summary": "江西特色柑橘产业。采后品质管理应关注成熟度、机械伤、预冷、贮藏通风和食品安全合规，不能仅凭外观图片确诊病害。",
        "source_name": "赣州市农业农村局",
        "source_url": "https://nync.ganzhou.gov.cn/",
        "source_label": "赣州农业农村信息",
    },
    "红壤": {
        "term": "红壤",
        "title": "江西红壤",
        "summary": "江西广泛分布的酸性土壤类型，改良和施肥需依据土壤检测、作物需肥特性和水土保持要求，避免凭经验过量施用。",
        "source_name": "中国科学院南京土壤研究所",
        "source_url": "http://www.issas.ac.cn/",
        "source_label": "中国科学院土壤科学资料",
    },
    "鄱阳湖": {
        "term": "鄱阳湖流域农业生态",
        "summary": "鄱阳湖周边农业管理需要兼顾稻作生产、湿地和水质保护，重点控制氮磷流失、农药风险和暴雨期排水污染。",
        "source_name": "江西省生态环境厅",
        "source_url": "https://sthjt.jiangxi.gov.cn/",
        "source_label": "江西生态环境公开信息",
    },
    "植保无人机": {
        "term": "植保无人机",
        "title": "植保无人机",
        "summary": "用于农药喷洒和叶面施肥的农业航空器。作业需核验登记药剂、风速、敏感目标、飞行区域和设备记录，并遵守当地监管要求。",
        "source_name": "农业农村部农业机械化总站",
        "source_url": "https://www.amic.agri.gov.cn/",
        "source_label": "农业机械化公开信息",
    },
}


def lookup_term(term: str) -> Dict[str, Any] | None:
    value = (term or "").strip()
    if value in AGRI_TERMS:
        return AGRI_TERMS[value]
    for key, item in AGRI_TERMS.items():
        if key in value or value in key:
            return item
    return None

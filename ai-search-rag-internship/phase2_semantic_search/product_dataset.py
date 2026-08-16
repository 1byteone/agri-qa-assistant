"""Deterministic product-search data for interview-defensible experiments.

The catalog is synthetic on purpose. It exercises the same data contracts as a
real search project without pretending that generated metrics came from a
company's production logs.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class FamilySpec:
    family_id: str
    category: str
    name: str
    scenario: str
    common_features: tuple[str, ...]
    feature_sets: tuple[tuple[str, str], ...]
    synonyms: tuple[str, ...]
    base_price: int
    price_step: int


FAMILY_SPECS: tuple[FamilySpec, ...] = (
    FamilySpec(
        family_id="audio",
        category="数码配件",
        name="降噪蓝牙耳机",
        scenario="通勤",
        common_features=("无线", "蓝牙", "便携"),
        feature_sets=(
            ("主动降噪", "隔绝地铁噪声"),
            ("长续航", "连续听歌"),
            ("低延迟", "游戏和视频"),
            ("通话清晰", "会议通话"),
            ("入耳舒适", "长时间佩戴"),
        ),
        synonyms=("耳塞", "无线耳机", "通勤听歌"),
        base_price=199,
        price_step=20,
    ),
    FamilySpec(
        family_id="thermos",
        category="户外用品",
        name="轻量保温杯",
        scenario="露营",
        common_features=("防漏", "便携", "户外"),
        feature_sets=(
            ("316不锈钢", "耐腐蚀"),
            ("大容量", "长时间饮水"),
            ("轻量杯身", "背包不增重"),
            ("保温保冷", "冷热饮都适用"),
            ("一键开盖", "单手取水"),
        ),
        synonyms=("水杯", "随行杯", "户外喝水"),
        base_price=79,
        price_step=8,
    ),
    FamilySpec(
        family_id="keyboard",
        category="电脑外设",
        name="静音机械键盘",
        scenario="办公",
        common_features=("有线无线双模", "紧凑布局", "可充电"),
        feature_sets=(
            ("红轴手感", "按键轻柔"),
            ("静音轴体", "办公室不扰人"),
            ("蓝牙多设备", "电脑平板切换"),
            ("可编程按键", "快捷操作"),
            ("人体工学", "长时间打字"),
        ),
        synonyms=("办公键盘", "码字键盘", "打字工具"),
        base_price=189,
        price_step=18,
    ),
    FamilySpec(
        family_id="charger",
        category="数码配件",
        name="多口氮化镓充电器",
        scenario="出差",
        common_features=("小体积", "便携", "安全保护"),
        feature_sets=(
            ("65W快充", "笔记本和手机"),
            ("三口输出", "同时充多台设备"),
            ("100W高功率", "大功率笔记本"),
            ("折叠插脚", "收纳不占空间"),
            ("协议兼容", "兼容主流快充"),
        ),
        synonyms=("充电头", "电源适配器", "出差充电"),
        base_price=129,
        price_step=15,
    ),
    FamilySpec(
        family_id="shoes",
        category="户外服饰",
        name="防滑徒步鞋",
        scenario="徒步",
        common_features=("耐磨", "抓地", "户外"),
        feature_sets=(
            ("防水鞋面", "雨天可穿"),
            ("轻量鞋底", "长距离不累"),
            ("高帮支撑", "保护脚踝"),
            ("透气网面", "夏季不闷脚"),
            ("越野抓地", "复杂路面稳定"),
        ),
        synonyms=("登山鞋", "户外鞋", "爬山鞋"),
        base_price=259,
        price_step=25,
    ),
    FamilySpec(
        family_id="chair",
        category="办公家具",
        name="人体工学办公椅",
        scenario="久坐办公",
        common_features=("可调节", "支撑性", "办公"),
        feature_sets=(
            ("腰部支撑", "缓解久坐腰酸"),
            ("头枕可调", "颈部放松"),
            ("透气网布", "夏天久坐"),
            ("扶手联动", "手臂支撑"),
            ("小户型窄身", "小空间办公"),
        ),
        synonyms=("电脑椅", "办公座椅", "久坐椅"),
        base_price=499,
        price_step=35,
    ),
    FamilySpec(
        family_id="case",
        category="手机配件",
        name="防摔手机壳",
        scenario="日常通勤",
        common_features=("轻薄", "耐用", "保护"),
        feature_sets=(
            ("镜头全包", "保护摄像头"),
            ("磁吸兼容", "支持磁吸配件"),
            ("透明不发黄", "保留手机外观"),
            ("防滑边框", "手感稳固"),
            ("军规防摔", "高强度防护"),
        ),
        synonyms=("手机套", "保护壳", "手机保护"),
        base_price=39,
        price_step=5,
    ),
    FamilySpec(
        family_id="airfryer",
        category="厨房电器",
        name="智能空气炸锅",
        scenario="家庭做饭",
        common_features=("少油", "易清洗", "厨房"),
        feature_sets=(
            ("大容量", "适合多人用餐"),
            ("可视窗口", "随时观察火候"),
            ("低脂烹饪", "健康少油"),
            ("一键菜单", "新手也好操作"),
            ("双锅分区", "同时做两种食物"),
        ),
        synonyms=("空气炸锅", "无油锅", "厨房小家电"),
        base_price=229,
        price_step=22,
    ),
    FamilySpec(
        family_id="luggage",
        category="旅行用品",
        name="轻便登机箱",
        scenario="短途出行",
        common_features=("静音轮", "耐磨", "便携"),
        feature_sets=(
            ("20寸登机", "符合登机尺寸"),
            ("铝框结构", "箱体更稳固"),
            ("扩容设计", "回程能多装"),
            ("防水面料", "雨天保护行李"),
            ("分区收纳", "衣物电子设备分开"),
        ),
        synonyms=("行李箱", "旅行箱", "登机箱"),
        base_price=299,
        price_step=28,
    ),
    FamilySpec(
        family_id="lamp",
        category="办公家具",
        name="护眼阅读台灯",
        scenario="夜间学习",
        common_features=("无频闪", "可调亮度", "节能"),
        feature_sets=(
            ("色温调节", "学习休息切换"),
            ("定时关闭", "睡前自动熄灯"),
            ("长臂照明", "覆盖大桌面"),
            ("夹式安装", "宿舍节省空间"),
            ("高显色", "阅读颜色更自然"),
        ),
        synonyms=("学习灯", "桌面灯", "阅读灯"),
        base_price=89,
        price_step=9,
    ),
)

QUERY_ONLY_PHRASES: dict[str, tuple[str, ...]] = {
    "audio": ("早高峰隔绝人声", "充一次电用很久", "打游戏声音别拖", "线上开会人声清楚", "戴久了耳朵不疼"),
    "thermos": ("放包里不洒", "一天喝水不用反复加", "背包里尽量没重量", "冷饮热饮都能带", "走路时单手打开"),
    "keyboard": ("按键别吵同事", "敲代码手感轻", "电脑平板来回切", "常用操作一键完成", "久坐打字手腕舒服"),
    "charger": ("一只充电头解决出差", "手机电脑一起充", "大功率本也能带动", "收进行李不占地方", "各种设备都能快充"),
    "shoes": ("下雨走山路鞋里不湿", "走一天脚底不累", "碎石路保护脚踝", "夏天走路脚不闷", "泥地石路都抓得住"),
    "chair": ("坐一天腰不容易酸", "脖子需要有地方靠", "夏天坐着后背不出汗", "手臂能跟着椅背动", "小书桌也放得下"),
    "case": ("镜头朝下也别磕坏", "能吸住磁吸支架", "手机原色要露出来", "拿在手里别打滑", "摔一下也尽量不坏"),
    "airfryer": ("一次做够一家人", "不用打开锅盖看火", "少放油也能做脆", "厨房小白也会用", "两种食物不要串味"),
    "luggage": ("不用托运也能带上飞机", "箱子硬一点更安心", "回来买东西还能多装", "小雨天行李别进水", "衣服和电脑分开放"),
    "lamp": ("学习和休息亮度不同", "睡前不用起身关灯", "桌面大一点也照得到", "宿舍桌边能夹住", "看书颜色不要失真"),
}


def _product_id(family_index: int, variant_index: int) -> str:
    return f"prod-{family_index + 1:02d}-{variant_index + 1:03d}"


def build_product_catalog(product_count: int = 500) -> list[dict[str, Any]]:
    """Build a stable catalog with explicit fields and searchable text."""

    family_count = len(FAMILY_SPECS)
    if product_count <= 0 or product_count % family_count != 0:
        raise ValueError(f"product_count must be a positive multiple of {family_count}")

    per_family = product_count // family_count
    catalog: list[dict[str, Any]] = []
    for family_index, family in enumerate(FAMILY_SPECS):
        for variant_index in range(per_family):
            feature_index = variant_index % len(family.feature_sets)
            feature, feature_explanation = family.feature_sets[feature_index]
            price = family.base_price + variant_index * family.price_step
            product_id = _product_id(family_index, variant_index)
            title = f"{family.name} {family.family_id.upper()}-{variant_index + 1:03d}"
            attributes = [
                *family.common_features,
                feature,
                f"{price}元档",
            ]
            description = (
                f"面向{family.scenario}场景的{family.name}，主打{feature_explanation}。"
                f"适合关注{feature}和{family.common_features[0]}的用户。"
            )
            searchable_text = " ".join(
                (
                    f"标题 {title}",
                    f"类目 {family.category}",
                    f"场景 {family.scenario}",
                    f"属性 {' '.join(attributes)}",
                    f"描述 {description}",
                )
            )
            catalog.append(
                {
                    "id": product_id,
                    "title": title,
                    "category": family.category,
                    "attributes": attributes,
                    "description": description,
                    "price": price,
                    "text": searchable_text,
                    "family_id": family.family_id,
                    "feature_index": feature_index,
                    "data_version": "product-catalog-v1",
                }
            )
    return catalog


def build_product_queries(catalog: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, list[str]]]:
    """Build 50 query/qrels pairs with five intent types per family."""

    products_by_family: dict[str, list[dict[str, Any]]] = {}
    for product in catalog:
        products_by_family.setdefault(str(product["family_id"]), []).append(product)

    queries: list[dict[str, Any]] = []
    qrels: dict[str, list[str]] = {}
    query_templates = (
        ("exact_category", "{name} {feature}"),
        ("natural_language", "想找{synonym}，用于{scenario}，重点是{query_phrase}"),
        ("attribute_filter", "{category} {query_phrase} {common_feature}"),
        ("long_tail", "{scenario}想要{synonym}，{query_phrase}，预算不要太高"),
        ("scenario_first", "{scenario}用的{synonym}，希望{query_phrase}"),
    )

    query_number = 1
    for family in FAMILY_SPECS:
        family_products = products_by_family[family.family_id]
        for feature_index, (feature, explanation) in enumerate(family.feature_sets):
            matching_products = [
                product
                for product in family_products
                if int(product["feature_index"]) == feature_index
            ]
            if not matching_products:
                raise RuntimeError(f"no matching products for {family.family_id}:{feature_index}")

            template_index = feature_index
            query_type, template = query_templates[template_index]
            query_text = template.format(
                name=family.name,
                feature=feature,
                explanation=explanation,
                synonym=family.synonyms[feature_index % len(family.synonyms)],
                scenario=family.scenario,
                category=family.category,
                common_feature=family.common_features[feature_index % len(family.common_features)],
                query_phrase=QUERY_ONLY_PHRASES[family.family_id][feature_index],
            )
            query_id = f"q-{query_number:03d}"
            query_number += 1
            relevant_ids = [str(product["id"]) for product in matching_products]
            queries.append(
                {
                    "query_id": query_id,
                    "query": query_text,
                    "query_type": query_type,
                    "family_id": family.family_id,
                    "required_feature": feature,
                    "relevant_ids": relevant_ids,
                    "data_version": "product-qrels-v1",
                }
            )
            qrels[query_id] = relevant_ids
    return queries, qrels


def write_product_dataset(output_dir: str | Path, *, product_count: int = 500) -> dict[str, Any]:
    """Write catalog and qrels and return a compact manifest."""

    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    catalog = build_product_catalog(product_count)
    queries, qrels = build_product_queries(catalog)

    catalog_path = directory / "product_catalog_v1.json"
    queries_path = directory / "product_queries_v1.json"
    qrels_path = directory / "product_qrels_v1.json"
    manifest_path = directory / "product_dataset_manifest_v1.json"

    catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    queries_path.write_text(json.dumps(queries, ensure_ascii=False, indent=2), encoding="utf-8")
    qrels_path.write_text(json.dumps(qrels, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest = {
        "dataset_type": "synthetic_teaching_catalog",
        "data_version": "product-search-v1",
        "product_count": len(catalog),
        "query_count": len(queries),
        "family_count": len(FAMILY_SPECS),
        "relevance_definition": "products in the same family and feature bucket as the query intent",
        "files": {
            "catalog": catalog_path.name,
            "queries": queries_path.name,
            "qrels": qrels_path.name,
        },
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def family_specs_as_dicts() -> list[dict[str, Any]]:
    """Expose the scenario definitions for notebooks and teaching notes."""

    return [asdict(spec) for spec in FAMILY_SPECS]

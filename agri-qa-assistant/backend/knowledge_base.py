import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

from config import settings

logger = logging.getLogger(__name__)


class KnowledgeBase:
    """农业领域私有知识库（ChromaDB）"""

    def __init__(self):
        self.persist_dir = settings.chroma_persist_dir
        self.collection_name = "agri_knowledge"
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=settings.agnes_api_key,
            openai_api_base=settings.agnes_base_url,
            model=settings.agnes_embedding_model,
        )
        self._vectorstore: Optional[Chroma] = None
        self._ensure_db_dir()

    def _ensure_db_dir(self):
        Path(self.persist_dir).mkdir(parents=True, exist_ok=True)

    def _get_vectorstore(self) -> Chroma:
        if self._vectorstore is None:
            self._vectorstore = Chroma(
                collection_name=self.collection_name,
                persist_directory=self.persist_dir,
                embedding_function=self.embeddings,
            )
        return self._vectorstore

    def add_documents(self, documents: List[Document]) -> int:
        """添加文档到知识库"""
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", "。", "；", " ", ""],
        )
        chunks = text_splitter.split_documents(documents)
        
        vectorstore = self._get_vectorstore()
        vectorstore.add_documents(chunks)
        return len(chunks)

    def add_texts(self, texts: List[str], metadatas: Optional[List[Dict[str, Any]]] = None) -> int:
        """添加纯文本到知识库"""
        documents = [
            Document(page_content=text, metadata=meta or {})
            for text, meta in zip(texts, metadatas or [{}] * len(texts))
        ]
        return self.add_documents(documents)

    def search(self, query: str, top_k: int = 5, score_threshold: float = 0.5) -> List[Dict[str, Any]]:
        """语义检索"""
        vectorstore = self._get_vectorstore()
        results = vectorstore.similarity_search_with_score(query, k=top_k)
        
        filtered = []
        for doc, score in results:
            if score >= score_threshold:
                filtered.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": float(score),
                })
        return filtered

    def get_status(self) -> Dict[str, Any]:
        """获取知识库状态"""
        try:
            vectorstore = self._get_vectorstore()
            count = vectorstore._collection.count()
            return {
                "total_documents": count,
                "collection_name": self.collection_name,
                "persist_dir": self.persist_dir,
            }
        except Exception as e:
            logger.error(f"获取知识库状态失败: {e}")
            return {
                "total_documents": 0,
                "collection_name": self.collection_name,
                "error": str(e),
            }

    def clear(self):
        """清空知识库"""
        try:
            import shutil
            if os.path.exists(self.persist_dir):
                shutil.rmtree(self.persist_dir)
            self._vectorstore = None
            self._ensure_db_dir()
        except Exception as e:
            logger.error(f"清空知识库失败: {e}")


# 全局知识库实例
knowledge_base = KnowledgeBase()


def init_default_knowledge_base():
    """初始化默认农业知识库"""
    default_docs = [
        # 作物种植
        Document(
            page_content="水稻种植技术：水稻喜高温、多湿、短日照，对土壤要求不严。播种前需进行种子处理，包括晒种、选种、浸种催芽。插秧时每穴3-5株苗，行距30cm，株距20cm。分蘖期保持浅水层，抽穗期保持3-5cm水层，成熟期适时排水晒田。",
            metadata={"category": "crop", "crop": "水稻", "topic": "planting"}
        ),
        Document(
            page_content="小麦种植技术：小麦适应性强，耐寒耐旱。播种前深耕细耙，施足底肥。播种深度3-5cm，播种量每亩15-20kg。返青期追施拔节肥，抽穗期防治锈病和白粉病，成熟期及时收获。",
            metadata={"category": "crop", "crop": "小麦", "topic": "planting"}
        ),
        Document(
            page_content="玉米种植技术：玉米喜温，种子发芽最低温度8-10℃。播种深度5-6cm，亩保苗3500-4000株。拔节期追施穗肥，大喇叭口期防治玉米螟，抽雄期遇高温干旱需灌溉。",
            metadata={"category": "crop", "crop": "玉米", "topic": "planting"}
        ),
        # 病虫害防治
        Document(
            page_content="水稻稻飞虱防治：稻飞虱分白背飞虱、褐飞虱和灰飞虱。防治适期为若虫盛发期，可用吡虫啉、噻虫嗪等药剂喷雾。同时保护田间蜘蛛、青蛙等天敌。",
            metadata={"category": "pest", "crop": "水稻", "pest": "稻飞虱", "topic": "control"}
        ),
        Document(
            page_content="小麦锈病防治：小麦锈病分条锈病、叶锈病和秆锈病。防治策略：选用抗病品种，合理密植，增施磷钾肥。药剂防治可用戊唑醇、三唑酮等，在发病初期喷雾。",
            metadata={"category": "pest", "crop": "小麦", "pest": "锈病", "topic": "control"}
        ),
        Document(
            page_content="玉米螟防治：玉米螟是玉米主要害虫，幼虫钻蛀茎秆和果穗。防治方法：心叶期用苏云金杆菌(Bt)制剂颗粒剂撒入心叶；喇叭口期用辛硫磷颗粒剂灌心；生物防治释放赤眼蜂。",
            metadata={"category": "pest", "crop": "玉米", "pest": "玉米螟", "topic": "control"}
        ),
        Document(
            page_content="蚜虫综合防治：蚜虫可危害小麦、玉米、蔬菜等多种作物。农业防治：清除杂草，合理密植。物理防治：黄色粘虫板诱杀。生物防治：释放蚜茧蜂、瓢虫。化学防治：吡虫啉、啶虫脒喷雾。",
            metadata={"category": "pest", "topic": "control"}
        ),
        # 肥料施用
        Document(
            page_content="氮磷钾肥施用原则：氮肥促进茎叶生长，磷肥促进根系发育和开花结果，钾肥增强抗逆性。施肥原则：有机肥为主，化肥为辅；氮磷钾配合，适量补充微肥。水稻分蘖期施氮肥，孕穗期补钾；小麦拔节期追氮，抽穗前喷磷酸二氢钾。",
            metadata={"category": "fertilizer", "topic": "npk"}
        ),
        Document(
            page_content="测土配方施肥：根据土壤化验结果和作物需肥特性，制定施肥方案。步骤：1.取土样检测；2.确定目标产量；3.计算养分需求量；4.确定肥料品种和用量；5.调整施肥方法。可减少化肥用量10-20%，提高产量5-15%。",
            metadata={"category": "fertilizer", "topic": "soil_testing"}
        ),
        Document(
            page_content="叶面肥施用技术：叶面肥可作为根部施肥的补充。适宜时期：作物生长后期、根系吸收能力下降时、出现缺素症时。常用叶面肥：尿素(0.5-1%)、磷酸二氢钾(0.3%)、硼砂(0.1-0.2%)。喷施时间：傍晚或阴天，避开高温。",
            metadata={"category": "fertilizer", "topic": "foliar"}
        ),
        # 土壤管理
        Document(
            page_content="土壤改良技术：酸性土壤施用石灰调节pH值至6.0-7.0；盐碱地增施有机肥、种植耐盐作物；黏重土壤掺沙改良质地；沙质土壤增施有机肥提高保水保肥能力。深翻深度20-30cm，打破犁底层。",
            metadata={"category": "soil", "topic": "amendment"}
        ),
        Document(
            page_content="节水灌溉技术：水稻浅水勤灌，亩均用水量300-400m³；小麦玉米滴灌亩均用水量150-200m³，比漫灌节水50%以上。推广喷灌、微喷灌、水肥一体化技术。灌溉水质标准：pH 5.5-8.5，含盐量<1g/L。",
            metadata={"category": "irrigation", "topic": "water_saving"}
        ),
        # 农机具
        Document(
            page_content="旋耕机使用与维护：旋耕机适用于水旱田整地，耕深12-18cm。使用前检查刀片是否紧固，齿轮箱油位是否正常。作业时先结合动力输出轴，再缓慢降落，严禁急转弯。每工作50小时更换齿轮箱润滑油，季节性作业后彻底清洗保养。",
            metadata={"category": "machinery", "topic": "tillage"}
        ),
        Document(
            page_content="植保无人机操作规范：植保无人机适用于病虫害防治和叶面施肥。作业前检查电池电量、药箱密封性、喷头是否堵塞。飞行高度距作物冠层2-3米，飞行速度3-5米/秒。避免在高温(>35℃)、大风(>4级)、降雨天气作业。作业后清洗药箱、滤网和喷头。",
            metadata={"category": "machinery", "topic": "spraying"}
        ),
    ]

    kb = knowledge_base
    current_count = kb.get_status()["total_documents"]
    if current_count == 0:
        added = kb.add_documents(default_docs)
        logger.info(f"默认农业知识库初始化完成，添加 {added} 个文档片段")
    else:
        logger.info(f"知识库已存在 {current_count} 个文档片段，跳过初始化")
# -*- coding: utf-8 -*-
"""
图像诊断模块 — 病虫害图像分析与辅助识别。

功能：
1. 图片上传与校验（格式/大小）
2. LLM 多模态图像分析（如果模型支持）
3. 规则回退：基于图片元数据和关键词的启发式分析
4. 人工审核标记（100% 图像回答带免责声明）
"""
from __future__ import annotations
import base64
import json
import logging
import re
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# 允许的图片格式
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_BYTES = 10 * 1024 * 1024  # 10MB

# 图片存储目录
IMAGE_STORE_DIR = Path(__file__).resolve().parent / "data" / "image_diagnostics"


@dataclass
class ImageDiagnosis:
    """图像诊断结果。"""
    id: str
    possible_causes: List[str]          # 可能原因列表
    confidence: float                   # 整体置信度 0-1
    analysis: str                       # 分析文本
    recommendations: List[str]          # 建议
    disclaimer: str                     # 免责声明
    requires_human_review: bool = True  # 是否要求人工审核
    mode: str = "rule"                  # rule / llm

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ImageDiagnosisEngine:
    """图像诊断引擎。"""

    def __init__(self, llm=None):
        self.llm = llm

    def validate_image(self, content: bytes, content_type: Optional[str]) -> Optional[str]:
        """校验图片，返回错误信息（None 表示通过）。

        Parameters
        ----------
        content : bytes
            图片二进制内容。
        content_type : str, optional
            图片 MIME 类型。

        Returns
        -------
        str or None
            错误信息，None 表示校验通过。
        """
        # 校验 MIME 类型
        if content_type and content_type not in ALLOWED_IMAGE_TYPES:
            return f"不支持的图片格式: {content_type}，仅支持 JPG/PNG/WebP"
        # 校验大小
        if len(content) > MAX_IMAGE_BYTES:
            return "图片超过 10MB 大小限制"
        if len(content) == 0:
            return "图片内容为空"
        # 校验魔数（简化版）
        if content[:3] == b"\xff\xd8\xff":  # JPEG
            pass
        elif content[:8] == b"\x89PNG\r\n\x1a\n":  # PNG
            pass
        elif content[:4] == b"RIFF":  # WebP
            pass
        elif content_type:
            pass  # 有 MIME 类型时放宽魔数校验
        else:
            return "无法识别的图片格式"
        return None

    def analyze(
        self,
        content: bytes,
        content_type: str = "image/jpeg",
        description: str = "",
        crop: str = "",
    ) -> ImageDiagnosis:
        """分析图片。

        Parameters
        ----------
        content : bytes
            图片二进制内容。
        content_type : str
            图片 MIME 类型。
        description : str
            用户补充描述。
        crop : str
            作物名称。

        Returns
        -------
        ImageDiagnosis
            诊断结果。
        """
        # 优先使用 LLM 多模态分析
        if self.llm:
            try:
                result = self._analyze_with_llm(content, content_type, description, crop)
                if result:
                    return result
            except Exception as exc:
                logger.warning("LLM 图像分析失败，回退到规则模式: %s", exc)
        # 规则回退
        return self._analyze_with_rules(content, description, crop)

    def _analyze_with_llm(
        self,
        content: bytes,
        content_type: str,
        description: str,
        crop: str,
    ) -> Optional[ImageDiagnosis]:
        """使用 LLM 多模态分析图片。

        注意：仅当 LLM 提供商支持图像输入时可用。
        """
        # 这里假设 LLM 支持 OpenAI 格式的图像输入
        base64_image = base64.b64encode(content).decode("utf-8")
        prompt = f"""你是一个农业病虫害诊断专家。请分析这张植物图片。

用户描述: {description or "无"}
作物: {crop or "未知"}

请以 JSON 格式输出：
```json
{{
  "possible_causes": ["可能原因1", "可能原因2"],
  "confidence": <0-1 置信度>,
  "analysis": "分析文本",
  "recommendations": ["建议1", "建议2"]
}}
```

要求：
- 仅作为辅助识别，不作为确诊
- 置信度低于 0.7 时明确说明需要人工确认
- 危险/扩散情况建议咨询当地农技站"""

        # 构建多模态消息
        try:
            response = self.llm.invoke([
                {"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:{content_type};base64,{base64_image}"}},
                ]}
            ])
            text = response.content if hasattr(response, 'content') else str(response)
            json_match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
            if not json_match:
                json_match = re.search(r"(\{.*\})", text, re.DOTALL)
            if not json_match:
                return None
            data = json.loads(json_match.group(1))
            return ImageDiagnosis(
                id=f"img_diag_{uuid.uuid4().hex[:12]}",
                possible_causes=data.get("possible_causes", []),
                confidence=float(data.get("confidence", 0.5)),
                analysis=data.get("analysis", ""),
                recommendations=data.get("recommendations", []),
                disclaimer="⚠️ 本结果为 AI 辅助识别，仅供参考，不能作为确诊依据。请结合现场情况并咨询当地农技人员确认。",
                requires_human_review=True,
                mode="llm",
            )
        except Exception as exc:
            logger.warning("LLM 多模态分析异常: %s", exc)
            return None

    def _analyze_with_rules(self, content: bytes, description: str, crop: str) -> ImageDiagnosis:
        """规则模式分析（无 LLM 时回退）。

        基于用户描述的关键词启发式分析。
        """
        text = f"{description} {crop}"

        # 症状关键词匹配
        symptom_rules = [
            (r"叶片.*斑点|斑点|黄斑|褐斑", "叶斑病类（如稻瘟病、纹枯病等叶部病害）", "观察斑点形状、边缘、有无霉层，咨询当地农技站"),
            (r"叶片.*发黄|发黄|黄化|褪绿", "营养失调或缺素症（如缺氮、缺钾）", "检查施肥记录，建议取土检测"),
            (r"卷叶|扭曲|皱缩", "病毒病或害虫为害（如蚜虫、飞虱传播）", "检查叶背是否有小型害虫，观察扩散情况"),
            (r"根部.*腐烂|烂根|根腐", "根部病害（如根腐病）或积水渍害", "检查排水情况，减少灌溉，咨询农技人员"),
            (r"白粉|粉状|霉层", "白粉病或霉病类", "观察粉状物分布，防治前确认病害类型"),
            (r"枯死|枯萎|干枯", "枯萎病或干旱胁迫", "检查土壤墒情，观察发病范围"),
            (r"虫|虫子|食叶|缺口", "害虫为害（如蚜虫、螟虫等）", "观察虫体形态，记录为害部位"),
            (r"霜冻|冻害|低温", "低温冻害", "采取覆盖保温措施，观察恢复情况"),
        ]

        matched = []
        for pattern, cause, recommendation in symptom_rules:
            if re.search(pattern, text):
                matched.append((cause, recommendation))

        if not matched:
            return ImageDiagnosis(
                id=f"img_diag_{uuid.uuid4().hex[:12]}",
                possible_causes=["信息不足，无法通过描述判断"],
                confidence=0.3,
                analysis="当前描述信息有限，无法确定具体问题。建议补充作物、生育期、症状细节和田间环境信息。",
                recommendations=[
                    "补充清晰的照片（叶片正面、背面、整体植株）",
                    "描述症状出现的时间和扩散速度",
                    "咨询当地农技站获取专业诊断",
                ],
                disclaimer="⚠️ 本结果为 AI 辅助识别，仅供参考，不能作为确诊依据。",
                requires_human_review=True,
                mode="rule",
            )

        causes = [m[0] for m in matched]
        recommendations = [m[1] for m in matched[:3]]
        recommendations.append("以上仅为初步判断，请咨询当地农技站确认后再采取措施")

        return ImageDiagnosis(
            id=f"img_diag_{uuid.uuid4().hex[:12]}",
            possible_causes=causes,
            confidence=min(0.9, 0.5 + 0.1 * len(matched)),
            analysis=f"基于描述匹配到 {len(matched)} 类可能问题。注意：图片诊断存在不确定性，需结合现场信息确认。",
            recommendations=recommendations,
            disclaimer="⚠️ 本结果为 AI 辅助识别，仅供参考，不能作为确诊依据。请结合现场情况并咨询当地农技人员确认。",
            requires_human_review=True,
            mode="rule",
        )


# 全局实例
image_engine = ImageDiagnosisEngine()
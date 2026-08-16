from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import nbformat as nbf


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_ROOT = ROOT / "notebooks"


def md(text: str) -> nbf.NotebookNode:
    return nbf.v4.new_markdown_cell(dedent(text).strip())


def code(text: str) -> nbf.NotebookNode:
    return nbf.v4.new_code_cell(dedent(text).strip())


MISSION_CARDS = {
    "phase1": {
        "name": "Phase 1 总览：建立证据地基",
        "role": "文档考古组组长",
        "story": "先把散落文件整理成每一条都能回到原文的证据单元，后面的搜索比赛才有可信的赛道。",
        "goal": "完成从 PDF/Markdown 到稳定 chunks.json 的第一条可复现流水线。",
        "artifact": "文档考古工具总览 + chunks.json",
        "reward": "解锁徽章：证据地基组长",
    },
    "phase2": {
        "name": "Phase 2 总览：赢下搜索对决",
        "role": "检索战术总教练",
        "story": "同一个问题会被不同搜索方法排出不同顺序。你要用可解释 baseline 和指标判断谁真的找到了证据。",
        "goal": "完成 BM25、Dense 机制实验、RRF 融合和 qrels 质量评估。",
        "artifact": "Hybrid 检索对决总览 + 质量成绩单",
        "reward": "解锁徽章：检索战术总教练",
    },
    "phase3": {
        "name": "Phase 3 总览：速度与质量双榜",
        "role": "性能与质量分析师",
        "story": "更快的搜索不一定更有用。你要把速度、召回、排名和参数变化放到同一张实验板上。",
        "goal": "用可复现 benchmark 选择一个有证据支撑的配置。",
        "artifact": "Benchmark 总览 + 质量-速度结论",
        "reward": "解锁徽章：性能与质量分析师",
    },
    "phase4": {
        "name": "Phase 4 总览：上线证据工作台",
        "role": "Mini RAG 发布负责人",
        "story": "最后一公里是让真实用户能查询、能看到引用、遇到无证据时能得到诚实回答。",
        "goal": "把解析、检索、评估和 API 组合成可验收的 Mini RAG 产品。",
        "artifact": "可启动、可测试、可追溯的 Evidence Desk",
        "reward": "解锁徽章：Evidence Desk 发布官",
    },
    "phase0": {
        "name": "Mission Control：接手第一宗案件",
        "role": "知识库调查员实习生",
        "story": "案件资料散落在 Markdown、PDF 和实验记录里。你的第一项任务是建立调查地图，知道每条证据从哪里来、要交给谁。",
        "goal": "建立一份可复现的项目任务档案，并说清四阶段如何组成一条产品链路。",
        "artifact": "项目任务地图 + 第一份案件档案",
        "reward": "解锁徽章：案件接收员",
    },
    "phase1.1": {
        "name": "Phase 1.1：文档考古现场",
        "role": "文档考古员",
        "story": "你在现场找到了一份没有标签的 Markdown 案件材料。搜索系统不能只拿到正文，还必须知道证据来自哪个文件。",
        "goal": "把原始文件变成带 source、page 和 metadata 的第一份 Document。",
        "artifact": "文档清单 + 可追溯 Document 记录",
        "reward": "解锁徽章：来源追踪员",
    },
    "phase1.2": {
        "name": "Phase 1.2：边界救援任务",
        "role": "证据切片工程师",
        "story": "一条关键线索正好卡在两个 Chunk 的边界上。切得太大难搜索，切得太小又会把上下文拆散。",
        "goal": "用实验理解 chunk_size、overlap 和分隔符如何决定证据边界。",
        "artifact": "Chunk 边界实验板 + 边界救援结论",
        "reward": "解锁徽章：边界救援员",
    },
    "phase1.3": {
        "name": "Phase 1.3：证据流水线交付",
        "role": "知识库流水线负责人",
        "story": "调查组不能手工处理每一份文件。你要把解析、切分、稳定 ID 和 JSON 交付串成可重复执行的流水线。",
        "goal": "从输入目录生成下游检索可以直接读取的 chunks.json。",
        "artifact": "可复现的 Phase 1 文档考古工具",
        "reward": "解锁徽章：流水线交付官",
    },
    "phase2.1": {
        "name": "Phase 2.1：关键词搜索擂台",
        "role": "搜索擂台选手",
        "story": "第一场比赛是 BM25。它不会读心，却能清楚告诉你哪些词命中了、稀有词为什么更有价值。",
        "goal": "从零理解 token、TF、DF、IDF，并建立可解释的 BM25 baseline。",
        "artifact": "BM25 搜索排行榜 + 命中词解释",
        "reward": "解锁徽章：关键词侦探",
    },
    "phase2.2": {
        "name": "Phase 2.2：检索双雄对决",
        "role": "排名策略师",
        "story": "关键词检索擅长精确命中，向量检索擅长语义相近。你要让两支队伍先各自展示排名，再观察 RRF 如何做裁判。",
        "goal": "用二维直觉实验理解 cosine 和 RRF，并诚实区分模拟结果与真实模型结果。",
        "artifact": "BM25 vs Dense vs Hybrid 对决板",
        "reward": "解锁徽章：融合策略师",
    },
    "phase2.3": {
        "name": "Phase 2.3：检索裁判席",
        "role": "搜索质量裁判",
        "story": "排行榜看起来漂亮不代表真的找到了证据。你要用 qrels 给每个 Query 判分，并找出最值得修复的失败样本。",
        "goal": "计算 Recall/MRR，形成可解释的检索质量基线。",
        "artifact": "检索挑战赛成绩单 + 失败 Query 案例",
        "reward": "解锁徽章：证据裁判",
    },
    "phase3.1": {
        "name": "Phase 3.1：检索竞速计时台",
        "role": "性能计时工程师",
        "story": "用户说搜索有点慢，但‘感觉快’不是工程证据。你要区分预热、稳定运行、平均延迟和尾延迟。",
        "goal": "建立可复现的 mean、P50、P95 计时基线。",
        "artifact": "检索速度计时卡",
        "reward": "解锁徽章：延迟计时员",
    },
    "phase3.2": {
        "name": "Phase 3.2：参数改装实验室",
        "role": "实验车辆调参师",
        "story": "你有一台会漏证据的搜索引擎。现在只能一次改一个旋钮，找出速度、召回和上下文噪声之间更值得采用的配置。",
        "goal": "用单变量实验比较 top-k、chunk_size 和 overlap，形成有边界的工程结论。",
        "artifact": "质量-速度 Pareto 实验板",
        "reward": "解锁徽章：单变量实验员",
    },
    "phase3.3": {
        "name": "Phase 3.3：证据实验报告厅",
        "role": "技术调查记者",
        "story": "董事会只看结论，但工程团队需要知道数字的适用范围、失败原因和不能声称的事情。",
        "goal": "把实验数据写成一页能被真实观众审阅的性能与质量报告。",
        "artifact": "Phase 3 实验报告 + 一条简历级结论",
        "reward": "解锁徽章：证据报告员",
    },
    "phase4.1": {
        "name": "Phase 4.1：API 合同审讯室",
        "role": "产品接口审查员",
        "story": "搜索能力要交给别人使用，接口就像一份对外承诺：输入什么、返回什么、错误如何表达，都不能靠猜。",
        "goal": "写清 HTTP、JSON、状态码和 citation contract，并用测试保护它。",
        "artifact": "可验证的 API 合同清单",
        "reward": "解锁徽章：接口审查员",
    },
    "phase4.2": {
        "name": "Phase 4.2：搭建证据工作台",
        "role": "Mini RAG 产品工程师",
        "story": "现在把前面所有证据接到一张工作台：用户提出问题，系统检索原文，并把能点击回去的证据交还给用户。",
        "goal": "完成一个无外部 API Key 也能工作的 evidence-first Mini RAG 服务。",
        "artifact": "可运行的 Evidence Desk API",
        "reward": "解锁徽章：证据工作台建造师",
    },
    "phase4.3": {
        "name": "Phase 4.3：Demo Day 最终审判",
        "role": "项目发布负责人",
        "story": "真实观众不会为你背诵术语。你要现场展示一次查询、引用、无证据 fallback 和自动化验收。",
        "goal": "完成从输入文件到可追溯回答的最终演示，并留下可复现记录。",
        "artifact": "最终 Demo 记录 + 面试级项目展示",
        "reward": "解锁徽章：Evidence Quest 通关者",
    },
}


def infer_mission_key(cells: list[nbf.NotebookNode]) -> str:
    """根据 Notebook 标题选择任务卡；标题是教学内容的稳定标识。"""
    title = cells[0].source if cells else ""
    for marker in ("Phase 4.3", "Phase 4.2", "Phase 4.1", "Phase 3.3", "Phase 3.2", "Phase 3.1", "Phase 2.3", "Phase 2.2", "Phase 2.1", "Phase 1.3", "Phase 1.2", "Phase 1.1", "Phase 4：", "Phase 3：", "Phase 2：", "Phase 1：", "Phase 0"):
        if marker in title:
            return marker.lower().replace("phase ", "phase").replace("：", "").replace(":", "")
    return "phase0"


def mission_card(key: str) -> nbf.NotebookNode:
    """生成每课开头的剧情、Goal、作品和通关条件。"""
    mission = MISSION_CARDS[key]
    return md(f"""
    ## Evidence Quest 任务卡：{mission['name']}

    **你的身份：** {mission['role']}  
    **案件背景：** {mission['story']}

    ### 本关专业 Goal

    {mission['goal']}

    ### 你要交付的作品

    **{mission['artifact']}**

    ### 通关判定

    - 先运行带逐行中文注释的示范，预测输出，再自己重新敲一遍关键代码。
    - 至少改变一个参数或输入，记录它为什么改变了结果。
    - 完成末尾的 Boss Challenge，并能解释一个失败样本。
    - 把本关产物交给下一关，而不是把代码停留在 Notebook 屏幕上。

    **通关奖励：** {mission['reward']}  
    **学习节奏：** 看故事 -> 跟敲一小段 -> 观察输出 -> 自己改写 -> 验收作品。
    """)


def quest_runtime(key: str) -> nbf.NotebookNode:
    """生成离线任务看板；不依赖 API Key，也不隐藏核心学习逻辑。"""
    return code(f"""
    # 定义本关任务编号，后面的记录会用它区分不同阶段。
    QUEST_STAGE = {key!r}

    # 定义学习者可以持续保存的案件档案路径。
    QUEST_PROFILE_PATH = ROOT / "data" / "processed" / "evidence_quest_profile.json"

    # 如果第一次打开课程还没有档案，就使用一个安全的默认案件。
    default_profile = {{
        "case_name": "校园知识库失踪案",
        "audience": "需要快速查证资料的同学",
        "must_answer": "证据来自哪里，能否回到原文？",
        "must_refuse": "检索结果没有证据时必须说不知道",
        "xp": 0,
        "badges": [],
    }}

    # 检查任务档案是否已经由 Mission Control 创建。
    if QUEST_PROFILE_PATH.is_file():
        # 读取学员自己的案件主题，让所有 Notebook 共享同一个故事。
        quest_profile = json.loads(QUEST_PROFILE_PATH.read_text(encoding="utf-8"))
    else:
        # 没有档案时复制默认值，避免直接修改模板字典。
        quest_profile = dict(default_profile)

    # 计算当前累计经验值；错误值按 0 处理，避免看板阻塞学习。
    quest_xp = int(quest_profile.get("xp", 0))

    # 读取已经获得的徽章，并复制成当前 Notebook 的列表。
    quest_badges = list(quest_profile.get("badges", []))

    # 用可见的文字看板告诉学习者自己正在解决哪个真实问题。
    print("Evidence Quest / 当前关卡:", QUEST_STAGE)
    print("案件:", quest_profile.get("case_name", default_profile["case_name"]))
    print("服务对象:", quest_profile.get("audience", default_profile["audience"]))
    print("累计 XP:", quest_xp, "| 徽章:", ", ".join(quest_badges) if quest_badges else "尚未获得")
    """)


def boss_challenge(key: str) -> tuple[nbf.NotebookNode, nbf.NotebookNode]:
    """生成默认注释的独立挑战，让学员重新敲一遍而不是复制答案。"""
    challenge_text = {
        "phase0": "把案件的服务对象和‘必须说不知道’条件改成你自己的真实主题，并重新生成档案。",
        "phase1.1": "不看上面的示范，重新构造一个包含 text、source、page、metadata 的 Document。",
        "phase1.2": "只把 overlap 改成另一个值，预测 Chunk 数、边界和重复文本会如何变化。",
        "phase1.3": "把输入目录换成你准备的一份 Markdown，检查稳定 chunk_id 是否在两次运行中一致。",
        "phase2.1": "挑一个稀有词和一个常见词，比较它们的 IDF，并解释哪个更能区分案件。",
        "phase2.2": "手算两份排名的 RRF 分数，观察共同出现的文档为什么得到更高融合排名。",
        "phase2.3": "新增一道 Query 和 qrels，先预测 Recall/MRR，再运行评估检查预测是否正确。",
        "phase3.1": "把 warmup 次数和测量次数各改一次，说明为什么冷启动和稳定延迟不能混报。",
        "phase3.2": "只改 top_k，画出质量与延迟变化，并写一句‘在什么范围内结论成立’。",
        "phase3.3": "从报告中挑一条数字，补上数据版本、参数、环境和不能声称的内容。",
        "phase4.1": "为一个空 Query 或不存在的 source 写出预期状态码和错误 JSON。",
        "phase4.2": "提出一个没有证据的问题，确认系统返回不知道，而不是编造答案。",
        "phase4.3": "用一个真实观众会问的问题跑完整 Demo，并记录 citation 的 chunk_id、source、page。",
        "phase1": "从输入目录完整跑一次解析和分块，并解释一个 Chunk 如何回到原文。",
        "phase2": "给同一个 Query 展示两种排名，解释为什么最终选择某个检索 baseline。",
        "phase3": "把一个参数变化同时放到质量表和延迟表，写出有边界的工程结论。",
        "phase4": "从用户 Query 开始展示完整链路，并证明无证据时系统不会编造。",
    }[key]
    return (
        md(f"""
        ## Boss Challenge：{challenge_text}

        下面是**故意保持注释状态**的跟敲模板。请先自己写，再取消注释逐行运行；不要把它当成需要复制的答案。
        """),
        code("\n".join([
            "# 第 1 行：先写出本挑战需要的新变量或新输入。",
            "# challenge_input = ...",
            "",
            "# 第 2 行：调用本课已经学会的函数或模块。",
            "# challenge_result = ...",
            "",
            "# 第 3 行：打印一个中间结果，先观察再下结论。",
            "# print(challenge_result)",
            "",
            "# 第 4 行：写一个断言，把你的理解变成机器可检查的条件。",
            "# assert ...",
        ])),
    )


def checkpoint_cells(key: str) -> tuple[nbf.NotebookNode, nbf.NotebookNode]:
    """在每课结尾显示作品是否已经出现在磁盘上。"""
    artifact_paths = {
        "phase0": ["data/processed/project_orientation.json", "data/processed/evidence_quest_profile.json"],
        "phase1.1": ["data/processed/document_inventory.json"],
        "phase1.2": ["data/processed/phase1_chunk_experiment.json"],
        "phase1.3": ["data/processed/chunks.json", "phase1_doc_parser/output/chunks.json"],
        "phase2.1": ["data/processed/phase2_bm25_baseline.json"],
        "phase2.2": ["data/processed/phase2_rrf_demo.json"],
        "phase2.3": ["data/processed/phase2_evaluation.json"],
        "phase3.1": ["data/processed/phase3_timing_baseline.json"],
        "phase3.2": ["data/processed/phase3_single_variable_experiments.json"],
        "phase3.3": ["docs/phase3_baseline_report.md"],
        "phase4.1": ["data/processed/phase4_api_contract_record.json"],
        "phase4.2": ["data/processed/phase4_service_record.json"],
        "phase4.3": ["data/processed/phase4_acceptance_record.json"],
        "phase1": ["data/processed/chunks.json", "phase1_doc_parser/output/chunks.json"],
        "phase2": ["data/processed/phase2_evaluation.json", "data/processed/phase2_rrf_demo.json"],
        "phase3": ["docs/phase3_baseline_report.md", "data/processed/phase3_timing_baseline.json"],
        "phase4": ["data/processed/phase4_acceptance_record.json"],
    }[key]
    candidates = repr(artifact_paths)
    return (
        md("""
        ## 作品检查站

        作品不是‘我运行过代码’，而是别人可以在文件浏览器中找到、下一阶段可以读取、你能解释生成过程的证据。下面的检查只报告事实，不替你假装通关。
        """),
        code(f"""
        # 列出本关应该产生的作品路径。
        quest_artifact_candidates = {candidates}

        # 把相对路径转换为项目根目录下的绝对路径。
        quest_artifact_paths = [ROOT / path for path in quest_artifact_candidates]

        # 只保留已经真正写入磁盘的作品。
        quest_existing_artifacts = [str(path.relative_to(ROOT)) for path in quest_artifact_paths if path.is_file()]

        # 保存一个不依赖外部服务的本关检查结果，方便复盘。
        quest_checkpoint = {{"stage": QUEST_STAGE, "existing_artifacts": quest_existing_artifacts}}

        # 打印检查结果，让学习者知道下一步是继续学习还是补交作品。
        print("本关作品:", quest_existing_artifacts if quest_existing_artifacts else "还没有生成，请回到交付单元格")
        """),
    )


def make_notebook(cells: list[nbf.NotebookNode]) -> nbf.NotebookNode:
    # 根据首个标题确定本 Notebook 对应的任务卡。
    mission_key = infer_mission_key(cells)

    # 找到 SETUP 代码单元格，任务运行时必须在 ROOT 和 json 创建之后执行。
    setup_index = next((index for index, cell in enumerate(cells) if cell.cell_type == "code"), len(cells) - 1)

    # 插入任务卡、任务看板、Boss Challenge 和作品检查站。
    enhanced_cells = list(cells)
    enhanced_cells.insert(1, mission_card(mission_key))
    enhanced_cells.insert(setup_index + 2, quest_runtime(mission_key))
    challenge_markdown, challenge_code = boss_challenge(mission_key)
    enhanced_cells.extend([challenge_markdown, challenge_code])
    checkpoint_markdown, checkpoint_code = checkpoint_cells(mission_key)
    enhanced_cells.extend([checkpoint_markdown, checkpoint_code])

    notebook = nbf.v4.new_notebook()
    notebook.cells = enhanced_cells
    notebook.metadata = {
        "kernelspec": {
            "display_name": "Python 3 (ai-rag-internship)",
            "language": "python",
            "name": "python3",
        },
        "language_info": {"name": "python", "version": "3.12"},
    }
    return notebook


SETUP = """
# 导入 Path，用它表示跨平台的文件路径。
from pathlib import Path

# 导入 json，用它读取和保存项目的结构化数据。
import json

# 导入 sys，用它把项目根目录加入 Python 的模块搜索路径。
import sys


# 定义一个函数，负责从当前工作目录向上查找项目根目录。
def find_project_root() -> Path:
    # 把当前目录和它的所有父目录放进候选列表。
    candidates = [Path.cwd(), *Path.cwd().parents]

    # 逐个检查候选目录是否包含本项目的两个核心模块目录。
    for candidate in candidates:
        # 找到同时存在的目录时，返回这个候选目录。
        if (candidate / "phase1_doc_parser").is_dir() and (candidate / "phase2_semantic_search").is_dir():
            return candidate

    # 如果所有候选目录都不符合，说明 Jupyter 启动位置不在项目内。
    raise RuntimeError("找不到项目根目录，请从 ai-search-rag-internship 启动 JupyterLab")


# 执行查找函数，得到当前项目根目录。
ROOT = find_project_root()

# 如果项目根目录还不在模块搜索路径中，就把它添加进去。
if str(ROOT) not in sys.path:
    # 把项目根目录插入最前面，确保导入的是当前项目代码。
    sys.path.insert(0, str(ROOT))

# 打印根目录，帮助学习者确认 Notebook 没有在错误目录运行。
print("项目根目录:", ROOT)
"""


def build_mission_control() -> nbf.NotebookNode:
    """创建兴趣驱动的入口：先选择真实观众和案件，再进入技术阶段。"""
    return make_notebook([
        md("""
        # Evidence Quest：Mission Control

        欢迎接案。你不是来背诵 RAG 术语的，而是要为一个真实的人做出一台能查证资料的证据工作台。

        本 Notebook 是整个项目的任务控制台：先选择案件主题、服务对象和必须拒答的边界，再把它保存成后续所有阶段共同使用的项目合同。
        """),
        md("""
        ## 先决定作品给谁用

        请选择一个你愿意持续追问的问题领域，例如：课程资料、游戏世界观、旅行攻略、开源项目文档或自己的学习笔记。主题不需要宏大，但必须能让真实用户提出至少 5 个问题。

        **重要原则：** 用户问题和‘不知道’边界先于模型。没有这两项，后面的检索指标和引用都不知道在保护什么。
        """),
        code(SETUP),
        code("""
        # 定义几个可直接开始的案件主题；学习者也可以在后面替换成自己的主题。
        case_options = [
            {"name": "校园知识库失踪案", "audience": "需要复习课程资料的同学", "question": "这条知识来自哪份资料？", "refusal": "资料里没有证据时必须说不知道"},
            {"name": "游戏世界观考据案", "audience": "想核对设定的玩家", "question": "这个角色或事件在原文哪一段？", "refusal": "不能把猜测当成官方设定"},
            {"name": "个人学习资料侦探案", "audience": "希望快速回顾笔记的自己", "question": "我以前在哪个文件记录过这个概念？", "refusal": "找不到原文时必须返回待补证据"},
        ]

        # 选择一个案件编号；先用 1 跑通，再改成 2 或 3 观察整个项目的主题变化。
        selected_case_number = 1

        # 检查编号是否落在选项范围内，尽早发现拼写或输入错误。
        assert 1 <= selected_case_number <= len(case_options)

        # 根据人类可读的编号取出案件配置。
        selected_case = case_options[selected_case_number - 1]

        # 写下项目必须遵守的用户故事和拒答边界。
        quest_profile = {
            "case_name": selected_case["name"],
            "audience": selected_case["audience"],
            "must_answer": selected_case["question"],
            "must_refuse": selected_case["refusal"],
            "questions": [
                selected_case["question"],
                "哪些词能准确找到证据？",
                "不同切分方式会不会漏掉线索？",
                "搜索变快后质量有没有下降？",
                "用户能不能点击引用回到原文？",
            ],
            "xp": 0,
            "badges": ["案件接收员"],
        }

        # 创建处理数据目录，确保第一次运行也能保存档案。
        profile_directory = ROOT / "data" / "processed"
        profile_directory.mkdir(parents=True, exist_ok=True)

        # 定义后续 Notebook 读取的统一项目合同路径。
        profile_path = profile_directory / "evidence_quest_profile.json"

        # 以 UTF-8 保存中文案件档案，缩进让它也能作为作品展示。
        profile_path.write_text(json.dumps(quest_profile, ensure_ascii=False, indent=2), encoding="utf-8")

        # 打印案件合同，让学习者确认自己不是在为抽象的 demo 学习。
        print("已接手案件:", quest_profile["case_name"])
        print("服务对象:", quest_profile["audience"])
        print("必须回答:", quest_profile["must_answer"])
        print("必须拒答:", quest_profile["must_refuse"])
        print("已保存:", profile_path)

        # 只有关键字段齐全，后面的阶段才允许开始。
        assert {"case_name", "audience", "must_answer", "must_refuse", "questions"} <= quest_profile.keys()
        """),
        md("""
        ## 你的第一张案件卡

        请在下方 Markdown 中写下：

        - 真实观众是谁；
        - 观众会问的 5 个问题；
        - 哪一种回答必须回到原文；
        - 哪一种情况必须明确说“不知道”。

        这张卡会直接影响后面的 qrels、Boss Query 和 API 验收。它不是装饰性的产品文案，而是测试标准的来源。
        """),
        code("""
        # 读取刚刚保存的案件档案，确认跨 Notebook 的项目合同可复用。
        saved_profile = json.loads(profile_path.read_text(encoding="utf-8"))

        # 打印五道挑战题，后面的检索评估会逐题使用它们。
        for question_number, question in enumerate(saved_profile["questions"], start=1):
            print(f"Query {question_number}: {question}")

        # 交付标准是问题清单足够驱动后续实验，而不是只存在一个标题。
        assert len(saved_profile["questions"]) >= 5
        """),
        md("""
        ## Mission Control 通关

        现在你已经有了一个可展示的项目起点：一份为真实观众设计的案件合同。接下来每个 Phase 都会给这宗案件增加新的能力，最后合并成 Evidence Desk。
        """),
    ])


def build_orientation() -> nbf.NotebookNode:
    return make_notebook([
        md("""
        # Phase 0：认识项目、环境和完整链路

        这一课不急着写 RAG 算法。先建立一张工程地图：每个目录解决什么问题，每个阶段的输入和输出是什么，为什么这些阶段必须按顺序连接。

        ## 本课交付

        - 确认 Jupyter 使用的是 `ai-rag-internship` 环境。
        - 找到项目根目录和四个阶段模块。
        - 看懂一条从原始 Markdown 到 API 引用的完整数据流。
        - 生成 `data/processed/project_orientation.json` 作为学习起点记录。

        **默认基础：** 会一点 Python 基础，但不了解机器学习和 RAG。每个代码单元格都只解决一个小问题。
        """),
        md("""
        ## 1. 为什么先认识项目？

        RAG 不是一个单独的函数，而是一条流水线。如果不知道流水线的边界，遇到错误时就会把所有问题都归因于“模型不够好”。本项目故意拆成四层：

        ```text
        Phase 1  文件 -> 可追溯 Chunk
        Phase 2  Chunk -> 排名结果
        Phase 3  排名结果 -> 质量/性能证据
        Phase 4  证据 -> 可调用的 API 产品
        ```

        以后每个 Notebook 都会回答三个问题：输入是什么、这一步改变了什么、输出交给谁。
        """),
        code(SETUP),
        md("""
        ### 逐句说明这段启动代码

        - `Path` 让路径拼接不依赖 Windows 或 Linux 的斜杠写法。
        - `json` 让我们保存可重复读取的实验数据，而不是只看屏幕输出。
        - `sys.path` 决定 Python 能否导入项目中的 `phase1_doc_parser` 等模块。
        - `find_project_root()` 用项目目录特征定位根目录，避免 Notebook 从不同位置启动就失效。
        """),
        code("""
        # 定义本项目中必须存在的四个阶段目录。
        phase_directories = [
            "phase1_doc_parser",
            "phase2_semantic_search",
            "phase3_optimization_eval",
            "phase4_mini_rag_system",
        ]

        # 逐个构造阶段目录的绝对路径。
        phase_paths = [ROOT / directory for directory in phase_directories]

        # 打印每个目录是否存在，先确认工程骨架没有缺失。
        for path in phase_paths:
            # 输出目录名和布尔结果，帮助定位环境问题。
            print(path.name, "exists=", path.is_dir(), "path=", path)

        # 只有四个阶段都存在，后续 Notebook 才有意义。
        assert all(path.is_dir() for path in phase_paths)

        # 输出环境检查通过的结果。
        print("项目骨架检查通过。")
        """),
        code("""
        # 定义项目中用于教学的原始文档目录。
        input_directory = ROOT / "phase1_doc_parser" / "examples" / "input"

        # 找出原始目录中的所有文件，并按文件名排序保证输出稳定。
        input_files = sorted(path for path in input_directory.iterdir() if path.is_file())

        # 打印输入目录，确认数据从哪里开始进入系统。
        print("输入目录:", input_directory)

        # 逐个打印文件名和扩展名，建立对数据类型的直觉。
        for path in input_files:
            # suffix 表示文件扩展名，例如 .md 或 .pdf。
            print({"name": path.name, "suffix": path.suffix.lower(), "bytes": path.stat().st_size})

        # 确保教学数据至少包含一个文件。
        assert input_files
        """),
        md("""
        ## 2. 把目录结构翻译成数据流

        目录只是工程组织方式，数据流才是系统真正的逻辑。下面用 Python 字典写出一份“项目合同”：每个阶段明确输入、处理和输出。字典不是生产配置，而是帮助你把抽象概念落到字段上。
        """),
        code("""
        # 为每个阶段记录输入、核心处理和交付物。
        project_contract = {
            "phase1": {"input": "PDF/Markdown/TXT", "process": "parse + split", "output": "chunks.json"},
            "phase2": {"input": "chunks.json", "process": "BM25/Dense/RRF", "output": "rankings + qrels metrics"},
            "phase3": {"input": "rankings + qrels", "process": "benchmark + error analysis", "output": "experiment records"},
            "phase4": {"input": "validated knowledge base", "process": "FastAPI orchestration", "output": "search/chat citations"},
        }

        # 逐行打印合同，让每个阶段的边界可见。
        for phase_name, contract in project_contract.items():
            # 输出阶段名和它的输入、处理、输出。
            print(phase_name, "->", contract)

        # 确认每个阶段都写明了三类关键信息。
        assert all({"input", "process", "output"} <= contract.keys() for contract in project_contract.values())
        """),
        md("""
        ## 3. 第一次导入：从项目代码得到一个真实结果

        现在只导入 Phase 1 的解析函数，不实现细节。这里的目的不是跳过学习，而是建立一个基线：之后我们会在细分 Notebook 中手写最小版本，再和这个已经测试过的生产模块对照。
        """),
        code("""
        # 从 Phase 1 模块导入已经测试过的文件解析入口。
        from phase1_doc_parser.parser import parse_file

        # 选择第一个真实教学文件作为观察对象。
        first_file = input_files[0]

        # 调用解析函数，把一个文件统一转换为 ParsedDocument 列表。
        parsed_documents = parse_file(first_file)

        # 打印解析数量，确认函数确实产生了结构化结果。
        print("解析结果数量:", len(parsed_documents))

        # 查看第一份结果的字段，建立 Document 数据结构的直觉。
        print(parsed_documents[0])

        # 确保解析结果不为空，避免拿空数据继续学习。
        assert parsed_documents
        """),
        md("""
        ## 4. 保存学习起点

        记录环境和项目合同，是为了让后续实验知道自己从什么状态开始。之后的报告会继续保存参数、数据规模和指标；没有这些信息，数字不能复现。
        """),
        code("""
        # 创建项目处理数据目录；目录已经存在时不会报错。
        orientation_directory = ROOT / "data" / "processed"
        orientation_directory.mkdir(parents=True, exist_ok=True)

        # 组合本课需要保存的起点信息。
        orientation_record = {
            "project_root": str(ROOT),
            "input_files": [path.name for path in input_files],
            "contract": project_contract,
            "next_notebook": "phase1/01_files_and_documents.ipynb",
        }

        # 选择一个稳定的 JSON 文件作为本课交付物。
        orientation_path = orientation_directory / "project_orientation.json"

        # 以 UTF-8 写入中文，并保留缩进方便人工阅读。
        orientation_path.write_text(json.dumps(orientation_record, ensure_ascii=False, indent=2), encoding="utf-8")

        # 打印交付物路径，方便在 Jupyter 文件浏览器中找到它。
        print("已生成:", orientation_path)
        """),
        md("""
        ## Phase 0 验收

        - [ ] 能说出四个阶段的输入和输出。
        - [ ] 能解释为什么 Phase 2 不能绕过 `chunks.json` 直接读取原始文件。
        - [ ] 能指出项目根目录、原始数据目录和处理数据目录。
        - [ ] 已生成 `project_orientation.json`。

        下一课从最基础的文件读写开始，手动构造一条 Document 记录。
        """),
    ])


def build_phase1_files() -> nbf.NotebookNode:
    return make_notebook([
        md("""
        # Phase 1.1：文件、文本和 Document 数据结构

        ## 目标

        从一个真实 Markdown 文件开始，不调用解析器，先自己观察：路径如何指向文件，文本如何读进内存，为什么需要 `source/page/metadata`。

        **本课交付：** `data/processed/document_inventory.json`。
        """),
        md("""
        ## 先建立三个词的区别

        - **Path**：文件在磁盘上的位置。
        - **Text**：文件内容被读进 Python 后的字符串。
        - **Document**：Text 加上来源、页码和格式等描述信息。

        后面的 Chunk 是从 Document 切出来的更小单位。把这些层次分开，才能知道问题发生在“读文件”还是“切文本”。
        """),
        code(SETUP),
        code("""
        # 指向项目中的 Markdown 教学文件。
        markdown_path = ROOT / "phase1_doc_parser" / "examples" / "input" / "quickstart.md"

        # 确认路径确实指向一个文件，而不是拼错的路径。
        assert markdown_path.is_file()

        # 打印路径的字符串形式，理解 Path 对象和普通字符串的关系。
        print("文件路径:", markdown_path)

        # 打印扩展名，后续可以用它选择不同解析器。
        print("文件扩展名:", markdown_path.suffix)
        """),
        md("""
        ### 逐句理解 `Path`

        `ROOT / "phase1_doc_parser"` 不是字符串拼接，而是 Path 的路径连接操作。它会根据操作系统选择正确的分隔符。`is_file()` 是在真正读取之前做的边界检查，错误会更早、更容易理解。
        """),
        code("""
        # 以 UTF-8 编码读取整个 Markdown 文件。
        raw_text = markdown_path.read_text(encoding="utf-8-sig")

        # 打印原始字符数，观察文件内容进入内存后的规模。
        print("原始字符数:", len(raw_text))

        # 打印前 200 个字符，确认读取到的是正文而不是二进制乱码。
        print(raw_text[:200])

        # 去除首尾空白，得到后续解析使用的正文。
        normalized_text = raw_text.strip()

        # 验证正文没有因为清理而变成空字符串。
        assert normalized_text
        """),
        md("""
        ## 1. 自己构造第一条 Document

        现在先不用 `dataclass`，用普通字典表达一份文档。这样你能直接看到每个字段是什么；下一步再对比生产模块的 `ParsedDocument`。
        """),
        code("""
        # 检查本单元格依赖的前置变量是否已经创建。
        required_variables = {"markdown_path", "normalized_text"}

        # 找出当前 Kernel 中尚未存在的前置变量。
        missing_variables = sorted(name for name in required_variables if name not in globals())

        # 如果学习者跳过了前面的单元格，就给出可执行的修复提示。
        if missing_variables:
            raise RuntimeError("请先从本 Notebook 顶部依次运行前面的代码单元格；缺少变量: " + ", ".join(missing_variables))

        # 创建一个最小 Document 字典，把正文放到 text 字段。
        manual_document = {"text": normalized_text}

        # 加入 source，让未来的检索结果可以回到原始文件。
        manual_document["source"] = str(markdown_path)

        # Markdown 没有 PDF 页码，因此用 None 表示页码不存在。
        manual_document["page"] = None

        # 加入格式信息，让下游知道这段内容来自 Markdown。
        manual_document["metadata"] = {"format": "markdown"}

        # 打印手工构造的数据，观察字段和值的对应关系。
        print(json.dumps(manual_document, ensure_ascii=False, indent=2))

        # 检查四个基础字段都存在。
        assert {"text", "source", "page", "metadata"} <= manual_document.keys()
        """),
        md("""
        ### 为什么不只保存字符串？

        如果只保存 `text`，检索命中后用户看不到来源；如果只保存 `source`，系统没有可供匹配的正文；如果把页码藏在文件名里，PDF 页码和 Markdown 会变得不一致。稳定字段是后续阶段之间的契约。
        """),
        code("""
        # 导入生产解析函数，用相同文件生成正式 Document 对象。
        from phase1_doc_parser.parser import parse_file

        # 运行生产解析器，观察它返回的统一结构。
        parsed_document = parse_file(markdown_path)[0]

        # 打印生产对象，和上面的字典进行逐字段对比。
        print(parsed_document)

        # 检查生产解析器保留了同样的正文和来源信息。
        assert parsed_document.text == normalized_text
        assert parsed_document.source == str(markdown_path)
        assert parsed_document.page is None
        """),
        md("""
        ## 2. 处理格式差异：Markdown heading 是有价值的元数据

        Markdown 的 `# 标题` 不只是正文字符，它可以帮助我们解释 Chunk 所属章节。生产解析器用正则提取标题并存入 `metadata["headings"]`。这里先用一个最小循环观察“逐行处理”是什么。
        """),
        code("""
        # 创建一个空列表，准备保存以 # 开头的标题文本。
        heading_lines = []

        # 按换行把正文拆成一行一行的字符串。
        for line in normalized_text.splitlines():
            # 去除行首尾空白，避免标题结果带有多余空格。
            cleaned_line = line.strip()

            # 只把 Markdown 一级到六级标题识别为 heading。
            if cleaned_line.startswith("#") and not cleaned_line.startswith("######"):
                # 去掉标题符号和左侧空白，只保留标题文字。
                heading_lines.append(cleaned_line.lstrip("#").strip())

        # 输出手工提取的标题，理解元数据如何从正文派生。
        print("手工提取的标题:", heading_lines)

        # 生产解析器应至少返回相同的标题信息。
        assert parsed_document.metadata["headings"]
        """),
        md("""
        ## 3. 生成文档清单

        真实项目通常不是只读一个文件。批处理前先生成清单，可以提前发现空文件、未知扩展名和文件规模异常。这个清单不是最终 Chunk，而是解析阶段的可审计输入记录。
        """),
        code("""
        # 指向所有原始输入文件所在目录。
        input_directory = ROOT / "phase1_doc_parser" / "examples" / "input"

        # 找到目录下的全部普通文件并排序。
        input_files = sorted(path for path in input_directory.iterdir() if path.is_file())

        # 创建空列表，用于保存每个文件的检查结果。
        inventory = []

        # 逐个检查输入文件。
        for path in input_files:
            # 读取文件字节大小，发现明显的空文件。
            byte_size = path.stat().st_size

            # 记录文件名、扩展名、大小和是否被支持。
            inventory.append({"name": path.name, "suffix": path.suffix.lower(), "bytes": byte_size, "supported": path.suffix.lower() in {".md", ".markdown", ".txt", ".pdf"}})

        # 创建数据目录，确保清单有固定存放位置。
        output_directory = ROOT / "data" / "processed"
        output_directory.mkdir(parents=True, exist_ok=True)

        # 指定清单文件路径。
        inventory_path = output_directory / "document_inventory.json"

        # 写入 UTF-8 JSON，保留缩进方便检查。
        inventory_path.write_text(json.dumps(inventory, ensure_ascii=False, indent=2), encoding="utf-8")

        # 打印清单路径和文件数量。
        print("已生成:", inventory_path, "files=", len(inventory))

        # 确保清单覆盖了每一个输入文件。
        assert len(inventory) == len(input_files)
        """),
        md("""
        ## 本课验收

        - [ ] 能解释 Path、Text、Document 的区别。
        - [ ] 能手工构造一条包含 `text/source/page/metadata` 的 Document。
        - [ ] 能说出为什么 Markdown 标题属于有用元数据。
        - [ ] 已生成 `document_inventory.json`。

        下一课不再把整篇文档当成一个字符串，而是从最简单的字符串切片开始写 Chunking。
        """),
    ])


def build_phase1_chunking() -> nbf.NotebookNode:
    return make_notebook([
        md("""
        # Phase 1.2：从字符串切片手写 Chunking

        ## 目标

        先不用项目里的 `RecursiveSplitter`，手写一个最小可理解版本。通过小字符串观察：长度上限、overlap、分隔符和边界错误分别是什么，再接入正式实现。

        **本课交付：** `data/processed/phase1_chunk_experiment.json`。
        """),
        md("""
        ## 1. 最小问题：如何把长文本变短？

        Python 字符串可以用切片 `text[start:end]` 取出一段。`start` 包含在结果中，`end` 不包含在结果中。我们先用固定窗口切，不考虑语义；这是理解算法的地基。
        """),
        code(SETUP),
        code("""
        # 创建一段超过窗口长度的教学文本。
        text = "ABCDEFGHIJ" * 4

        # 设置每个窗口最多保存 10 个字符。
        chunk_size = 10

        # 从第 0 个字符开始取出第一个窗口。
        first_chunk = text[0:chunk_size]

        # 打印原文和第一个窗口，观察切片的边界。
        print("原文:", text)
        print("第一个 Chunk:", first_chunk)

        # 验证窗口长度没有超过上限。
        assert len(first_chunk) == chunk_size
        """),
        code("""
        # 创建空列表，用于保存固定窗口切分结果。
        simple_chunks = []

        # 每次向前移动 chunk_size 个字符，直到走完整个文本。
        for start in range(0, len(text), chunk_size):
            # 根据当前起点取出一个不超过上限的窗口。
            chunk = text[start : start + chunk_size]

            # 把窗口追加到结果列表。
            simple_chunks.append(chunk)

        # 打印所有窗口，观察长文本如何被切成多个独立片段。
        print(simple_chunks)

        # 验证每个窗口都满足长度上限。
        assert all(len(chunk) <= chunk_size for chunk in simple_chunks)
        """),
        md("""
        ## 2. 加入 overlap：为什么窗口不再只向前移动 `chunk_size`？

        如果相邻 Chunk 之间没有共享内容，事实刚好在边界断开时，两个 Chunk 都可能只拿到一半线索。设 `overlap=3`，下一块的起点就从 `start + chunk_size - overlap` 开始。

        注意：overlap 复制的是上下文，不是新增信息。它会增加 Chunk 数或重复内容，因此必须通过检索评估决定是否值得。
        """),
        code("""
        # 设置相邻 Chunk 共享的字符数。
        overlap = 3

        # 计算相邻窗口真正需要移动的步长。
        step = chunk_size - overlap

        # 确保步长为正数，否则循环不会向前推进。
        assert step > 0

        # 创建空列表，用于保存带 overlap 的窗口。
        overlapping_chunks = []

        # 按 step 移动起点，让相邻窗口发生重叠。
        for start in range(0, len(text), step):
            # 取出当前窗口。
            chunk = text[start : start + chunk_size]

            # 保存当前窗口。
            overlapping_chunks.append(chunk)

        # 打印窗口，观察相邻结果的重复部分。
        for index, chunk in enumerate(overlapping_chunks):
            # 输出编号和正文，方便肉眼比较边界。
            print(index, chunk)

        # 验证所有窗口仍然遵守最大长度。
        assert all(len(chunk) <= chunk_size for chunk in overlapping_chunks)
        """),
        md("""
        ### 一个必须理解的边界错误

        当 `overlap >= chunk_size` 时，`step <= 0`，起点不会正常前进。生产实现必须在初始化时拒绝这个参数，而不是等循环卡死。参数校验是算法正确性的一部分。
        """),
        code("""
        # 导入项目中的正式分块器。
        from phase1_doc_parser.splitter import RecursiveSplitter

        # 用非法参数创建分块器，验证正式实现会主动拒绝。
        try:
            # overlap 等于 chunk_size，意味着窗口没有可移动空间。
            RecursiveSplitter(chunk_size=10, overlap=10)
        except ValueError as error:
            # 打印清晰的错误信息，理解失败原因。
            print("参数被拒绝:", error)
        """),
        md("""
        ## 3. 为什么要优先按段落和标点切？

        固定字符窗口简单但可能把一句话切成两半。Recursive Splitter 的思想是：先尝试段落边界，再尝试换行和标点；只有某一段仍然太长时，才降级到更细的分隔符。它在“语义完整”和“长度上限”之间做折中。
        """),
        code("""
        # 定义一段包含段落、换行和中文标点的文本。
        structured_text = "第一段介绍来源。这里还有补充。\\n\\n第二段介绍 overlap；它保留边界上下文。"

        # 使用小窗口强迫分块器展示边界选择过程。
        splitter = RecursiveSplitter(chunk_size=24, overlap=6)

        # 执行正式分块。
        recursive_chunks = splitter.split(structured_text)

        # 逐个打印 Chunk 及字符长度。
        for index, chunk in enumerate(recursive_chunks):
            # 输出编号、长度和内容，观察自然边界是否被保留。
            print(index, len(chunk), repr(chunk))

        # 验证正式结果也满足长度约束。
        assert recursive_chunks
        assert all(len(chunk) <= 24 for chunk in recursive_chunks)
        """),
        md("""
        ## 4. 比较参数，而不是凭感觉选参数

        下面只改变 `chunk_size` 和 `overlap`，记录 Chunk 数、平均长度和最大长度。注意：这些是数据形状指标，不是检索质量指标；Phase 2 会用 qrels 检查哪个配置更容易召回正确证据。
        """),
        code("""
        # 定义待比较的参数组合。
        configurations = [(32, 0), (32, 8), (64, 16), (128, 32)]

        # 创建空列表，用于保存每组配置的统计结果。
        experiment_rows = []

        # 逐组运行分块实验。
        for current_size, current_overlap in configurations:
            # 用当前参数创建一个新的分块器。
            current_splitter = RecursiveSplitter(chunk_size=current_size, overlap=current_overlap)

            # 对真实教学文本进行分块。
            current_chunks = current_splitter.split(structured_text)

            # 收集每个 Chunk 的字符长度。
            current_lengths = [len(chunk) for chunk in current_chunks]

            # 计算并记录可比较的数据形状指标。
            experiment_rows.append({"chunk_size": current_size, "overlap": current_overlap, "count": len(current_chunks), "avg_chars": round(sum(current_lengths) / len(current_lengths), 2), "max_chars": max(current_lengths)})

        # 输出实验结果，先观察参数改变带来的现象。
        for row in experiment_rows:
            # 每次打印一组配置和它的统计结果。
            print(row)

        # 确认每组结果都满足最大长度约束。
        assert all(row["max_chars"] <= row["chunk_size"] for row in experiment_rows)
        """),
        code("""
        # 创建处理数据目录，保证实验记录有固定位置。
        experiment_directory = ROOT / "data" / "processed"
        experiment_directory.mkdir(parents=True, exist_ok=True)

        # 指定本课实验记录路径。
        experiment_path = experiment_directory / "phase1_chunk_experiment.json"

        # 把实验参数和结果一起保存，避免只保留结论而丢失条件。
        experiment_path.write_text(json.dumps(experiment_rows, ensure_ascii=False, indent=2), encoding="utf-8")

        # 打印实验记录路径。
        print("已生成:", experiment_path)
        """),
        md("""
        ## 本课验收

        - [ ] 能解释 `text[start:end]` 的边界。
        - [ ] 能推导 `step = chunk_size - overlap`。
        - [ ] 能说出 overlap 的收益和成本。
        - [ ] 能解释为什么递归分隔符优先于固定字符切片。
        - [ ] 已保存 `phase1_chunk_experiment.json`。

        下一课把这些理解接到批量构建器，正式生成整个项目后续要用的 `chunks.json`。
        """),
    ])


def build_phase1_delivery() -> nbf.NotebookNode:
    return make_notebook([
        md("""
        # Phase 1.3：批量解析、验证和交付 chunks.json

        ## 目标

        把前两课的理解接入项目生产模块：批量读取输入目录、分块、生成稳定 ID、验证数据契约、保存并重新加载 JSON。

        **本课交付：** `data/processed/chunks.json`，它是 Phase 2 的唯一输入。
        """),
        md("""
        ## 1. 生产函数解决了哪些重复工作？

        手写版本帮助理解原理，但正式项目还需要处理文件排序、PDF 页码、稳定哈希、输出格式和异常边界。`build_chunks()` 把这些工作集中起来，并由测试保护。

        使用模块不是停止学习，而是把“已经理解的算法”放进可复用工程边界。
        """),
        code(SETUP),
        code("""
        # 从生产模块导入批量构建函数。
        from phase1_doc_parser.main import build_chunks

        # 从生产模块导入正式的递归分块器。
        from phase1_doc_parser.splitter import RecursiveSplitter

        # 指定真实输入目录。
        input_directory = ROOT / "phase1_doc_parser" / "examples" / "input"

        # 选择本阶段经过实验的分块参数。
        splitter = RecursiveSplitter(chunk_size=128, overlap=32)

        # 批量生成结构化 Chunk。
        chunks = build_chunks(input_directory, splitter)

        # 打印总数量，确认批处理确实产生结果。
        print("生成 Chunk 数:", len(chunks))

        # 查看第一条完整记录，确认字段没有在批处理中丢失。
        print(json.dumps(chunks[0], ensure_ascii=False, indent=2))

        # 不能为空，否则后续检索没有任何数据。
        assert chunks
        """),
        md("""
        ## 2. 逐字段验证数据契约

        数据契约不是形式主义。`id` 用于评估和引用，`text` 用于检索，`source/page` 用于回溯，`metadata` 用于解释。任何字段缺失，最终 API 都可能无法给用户可靠证据。
        """),
        code("""
        # 定义每条 Chunk 必须拥有的字段集合。
        required_fields = {"id", "text", "source", "page", "chunk_index", "metadata"}

        # 逐条检查字段集合和非空字段。
        for chunk in chunks:
            # 确认当前记录包含全部字段。
            assert required_fields <= chunk.keys()

            # 确认正文、ID 和来源不能为空。
            assert chunk["id"] and chunk["text"] and chunk["source"]

        # 把全部 Chunk ID 放进列表，准备检查重复。
        chunk_ids = [str(chunk["id"]) for chunk in chunks]

        # 稳定 ID 必须唯一，否则两个证据无法区分。
        assert len(chunk_ids) == len(set(chunk_ids))

        # 输出契约检查结果。
        print("字段、非空值和唯一 ID 检查通过。")
        """),
        code("""
        # 逐条检查正文长度不超过分块器的上限。
        for chunk in chunks:
            # 当前长度必须小于或等于 128 个字符。
            assert len(str(chunk["text"])) <= 128

        # 检查同一输入重复运行能得到相同 ID 顺序。
        repeated_chunks = build_chunks(input_directory, RecursiveSplitter(chunk_size=128, overlap=32))

        # 提取第二次运行的 ID 列表。
        repeated_ids = [str(chunk["id"]) for chunk in repeated_chunks]

        # 断言两次运行完全一致，证明索引引用可复现。
        assert chunk_ids == repeated_ids

        # 输出稳定性检查结果。
        print("长度和稳定 ID 检查通过。")
        """),
        md("""
        ## 3. 保存和重新加载：磁盘文件才是阶段交付

        内存中的 `chunks` 只在当前 Kernel 存活。下一阶段或服务启动时需要从磁盘读取，所以保存后必须重新加载并验证，而不是只看写入函数没有报错。
        """),
        code("""
        # 创建处理数据目录。
        processed_directory = ROOT / "data" / "processed"
        processed_directory.mkdir(parents=True, exist_ok=True)

        # 指定 Phase 1 的正式交付文件。
        chunks_path = processed_directory / "chunks.json"

        # 以 UTF-8 JSON 保存全部 Chunk。
        chunks_path.write_text(json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8")

        # 从磁盘重新读取 JSON，模拟下一阶段的输入。
        loaded_chunks = json.loads(chunks_path.read_text(encoding="utf-8"))

        # 确认重新加载后的数量和 ID 与内存结果一致。
        assert len(loaded_chunks) == len(chunks)
        assert [item["id"] for item in loaded_chunks] == chunk_ids

        # 打印最终交付路径和数量。
        print("Phase 1 交付:", chunks_path, "chunks=", len(loaded_chunks))
        """),
        md("""
        ## 4. 追溯演练：从 Chunk 回到原文

        随机选择一条 Chunk，打印它的来源、页码和正文。这个动作模拟最终用户点击 citation 的第一步，也是判断 Phase 1 是否真正完成的关键。
        """),
        code("""
        # 选择第一条 Chunk 作为追溯样本。
        trace_sample = loaded_chunks[0]

        # 输出引用所需的最小信息。
        print("chunk_id:", trace_sample["id"])
        print("source:", trace_sample["source"])
        print("page:", trace_sample["page"])
        print("text:", trace_sample["text"])

        # 确认来源路径仍然指向存在的原始文件。
        assert Path(trace_sample["source"]).is_file()
        """),
        md("""
        ## Phase 1 最终闸门

        - [ ] 能从原始文件解释到 `ParsedDocument`、Chunk、稳定 ID 的变化过程。
        - [ ] 所有 Chunk 通过字段、非空、长度和唯一性检查。
        - [ ] 重复运行得到相同 ID。
        - [ ] `chunks.json` 能保存、重新加载并追溯到真实文件。

        现在 Phase 2 可以把这份文件当作稳定语料，而不必重新猜测文档边界。
        """),
    ])


def build_phase2_bm25() -> nbf.NotebookNode:
    return make_notebook([
        md("""
        # Phase 2.1：Token、TF、IDF 与手写 BM25

        ## 目标

        先把文字变成 token，再从词频、文档频率推导 BM25 的直觉。最后用一个教学版 BM25 和项目正式 `BM25Retriever` 对照。

        **本课交付：** `data/processed/phase2_bm25_baseline.json`。
        """),
        md("""
        ## 1. 检索器为什么不能直接比较整句字符串？

        Query 和 Document 都是字符串，但检索需要知道“哪些词出现、出现多少次、在哪些文档出现”。Tokenizer 把字符串转换成 token 列表，后续统计才有输入。

        本项目的中文 baseline 用单个汉字和英文/数字词，优点是确定、无额外词典；缺点是中文专业词可能被拆开。这个取舍要用 qrels 验证。
        """),
        code(SETUP),
        code("""
        # 从项目 BM25 模块导入确定性 tokenizer。
        from phase2_semantic_search.bm25 import tokenize

        # 准备一条同时包含中文、英文和数字的 Query。
        query_text = "BM25 对产品型号更稳 2024"

        # 调用 tokenizer，把 Query 转为可统计的 token 列表。
        query_tokens = tokenize(query_text)

        # 打印原文和 token，观察中文被如何切分。
        print("原文:", query_text)
        print("tokens:", query_tokens)

        # 确认 tokenizer 至少产生了一个 token。
        assert query_tokens
        """),
        md("""
        ## 2. 从最简单的 TF 和 DF 开始

        - **TF（Term Frequency）**：一个词在当前文档出现几次。
        - **DF（Document Frequency）**：一个词出现在多少篇不同文档。
        - **IDF**：DF 越低，词越稀有，越能区分文档。

        先用小语料手算，之后再看完整 BM25 公式。
        """),
        code("""
        # 定义三篇极小文档，每篇文档用 token 列表表示。
        toy_documents = [["bm25", "search", "bm25"], ["dense", "search"], ["search", "api"]]

        # 选择要观察的词。
        target_term = "bm25"

        # 统计目标词在第一篇文档中的出现次数。
        term_frequency = toy_documents[0].count(target_term)

        # 统计目标词出现在多少篇不同文档中。
        document_frequency = sum(target_term in document for document in toy_documents)

        # 打印 TF 和 DF，观察“当前文档频率”和“全局文档频率”的区别。
        print("TF:", term_frequency)
        print("DF:", document_frequency)

        # 目标词应该在第一篇文档出现两次。
        assert term_frequency == 2

        # 目标词只应该出现在一篇文档中。
        assert document_frequency == 1
        """),
        code("""
        # 导入数学库，用对数计算 IDF。
        import math

        # 记录 toy corpus 的文档总数。
        document_count = len(toy_documents)

        # 使用 BM25 常见的平滑公式计算 IDF。
        idf_value = math.log(1 + (document_count - document_frequency + 0.5) / (document_frequency + 0.5))

        # 输出 IDF，观察稀有词会获得较高的区分权重。
        print("IDF:", round(idf_value, 4))

        # 用一个所有文档都有的词计算对照 IDF。
        common_frequency = sum("search" in document for document in toy_documents)

        # 计算 common term 的 IDF。
        common_idf = math.log(1 + (document_count - common_frequency + 0.5) / (common_frequency + 0.5))

        # 对比稀有词和常见词的权重。
        print("common term IDF:", round(common_idf, 4))
        print("稀有词权重更高:", idf_value > common_idf)
        """),
        md("""
        ## 3. 手写一个可读的 BM25 版本

        完整公式包含 TF 饱和和长度归一化。教学版本只支持一个 Query 和一个文档列表，但保留三个核心思想：命中奖励、IDF、长度修正。每条语句都写注释，先关注变量如何流动。
        """),
        code("""
        # 定义一个教学版 BM25 函数，输入是 Query token 和文档 token 列表。
        def simple_bm25(query_terms, documents, k1=1.5, b=0.75):
            # 导入 Counter，方便统计每篇文档的词频。
            from collections import Counter

            # 记录整个语料的文档数量。
            total_documents = len(documents)

            # 计算所有文档的平均 token 长度。
            average_length = sum(len(document) for document in documents) / max(total_documents, 1)

            # 统计每个词出现在多少篇不同文档中。
            document_frequencies = Counter(term for document in documents for term in set(document))

            # 创建空列表，用于保存每篇文档的最终得分。
            scores = []

            # 逐篇文档计算 Query 的匹配分数。
            for document in documents:
                # 统计当前文档中每个词的出现次数。
                frequencies = Counter(document)

                # 记录当前文档的 token 长度。
                document_length = len(document)

                # 从零开始累加当前文档得分。
                score = 0.0

                # 逐个 Query token 计算贡献。
                for term in set(query_terms):
                    # 读取该词在当前文档中的 TF。
                    term_frequency = frequencies.get(term, 0)

                    # 没有命中时，该词对当前文档没有贡献。
                    if term_frequency == 0:
                        continue

                    # 读取该词的 DF。
                    term_document_frequency = document_frequencies[term]

                    # 计算该词的 IDF。
                    term_idf = math.log(1 + (total_documents - term_document_frequency + 0.5) / (term_document_frequency + 0.5))

                    # 计算文档长度归一化项。
                    length_factor = 1 - b + b * document_length / max(average_length, 1e-12)

                    # 计算 TF 饱和后的贡献并累加。
                    score += term_idf * term_frequency * (k1 + 1) / (term_frequency + k1 * length_factor)

                # 保存当前文档的总分。
                scores.append(score)

            # 返回每篇文档的分数，顺序与输入文档一致。
            return scores

        # 对 toy corpus 运行教学版 BM25。
        toy_scores = simple_bm25(["bm25"], toy_documents)

        # 打印得分，观察命中文档和未命中文档的区别。
        print(toy_scores)

        # 第一篇文档命中了 bm25，应该获得正分。
        assert toy_scores[0] > 0

        # 第二篇文档没有命中 bm25，应该得分为零。
        assert toy_scores[1] == 0
        """),
        md("""
        ### 为什么生产实现比教学函数长？

        教学函数只返回分数，生产 `BM25Retriever` 还要处理 tokenizer、top-k、过滤器、稳定排序、文档元数据和输入校验。理解公式后再使用模块，你能知道这些工程代码分别保护什么行为。
        """),
        code("""
        # 读取 Phase 1 的真实 Chunk 数据。
        chunks_path = ROOT / "data" / "processed" / "chunks.json"
        chunks = json.loads(chunks_path.read_text(encoding="utf-8"))

        # 导入生产 BM25 检索器。
        from phase2_semantic_search.bm25 import BM25Retriever

        # 用真实 Chunk 创建索引对象。
        retriever = BM25Retriever(chunks)

        # 运行一条真实 Query。
        real_results = retriever.search("Chunk overlap", top_k=5)

        # 输出排名、分数、来源和正文片段，观察生产结果合同。
        for rank, result in enumerate(real_results, start=1):
            # 每一行代表一个可追溯检索结果。
            print(rank, result.doc_id, round(result.score, 4), result.metadata.get("source"), result.text[:80])

        # 至少应该找到一条包含 Query 词的结果。
        assert real_results
        """),
        code("""
        # 创建 baseline 记录，保存 Query 和结果 ID，而不是只保存屏幕输出。
        baseline_record = {
            "retriever": "BM25",
            "query": "Chunk overlap",
            "top_k": 5,
            "results": [{"rank": rank, "chunk_id": result.doc_id, "score": result.score} for rank, result in enumerate(real_results, start=1)],
        }

        # 指定 baseline 的输出路径。
        baseline_path = ROOT / "data" / "processed" / "phase2_bm25_baseline.json"

        # 保存 baseline，供后续 RRF 和评估 Notebook 读取。
        baseline_path.write_text(json.dumps(baseline_record, ensure_ascii=False, indent=2), encoding="utf-8")

        # 打印交付路径。
        print("已生成:", baseline_path)
        """),
        md("""
        ## 本课验收

        - [ ] 能区分 TF、DF、IDF。
        - [ ] 能解释 BM25 为什么不会无限奖励重复词。
        - [ ] 能读懂手写函数中每个变量的来源和用途。
        - [ ] 能把教学实现和生产实现的差异说清楚。
        - [ ] 已生成 `phase2_bm25_baseline.json`。
        """),
    ])


def build_phase2_dense_rrf() -> nbf.NotebookNode:
    return make_notebook([
        md("""
        # Phase 2.2：Dense 直觉、Cosine 和 RRF 融合

        ## 目标

        不把 Dense 当作黑盒：先用二维向量理解 cosine，再用两个人工排名手写 RRF，最后接入生产融合函数。真实 BGE-M3 依赖是可选项，本课不会把模拟向量冒充模型成绩。

        **本课交付：** `data/processed/phase2_rrf_demo.json`。
        """),
        md("""
        ## 1. Dense 检索到底改变了什么？

        Sparse/BM25 主要观察词是否出现；Dense 把文本映射到连续向量，向量方向可以表达训练数据学到的语义关系。我们先不下载模型，只用二维向量理解“相似度排序”这个机制。
        """),
        code(SETUP),
        code("""
        # 导入 NumPy，用数组表示二维向量。
        import numpy as np

        # 定义一个查询向量，假设它代表“猫”这一语义方向。
        query_vector = np.array([1.0, 0.0])

        # 定义三个文档向量，方向分别接近猫、猫的近义表达和汽车型号。
        document_vectors = {"cat": np.array([0.9, 0.1]), "kitten": np.array([0.8, 0.3]), "car_model": np.array([0.1, 0.99])}

        # 输出向量形状，确认每个向量都有两个维度。
        print("query shape:", query_vector.shape)
        print("document shape:", document_vectors["cat"].shape)

        # 向量的维度是模型表示语义的坐标数量，真实模型通常远大于 2。
        assert query_vector.shape == (2,)
        """),
        code("""
        # 定义 cosine 函数，比较两个向量的方向相似度。
        def cosine_similarity(left, right):
            # 计算两个向量的点积。
            dot_product = np.dot(left, right)

            # 计算左向量的长度。
            left_norm = np.linalg.norm(left)

            # 计算右向量的长度。
            right_norm = np.linalg.norm(right)

            # 用点积除以长度乘积，得到方向相似度。
            return float(dot_product / (left_norm * right_norm))

        # 计算查询与每篇文档的 cosine 分数。
        dense_scores = {}
        for document_id, vector in document_vectors.items():
            # 保存当前文档和查询向量的相似度。
            dense_scores[document_id] = cosine_similarity(query_vector, vector)

        # 从高到低排序，得到 Dense 的人工排名。
        dense_ranking = sorted(dense_scores, key=dense_scores.get, reverse=True)

        # 输出分数和排名，观察语义方向如何影响顺序。
        print(dense_scores)
        print(dense_ranking)

        # “cat” 应该比 “car_model” 更接近查询方向。
        assert dense_ranking[0] == "cat"
        """),
        md("""
        ### 重要边界：模拟不是 BGE-M3

        上面的向量是我们手工写的，用来理解数学。它没有经过文本模型训练，所以不能得出“Dense 召回率是多少”的结论。真实 BGE-M3 实验必须记录模型 ID、revision、设备、向量维度、归一化方法和数据集版本。
        """),
        code("""
        # 导入 importlib.util，用它检查可选包是否安装。
        import importlib.util

        # 检查 FlagEmbedding 是否存在，不在 Notebook 中偷偷下载模型。
        flag_embedding_available = importlib.util.find_spec("FlagEmbedding") is not None

        # 打印检查结果，让环境能力边界可见。
        print("FlagEmbedding installed:", flag_embedding_available)

        # 当前教学课只要求知道真实模型的入口，不要求网络下载才能完成。
        print("真实 BGE-M3 入口：BGEM3FlagModel('BAAI/bge-m3')；需单独记录下载和运行条件。")
        """),
        md("""
        ## 2. 为什么不能直接把 BM25 分数和 cosine 相加？

        BM25 分数可能是 0～若干，cosine 通常在 -1～1；两个分数的量纲和分布不同。直接相加等于默认它们已经校准，这个默认通常没有证据。

        RRF 只使用排名：某文档在一条排名中第 1 名，就贡献 `1/(rrf_k+1)`；出现在另一条排名中，还会贡献第二份分数。
        """),
        code("""
        # 定义两路人工排名，模拟精确匹配和语义匹配互补。
        bm25_ranking = ["exact_model", "semantic_doc", "unrelated"]
        dense_ranking = ["semantic_doc", "exact_model", "another_doc"]

        # 设置 RRF 的平滑常数，常见默认值是 60。
        rrf_k = 60

        # 创建空字典，用于累加每个文档的 RRF 分数。
        rrf_scores = {}

        # 把两路排名放入列表，统一处理。
        ranking_lists = [bm25_ranking, dense_ranking]

        # 逐路处理排名。
        for ranking in ranking_lists:
            # enumerate 从 0 开始，所以 rank 加 1 才符合人类排名。
            for zero_based_rank, document_id in enumerate(ranking):
                # 把机器索引转换为第 1 名、第 2 名等。
                rank = zero_based_rank + 1

                # 计算当前文档在当前排名中的贡献。
                contribution = 1 / (rrf_k + rank)

                # 把贡献累加到文档总分。
                rrf_scores[document_id] = rrf_scores.get(document_id, 0.0) + contribution

        # 按 RRF 分数从高到低得到融合排名。
        manual_fused = sorted(rrf_scores, key=rrf_scores.get, reverse=True)

        # 打印每个文档的融合分数和最终顺序。
        print(rrf_scores)
        print(manual_fused)

        # 两路都出现的文档应该获得两份贡献。
        assert "exact_model" in manual_fused
        assert "semantic_doc" in manual_fused
        """),
        md("""
        ## 3. 接入正式 RRF 函数

        正式函数还会去重同一路排名中的重复 ID、保存最佳名次、稳定处理同分排序。现在把同样的输入交给生产模块，验证我们的理解没有偏离。
        """),
        code("""
        # 导入项目中的生产 RRF 函数。
        from phase2_semantic_search.fusion import reciprocal_rank_fusion

        # 传入带名称的两路排名，名称方便之后记录实验来源。
        production_fused = reciprocal_rank_fusion({"bm25": bm25_ranking, "dense": dense_ranking}, rrf_k=rrf_k)

        # 提取正式结果中的文档 ID 顺序。
        production_ids = [item.doc_id for item in production_fused]

        # 打印正式结果，观察它还提供了 best_rank 等解释字段。
        for item in production_fused:
            # 输出文档 ID、融合分数和最佳名次。
            print(item.doc_id, round(item.score, 6), item.best_rank)

        # 正式函数至少应该返回三篇不同文档。
        assert len(production_ids) == 4
        """),
        code("""
        # 组合 RRF 教学记录，明确标记排名来自人工模拟。
        rrf_record = {
            "experiment_type": "mechanism_demo",
            "ranking_sources": ["manual_bm25_like", "manual_dense_like"],
            "rrf_k": rrf_k,
            "rankings": {"bm25": bm25_ranking, "dense": dense_ranking},
            "fused_ids": production_ids,
            "note": "人工向量和人工排名用于理解机制，不代表 BGE-M3 质量指标。",
        }

        # 指定 RRF 教学记录路径。
        rrf_path = ROOT / "data" / "processed" / "phase2_rrf_demo.json"

        # 保存记录，防止把模拟实验误写成无条件结论。
        rrf_path.write_text(json.dumps(rrf_record, ensure_ascii=False, indent=2), encoding="utf-8")

        # 打印交付路径。
        print("已生成:", rrf_path)
        """),
        md("""
        ## 本课验收

        - [ ] 能解释向量、点积、范数和 cosine 的关系。
        - [ ] 能明确区分 Dense 原理模拟与真实 BGE-M3 实验。
        - [ ] 能手写 RRF，并说明它为什么不需要比较原始分数量纲。
        - [ ] 能读懂正式 RRF 返回的 `doc_id/score/best_rank`。
        - [ ] 已生成 `phase2_rrf_demo.json`。
        """),
    ])


def build_phase2_evaluation() -> nbf.NotebookNode:
    return make_notebook([
        md("""
        # Phase 2.3：qrels、Recall/MRR 与检索交付

        ## 目标

        把“看起来相关”变成可计算评估：为 Query 标注相关 Chunk ID，手算 Recall@k/MRR@k，再调用项目指标函数验证，最后保存 BM25 baseline 报告。

        **本课交付：** `data/processed/phase2_evaluation.json`。
        """),
        md("""
        ## 1. qrels 是什么？

        qrels（query relevance judgments）记录“对于某条 Query，哪些文档被认为相关”。它不是检索器自动生成的分数，而是评估标准。

        如果没有 qrels，系统只能说“我返回了五条结果”；有了 qrels，才能说“前五条找回了多少相关证据”。小样例适合教学，正式项目还要扩大 Query 并记录标注依据。
        """),
        code(SETUP),
        code("""
        # 读取 Phase 1 交付的 Chunk 数据。
        chunks = json.loads((ROOT / "data" / "processed" / "chunks.json").read_text(encoding="utf-8"))

        # 定义两条教学 Query 和它们的关键词。
        queries = {"q-001": "Chunk overlap", "q-002": "Dense BM25"}

        # 导入生产 BM25 检索器。
        from phase2_semantic_search.bm25 import BM25Retriever

        # 用真实 Chunk 建立 BM25 索引。
        retriever = BM25Retriever(chunks)

        # 创建空字典，用于保存每条 Query 的排名 ID。
        runs = {}

        # 对每条 Query 执行 top-5 检索。
        for query_id, query in queries.items():
            # 调用检索器得到带分数的结果。
            results = retriever.search(query, top_k=5)

            # 只保留排名 ID，形成评估函数需要的 run。
            runs[query_id] = [result.doc_id for result in results]

        # 打印每条 Query 的排名结果。
        print(runs)
        """),
        md("""
        ## 2. 手工构造教学 qrels

        这里用一个透明规则生成小样例标注：正文中包含 `overlap` 的 Chunk 作为 q-001 的相关证据，正文中包含 `Dense` 或 `BM25` 的 Chunk 作为 q-002 的相关证据。真实项目应由人工按照标注规范复核，而不是永远依赖关键词规则。
        """),
        code("""
        # 为每条 Query 创建空的相关 ID 集合。
        qrels = {"q-001": set(), "q-002": set()}

        # 遍历所有 Chunk，按照教学规则挑选相关证据。
        for chunk in chunks:
            # 取出正文并统一转为小写，方便英文关键词匹配。
            text = str(chunk["text"]).lower()

            # overlap 出现在正文时，把 Chunk 标记为 q-001 相关。
            if "overlap" in text:
                qrels["q-001"].add(str(chunk["id"]))

            # dense 或 bm25 出现在正文时，把 Chunk 标记为 q-002 相关。
            if "dense" in text or "bm25" in text:
                qrels["q-002"].add(str(chunk["id"]))

        # 输出 qrels，观察 Query 和相关 ID 的关系。
        print(qrels)

        # 两条教学 Query 都应该至少有一条相关 Chunk。
        assert all(qrels.values())
        """),
        md("""
        ## 3. 手算 Recall@k 和 MRR@k

        假设排名是 `[wrong, target, other]`，相关集合是 `{target}`：

        - Recall@3 = 1/1 = 1，因为唯一相关文档进入前三名。
        - MRR@3 = 1/2 = 0.5，因为第一个相关文档排在第 2 名。

        两个指标关注不同问题：Recall 关心找没找全，MRR 关心第一个正确结果是否靠前。
        """),
        code("""
        # 创建一个用于手算的排名列表。
        toy_ranking = ["wrong", "target", "other"]

        # 创建手算用的相关文档集合。
        toy_relevant = {"target"}

        # 截取 top-3 结果并求与相关集合的交集。
        retrieved_relevant = set(toy_ranking[:3]) & toy_relevant

        # 计算 Recall：召回的相关数量除以全部相关数量。
        toy_recall = len(retrieved_relevant) / len(toy_relevant)

        # 找到第一个相关结果的排名位置。
        first_relevant_rank = toy_ranking.index("target") + 1

        # 计算 MRR：第一个相关结果排名的倒数。
        toy_mrr = 1 / first_relevant_rank

        # 打印手算结果。
        print("toy Recall@3:", toy_recall)
        print("toy MRR@3:", toy_mrr)

        # 验证手算结果。
        assert toy_recall == 1.0
        assert toy_mrr == 0.5
        """),
        code("""
        # 从项目模块导入正式的 Recall/MRR 评估函数。
        from phase2_semantic_search.metrics import evaluate_qrels, recall_at_k, mrr_at_k

        # 计算所有 Query 的平均 Recall@5 和 MRR@5。
        metrics = evaluate_qrels(runs, qrels, k=5)

        # 打印总体指标。
        print(metrics)

        # 对每条 Query 单独输出两个指标，定位是哪条 Query 表现不好。
        for query_id, relevant_ids in qrels.items():
            # 读取当前 Query 的排名。
            ranked_ids = runs[query_id]

            # 计算当前 Query 的 Recall@5。
            query_recall = recall_at_k(ranked_ids, relevant_ids, k=5)

            # 计算当前 Query 的 MRR@5。
            query_mrr = mrr_at_k(ranked_ids, relevant_ids, k=5)

            # 打印 Query 级别的指标。
            print(query_id, "Recall@5=", query_recall, "MRR@5=", query_mrr)

        # 总体指标必须是合法的 0 到 1 之间的数。
        assert 0 <= metrics["recall@5"] <= 1
        assert 0 <= metrics["mrr@5"] <= 1
        """),
        md("""
        ## 4. 保存评估证据

        报告必须同时保存 Query、qrels、run 和指标。只有一个总分，无法追问某条 Query 为什么失败；只有排名没有 qrels，又无法判断是否正确。
        """),
        code("""
        # 把集合转换为排序列表，确保 JSON 输出稳定。
        serializable_qrels = {query_id: sorted(relevant_ids) for query_id, relevant_ids in qrels.items()}

        # 组合 Phase 2 的评估记录。
        evaluation_record = {"queries": queries, "qrels": serializable_qrels, "runs": runs, "metrics": metrics, "k": 5}

        # 指定评估记录路径。
        evaluation_path = ROOT / "data" / "processed" / "phase2_evaluation.json"

        # 写入评估记录，供 Phase 3 读取。
        evaluation_path.write_text(json.dumps(evaluation_record, ensure_ascii=False, indent=2), encoding="utf-8")

        # 打印交付路径。
        print("已生成:", evaluation_path)
        """),
        md("""
        ## Phase 2 最终闸门

        - [ ] 能区分 Query、run 和 qrels。
        - [ ] 能手算 Recall 和 MRR，并解释两者不同。
        - [ ] 指标来自真实 `chunks.json` 和固定 qrels。
        - [ ] 能定位到 Query 级别，而不是只看总分。
        - [ ] 已生成 `phase2_evaluation.json`。
        """),
    ])


def build_phase3_timing() -> nbf.NotebookNode:
    return make_notebook([
        md("""
        # Phase 3.1：计时、Warmup、Mean、P50 和 P95

        ## 目标

        建立一个可复用的 benchmark 计时器，测量真实 `KnowledgeBase.search()`，理解冷启动与稳定态的区别，并输出 mean/P50/P95。

        **本课交付：** `data/processed/phase3_timing_baseline.json`。
        """),
        md("""
        ## 1. 性能数字为什么需要实验设计？

        一次调用的耗时可能包含首次导入、内存分配、缓存建立等因素。稳定态 benchmark 通常先 warmup，再测多次。平均值描述总体水平，P50 描述典型请求，P95 暴露长尾。

        当前语料很小，所以数字不是生产承诺；我们正在验证测量方法是否正确。
        """),
        code(SETUP),
        code("""
        # 导入 perf_counter，它适合测量短时间间隔。
        from time import perf_counter

        # 导入统计函数，计算平均值和中位数。
        from statistics import mean, median

        # 导入 KnowledgeBase，它会复用 Phase 1 和 Phase 2 的生产逻辑。
        from phase4_mini_rag_system.knowledge_base import KnowledgeBase

        # 创建一个知识库对象。
        knowledge_base = KnowledgeBase()

        # 使用固定输入和固定分块参数构建索引。
        knowledge_base.ingest(ROOT / "phase1_doc_parser" / "examples" / "input", chunk_size=128, overlap=32)

        # 输出索引版本，记录 benchmark 的数据条件。
        print("index_version:", knowledge_base.index_version)

        # 确认索引中存在数据。
        assert knowledge_base.chunks
        """),
        code("""
        # 定义一个函数，计时一次真实搜索并返回毫秒数。
        def time_one_search(query, top_k=5):
            # 在计时开始前记录高精度时间点。
            start_time = perf_counter()

            # 执行真正的知识库搜索，不测量空函数。
            knowledge_base.search(query, top_k=top_k)

            # 记录结束时间并转换为毫秒。
            elapsed_ms = (perf_counter() - start_time) * 1000

            # 返回这一次请求的耗时。
            return elapsed_ms

        # 测量第一次调用，观察冷启动样本。
        first_ms = time_one_search("Chunk overlap")

        # 打印第一次调用时间。
        print("first call ms:", round(first_ms, 4))
        """),
        code("""
        # 创建空列表，用于保存 warmup 后的稳定态样本。
        stable_samples = []

        # 先执行五次不计入结果的 warmup。
        for _ in range(5):
            # 让解释器和索引有机会完成首次准备工作。
            time_one_search("Chunk overlap")

        # 再执行三十次正式测量。
        for _ in range(30):
            # 把每次耗时保存到样本列表。
            stable_samples.append(time_one_search("Chunk overlap"))

        # 输出部分样本，确认确实测量了多次。
        print("samples:", [round(sample, 4) for sample in stable_samples[:5]], "...")

        # 确认样本数量满足预期。
        assert len(stable_samples) == 30
        """),
        md("""
        ## 2. 自己实现 percentile

        为了理解 P50/P95，不先调用统计库。把样本排序后，用位置取近似分位数。不同工具可能使用不同插值规则，正式报告必须说明采用的定义。
        """),
        code("""
        # 定义一个教学版 percentile 函数。
        def simple_percentile(values, fraction):
            # 确保输入列表不为空。
            if not values:
                raise ValueError("values 不能为空")

            # 将样本从小到大排序，避免改变原始列表。
            ordered_values = sorted(values)

            # 根据 nearest-rank 思路计算数组位置。
            position = max(0, min(len(ordered_values) - 1, round(fraction * len(ordered_values)) - 1))

            # 返回对应位置的样本。
            return ordered_values[position]

        # 计算稳定态平均值。
        mean_ms = mean(stable_samples)

        # 计算稳定态中位数，也就是 P50 的一种实现。
        p50_ms = median(stable_samples)

        # 计算稳定态 P95。
        p95_ms = simple_percentile(stable_samples, 0.95)

        # 打印三种读数。
        print({"mean_ms": round(mean_ms, 4), "p50_ms": round(p50_ms, 4), "p95_ms": round(p95_ms, 4)})

        # 三个延迟指标都必须为非负数。
        assert mean_ms >= 0 and p50_ms >= 0 and p95_ms >= 0
        """),
        md("""
        ### 如何解释三个数字

        - Mean 适合看总体耗时，但可能受极端值影响。
        - P50 表示一半请求不超过的耗时，接近典型请求。
        - P95 表示 95% 请求不超过的耗时，能发现长尾。

        不能把当前几毫秒的结果写成“系统生产性能”，因为数据规模、硬件、并发和模型路径都不同。
        """),
        code("""
        # 记录当前 Python 版本，方便复现实验环境。
        python_version = sys.version.split()[0]

        # 组合 benchmark 基线记录。
        timing_record = {"query": "Chunk overlap", "top_k": 5, "warmup": 5, "iterations": 30, "python": python_version, "index_version": knowledge_base.index_version, "first_ms": first_ms, "mean_ms": mean_ms, "p50_ms": p50_ms, "p95_ms": p95_ms}

        # 指定 Phase 3 基线文件路径。
        timing_path = ROOT / "data" / "processed" / "phase3_timing_baseline.json"

        # 保存计时条件和结果。
        timing_path.write_text(json.dumps(timing_record, ensure_ascii=False, indent=2), encoding="utf-8")

        # 打印交付路径。
        print("已生成:", timing_path)
        """),
        md("""
        ## 本课验收

        - [ ] 能解释为什么先 warmup 再测稳定态。
        - [ ] 能说明 mean、P50、P95 的不同含义。
        - [ ] 计时函数测的是实际搜索而不是空函数。
        - [ ] 已保存条件、版本、迭代次数和结果。
        """),
    ])


def build_phase3_experiments() -> nbf.NotebookNode:
    return make_notebook([
        md("""
        # Phase 3.2：单变量实验：top-k 与分块参数

        ## 目标

        一次只改变一个主要变量，同时记录质量和性能。我们会比较不同 `top_k`，再比较不同 Chunk 配置，理解“更快”和“更好”可能互相冲突。

        **本课交付：** `data/processed/phase3_single_variable_experiments.json`。
        """),
        md("""
        ## 1. 什么叫单变量实验？

        如果同时改变 chunk_size、top_k 和 tokenizer，结果发生变化时无法归因。单变量实验固定其他条件，只修改一个变量，并把固定条件一起记录。

        本课使用小型本地语料，结论只适用于当前数据版本；方法可以复用到真实大规模语料。
        """),
        code(SETUP),
        code("""
        # 导入计时器，测量搜索调用耗时。
        from time import perf_counter

        # 导入 KnowledgeBase，构建可复用的生产检索服务。
        from phase4_mini_rag_system.knowledge_base import KnowledgeBase

        # 导入 Recall 指标，用于判断相关证据是否进入 top-k。
        from phase2_semantic_search.metrics import recall_at_k

        # 定义固定的原始输入目录。
        input_directory = ROOT / "phase1_doc_parser" / "examples" / "input"

        # 建立一个固定 Query，后续只改变 top_k 或分块参数。
        fixed_query = "Chunk overlap"

        # 找出正文中包含 overlap 的 Chunk ID，作为教学相关集合。
        reference_kb = KnowledgeBase()
        reference_kb.ingest(input_directory, chunk_size=128, overlap=32)
        relevant_ids = {str(chunk["id"]) for chunk in reference_kb.chunks if "overlap" in str(chunk["text"]).lower()}

        # 确认教学相关集合不为空。
        assert relevant_ids
        """),
        code("""
        # 定义一个实验函数，固定 Query 和索引，只改变 top_k。
        def measure_top_k(top_k):
            # 预热一次当前 Query。
            reference_kb.search(fixed_query, top_k=top_k)

            # 记录计时起点。
            start_time = perf_counter()

            # 执行正式搜索。
            results = reference_kb.search(fixed_query, top_k=top_k)

            # 计算单次搜索耗时。
            elapsed_ms = (perf_counter() - start_time) * 1000

            # 提取排名 ID，供 Recall 计算。
            ranked_ids = [result["chunk_id"] for result in results]

            # 返回这组配置的完整实验记录。
            return {"top_k": top_k, "elapsed_ms": elapsed_ms, "recall": recall_at_k(ranked_ids, relevant_ids, k=top_k), "result_count": len(results)}

        # 只改变 top_k，保存三组结果。
        top_k_results = [measure_top_k(top_k) for top_k in (1, 2, 5)]

        # 打印结果，观察返回数量、质量和耗时的关系。
        for row in top_k_results:
            # 输出每组 top_k 的实验记录。
            print(row)
        """),
        md("""
        ### 读结果时不要预设结论

        top_k 增大通常给 Recall 更多机会，但也会带来更多上下文和排序/序列化成本。当前小数据可能看不出明显延迟差异，这不代表大数据上没有成本，只代表本次实验的规模太小。
        """),
        code("""
        # 定义要比较的分块配置，其他 Query 和 qrels 保持不变。
        chunk_configurations = [(64, 16), (128, 32), (256, 64)]

        # 创建空列表，保存分块参数实验结果。
        chunk_results = []

        # 逐组构建独立知识库，避免索引状态互相污染。
        for chunk_size, overlap in chunk_configurations:
            # 创建当前配置的知识库。
            current_kb = KnowledgeBase()

            # 用当前参数导入文档并建立 BM25 索引。
            current_kb.ingest(input_directory, chunk_size=chunk_size, overlap=overlap)

            # 记录计时起点。
            start_time = perf_counter()

            # 执行固定 Query。
            current_results = current_kb.search(fixed_query, top_k=5)

            # 计算当前配置的搜索耗时。
            elapsed_ms = (perf_counter() - start_time) * 1000

            # 提取当前排名 ID。
            current_ids = [result["chunk_id"] for result in current_results]

            # 记录索引规模、质量和单次耗时。
            chunk_results.append({"chunk_size": chunk_size, "overlap": overlap, "chunks": len(current_kb.chunks), "elapsed_ms": elapsed_ms, "recall": recall_at_k(current_ids, relevant_ids, k=5)})

        # 打印分块配置对照结果。
        for row in chunk_results:
            # 输出一组配置的完整结果。
            print(row)
        """),
        md("""
        ## 2. 错误归因：指标变差以后先查哪一层？

        评估数字只是症状。相关 Chunk 不在 top-k，优先查解析、分块、tokenizer 或召回；相关 Chunk 已经在 top-k 但答案错，才查上下文编排和生成。下一次实验只改对应层，才能建立因果关系。
        """),
        code("""
        # 创建一份可复用的错误归因表。
        failure_taxonomy = [
            {"observed": "相关 Chunk 不在 top-k", "layer": "parsing/chunking/retrieval", "next_change": "只改分块或召回策略"},
            {"observed": "相关 Chunk 在 top-k，但答案漏掉事实", "layer": "context/generation", "next_change": "只改上下文编排或 prompt"},
            {"observed": "答案出现证据中没有的事实", "layer": "faithfulness", "next_change": "增加证据约束和人工复核"},
        ]

        # 逐条打印归因规则，形成调试习惯。
        for failure in failure_taxonomy:
            # 输出观察、归因层和下一步实验变量。
            print(failure)

        # 三种错误都必须写明下一步动作。
        assert all(failure["next_change"] for failure in failure_taxonomy)
        """),
        code("""
        # 组合两个单变量实验的完整记录。
        experiment_record = {"fixed_query": fixed_query, "relevant_ids": sorted(relevant_ids), "top_k_results": top_k_results, "chunk_results": chunk_results, "failure_taxonomy": failure_taxonomy}

        # 指定实验记录路径。
        experiment_path = ROOT / "data" / "processed" / "phase3_single_variable_experiments.json"

        # 保存实验条件和结果，供下一课生成报告。
        experiment_path.write_text(json.dumps(experiment_record, ensure_ascii=False, indent=2), encoding="utf-8")

        # 打印交付路径。
        print("已生成:", experiment_path)
        """),
        md("""
        ## 本课验收

        - [ ] 能指出每个实验固定了什么、改变了什么。
        - [ ] 能同时查看 Recall 和延迟，而不是只追求一个数字。
        - [ ] 能把一次失败映射到下一步实验。
        - [ ] 已生成 `phase3_single_variable_experiments.json`。
        """),
    ])


def build_phase3_report() -> nbf.NotebookNode:
    return make_notebook([
        md("""
        # Phase 3.3：生成实验报告与优化边界

        ## 目标

        读取前两课的实验记录，把性能、质量、环境和限制写成一份可复现报告。ONNX/INT8 在本课只做能力检查，不伪造未执行的加速结果。

        **本课交付：** `docs/phase3_baseline_report.md`。
        """),
        md("""
        ## 1. 报告为什么要包含限制？

        专业报告不仅展示最好数字，还要写清楚数据规模、硬件、迭代次数、模型路径和不能推广的地方。当前项目使用小型本地语料，报告应明确这是教学 baseline，不是线上 SLA。
        """),
        code(SETUP),
        code("""
        # 读取 Phase 3.1 的计时基线。
        timing_path = ROOT / "data" / "processed" / "phase3_timing_baseline.json"
        timing_record = json.loads(timing_path.read_text(encoding="utf-8"))

        # 读取 Phase 3.2 的单变量实验。
        experiment_path = ROOT / "data" / "processed" / "phase3_single_variable_experiments.json"
        experiment_record = json.loads(experiment_path.read_text(encoding="utf-8"))

        # 打印关键基线，确认输入文件确实存在并可读取。
        print("timing baseline:", timing_record)
        print("top_k experiments:", len(experiment_record["top_k_results"]))
        print("chunk experiments:", len(experiment_record["chunk_results"]))

        # 至少要有一组结果才能生成报告。
        assert experiment_record["top_k_results"]
        assert experiment_record["chunk_results"]
        """),
        code("""
        # 导入 importlib.util 检查可选优化依赖。
        import importlib.util

        # 记录 ONNX 运行时是否安装。
        onnx_available = importlib.util.find_spec("onnxruntime") is not None

        # 记录 psutil 是否安装，用于以后测内存。
        psutil_available = importlib.util.find_spec("psutil") is not None

        # 输出依赖能力，但不因缺少可选包而伪造实验结果。
        print({"onnxruntime": onnx_available, "psutil": psutil_available})
        """),
        md("""
        ## 2. 从数据中生成结论草稿

        先让程序提取可核对的事实，再由人写解释。程序可以告诉我们哪组 Recall 高、哪组 Chunk 数多，但不能替我们决定业务是否愿意用更多延迟换召回。
        """),
        code("""
        # 找出 top_k 实验中 Recall 最高的配置。
        best_top_k = max(experiment_record["top_k_results"], key=lambda row: row["recall"])

        # 找出 Chunk 数最少的配置，作为成本侧观察。
        smallest_chunk_index = min(experiment_record["chunk_results"], key=lambda row: row["chunks"])

        # 打印两个事实，后续报告正文会引用它们。
        print("best top_k by recall:", best_top_k)
        print("smallest index:", smallest_chunk_index)

        # 检查自动提取的结果包含必要字段。
        assert "recall" in best_top_k
        assert "chunks" in smallest_chunk_index
        """),
        md("""
        ## 3. 生成 Markdown 报告

        报告使用当前运行真实数据填充，不手写一个可能与 Notebook 输出不一致的数字。`notes` 明确写出边界：样本小、没有并发、没有真实 ONNX 结果。
        """),
        code("""
        # 读取当前时间之外的稳定实验字段，避免报告每次无意义变化。
        report_lines = [
            "# Phase 3 Baseline Report",
            "",
            "## 实验范围",
            "",
            "本报告来自本地小型 Markdown 语料，检索器为 BM25，目标是验证 benchmark 方法而不是宣称生产 SLA。",
            "",
            "## 计时基线",
            "",
            f"- index_version: `{timing_record['index_version']}`",
            f"- query: `{timing_record['query']}`",
            f"- warmup: `{timing_record['warmup']}`",
            f"- iterations: `{timing_record['iterations']}`",
            f"- mean_ms: `{timing_record['mean_ms']:.4f}`",
            f"- p50_ms: `{timing_record['p50_ms']:.4f}`",
            f"- p95_ms: `{timing_record['p95_ms']:.4f}`",
            "",
            "## 单变量实验",
            "",
            "### top_k",
        ]

        # 把 top_k 实验逐行写入报告，保留完整条件。
        for row in experiment_record["top_k_results"]:
            # 使用表格行记录 top_k、结果量、Recall 和耗时。
            report_lines.append(f"- top_k={row['top_k']}: results={row['result_count']}, recall={row['recall']:.3f}, elapsed_ms={row['elapsed_ms']:.4f}")

        # 加入分块参数实验小节。
        report_lines.extend(["", "### chunk_size/overlap", ""])

        # 把分块实验逐行写入报告。
        for row in experiment_record["chunk_results"]:
            # 记录参数、索引规模、Recall 和耗时。
            report_lines.append(f"- size={row['chunk_size']}, overlap={row['overlap']}: chunks={row['chunks']}, recall={row['recall']:.3f}, elapsed_ms={row['elapsed_ms']:.4f}")

        # 加入优化边界，防止读者把 baseline 当成量化结论。
        report_lines.extend(["", "## 限制与下一步", "", "- 当前语料规模很小，不能代表生产规模延迟。", "- 当前没有执行真实 ONNX/INT8 导出，因此不报告量化收益。", "- 下一步应固定更大数据集和 qrels，再比较 Dense/Hybrid 与 BM25。"])

        # 将报告行连接成一个 Markdown 字符串。
        report_text = "\\n".join(report_lines) + "\\n"

        # 指定报告路径。
        report_path = ROOT / "docs" / "phase3_baseline_report.md"

        # 写入报告文件。
        report_path.write_text(report_text, encoding="utf-8")

        # 打印报告路径。
        print("已生成:", report_path)
        """),
        md("""
        ## Phase 3 最终闸门

        - [ ] 报告中的数字来自前面保存的实验记录。
        - [ ] 同时报告质量、延迟、输入规模和实验条件。
        - [ ] 明确写出当前没有执行的 ONNX/INT8 结论。
        - [ ] 能解释为什么更快不自动等于更好。
        - [ ] 已生成 `docs/phase3_baseline_report.md`。
        """),
    ])


def build_phase4_contract() -> nbf.NotebookNode:
    return make_notebook([
        md("""
        # Phase 4.1：HTTP、JSON 与 API 合同

        ## 目标

        从用户视角理解服务：请求是什么，响应是什么，状态码表达什么，为什么 `/search` 必须返回 citations。先使用 FastAPI `TestClient` 在内存中验证，不依赖手工启动服务器。

        **本课交付：** 一组 API 合同断言，为下一课的产品编排提供边界。
        """),
        md("""
        ## 1. Python 函数和 HTTP 接口的区别

        Python 函数可以直接传对象；HTTP 客户端只能传文本/JSON，并通过状态码告诉调用方结果。API 合同把内部对象转换成稳定的外部协议，前端、测试和其他服务都依赖这个协议。

        本项目的核心接口：

        ```text
        GET  /health  -> 服务和索引状态
        POST /search  -> Query 和可追溯结果
        POST /chat    -> 答案模式和 citations
        ```
        """),
        code(SETUP),
        md("""
        ## 2. 先手写一个最小 API 合同

        在使用 FastAPI 之前，先用普通 Python 函数模拟一个服务边界。这个函数接收一个 JSON 风格字典，检查 `query`，再返回一个包含 `status_code/body` 的响应。它不是最终服务器，而是帮助你理解：API 的核心是稳定的输入校验和输出合同。
        """),
        code("""
        # 定义一个最小搜索函数，模拟 HTTP 服务的输入和输出。
        def manual_search_api(request_body):
            # 从请求字典中读取 query；缺失时使用空字符串。
            query = str(request_body.get("query", ""))

            # 如果 query 为空，返回客户端输入错误的响应。
            if not query:
                return {"status_code": 422, "body": {"code": "QUERY_REQUIRED", "message": "query 不能为空"}}

            # 对合法输入返回一个固定结构，模拟后续检索结果。
            return {"status_code": 200, "body": {"query": query, "results": [], "citations": []}}

        # 发送合法请求，观察服务合同的成功形状。
        manual_ok = manual_search_api({"query": "overlap"})

        # 打印成功响应的状态码和正文。
        print(manual_ok)

        # 发送空请求，观察输入校验如何转成 422。
        manual_bad = manual_search_api({"query": ""})

        # 打印错误响应，理解调用方可以根据 code 做什么。
        print(manual_bad)

        # 验证两类输入得到不同状态码。
        assert manual_ok["status_code"] == 200
        assert manual_bad["status_code"] == 422
        """),
        md("""
        ### 为什么还要使用 FastAPI？

        手写函数展示了合同的本质，但没有 HTTP 路由、JSON 序列化、自动文档、类型校验和测试工具。FastAPI 把这些通用工程能力提供出来；我们要学习的是“知道它替我们做了什么”，而不是把框架当黑盒。
        """),
        code("""
        # 从 FastAPI 导入测试客户端，它会在内存中发送 HTTP 请求。
        from fastapi.testclient import TestClient

        # 从项目应用工厂导入 create_app，避免直接依赖全局状态。
        from phase4_mini_rag_system.app import create_app

        # 指定应用默认读取的教学输入目录。
        input_directory = ROOT / "phase1_doc_parser" / "examples" / "input"

        # 创建一个已经完成初始 ingest 的 FastAPI 应用。
        app = create_app(input_directory)

        # 创建测试客户端，后面的 get/post 就像真实 HTTP 调用。
        client = TestClient(app)

        # 确认客户端和应用对象创建成功。
        print("API TestClient ready")
        """),
        md("""
        ## 3. `/health`：先看服务是否准备好

        健康接口通常返回 200 和索引信息。`chunks` 和 `index_version` 让调用方知道服务不是“能响应但没有数据”。
        """),
        code("""
        # 向 health 路由发送 GET 请求。
        health_response = client.get("/health")

        # 读取 HTTP 状态码。
        print("status:", health_response.status_code)

        # 把 JSON 响应转换为 Python 字典。
        health_payload = health_response.json()

        # 打印响应内容，观察外部 API 合同。
        print(health_payload)

        # 健康检查成功时必须返回 200。
        assert health_response.status_code == 200

        # 健康响应必须报告 Chunk 数和索引版本。
        assert health_payload["chunks"] > 0
        assert health_payload["index_version"]
        """),
        md("""
        ## 4. `/search`：请求和引用响应

        请求体是 JSON：`query` 是用户问题，`top_k` 控制返回数量。响应中的每条结果必须包含 `chunk_id/text/source/page/score`，否则用户无法回到原文，也无法评估排名。
        """),
        code("""
        # 创建一个合法的搜索请求 JSON。
        search_request = {"query": "Chunk overlap", "top_k": 3}

        # 向 search 路由发送 POST 请求并携带 JSON。
        search_response = client.post("/search", json=search_request)

        # 把响应转换为 Python 字典。
        search_payload = search_response.json()

        # 输出状态和结果数量，理解请求到响应的转换。
        print("status:", search_response.status_code)
        print("result count:", len(search_payload["results"]))

        # 合法请求必须返回 200。
        assert search_response.status_code == 200

        # 结果列表不能为空，否则 Query 没有得到证据。
        assert search_payload["results"]

        # 定义 citation 的最小字段集合。
        citation_fields = {"chunk_id", "text", "source", "page", "score"}

        # 检查第一条结果是否满足引用合同。
        assert citation_fields <= search_payload["results"][0].keys()
        """),
        md("""
        ## 5. 状态码：输入错误不是服务器崩溃

        Pydantic 会校验 `query` 的最小长度。空 Query 属于客户端输入错误，应返回 422；调用方可以据此提示用户，而不是显示“服务器坏了”。
        """),
        code("""
        # 创建一个违反 query 最小长度约束的请求。
        invalid_request = {"query": ""}

        # 发送非法请求，观察 FastAPI 的校验响应。
        invalid_response = client.post("/search", json=invalid_request)

        # 输出状态码和错误详情。
        print("status:", invalid_response.status_code)
        print("detail:", invalid_response.json().get("detail"))

        # 空 Query 应该被识别为请求校验错误。
        assert invalid_response.status_code == 422
        """),
        md("""
        ## 本课验收

        - [ ] 能区分 Python 函数调用和 HTTP 请求。
        - [ ] 能解释 200 与 422 的区别。
        - [ ] 能说出 citations 为什么是产品合同而不是调试输出。
        - [ ] 能手写一个最小请求校验和响应合同。
        - [ ] `/health`、`/search` 和空 Query 行为已通过断言。
        """),
    ])


def build_phase4_service() -> nbf.NotebookNode:
    return make_notebook([
        md("""
        # Phase 4.2：从 KnowledgeBase 到 evidence-first 服务

        ## 目标

        先把服务内部逻辑拆成“导入 → 建索引 → 搜索 → 组织证据”，再通过 FastAPI 暴露。理解这一层，才能知道 API 路由不是魔法，而是对已有项目能力的编排。

        **本课交付：** 一次临时知识库导入记录和 evidence-only 答案验证。
        """),
        md("""
        ## 1. 为什么索引不能每次请求重建？

        文档解析和 BM25 建索引是相对昂贵的初始化工作。服务启动时 ingest 一次，之后多个 Query 复用同一个 `KnowledgeBase`；如果每次请求都重建，延迟会变高，也更难保证同一批请求使用同一版本索引。
        """),
        code(SETUP),
        code("""
        # 导入临时目录工具，创建一个隔离的练习知识库。
        from tempfile import TemporaryDirectory

        # 导入 KnowledgeBase，观察服务内部的核心对象。
        from phase4_mini_rag_system.knowledge_base import KnowledgeBase

        # 创建临时目录，退出代码块后会自动清理。
        with TemporaryDirectory() as temporary_directory:
            # 把临时目录字符串转换成 Path 对象。
            temporary_path = Path(temporary_directory)

            # 指定一份临时 Markdown 文件。
            guide_path = temporary_path / "guide.md"

            # 写入一条可被检索的事实。
            guide_path.write_text("# Guide\\n\\noverlap 保留跨边界上下文。", encoding="utf-8")

            # 创建一个空 KnowledgeBase。
            knowledge_base = KnowledgeBase()

            # 导入文档并构建 BM25 索引。
            chunk_count = knowledge_base.ingest(temporary_path, chunk_size=128, overlap=32)

            # 打印导入数量和索引版本。
            print("ingested chunks:", chunk_count)
            print("index version:", knowledge_base.index_version)

            # 确认索引已经准备好。
            assert chunk_count > 0
            assert knowledge_base.retriever is not None
        """),
        md("""
        ## 2. 搜索和证据回答是两个步骤

        `search()` 负责找到并排序证据；`evidence_answer()` 负责在没有 LLM 时把证据明确展示给用户。分开这两步有两个好处：检索可以独立评估，生成失败时仍然保留证据。
        """),
        code("""
        # 再创建一个临时目录，保证本单元格可以独立执行。
        with TemporaryDirectory() as temporary_directory:
            # 把临时目录转换为 Path。
            temporary_path = Path(temporary_directory)

            # 创建知识库输入文件。
            (temporary_path / "guide.md").write_text("Chunk overlap 可以保留跨边界上下文。", encoding="utf-8")

            # 创建并导入知识库。
            knowledge_base = KnowledgeBase()
            knowledge_base.ingest(temporary_path)

            # 搜索用户问题并取得结构化结果。
            results = knowledge_base.search("overlap 上下文", top_k=3)

            # 将搜索结果组织成 evidence-only 答案。
            answer = knowledge_base.evidence_answer("overlap 上下文", results)

            # 输出答案和第一条引用信息。
            print(answer)
            print(results[0])

            # 有证据的问题必须返回结果和 Chunk ID。
            assert results
            assert results[0]["chunk_id"]

            # evidence-only 答案必须明确它没有调用生成模型。
            assert "evidence-only" in answer
        """),
        md("""
        ## 3. 没有证据时不能编造

        对不存在的词进行查询，结果应该为空，答案应该明确说没有足够证据。这个行为是 evidence-first 产品的安全底线。
        """),
        code("""
        # 创建一个包含已知事实的临时知识库。
        with TemporaryDirectory() as temporary_directory:
            # 把临时目录转为 Path。
            temporary_path = Path(temporary_directory)

            # 写入一条不包含未知词的文档。
            (temporary_path / "guide.md").write_text("系统支持本地检索。", encoding="utf-8")

            # 导入文档并建立索引。
            knowledge_base = KnowledgeBase()
            knowledge_base.ingest(temporary_path)

            # 查询知识库中不存在的词。
            empty_results = knowledge_base.search("完全不存在的词", top_k=3)

            # 让服务根据空证据生成 fallback 文本。
            empty_answer = knowledge_base.evidence_answer("完全不存在的词", empty_results)

            # 输出结果，观察系统如何表达不知道。
            print("results:", empty_results)
            print("answer:", empty_answer)

            # 没有证据时结果必须为空。
            assert empty_results == []

            # 答案必须明确表示无法回答。
            assert "无法回答" in empty_answer
        """),
        md("""
        ## 本课验收

        - [ ] 能画出 ingest、search、answer 的内部顺序。
        - [ ] 能解释为什么索引应该复用。
        - [ ] 有证据时返回引用，无证据时明确不知道。
        - [ ] 能说明 evidence-only fallback 如何降低幻觉风险。
        """),
    ])


def build_phase4_acceptance() -> nbf.NotebookNode:
    return make_notebook([
        md("""
        # Phase 4.3：端到端验收、Demo 记录和最终交付

        ## 目标

        把用户故事变成自动化验收：健康检查、检索引用、无 LLM fallback、错误输入、Demo 记录和项目测试。完成后，四个阶段的产物就真正组成一个可运行项目。

        **本课交付：** `data/processed/phase4_acceptance_record.json`。
        """),
        md("""
        ## 1. 用户故事先于代码

        > 作为需要查阅技术资料的实习生，我输入一个问题，希望得到可回到原文的证据；如果知识库没有足够信息，系统应该明确说不知道，而不是编造。

        这个故事对应五类检查：服务可用、能搜索、有引用、无证据可解释、非法输入被拒绝。
        """),
        code(SETUP),
        code("""
        # 导入 FastAPI 测试客户端。
        from fastapi.testclient import TestClient

        # 导入应用工厂，创建独立测试应用。
        from phase4_mini_rag_system.app import create_app

        # 指定稳定的教学输入目录。
        input_directory = ROOT / "phase1_doc_parser" / "examples" / "input"

        # 创建应用并在启动阶段 ingest 文档。
        app = create_app(input_directory)

        # 创建可以发送 HTTP 请求的测试客户端。
        client = TestClient(app)

        # 输出应用已经准备好。
        print("acceptance app ready")
        """),
        md("""
        ## 2. 编写一组最小验收函数

        函数的价值是避免把相同断言复制到很多地方，同时保留每个用户故事的名字。每条断言都应该在失败时告诉我们哪个合同被破坏。
        """),
        code("""
        # 定义健康检查验收函数。
        def check_health():
            # 发送 health 请求。
            response = client.get("/health")

            # 断言 HTTP 层成功。
            assert response.status_code == 200, response.text

            # 读取 JSON 响应。
            payload = response.json()

            # 断言索引中有 Chunk。
            assert payload["chunks"] > 0

            # 返回结果供总记录使用。
            return payload

        # 定义检索引用验收函数。
        def check_search_citations():
            # 发送一条已知 Query。
            response = client.post("/search", json={"query": "Chunk overlap", "top_k": 3})

            # 断言请求成功。
            assert response.status_code == 200, response.text

            # 读取响应 JSON。
            payload = response.json()

            # 结果不能为空。
            assert payload["results"]

            # 检查引用的最小字段。
            required_fields = {"chunk_id", "source", "page", "score", "text"}
            assert required_fields <= payload["results"][0].keys()

            # 返回检索响应。
            return payload
        """),
        code("""
        # 定义聊天 fallback 验收函数。
        def check_chat_fallback():
            # 发送聊天请求；默认环境没有开启 LLM。
            response = client.post("/chat", json={"query": "Chunk overlap", "top_k": 3})

            # 请求本身应该成功。
            assert response.status_code == 200, response.text

            # 读取聊天响应。
            payload = response.json()

            # 必须返回引用，不能只返回一句无来源答案。
            assert payload["citations"]

            # 记录模式，允许 evidence-only 或显式 fallback。
            assert payload["mode"] in {"evidence-only", "evidence-only-fallback", "llm"}

            # 返回聊天响应供 Demo 记录。
            return payload

        # 定义非法 Query 验收函数。
        def check_invalid_query():
            # 发送空 Query。
            response = client.post("/search", json={"query": ""})

            # 空 Query 应该是 422，而不是服务器 500。
            assert response.status_code == 422

            # 返回状态码供记录。
            return response.status_code
        """),
        md("""
        ## 3. 执行完整验收并保存 Demo

        现在才运行刚才定义的检查。把响应中的索引版本、模式和 citation 摘要保存下来，形成一次可回放的项目证据。
        """),
        code("""
        # 执行健康检查并保存结果。
        health_payload = check_health()

        # 执行检索引用检查并保存结果。
        search_payload = check_search_citations()

        # 执行聊天 fallback 检查并保存结果。
        chat_payload = check_chat_fallback()

        # 执行非法输入检查并保存状态码。
        invalid_status = check_invalid_query()

        # 提取引用中的稳定字段，避免记录过大的正文。
        citation_summary = []
        for citation in chat_payload["citations"]:
            # 保存用户回溯原文所需的字段。
            citation_summary.append({"chunk_id": citation["chunk_id"], "source": citation["source"], "page": citation["page"], "score": citation["score"]})

        # 组合一次端到端验收记录。
        acceptance_record = {"health": health_payload, "search_trace_id": search_payload["trace_id"], "chat_trace_id": chat_payload["trace_id"], "chat_mode": chat_payload["mode"], "invalid_query_status": invalid_status, "citations": citation_summary}

        # 指定最终验收记录路径。
        acceptance_path = ROOT / "data" / "processed" / "phase4_acceptance_record.json"

        # 保存验收记录。
        acceptance_path.write_text(json.dumps(acceptance_record, ensure_ascii=False, indent=2), encoding="utf-8")

        # 打印交付路径和聊天模式。
        print("已生成:", acceptance_path)
        print("chat mode:", chat_payload["mode"])
        """),
        md("""
        ## 4. 运行项目测试：Notebook 验收之后还要有长期保护

        Notebook 断言适合边学边反馈，`pytest` 测试适合以后修改代码时持续保护行为。这里用当前环境运行项目测试，并检查返回码。
        """),
        code("""
        # 导入 subprocess，用它调用项目测试命令。
        import subprocess

        # 用当前 Python 解释器运行 pytest，避免切换到错误环境。
        test_process = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=ROOT, capture_output=True, text=True)

        # 打印 pytest 的最后几行，快速查看测试结果。
        print(test_process.stdout[-1000:])

        # 如果测试失败，打印标准错误帮助定位。
        if test_process.returncode != 0:
            print(test_process.stderr)

        # 所有项目测试必须通过，最终项目才算可交付。
        assert test_process.returncode == 0
        """),
        md("""
        ## 最终 0→1 项目验收

        你现在可以从根目录启动真实服务：

        ```powershell
        conda activate 'F:\\anaconda\\miniconda3\\envs\\ai-rag-internship'
        python -m phase4_mini_rag_system
        ```

        然后打开 `http://127.0.0.1:8000/`。最终项目已经具备：

        ```text
        文件解析 -> 中文分块 -> 稳定 Chunk ID -> BM25 检索
        -> 质量/性能实验 -> FastAPI -> evidence-only 引用回答
        ```

        如果要继续升级，下一条独立实验才是 BGE-M3 Dense、Faiss HNSW、ONNX/INT8 和真实 LLM；这些升级必须沿用已有 qrels、benchmark 和引用合同。
        """),
        md("""
        ## Phase 4 最终闸门

        - [ ] 能从用户故事解释每一条 API 断言。
        - [ ] `/health`、`/search`、`/chat` 和错误输入均已验证。
        - [ ] 答案包含 citations，且无证据时不会编造。
        - [ ] `phase4_acceptance_record.json` 已生成。
        - [ ] pytest 全部通过。

        至此，学习不是停在教程代码，而是完成了一套可运行、可解释、可测试的完整项目。
        """),
    ])


def main() -> None:
    # 定义 Notebook 文件和生成函数的对应关系。
    notebooks = {
        "00_mission_control.ipynb": (NOTEBOOK_ROOT, build_mission_control),
        "00_project_orientation.ipynb": (NOTEBOOK_ROOT, build_orientation),
        "phase1/01_files_and_documents.ipynb": (NOTEBOOK_ROOT / "phase1", build_phase1_files),
        "phase1/02_chunking_from_scratch.ipynb": (NOTEBOOK_ROOT / "phase1", build_phase1_chunking),
        "phase1/03_phase1_delivery.ipynb": (NOTEBOOK_ROOT / "phase1", build_phase1_delivery),
        "phase2/01_tokenization_and_bm25.ipynb": (NOTEBOOK_ROOT / "phase2", build_phase2_bm25),
        "phase2/02_dense_and_rrf.ipynb": (NOTEBOOK_ROOT / "phase2", build_phase2_dense_rrf),
        "phase2/03_phase2_evaluation.ipynb": (NOTEBOOK_ROOT / "phase2", build_phase2_evaluation),
        "phase3/01_metrics_and_timing.ipynb": (NOTEBOOK_ROOT / "phase3", build_phase3_timing),
        "phase3/02_single_variable_experiments.ipynb": (NOTEBOOK_ROOT / "phase3", build_phase3_experiments),
        "phase3/03_phase3_report.ipynb": (NOTEBOOK_ROOT / "phase3", build_phase3_report),
        "phase4/01_http_and_api_contract.ipynb": (NOTEBOOK_ROOT / "phase4", build_phase4_contract),
        "phase4/02_build_mini_rag.ipynb": (NOTEBOOK_ROOT / "phase4", build_phase4_service),
        "phase4/03_acceptance_and_demo.ipynb": (NOTEBOOK_ROOT / "phase4", build_phase4_acceptance),
    }

    # 逐个生成 Notebook，确保父目录提前存在。
    for relative_path, (directory, builder) in notebooks.items():
        # 创建当前 Notebook 所在目录。
        directory.mkdir(parents=True, exist_ok=True)

        # 调用对应构建函数得到 Notebook 对象。
        notebook = builder()

        # 计算最终文件路径。
        output_path = directory / Path(relative_path).name

        # 写入 ipynb 文件。
        nbf.write(notebook, output_path)

        # 输出生成结果和单元格数量。
        print("wrote", output_path, "cells=", len(notebook.cells))

    # 为四本历史阶段总览补上同一套任务卡和作品检查站，保持入口体验一致。
    overview_paths = {
        "phase1_document_parser.ipynb": "phase1",
        "phase2_hybrid_retrieval.ipynb": "phase2",
        "phase3_benchmark_evaluation.ipynb": "phase3",
        "phase4_mini_rag.ipynb": "phase4",
    }

    # 只处理生成器明确管理的四个总览，不触碰学员的 Untitled.ipynb。
    for filename in overview_paths:
        overview_path = NOTEBOOK_ROOT / filename
        if not overview_path.is_file():
            continue
        overview = nbf.read(overview_path, as_version=4)
        if any("Evidence Quest 任务卡" in cell.source for cell in overview.cells if cell.cell_type == "markdown"):
            continue
        enriched_overview = make_notebook(list(overview.cells))
        nbf.write(enriched_overview, overview_path)
        print("enriched", overview_path, "cells=", len(enriched_overview.cells))


if __name__ == "__main__":
    # 从命令行执行生成入口。
    main()

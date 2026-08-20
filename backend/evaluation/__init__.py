"""
CropWise 评测模块
==================

提供：
- 农业领域评测集加载
- AgriEval 评测运行器
- 评测报告生成与保存

使用示例：
    from evaluation import AgriEvalRunner, load_eval_set

    runner = AgriEvalRunner()
    report = runner.run_batch(retrieve_fn, generate_fn)
    runner.save_report(report)
"""

from evaluation.agri_eval_runner import (
    AgriEvalRunner,
    load_eval_set,
    quick_eval,
    EVAL_SUBSET_PATH,
)

__all__ = [
    "AgriEvalRunner",
    "load_eval_set",
    "quick_eval",
    "EVAL_SUBSET_PATH",
]

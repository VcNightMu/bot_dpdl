# 日期: 2026-06-01
# 开发者: 宝生玛格
# 功能: #流派指令格式化模块，展示9个固定流派列表
# 模型: mimo/mimo-v2.5

"""#流派 格式化模块

展示9个固定流派列表。
"""
from __future__ import annotations

from resolver.category import CATEGORIES


def format_categories() -> str:
    """格式化流派列表

    🏷️ 所有流派

    四星队
    精一满级四星队
    ...
    """
    header = "🏷️ 所有流派\n"
    items = "\n".join(CATEGORIES)
    return f"{header}\n{items}"

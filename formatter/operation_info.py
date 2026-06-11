# 日期: 2026-06-11
# 开发者: 橘雪莉
# 功能: #人数指令格式化模块，展示关卡各流派人数统计（表格格式）
# 模型: mimo/mimo-v2.5

"""#人数 格式化模块

展示关卡各流派人数统计。

格式：
📊 关卡代号 中文名

流派名称 | 普通 | 突袭
精二1级     1    1
精一满级    2    2
"""
from __future__ import annotations

from api_client.models import OperationInfoEntry


def format_operation_info(
    info: OperationInfoEntry,
    filter_categories: list[str] | None = None,
) -> str:
    """格式化关卡人数统计

    Args:
        info: API 返回的关卡统计信息
        filter_categories: 要展示的流派列表，None 则展示全部
    """
    # 标题行
    header = f"📊 {info.operation} {info.cn_name}"

    # 筛选要展示的流派
    if filter_categories:
        items = []
        for cat in filter_categories:
            if cat in info.categories:
                items.append((cat, info.categories[cat]))
    else:
        # 只展示内置流派（CATEGORIES），按最少人数升序排列
        from resolver.category import CATEGORIES, CATEGORY_ALIASES
        # 构建标准名集合（包含别名映射到的标准名）
        valid_cats = set(CATEGORIES)
        
        items = []
        for cat_name, stats in info.categories.items():
            if cat_name in valid_cats:
                items.append((cat_name, stats))
        
        # 按普通最少人数升序排列
        items.sort(key=lambda x: x[1].normal.num if x[1].normal.num > 0 else 999)

    if not items:
        return f"{header}\n\n没有找到流派数据 😅"

    has_challenge = info.has_challenge

    # 构建表格
    if has_challenge:
        # 有突袭：显示普通+突袭两列
        lines = [header, "", "流派名称         最少人数"]
        for cat_name, stats in items:
            normal_num = stats.normal.num
            challenge_num = stats.challenge.num
            normal_str = str(normal_num) if normal_num > 0 else "-"
            challenge_str = str(challenge_num) if challenge_num > 0 else "-"
            name_display = _pad_cn(cat_name, 14)
            lines.append(f"{name_display}普通{normal_str}  突袭{challenge_str}")
    else:
        # 无突袭：只显示普通列
        lines = [header, "", "流派名称         最少人数"]
        for cat_name, stats in items:
            normal_num = stats.normal.num
            normal_str = str(normal_num) if normal_num > 0 else "-"
            name_display = _pad_cn(cat_name, 14)
            lines.append(f"{name_display}{normal_str}")

    return "\n".join(lines)


def _pad_cn(text: str, width: int) -> str:
    """中文对齐填充，中文字符占2个宽度"""
    result = ""
    current_width = 0
    for ch in text:
        if '\u4e00' <= ch <= '\u9fff' or '\u3000' <= ch <= '\u303f' or '\uff00' <= ch <= '\uffef':
            current_width += 2
        else:
            current_width += 1
        result += ch
    # 补齐空格
    while current_width < width:
        result += " "
        current_width += 1
    return result

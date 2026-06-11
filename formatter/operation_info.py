# 日期: 2026-06-11
# 开发者: 橘雪莉
# 功能: #人数指令格式化模块，展示关卡各流派人数统计（表格格式）
# 模型: mimo/mimo-v2.5

"""#人数 格式化模块

展示关卡各流派人数统计。
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
    header = f"📊 {info.operation} {info.cn_name}"

    # 筛选要展示的流派
    if filter_categories:
        items = []
        for cat in filter_categories:
            if cat in info.categories:
                items.append((cat, info.categories[cat]))
    else:
        from resolver.category import CATEGORIES
        valid_cats = set(CATEGORIES)
        items = [(k, v) for k, v in info.categories.items() if k in valid_cats]
        # 双关键字排序：普通人数升序，普通相同则突袭人数升序（0视为最大）
        def sort_key(x: tuple) -> tuple[int, int]:
            n = x[1].normal.num
            c = x[1].challenge.num
            return (n if n > 0 else 999, c if c > 0 else 999)
        items.sort(key=sort_key)

    if not items:
        return f"{header}\n\n没有找到流派数据 😅"

    has_challenge = info.has_challenge

    if has_challenge:
        return _format_with_challenge(header, items)
    else:
        return _format_without_challenge(header, items)


def _format_with_challenge(header: str, items: list) -> str:
    """有突袭的关卡：显示普通+突袭两列"""
    # 先计算所有行，用于确定列宽
    rows = []
    for cat_name, stats in items:
        n = stats.normal.num
        c = stats.challenge.num
        rows.append((cat_name, n, c))

    # 流派名称最大显示宽度（中文字符占2）
    name_width = max(_display_width(name) for name, _, _ in rows) if rows else 0
    name_width = max(name_width, 6)  # 至少 "流派名称" 的宽度

    # 数字列宽度
    num_width = 4

    lines = [header, ""]

    # 表头
    name_header = "流派名称".ljust(name_width + 2)
    lines.append(f"{name_header}普通  突袭")

    # 分隔线
    lines.append("─" * (name_width + 2 + num_width * 2 + 2))

    # 数据行
    for name, n, c in rows:
        n_str = str(n) if n > 0 else "-"
        c_str = str(c) if c > 0 else "-"

        # 流派名称左对齐，数字右对齐
        name_padded = _pad_cn_right(name, name_width + 2)
        n_padded = n_str.rjust(num_width)
        c_padded = c_str.rjust(num_width)

        lines.append(f"{name_padded}{n_padded}  {c_padded}")

    return "\n".join(lines)


def _format_without_challenge(header: str, items: list) -> str:
    """无突袭的关卡：只显示一列"""
    rows = []
    for cat_name, stats in items:
        n = stats.normal.num
        rows.append((cat_name, n))

    name_width = max(_display_width(name) for name, _ in rows) if rows else 0
    name_width = max(name_width, 6)

    lines = [header, ""]

    name_header = "流派名称".ljust(name_width + 2)
    lines.append(f"{name_header}最少人数")
    lines.append("─" * (name_width + 2 + 6))

    for name, n in rows:
        n_str = str(n) if n > 0 else "-"
        name_padded = _pad_cn_right(name, name_width + 2)
        n_padded = n_str.rjust(4)
        lines.append(f"{name_padded}{n_padded}")

    return "\n".join(lines)


def _display_width(text: str) -> int:
    """计算字符串显示宽度（中文占2）"""
    width = 0
    for ch in text:
        if '\u4e00' <= ch <= '\u9fff' or '\u3000' <= ch <= '\u303f' or '\uff00' <= ch <= '\uffef':
            width += 2
        else:
            width += 1
    return width


def _pad_cn_right(text: str, target_width: int) -> str:
    """中文右填充到指定宽度"""
    current = _display_width(text)
    padding = target_width - current
    return text + " " * max(0, padding)

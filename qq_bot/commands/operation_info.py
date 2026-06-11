# 日期: 2026-06-11
# 开发者: 橘雪莉
# 功能: #人数指令 - 查询关卡各流派人数统计
# 模型: mimo/mimo-v2.5

"""#人数 指令 - 查关卡人数统计"""
import logging
import re

from api_client import WikiClient
from config import config
from resolver.category import normalize_category, CATEGORIES
from resolver.duplicate import check_duplicate_operation
from formatter.operation_info import format_operation_info

logger = logging.getLogger(__name__)


async def handle_operation_info(match: re.Match, group_id: int, user_id: int, operation_index: dict | None = None) -> str:
    """
    处理 #人数 指令
    格式: #人数 <关卡> [流派1] [流派2] ...
    示例: #人数 M8-8 四星队 精一满级
    """
    args = match.group(1).strip()

    if not args:
        return (
            "缺少关卡参数，格式：#人数 <关卡> [流派1] [流派2] ...\n"
            "示例：#人数 M8-8 四星队 精一满级\n"
            "不指定流派则展示所有流派"
        )

    parts = args.split()
    operation_input = parts[0]

    # 解析流派参数（支持多个）
    filter_categories = []
    for cat_input in parts[1:]:
        cat = normalize_category(cat_input)
        if not cat:
            return f"未找到流派 \"{cat_input}\"，发送 #流派 查看所有流派"
        filter_categories.append(cat)

    # 从 operation_index 获取 operation 和 cn_name
    if not operation_index:
        return "关卡索引未就绪，请稍后重试"

    # 检测重复关卡代号
    dup_msg = check_duplicate_operation(operation_input, operation_index, cmd_name="#人数")
    if dup_msg:
        return dup_msg

    # 精确匹配关卡
    from resolver.operation import normalize_operation
    normalized = normalize_operation(operation_input)

    entry = operation_index.get("by_operation", {}).get(normalized)
    if not entry:
        # 尝试中文名匹配
        entry = operation_index.get("by_cn_name", {}).get(operation_input.strip())

    if not entry:
        return f"未找到关卡 \"{operation_input}\""

    operation = entry["operation"]
    cn_name = entry["cn_name"]

    logger.info(f"#人数指令: operation={operation}, cn_name={cn_name}, filter={filter_categories}")

    try:
        # 调用wiki API查询人数统计
        async with WikiClient(base_url=config.wiki_base_url, token=config.wiki_api_token) as client:
            result = await client.operation_info_entry(operation=operation, cn_name=cn_name)

            # 格式化返回结果
            return format_operation_info(result, filter_categories if filter_categories else None)
    except Exception as e:
        logger.error(f"查询人数统计失败: {e}", exc_info=True)
        return "查询失败，请稍后重试"

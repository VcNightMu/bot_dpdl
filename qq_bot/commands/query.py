# 日期: 2026-06-01
# 开发者: 橘雪莉
# 功能: #查指令 - 按关卡代号和流派查询最佳记录
# 模型: mimo/mimo-v2.5

"""#查 指令 - 按关卡查最佳记录"""
import logging
import re
from dataclasses import asdict

from api_client import WikiClient
from resolver.operation import normalize_operation
from resolver.category import normalize_category
from resolver.duplicate import check_duplicate_operation
from formatter.record import format_records
from config import config

logger = logging.getLogger(__name__)


async def handle_query(match: re.Match, group_id: int, user_id: int, operation_index: dict | None = None) -> str | list[str]:
    """
    处理 #查 指令
    格式: #查 <关卡> <流派>
    示例: #查 H11-1 四星队
    """
    args = match.group(1).strip()
    
    # 解析参数
    parts = args.split()
    if len(parts) < 2:
        return (
            "缺少流派参数，格式：#查 <关卡> <流派>\n"
            "发送 #流派 查看所有流派"
        )
    
    operation_input = parts[0]
    category_input = parts[1]
    
    # 归一流派名
    category = normalize_category(category_input)
    if not category:
        return f"未找到流派 \"{category_input}\"，发送 #流派 查看所有流派"
    
    # 检测重复关卡代号
    dup_msg = check_duplicate_operation(operation_input, operation_index)
    if dup_msg:
        return dup_msg
    
    # 归一化关卡代号
    operation = normalize_operation(operation_input)
    
    logger.info(f"#查指令: operation={operation}, category={category}")
    
    try:
        # 调用wiki API查询记录
        async with WikiClient(base_url=config.wiki_base_url, token=config.wiki_api_token) as client:
            result = await client.query_records(operation=operation, category=category)
            
            # 格式化返回结果（BotRecord dataclass → dict）
            records_dict = [asdict(r) for r in result.records]
            return format_records(records_dict, result.count_valid)
    except Exception as e:
        logger.error(f"查询记录失败: {e}", exc_info=True)
        return "查询失败，请稍后重试"

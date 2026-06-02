# 日期: 2026-06-01
# 开发者: 橘雪莉
# 功能: 指令路由与分发 - 将群消息正则匹配到对应指令处理函数
# 模型: mimo/mimo-v2.5

"""指令路由+分发"""
import logging
import re
from typing import Callable, Awaitable

logger = logging.getLogger(__name__)


class CommandHandler:
    """指令处理器"""
    
    def __init__(self):
        # 指令注册表：正则模式 -> 处理函数
        self.commands: list[tuple[re.Pattern, Callable]] = []
        self._register_commands()
    
    def _register_commands(self):
        """注册所有指令"""
        from qq_bot.commands.query import handle_query
        from qq_bot.commands.uncleared import handle_uncleared
        from qq_bot.commands.stale import handle_stale
        from qq_bot.commands.category import handle_category
        from qq_bot.commands.help import handle_help
        
        # 指令匹配规则（顺序重要：无参数的放前面，有参数的放后面）
        self.commands = [
            # 无参数分支 - 返回错误提示
            (re.compile(r"^#查\s*$"), self._no_args_query),
            (re.compile(r"^#未通关\s*$"), self._no_args_uncleared),
            (re.compile(r"^#待压人\s*$"), self._no_args_stale),
            # 有参数分支
            (re.compile(r"^#查\s+(.+)"), handle_query),
            (re.compile(r"^#未通关\s+(.+)"), handle_uncleared),
            (re.compile(r"^#待压人\s+(.+)"), handle_stale),
            (re.compile(r"^#流派\s*$"), handle_category),
            (re.compile(r"^#help$"), handle_help),
        ]
    
    async def handle(self, raw_msg: str | list, group_id: int, user_id: int, operation_index: dict | None = None) -> str | list[str] | None:
        """处理指令"""
        # 兼容 OneBot11 列表格式和纯文本格式
        if isinstance(raw_msg, list):
            parts = []
            for seg in raw_msg:
                if isinstance(seg, dict) and seg.get("type") == "text":
                    parts.append(seg.get("data", {}).get("text", ""))
            msg = "".join(parts)
        else:
            msg = raw_msg.strip()
        
        # 匹配指令
        for pattern, handler in self.commands:
            match = pattern.match(msg)
            if match:
                logger.info(f"匹配到指令: {pattern.pattern}")
                try:
                    return await handler(match, group_id, user_id, operation_index)
                except Exception as e:
                    logger.error(f"执行指令失败: {e}", exc_info=True)
                    return "指令执行失败，请稍后重试"
        
        # 没有匹配到任何指令
        return None
    
    # -- 无参数错误提示 --
    @staticmethod
    async def _no_args_query(match: re.Match, group_id: int, user_id: int, operation_index: dict | None = None) -> str:
        return "缺少参数，格式：#查 <关卡> <流派>\n发送 #流派 查看所有流派"

    @staticmethod
    async def _no_args_uncleared(match: re.Match, group_id: int, user_id: int, operation_index: dict | None = None) -> str:
        return "缺少参数，格式：#未通关 <活动名> <流派>\n发送 #流派 查看所有流派"

    @staticmethod
    async def _no_args_stale(match: re.Match, group_id: int, user_id: int, operation_index: dict | None = None) -> str:
        return "缺少参数，格式：#待压人 <活动名> <流派> [天数]\n发送 #流派 查看所有流派"

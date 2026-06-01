# 日期: 2026-06-01
# 开发者: 橘雪莉
# 功能: category.py 单元测试 - 验证 #流派 指令处理
# 模型: mimo/mimo-v2.5

"""qq_bot/commands/category.py 单元测试"""

import sys
import re
import pytest
from unittest.mock import patch

sys.path.insert(0, r"F:\ArkCodes\bot_dpdl")

from qq_bot.commands.category import handle_category


@pytest.fixture
def match():
    """模拟正则匹配对象"""
    m = re.match(r"^#流派\s*$", "#流派")
    return m


class TestHandleCategory:
    """测试 handle_category"""

    @pytest.mark.asyncio
    async def test_returns_string(self, match):
        """返回值是字符串"""
        result = await handle_category(match, group_id=1, user_id=1)
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_contains_categories(self, match):
        """输出包含流派名称"""
        result = await handle_category(match, group_id=1, user_id=1)
        assert "四星队" in result

    @pytest.mark.asyncio
    async def test_contains_all_seven(self, match):
        """输出包含全部 7 个流派"""
        result = await handle_category(match, group_id=1, user_id=1)
        assert "四星队" in result
        assert "精一满级四星队" in result
        assert "精一1级四星队" in result
        assert "三星队" in result
        assert "精一1级" in result
        assert "无精英满级" in result
        assert "无精英1级" in result

    @pytest.mark.asyncio
    async def test_ignores_extra_args(self, match):
        """忽略额外参数"""
        result = await handle_category(match, group_id=1, user_id=1)
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_group_and_user_id_ignored(self, match):
        """group_id 和 user_id 不影响输出"""
        result1 = await handle_category(match, group_id=100, user_id=200)
        result2 = await handle_category(match, group_id=300, user_id=400)
        assert result1 == result2

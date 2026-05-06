import asyncio
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.event.filter import EventMessageType
from astrbot.api.star import Context, Star, register
from astrbot.api import logger

@register(
    "astrbot_plugin_auto_recall",
    "YourName",
    "自动撤回机器人自身消息，支持延迟、关键词过滤和群白名单",
    "1.1.0"
)
class AutoRecallPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        logger.info("自动撤回插件已初始化！")

    @filter.event_message_type(EventMessageType.ALL)
    async def on_message(self, event: AstrMessageEvent):
        message_obj = event.message_obj

        if message_obj.self_id != message_obj.sender.user_id:
            return

        # ---------- 群白名单检查（从逗号分隔字符串解析）----------
        whitelist_str = self.config.get('group_whitelist', '')
        if whitelist_str.strip():
            whitelist = [x.strip() for x in whitelist_str.split(',') if x.strip()]
            group_id = None
            if hasattr(message_obj, 'group_id'):
                group_id = str(message_obj.group_id)
            if not group_id and hasattr(event, 'group_id'):
                group_id = str(event.group_id)
            if not group_id or group_id not in whitelist:
                return

        # ---------- 关键词检查 ----------
        keywords_str = self.config.get('keywords', '')
        if keywords_str.strip():
            keywords = [x.strip() for x in keywords_str.split(',') if x.strip()]
            msg_text = message_obj.get_plain_text() if hasattr(message_obj, 'get_plain_text') else getattr(message_obj, 'message', '')
            if not any(kw in msg_text for kw in keywords):
                return

        # ---------- 撤回延迟 ----------
        delay_str = self.config.get('recall_delay', '0.1')
        try:
            delay = float(delay_str)
        except:
            delay = 0.1

        try:
            await asyncio.sleep(delay)
            await event.recall_message()
            logger.info(f"已撤回消息，消息ID: {message_obj.message_id}")
        except Exception as e:
            logger.error(f"撤回消息时出错: {e}")

    async def terminate(self):
        logger.info("自动撤回插件已停止。")

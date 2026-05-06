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

        # 只处理机器人自己发送的消息
        if message_obj.self_id != message_obj.sender.user_id:
            return

        # ---------- 群白名单检查 ----------
        group_id = None
        if hasattr(message_obj, 'group_id'):
            group_id = str(message_obj.group_id)
        # 有些平台 group_id 可能在 event 上
        if not group_id and hasattr(event, 'group_id'):
            group_id = str(event.group_id)

        whitelist = self.config.get('group_whitelist', [])
        if whitelist:
            # 有白名单，但当前消息不是群消息，直接忽略
            if not group_id:
                return
            # 是群消息但不在白名单里，也忽略
            if group_id not in [str(g) for g in whitelist]:
                return

        # ---------- 关键词检查 ----------
        keywords = self.config.get('keywords', [])
        if keywords:
            # 获取消息文本
            msg_text = message_obj.get_plain_text() if hasattr(message_obj, 'get_plain_text') else getattr(message_obj, 'message', '')
            if not any(keyword in msg_text for keyword in keywords):
                # 没有包含任何一个关键词，不撤回
                return

        # ---------- 执行撤回 ----------
        delay = self.config.get('recall_delay', 0.1)
        try:
            await asyncio.sleep(delay)
            await event.recall_message()
            logger.info(f"已撤回消息，消息ID: {message_obj.message_id}")
        except Exception as e:
            logger.error(f"撤回消息时出错: {e}")

    async def terminate(self):
        logger.info("自动撤回插件已停止。")

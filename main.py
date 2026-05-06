import asyncio
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.event.filter import EventMessageType
from astrbot.api.star import Context, Star, register
from astrbot.api import logger

@register("astrbot_plugin_auto_recall", "YourName", "一个自动撤回机器人自身消息的插件", "1.0.0")
class AutoRecallPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        logger.info("自动撤回插件已初始化！")

    @filter.event_message_type(EventMessageType.ALL)
    async def on_message(self, event: AstrMessageEvent):
        message_obj = event.message_obj

        if message_obj.self_id == message_obj.sender.user_id:
            try:
                await asyncio.sleep(0.1)
                await event.recall_message()
                logger.info(f"已尝试撤回机器人自身消息，消息ID: {message_obj.message_id}")
            except Exception as e:
                logger.error(f"撤回消息时出错: {e}")

    async def terminate(self):
        logger.info("自动撤回插件已停止。")

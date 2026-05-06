import asyncio
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger

@register("astrbot_plugin_auto_recall", "YourName", "一个自动撤回机器人自身消息的插件", "1.0.0")
class AutoRecallPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        logger.info("自动撤回插件已初始化！")

    # 核心功能：监听所有消息事件
    @filter.on_message()
    async def on_message(self, event: AstrMessageEvent):
        # 1. 获取消息对象
        message_obj = event.message_obj
        
        # 2. 判断消息发送者是不是机器人自己
        if message_obj.self_id == message_obj.sender.user_id:
            try:
                # 3. 执行撤回操作，设置一个很小的延迟，防止网络波动导致指令失败
                await asyncio.sleep(0.1)
                await event.recall_message()
                logger.info(f"已尝试撤回机器人自身消息，消息ID: {message_obj.message_id}")
            except Exception as e:
                logger.error(f"撤回消息时出错: {e}")

    async def terminate(self):
        '''插件被卸载/停用时会调用此方法，可以在这里做一些清理工作'''
        logger.info("自动撤回插件已停止。")

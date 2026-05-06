import asyncio
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.api.all import *

@register("astrbot_plugin_auto_recall", "YourName", "一个自动撤回机器人自身消息的强大插件", "1.2.0")
class AutoRecallPlugin(Star):
    def __init__(self, context: Context, config: dict):
        super().__init__(context)
        self.config = config
        logger.info("自动撤回增强版插件已初始化！")

    @filter.on_decorating_result()
    async def on_recall(self, event: AstrMessageEvent):
        # 群白名单检查
        group_whitelist = self.config.get('group_whitelist', [])
        if group_whitelist:
            group_id = event.get_group_id()
            if group_id not in group_whitelist:
                return

        result = event.get_result()
        if not result or not result.chain:
            return
            
        # 提取纯文本
        plain_text = ""
        for seg in result.chain:
            if isinstance(seg, Plain):
                plain_text += seg.text

        # 检查关键词
        should_recall = False
        recall_words = self.config.get('recall_words', [])
        if recall_words and any(word in plain_text for word in recall_words):
            should_recall = True

        # 检查长度
        max_len = self.config.get('max_plain_len', 0)
        if max_len > 0 and len(plain_text) > max_len:
            should_recall = True

        if should_recall:
            delay = self.config.get('recall_time', 0.5)
            client = event.bot
            # 发送消息并获取 message_id（适配 aiocqhttp 逻辑）
            send_result = None
            if group_id := event.get_group_id():
                send_result = await client.send_group_msg(group_id=int(group_id), message=event._parse_onebot_json(MessageChain(chain=result.chain)))
            elif user_id := event.get_sender_id():
                send_result = await client.send_private_msg(user_id=int(user_id), message=event._parse_onebot_json(MessageChain(chain=result.chain)))

            if send_result and (message_id := send_result.get("message_id")):
                async def recall_task():
                    await asyncio.sleep(delay)
                    try:
                        await client.delete_msg(message_id=message_id)
                        logger.info(f"已自动撤回消息: {message_id}")
                    except Exception as e:
                        logger.error(f"撤回消息失败: {e}")
                asyncio.create_task(recall_task())
                # 清空原消息链，阻止其被正常发送
                result.chain.clear()
                event.stop_event()

    async def terminate(self):
        logger.info("自动撤回插件已停止。")

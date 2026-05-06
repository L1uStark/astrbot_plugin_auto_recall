import asyncio
from astrbot.api.event import filter, AstrMessageEvent, EventMessageType
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.api.all import *  # 包含 Plain, MessageChain 等

@register("astrbot_plugin_auto_recall", "L1uStark", "自动撤回机器人自身消息，支持延迟、关键词过滤和群白名单，同时可撤回MaiBot的消息", "1.3.0")
class AutoRecallPlugin(Star):
    def __init__(self, context: Context, config: dict):
        super().__init__(context)
        self.config = config
        logger.info("自动撤回增强版插件已初始化！")

    # ---------- 功能 1：在 AstrBot 自己的回复发送前拦截并控制撤回 ----------
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

        # 关键词与长度检查
        should_recall = False
        recall_words = self.config.get('recall_words', [])
        if recall_words and any(word in plain_text for word in recall_words):
            should_recall = True
        max_len = self.config.get('max_plain_len', 0)
        if max_len > 0 and len(plain_text) > max_len:
            should_recall = True

        if not should_recall:
            return

        delay = self.config.get('recall_time', 0.5)
        client = event.bot

        # 手动发送消息并获取 message_id（适用于 OneBot v11 / aiocqhttp）
        send_result = None
        if group_id := event.get_group_id():
            send_result = await client.send_group_msg(
                group_id=int(group_id),
                message=event._parse_onebot_json(MessageChain(chain=result.chain))
            )
        elif user_id := event.get_sender_id():
            send_result = await client.send_private_msg(
                user_id=int(user_id),
                message=event._parse_onebot_json(MessageChain(chain=result.chain))
            )

        if send_result and (message_id := send_result.get("message_id")):
            async def recall_task():
                await asyncio.sleep(delay)
                try:
                    await client.delete_msg(message_id=message_id)
                    logger.info(f"已自动撤回消息: {message_id}")
                except Exception as e:
                    logger.error(f"撤回消息失败: {e}")

            asyncio.create_task(recall_task())
            # 阻止原始消息继续被发送
            result.chain.clear()
            event.stop_event()


    # ---------- 功能 2：监听并撤回 MaiBot（或其他客户端）发出的消息 ----------
    @filter.event_message_type(EventMessageType.ALL)
    async def on_bot_message(self, event: AstrMessageEvent):
        # 获取当前机器人的 QQ 号（self_id）和消息发送者的 QQ 号（sender_id）
        self_id = event.get_self_id()
        sender_id = event.get_sender_id()

        # 关键判断：只处理发送者是机器人自己的消息（这些消息可能是 MaiBot 或其他客户端发出的）
        if str(sender_id) != str(self_id):
            return

        # 获取这条消息的 message_id，撤回时需要用到
        message_obj = event.message_obj
        if not message_obj:
            return
        message_id = message_obj.message_id

        # ---------- 应用与功能 1 完全相同的撤回规则 ----------
        # 群白名单检查
        group_whitelist = self.config.get('group_whitelist', [])
        if group_whitelist:
            group_id = event.get_group_id()
            if group_id not in group_whitelist:
                return

        # 提取消息文本（用于关键词和长度检查）
        msg_text = ""
        if hasattr(message_obj, 'get_plain_text'):
            msg_text = message_obj.get_plain_text()
        elif hasattr(message_obj, 'message'):
            msg_text = str(message_obj.message)

        should_recall = False
        # 关键词检查
        recall_words = self.config.get('recall_words', [])
        if recall_words and any(word in msg_text for word in recall_words):
            should_recall = True
        # 长度检查
        max_len = self.config.get('max_plain_len', 0)
        if max_len > 0 and len(msg_text) > max_len:
            should_recall = True

        if not should_recall:
            return

        # 延迟撤回
        delay = self.config.get('recall_time', 0.5)
        try:
            await asyncio.sleep(delay)
            await event.bot.delete_msg(message_id=message_id)
            logger.info(f"已撤回机器人(MaiBot等)消息: {message_id}")
        except Exception as e:
            logger.error(f"撤回机器人消息失败: {e}")


    async def terminate(self):
        logger.info("自动撤回插件已停止。")

from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger, AstrBotConfig
import time

@register("deal-with-aubergine", "HakimYu", "一个简单的 禁言 插件", "1.0.2")
class MyPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        # 使用字典记录每个用户的消息计数
        self.user_message_counts = {}
        # 使用字典记录每个用户的最后消息时间
        self.user_last_message_times = {}

    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    async def on_group_message(self, event: AstrMessageEvent):
        # 判断消息是否来自指定群 指定 人
        # logger.info(f"消息来自群: {event.get_group_id()}, 消息来自用户: {event.get_sender_id()}")
        if event.get_group_id() not in self.config.group_ids or event.get_sender_id() not in self.config.user_ids:
            return

        user_id = event.get_sender_id()
        current_time = time.time()

        # 获取用户的消息计数和最后消息时间，如果不存在则初始化为0
        message_count = self.user_message_counts.get(user_id, 0)
        last_message_time = self.user_last_message_times.get(user_id, 0)

        # 判断消息是否发送频率过高
        if message_count > self.config.message_limit and current_time - last_message_time < self.config.time_limit:
            if event.get_platform_name() == "aiocqhttp":
                # 使用 aiocqhttp 原生 API 进行禁言
                from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import AiocqhttpMessageEvent
                assert isinstance(event, AiocqhttpMessageEvent)
                client = event.bot
                payloads = {
                    "group_id": int(event.get_group_id()),
                    "user_id": int(event.get_sender_id()),
                    "duration": self.config.ban_duration  # 使用配置的禁言时长
                }
                ret = await client.api.call_action('set_group_ban', **payloads)
                # 重置该用户的消息计数和时间
                self.user_message_counts[user_id] = 0
                self.user_last_message_times[user_id] = 0
                logger.info(f"ret: {ret}")
                logger.info(f"发送过快，禁言: {event.get_sender_id()} {self.config.ban_duration}秒")
                yield event.plain_result(f"塔菲制裁你喵！禁言{self.config.ban_duration}秒")
            return

        # 更新用户的消息计数和时间
        self.user_message_counts[user_id] = message_count + 1
        self.user_last_message_times[user_id] = current_time
        return

    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("add-deal-with-person")
    async def add_deal_with_person(self, event: AstrMessageEvent, user_id: str):
        if user_id in self.config.user_ids:
            yield event.plain_result(f" {user_id} 已经在禁言列表中")
            return
        self.config.user_ids.append(user_id)
        self.config.save_config()
        yield event.plain_result(f" 已添加 {user_id} 到禁言列表")
        return

    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("remove-deal-with-person")
    async def remove_deal_with_person(self, event: AstrMessageEvent, user_id: str):
        if user_id not in self.config.user_ids:
            yield event.plain_result(f" {user_id} 不在禁言列表中")
            return
        self.config.user_ids.remove(user_id)
        self.config.save_config()
        yield event.plain_result(f" 已从禁言列表移除 {user_id}")
        return

    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("add-deal-with-group")
    async def add_deal_with_group(self, event: AstrMessageEvent, group_id: str):
        if group_id in self.config.group_ids:
            yield event.plain_result(f" {group_id} 已经在禁言列表中")
            return
        self.config.group_ids.append(group_id)
        self.config.save_config()
        yield event.plain_result(f" 已添加 {group_id} 到禁言列表")
        return

    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("remove-deal-with-group")
    async def remove_deal_with_group(self, event: AstrMessageEvent, group_id: str):
        if group_id not in self.config.group_ids:
            yield event.plain_result(f" {group_id} 不在禁言列表中")
            return
        self.config.group_ids.remove(group_id)
        self.config.save_config()
        yield event.plain_result(f" 已从禁言列表移除 {group_id}")
        return

    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("set-message-limit")
    async def set_message_limit(self, event: AstrMessageEvent, limit: int):
        if limit < 1:
            yield event.plain_result("消息限制必须大于0")
            return
        self.config.message_limit = limit
        self.config.save_config()
        yield event.plain_result(f"已设置消息限制为 {limit} 条")
        return

    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("set-time-limit")
    async def set_time_limit(self, event: AstrMessageEvent, limit: int):
        if limit < 1:
            yield event.plain_result("时间限制必须大于0")
            return
        self.config.time_limit = limit
        self.config.save_config()
        yield event.plain_result(f"已设置时间限制为 {limit} 秒")
        return

    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("set-ban-duration")
    async def set_ban_duration(self, event: AstrMessageEvent, duration: int):
        if duration < 1:
            yield event.plain_result("禁言时长必须大于0")
            return
        self.config.ban_duration = duration
        self.config.save_config()
        yield event.plain_result(f"已设置禁言时长为 {duration} 秒")
        return

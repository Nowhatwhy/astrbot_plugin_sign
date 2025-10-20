from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
import astrbot.api.message_components as Comp
from astrbot.api import logger
from astrbot.api import AstrBotConfig
from datetime import time
import re
import sign
_TIME_RE = re.compile(r"^\s*(\d{1,2})[:：](\d{1,2})(?:[:：](\d{1,2}))?\s*$")
@register("helloworld", "YourName", "一个简单的 Hello World 插件", "1.0.0")
class MyPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
    def parse_time_hms(self, s: str) -> time:
        m = _TIME_RE.match(s)
        if not m:
            raise ValueError("时间格式应为 HH:MM 或 HH:MM:SS，例如 21:40 或 08:05:00")
        h, mi, sec = int(m.group(1)), int(m.group(2)), int(m.group(3) or 0)
        if not (0 <= h <= 23 and 0 <= mi <= 59 and 0 <= sec <= 59):
            raise ValueError("时间数值不合法（小时0-23，分钟/秒0-59）")
        return time(hour=h, minute=mi, second=sec)
    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""
        
    
    # 注册指令的装饰器。指令名为 helloworld。注册成功后，发送 `/helloworld` 就会触发这个指令，并回复 `你好, {user_name}!`
    @filter.command("helloworld")
    async def helloworld(self, event: AstrMessageEvent):
        """这是一个 hello world 指令""" # 这是 handler 的描述，将会被解析方便用户了解插件内容。建议填写。
        user_name = event.get_sender_name()
        user_id = event.get_sender_id()
        message_str = event.message_str # 用户发的纯文本消息字符串
        message_chain = event.get_messages() # 用户所发的消息的消息链 # from astrbot.api.message_components import *
        logger.info(message_chain)
        yield event.chain_result([Comp.At(qq=user_id), Comp.Plain(text="尼玛")])

    @filter.command("sign")
    async def sign(self, event: AstrMessageEvent):
        user_id = event.get_sender_id()
        result = await sign.sign_single(int(user_id))
        yield event.plain_result(result.__str__())
    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""

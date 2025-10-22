from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
import astrbot.api.message_components as Comp
from astrbot.api import logger
from astrbot.api import AstrBotConfig
from datetime import time
from astrbot.api.event import MessageChain
import re
from . import sign
import asyncio
from .result import Result
from . import daily_sign
from datetime import datetime, timedelta
_TIME_RE = re.compile(r"^\s*(\d{1,2})[:：](\d{1,2})(?:[:：](\d{1,2}))?\s*$")
@register("astrbot_plugin_sign", "Nowhatwhy", "一个简单签到", "1.0.0")
class MyPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        self.stop_event = asyncio.Event()
        asyncio.create_task(self.auto_sign_task())
    def parse_time_hms(self, s: str) -> time:
        m = _TIME_RE.match(s)
        if not m:
            raise ValueError("时间格式应为 HH:MM 或 HH:MM:SS，例如 21:40 或 08:05:00")
        h, mi, sec = int(m.group(1)), int(m.group(2)), int(m.group(3) or 0)
        if not (0 <= h <= 23 and 0 <= mi <= 59 and 0 <= sec <= 59):
            raise ValueError("时间数值不合法（小时0-23，分钟/秒0-59）")
        return time(hour=h, minute=mi, second=sec)
    def next_run_time(self,) -> datetime:
        now = datetime.now()
        try:
            run_time= self.parse_time_hms(self.config.get('sign_time', '21:30:00'))
        except ValueError:
            run_time = time(hour=21, minute=30, second=0)
        
        today_run = now.replace(hour=run_time.hour, minute=run_time.minute, second=run_time.second, microsecond=0)
        if today_run > now:
            return today_run
        else:
            return today_run + timedelta(days=1)
    async def send_sign_message(self, results: list[Result]):
        """发送签到结果消息"""
        session_str = f"default:GroupMessage:{self.config.get('group_id')}"
        results_success: list['Result'] = []
        results_fail: list['Result'] = []
        for res in results:
            if res.success:
                results_success.append(res)
            else:
                results_fail.append(res)
        success_message_chain = MessageChain()
        success_message_chain.message("签到成功用户列表：\n\n" + "\n\n".join(map(str, results_success)))
        fail_message_chain = MessageChain()
        fail_message_chain.message("签到失败用户列表：\n\n" + "\n\n".join(map(str, results_fail)))
        at_message_chain = MessageChain()
        for res in results_fail:
            at_message_chain.at(res.user_name, res.user_id)
        await self.context.send_message(session_str, MessageChain().at("123", "736644851"))
        if results_success:
            await self.context.send_message(session_str, success_message_chain)
        if results_fail:
            await self.context.send_message(session_str, at_message_chain)
            await self.context.send_message(session_str, fail_message_chain)
            await self.context.send_message(session_str, MessageChain().message("请签到失败用户检查原因后使用/sign指令重新签到"))
    async def auto_sign_task(self):
        """自动签到任务"""
        while not self.stop_event.is_set():
            now = datetime.now()
            wait_seconds = (self.next_run_time() - now).total_seconds()
            logger.info(f"下次自动签到时间：{self.next_run_time().strftime('%Y-%m-%d %H:%M:%S')}，等待 {wait_seconds} 秒")
            try:
                await asyncio.wait_for(self.stop_event.wait(), timeout=wait_seconds)
                if self.stop_event.is_set():
                    break
            except asyncio.TimeoutError:
                pass  # 超时，继续执行签到任务
            await self.send_sign_message(await sign.sign_all())
    
    # 注册指令的装饰器。指令名为 helloworld。注册成功后，发送 `/helloworld` 就会触发这个指令，并回复 `你好, {user_name}!`
    @filter.command("helloworld")
    async def helloworld(self, event: AstrMessageEvent, message: str = ""):
        """这是一个 hello world 指令""" # 这是 handler 的描述，将会被解析方便用户了解插件内容。建议填写。
        user_name = event.get_sender_name()
        user_id = event.get_sender_id()
        message_str = event.message_str # 用户发的纯文本消息字符串
        message_chain = event.get_messages() # 用户所发的消息的消息链 # from astrbot.api.message_components import *
        logger.info(message_chain)
        if message:
            yield event.plain_result(f"你好, {user_name}! 你刚才发送了消息: {message_str}")
        else:
            yield event.plain_result(f"你好, {user_name}! 你刚才没有发送任何消息")


    @filter.command("sign")
    async def sign(self, event: AstrMessageEvent, user_id: str = ""):
        if user_id == "":
            user_id = event.get_sender_id()
        try:
            int(user_id)
        except ValueError:
            yield event.plain_result("用户ID应为整数")
            return
        result = await sign.sign_single(int(user_id))
        yield event.plain_result(result.__str__())
    @filter.command("sign_all")
    async def sign_all(self, event: AstrMessageEvent):
        user_id = event.get_sender_id()
        if user_id != self.config.get('admin'):
            yield event.plain_result("只有管理员才能使用此指令")
            return
        yield event.plain_result("管理员正在为所有用户执行签到，请稍候...")
        results = await sign.sign_all()
        yield event.plain_result("\n\n".join([res.__str__() for res in results]))
    @filter.command("register")
    async def register(self, event: AstrMessageEvent, stu_id: str = "", user_name: str = ""):
        """注册新用户，参数：学号，姓名"""
        if stu_id == "" or user_name == "":
            yield event.plain_result("请提供学号和姓名，例如 /register 12345678 张三")
            return
        if user_name.__len__() > 9:
            yield event.plain_result("姓名长度不能超过9个字符")
            return
        user_id = event.get_sender_id()
        try:
            int(stu_id)
        except ValueError:
            yield event.plain_result("学号应为整数")
            return
        user = sign.db.get_user_by_stu_id(int(stu_id))
        if user:
            yield event.plain_result(f"学号 {stu_id} 已被注册，用户ID为 {user.id}，姓名为 {user.user_name}。如需修改姓名，请联系管理员。")
            return
        success = sign.db.create_user(int(user_id), int(stu_id), user_name, initial_balance=10)
        if success:
            yield event.plain_result(f"注册成功！用户ID为 {event.get_sender_id()}，学号为 {stu_id}，姓名为 {user_name}。初始E币余额为10。")
        else:
            yield event.plain_result(f"注册失败，用户ID {event.get_sender_id()} 已存在。如需修改信息，请联系管理员。")
    @filter.command("update")
    async def update(self, event: AstrMessageEvent, stu_id: str = "", user_name: str = ""):
        """更新用户信息，参数：学号，姓名"""
        if stu_id == "" or user_name == "":
            yield event.plain_result("请提供学号和姓名，例如 /update 12345678 张三")
            return
        if user_name.__len__() > 9:
            yield event.plain_result("姓名长度不能超过9个字符")
            return
        user_id = event.get_sender_id()
        try:
            int(stu_id)
        except ValueError:
            yield event.plain_result("学号应为整数")
            return
        user = sign.db.get_user(int(user_id))
        if not user:
            yield event.plain_result(f"用户ID {user_id} 不存在，请先使用 /register 指令注册用户")
            return
        if user.stu_id == int(stu_id) and user.user_name == user_name:
            yield event.plain_result(f"学号和姓名均未更改，无需更新")
            return
        success = sign.db.update(int(stu_id), user_name)
        if success:
            yield event.plain_result(f"更新成功！用户ID为 {user_id}，学号更新为 {stu_id}，姓名更新为 {user_name}。")
        else:
            yield event.plain_result(f"数据库更新失败，请联系管理员。")
    @filter.command("get_info")
    async def get_info(self, event: AstrMessageEvent, user_id: str = ""):
        """获取用户信息，参数：用户ID（可选，默认自己）"""
        if user_id == "":
            user_id = event.get_sender_id()
        try:
            int(user_id)
        except ValueError:
            yield event.plain_result("用户ID应为整数")
            return
        user = sign.db.get_user(int(user_id))
        if not user:
            yield event.plain_result(f"用户ID {user_id} 不存在")
            return
        yield event.plain_result(str(user))
    @filter.command("get_all_info")
    async def get_all_info(self, event: AstrMessageEvent):
        """获取所有用户信息（仅管理员可用）"""
        user_id = event.get_sender_id()
        if user_id != self.config.get('admin'):
            yield event.plain_result("只有管理员才能使用此指令")
            return
        users = sign.db.get_user_list()
        yield event.plain_result("\n\n".join([str(user) for user in users]))
    @filter.command("update_e_coin")
    async def update_e_coin(self, event: AstrMessageEvent, user_id: str = "", amount: str = ""):
        """更新用户E币余额，参数：用户ID，金额（正数增加，负数减少，仅管理员可用）"""
        admin_id = event.get_sender_id()
        if admin_id != self.config.get('admin'):
            yield event.plain_result("只有管理员才能使用此指令")
            return
        if user_id == "" or amount == "":
            yield event.plain_result("请提供用户ID和金额，例如 /update_e_coin 12345678 10")
            return
        try:
            int(user_id)
            amt = int(amount)
        except ValueError:
            yield event.plain_result("用户ID和金额应为整数")
            return
        user = sign.db.get_user(int(user_id))
        if not user:
            yield event.plain_result(f"用户ID {user_id} 不存在")
            return        
        total_amount = user.e_coin + amt
        res = sign.db.update_balance(int(user_id), amt)
        if res == -1:
            yield event.plain_result(f"用户ID {user_id} 不存在")
        elif res == 0:
            yield event.plain_result(f"用户ID {user_id} 余额不足，无法减少 {amount} E币")
        else:
            yield event.plain_result(f"用户ID {user_id} E币余额已更新，总金额：{total_amount} E币")
    @filter.command("每日签到")
    async def daily_sign(self, event: AstrMessageEvent, user_id: str = ""):
        """进行每日签到，参数：用户ID（管理员可加参数，默认自己）"""
        if user_id != "":
            if event.get_sender_id() != self.config.get('admin'):
                yield event.plain_result("只有管理员才能为他人签到")
                return
            try:
                int(user_id)
            except ValueError:
                yield event.plain_result("用户ID应为整数")
                return
        else:
            user_id = event.get_sender_id()
        result = daily_sign.daily_sign(int(user_id))
        yield event.plain_result(result.__str__())
        
    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""
        logger.info("插件正在终止...")
        self.stop_event.set()


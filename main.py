from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
import astrbot.api.message_components as Comp
from astrbot.api import logger
from astrbot.api import AstrBotConfig
from datetime import time
from astrbot.api.event import MessageChain

from astrbot.api.event import filter
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.core.config.astrbot_config import AstrBotConfig
from astrbot.core.message.message_event_result import MessageEventResult
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import (
    AiocqhttpMessageEvent,
)
from astrbot.core.star.star_tools import StarTools

import re
from . import sign
import asyncio
from .result import Result
from . import daily_sign
from datetime import datetime, timedelta
import random
_TIME_RE = re.compile(r"^\s*(\d{1,2})[:：](\d{1,2})(?:[:：](\d{1,2}))?\s*$")
@register("astrbot_plugin_sign", "Nowhatwhy", "一个简单签到", "1.1.0")
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
    def next_run_time(self ) -> datetime:
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
            await sign.refresh_token_all()
            await self.send_sign_message(await sign.sign_all())

    # 注册指令的装饰器。指令名为 helloworld。注册成功后，发送 `/helloworld` 就会触发这个指令，并回复 `你好, {user_name}!`
    @filter.command("helloworld")
    async def helloworld(self, event: AiocqhttpMessageEvent):
        """这是一个 hello world 指令""" # 这是 handler 的描述，将会被解析方便用户了解插件内容。建议填写。
        messages = event.get_messages()
        if not isinstance(messages[1], Comp.At):
            yield event.plain_result("请使用 @提及 方式调用此指令")
            return
        yield event.plain_result(f"你好，{messages[1].qq}")
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
    @filter.command("抢劫")
    async def rob(self, event: AiocqhttpMessageEvent, user_id: str = "", rob_amount: int = 10):
        """抢劫其他用户，参数：用户ID，抢劫金额（默认10E币）抢劫成功获得对方金额，失败则赔偿对方金额"""
        if user_id == "":
            yield event.plain_result("请输入要抢劫的对象。参数：用户ID，抢劫金额（默认10E币）抢劫成功获得对方金额，失败则赔偿对方金额")
            return
        try:
            int(user_id)
        except ValueError:
            yield event.plain_result("用户ID应为整数")
            return
        if user_id == event.get_sender_id():
            yield event.plain_result("不能抢劫自己")
            return
        if rob_amount <= 0 or rob_amount >= 100:
            yield event.plain_result("抢劫金额应在1到99之间")
            return
        user1 = sign.db.get_user(int(event.get_sender_id()))
        user2 = sign.db.get_user(int(user_id))
        if not user1 or not user2:
            yield event.plain_result("用户不存在，请检查用户ID是否正确")
            return
        if user1.e_coin < rob_amount or user2.e_coin < rob_amount:
            yield event.plain_result("双方E币余额均需大于抢劫金额")
            return
        success = random.choice([True, False])
        client = event.bot
        if success:
            sign.db.update_balance(user1.id, rob_amount)
            sign.db.update_balance(user2.id, -rob_amount)
            yield event.plain_result(f"抢劫成功！你从用户 {user2.user_name}（ID: {user2.id}）处抢得 {rob_amount} E币。")
        else:
            sign.db.update_balance(user1.id, -rob_amount)
            sign.db.update_balance(user2.id, rob_amount)
            await client.set_group_ban(
                group_id= int(event.get_group_id()), user_id=user1.id, duration=60
            )
            yield event.plain_result(f"抢劫失败！你赔偿用户 {user2.user_name}（ID: {user2.id}） {rob_amount} E币，并关进监狱60秒。")
    @filter.command("e菜单")
    async def e_menu(self, event: AstrMessageEvent):
        """显示E币菜单"""
        menu = (
            "E币菜单：\n"
            "/sign - 执行签到，扣除5E币\n"
            "/每日签到 - 每日签到，获得10E币（仅限未签到用户）\n"
            "/register 学号 姓名 - 注册新用户，初始10E币\n"
            "/update 学号 姓名 - 更新用户信息\n"
            "/get_info [用户ID] - 获取用户信息，默认自己\n"
            "/rob 用户ID [金额] - 抢劫其他用户，成功获得对方金额，失败赔偿对方金额（金额默认10E币）\n"
            "管理员指令：\n"
            "/sign_all - 为所有用户执行签到\n"
            "/get_all_info - 获取所有用户信息\n"
            "/update_e_coin 用户ID 金额 - 更新用户E币余额，正数增加，负数减少\n"
        )
        yield event.plain_result(menu)
    @filter.command("get_token")
    async def get_token(self, event: AiocqhttpMessageEvent):
        res = await sign.refresh_token(int(event.get_sender_id()))
        if res == -1:
            yield event.plain_result("用户不存在，请创建账号")
            return
        if res == 0:
            yield event.plain_result("5次请求token都失败了，请重试或者联系管理员")
        yield event.plain_result("刷新token成功，现在你可以签到了")
        return
    @filter.command("转账")
    async def transfer(self, event: AiocqhttpMessageEvent, to_user_id: str = "", amount: str = ""):
        """转账E币给其他用户，参数：用户ID，金额"""
        if to_user_id == "" or amount == "":
            yield event.plain_result("请提供目标用户ID和转账金额，例如 /转账 12345678 10")
            return
        try:
            int(to_user_id)
            amt = int(amount)
        except ValueError:
            yield event.plain_result("用户ID和金额应为整数")
            return
        if amt <= 0:
            yield event.plain_result("你小子想干嘛？转账金额必须为正数")
            return
        from_user_id = event.get_sender_id()
        if str(from_user_id) == to_user_id:
            yield event.plain_result("不能给自己转账")
            return
        from_user = sign.db.get_user(int(from_user_id))
        to_user = sign.db.get_user(int(to_user_id))
        if not from_user or not to_user:
            yield event.plain_result("用户不存在，请检查用户ID是否正确")
            return
        if from_user.e_coin < amt:
            yield event.plain_result("余额不足，无法完成转账")
            return
        from_user_balance = from_user.e_coin - amt
        to_user_balance = to_user.e_coin + amt
        sign.db.update_balance(from_user.id, -amt)
        sign.db.update_balance(to_user.id, amt)
        yield event.plain_result(f"转账成功！你向用户 {to_user.user_name}（ID: {to_user.id}）转账了 {amt} E币。\n你的新余额为 {from_user_balance} E币。\n对方的新余额为 {to_user_balance} E币。")
    @filter.command("查询电费")
    async def query_electricity_fee(self, event: AiocqhttpMessageEvent, type: str = '电费'):
        """查询电费余额"""
        headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) EdgiOS/121.0.2277.107 Version/17.0 Mobile/15E148 Safari/604.1",
            "Cookie": "ASP.NET_SessionId=mcwdx3evuy4f5d0ry1m0fqtk; EF.TerminalId=b230fd753c6947708f39d71e155dffe8; .ASPXAUTH=3CBC84A53432CA9AE7E4C14DB04C900890F15472841CADC6F8B9482731F56E872C63644A1B531EF12CD183F69D6CB813EC7DA228325861D5CBBD7911A26CACECDFFE5D7A79EFF14CDBC256CA7670BDCF6F218310B94B583E9BEF27BC05AB4ECF22EB5E2E8E80E8B42FD34379A42162BD77499CAA9DC33EC2417F3241484CA25021F68026D6BB4768B607544A8F308D46"
        }
        data = {
            "xiaoqu": "NewS",
            "ld_Name": "东校区E号学生宿舍楼",
            "ld_Id": "15",
            "Room_No": "219",
            "etype": "" if type == "电费" else ""
        }
        url = "https://pay.ahut.edu.cn/Charge/GetIMS_AHUTService"
        async with sign.aiohttp.ClientSession() as session:
            async with session.post(url, data=data, headers=headers) as resp:
                js = await resp.json()
                if js.get('Code') != 0:
                    yield event.plain_result(f"查询失败，错误信息：{js.get('Message')}")
                    return
                yield event.plain_result(str(js))
    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""
        logger.info("插件正在终止...")
        self.stop_event.set()


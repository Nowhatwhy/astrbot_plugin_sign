from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class User:
    id: int
    stu_id: int = 0
    user_name: str = ""
    e_coin: int = 0
    is_admin: bool = False
    sign_date: Optional[str] = None   # 也可以用 date
    token: str = ""

    def to_dict(self):
        return {
            "用户ID": self.id,
            "E币余额": self.e_coin,
            "学号": self.stu_id,
            "是否管理员": self.is_admin,
            "最后签到日期": self.sign_date,
            "姓名": self.user_name
        }
    def __str__(self):
        return f"用户ID: {self.id}\n姓名: {self.user_name}\nE币余额: {self.e_coin}\n学号: {self.stu_id}\n是否管理员: {self.is_admin}\n最后签到日期: {self.sign_date}"
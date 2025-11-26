from . import db
from .result import Result
from .user import User
import datetime
def daily_sign(user_id: int) -> Result:
    """为指定用户执行每日签到"""
    user = db.get_user(user_id)
    result = Result(False, -1, "", "")
    if not user:
        result.mes = "用户不存在，请先创建用户"
        return result
    result.user_id = user.id
    result.user_name = user.user_name   
    if user.sign_date is not None and str(user.sign_date) == datetime.date.today().isoformat():
        result.mes = "今日已签到，无需重复签到"
        return result
    db.update_sign_date(user.id, datetime.date.today().isoformat())
    total = user.e_coin + 10
    db.update_balance(user.id, 10)
    result.mes = f"签到成功，获得10E币，当前余额为{total}E币"
    result.success = True
    return result
    
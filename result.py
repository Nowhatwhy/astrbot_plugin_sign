class Result:
    def __init__(self, success: bool, user_id: int, user_name: str, mes: str):
        self.success = success
        self.user_id = user_id
        self.mes = mes
        self.user_name = user_name
    def to_dict(self):
        return {
            "success": self.success,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "mes": self.mes
        }
    def __repr__(self):
        return f"用户ID: {self.user_id}\n姓名: {self.user_name}\n签到结果: "+("成功" if self.success else "失败")+f"\n消息: {self.mes}"
    def __str__(self):
        return f"用户ID: {self.user_id}\n姓名: {self.user_name}\n签到结果: "+("成功" if self.success else "失败")+f"\n消息: {self.mes}"

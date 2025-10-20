class Result:
    def __init__(self, success: bool, user_id: int, mes: str):
        self.success = success
        self.user_id = user_id
        self.mes = mes
    def to_dict(self):
        return {
            "success": self.success,
            "user_id": self.user_id,
            "mes": self.mes
        }
    def __repr__(self):
        return f"用户ID: {self.user_id}\n签到结果: "+("成功" if self.success else "失败")+f"\n消息: {self.mes}"
    def __str__(self):
        return f"用户ID: {self.user_id}\n签到结果: "+("成功" if self.success else "失败")+f"\n消息: {self.mes}"


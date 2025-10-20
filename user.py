class User:
    def __init__(self, id, e_coin=0, stu_id=None, is_admin=False, sign_date=None, user_name=None):
        self.id = id
        self.e_coin = e_coin
        self.stu_id = stu_id
        self.is_admin = is_admin
        self.sign_date = sign_date
        self.user_name = user_name
    def to_dict(self):
        return {
            "用户ID": self.id,
            "E币余额": self.e_coin,
            "学号": self.stu_id,
            "是否管理员": self.is_admin,
            "最后签到日期": self.sign_date,
            "姓名": self.user_name
        }
    def __repr__(self):
        return f"User(id={self.id}, user_name={self.user_name}, e_coin={self.e_coin}, stu_id={self.stu_id}, is_admin={self.is_admin}, sign_date={self.sign_date})"
    def __str__(self):
        return f"用户ID: {self.id}, 姓名: {self.user_name}, E币余额: {self.e_coin}, 学号: {self.stu_id}, 是否管理员: {self.is_admin}, 最后签到日期: {self.sign_date}"
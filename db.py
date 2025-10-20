from sqlalchemy import create_engine, text
from user import User
# ---------------- 数据库连接 ----------------
engine = create_engine(
    "mysql+pymysql://root:qq736644851@localhost:3306/ECoin?charset=utf8mb4",
    echo=False,
    future=True
)

# ---------------- 基础函数 ----------------
def get_user(user_id: int) -> User | None:
    """根据用户ID获取完整用户对象"""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT id, e_coin, stu_id, is_admin ,sign_date FROM users WHERE id = :id"), {"id": user_id}).fetchone()
        if not result:
            return None
        return User(*result)


def update_balance(user_id: int, amount: int) -> int:
    """增加或减少用户E币，返回是否成功"""
    with engine.begin() as conn:
        user = conn.execute(text("SELECT e_coin FROM users WHERE id = :id"), {"id": user_id}).fetchone()
        if not user:
            return -1  # 用户不存在
        new_balance = user[0] + amount
        if new_balance < 0:
            return 0  # 余额不足
        conn.execute(text("UPDATE users SET e_coin = :b WHERE id = :id"), {"b": new_balance, "id": user_id})
        return 1  # 成功


def create_user(user_id: int, stu_id: int | None = None, initial_balance: int = 0, is_admin: bool = False) -> bool:
    """创建新用户"""
    with engine.begin() as conn:
        exists = conn.execute(text("SELECT 1 FROM users WHERE id = :id"), {"id": user_id}).fetchone()
        if exists:
            return False
        conn.execute(
            text("INSERT INTO users (id, e_coin, stu_id, is_admin) VALUES (:id, :coin, :stu, :adm)"),
            {"id": user_id, "coin": initial_balance, "stu": stu_id, "adm": int(is_admin)}
        )
        return True

def get_user_list() -> list[User]:
    """获取所有用户列表"""
    with engine.connect() as conn:
        results = conn.execute(text("SELECT id, e_coin, stu_id, is_admin, sign_date FROM users")).fetchall()
        return [User(*row) for row in results]
def get_user_by_stu_id(stu_id: int) -> User | None:
    """根据学号获取用户对象"""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT id, e_coin, stu_id, is_admin, sign_date FROM users WHERE stu_id = :s"), {"s": stu_id}).fetchone()
        return User(*result) if result else None
def get_sign_date(id: int) -> str | None:
    """获取用户最后签到日期"""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT sign_date FROM users WHERE id = :id"), {"id": id}).fetchone()
        return result[0] if result else None
def update_sign_date(id: int, sign_date: str) -> None:
    """更新用户最后签到日期"""
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE users SET sign_date = :date WHERE id = :id"),
            {"date": sign_date, "id": id}
        )
if __name__ == "__main__":
    # 测试代码
    print(get_sign_date(736644851))
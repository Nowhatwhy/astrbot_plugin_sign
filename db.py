from sqlalchemy import create_engine, text
from dataclasses import asdict
from user import User
engine = create_engine(
    "mysql+pymysql://root:qq736644851@127.0.0.1:3306/ECoin?charset=utf8mb4",
    echo=False,
    pool_pre_ping=True,      # 断线自动探活
    pool_recycle=3600,       # 防止空闲被踢
    connect_args={"connect_timeout": 5},  # ✅ 建连超时，避免长时间卡住
)

def get_user(user_id: int) -> User | None:
    """根据用户ID获取完整用户对象"""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT id, stu_id, user_name, e_coin, is_admin, sign_date, token FROM users WHERE id = :id"), {"id": user_id}).fetchone()
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


def create_user(user_id: int, stu_id: int, user_name: str, initial_balance: int = 0, is_admin: bool = False, sign_date: str = "2025-01-01") -> bool:
    """创建新用户"""
    with engine.begin() as conn:
        exists = conn.execute(text("SELECT 1 FROM users WHERE id = :id"), {"id": user_id}).fetchone()
        if exists:
            return False
        conn.execute(
            text("INSERT INTO users (id, e_coin, stu_id, is_admin, sign_date, user_name) VALUES (:id, :coin, :stu, :adm, :sign_date, :uname)"),
            {"id": user_id, "coin": initial_balance, "stu": stu_id, "adm": int(is_admin), "sign_date": sign_date, "uname": user_name}
        )
        return True

def get_user_list() -> list[User]:
    """获取所有用户列表"""
    with engine.connect() as conn:
        results = conn.execute(text("SELECT id, stu_id, user_name, e_coin, is_admin, sign_date, token FROM users")).fetchall()
        return [User(*row) for row in results]
def get_user_by_stu_id(stu_id: int) -> User | None:
    """根据学号获取用户对象"""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT id, stu_id, user_name, e_coin, is_admin, sign_date, token FROM users WHERE stu_id = :s"), {"s": stu_id}).fetchone()
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
def update(stu_id: int, user_name: str)-> bool:
    """更新用户学号和姓名"""
    with engine.begin() as conn:
        result = conn.execute(
            text("UPDATE users SET stu_id = :stu, user_name = :uname WHERE stu_id = :s"),
            {"stu": stu_id, "uname": user_name, "s": stu_id}
        )
        return result.rowcount > 0  # 返回是否有行被更新
from sqlalchemy import text

def update_user(user: User) -> int:
    d = asdict(user)
    uid = d.pop("id")
    d = {k: v for k, v in d.items() if v is not None}  # 忽略为 None 的字段
    if not d:
        return 0
    sql = f"UPDATE users SET {', '.join(f'{k}=:{k}' for k in d)} WHERE id=:id"
    d["id"] = uid
    with engine.begin() as conn:
        return conn.execute(text(sql), d).rowcount
if __name__ == "__main__":
    # 测试代码
    update_user(User(id=736644851,user_name="方法",stu_id=239074022,e_coin=100))
    print(get_user(736644851))
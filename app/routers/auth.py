"""认证路由：注册 / 登录"""
from fastapi import APIRouter, HTTPException

from .. import db, security
from ..schemas import LoginRequest, RegisterRequest

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/register", summary="用户注册")
def register(body: RegisterRequest):
    username = body.username.strip()
    with db.get_conn() as conn:
        exists = conn.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone()
        if exists:
            raise HTTPException(400, "用户名已存在")
        cur = conn.execute(
            "INSERT INTO users(username, password_hash) VALUES(?,?)",
            (username, security.hash_password(body.password)),
        )
        user_id = cur.lastrowid
    token = security.create_token({"uid": user_id, "username": username, "role": "user"})
    return {"token": token, "user": {"id": user_id, "username": username, "role": "user"}}


@router.post("/login", summary="登录")
def login(body: LoginRequest):
    with db.get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE username=?", (body.username.strip(),)).fetchone()
        if row is None or not security.verify_password(body.password, row["password_hash"]):
            raise HTTPException(401, "用户名或密码错误")
        user = db.row_to_dict(row)
    token = security.create_token({"uid": user["id"], "username": user["username"], "role": user["role"]})
    user.pop("password_hash", None)
    return {"token": token, "user": user}

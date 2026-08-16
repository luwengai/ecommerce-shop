"""通用依赖：当前用户 / 当前管理员"""
from fastapi import Depends, Header, HTTPException

from .. import db, security


def get_current_user(authorization: str = Header(None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "未登录")
    payload = security.verify_token(authorization[7:])
    if payload is None:
        raise HTTPException(401, "登录已过期，请重新登录")
    with db.get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE id=?", (payload["uid"],)).fetchone()
    if row is None:
        raise HTTPException(401, "用户不存在")
    user = db.row_to_dict(row)
    user.pop("password_hash", None)
    return user


def get_current_admin(user: dict = Depends(get_current_user)) -> dict:
    if user["role"] != "admin":
        raise HTTPException(403, "需要管理员权限")
    return user

"""订单路由（需登录）：下单 / 我的订单 / 取消"""
import secrets
import time

from fastapi import APIRouter, Depends, HTTPException

from .. import db
from .deps import get_current_user

router = APIRouter(prefix="/api/orders", tags=["订单"])


def _gen_order_no() -> str:
    return time.strftime("%Y%m%d%H%M%S") + secrets.token_hex(2).upper()


def _order_detail(conn, order_id: int, user_id: int | None = None):
    row = conn.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
    if row is None:
        raise HTTPException(404, "订单不存在")
    if user_id is not None and row["user_id"] != user_id:
        raise HTTPException(403, "无权查看该订单")
    items = conn.execute("SELECT * FROM order_items WHERE order_id=?", (order_id,)).fetchall()
    data = db.row_to_dict(row)
    data["items"] = [db.row_to_dict(i) for i in items]
    return data


@router.post("", summary="从购物车下单")
def create_order(user: dict = Depends(get_current_user)):
    with db.get_conn() as conn:
        cart_rows = conn.execute(
            """SELECT c.product_id, c.quantity, p.name, p.price, p.stock, p.status
               FROM cart c JOIN products p ON p.id=c.product_id WHERE c.user_id=?""",
            (user["id"],),
        ).fetchall()
        if not cart_rows:
            raise HTTPException(400, "购物车为空")
        total = 0.0
        for c in cart_rows:
            if c["status"] != "on":
                raise HTTPException(400, f"商品「{c['name']}」已下架，请从购物车移除")
            if c["quantity"] > c["stock"]:
                raise HTTPException(400, f"商品「{c['name']}」库存不足，当前库存 {c['stock']}")
            total += c["price"] * c["quantity"]

        order_no = _gen_order_no()
        cur = conn.execute(
            "INSERT INTO orders(order_no, user_id, total_amount) VALUES(?,?,?)",
            (order_no, user["id"], round(total, 2)),
        )
        order_id = cur.lastrowid
        for c in cart_rows:
            conn.execute(
                "INSERT INTO order_items(order_id, product_id, product_name, price, quantity) VALUES(?,?,?,?,?)",
                (order_id, c["product_id"], c["name"], c["price"], c["quantity"]),
            )
            conn.execute("UPDATE products SET stock=stock-?, sales=sales+? WHERE id=?", (c["quantity"], c["quantity"], c["product_id"]))
        conn.execute("DELETE FROM cart WHERE user_id=?", (user["id"],))
    return _order_detail(conn, order_id)


@router.get("/my", summary="我的订单")
def my_orders(user: dict = Depends(get_current_user)):
    with db.get_conn() as conn:
        rows = conn.execute("SELECT * FROM orders WHERE user_id=? ORDER BY id DESC", (user["id"],)).fetchall()
        data = [db.row_to_dict(r) for r in rows]
        for d in data:
            d["items"] = [db.row_to_dict(i) for i in conn.execute("SELECT * FROM order_items WHERE order_id=?", (d["id"],)).fetchall()]
    return {"items": data}


@router.get("/{order_id}", summary="订单详情")
def get_order(order_id: int, user: dict = Depends(get_current_user)):
    with db.get_conn() as conn:
        return _order_detail(conn, order_id, user["id"])


@router.post("/{order_id}/cancel", summary="取消订单（仅待付款）")
def cancel_order(order_id: int, user: dict = Depends(get_current_user)):
    with db.get_conn() as conn:
        row = conn.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
        if row is None:
            raise HTTPException(404, "订单不存在")
        if row["user_id"] != user["id"]:
            raise HTTPException(403, "无权操作该订单")
        if row["status"] != "pending":
            raise HTTPException(400, "仅待付款订单可取消")
        conn.execute("UPDATE orders SET status='cancelled' WHERE id=?", (order_id,))
        # 回补库存
        for it in conn.execute("SELECT * FROM order_items WHERE order_id=?", (order_id,)).fetchall():
            conn.execute("UPDATE products SET stock=stock+?, sales=MAX(0,sales-?) WHERE id=?", (it["quantity"], it["quantity"], it["product_id"]))
    return {"ok": True, "status": "cancelled"}

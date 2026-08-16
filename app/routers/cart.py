"""购物车路由（需登录）"""
from fastapi import APIRouter, Depends, HTTPException

from .. import db
from ..schemas import CartAddRequest, CartUpdateRequest
from .deps import get_current_user

router = APIRouter(prefix="/api/cart", tags=["购物车"])


def _cart_items(conn, user_id: int):
    return conn.execute(
        """SELECT c.product_id, c.quantity, p.name, p.price, p.stock, p.status, p.image
           FROM cart c JOIN products p ON p.id=c.product_id
           WHERE c.user_id=? ORDER BY c.id DESC""",
        (user_id,),
    ).fetchall()


@router.get("", summary="查看购物车")
def get_cart(user: dict = Depends(get_current_user)):
    with db.get_conn() as conn:
        rows = _cart_items(conn, user["id"])
        items = [db.row_to_dict(r) for r in rows]
        total = sum(i["price"] * i["quantity"] for i in items)
    return {"items": items, "total": round(total, 2)}


@router.post("", summary="加入购物车")
def add_to_cart(body: CartAddRequest, user: dict = Depends(get_current_user)):
    with db.get_conn() as conn:
        prod = conn.execute("SELECT * FROM products WHERE id=?", (body.product_id,)).fetchone()
        if prod is None or prod["status"] != "on":
            raise HTTPException(404, "商品不存在或已下架")
        exists = conn.execute("SELECT id, quantity FROM cart WHERE user_id=? AND product_id=?", (user["id"], body.product_id)).fetchone()
        if exists:
            new_qty = exists["quantity"] + body.quantity
            if new_qty > prod["stock"]:
                raise HTTPException(400, f"库存不足，当前库存 {prod['stock']}")
            conn.execute("UPDATE cart SET quantity=? WHERE id=?", (new_qty, exists["id"]))
        else:
            if body.quantity > prod["stock"]:
                raise HTTPException(400, f"库存不足，当前库存 {prod['stock']}")
            conn.execute("INSERT INTO cart(user_id, product_id, quantity) VALUES(?,?,?)", (user["id"], body.product_id, body.quantity))
    return {"ok": True, "message": "已加入购物车"}


@router.patch("/{product_id}", summary="修改数量")
def update_cart(product_id: int, body: CartUpdateRequest, user: dict = Depends(get_current_user)):
    with db.get_conn() as conn:
        row = conn.execute("SELECT c.id, p.stock FROM cart c JOIN products p ON p.id=c.product_id WHERE c.user_id=? AND c.product_id=?", (user["id"], product_id)).fetchone()
        if row is None:
            raise HTTPException(404, "购物车中没有该商品")
        if body.quantity > row["stock"]:
            raise HTTPException(400, f"库存不足，当前库存 {row['stock']}")
        conn.execute("UPDATE cart SET quantity=? WHERE id=?", (body.quantity, row["id"]))
    return {"ok": True}


@router.delete("/{product_id}", summary="移除商品")
def remove_from_cart(product_id: int, user: dict = Depends(get_current_user)):
    with db.get_conn() as conn:
        conn.execute("DELETE FROM cart WHERE user_id=? AND product_id=?", (user["id"], product_id))
    return {"ok": True}


@router.delete("", summary="清空购物车")
def clear_cart(user: dict = Depends(get_current_user)):
    with db.get_conn() as conn:
        conn.execute("DELETE FROM cart WHERE user_id=?", (user["id"],))
    return {"ok": True}

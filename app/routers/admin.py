"""管理后台路由（需管理员）：商品管理 / 订单处理 / 数据统计"""
from fastapi import APIRouter, Depends, HTTPException, Query

from .. import db
from ..schemas import ProductCreateRequest, ProductUpdateRequest, StatusUpdateRequest, StockUpdateRequest
from .deps import get_current_admin

router = APIRouter(prefix="/api/admin", tags=["管理后台"])


# ---------- 商品管理 ----------
@router.post("/products", summary="新增商品")
def create_product(body: ProductCreateRequest, admin: dict = Depends(get_current_admin)):
    with db.get_conn() as conn:
        cat = conn.execute("SELECT id FROM categories WHERE id=?", (body.category_id,)).fetchone()
        if cat is None:
            raise HTTPException(400, "分类不存在")
        cur = conn.execute(
            "INSERT INTO products(category_id, name, description, price, stock, image) VALUES(?,?,?,?,?,?)",
            (body.category_id, body.name, body.description, body.price, body.stock, body.image),
        )
        return {"ok": True, "id": cur.lastrowid}


@router.put("/products/{product_id}", summary="更新商品")
def update_product(product_id: int, body: ProductUpdateRequest, admin: dict = Depends(get_current_admin)):
    fields, params = [], []
    for key in ("category_id", "name", "description", "price", "image"):
        val = getattr(body, key)
        if val is not None:
            fields.append(f"{key}=?")
            params.append(val)
    if not fields:
        raise HTTPException(400, "没有需要更新的字段")
    params.append(product_id)
    with db.get_conn() as conn:
        row = conn.execute("SELECT id FROM products WHERE id=?", (product_id,)).fetchone()
        if row is None:
            raise HTTPException(404, "商品不存在")
        conn.execute(f"UPDATE products SET {', '.join(fields)} WHERE id=?", params)
    return {"ok": True}


@router.patch("/products/{product_id}/stock", summary="调整库存")
def update_stock(product_id: int, body: StockUpdateRequest, admin: dict = Depends(get_current_admin)):
    with db.get_conn() as conn:
        row = conn.execute("SELECT id FROM products WHERE id=?", (product_id,)).fetchone()
        if row is None:
            raise HTTPException(404, "商品不存在")
        conn.execute("UPDATE products SET stock=? WHERE id=?", (body.stock, product_id))
    return {"ok": True, "stock": body.stock}


@router.patch("/products/{product_id}/status", summary="上架/下架")
def update_status(product_id: int, body: StatusUpdateRequest, admin: dict = Depends(get_current_admin)):
    if body.status not in ("on", "off"):
        raise HTTPException(400, "status 只能是 on/off")
    with db.get_conn() as conn:
        row = conn.execute("SELECT id FROM products WHERE id=?", (product_id,)).fetchone()
        if row is None:
            raise HTTPException(404, "商品不存在")
        conn.execute("UPDATE products SET status=? WHERE id=?", (body.status, product_id))
    return {"ok": True, "status": body.status}


@router.delete("/products/{product_id}", summary="删除商品")
def delete_product(product_id: int, admin: dict = Depends(get_current_admin)):
    with db.get_conn() as conn:
        conn.execute("DELETE FROM products WHERE id=?", (product_id,))
        conn.execute("DELETE FROM cart WHERE product_id=?", (product_id,))
    return {"ok": True}


# ---------- 订单管理 ----------
@router.get("/orders", summary="全部订单")
def admin_orders(
    status: str | None = None,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    admin: dict = Depends(get_current_admin),
):
    where, params = [], []
    if status:
        where.append("status=?")
        params.append(status)
    cond = (" WHERE " + " AND ".join(where)) if where else ""
    with db.get_conn() as conn:
        total = conn.execute(f"SELECT COUNT(*) c FROM orders{cond}", params).fetchone()["c"]
        rows = conn.execute(
            f"""SELECT o.*, u.username FROM orders o JOIN users u ON u.id=o.user_id
                {cond} ORDER BY o.id DESC LIMIT ? OFFSET ?""",
            params + [size, (page - 1) * size],
        ).fetchall()
        data = [db.row_to_dict(r) for r in rows]
        for d in data:
            d["items"] = [db.row_to_dict(i) for i in conn.execute("SELECT * FROM order_items WHERE order_id=?", (d["id"],)).fetchall()]
    return {"items": data, "total": total, "page": page, "size": size}


@router.post("/orders/{order_id}/ship", summary="发货")
def ship_order(order_id: int, admin: dict = Depends(get_current_admin)):
    with db.get_conn() as conn:
        row = conn.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
        if row is None:
            raise HTTPException(404, "订单不存在")
        if row["status"] != "paid":
            raise HTTPException(400, "仅已付款订单可发货")
        conn.execute("UPDATE orders SET status='shipped', shipped_at=datetime('now','localtime') WHERE id=?", (order_id,))
    return {"ok": True, "status": "shipped"}


@router.post("/orders/{order_id}/complete", summary="完成订单")
def complete_order(order_id: int, admin: dict = Depends(get_current_admin)):
    with db.get_conn() as conn:
        row = conn.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
        if row is None:
            raise HTTPException(404, "订单不存在")
        if row["status"] not in ("paid", "shipped"):
            raise HTTPException(400, "仅已付款/已发货订单可完成")
        conn.execute("UPDATE orders SET status='completed' WHERE id=?", (order_id,))
    return {"ok": True, "status": "completed"}


# ---------- 数据统计 ----------
@router.get("/stats", summary="经营统计")
def stats(admin: dict = Depends(get_current_admin)):
    with db.get_conn() as conn:
        revenue = conn.execute("SELECT COALESCE(SUM(total_amount),0) v FROM orders WHERE status IN ('paid','shipped','completed')").fetchone()["v"]
        order_total = conn.execute("SELECT COUNT(*) c FROM orders").fetchone()["c"]
        todo = conn.execute("SELECT COUNT(*) c FROM orders WHERE status IN ('pending','paid')").fetchone()["c"]
        prod_total = conn.execute("SELECT COUNT(*) c FROM products").fetchone()["c"]
        low_stock = conn.execute("SELECT COUNT(*) c FROM products WHERE status='on' AND stock<=10").fetchone()["c"]
        top = [db.row_to_dict(r) for r in conn.execute(
            "SELECT name, sales, price, stock FROM products ORDER BY sales DESC LIMIT 5").fetchall()]
        trend_rows = conn.execute(
            """SELECT date(paid_at) d, SUM(total_amount) v FROM orders
               WHERE paid_at IS NOT NULL AND date(paid_at) >= date('now','-6 days')
               GROUP BY date(paid_at) ORDER BY d""").fetchall()
        trend = [{"date": r["d"], "amount": round(r["v"], 2)} for r in trend_rows]
        status_rows = conn.execute("SELECT status, COUNT(*) c FROM orders GROUP BY status").fetchall()
        by_status = {r["status"]: r["c"] for r in status_rows}
    return {
        "revenue": round(revenue, 2),
        "order_total": order_total,
        "todo_orders": todo,
        "product_total": prod_total,
        "low_stock": low_stock,
        "top_products": top,
        "trend": trend,
        "by_status": by_status,
    }

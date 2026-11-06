import asyncio
from . import db
out_time = 1
scan_interval = 10

def cancel_expired_orders():
    """找出超时待付款订单，取消并回补库存"""
    with db.get_conn() as conn:
        expired = conn.execute(
            """SELECT id FROM orders
               WHERE status='pending'
               AND created_at < datetime('now','localtime',?)
            """,
            (f"-{out_time} minutes",),
        ).fetchall()

        for row in expired:
            oid = row["id"]
            for it in conn.execute("SELECT * FROM order_items WHERE order_id=?",(oid,)).fetchall():
                conn.execute(
                    "UPDATE products SET stock=stock+?,sales=MAX(0,sales-?) WHERE id =?",
                    (it["quantity"],it["quantity"],it["product_id"]),
                )

            conn.execute("UPDATE orders SET status='cancelled' WHERE id=? AND status='pending'",
                         (oid,),
                         )

        if expired:
            print(f"[tasks]  自动取消 {len(expired)}个超时订单")

SHIP_TIMEOUT_DAYS=3
def refund_unshipped_orders():
    with db.get_conn() as conn:
        expired = conn.execute(
            """SELECT id FROM orders
               WHERE status='paid'
               AND paid_at < datetime('now','localtime','-1 minutes')
            """,
            #(f"-{SHIP_TIMEOUT_DAYS} days",),
        ).fetchall()
        for row in expired:
            oid = row["id"]
            for it in conn.execute("SELECT * FROM order_items WHERE order_id=?", (oid,)).fetchall():
                conn.execute("UPDATE products SET stock=stock+?, sales=MAX(0,sales-?) WHERE id=?",
                             (it["quantity"], it["quantity"], it["product_id"]))
            conn.execute("UPDATE orders SET status='refunded' WHERE id=? AND status='paid'", (oid,))
        if expired:
            print(f"[tasks] 自动退款 {len(expired)} 个超时未发货订单")



async def auto_cancel_loop():
    while True:
        await asyncio.sleep(scan_interval)
        cancel_expired_orders()
        refund_unshipped_orders()

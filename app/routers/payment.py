"""支付路由：模拟第三方支付 + 回调（真实环境替换为微信/支付宝回调验签）"""
from fastapi import APIRouter, Depends, HTTPException

from .. import db
from ..schemas import PaymentRequest
from .deps import get_current_user

router = APIRouter(prefix="/api/payment", tags=["支付"])


@router.post("/mock", summary="模拟支付并回调")
def mock_pay(body: PaymentRequest, user: dict = Depends(get_current_user)):
    with db.get_conn() as conn:
        row = conn.execute("SELECT * FROM orders WHERE id=?", (body.order_id,)).fetchone()
        if row is None:
            raise HTTPException(404, "订单不存在")
        if row["user_id"] != user["id"]:
            raise HTTPException(403, "无权操作该订单")
        if row["status"] != "pending":
            raise HTTPException(400, f"当前订单状态为 {row['status']}，不能支付")
        conn.execute("INSERT INTO payments(order_id, amount, pay_type, status) VALUES(?,?,?,?)",
                     (row["id"], row["total_amount"], body.pay_type, "success"))
        conn.execute("UPDATE orders SET status='paid', paid_at=datetime('now','localtime') WHERE id=?", (row["id"],))
        order_no = row["order_no"]
    return {"ok": True, "message": "支付成功", "order_no": order_no, "status": "paid"}

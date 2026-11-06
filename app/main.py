"""电商商城 FastAPI 入口"""
import os
import asyncio
from .tasks import auto_cancel_loop
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from . import db
from .routers import admin, auth, cart, orders, payment, products
from .seed import seed_if_empty

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")

app = FastAPI(
    title="电商商城系统 API",
    description="用 Codex / Claude Code 开发的电商应用（商品/购物车/订单/支付/管理后台）",
    version="1.0.0",
)

@app.on_event("startup")
async def start_background_tasks():
    asyncio.create_task(auto_cancel_loop())


# 初始化数据库 + 演示数据
db.init_db()
seed_if_empty()

app.include_router(auth.router)
app.include_router(products.router)
app.include_router(cart.router)
app.include_router(orders.router)
app.include_router(payment.router)
app.include_router(admin.router)


@app.get("/", include_in_schema=False)
def index():
    return RedirectResponse("/static/index.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/api/health", tags=["系统"])
def health():
    return {"status": "ok", "service": "ecommerce-shop"}

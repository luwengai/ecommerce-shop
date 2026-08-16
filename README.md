# 电商商城系统（后端 API + 管理后台）

用 **Codex / Claude Code** 开发的 B2C 电商应用，覆盖「商品 → 购物车 → 订单 → 支付 → 管理后台」完整链路。
后端 FastAPI + SQLite，零 ORM、JWT 自实现（HMAC-SHA256），支付为模拟沙箱（可替换微信/支付宝回调）。

## 功能

- 🛍️ 商品：分类、搜索、分页、详情、上架/下架
- 🛒 购物车：加购、改数量、删除、清空、库存校验
- 📦 订单：购物车下单、库存扣减、订单状态机（待付款→已付款→已发货→已完成/已取消）、取消回补库存
- 💳 支付：模拟第三方支付 + 回调，订单超时/状态变更可扩展
- 🛠️ 管理后台：商品 CRUD、库存调整、订单发货/完成、经营统计（销售额/趋势/TOP 商品/低库存预警）
- 📚 自动接口文档（Swagger）

## 快速开始

```bash
pip install -r requirements.txt
python run.py            # 默认 127.0.0.1:8000
# python run.py --port 9000
```

| 入口 | 地址 |
|---|---|
| 商城前台 | http://127.0.0.1:8000/static/index.html |
| 管理后台 | http://127.0.0.1:8000/static/admin.html |
| Swagger 接口文档 | http://127.0.0.1:8000/docs |

## 演示账号

| 角色 | 账号 | 密码 |
|---|---|---|
| 管理员 | admin | admin123 |
| 测试用户 | demo | 123456 |

首次启动自动写入演示数据：5 个分类、11 个商品。

## 目录结构

```
ecommerce-shop/
├── app/
│   ├── main.py          # FastAPI 入口
│   ├── db.py            # SQLite 连接与建表
│   ├── security.py      # 自写 HMAC JWT + PBKDF2 密码哈希
│   ├── schemas.py       # 请求/响应模型
│   ├── seed.py          # 演示数据
│   └── routers/         # auth / products / cart / orders / payment / admin
├── static/              # 商城前台 + 管理后台（原生 HTML/JS）
├── data/                # SQLite 数据文件（自动生成）
├── run.py               # 启动入口
└── requirements.txt
```

## 核心 API

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | /api/auth/register | 注册 |
| POST | /api/auth/login | 登录（返回 JWT） |
| GET | /api/products | 商品列表（category_id / q / page / size） |
| POST | /api/cart | 加入购物车（需登录） |
| POST | /api/orders | 从购物车下单（需登录） |
| POST | /api/payment/mock | 模拟支付（需登录） |
| POST | /api/admin/products | 新增商品（需管理员） |
| GET | /api/admin/stats | 经营统计（需管理员） |

## 说明

- 生产环境请替换 `SECRET_KEY`（环境变量 `SHOP_SECRET_KEY`）与支付沙箱为真实微信/支付宝回调验签。
- 数据库为 SQLite，删除 `data/shop.db` 后重启可重置数据。

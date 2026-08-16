"""启动入口：python run.py [--port 8000]"""
import argparse

import uvicorn

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="启动电商商城系统")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    print("=" * 56)
    print("电商商城系统已启动")
    print(f"  商城前台: http://{args.host}:{args.port}/static/index.html")
    print(f"  管理后台: http://{args.host}:{args.port}/static/admin.html")
    print(f"  接口文档: http://{args.host}:{args.port}/docs")
    print(f"  演示账号: 管理员 admin/admin123   用户 demo/123456")
    print("=" * 56)
    uvicorn.run("app.main:app", host=args.host, port=args.port, reload=False)

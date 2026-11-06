"""演示数据：仅在空库时写入（分类 + 商品 + 管理员/测试用户）"""
from . import db, security

CATEGORIES = ["T恤", "卫衣", "外套", "裤子", "配饰","鞋类","羽绒服"]

PRODUCTS = [
    (1, "基础纯棉白T 圆领短袖", "重磅纯棉，不透不皱，百搭基础款，男女同款。", 59.0, 200),
    (1, "潮流印花T恤 宽松oversize", "街头风印花，宽松版型，夏季清凉透气。", 89.0, 150),
    (1, "重磅水洗做旧T恤", "水洗做旧工艺，落肩剪裁，复古质感。", 99.0, 80),
    (2, "加绒连帽卫衣 男女同款", "加绒内里，连帽设计，秋冬保暖必备。", 139.0, 120),
    (2, "美式复古圆领卫衣", "美式复古配色，重磅面料，不易变形。", 129.0, 60),
    (3, "飞行员夹克 防风外套", "防风面料，多口袋设计，通勤户外两相宜。", 219.0, 45),
    (3, "中长款风衣 百搭外套", "垂坠感面料，系带收腰，显高显瘦。", 259.0, 30),
    (4, "宽松直筒休闲裤", "直筒版型，弹力腰头，久坐不勒。", 109.0, 100),
    (4, "束脚运动裤 速干面料", "速干透气，束脚设计，运动日常都能穿。", 119.0, 90),
    (5, "棒球帽 刺绣鸭舌帽", "立体刺绣，可调节大小，男女通用。", 49.0, 300),
    (5, "纯色帆布腰带", "厚实帆布，金属扣头，简约百搭。", 39.0, 200),
    (5,"情侣对戒","优雅大方，百搭耀眼。",99.0,200),
    (6,"轻便透气运动鞋","穿上更舒服，脚不臭。",199.0,100),
    (6,"户外防水登山鞋","符合人类脚的设计",399.0,200),
    (7,"大鹅羽绒服。","大兴安岭原产地，适合零下20°。",1999.0,300),
    (7,"鸭绒羽绒服","柔软，保暖，放心。",499.0,400),
]


def seed_if_empty() -> None:
    with db.get_conn() as conn:
        count = conn.execute("SELECT COUNT(*) c FROM products").fetchone()["c"]
        if count:
            return
        for i, name in enumerate(CATEGORIES):
            conn.execute("INSERT INTO categories(name, sort) VALUES(?,?)", (name, i))
        for cat_id, name, desc, price, stock in PRODUCTS:
            conn.execute(
                "INSERT INTO products(category_id, name, description, price, stock, status) VALUES(?,?,?,?,?,'on')",
                (cat_id, name, desc, price, stock),
            )
        conn.execute(
            "INSERT INTO users(username, password_hash, role) VALUES(?,?,?)",
            ("admin", security.hash_password("admin123"), "admin"),
        )
        conn.execute(
            "INSERT INTO users(username, password_hash, role) VALUES(?,?,?)",
            ("demo", security.hash_password("123456"), "user"),
        )
    print("[seed] 演示数据已写入：11 个商品 / 5 个分类 / 管理员 admin / 测试用户 demo")

// 管理后台逻辑
const API = "";
let token = localStorage.getItem("admin_token") || "";
let tab = "stats";

async function api(path, method = "GET", body = null) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = "Bearer " + token;
  const res = await fetch(API + path, { method, headers, body: body ? JSON.stringify(body) : undefined });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || data.message || "请求失败");
  return data;
}

function toast(msg) {
  const el = document.createElement("div");
  el.className = "toast"; el.textContent = msg;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 2000);
}

function renderAdminBox() {
  const box = document.getElementById("adminUserBox");
  if (token) {
    box.innerHTML = `<span style="font-size:14px">管理员已登录</span>
      <button class="btn ghost" onclick="logout()">退出</button>`;
  } else {
    box.innerHTML = "";
  }
}

function logout() { token = ""; localStorage.removeItem("admin_token"); render(); }

function renderLogin() {
  document.getElementById("adminMain").innerHTML = `
    <div style="max-width:360px;margin:60px auto">
      <div class="panel">
        <h3 style="margin-bottom:14px">管理员登录</h3>
        <div class="field" style="margin-bottom:12px"><label>用户名</label><input id="au" value="admin"></div>
        <div class="field" style="margin-bottom:12px"><label>密码</label><input id="ap" type="password" value="admin123"></div>
        <button class="btn" style="width:100%" onclick="doLogin()">登录</button>
      </div>
    </div>`;
}

async function doLogin() {
  try {
    const data = await api("/api/auth/login", "POST", { username: document.getElementById("au").value.trim(), password: document.getElementById("ap").value });
    if (data.user.role !== "admin") throw new Error("该账号不是管理员");
    token = data.token; localStorage.setItem("admin_token", token);
    toast("登录成功"); render();
  } catch (e) { toast(e.message); }
}

// ---------- 统计 ----------
async function renderStats() {
  const main = document.getElementById("adminMain");
  const s = await api("/api/admin/stats");
  main.innerHTML = `
    <div class="tabs">${tabBtns()}</div>
    <div class="stats">
      <div class="stat"><div class="num">¥${s.revenue.toFixed(2)}</div><div class="label">累计销售额（已付款）</div></div>
      <div class="stat"><div class="num">${s.order_total}</div><div class="label">订单总数</div></div>
      <div class="stat"><div class="num">${s.todo_orders}</div><div class="label">待处理订单</div></div>
      <div class="stat"><div class="num">${s.product_total}</div><div class="label">商品总数</div></div>
      <div class="stat"><div class="num" style="color:${s.low_stock ? "#ef4444" : "#16a34a"}">${s.low_stock}</div><div class="label">低库存商品（≤10）</div></div>
    </div>
    <div class="panel" style="margin-bottom:16px">
      <h4 style="margin-bottom:12px">近 7 日销售趋势</h4>
      ${s.trend.length ? s.trend.map(t => `<div style="display:flex;align-items:center;gap:8px;margin:4px 0;font-size:13px">
        <span style="width:80px;color:#6b7280">${t.date}</span>
        <span class="bar" style="width:${Math.max(2, t.amount / 100)}px"></span>
        <span>¥${t.amount.toFixed(2)}</span></div>`).join("") : '<div style="color:#9ca3af;font-size:13px">暂无销售数据</div>'}
    </div>
    <div class="panel">
      <h4 style="margin-bottom:12px">TOP 5 热销商品</h4>
      <table><tr><th>商品</th><th>销量</th><th>单价</th><th>剩余库存</th></tr>
      ${s.top_products.map(p => `<tr><td>${p.name}</td><td>${p.sales}</td><td>¥${p.price.toFixed(2)}</td><td>${p.stock}</td></tr>`).join("") || '<tr><td colspan="4" style="color:#9ca3af">暂无数据</td></tr>'}
      </table>
    </div>`;
}

// ---------- 商品管理 ----------
async function renderProducts() {
  const main = document.getElementById("adminMain");
  const data = await api("/api/products?size=100");
  const cats = (await api("/api/products/meta/categories")).items;
  main.innerHTML = `
    <div class="tabs">${tabBtns()}</div>
    <div class="toolbar"><button class="btn green" onclick="openProduct()">＋ 新增商品</button></div>
    <table>
      <tr><th>ID</th><th>名称</th><th>分类</th><th>价格</th><th>库存</th><th>销量</th><th>状态</th><th>操作</th></tr>
      ${data.items.map(p => `<tr>
        <td>${p.id}</td><td>${p.name}</td><td>${p.category_name || ""}</td>
        <td>¥${p.price.toFixed(2)}</td>
        <td><b style="color:${p.stock <= 10 ? "#ef4444" : "#222"}">${p.stock}</b></td>
        <td>${p.sales}</td>
        <td><span class="tag ${p.status}">${p.status === "on" ? "在售" : "下架"}</span></td>
        <td style="white-space:nowrap">
          <button class="btn ghost" onclick='openProduct(${JSON.stringify(p).replace(/'/g, "&#39;")})'>编辑</button>
          <button class="btn gray" onclick="setStock(${p.id},${p.stock})">库存</button>
          <button class="btn ${p.status === "on" ? "red" : "green"}" onclick="toggleStatus(${p.id},'${p.status === "on" ? "off" : "on"}')">${p.status === "on" ? "下架" : "上架"}</button>
        </td></tr>`).join("")}
    </table>`;
  window._cats = cats;
}

function openProduct(p) {
  const isEdit = !!p;
  const cats = window._cats || [];
  const catOpts = cats.map(c => `<option value="${c.id}" ${p && p.category_id === c.id ? "selected" : ""}>${c.name}</option>`).join("");
  document.getElementById("adminModal").innerHTML = `
  <div class="modal-mask" onclick="if(event.target===this)closeA()">
    <div class="modal">
      <h3>${isEdit ? "编辑商品" : "新增商品"}</h3>
      <div class="field"><label>名称</label><input id="pName" value="${isEdit ? p.name : ""}"></div>
      <div class="field"><label>分类</label><select id="pCat" style="width:100%;padding:8px;border:1px solid #d1d5db;border-radius:8px">${catOpts}</select></div>
      <div class="field"><label>价格（元）</label><input id="pPrice" type="number" step="0.01" value="${isEdit ? p.price : ""}"></div>
      <div class="field"><label>库存</label><input id="pStock" type="number" value="${isEdit ? p.stock : 0}"></div>
      <div class="field"><label>描述</label><input id="pDesc" value="${isEdit ? (p.description || "") : ""}"></div>
      <div class="actions">
        <button class="btn gray" onclick="closeA()">取消</button>
        <button class="btn" onclick="saveProduct(${isEdit ? p.id : "null"})">保存</button>
      </div>
    </div>
  </div>`;
}

async function saveProduct(id) {
  const body = {
    name: document.getElementById("pName").value.trim(),
    category_id: +document.getElementById("pCat").value,
    price: +document.getElementById("pPrice").value,
    stock: +document.getElementById("pStock").value,
    description: document.getElementById("pDesc").value.trim(),
  };
  if (!body.name || !body.price) { toast("名称和价格必填"); return; }
  try {
    if (id) await api(`/api/admin/products/${id}`, "PUT", body);
    else await api("/api/admin/products", "POST", body);
    closeA(); toast("保存成功"); renderProducts();
  } catch (e) { toast(e.message); }
}

function setStock(id, cur) {
  document.getElementById("adminModal").innerHTML = `
  <div class="modal-mask" onclick="if(event.target===this)closeA()">
    <div class="modal">
      <h3>调整库存</h3>
      <div class="field"><label>库存数量</label><input id="sStock" type="number" value="${cur}"></div>
      <div class="actions"><button class="btn gray" onclick="closeA()">取消</button>
        <button class="btn" onclick="saveStock(${id})">保存</button></div>
    </div>
  </div>`;
}

async function saveStock(id) {
  try {
    await api(`/api/admin/products/${id}/stock`, "PATCH", { stock: +document.getElementById("sStock").value });
    closeA(); toast("库存已更新"); renderProducts();
  } catch (e) { toast(e.message); }
}

async function toggleStatus(id, status) {
  try { await api(`/api/admin/products/${id}/status`, "PATCH", { status }); toast(status === "on" ? "已上架" : "已下架"); renderProducts(); } catch (e) { toast(e.message); }
}

function closeA() { document.getElementById("adminModal").innerHTML = ""; }

// ---------- 订单管理 ----------
const STATUS = { pending: "待付款", paid: "已付款", shipped: "已发货", completed: "已完成", cancelled: "已取消" };

async function renderOrders() {
  const main = document.getElementById("adminMain");
  const data = await api("/api/admin/orders?size=100");
  main.innerHTML = `
    <div class="tabs">${tabBtns()}</div>
    <table>
      <tr><th>订单号</th><th>用户</th><th>商品</th><th>金额</th><th>状态</th><th>下单时间</th><th>操作</th></tr>
      ${data.items.map(o => `<tr>
        <td>${o.order_no}</td><td>${o.username}</td>
        <td>${o.items.map(i => `${i.product_name}×${i.quantity}`).join("<br>")}</td>
        <td>¥${o.total_amount.toFixed(2)}</td>
        <td><span class="tag" style="background:#eef2ff;color:#4338ca">${STATUS[o.status] || o.status}</span></td>
        <td style="font-size:12px">${o.created_at}</td>
        <td style="white-space:nowrap">
          ${o.status === "paid" ? `<button class="btn" onclick="ship(${o.id})">发货</button>` : ""}
          ${o.status === "shipped" ? `<button class="btn green" onclick="complete(${o.id})">完成</button>` : ""}
        </td></tr>`).join("") || '<tr><td colspan="7" style="color:#9ca3af;text-align:center">暂无订单</td></tr>'}
    </table>`;
}

async function ship(id) { try { await api(`/api/admin/orders/${id}/ship`, "POST"); toast("已发货"); renderOrders(); } catch (e) { toast(e.message); } }
async function complete(id) { try { await api(`/api/admin/orders/${id}/complete`, "POST"); toast("订单已完成"); renderOrders(); } catch (e) { toast(e.message); } }

// ---------- 主渲染 ----------
function tabBtns() {
  return [
    ["stats", "经营统计"], ["products", "商品管理"], ["orders", "订单管理"],
  ].map(([k, label]) => `<button class="btn ${tab === k ? "active" : "ghost"}" onclick="tab='${k}';render()">${label}</button>`).join("");
}

async function render() {
  renderAdminBox();
  if (!token) { renderLogin(); return; }
  try {
    if (tab === "stats") await renderStats();
    else if (tab === "products") await renderProducts();
    else await renderOrders();
  } catch (e) {
    if (e.message.includes("登录")) { token = ""; localStorage.removeItem("admin_token"); renderLogin(); }
    else toast(e.message);
  }
}

render();

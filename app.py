"""
MedAxis Retail - Pharmacy Chain Operations Platform
Combined prototype backend (Auth + Inventory + Billing + AI Insights)
"""
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timedelta
import json, random, hashlib, time
from enum import Enum

app = FastAPI(title="MedAxis API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer(auto_error=False)

# ── In-memory DB (prototype) ──────────────────────────────────────────────────

USERS = {
    "admin@medaxis.in":     {"id": "u1", "password": "admin123",    "role": "superadmin",          "name": "Arjun Mehta",     "store_id": None},
    "supervisor@medaxis.in":{"id": "u2", "password": "super123",    "role": "regional_supervisor", "name": "Priya Sharma",    "store_id": None},
    "pharma@medaxis.in":    {"id": "u3", "password": "pharma123",   "role": "pharmacist",          "name": "Dr. Kavita Rao",  "store_id": "S001"},
    "inventory@medaxis.in": {"id": "u4", "password": "inv123",      "role": "inventory_controller","name": "Ravi Nair",       "store_id": "S002"},
}

TOKENS = {}  # token -> user_email

STORES = [
    {"id": "S001", "name": "MedAxis - Banjara Hills",    "city": "Hyderabad", "type": "urban"},
    {"id": "S002", "name": "MedAxis - Kondapur",         "city": "Hyderabad", "type": "urban"},
    {"id": "S003", "name": "MedAxis - Miyapur",          "city": "Hyderabad", "type": "semi-urban"},
    {"id": "S004", "name": "MedAxis - Secunderabad",     "city": "Hyderabad", "type": "urban"},
    {"id": "S005", "name": "MedAxis - LB Nagar",         "city": "Hyderabad", "type": "semi-urban"},
]

PRODUCTS = [
    {"sku_id": "SKU001", "name": "Paracetamol 500mg",      "category": "Analgesic",    "unit": "Strip(10)", "price": 18.50,  "reorder_pt": 50},
    {"sku_id": "SKU002", "name": "Amoxicillin 250mg",      "category": "Antibiotic",   "unit": "Strip(10)", "price": 85.00,  "reorder_pt": 30},
    {"sku_id": "SKU003", "name": "Metformin 500mg",        "category": "Antidiabetic", "unit": "Strip(10)", "price": 42.00,  "reorder_pt": 40},
    {"sku_id": "SKU004", "name": "Atorvastatin 10mg",      "category": "Cardiac",      "unit": "Strip(10)", "price": 120.00, "reorder_pt": 25},
    {"sku_id": "SKU005", "name": "Cetirizine 10mg",        "category": "Antiallergic", "unit": "Strip(10)", "price": 28.00,  "reorder_pt": 60},
    {"sku_id": "SKU006", "name": "Omeprazole 20mg",        "category": "Antacid",      "unit": "Strip(10)", "price": 55.00,  "reorder_pt": 35},
    {"sku_id": "SKU007", "name": "Azithromycin 500mg",     "category": "Antibiotic",   "unit": "Strip(3)",  "price": 95.00,  "reorder_pt": 20},
    {"sku_id": "SKU008", "name": "Vitamin D3 60K",         "category": "Supplement",   "unit": "Capsule",   "price": 32.00,  "reorder_pt": 45},
    {"sku_id": "SKU009", "name": "Insulin Glargine 100U",  "category": "Antidiabetic", "unit": "Vial",      "price": 890.00, "reorder_pt": 10},
    {"sku_id": "SKU010", "name": "Pantoprazole 40mg",      "category": "Antacid",      "unit": "Strip(10)", "price": 68.00,  "reorder_pt": 30},
]

# Stock levels per store per SKU
random.seed(42)
STOCK = {}
for store in STORES:
    for prod in PRODUCTS:
        qty = random.randint(5, 200)
        STOCK[f"{store['id']}_{prod['sku_id']}"] = {
            "store_id": store["id"], "sku_id": prod["sku_id"],
            "qty_on_hand": qty, "reorder_point": prod["reorder_pt"],
            "last_updated": datetime.now().isoformat()
        }

# Force some low-stock situations
STOCK["S001_SKU009"]["qty_on_hand"] = 3
STOCK["S003_SKU002"]["qty_on_hand"] = 8
STOCK["S002_SKU007"]["qty_on_hand"] = 4
STOCK["S001_SKU004"]["qty_on_hand"] = 12

BATCHES = []
batch_id = 1
for store in STORES[:3]:
    for prod in PRODUCTS[:6]:
        for _ in range(2):
            exp_days = random.randint(-10, 180)
            BATCHES.append({
                "batch_id": f"B{batch_id:04d}",
                "sku_id": prod["sku_id"],
                "store_id": store["id"],
                "lot_no": f"LOT{random.randint(1000,9999)}",
                "mfg_date": (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d"),
                "exp_date": (datetime.now() + timedelta(days=exp_days)).strftime("%Y-%m-%d"),
                "qty": random.randint(10, 100),
                "expires_in_days": exp_days
            })
            batch_id += 1

SALES = []
sale_id = 1
for day in range(30):
    for store in STORES:
        num_sales = random.randint(20, 80)
        for _ in range(num_sales):
            items = random.sample(PRODUCTS, random.randint(1, 4))
            total = sum(p["price"] * random.randint(1, 3) for p in items)
            SALES.append({
                "sale_id": f"INV{sale_id:06d}",
                "store_id": store["id"],
                "date": (datetime.now() - timedelta(days=day)).strftime("%Y-%m-%d"),
                "total": round(total, 2),
                "items": len(items),
                "payment_mode": random.choice(["UPI", "Cash", "Card"]),
                "gst": round(total * 0.12, 2)
            })
            sale_id += 1

TRANSFERS = [
    {"transfer_id": "TRF001", "from_store": "S003", "to_store": "S001", "sku_id": "SKU009",
     "sku_name": "Insulin Glargine 100U", "qty": 20, "status": "pending",
     "initiated_by": "Ravi Nair", "created_at": datetime.now().isoformat()},
    {"transfer_id": "TRF002", "from_store": "S004", "to_store": "S002", "sku_id": "SKU007",
     "sku_name": "Azithromycin 500mg", "qty": 30, "status": "approved",
     "initiated_by": "Dr. Kavita Rao", "created_at": (datetime.now()-timedelta(hours=2)).isoformat()},
    {"transfer_id": "TRF003", "from_store": "S002", "to_store": "S003", "sku_id": "SKU002",
     "sku_name": "Amoxicillin 250mg", "qty": 50, "status": "in_transit",
     "initiated_by": "Ravi Nair", "created_at": (datetime.now()-timedelta(days=1)).isoformat()},
]

ANOMALIES = [
    {"id": "AN001", "type": "unusual_stock_movement", "store_id": "S001", "sku_id": "SKU009",
     "description": "Insulin Glargine stock dropped 45 units in 2 hours — 3× daily average",
     "score": 0.91, "severity": "high", "timestamp": datetime.now().isoformat(), "resolved": False},
    {"id": "AN002", "type": "suspicious_transaction", "store_id": "S003", "sku_id": "SKU002",
     "description": "5 transactions for Amoxicillin without valid Rx within 30 min",
     "score": 0.78, "severity": "medium", "timestamp": (datetime.now()-timedelta(hours=1)).isoformat(), "resolved": False},
    {"id": "AN003", "type": "price_anomaly", "store_id": "S004", "sku_id": "SKU004",
     "description": "Atorvastatin sold at ₹45 — 62% below MRP. Possible billing error.",
     "score": 0.85, "severity": "high", "timestamp": (datetime.now()-timedelta(hours=3)).isoformat(), "resolved": True},
]

# ── Auth helpers ──────────────────────────────────────────────────────────────

def make_token(email: str) -> str:
    token = hashlib.sha256(f"{email}{time.time()}".encode()).hexdigest()[:32]
    TOKENS[token] = email
    return token

def get_current_user(creds: HTTPAuthorizationCredentials = Depends(security)):
    if not creds:
        raise HTTPException(status_code=401, detail="Not authenticated")
    email = TOKENS.get(creds.credentials)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return USERS[email]

# ── Models ────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: str
    password: str

class SaleItem(BaseModel):
    sku_id: str
    qty: int

class CreateSaleRequest(BaseModel):
    store_id: str
    items: List[SaleItem]
    payment_mode: str = "UPI"

class TransferRequest(BaseModel):
    from_store: str
    to_store: str
    sku_id: str
    qty: int

class NLQRequest(BaseModel):
    question: str

# ── AUTH ENDPOINTS ────────────────────────────────────────────────────────────

@app.post("/auth/login")
def login(req: LoginRequest):
    user = USERS.get(req.email)
    if not user or user["password"] != req.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = make_token(req.email)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user["id"], "name": user["name"],
                 "email": req.email, "role": user["role"],
                 "store_id": user["store_id"]}
    }

@app.post("/auth/logout")
def logout(creds: HTTPAuthorizationCredentials = Depends(security)):
    if creds and creds.credentials in TOKENS:
        del TOKENS[creds.credentials]
    return {"message": "Logged out"}

@app.get("/auth/me")
def me(user=Depends(get_current_user)):
    return user

# ── STORE ENDPOINTS ───────────────────────────────────────────────────────────

@app.get("/stores")
def get_stores(user=Depends(get_current_user)):
    return STORES

# ── INVENTORY ENDPOINTS ───────────────────────────────────────────────────────

@app.get("/inventory/products")
def get_products(user=Depends(get_current_user)):
    return PRODUCTS

@app.get("/inventory/stock")
def get_stock(store_id: Optional[str] = None, user=Depends(get_current_user)):
    items = list(STOCK.values())
    if store_id:
        items = [i for i in items if i["store_id"] == store_id]
    # Join product info
    prod_map = {p["sku_id"]: p for p in PRODUCTS}
    store_map = {s["id"]: s["name"] for s in STORES}
    result = []
    for item in items:
        p = prod_map.get(item["sku_id"], {})
        result.append({**item, "name": p.get("name",""), "category": p.get("category",""),
                       "price": p.get("price",0), "store_name": store_map.get(item["store_id"],"")})
    return result

@app.get("/inventory/alerts/low-stock")
def low_stock_alerts(user=Depends(get_current_user)):
    alerts = []
    prod_map = {p["sku_id"]: p for p in PRODUCTS}
    store_map = {s["id"]: s["name"] for s in STORES}
    for item in STOCK.values():
        if item["qty_on_hand"] <= item["reorder_point"]:
            p = prod_map.get(item["sku_id"], {})
            alerts.append({
                **item,
                "name": p.get("name",""),
                "category": p.get("category",""),
                "store_name": store_map.get(item["store_id"],""),
                "severity": "critical" if item["qty_on_hand"] <= item["reorder_point"] * 0.3 else "warning"
            })
    return sorted(alerts, key=lambda x: x["qty_on_hand"])

@app.get("/inventory/alerts/expiry")
def expiry_alerts(days: int = 30, user=Depends(get_current_user)):
    prod_map = {p["sku_id"]: p for p in PRODUCTS}
    store_map = {s["id"]: s["name"] for s in STORES}
    alerts = []
    for b in BATCHES:
        if b["expires_in_days"] <= days:
            p = prod_map.get(b["sku_id"], {})
            alerts.append({
                **b,
                "name": p.get("name",""),
                "store_name": store_map.get(b["store_id"],""),
                "status": "expired" if b["expires_in_days"] < 0 else "expiring_soon"
            })
    return sorted(alerts, key=lambda x: x["expires_in_days"])

@app.get("/inventory/transfers")
def get_transfers(user=Depends(get_current_user)):
    store_map = {s["id"]: s["name"] for s in STORES}
    return [{**t,
             "from_store_name": store_map.get(t["from_store"],""),
             "to_store_name": store_map.get(t["to_store"],"")} for t in TRANSFERS]

@app.post("/inventory/transfers")
def create_transfer(req: TransferRequest, user=Depends(get_current_user)):
    prod_map = {p["sku_id"]: p for p in PRODUCTS}
    p = prod_map.get(req.sku_id, {})
    t = {
        "transfer_id": f"TRF{len(TRANSFERS)+1:03d}",
        "from_store": req.from_store, "to_store": req.to_store,
        "sku_id": req.sku_id, "sku_name": p.get("name",""),
        "qty": req.qty, "status": "pending",
        "initiated_by": user["name"], "created_at": datetime.now().isoformat()
    }
    TRANSFERS.append(t)
    return t

@app.patch("/inventory/transfers/{transfer_id}/status")
def update_transfer(transfer_id: str, body: dict, user=Depends(get_current_user)):
    for t in TRANSFERS:
        if t["transfer_id"] == transfer_id:
            t["status"] = body.get("status", t["status"])
            return t
    raise HTTPException(404, "Transfer not found")

# ── BILLING ENDPOINTS ─────────────────────────────────────────────────────────

@app.get("/billing/sales")
def get_sales(store_id: Optional[str] = None, limit: int = 50, user=Depends(get_current_user)):
    sales = SALES
    if store_id:
        sales = [s for s in sales if s["store_id"] == store_id]
    store_map = {s["id"]: s["name"] for s in STORES}
    result = [{**s, "store_name": store_map.get(s["store_id"],"")} for s in sales[:limit]]
    return result

@app.post("/billing/sales")
def create_sale(req: CreateSaleRequest, user=Depends(get_current_user)):
    prod_map = {p["sku_id"]: p for p in PRODUCTS}
    items_detail = []
    total = 0
    for item in req.items:
        p = prod_map.get(item.sku_id)
        if not p:
            raise HTTPException(400, f"SKU {item.sku_id} not found")
        line_total = p["price"] * item.qty
        total += line_total
        items_detail.append({"sku_id": item.sku_id, "name": p["name"],
                              "qty": item.qty, "unit_price": p["price"], "total": line_total})
        # Update stock
        key = f"{req.store_id}_{item.sku_id}"
        if key in STOCK:
            STOCK[key]["qty_on_hand"] = max(0, STOCK[key]["qty_on_hand"] - item.qty)
    gst = round(total * 0.12, 2)
    sale = {
        "sale_id": f"INV{len(SALES)+1:06d}",
        "store_id": req.store_id, "date": datetime.now().strftime("%Y-%m-%d"),
        "total": round(total, 2), "gst": gst, "grand_total": round(total + gst, 2),
        "items": items_detail, "payment_mode": req.payment_mode,
        "cashier": user["name"], "timestamp": datetime.now().isoformat()
    }
    SALES.insert(0, {**sale, "items": len(items_detail)})
    return sale

# ── REPORTING ENDPOINTS ───────────────────────────────────────────────────────

@app.get("/reports/dashboard")
def dashboard(user=Depends(get_current_user)):
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    today_sales = [s for s in SALES if s["date"] == today]
    yesterday_sales = [s for s in SALES if s["date"] == yesterday]
    month_sales = [s for s in SALES if s["date"] >= (datetime.now()-timedelta(days=30)).strftime("%Y-%m-%d")]

    today_rev = sum(s["total"] for s in today_sales)
    yest_rev = sum(s["total"] for s in yesterday_sales)
    month_rev = sum(s["total"] for s in month_sales)

    # Sales by store (last 30 days)
    store_rev = {}
    for s in month_sales:
        store_rev[s["store_id"]] = store_rev.get(s["store_id"], 0) + s["total"]
    store_map = {s["id"]: s["name"] for s in STORES}

    # Daily trend (last 7 days)
    daily = {}
    for s in SALES:
        daily[s["date"]] = daily.get(s["date"], 0) + s["total"]
    trend = [{"date": k, "revenue": round(v,2)} for k,v in sorted(daily.items())[-7:]]

    low_stock_count = sum(1 for i in STOCK.values() if i["qty_on_hand"] <= i["reorder_point"])
    expiry_count = sum(1 for b in BATCHES if 0 <= b["expires_in_days"] <= 30)

    return {
        "kpis": {
            "today_revenue": round(today_rev, 2),
            "today_transactions": len(today_sales),
            "month_revenue": round(month_rev, 2),
            "yoy_growth": 12.4,
            "low_stock_alerts": low_stock_count,
            "expiry_alerts": expiry_count,
            "active_stores": len(STORES),
            "pending_transfers": sum(1 for t in TRANSFERS if t["status"] == "pending")
        },
        "store_revenue": [{"store_id": k, "store_name": store_map.get(k,""), "revenue": round(v,2)}
                          for k,v in sorted(store_rev.items(), key=lambda x: -x[1])],
        "daily_trend": trend,
        "top_products": [
            {"name": "Paracetamol 500mg",   "units_sold": 1240, "revenue": 22940},
            {"name": "Metformin 500mg",      "units_sold": 980,  "revenue": 41160},
            {"name": "Omeprazole 20mg",      "units_sold": 870,  "revenue": 47850},
            {"name": "Cetirizine 10mg",      "units_sold": 760,  "revenue": 21280},
            {"name": "Atorvastatin 10mg",    "units_sold": 650,  "revenue": 78000},
        ]
    }

# ── AI INSIGHTS ENDPOINTS ─────────────────────────────────────────────────────

@app.get("/ai/anomalies")
def get_anomalies(user=Depends(get_current_user)):
    store_map = {s["id"]: s["name"] for s in STORES}
    prod_map = {p["sku_id"]: p for p in PRODUCTS}
    return [{**a,
             "store_name": store_map.get(a["store_id"],""),
             "sku_name": prod_map.get(a["sku_id"],{}).get("name","")} for a in ANOMALIES]

@app.patch("/ai/anomalies/{anomaly_id}/resolve")
def resolve_anomaly(anomaly_id: str, user=Depends(get_current_user)):
    for a in ANOMALIES:
        if a["id"] == anomaly_id:
            a["resolved"] = True
            a["resolved_by"] = user["name"]
            a["resolved_at"] = datetime.now().isoformat()
            return a
    raise HTTPException(404, "Not found")

@app.get("/ai/forecast/{sku_id}")
def forecast(sku_id: str, user=Depends(get_current_user)):
    prod_map = {p["sku_id"]: p for p in PRODUCTS}
    p = prod_map.get(sku_id)
    if not p:
        raise HTTPException(404, "SKU not found")
    # Simulated forecast
    base = random.randint(40, 120)
    predictions = []
    for i in range(14):
        predictions.append({
            "date": (datetime.now() + timedelta(days=i+1)).strftime("%Y-%m-%d"),
            "predicted_units": base + random.randint(-10, 20) + (5 if i % 7 == 5 else 0),
            "lower_bound": base - 15,
            "upper_bound": base + 25
        })
    return {
        "sku_id": sku_id, "sku_name": p["name"],
        "model": "Prophet + ARIMA ensemble",
        "confidence": 0.87,
        "recommendations": [
            f"Reorder {base * 2} units by {(datetime.now()+timedelta(days=3)).strftime('%d %b')}",
            "Demand peaks expected on weekends — pre-stock Friday",
            "Current stock sufficient for 4.2 days at forecast rate"
        ],
        "predictions": predictions
    }

@app.post("/ai/query")
def nlq(req: NLQRequest, user=Depends(get_current_user)):
    q = req.question.lower()
    # Rule-based NLQ prototype (real impl uses LangChain + Claude)
    if any(w in q for w in ["low stock", "running out", "reorder"]):
        alerts = [i for i in STOCK.values() if i["qty_on_hand"] <= i["reorder_point"]]
        prod_map = {p["sku_id"]: p for p in PRODUCTS}
        store_map = {s["id"]: s["name"] for s in STORES}
        items = [f"{prod_map[a['sku_id']]['name']} at {store_map[a['store_id']]} ({a['qty_on_hand']} units)"
                 for a in alerts[:5]]
        return {"answer": f"There are {len(alerts)} low-stock items. Critical ones: {', '.join(items)}.",
                "data_source": "inventory.stock_levels", "confidence": 0.95}
    elif any(w in q for w in ["revenue", "sales", "earn"]):
        today = datetime.now().strftime("%Y-%m-%d")
        today_rev = sum(s["total"] for s in SALES if s["date"] == today)
        month_rev = sum(s["total"] for s in SALES)
        return {"answer": f"Today's revenue is ₹{today_rev:,.0f} across all stores. Month-to-date: ₹{month_rev:,.0f}.",
                "data_source": "billing.sales", "confidence": 0.98}
    elif any(w in q for w in ["expir", "wastage", "expire"]):
        exp = [b for b in BATCHES if b["expires_in_days"] <= 30]
        return {"answer": f"{len(exp)} batches expiring within 30 days. Estimated wastage risk: ₹{len(exp)*1200:,}.",
                "data_source": "inventory.batches", "confidence": 0.92}
    elif any(w in q for w in ["transfer", "inter-store"]):
        pending = [t for t in TRANSFERS if t["status"] == "pending"]
        return {"answer": f"{len(TRANSFERS)} transfers total, {len(pending)} pending approval.",
                "data_source": "inventory.transfers", "confidence": 0.96}
    elif any(w in q for w in ["top", "best", "fast", "moving"]):
        return {"answer": "Top fast-moving product: Paracetamol 500mg (1,240 units/month). Followed by Metformin 500mg (980 units). Category leader: Analgesics at 34% of volume.",
                "data_source": "reporting.product_velocity", "confidence": 0.93}
    else:
        return {"answer": f"Based on current data: All 37 stores are operational. Total active SKUs: {len(PRODUCTS)}. This month's revenue is trending 12.4% above last month. Ask me about sales, stock, transfers, or expiry for specific insights.",
                "data_source": "reporting.summary", "confidence": 0.75}

@app.get("/health")
def health():
    return {"status": "ok", "service": "MedAxis API", "timestamp": datetime.now().isoformat()}

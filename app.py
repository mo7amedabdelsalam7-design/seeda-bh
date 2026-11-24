import html
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Optional
from urllib.parse import parse_qsl, urlencode, urlparse, urlsplit, urlunsplit

from fastapi import FastAPI, Query, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
import requests
import uvicorn

from google_auth import get_current_user, get_db, is_pg, setup_google_auth

BASE_DIR = Path(__file__).resolve().parent
os.chdir(BASE_DIR)
STATIC_DIR = BASE_DIR / "static"
MICROLESS_IMAGES_DIR = STATIC_DIR / "images" / "microless"
MICROLESS_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

AFFILIATE_PARAM = "utm_source"
AFFILIATE_CODE = ""
TELEGRAM_CHANNEL_URL = "https://t.me/+FN5Lg1E3z0MyYWY0"
ALLOWED_PROXY_HOSTS = {
    "cdn.microless.com",
    "bahrain.microless.com",
    "www.bahrain.microless.com",
    "bahrain.alershadonline.com",
    "www.bahrain.alershadonline.com",
    "cdn.shopify.com",
    "advancedpcbahrain.com",
    "www.advancedpcbahrain.com",
    "gcc.luluhypermarket.com",
    "www.gcc.luluhypermarket.com",
    "bf1af2.akinoncloudcdn.com",
    "ramezshopping.com",
    "www.ramezshopping.com",
    "hypermax.com.bh",
    "www.hypermax.com.bh",
    "cdn.mafrservices.com",
    "mafrservices.com",
    "cdnprod.mafretailproxy.com",
    "mafretailproxy.com",
    "deliveryxadok.s3.us-east-2.amazonaws.com",
    "s3.us-east-2.amazonaws.com",
    "ansargallery.bh",
    "www.ansargallery.bh",
    "media.ansargallery.bh",
}

STORE_META = {
    "noon_bh": {"label": "نون البحرين", "badge": "noon", "decimals": 2},
    "extra_bh": {"label": "إكسترا البحرين", "badge": "eXtra", "decimals": 3},
    "microless_bh": {"label": "ميكروليس البحرين", "badge": "Microless", "decimals": 3},
    "alershad_bh": {"label": "الإرشاد البحرين", "badge": "AlErshad", "decimals": 3},
    "ramez_bh": {"label": "رامز البحرين", "badge": "Ramez", "decimals": 3},
    "hypermax_bh": {"label": "هايبرماكس البحرين", "badge": "HyperMax", "decimals": 3},
    "zain_bh": {"label": "زين البحرين", "badge": "zain", "decimals": 3},
    "stc_bh": {"label": "stc البحرين", "badge": "stc", "decimals": 3},
    "batelco_bh": {"label": "باتلكو البحرين", "badge": "Batelco", "decimals": 3},
    "virgin_bh": {"label": "فيرجن ميجاستور البحرين", "badge": "Virgin", "decimals": 2},
    "jarir_bh": {"label": "مكتبة جرير البحرين", "badge": "جرير", "decimals": 2},
    "sharafdg_bh": {"label": "شرف DG البحرين", "badge": "SDG", "decimals": 3},
    "sharaf_bh": {"label": "شرف DG البحرين", "badge": "SDG", "decimals": 3},
    "ourshopee_bh": {"label": "أور شوبي البحرين", "badge": "OurShopee", "decimals": 2},
    "advancedpc_bh": {"label": "أدفانسد بي سي البحرين", "badge": "AdvPC", "decimals": 3},
    "lulu_bh": {"label": "لولو هايبرماركت البحرين", "badge": "LuLu", "decimals": 3},
    "ansar_bh": {"label": "أنصار جاليري البحرين", "badge": "Ansar", "decimals": 3},
}


def _sql(conn: Any, query: str) -> str:
    if getattr(conn, "kind", "") == "pg" or is_pg():
        return query.replace("?", "%s")
    return query


def _row_to_dict(row: Any) -> dict[str, Any]:
    if row is None:
        return {}
    if isinstance(row, dict):
        return dict(row)
    try:
        return dict(row)
    except Exception:
        return {}


def ensure_db_ready():
    conn = get_db()
    cur = conn.cursor()
    if getattr(conn, "kind", "") == "pg" or is_pg():
        cur.execute("""
            CREATE TABLE IF NOT EXISTS products (
                sku TEXT PRIMARY KEY,
                store TEXT DEFAULT 'noon_bh',
                name TEXT NOT NULL,
                category TEXT,
                image_url TEXT,
                product_url TEXT NOT NULL,
                current_price DOUBLE PRECISION NOT NULL,
                old_price DOUBLE PRECISION,
                discount_pct DOUBLE PRECISION DEFAULT 0,
                lowest_price DOUBLE PRECISION NOT NULL,
                highest_price DOUBLE PRECISION NOT NULL,
                avg_price DOUBLE PRECISION NOT NULL,
                is_real_deal INTEGER DEFAULT 0,
                in_stock INTEGER DEFAULT 1,
                last_alert_at DOUBLE PRECISION DEFAULT 0,
                last_alert_price DOUBLE PRECISION,
                last_price_change_at DOUBLE PRECISION NOT NULL,
                updated_at DOUBLE PRECISION NOT NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS price_history (
                id SERIAL PRIMARY KEY,
                sku TEXT NOT NULL REFERENCES products(sku),
                price DOUBLE PRECISION NOT NULL,
                recorded_at DOUBLE PRECISION NOT NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS saved_deals (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                deal_key TEXT NOT NULL,
                title TEXT,
                price TEXT,
                url TEXT,
                created_at DOUBLE PRECISION NOT NULL,
                UNIQUE(user_id, deal_key)
            )
        """)
    else:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS products (
                sku TEXT PRIMARY KEY,
                store TEXT DEFAULT 'noon_bh',
                name TEXT NOT NULL,
                category TEXT,
                image_url TEXT,
                product_url TEXT NOT NULL,
                current_price REAL NOT NULL,
                old_price REAL,
                discount_pct REAL DEFAULT 0,
                lowest_price REAL NOT NULL,
                highest_price REAL NOT NULL,
                avg_price REAL NOT NULL,
                is_real_deal INTEGER DEFAULT 0,
                in_stock INTEGER DEFAULT 1,
                last_alert_at REAL DEFAULT 0,
                last_alert_price REAL,
                last_price_change_at REAL NOT NULL,
                updated_at REAL NOT NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sku TEXT NOT NULL,
                price REAL NOT NULL,
                recorded_at REAL NOT NULL,
                FOREIGN KEY (sku) REFERENCES products(sku)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS saved_deals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                deal_key TEXT NOT NULL,
                title TEXT,
                price TEXT,
                url TEXT,
                created_at REAL NOT NULL,
                UNIQUE(user_id, deal_key)
            )
        """)
    conn.commit()
    conn.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    MICROLESS_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    ensure_db_ready()
    yield


app = FastAPI(title="صيدة — لقطات وخصومات البحرين", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
setup_google_auth(app)


def apply_affiliate(raw_url: str) -> str:
    if not raw_url or not AFFILIATE_CODE.strip():
        return raw_url
    parts = urlsplit(raw_url)
    q = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if k != AFFILIATE_PARAM]
    q.append((AFFILIATE_PARAM, AFFILIATE_CODE.strip()))
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(q), parts.fragment))


def format_time_ago(ts: Optional[float]) -> str:
    if not ts:
        return "الحين"
    diff = max(0, int(time.time() - float(ts)))
    if diff < 60:
        return "من شوي"
    if diff < 3600:
        return f"من {diff // 60} دقايق"
    if diff < 86400:
        return f"من {diff // 3600} ساعات"
    return f"من {diff // 86400} أيام"


def get_user_saved_keys(user_id: Optional[int]) -> list[str]:
    if not user_id:
        return []
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute(_sql(conn, "SELECT deal_key FROM saved_deals WHERE user_id = ?"), (user_id,))
        keys = [_row_to_dict(r).get("deal_key") for r in cur.fetchall()]
        return [str(k) for k in keys if k is not None]
    except Exception:
        return []
    finally:
        conn.close()


def build_header_auth_html(user: Optional[dict]) -> str:
    if not user:
        return """
        <a href="/login/google" class="btn-primary">دخول بقوقل</a>
        <a href="/login" class="btn-outline">دخول</a>
        """
    safe_name = html.escape(user.get("name") or "هلا بيك")
    return f"""
        <a href="/wishlist" class="btn-primary">⭐ المفضلة</a>
        <span style="font-size:0.82rem; font-weight:800; color:var(--text-secondary); white-space:nowrap;">{safe_name}</span>
        <a href="/logout" class="btn-outline">خروج</a>
    """


def resolve_local_product_image(sku: Any, store: Any) -> str:
    sku_str = str(sku or "").strip()
    store_str = str(store or "").strip().lower()
    if not sku_str or store_str != "microless_bh":
        return ""
    safe_sku = "".join(ch for ch in sku_str if ch.isalnum() or ch in {"_", "-"})
    if not safe_sku:
        return ""
    img_file = MICROLESS_IMAGES_DIR / f"{safe_sku}.jpg"
    if img_file.exists() and img_file.stat().st_size > 500:
        return f"/static/images/microless/{safe_sku}.jpg"
    return ""


@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok", "service": "seeda_bh"}


@app.get("/img-proxy", include_in_schema=False)
def img_proxy(url: str = Query(..., min_length=5)):
    target = url.strip()
    if target.startswith("//"):
        target = "https:" + target
    parsed = urlparse(target)
    if parsed.scheme not in {"http", "https"}:
        return Response(status_code=400)
    host = (parsed.netloc or "").lower()
    if (
        host not in ALLOWED_PROXY_HOSTS
        and not host.endswith(".microless.com")
        and not host.endswith(".alershadonline.com")
        and not host.endswith(".shopify.com")
        and not host.endswith(".akinoncloudcdn.com")
        and not host.endswith(".ramezshopping.com")
        and not host.endswith(".hypermax.com.bh")
        and not host.endswith(".mafrservices.com")
        and not host.endswith(".mafretailproxy.com")
        and not host.endswith(".amazonaws.com")
        and not host.endswith(".ansargallery.bh")
    ):
        return Response(status_code=403)

    if "microless.com" in host:
        referer = "https://bahrain.microless.com/"
    elif "alershadonline.com" in host:
        referer = "https://bahrain.alershadonline.com/"
    elif "ansargallery.bh" in host:
        referer = "https://www.ansargallery.bh/"
    elif "hypermax.com.bh" in host or "mafrservices.com" in host or "mafretailproxy.com" in host:
        referer = "https://www.hypermax.com.bh/"
    elif "ramezshopping.com" in host or "amazonaws.com" in host:
        referer = "https://ramezshopping.com/"
    elif "akinoncloudcdn.com" in host or "luluhypermarket.com" in host:
        referer = "https://gcc.luluhypermarket.com/"
    else:
        referer = f"{parsed.scheme}://{host}/"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Referer": referer,
        "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
    }

    content = b""
    content_type = "image/jpeg"
    fetched_ok = False

    try:
        from curl_cffi import requests as c_req
        c_resp = c_req.get(target, headers=headers, impersonate="chrome124", timeout=15)
        ctype = (c_resp.headers.get("Content-Type") or "").lower()
        if c_resp.status_code == 200 and c_resp.content and "text/html" not in ctype:
            content = c_resp.content
            content_type = c_resp.headers.get("Content-Type") or "image/jpeg"
            fetched_ok = True
    except Exception:
        fetched_ok = False

    if not fetched_ok:
        try:
            resp = requests.get(target, headers=headers, timeout=12)
            ctype = (resp.headers.get("Content-Type") or "").lower()
            if resp.ok and resp.content and "text/html" not in ctype:
                content = resp.content
                content_type = resp.headers.get("Content-Type") or "image/jpeg"
                fetched_ok = True
        except Exception:
            fetched_ok = False

    if not fetched_ok or not content:
        return Response(status_code=502)

    return Response(
        content=content,
        media_type=content_type,
        headers={"Cache-Control": "public, max-age=86400"},
    )


@app.get("/favicon.ico", include_in_schema=False)
@app.get("/favicon.svg", include_in_schema=False)
def favicon():
    logo_path = BASE_DIR / "logo.png"
    if logo_path.exists():
        return FileResponse(str(logo_path), media_type="image/png")
    svg = r"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
      <rect width="64" height="64" rx="16" fill="#CE1126"/>
      <path d="M0 0 H22 L34 10.6 L22 21.3 L34 32 L22 42.6 L34 53.3 L22 64 H0 Z" fill="#FFFFFF"/>
      <circle cx="43" cy="32" r="10" fill="#FFD166"/>
      <circle cx="43" cy="32" r="4" fill="#CE1126"/>
    </svg>"""
    return Response(content=svg, media_type="image/svg+xml")


@app.get("/logo.png", include_in_schema=False)
def serve_logo():
    logo_path = BASE_DIR / "logo.png"
    if logo_path.exists():
        return FileResponse(str(logo_path), media_type="image/png")
    return Response(status_code=404)


# ===== API Endpoints =====
@app.get("/api/summary")
def api_summary():
    conn = get_db()
    cur = conn.cursor()

    cur.execute(_sql(conn, "SELECT COUNT(*) AS cnt FROM products WHERE in_stock = 1"))
    total_active = _row_to_dict(cur.fetchone()).get("cnt", 0) or 0

    cur.execute(_sql(conn, "SELECT COUNT(*) AS cnt FROM products WHERE in_stock = 1 AND is_real_deal = 1"))
    real_deals = _row_to_dict(cur.fetchone()).get("cnt", 0) or 0

    cur.execute(_sql(conn, "SELECT COALESCE(MAX(discount_pct), 0) AS max_d, MAX(updated_at) AS last_u FROM products WHERE in_stock = 1"))
    row = _row_to_dict(cur.fetchone())
    max_disc = round(float(row.get("max_d") or 0), 1)
    last_updated = row.get("last_u")

    cur.execute(_sql(conn, """
        SELECT store, COUNT(*) AS cnt, COALESCE(MAX(discount_pct), 0) AS max_disc
        FROM products
        WHERE in_stock = 1
        GROUP BY store
    """))
    stores_stats = {}
    for raw_r in cur.fetchall():
        r = _row_to_dict(raw_r)
        st_key = r.get("store") or "noon_bh"
        stores_stats[st_key] = {
            "count": int(r.get("cnt") or 0),
            "max_discount": round(float(r.get("max_disc") or 0), 1),
        }

    cur.execute(_sql(conn, """
        SELECT category, COUNT(*) AS cnt, COALESCE(MAX(discount_pct), 0) AS max_disc
        FROM products
        WHERE in_stock = 1 AND category IS NOT NULL AND category != ''
        GROUP BY category
        ORDER BY cnt DESC
    """))
    categories = []
    for raw_r in cur.fetchall():
        r = _row_to_dict(raw_r)
        categories.append({
            "name": r.get("category"),
            "count": int(r.get("cnt") or 0),
            "max_discount": round(float(r.get("max_disc") or 0), 0),
        })
    conn.close()
    return {
        "total_active": int(total_active),
        "real_deals": int(real_deals),
        "max_discount": max_disc,
        "last_updated_text": format_time_ago(last_updated),
        "stores": stores_stats,
        "categories": categories,
    }


@app.get("/api/products")
def api_products(
    request: Request,
    q: str = "",
    category: str = "",
    store: str = "",
    real_only: int = 0,
    min_discount: float = 0,
    sort: str = "recent",
    page: int = Query(1, ge=1),
    limit: int = Query(24, ge=1, le=100),
):
    user = get_current_user(request)
    saved_keys = set(get_user_saved_keys(user["id"] if user else None))

    conn = get_db()
    cur = conn.cursor()

    like_op = "ILIKE" if (getattr(conn, "kind", "") == "pg" or is_pg()) else "LIKE"
    where = ["in_stock = 1"]
    params: list[Any] = []

    if q.strip():
        where.append(f"(name {like_op} ? OR sku {like_op} ?)")
        params.extend([f"%{q.strip()}%", f"%{q.strip()}%"])
    if category.strip():
        where.append("category = ?")
        params.append(category.strip())
    if store.strip():
        if store.strip() == "sharafdg_bh":
            where.append("store IN ('sharafdg_bh', 'sharaf_bh')")
        else:
            where.append("store = ?")
            params.append(store.strip())
    if real_only == 1:
        where.append("is_real_deal = 1")
    if min_discount > 0:
        where.append("discount_pct >= ?")
        params.append(min_discount)

    where_sql = " AND ".join(where)

    order_map = {
        "recent": "last_price_change_at DESC, updated_at DESC, sku ASC",
        "discount": "discount_pct DESC, current_price ASC, sku ASC",
        "price_asc": "current_price ASC, sku ASC",
        "price_desc": "current_price DESC, sku ASC",
        "real": "is_real_deal DESC, discount_pct DESC, sku ASC",
    }
    order_sql = order_map.get(sort, order_map["recent"])

    cur.execute(_sql(conn, f"SELECT COUNT(*) AS cnt FROM products WHERE {where_sql}"), params)
    total = int(_row_to_dict(cur.fetchone()).get("cnt", 0) or 0)

    offset = (page - 1) * limit
    cur.execute(
        _sql(conn, f"""
            SELECT sku, store, name, category, image_url, product_url,
                   current_price, old_price, discount_pct,
                   lowest_price, highest_price, avg_price,
                   is_real_deal, last_price_change_at, updated_at
            FROM products
            WHERE {where_sql}
            ORDER BY {order_sql}
            LIMIT ? OFFSET ?
        """),
        params + [limit, offset],
    )
    items = []
    for raw_r in cur.fetchall():
        d = _row_to_dict(raw_r)
        st_key = d.get("store") or ("ansar_bh" if str(d.get("sku") or "").startswith("ANSAR_") else "noon_bh")
        dec = STORE_META.get(st_key, {}).get("decimals", 2)
        d["store"] = st_key
        local_img = resolve_local_product_image(d.get("sku"), st_key)
        if local_img:
            d["image_url"] = local_img
        d["current_price"] = round(float(d.get("current_price") or 0), dec)
        d["old_price"] = round(float(d["old_price"]), dec) if d.get("old_price") is not None else None
        d["discount_pct"] = float(d.get("discount_pct") or 0)
        d["lowest_price"] = round(float(d.get("lowest_price") or d["current_price"]), dec)
        d["highest_price"] = round(float(d.get("highest_price") or d["current_price"]), dec)
        d["avg_price"] = round(float(d.get("avg_price") or d["current_price"]), dec)
        d["affiliate_url"] = apply_affiliate(d.get("product_url") or "")
        d["updated_ago"] = format_time_ago(d.get("last_price_change_at") or d.get("updated_at"))
        d["is_lowest_now"] = 1 if d["current_price"] <= d["lowest_price"] else 0
        d["is_saved"] = 1 if str(d.get("sku")) in saved_keys else 0
        items.append(d)

    conn.close()
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "pages": max(1, (total + limit - 1) // limit),
        "items": items,
    }


@app.get("/api/history/{sku}")
def api_history(sku: str):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(_sql(conn, "SELECT * FROM products WHERE sku = ?"), (sku,))
    prod = cur.fetchone()
    if not prod:
        conn.close()
        return JSONResponse(status_code=404, content={"error": "المنتج مو موجود"})

    prod_dict = _row_to_dict(prod)
    st_key = prod_dict.get("store") or ("ansar_bh" if str(prod_dict.get("sku") or "").startswith("ANSAR_") else "noon_bh")
    dec = STORE_META.get(st_key, {}).get("decimals", 2)

    cur.execute(
        _sql(conn, "SELECT price, recorded_at FROM price_history WHERE sku = ? ORDER BY recorded_at ASC"),
        (sku,),
    )
    hist = []
    for raw_r in cur.fetchall():
        r = _row_to_dict(raw_r)
        hist.append({
            "price": round(float(r.get("price") or 0), dec),
            "date": time.strftime("%Y-%m-%d %H:%M", time.localtime(float(r.get("recorded_at") or 0))),
        })
    conn.close()
    prod_dict["store"] = st_key
    prod_dict["affiliate_url"] = apply_affiliate(prod_dict.get("product_url") or "")
    return {"product": prod_dict, "history": hist}


@app.post("/api/wishlist/toggle")
async def api_wishlist_toggle(request: Request):
    user = get_current_user(request)
    if not user or not user.get("id"):
        return JSONResponse(status_code=401, content={"ok": False, "error": "unauthorized"})

    try:
        payload = await request.json()
    except Exception:
        payload = {}

    deal_key = str(payload.get("deal_key") or "").strip()
    if not deal_key:
        return JSONResponse(status_code=400, content={"ok": False, "error": "missing_deal_key"})

    user_id = int(user["id"])
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute(
            _sql(conn, "SELECT id FROM saved_deals WHERE user_id = ? AND deal_key = ?"),
            (user_id, deal_key),
        )
        existing = cur.fetchone()
        if existing:
            cur.execute(
                _sql(conn, "DELETE FROM saved_deals WHERE user_id = ? AND deal_key = ?"),
                (user_id, deal_key),
            )
            saved = False
        else:
            cur.execute(
                _sql(
                    conn,
                    """
                    INSERT INTO saved_deals (user_id, deal_key, title, price, url, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                ),
                (
                    user_id,
                    deal_key,
                    str(payload.get("title") or ""),
                    str(payload.get("price") or ""),
                    str(payload.get("url") or ""),
                    time.time(),
                ),
            )
            saved = True
        conn.commit()
        return {"ok": True, "saved": saved}
    except Exception as exc:
        return JSONResponse(status_code=500, content={"ok": False, "error": str(exc)})
    finally:
        conn.close()


def render_layout(
    page_title: str,
    active_nav: str,
    body_html: str,
    extra_script: str = "",
    user: Optional[dict] = None,
) -> str:
    has_custom_logo = (BASE_DIR / "logo.png").exists()
    logo_visual = (
        '<img src="/logo.png" alt="صيدة" class="brand-logo-img" />'
        if has_custom_logo
        else r"""
        <div class="bahrain-chili-mark" aria-hidden="true">
            <svg viewBox="0 0 64 64" width="38" height="38">
                <defs>
                    <linearGradient id="bhRed" x1="0" y1="0" x2="1" y2="1">
                        <stop offset="0%" stop-color="#E11D38"/>
                        <stop offset="100%" stop-color="#A80B1E"/>
                    </linearGradient>
                </defs>
                <rect width="64" height="64" rx="16" fill="url(#bhRed)"/>
                <path d="M0 0 H20 L31 10.6 L20 21.3 L31 32 L20 42.6 L31 53.3 L20 64 H0 Z" fill="#FFFFFF"/>
                <circle cx="43" cy="32" r="10" fill="#FFD166"/>
                <circle cx="43" cy="32" r="4" fill="#A80B1E"/>
            </svg>
        </div>
        """
    )

    def nav_cls(key: str) -> str:
        return "nav-link active" if active_nav == key else "nav-link"

    auth_buttons_html = build_header_auth_html(user)

    return f"""<!DOCTYPE html>
<html lang="ar" dir="rtl" data-theme="dark">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{html.escape(page_title)} | صيدة 🎯</title>
    <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800;900&display=swap" rel="stylesheet" />
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {{
            --bh-red: #CE1126;
            --bh-red-bright: #EF233C;
            --bh-red-soft: rgba(206, 17, 38, 0.14);
            --bh-gold: #F59E0B;
            --bh-green: #10B981;
            --radius-xl: 22px;
            --radius-lg: 16px;
            --radius-md: 12px;
            --transition: all 0.22s ease;
        }}

        html[data-theme="dark"] {{
            --bg-main: #0B0D12;
            --bg-surface: #131722;
            --bg-card: #181D2B;
            --bg-card-hover: #1E2536;
            --bg-input: #0F131C;
            --border-color: rgba(255, 255, 255, 0.08);
            --border-strong: rgba(206, 17, 38, 0.38);
            --text-primary: #F8FAFC;
            --text-secondary: #94A3B8;
            --text-muted: #64748B;
            --shadow-card: 0 12px 30px rgba(0, 0, 0, 0.35);
            --header-bg: #11151F;
        }}

        html[data-theme="light"] {{
            --bg-main: #F6F7FB;
            --bg-surface: #FFFFFF;
            --bg-card: #FFFFFF;
            --bg-card-hover: #FFF8F8;
            --bg-input: #F1F3F9;
            --border-color: rgba(15, 23, 42, 0.09);
            --border-strong: rgba(206, 17, 38, 0.35);
            --text-primary: #0F172A;
            --text-secondary: #475569;
            --text-muted: #64748B;
            --shadow-card: 0 10px 26px rgba(15, 23, 42, 0.07);
            --header-bg: #FFFFFF;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Cairo', sans-serif;
        }}

        body {{
            background: var(--bg-main);
            color: var(--text-primary);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            transition: background 0.25s ease, color 0.25s ease;
        }}

        a {{
            color: inherit;
            text-decoration: none;
        }}

        .container {{
            width: 100%;
            max-width: 1340px;
            margin: 0 auto;
            padding: 0 20px;
        }}

        .navbar {{
            position: relative;
            z-index: 50;
            background: var(--header-bg);
            border-bottom: 1px solid var(--border-color);
        }}

        .navbar-inner {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 14px;
            min-height: 68px;
            flex-wrap: wrap;
            padding: 10px 0;
        }}

        .brand-link {{
            display: flex;
            align-items: center;
            gap: 10px;
            flex-shrink: 0;
        }}

        .brand-logo-img {{
            height: 40px;
            width: auto;
            border-radius: 10px;
            object-fit: contain;
        }}

        .bahrain-chili-mark {{
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 6px 18px rgba(206, 17, 38, 0.35);
            border-radius: 14px;
        }}

        .brand-text {{
            display: flex;
            flex-direction: column;
            line-height: 1.15;
        }}

        .brand-title {{
            font-size: 1.2rem;
            font-weight: 900;
            letter-spacing: -0.3px;
            display: flex;
            align-items: center;
            gap: 6px;
        }}

        .brand-title span {{
            color: var(--bh-red-bright);
        }}

        .brand-sub {{
            font-size: 0.72rem;
            color: var(--text-secondary);
            font-weight: 600;
        }}

        .nav-search {{
            flex: 1;
            min-width: 220px;
            max-width: 390px;
            position: relative;
        }}

        .nav-search input {{
            width: 100%;
            background: var(--bg-input);
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            padding: 9px 40px 9px 14px;
            border-radius: 999px;
            font-size: 0.88rem;
            outline: none;
            transition: var(--transition);
        }}

        .nav-search input:focus {{
            border-color: var(--bh-red-bright);
            box-shadow: 0 0 0 3px var(--bh-red-soft);
        }}

        .nav-search button {{
            position: absolute;
            right: 12px;
            top: 50%;
            transform: translateY(-50%);
            background: none;
            border: none;
            color: var(--text-secondary);
            cursor: pointer;
            font-size: 1rem;
        }}

        .nav-links {{
            display: flex;
            align-items: center;
            gap: 6px;
            flex-wrap: wrap;
        }}

        .nav-link {{
            padding: 7px 12px;
            border-radius: 10px;
            font-size: 0.88rem;
            font-weight: 700;
            color: var(--text-secondary);
            transition: var(--transition);
            display: inline-flex;
            align-items: center;
            gap: 6px;
            flex-shrink: 0;
        }}

        .nav-link:hover {{
            color: var(--text-primary);
            background: var(--bg-card);
        }}

        .nav-link.active {{
            color: #FFFFFF;
            background: var(--bh-red);
            box-shadow: 0 6px 16px rgba(206, 17, 38, 0.32);
        }}

        .live-dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #EF4444;
            display: inline-block;
            box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.25);
        }}

        .nav-actions {{
            display: flex;
            align-items: center;
            gap: 8px;
            flex-shrink: 0;
        }}

        .theme-btn {{
            width: 36px;
            height: 36px;
            border-radius: 10px;
            border: 1px solid var(--border-color);
            background: var(--bg-card);
            color: var(--text-primary);
            cursor: pointer;
            font-size: 1rem;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            transition: var(--transition);
        }}

        .theme-btn:hover {{
            border-color: var(--bh-red-bright);
        }}

        .btn-outline {{
            padding: 7px 12px;
            border-radius: 10px;
            border: 1px solid var(--border-color);
            background: var(--bg-card);
            color: var(--text-primary);
            font-weight: 700;
            font-size: 0.84rem;
            transition: var(--transition);
            white-space: nowrap;
        }}

        .btn-outline:hover {{
            border-color: var(--bh-red-bright);
        }}

        .btn-primary {{
            padding: 7px 14px;
            border-radius: 10px;
            border: none;
            background: linear-gradient(135deg, #CE1126, #EF233C);
            color: #FFFFFF;
            font-weight: 800;
            font-size: 0.84rem;
            cursor: pointer;
            box-shadow: 0 6px 18px rgba(206, 17, 38, 0.32);
            transition: var(--transition);
            display: inline-flex;
            align-items: center;
            gap: 6px;
            white-space: nowrap;
        }}

        .btn-primary:hover {{
            transform: translateY(-1px);
            filter: brightness(1.06);
        }}

        main {{
            flex: 1;
            padding: 22px 0 60px;
        }}

        .hero-box {{
            position: relative;
            overflow: hidden;
            border-radius: 26px;
            background: linear-gradient(135deg, rgba(206, 17, 38, 0.16) 0%, var(--bg-surface) 48%, rgba(206, 17, 38, 0.08) 100%);
            border: 1px solid var(--border-strong);
            padding: 34px 32px;
            margin-bottom: 34px;
            box-shadow: var(--shadow-card);
            display: grid;
            grid-template-columns: 1.45fr 1fr;
            gap: 28px;
            align-items: center;
        }}

        .hero-badge {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: var(--bh-red-soft);
            color: var(--bh-red-bright);
            border: 1px solid rgba(239, 35, 60, 0.35);
            padding: 6px 14px;
            border-radius: 999px;
            font-size: 0.82rem;
            font-weight: 800;
            margin-bottom: 14px;
        }}

        .hero-title {{
            font-size: 2.15rem;
            font-weight: 900;
            line-height: 1.25;
            margin-bottom: 12px;
        }}

        .hero-title span {{
            color: var(--bh-red-bright);
        }}

        .hero-desc {{
            color: var(--text-secondary);
            font-size: 0.98rem;
            line-height: 1.7;
            margin-bottom: 22px;
            max-width: 620px;
        }}

        .hero-cta-group {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-bottom: 24px;
        }}

        .hero-stats {{
            display: flex;
            flex-wrap: wrap;
            gap: 24px;
            padding-top: 16px;
            border-top: 1px solid var(--border-color);
        }}

        .stat-item strong {{
            display: block;
            font-size: 1.35rem;
            font-weight: 900;
            color: var(--text-primary);
        }}

        .stat-item span {{
            font-size: 0.8rem;
            color: var(--text-secondary);
        }}

        .hero-showcase {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 20px;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 14px;
        }}

        .showcase-top {{
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .tag-pill {{
            background: rgba(16, 185, 129, 0.14);
            color: var(--bh-green);
            padding: 4px 11px;
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 800;
        }}

        .showcase-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: var(--bg-input);
            padding: 12px 14px;
            border-radius: 14px;
            border: 1px solid var(--border-color);
        }}

        .sec-head {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            margin-bottom: 18px;
            flex-wrap: wrap;
        }}

        .sec-title {{
            font-size: 1.35rem;
            font-weight: 900;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .sec-sub {{
            font-size: 0.86rem;
            color: var(--text-secondary);
        }}

        .stores-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(195px, 1fr));
            gap: 14px;
            margin-bottom: 36px;
        }}

        .store-card {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-lg);
            padding: 18px 14px;
            text-align: center;
            transition: var(--transition);
            position: relative;
        }}

        .store-card:hover {{
            transform: translateY(-3px);
            border-color: var(--bh-red-bright);
            background: var(--bg-card-hover);
        }}

        .store-icon {{
            width: 52px;
            height: 52px;
            border-radius: 15px;
            margin: 0 auto 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 900;
            font-size: 0.78rem;
        }}

        .store-name {{
            font-weight: 800;
            font-size: 1rem;
            margin-bottom: 4px;
        }}

        .store-meta {{
            font-size: 0.8rem;
            color: var(--bh-green);
            font-weight: 700;
        }}

        .cats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
            gap: 14px;
            margin-bottom: 36px;
        }}

        .cat-card {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-lg);
            padding: 16px 18px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            transition: var(--transition);
        }}

        .cat-card:hover {{
            border-color: var(--bh-red-bright);
            transform: translateY(-2px);
        }}

        .cat-badge-icon {{
            width: 44px;
            height: 44px;
            border-radius: 12px;
            background: var(--bh-red-soft);
            color: var(--bh-red-bright);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.25rem;
            flex-shrink: 0;
        }}

        .products-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 18px;
        }}

        .deal-card {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 18px;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            transition: var(--transition);
            box-shadow: var(--shadow-card);
        }}

        .deal-card:hover {{
            transform: translateY(-4px);
            border-color: var(--bh-red-bright);
        }}

        .deal-thumb {{
            position: relative;
            height: 205px;
            background: #FFFFFF;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 14px;
        }}

        .deal-thumb img {{
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
        }}

        .badges-top-right {{
            position: absolute;
            top: 10px;
            right: 10px;
            display: flex;
            flex-direction: column;
            gap: 5px;
        }}

        .badge-disc {{
            background: var(--bh-red);
            color: #FFFFFF;
            font-weight: 900;
            font-size: 0.78rem;
            padding: 3px 9px;
            border-radius: 8px;
        }}

        .badge-real {{
            background: #10B981;
            color: #FFFFFF;
            font-weight: 800;
            font-size: 0.74rem;
            padding: 3px 9px;
            border-radius: 8px;
        }}

        .badge-store {{
            position: absolute;
            bottom: 10px;
            left: 10px;
            background: rgba(15, 23, 42, 0.82);
            color: #FDE047;
            font-size: 0.72rem;
            font-weight: 800;
            padding: 3px 9px;
            border-radius: 8px;
        }}

        .deal-body {{
            padding: 15px;
            display: flex;
            flex-direction: column;
            flex: 1;
            gap: 10px;
        }}

        .deal-cat {{
            font-size: 0.76rem;
            color: var(--text-secondary);
            font-weight: 700;
        }}

        .deal-title {{
            font-size: 0.93rem;
            font-weight: 700;
            line-height: 1.45;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
            min-height: 2.7em;
        }}

        .price-row {{
            display: flex;
            align-items: baseline;
            gap: 8px;
            margin-top: auto;
        }}

        .price-now {{
            font-size: 1.25rem;
            font-weight: 900;
            color: var(--bh-red-bright);
        }}

        .price-old {{
            font-size: 0.85rem;
            color: var(--text-muted);
            text-decoration: line-through;
        }}

        .history-mini {{
            display: flex;
            justify-content: space-between;
            font-size: 0.75rem;
            color: var(--text-secondary);
            background: var(--bg-input);
            padding: 7px 10px;
            border-radius: 10px;
        }}

        .card-actions {{
            display: grid;
            grid-template-columns: 1fr auto auto;
            gap: 6px;
        }}

        .btn-buy {{
            background: var(--bh-red);
            color: #FFFFFF;
            text-align: center;
            padding: 9px 10px;
            border-radius: 10px;
            font-weight: 800;
            font-size: 0.82rem;
            transition: var(--transition);
        }}

        .btn-buy:hover {{
            background: var(--bh-red-bright);
        }}

        .btn-hist {{
            background: var(--bg-input);
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            padding: 9px 10px;
            border-radius: 10px;
            font-weight: 700;
            font-size: 0.8rem;
            cursor: pointer;
            transition: var(--transition);
        }}

        .btn-hist:hover {{
            border-color: var(--bh-red-bright);
        }}

        .btn-save.saved {{
            background: rgba(16, 185, 129, 0.18);
            border-color: #10B981;
            color: #10B981;
        }}

        .filter-bar {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 18px;
            padding: 16px;
            margin-bottom: 22px;
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            align-items: center;
        }}

        .filter-bar select, .filter-bar input {{
            background: var(--bg-input);
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            padding: 9px 14px;
            border-radius: 11px;
            font-size: 0.88rem;
            outline: none;
        }}

        .chip-toggle {{
            padding: 9px 14px;
            border-radius: 11px;
            border: 1px solid var(--border-color);
            background: var(--bg-input);
            color: var(--text-secondary);
            font-weight: 700;
            font-size: 0.86rem;
            cursor: pointer;
        }}

        .chip-toggle.active {{
            background: rgba(16, 185, 129, 0.16);
            border-color: #10B981;
            color: #10B981;
        }}

        .coupon-card {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-top: 4px solid var(--bh-red);
            border-radius: 18px;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 14px;
        }}

        .coupon-code-box {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: var(--bh-red-soft);
            border: 1.5px dashed var(--bh-red-bright);
            padding: 11px 16px;
            border-radius: 12px;
            cursor: pointer;
            font-weight: 900;
            font-size: 1.1rem;
            color: var(--bh-red-bright);
        }}

        .auth-wrap {{
            max-width: 440px;
            margin: 24px auto;
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 22px;
            padding: 30px;
            box-shadow: var(--shadow-card);
        }}

        .form-group {{
            margin-bottom: 14px;
        }}

        .form-group label {{
            display: block;
            font-size: 0.85rem;
            font-weight: 700;
            margin-bottom: 6px;
            color: var(--text-secondary);
        }}

        .form-group input {{
            width: 100%;
            background: var(--bg-input);
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            padding: 11px 14px;
            border-radius: 12px;
            font-size: 0.92rem;
        }}

        .modal-backdrop {{
            position: fixed;
            inset: 0;
            background: rgba(0, 0, 0, 0.72);
            display: none;
            align-items: center;
            justify-content: center;
            z-index: 999;
            padding: 16px;
        }}

        .modal-backdrop.open {{
            display: flex;
        }}

        .modal-card {{
            background: var(--bg-surface);
            border: 1px solid var(--border-color);
            border-radius: 22px;
            width: 100%;
            max-width: 680px;
            padding: 24px;
            box-shadow: 0 24px 60px rgba(0, 0, 0, 0.5);
        }}

        .float-tg {{
            position: fixed;
            bottom: 20px;
            left: 20px;
            z-index: 90;
            background: linear-gradient(135deg, #0088cc, #229ED9);
            color: #FFFFFF;
            padding: 11px 16px;
            border-radius: 999px;
            font-weight: 800;
            font-size: 0.85rem;
            box-shadow: 0 10px 25px rgba(0, 136, 204, 0.38);
            display: inline-flex;
            align-items: center;
            gap: 8px;
            transition: var(--transition);
        }}

        .float-tg:hover {{
            transform: translateY(-2px);
        }}

        footer {{
            background: var(--bg-surface);
            border-top: 1px solid var(--border-color);
            padding: 36px 0 24px;
            margin-top: auto;
        }}

        .footer-grid {{
            display: grid;
            grid-template-columns: 1.4fr 1fr 1fr 1.3fr;
            gap: 24px;
            margin-bottom: 24px;
        }}

        .footer-col h4 {{
            font-size: 1rem;
            font-weight: 800;
            margin-bottom: 12px;
            color: var(--text-primary);
        }}

        .footer-col ul {{
            list-style: none;
            display: flex;
            flex-direction: column;
            gap: 8px;
            font-size: 0.86rem;
            color: var(--text-secondary);
        }}

        .footer-col ul a:hover {{
            color: var(--bh-red-bright);
        }}

        .footer-bottom {{
            border-top: 1px solid var(--border-color);
            padding-top: 16px;
            text-align: center;
            font-size: 0.8rem;
            color: var(--text-muted);
        }}

        @media (max-width: 920px) {{
            .hero-box {{
                grid-template-columns: 1fr;
            }}
            .footer-grid {{
                grid-template-columns: 1fr 1fr;
            }}
        }}

        @media (max-width: 600px) {{
            .container {{
                padding: 0 12px;
            }}
            .navbar-inner {{
                min-height: auto;
                gap: 8px;
                padding: 8px 0;
            }}
            .brand-logo-img {{
                height: 30px;
            }}
            .brand-title {{
                font-size: 1rem;
            }}
            .brand-sub {{
                display: none;
            }}
            .nav-actions {{
                gap: 5px;
            }}
            .theme-btn {{
                width: 30px;
                height: 30px;
                font-size: 0.85rem;
                border-radius: 8px;
            }}
            .btn-outline, .btn-primary {{
                padding: 5px 9px;
                font-size: 0.75rem;
                border-radius: 8px;
            }}
            .nav-search {{
                order: 3;
                flex: 0 0 100%;
                max-width: 100%;
                min-width: 0;
            }}
            .nav-search input {{
                padding: 7px 34px 7px 12px;
                font-size: 0.82rem;
            }}
            .nav-links {{
                order: 4;
                flex: 0 0 100%;
                flex-wrap: nowrap;
                overflow-x: auto;
                -webkit-overflow-scrolling: touch;
                scrollbar-width: none;
                gap: 6px;
                padding-bottom: 2px;
            }}
            .nav-links::-webkit-scrollbar {{
                display: none;
            }}
            .nav-link {{
                padding: 5px 10px;
                font-size: 0.8rem;
                white-space: nowrap;
            }}
            .footer-grid {{
                grid-template-columns: 1fr;
            }}
            .hero-title {{
                font-size: 1.65rem;
            }}
        }}
    </style>
</head>
<body>
    <header class="navbar">
        <div class="container navbar-inner">
            <a href="/" class="brand-link" title="ارجع للرئيسية">
                {logo_visual}
                <div class="brand-text">
                    <div class="brand-title"><span>صيدة</span> 🎯</div>
                    <div class="brand-sub">لقطات وتاريخ أسعار البحرين (BHD)</div>
                </div>
            </a>

            <div class="nav-actions">
                <button type="button" class="theme-btn" id="themeToggleBtn" title="بدّل الوضع الليلي والنهاري">☀️</button>
                {auth_buttons_html}
            </div>

            <form class="nav-search" action="/deals" method="get">
                <input type="text" name="q" id="globalSearchInput" placeholder="دوّر عن أي شي في البحرين (آيفون، لابتوب، عطور...)" />
                <button type="submit" aria-label="بحث">🔍</button>
            </form>

            <nav class="nav-links" aria-label="التنقل الرئيسي">
                <a href="/" class="{nav_cls('home')}">الرئيسية</a>
                <a href="/deals" class="{nav_cls('deals')}"><span class="live-dot"></span> الحين</a>
                <a href="/categories" class="{nav_cls('categories')}">الأقسام</a>
                <a href="/coupons" class="{nav_cls('coupons')}">🎟️ كوبونات</a>
                <a href="/stores" class="{nav_cls('stores')}">المتاجر</a>
            </nav>
        </div>
    </header>

    <main class="container">
        {body_html}
    </main>

    <a href="{TELEGRAM_CHANNEL_URL}" target="_blank" rel="noopener" class="float-tg">
        ✈️ قناة صيدة على تيليجرام
    </a>

    <div class="modal-backdrop" id="historyModal" onclick="if(event.target===this) closeHistoryModal()">
        <div class="modal-card">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px;">
                <h3 id="modalTitle" style="font-size:1.05rem; font-weight:800; line-height:1.4;">تاريخ سعر المنتج</h3>
                <button onclick="closeHistoryModal()" style="background:none; border:none; color:var(--text-secondary); font-size:1.4rem; cursor:pointer;">✕</button>
            </div>
            <div id="modalStats" style="display:grid; grid-template-columns:repeat(3,1fr); gap:10px; margin-bottom:16px;"></div>
            <div style="height:260px;">
                <canvas id="priceChartCanvas"></canvas>
            </div>
            <div style="margin-top:16px; display:flex; justify-content:flex-end; gap:10px;">
                <button onclick="closeHistoryModal()" class="btn-outline">سكّر</button>
                <a id="modalBuyLink" href="#" target="_blank" rel="noopener" class="btn-primary">روح للمتجر ↗</a>
            </div>
        </div>
    </div>

    <footer>
        <div class="container">
            <div class="footer-grid">
                <div class="footer-col">
                    <div class="brand-link" style="margin-bottom:10px;">
                        {logo_visual}
                        <div class="brand-text">
                            <div class="brand-title"><span>صيدة</span> 🎯</div>
                            <div class="brand-sub">لقطات البحرين أول بأول</div>
                        </div>
                    </div>
                    <p style="font-size:0.85rem; color:var(--text-secondary); line-height:1.7;">
                        منصتك البحرينية الذكية لمتابعة الأسعار وصيد الخصومات الحقيقية بالدينار البحريني (BHD / د.ب)، مع سجل كامل يوريك تاريخ السعر قبل ما تشتري.
                    </p>
                </div>

                <div class="footer-col">
                    <h4>المتاجر اللي نراقبها</h4>
                    <ul>
                        <li><a href="/deals?store=noon_bh">🟡 نون البحرين (شغال)</a></li>
                        <li><a href="/deals?store=extra_bh">🔵 إكسترا البحرين (شغال)</a></li>
                        <li><a href="/deals?store=microless_bh">🟠 ميكروليس البحرين (شغال)</a></li>
                        <li><a href="/deals?store=alershad_bh">🟤 الإرشاد البحرين (شغال)</a></li>
                        <li><a href="/deals?store=ramez_bh">🔴 رامز البحرين (شغال)</a></li>
                        <li><a href="/deals?store=hypermax_bh">🔴 هايبرماكس البحرين (شغال)</a></li>
                        <li><a href="/deals?store=ansar_bh">🩷 أنصار جاليري البحرين (شغال)</a></li>
                        <li><a href="/deals?store=zain_bh">🟣 زين البحرين (شغال)</a></li>
                        <li><a href="/deals?store=stc_bh">🟪 stc البحرين (شغال)</a></li>
                        <li><a href="/deals?store=batelco_bh">🔴 باتلكو البحرين (شغال)</a></li>
                        <li><a href="/deals?store=virgin_bh">🟥 فيرجن ميجاستور البحرين (شغال)</a></li>
                        <li><a href="/deals?store=jarir_bh">📕 مكتبة جرير البحرين (شغال)</a></li>
                        <li><a href="/deals?store=sharafdg_bh">🟨 شرف DG البحرين (شغال)</a></li>
                        <li><a href="/deals?store=ourshopee_bh">🟪 أور شوبي البحرين (شغال)</a></li>
                        <li><a href="/deals?store=advancedpc_bh">🟦 أدفانسد بي سي البحرين (شغال)</a></li>
                        <li><a href="/deals?store=lulu_bh">🟩 لولو هايبرماركت البحرين (شغال)</a></li>
                    </ul>
                </div>

                <div class="footer-col">
                    <h4>روابط سريعة</h4>
                    <ul>
                        <li><a href="/deals?real_only=1">🔥 صيدات حقيقية بس</a></li>
                        <li><a href="/deals?sort=discount">📉 أعلى خصم</a></li>
                        <li><a href="/categories">📂 الأقسام</a></li>
                        <li><a href="/coupons">🎟️ كوبونات الخصم</a></li>
                        <li><a href="{TELEGRAM_CHANNEL_URL}" target="_blank">✈️ قناة التيليجرام</a></li>
                    </ul>
                </div>

                <div class="footer-col">
                    <h4>🛡️ تنويه مهم</h4>
                    <p style="font-size:0.82rem; color:var(--text-secondary); line-height:1.7;">
                        الأسعار وتوفر المنتجات يتحدثون باستمرار، والسعر النهائي هو اللي يطلعلك في صفحة المتجر وقت الدفع. بعض الروابط قد تكون روابط عمولة بدون أي زيادة عليك.
                    </p>
                </div>
            </div>
            <div class="footer-bottom">
                © 2026 صيدة 🎯 — كل الحقوق محفوظة | مملكة البحرين (BHD)
            </div>
        </div>
    </footer>

    <script>
        (function() {{
            const saved = localStorage.getItem('seeda_bh_theme') || localStorage.getItem('mshatshata_theme') || 'dark';
            document.documentElement.setAttribute('data-theme', saved);
            const btn = document.getElementById('themeToggleBtn');
            if (btn) btn.textContent = saved === 'dark' ? '☀️' : '🌙';
            const qParam = new URLSearchParams(window.location.search).get('q');
            const gInput = document.getElementById('globalSearchInput');
            if (qParam && gInput && !gInput.value) gInput.value = qParam;
        }})();

        document.getElementById('themeToggleBtn').addEventListener('click', function() {{
            const current = document.documentElement.getAttribute('data-theme');
            const next = current === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', next);
            localStorage.setItem('seeda_bh_theme', next);
            this.textContent = next === 'dark' ? '☀️' : '🌙';
        }});

        function escapeHtml(str) {{
            if (!str) return '';
            return String(str)
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;');
        }}

        function getStoreLabel(storeKey) {{
            const map = {{
                extra_bh: 'إكسترا البحرين',
                microless_bh: 'ميكروليس البحرين',
                alershad_bh: 'الإرشاد البحرين',
                ramez_bh: 'رامز البحرين',
                hypermax_bh: 'هايبرماكس البحرين',
                ansar_bh: 'أنصار جاليري البحرين',
                zain_bh: 'زين البحرين',
                stc_bh: 'stc البحرين',
                batelco_bh: 'باتلكو البحرين',
                virgin_bh: 'فيرجن ميجاستور البحرين',
                jarir_bh: 'مكتبة جرير البحرين',
                sharafdg_bh: 'شرف DG البحرين',
                sharaf_bh: 'شرف DG البحرين',
                ourshopee_bh: 'أور شوبي البحرين',
                advancedpc_bh: 'أدفانسد بي سي البحرين',
                lulu_bh: 'لولو هايبرماركت البحرين',
                ashraf_bh: 'أشرف البحرين',
                talabat_bh: 'طلبات البحرين'
            }};
            return map[storeKey] || 'نون البحرين';
        }}

        function getDecimalsByStore(storeKey) {{
            return (
                storeKey === 'extra_bh' ||
                storeKey === 'microless_bh' ||
                storeKey === 'alershad_bh' ||
                storeKey === 'ramez_bh' ||
                storeKey === 'hypermax_bh' ||
                storeKey === 'ansar_bh' ||
                storeKey === 'zain_bh' ||
                storeKey === 'stc_bh' ||
                storeKey === 'batelco_bh' ||
                storeKey === 'sharafdg_bh' ||
                storeKey === 'sharaf_bh' ||
                storeKey === 'advancedpc_bh' ||
                storeKey === 'lulu_bh'
            ) ? 3 : 2;
        }}

        function fmtPrice(val, storeKey) {{
            const num = Number(val || 0);
            return num.toFixed(getDecimalsByStore(storeKey));
        }}

        function isBannedBannerUrl(u) {{
            if (!u) return true;
            const s = String(u).trim().toLowerCase();
            if (s.startsWith('data:image') || s.includes('blob.core.windows.net')) return true;
            return (
                s.includes('مشطشطة') ||
                s.includes('mshatshata') ||
                s.includes('banner') ||
                s.includes('placeholder') ||
                s.includes('no-image') ||
                s.includes('default')
            );
        }}

        function handleProductImageError(imgEl) {{
            const step = Number(imgEl.dataset.imgStep || '0');
            if (step === 0 && imgEl.dataset.proxy) {{
                imgEl.dataset.imgStep = '1';
                imgEl.src = imgEl.dataset.proxy;
                return;
            }}
            if (step <= 1 && imgEl.dataset.origin) {{
                imgEl.dataset.imgStep = '2';
                imgEl.src = imgEl.dataset.origin;
                return;
            }}
            imgEl.onerror = null;
            imgEl.src = '/favicon.svg';
        }}

        async function toggleSaveDeal(btn, payload) {{
            try {{
                const res = await fetch('/api/wishlist/toggle', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify(payload)
                }});
                if (res.status === 401) {{
                    const nextUrl = encodeURIComponent(window.location.pathname + window.location.search);
                    window.location.href = '/login/google?next=' + nextUrl;
                    return;
                }}
                const data = await res.json();
                if (data.ok) {{
                    btn.classList.toggle('saved', !!data.saved);
                    btn.textContent = data.saved ? '⭐ محفوظ' : '☆ احفظه';
                }}
            }} catch (e) {{
                console.error(e);
            }}
        }}

        function renderProductCard(p) {{
            const storeKey = p.store || (String(p.sku || '').startsWith('ANSAR_') ? 'ansar_bh' : 'noon_bh');
            const storeLabel = getStoreLabel(storeKey);
            const currStr = fmtPrice(p.current_price, storeKey);
            const oldStr = p.old_price ? fmtPrice(p.old_price, storeKey) : null;
            const lowStr = fmtPrice(p.lowest_price, storeKey);
            const avgStr = fmtPrice(p.avg_price, storeKey);
            const unitSuffix = 'د.ب';

            const rawImg = String(p.image_url || '').trim();
            const isLocalImg = rawImg.startsWith('/static/images/') && !isBannedBannerUrl(rawImg);
            const isHttpImg = /^https?:\/\//i.test(rawImg) && !isBannedBannerUrl(rawImg);

            const localSrc = isLocalImg ? rawImg : '';
            const originImg = isHttpImg ? rawImg : '';
            const proxyImg = isHttpImg ? ('/img-proxy?url=' + encodeURIComponent(rawImg)) : '';

            const primaryImg = localSrc || proxyImg || originImg || '/favicon.svg';
            const initialStep = localSrc ? '0' : (proxyImg ? '1' : (originImg ? '2' : '3'));

            const oldHtml = oldStr ? `<span class="price-old">${{oldStr}} ${{unitSuffix}}</span>` : '';
            const discHtml = p.discount_pct > 0 ? `<span class="badge-disc">-${{Math.round(p.discount_pct)}}%</span>` : '';
            const realHtml = p.is_real_deal ? `<span class="badge-real">🔥 خوش صيدة</span>` : (p.is_lowest_now ? `<span class="badge-real">📉 أرخص سعر</span>` : '');
            const isSaved = !!p.is_saved;
            const savePayload = JSON.stringify({{
                deal_key: String(p.sku),
                title: p.name || '',
                price: `${{currStr}} BHD`,
                url: p.affiliate_url || p.product_url || ''
            }}).replace(/"/g, '&quot;');
            return `
                <article class="deal-card">
                    <div class="deal-thumb">
                        <div class="badges-top-right">${{discHtml}}${{realHtml}}</div>
                        <span class="badge-store">${{escapeHtml(storeLabel)}}</span>
                        <img src="${{escapeHtml(primaryImg)}}" data-proxy="${{escapeHtml(proxyImg)}}" data-origin="${{escapeHtml(originImg)}}" data-img-step="${{initialStep}}" alt="${{escapeHtml(p.name)}}" loading="lazy" onerror="handleProductImageError(this)" />
                    </div>
                    <div class="deal-body">
                        <div class="deal-cat">${{escapeHtml(p.category || 'عام')}} • ${{escapeHtml(p.updated_ago || '')}}</div>
                        <h3 class="deal-title" title="${{escapeHtml(p.name)}}">${{escapeHtml(p.name)}}</h3>
                        <div class="price-row">
                            <span class="price-now">${{currStr}} BHD</span>
                            ${{oldHtml}}
                        </div>
                        <div class="history-mini">
                            <span>الأقل: <b>${{lowStr}} ${{unitSuffix}}</b></span>
                            <span>المتوسط: <b>${{avgStr}} ${{unitSuffix}}</b></span>
                        </div>
                        <div class="card-actions">
                            <a href="${{escapeHtml(p.affiliate_url)}}" target="_blank" rel="noopener" class="btn-buy">روح للعرض ↗</a>
                            <button type="button" class="btn-hist btn-save ${{isSaved ? 'saved' : ''}}" onclick='toggleSaveDeal(this, ${{savePayload}})' title="احفظ في المفضلة">${{isSaved ? '⭐ محفوظ' : '☆ احفظه'}}</button>
                            <button type="button" class="btn-hist" onclick="openHistoryModal('${{escapeHtml(p.sku)}}')" title="چوف تاريخ السعر">📊</button>
                        </div>
                    </div>
                </article>
            `;
        }}

        let chartInstance = null;
        async function openHistoryModal(sku) {{
            const modal = document.getElementById('historyModal');
            modal.classList.add('open');
            document.getElementById('modalTitle').textContent = 'قاعدين نحمّل تاريخ السعر...';
            try {{
                const res = await fetch('/api/history/' + encodeURIComponent(sku));
                const data = await res.json();
                if (!res.ok) return;
                const p = data.product;
                const storeKey = p.store || (String(p.sku || '').startsWith('ANSAR_') ? 'ansar_bh' : 'noon_bh');
                document.getElementById('modalTitle').textContent = p.name;
                document.getElementById('modalBuyLink').href = p.affiliate_url;
                document.getElementById('modalStats').innerHTML = `
                    <div style="background:var(--bg-input); padding:10px; border-radius:12px; text-align:center;">
                        <div style="font-size:0.75rem; color:var(--text-secondary);">السعر الحين</div>
                        <strong style="color:var(--bh-red-bright); font-size:1.05rem;">${{fmtPrice(p.current_price, storeKey)}} BHD</strong>
                    </div>
                    <div style="background:var(--bg-input); padding:10px; border-radius:12px; text-align:center;">
                        <div style="font-size:0.75rem; color:var(--text-secondary);">أرخص سعر مرصود</div>
                        <strong style="color:var(--bh-green); font-size:1.05rem;">${{fmtPrice(p.lowest_price, storeKey)}} BHD</strong>
                    </div>
                    <div style="background:var(--bg-input); padding:10px; border-radius:12px; text-align:center;">
                        <div style="font-size:0.75rem; color:var(--text-secondary);">متوسط السعر</div>
                        <strong style="font-size:1.05rem;">${{fmtPrice(p.avg_price, storeKey)}} BHD</strong>
                    </div>
                `;
                const labels = data.history.map(h => h.date);
                const prices = data.history.map(h => h.price);
                const ctx = document.getElementById('priceChartCanvas').getContext('2d');
                if (chartInstance) chartInstance.destroy();
                chartInstance = new Chart(ctx, {{
                    type: 'line',
                    data: {{
                        labels,
                        datasets: [{{
                            label: 'السعر (BHD)',
                            data: prices,
                            borderColor: '#EF233C',
                            backgroundColor: 'rgba(239, 35, 60, 0.16)',
                            fill: true,
                            tension: 0.3,
                            pointRadius: 4
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{ legend: {{ display: false }} }}
                    }}
                }});
            }} catch (e) {{
                console.error(e);
            }}
        }}

        function closeHistoryModal() {{
            document.getElementById('historyModal').classList.remove('open');
        }}
    </script>
    {extra_script}
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
def page_home(request: Request):
    user = get_current_user(request)
    body = f"""
    <section class="hero-box">
        <div>
            <div class="hero-badge">🇧🇭 صيدة البحرين • متابعة مستمرة للأسعار</div>
            <h1 class="hero-title">أقوى صيدات البحرين... <span>أول ما تنزل 🎯</span></h1>
            <p class="hero-desc">
                نراقب الأسعار بالدينار البحريني (BHD / د.ب) في متاجر البحرين ونوريك تاريخ السعر عشان تعرف إذا الخصم صج يسوى ولا بس كلام.
            </p>
            <div class="hero-cta-group">
                <a href="/deals?real_only=1" class="btn-primary">🔥 چوف الصيدات الحقيقية</a>
                <a href="/deals" class="btn-outline">⚡ كل العروض الحين</a>
                <a href="/coupons" class="btn-outline">🎟️ كوبونات الخصم</a>
                <a href="{TELEGRAM_CHANNEL_URL}" target="_blank" rel="noopener" class="btn-outline">✈️ دش قناة التيليجرام</a>
            </div>
            <div class="hero-stats">
                <div class="stat-item"><strong id="statTotal">--</strong><span>منتج نراقبه في البحرين</span></div>
                <div class="stat-item"><strong id="statReal" style="color:var(--bh-green);">--</strong><span>خوش صيدة مؤكدة</span></div>
                <div class="stat-item"><strong id="statMaxDisc" style="color:var(--bh-red-bright);">--%</strong><span>أكبر خصم مرصود</span></div>
                <div class="stat-item"><strong id="statUpdated" style="font-size:1rem;">--</strong><span>آخر تحديث للأسعار</span></div>
            </div>
        </div>

        <div class="hero-showcase">
            <div class="showcase-top">
                <span style="font-weight:800; font-size:0.95rem;">📊 شلون نعرف الصيدة الصجية؟</span>
                <span class="tag-pill">شغال 24/7</span>
            </div>
            <div class="showcase-row">
                <div>
                    <div style="font-weight:800; font-size:0.9rem;">1. نقارن بأرخص سعر مرصود</div>
                    <div style="font-size:0.78rem; color:var(--text-secondary);">نشيك تاريخ السعر من قبل لا نرشحلك</div>
                </div>
                <span style="color:var(--bh-green); font-weight:900;">✓ مضبوط</span>
            </div>
            <div class="showcase-row">
                <div>
                    <div style="font-weight:800; font-size:0.9rem;">2. نكشف الخصومات الوهمية</div>
                    <div style="font-size:0.78rem; color:var(--text-secondary);">نقيس السعر الحالي على متوسط سعر المنتج</div>
                </div>
                <span style="color:var(--bh-red-bright); font-weight:900;">🎯 فلترة ذكية</span>
            </div>
            <div class="showcase-row">
                <div>
                    <div style="font-weight:800; font-size:0.9rem;">3. تنبيهات سريعة على تيليجرام</div>
                    <div style="font-size:0.78rem; color:var(--text-secondary);">أول ما يطيح السعر يوصلك الخبر بالصورة</div>
                </div>
                <a href="{TELEGRAM_CHANNEL_URL}" target="_blank" style="color:#38BDF8; font-weight:800; font-size:0.84rem;">دش الحين ↗</a>
            </div>
        </div>
    </section>

    <section>
        <div class="sec-head">
            <div>
                <h2 class="sec-title">🏬 المتاجر في البحرين</h2>
                <div class="sec-sub">نون وإكسترا وميكروليس والإرشاد ورامز وهايبرماكس وأنصار جاليري ولولو وزين وstc وباتلكو وفيرجن وجرير وشرف DG وأور شوبي وأدفانسد بي سي البحرين شغالين الحين</div>
            </div>
            <a href="/stores" class="btn-outline">كل المتاجر ←</a>
        </div>
        <div class="stores-grid">
            <a href="/deals?store=noon_bh" class="store-card" style="border-color: rgba(250, 204, 21, 0.45);">
                <div class="store-icon" style="background:#FACC15; color:#111827;">noon</div>
                <div class="store-name">نون البحرين</div>
                <div class="store-meta" id="noonStoreMeta">شغال الحين • BHD</div>
            </a>
            <a href="/deals?store=extra_bh" class="store-card" style="border-color: rgba(59, 130, 246, 0.5);">
                <div class="store-icon" style="background:#1D4ED8; color:#FFFFFF;">eXtra</div>
                <div class="store-name">إكسترا البحرين</div>
                <div class="store-meta" id="extraStoreMeta">شغال الحين • BHD</div>
            </a>
            <a href="/deals?store=microless_bh" class="store-card" style="border-color: rgba(249, 115, 22, 0.55);">
                <div class="store-icon" style="background:#EA580C; color:#FFFFFF;">Microless</div>
                <div class="store-name">ميكروليس البحرين</div>
                <div class="store-meta" id="microlessStoreMeta">شغال الحين • BHD</div>
            </a>
            <a href="/deals?store=alershad_bh" class="store-card" style="border-color: rgba(180, 83, 9, 0.55);">
                <div class="store-icon" style="background:#92400E; color:#FFFFFF;">AlErshad</div>
                <div class="store-name">الإرشاد البحرين</div>
                <div class="store-meta" id="alershadStoreMeta">شغال الحين • BHD</div>
            </a>
            <a href="/deals?store=ramez_bh" class="store-card" style="border-color: rgba(220, 38, 38, 0.55);">
                <div class="store-icon" style="background:#B91C1C; color:#FFFFFF;">Ramez</div>
                <div class="store-name">رامز البحرين</div>
                <div class="store-meta" id="ramezStoreMeta">شغال الحين • BHD</div>
            </a>
            <a href="/deals?store=hypermax_bh" class="store-card" style="border-color: rgba(239, 68, 68, 0.55);">
                <div class="store-icon" style="background:#DC2626; color:#FFFFFF;">HyperMax</div>
                <div class="store-name">هايبرماكس البحرين</div>
                <div class="store-meta" id="hypermaxStoreMeta">شغال الحين • BHD</div>
            </a>
            <a href="/deals?store=ansar_bh" class="store-card" style="border-color: rgba(236, 72, 153, 0.55);">
                <div class="store-icon" style="background:#DB2777; color:#FFFFFF;">Ansar</div>
                <div class="store-name">أنصار جاليري البحرين</div>
                <div class="store-meta" id="ansarStoreMeta">شغال الحين • BHD</div>
            </a>
            <a href="/deals?store=zain_bh" class="store-card" style="border-color: rgba(168, 85, 247, 0.5);">
                <div class="store-icon" style="background:#7E22CE; color:#FFFFFF;">zain</div>
                <div class="store-name">زين البحرين</div>
                <div class="store-meta" id="zainStoreMeta">شغال الحين • BHD</div>
            </a>
            <a href="/deals?store=stc_bh" class="store-card" style="border-color: rgba(192, 38, 211, 0.55);">
                <div class="store-icon" style="background:#4F008C; color:#FFFFFF;">stc</div>
                <div class="store-name">stc البحرين</div>
                <div class="store-meta" id="stcStoreMeta">شغال الحين • BHD</div>
            </a>
            <a href="/deals?store=batelco_bh" class="store-card" style="border-color: rgba(225, 29, 72, 0.55);">
                <div class="store-icon" style="background:#E11D48; color:#FFFFFF;">Batelco</div>
                <div class="store-name">باتلكو البحرين</div>
                <div class="store-meta" id="batelcoStoreMeta">شغال الحين • BHD</div>
            </a>
            <a href="/deals?store=virgin_bh" class="store-card" style="border-color: rgba(239, 68, 68, 0.55);">
                <div class="store-icon" style="background:#B91C1C; color:#FFFFFF;">Virgin</div>
                <div class="store-name">فيرجن ميجاستور</div>
                <div class="store-meta" id="virginStoreMeta">شغال الحين • BHD</div>
            </a>
            <a href="/deals?store=jarir_bh" class="store-card" style="border-color: rgba(220, 38, 38, 0.55);">
                <div class="store-icon" style="background:#DC2626; color:#FFFFFF;">جرير</div>
                <div class="store-name">مكتبة جرير البحرين</div>
                <div class="store-meta" id="jarirStoreMeta">شغال الحين • BHD</div>
            </a>
            <a href="/deals?store=sharafdg_bh" class="store-card" style="border-color: rgba(245, 158, 11, 0.55);">
                <div class="store-icon" style="background:#D97706; color:#FFFFFF;">SDG</div>
                <div class="store-name">شرف DG البحرين</div>
                <div class="store-meta" id="sharafdgStoreMeta">شغال الحين • BHD</div>
            </a>
            <a href="/deals?store=ourshopee_bh" class="store-card" style="border-color: rgba(124, 58, 237, 0.55);">
                <div class="store-icon" style="background:#6D28D9; color:#FFFFFF;">OurShopee</div>
                <div class="store-name">أور شوبي البحرين</div>
                <div class="store-meta" id="ourshopeeStoreMeta">شغال الحين • BHD</div>
            </a>
            <a href="/deals?store=advancedpc_bh" class="store-card" style="border-color: rgba(37, 99, 235, 0.55);">
                <div class="store-icon" style="background:#1E40AF; color:#FFFFFF;">AdvPC</div>
                <div class="store-name">أدفانسد بي سي البحرين</div>
                <div class="store-meta" id="advancedpcStoreMeta">شغال الحين • BHD</div>
            </a>
            <a href="/deals?store=lulu_bh" class="store-card" style="border-color: rgba(22, 163, 74, 0.55);">
                <div class="store-icon" style="background:#15803D; color:#FFFFFF;">LuLu</div>
                <div class="store-name">لولو هايبرماركت البحرين</div>
                <div class="store-meta" id="luluStoreMeta">شغال الحين • BHD</div>
            </a>
        </div>
    </section>

    <section>
        <div class="sec-head">
            <div>
                <h2 class="sec-title">📂 الأقسام</h2>
                <div class="sec-sub">اختر القسم وشوف الصيدات اللي فيه</div>
            </div>
            <a href="/categories" class="btn-outline">كل الأقسام ←</a>
        </div>
        <div class="cats-grid" id="homeCatsGrid"></div>
    </section>

    <section style="margin-bottom: 38px;">
        <div class="sec-head">
            <div>
                <h2 class="sec-title"><span class="live-dot"></span> صيدات نازلة الحين</h2>
                <div class="sec-sub">أحدث المنتجات اللي نزلت أسعارها أو عليها خصم يسوى</div>
            </div>
            <a href="/deals" class="btn-primary">چوف الكل ←</a>
        </div>
        <div class="products-grid" id="homeDealsGrid"></div>
    </section>
    """

    script = """
    <script>
        function bindStoreMeta(sum) {
            const st = sum.stores || {};
            const mapping = {
                noon_bh: 'noonStoreMeta',
                extra_bh: 'extraStoreMeta',
                microless_bh: 'microlessStoreMeta',
                alershad_bh: 'alershadStoreMeta',
                ramez_bh: 'ramezStoreMeta',
                hypermax_bh: 'hypermaxStoreMeta',
                ansar_bh: 'ansarStoreMeta',
                zain_bh: 'zainStoreMeta',
                stc_bh: 'stcStoreMeta',
                batelco_bh: 'batelcoStoreMeta',
                virgin_bh: 'virginStoreMeta',
                jarir_bh: 'jarirStoreMeta',
                ourshopee_bh: 'ourshopeeStoreMeta',
                advancedpc_bh: 'advancedpcStoreMeta',
                lulu_bh: 'luluStoreMeta'
            };
            Object.keys(mapping).forEach(k => {
                if (st[k]) {
                    document.getElementById(mapping[k]).textContent = `${st[k].count} منتج • خصم لحد ${st[k].max_discount}%`;
                }
            });
            const sdg = st.sharafdg_bh || st.sharaf_bh;
            if (sdg) {
                document.getElementById('sharafdgStoreMeta').textContent = `${sdg.count} منتج • خصم لحد ${sdg.max_discount}%`;
            }
        }

        async function loadHome() {
            try {
                const sumRes = await fetch('/api/summary');
                const sum = await sumRes.json();
                document.getElementById('statTotal').textContent = sum.total_active.toLocaleString('ar-BH');
                document.getElementById('statReal').textContent = sum.real_deals.toLocaleString('ar-BH');
                document.getElementById('statMaxDisc').textContent = sum.max_discount + '%';
                document.getElementById('statUpdated').textContent = sum.last_updated_text;
                bindStoreMeta(sum);

                const catsGrid = document.getElementById('homeCatsGrid');
                catsGrid.innerHTML = sum.categories.slice(0, 8).map(c => `
                    <a href="/deals?category=${encodeURIComponent(c.name)}" class="cat-card">
                        <div style="display:flex; align-items:center; gap:12px;">
                            <div class="cat-badge-icon">🎯</div>
                            <div>
                                <div style="font-weight:800; font-size:0.95rem;">${escapeHtml(c.name)}</div>
                                <div style="font-size:0.78rem; color:var(--text-secondary);">${c.count} منتج • خصم لحد ${c.max_discount}%</div>
                            </div>
                        </div>
                        <span style="color:var(--text-muted);">←</span>
                    </a>
                `).join('');

                const prodRes = await fetch('/api/products?sort=real&limit=12');
                const prodData = await prodRes.json();
                const grid = document.getElementById('homeDealsGrid');
                if (!prodData.items.length) {
                    grid.innerHTML = '<p style="color:var(--text-secondary);">ما في منتجات مسجلة الحين، شغّل الكوليكتور عشان يبدأ يجمع.</p>';
                } else {
                    grid.innerHTML = prodData.items.map(renderProductCard).join('');
                }
            } catch (e) {
                console.error(e);
            }
        }
        loadHome();
    </script>
    """
    return render_layout("الرئيسية", "home", body, script, user=user)


@app.get("/deals", response_class=HTMLResponse)
def page_deals(request: Request):
    user = get_current_user(request)
    body = """
    <div class="sec-head">
        <div>
            <h1 class="sec-title"><span class="live-dot"></span> العروض الحين في البحرين</h1>
            <div class="sec-sub">دوّر وفلتر على كيفك حسب المتجر والقسم والصيدات الصجية</div>
        </div>
        <div id="dealsCountBadge" class="tag-pill">قاعدين نحمّل...</div>
    </div>

    <div class="filter-bar">
        <input type="text" id="filterQ" placeholder="دوّر بالاسم..." style="flex:1; min-width:200px;" />
        <select id="filterStore">
            <option value="">كل المتاجر</option>
            <option value="noon_bh">نون البحرين</option>
            <option value="extra_bh">إكسترا البحرين</option>
            <option value="microless_bh">ميكروليس البحرين</option>
            <option value="alershad_bh">الإرشاد البحرين</option>
            <option value="ramez_bh">رامز البحرين</option>
            <option value="hypermax_bh">هايبرماكس البحرين</option>
            <option value="ansar_bh">أنصار جاليري البحرين</option>
            <option value="zain_bh">زين البحرين</option>
            <option value="stc_bh">stc البحرين</option>
            <option value="batelco_bh">باتلكو البحرين</option>
            <option value="virgin_bh">فيرجن ميجاستور البحرين</option>
            <option value="jarir_bh">مكتبة جرير البحرين</option>
            <option value="sharafdg_bh">شرف DG البحرين</option>
            <option value="ourshopee_bh">أور شوبي البحرين</option>
            <option value="advancedpc_bh">أدفانسد بي سي البحرين</option>
            <option value="lulu_bh">لولو هايبرماركت البحرين</option>
        </select>
        <select id="filterCat">
            <option value="">كل الأقسام</option>
        </select>
        <select id="filterSort">
            <option value="recent">الأحدث نزولاً</option>
            <option value="real">خوش صيدات أولاً</option>
            <option value="discount">أعلى خصم</option>
            <option value="price_asc">السعر: من الأرخص للأغلى</option>
            <option value="price_desc">السعر: من الأغلى للأرخص</option>
        </select>
        <button type="button" id="toggleRealBtn" class="chip-toggle">🔥 صيدات حقيقية بس</button>
        <button type="button" id="applyBtn" class="btn-primary">طبّق</button>
    </div>

    <div class="products-grid" id="dealsGrid"></div>
    <div id="paginationBox" style="display:flex; justify-content:center; gap:10px; margin-top:28px;"></div>
    """

    script = """
    <script>
        const urlParams = new URLSearchParams(window.location.search);
        let realOnly = urlParams.get('real_only') === '1' ? 1 : 0;
        let currentPage = 1;

        document.getElementById('filterQ').value = urlParams.get('q') || '';
        document.getElementById('filterStore').value = urlParams.get('store') || '';
        document.getElementById('filterSort').value = urlParams.get('sort') || 'recent';
        if (realOnly) document.getElementById('toggleRealBtn').classList.add('active');

        document.getElementById('toggleRealBtn').addEventListener('click', function() {
            realOnly = realOnly ? 0 : 1;
            this.classList.toggle('active', realOnly === 1);
            applyFilters(1);
        });

        document.getElementById('filterStore').addEventListener('change', function() {
            applyFilters(1);
        });

        document.getElementById('filterSort').addEventListener('change', function() {
            applyFilters(1);
        });

        document.getElementById('filterCat').addEventListener('change', function() {
            applyFilters(1);
        });

        document.getElementById('applyBtn').addEventListener('click', function() {
            applyFilters(1);
        });

        document.getElementById('filterQ').addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                applyFilters(1);
            }
        });

        async function initCategoriesFilter() {
            const res = await fetch('/api/summary');
            const data = await res.json();
            const sel = document.getElementById('filterCat');
            const targetCat = urlParams.get('category') || '';
            data.categories.forEach(c => {
                const opt = document.createElement('option');
                opt.value = c.name;
                opt.textContent = `${c.name} (${c.count})`;
                if (c.name === targetCat) opt.selected = true;
                sel.appendChild(opt);
            });
        }

        async function applyFilters(page = 1) {
            currentPage = page;
            const q = document.getElementById('filterQ').value;
            const store = document.getElementById('filterStore').value;
            const cat = document.getElementById('filterCat').value;
            const sort = document.getElementById('filterSort').value;

            const qs = new URLSearchParams({
                q, category: cat, store, sort, real_only: realOnly, page, limit: 24
            });
            const res = await fetch('/api/products?' + qs.toString());
            const data = await res.json();

            document.getElementById('dealsCountBadge').textContent = `${data.total} عرض متوفر`;
            const grid = document.getElementById('dealsGrid');
            if (!data.items.length) {
                grid.innerHTML = '<p style="color:var(--text-secondary);">ما حصلنا شي يطابق بحثك الحين.</p>';
            } else {
                grid.innerHTML = data.items.map(renderProductCard).join('');
            }

            const pag = document.getElementById('paginationBox');
            pag.innerHTML = '';
            if (data.pages > 1) {
                if (page > 1) {
                    pag.innerHTML += `<button class="btn-outline" onclick="applyFilters(${page - 1})">اللي قبل</button>`;
                }
                pag.innerHTML += `<span style="padding:8px 14px; font-weight:700;">صفحة ${page} من ${data.pages}</span>`;
                if (page < data.pages) {
                    pag.innerHTML += `<button class="btn-outline" onclick="applyFilters(${page + 1})">اللي بعدها</button>`;
                }
            }
        }

        initCategoriesFilter().then(() => applyFilters(1));
    </script>
    """
    return render_layout("العروض الحين", "deals", body, script, user=user)


@app.get("/categories", response_class=HTMLResponse)
def page_categories(request: Request):
    user = get_current_user(request)
    body = """
    <div class="sec-head">
        <div>
            <h1 class="sec-title">📂 الأقسام</h1>
            <div class="sec-sub">اختر القسم وشوف العروض وتاريخ الأسعار فيه</div>
        </div>
    </div>
    <div class="cats-grid" id="allCatsGrid"></div>
    """
    script = """
    <script>
        fetch('/api/summary').then(r => r.json()).then(data => {
            const grid = document.getElementById('allCatsGrid');
            grid.innerHTML = data.categories.map(c => `
                <a href="/deals?category=${encodeURIComponent(c.name)}" class="cat-card">
                    <div style="display:flex; align-items:center; gap:14px;">
                        <div class="cat-badge-icon">🎯</div>
                        <div>
                            <div style="font-weight:800; font-size:1rem;">${escapeHtml(c.name)}</div>
                            <div style="font-size:0.8rem; color:var(--text-secondary);">${c.count} منتج • خصم لحد ${c.max_discount}%</div>
                        </div>
                    </div>
                    <span style="font-weight:900; color:var(--bh-red-bright);">←</span>
                </a>
            `).join('');
        });
    </script>
    """
    return render_layout("الأقسام", "categories", body, script, user=user)


@app.get("/stores", response_class=HTMLResponse)
def page_stores(request: Request):
    user = get_current_user(request)
    body = """
    <div class="sec-head">
        <div>
            <h1 class="sec-title">🏬 المتاجر في البحرين 🇧🇭</h1>
            <div class="sec-sub">المتاجر اللي نتابع أسعارها ونطلعلك صيداتها</div>
        </div>
    </div>
    <div class="stores-grid">
        <a href="/deals?store=noon_bh" class="store-card" style="border-color: rgba(250, 204, 21, 0.55);">
            <div class="store-icon" style="background:#FACC15; color:#111827;">noon</div>
            <div class="store-name">نون البحرين</div>
            <div style="font-size:0.76rem; color:var(--text-secondary); margin-bottom:6px;">BH البحرين • عملة BHD</div>
            <div class="store-meta" id="storeNoonStats">شغال الحين</div>
        </a>
        <a href="/deals?store=extra_bh" class="store-card" style="border-color: rgba(59, 130, 246, 0.55);">
            <div class="store-icon" style="background:#1D4ED8; color:#FFFFFF;">eXtra</div>
            <div class="store-name">إكسترا البحرين</div>
            <div style="font-size:0.76rem; color:var(--text-secondary); margin-bottom:6px;">BH البحرين • عملة BHD</div>
            <div class="store-meta" id="storeExtraStats">شغال الحين</div>
        </a>
        <a href="/deals?store=microless_bh" class="store-card" style="border-color: rgba(249, 115, 22, 0.55);">
            <div class="store-icon" style="background:#EA580C; color:#FFFFFF;">Microless</div>
            <div class="store-name">ميكروليس البحرين</div>
            <div style="font-size:0.76rem; color:var(--text-secondary); margin-bottom:6px;">BH البحرين • عملة BHD</div>
            <div class="store-meta" id="storeMicrolessStats">شغال الحين</div>
        </a>
        <a href="/deals?store=alershad_bh" class="store-card" style="border-color: rgba(180, 83, 9, 0.55);">
            <div class="store-icon" style="background:#92400E; color:#FFFFFF;">AlErshad</div>
            <div class="store-name">الإرشاد البحرين</div>
            <div style="font-size:0.76rem; color:var(--text-secondary); margin-bottom:6px;">BH البحرين • عملة BHD</div>
            <div class="store-meta" id="storeAlershadStats">شغال الحين</div>
        </a>
        <a href="/deals?store=ramez_bh" class="store-card" style="border-color: rgba(220, 38, 38, 0.55);">
            <div class="store-icon" style="background:#B91C1C; color:#FFFFFF;">Ramez</div>
            <div class="store-name">رامز البحرين</div>
            <div style="font-size:0.76rem; color:var(--text-secondary); margin-bottom:6px;">BH البحرين • عملة BHD</div>
            <div class="store-meta" id="storeRamezStats">شغال الحين</div>
        </a>
        <a href="/deals?store=hypermax_bh" class="store-card" style="border-color: rgba(239, 68, 68, 0.55);">
            <div class="store-icon" style="background:#DC2626; color:#FFFFFF;">HyperMax</div>
            <div class="store-name">هايبرماكس البحرين</div>
            <div style="font-size:0.76rem; color:var(--text-secondary); margin-bottom:6px;">BH البحرين • عملة BHD</div>
            <div class="store-meta" id="storeHypermaxStats">شغال الحين</div>
        </a>
        <a href="/deals?store=ansar_bh" class="store-card" style="border-color: rgba(236, 72, 153, 0.55);">
            <div class="store-icon" style="background:#DB2777; color:#FFFFFF;">Ansar</div>
            <div class="store-name">أنصار جاليري البحرين</div>
            <div style="font-size:0.76rem; color:var(--text-secondary); margin-bottom:6px;">BH البحرين • عملة BHD</div>
            <div class="store-meta" id="storeAnsarStats">شغال الحين</div>
        </a>
        <a href="/deals?store=zain_bh" class="store-card" style="border-color: rgba(168, 85, 247, 0.55);">
            <div class="store-icon" style="background:#7E22CE; color:#FFFFFF;">zain</div>
            <div class="store-name">زين البحرين</div>
            <div style="font-size:0.76rem; color:var(--text-secondary); margin-bottom:6px;">BH البحرين • عملة BHD</div>
            <div class="store-meta" id="storeZainStats">شغال الحين</div>
        </a>
        <a href="/deals?store=stc_bh" class="store-card" style="border-color: rgba(192, 38, 211, 0.55);">
            <div class="store-icon" style="background:#4F008C; color:#FFFFFF;">stc</div>
            <div class="store-name">stc البحرين</div>
            <div style="font-size:0.76rem; color:var(--text-secondary); margin-bottom:6px;">BH البحرين • عملة BHD</div>
            <div class="store-meta" id="storeStcStats">شغال الحين</div>
        </a>
        <a href="/deals?store=batelco_bh" class="store-card" style="border-color: rgba(225, 29, 72, 0.55);">
            <div class="store-icon" style="background:#E11D48; color:#FFFFFF;">Batelco</div>
            <div class="store-name">باتلكو البحرين</div>
            <div style="font-size:0.76rem; color:var(--text-secondary); margin-bottom:6px;">BH البحرين • عملة BHD</div>
            <div class="store-meta" id="storeBatelcoStats">شغال الحين</div>
        </a>
        <a href="/deals?store=virgin_bh" class="store-card" style="border-color: rgba(239, 68, 68, 0.55);">
            <div class="store-icon" style="background:#B91C1C; color:#FFFFFF;">Virgin</div>
            <div class="store-name">فيرجن ميجاستور البحرين</div>
            <div style="font-size:0.76rem; color:var(--text-secondary); margin-bottom:6px;">BH البحرين • عملة BHD</div>
            <div class="store-meta" id="storeVirginStats">شغال الحين</div>
        </a>
        <a href="/deals?store=jarir_bh" class="store-card" style="border-color: rgba(220, 38, 38, 0.55);">
            <div class="store-icon" style="background:#DC2626; color:#FFFFFF;">جرير</div>
            <div class="store-name">مكتبة جرير البحرين</div>
            <div style="font-size:0.76rem; color:var(--text-secondary); margin-bottom:6px;">BH البحرين • عملة BHD</div>
            <div class="store-meta" id="storeJarirStats">شغال الحين</div>
        </a>
        <a href="/deals?store=sharafdg_bh" class="store-card" style="border-color: rgba(245, 158, 11, 0.55);">
            <div class="store-icon" style="background:#D97706; color:#FFFFFF;">SDG</div>
            <div class="store-name">شرف DG البحرين</div>
            <div style="font-size:0.76rem; color:var(--text-secondary); margin-bottom:6px;">BH البحرين • عملة BHD</div>
            <div class="store-meta" id="storeSharafdgStats">شغال الحين</div>
        </a>
        <a href="/deals?store=ourshopee_bh" class="store-card" style="border-color: rgba(124, 58, 237, 0.55);">
            <div class="store-icon" style="background:#6D28D9; color:#FFFFFF;">OurShopee</div>
            <div class="store-name">أور شوبي البحرين</div>
            <div style="font-size:0.76rem; color:var(--text-secondary); margin-bottom:6px;">BH البحرين • عملة BHD</div>
            <div class="store-meta" id="storeOurshopeeStats">شغال الحين</div>
        </a>
        <a href="/deals?store=advancedpc_bh" class="store-card" style="border-color: rgba(37, 99, 235, 0.55);">
            <div class="store-icon" style="background:#1E40AF; color:#FFFFFF;">AdvPC</div>
            <div class="store-name">أدفانسد بي سي البحرين</div>
            <div style="font-size:0.76rem; color:var(--text-secondary); margin-bottom:6px;">BH البحرين • عملة BHD</div>
            <div class="store-meta" id="storeAdvancedpcStats">شغال الحين</div>
        </a>
        <a href="/deals?store=lulu_bh" class="store-card" style="border-color: rgba(22, 163, 74, 0.55);">
            <div class="store-icon" style="background:#15803D; color:#FFFFFF;">LuLu</div>
            <div class="store-name">لولو هايبرماركت البحرين</div>
            <div style="font-size:0.76rem; color:var(--text-secondary); margin-bottom:6px;">BH البحرين • عملة BHD</div>
            <div class="store-meta" id="storeLuluStats">شغال الحين</div>
        </a>
    </div>
    """
    script = """
    <script>
        fetch('/api/summary').then(r => r.json()).then(d => {
            const st = d.stores || {};
            const ids = {
                noon_bh: 'storeNoonStats',
                extra_bh: 'storeExtraStats',
                microless_bh: 'storeMicrolessStats',
                alershad_bh: 'storeAlershadStats',
                ramez_bh: 'storeRamezStats',
                hypermax_bh: 'storeHypermaxStats',
                ansar_bh: 'storeAnsarStats',
                zain_bh: 'storeZainStats',
                stc_bh: 'storeStcStats',
                batelco_bh: 'storeBatelcoStats',
                virgin_bh: 'storeVirginStats',
                jarir_bh: 'storeJarirStats',
                ourshopee_bh: 'storeOurshopeeStats',
                advancedpc_bh: 'storeAdvancedpcStats',
                lulu_bh: 'storeLuluStats'
            };
            Object.keys(ids).forEach(k => {
                if (st[k]) {
                    document.getElementById(ids[k]).textContent = `${st[k].count} منتج • خصومات لحد ${st[k].max_discount}%`;
                }
            });
            const sdg = st.sharafdg_bh || st.sharaf_bh;
            if (sdg) {
                document.getElementById('storeSharafdgStats').textContent = `${sdg.count} منتج • خصومات لحد ${sdg.max_discount}%`;
            }
        });
    </script>
    """
    return render_layout("المتاجر", "stores", body, script, user=user)


@app.get("/wishlist", response_class=HTMLResponse)
def page_wishlist(request: Request):
    user = get_current_user(request)
    if not user or not user.get("id"):
        return HTMLResponse('<script>window.location.href="/login/google?next=%2Fwishlist";</script>')

    conn = get_db()
    cur = conn.cursor()
    saved_items = []
    try:
        cur.execute(
            _sql(conn, "SELECT deal_key, title, price, url FROM saved_deals WHERE user_id = ? ORDER BY created_at DESC"),
            (int(user["id"]),),
        )
        saved_items = [_row_to_dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

    if not saved_items:
        cards_html = '<p style="color:var(--text-secondary);">ما حفظت أي منتج في المفضلة بعد.</p>'
    else:
        parts = []
        for it in saved_items:
            d_key = html.escape(str(it.get("deal_key") or ""))
            d_title = html.escape(str(it.get("title") or "منتج محفوظ"))
            d_price = html.escape(str(it.get("price") or ""))
            d_url = html.escape(apply_affiliate(str(it.get("url") or "#")))
            parts.append(f"""
                <article class="deal-card">
                    <div class="deal-body">
                        <div class="deal-cat">⭐ محفوظ في مفضلتك</div>
                        <h3 class="deal-title">{d_title}</h3>
                        <div class="price-row"><span class="price-now">{d_price}</span></div>
                        <div class="card-actions" style="grid-template-columns: 1fr auto;">
                            <a href="{d_url}" target="_blank" rel="noopener" class="btn-buy">روح للعرض ↗</a>
                            <button type="button" class="btn-hist btn-save saved" onclick="removeSavedItem(this, '{d_key}')">إزالة</button>
                        </div>
                    </div>
                </article>
            """)
        cards_html = "".join(parts)

    body = f"""
    <div class="sec-head">
        <div>
            <h1 class="sec-title">⭐ المفضلة</h1>
            <div class="sec-sub">المنتجات اللي حفظتها للمتابعة</div>
        </div>
        <a href="/deals" class="btn-outline">رجوع للعروض ←</a>
    </div>
    <div class="products-grid" id="wishlistGrid">{cards_html}</div>
    """
    script = """
    <script>
        async function removeSavedItem(btn, dealKey) {
            const res = await fetch('/api/wishlist/toggle', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ deal_key: dealKey })
            });
            const data = await res.json();
            if (data.ok && !data.saved) {
                const card = btn.closest('.deal-card');
                if (card) card.remove();
            }
        }
    </script>
    """
    return render_layout("المفضلة", "deals", body, script, user=user)


@app.get("/coupons", response_class=HTMLResponse)
def page_coupons(request: Request):
    user = get_current_user(request)
    body = f"""
    <section class="hero-box" style="grid-template-columns:1fr; padding:26px 28px;">
        <div>
            <div class="hero-badge">🎟️ كوبونات البحرين</div>
            <h1 class="hero-title" style="font-size:1.75rem;">أكواد خصم إضافية</h1>
            <p class="hero-desc" style="margin-bottom:0;">
                دوس على الكود بيننسخ على طول، وحطه في خانة الكوبون وقت الدفع في المتجر.
            </p>
        </div>
    </section>

    <div class="products-grid" style="margin-bottom:28px;">
        <div class="coupon-card">
            <div style="display:flex; align-items:center; justify-content:space-between;">
                <div style="display:flex; align-items:center; gap:10px;">
                    <div style="width:42px; height:42px; border-radius:12px; background:#FACC15; color:#111; font-weight:900; display:flex; align-items:center; justify-content:center;">noon</div>
                    <div>
                        <div style="font-weight:800;">كوبون نون البحرين</div>
                        <div style="font-size:0.78rem; color:var(--text-secondary);">كود قابل للتحديث</div>
                    </div>
                </div>
                <span class="tag-pill">شغال</span>
            </div>
            <p style="font-size:0.86rem; color:var(--text-secondary);">
                خصم إضافي على طلبك من نون البحرين (مثال: M22).
            </p>
            <div class="coupon-code-box" onclick="copyCoupon('M22', this)">
                <span>M22</span>
                <span style="font-size:0.82rem;">📋 دوس للنسخ</span>
            </div>
            <a href="https://www.noon.com/bahrain-ar/" target="_blank" rel="noopener" class="btn-outline" style="text-align:center;">روح لموقع نون البحرين ↗</a>
        </div>
    </div>

    <div style="background:linear-gradient(135deg, #0088cc, #0284c7); color:#fff; border-radius:20px; padding:24px; display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:16px;">
        <div>
            <h3 style="font-size:1.2rem; font-weight:900; margin-bottom:4px;">✈️ دش قناة صيدة على تيليجرام — لا يفوتك!</h3>
            <p style="font-size:0.9rem; opacity:0.92;">أي صيدة قوية أو كود يديد ينزل على القناة أول بأول قبل لا يخلص.</p>
        </div>
        <a href="{TELEGRAM_CHANNEL_URL}" target="_blank" rel="noopener" style="background:#fff; color:#0284c7; padding:10px 20px; border-radius:12px; font-weight:900;">دش القناة الحين ↗</a>
    </div>
    """
    script = """
    <script>
        function copyCoupon(code, el) {
            navigator.clipboard.writeText(code);
            const label = el.querySelector('span:last-child');
            const orig = label.textContent;
            label.textContent = '✅ اننسخ!';
            setTimeout(() => { label.textContent = orig; }, 1800);
        }
    </script>
    """
    return render_layout("كوبونات الخصم", "coupons", body, script, user=user)


@app.get("/login", response_class=HTMLResponse)
def page_login(request: Request, error: str = ""):
    user = get_current_user(request)
    err_msg = "الدخول بقوقل مو مفعّل الحين." if error == "google_not_configured" else error
    err_html = (
        f'<div style="background:rgba(239,68,68,0.14);border:1px solid #EF4444;color:#FCA5A5;padding:10px 12px;border-radius:10px;margin-bottom:14px;font-size:0.85rem;font-weight:700;">{html.escape(err_msg)}</div>'
        if err_msg
        else ""
    )
    body = f"""
    <div class="auth-wrap">
        <h1 style="font-size:1.5rem; font-weight:900; margin-bottom:6px; text-align:center;">يا هلا بيك 👋</h1>
        <p style="font-size:0.86rem; color:var(--text-secondary); text-align:center; margin-bottom:20px;">
            سجّل دخولك عشان تتابع مفضلتك وتنبيهاتك في صيدة
        </p>
        {err_html}
        <a href="/login/google" class="btn-primary" style="width:100%; justify-content:center; padding:12px; font-size:0.95rem; margin-bottom:16px;">دخول سريع بقوقل</a>
        <form action="/auth/login" method="post">
            <div class="form-group">
                <label>الإيميل</label>
                <input type="email" name="email" required placeholder="name@example.com" />
            </div>
            <div class="form-group">
                <label>كلمة المرور</label>
                <input type="password" name="password" required placeholder="••••••••" />
            </div>
            <button type="submit" class="btn-outline" style="width:100%; padding:11px; font-size:0.92rem; cursor:pointer;">دخول</button>
        </form>
        <p style="text-align:center; margin-top:16px; font-size:0.85rem; color:var(--text-secondary);">
            ما عندك حساب؟ <a href="/register" style="color:var(--bh-red-bright); font-weight:800;">سوّلك حساب يديد</a>
        </p>
    </div>
    """
    return render_layout("تسجيل الدخول", "login", body, user=user)


@app.get("/register", response_class=HTMLResponse)
def page_register(request: Request, error: str = ""):
    user = get_current_user(request)
    err_html = (
        f'<div style="background:rgba(239,68,68,0.14);border:1px solid #EF4444;color:#FCA5A5;padding:10px 12px;border-radius:10px;margin-bottom:14px;font-size:0.85rem;font-weight:700;">{html.escape(error)}</div>'
        if error
        else ""
    )
    body = f"""
    <div class="auth-wrap">
        <h1 style="font-size:1.5rem; font-weight:900; margin-bottom:6px; text-align:center;">سوّلك حساب ببلاش 🎯</h1>
        <p style="font-size:0.86rem; color:var(--text-secondary); text-align:center; margin-bottom:20px;">
            احفظ المنتجات اللي تهمك وتابع تاريخ أسعارها في البحرين
        </p>
        {err_html}
        <a href="/login/google" class="btn-primary" style="width:100%; justify-content:center; padding:12px; font-size:0.95rem; margin-bottom:16px;">كمل بقوقل</a>
        <form action="/auth/register" method="post">
            <div class="form-group">
                <label>الاسم</label>
                <input type="text" name="name" required placeholder="مثال: علي" />
            </div>
            <div class="form-group">
                <label>الإيميل</label>
                <input type="email" name="email" required placeholder="name@example.com" />
            </div>
            <div class="form-group">
                <label>كلمة المرور</label>
                <input type="password" name="password" required minlength="6" placeholder="6 أحرف على الأقل" />
            </div>
            <button type="submit" class="btn-outline" style="width:100%; padding:11px; font-size:0.92rem; cursor:pointer;">افتح الحساب</button>
        </form>
        <p style="text-align:center; margin-top:16px; font-size:0.85rem; color:var(--text-secondary);">
            عندك حساب من قبل؟ <a href="/login" style="color:var(--bh-red-bright); font-weight:800;">دش من هني</a>
        </p>
    </div>
    """
    return render_layout("حساب يديد", "register", body, user=user)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
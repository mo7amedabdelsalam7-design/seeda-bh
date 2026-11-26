import html
import os
import struct
import time
import zlib
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
STATIC_DIR.mkdir(parents=True, exist_ok=True)
MICROLESS_IMAGES_DIR = STATIC_DIR / "images" / "microless"
MICROLESS_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
AIVI_IMAGE_PATH = STATIC_DIR / "aivi_bh.png"
SOKO_IMAGE_PATH = STATIC_DIR / "soko_bh.png"
TALABAT_MART_IMAGE_PATH = STATIC_DIR / "talabat_mart_bh.png"
FLORMAR_IMAGE_PATH = STATIC_DIR / "flormar_bh.png"
NINJA_IMAGE_PATH = STATIC_DIR / "ninja_bh.png"
ASQ_IMAGE_PATH = STATIC_DIR / "asq_bh.png"
ALMAJED_IMAGE_PATH = STATIC_DIR / "almajed4oud_bh.png"
BBW_IMAGE_PATH = STATIC_DIR / "bbw_bh.png"
MINISO_IMAGE_PATH = STATIC_DIR / "miniso_bh.png"

AFFILIATE_PARAM = "utm_source"
AFFILIATE_CODE = ""
TELEGRAM_CHANNEL_URL = "https://t.me/+FN5Lg1E3z0MyYWY0"
ALLOWED_PROXY_HOSTS = {
    "cdn.microless.com",
    "bahrain.microless.com",
    "www.bahrain.microless.com",
    "bahrain.alershadonline.com",
    "www.bahrain.alershadonline.com",
    "bh.alnasser.net",
    "www.bh.alnasser.net",
    "randbfashion.com",
    "www.randbfashion.com",
    "cdn.shopify.com",
    "albayanperfumes.com",
    "www.albayanperfumes.com",
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
    "baraka-sports.com",
    "www.baraka-sports.com",
    "namshi.com",
    "www.namshi.com",
    "nooncdn.com",
    "aivi.com",
    "www.aivi.com",
    "ar-bh.aivi.com",
    "en-bh.aivi.com",
    "sokostore.com",
    "www.sokostore.com",
    "talabat.com",
    "www.talabat.com",
    "talabat.dhmedia.io",
    "flormarbh.com",
    "www.flormarbh.com",
    "ananinja.com",
    "www.ananinja.com",
    "img.ananinja.com",
    "abdulsamadalqurashi.com",
    "www.abdulsamadalqurashi.com",
    "bh.abdulsamadalqurashi.com",
    "bh.almajed4oud.com",
    "almajed4oud.com",
    "www.almajed4oud.com",
    "cdn.salla.sa",
    "media.salla.sa",
    "bathandbodyworks.com.bh",
    "www.bathandbodyworks.com.bh",
    "media.alshaya.com",
    "miniso-bh.com",
    "www.miniso-bh.com",
}

STORE_META = {
    "noon_bh": {"label": "نون البحرين", "badge": "noon", "decimals": 2, "logo": "/static/noon_bh.png", "accent": "#FACC15", "text_dark": True},
    "namshi_bh": {"label": "نمشي البحرين", "badge": "Namshi", "decimals": 2, "logo": "/static/namshi_bh.png", "accent": "#111827", "text_dark": False},
    "extra_bh": {"label": "إكسترا البحرين", "badge": "eXtra", "decimals": 3, "logo": "/static/extra_bh.png", "accent": "#1D4ED8", "text_dark": False},
    "microless_bh": {"label": "ميكروليس البحرين", "badge": "Microless", "decimals": 3, "logo": "/static/microless_bh.png", "accent": "#EA580C", "text_dark": False},
    "alershad_bh": {"label": "الإرشاد البحرين", "badge": "AlErshad", "decimals": 3, "logo": "/static/alershad_bh.png", "accent": "#92400E", "text_dark": False},
    "alnasser_bh": {"label": "النصر البحرين", "badge": "AlNasser", "decimals": 3, "logo": "/static/alnasser_bh.png", "accent": "#B91C1C", "text_dark": False},
    "randb_bh": {"label": "آر أند بي البحرين", "badge": "R&B", "decimals": 3, "logo": "/static/randb_bh.png", "accent": "#111827", "text_dark": False},
    "max_bh": {"label": "ماكس البحرين", "badge": "MAX", "decimals": 3, "logo": "/static/max_bh.png", "accent": "#DC2626", "text_dark": False},
    "splash_bh": {"label": "سبلاش البحرين", "badge": "Splash", "decimals": 3, "logo": "/static/splash_bh.png", "accent": "#E11D48", "text_dark": False},
    "ramez_bh": {"label": "رامز البحرين", "badge": "Ramez", "decimals": 3, "logo": "/static/ramez_bh.png", "accent": "#B91C1C", "text_dark": False},
    "hypermax_bh": {"label": "هايبرماكس البحرين", "badge": "HyperMax", "decimals": 3, "logo": "/static/hypermax_bh.png", "accent": "#DC2626", "text_dark": False},
    "zain_bh": {"label": "زين البحرين", "badge": "zain", "decimals": 3, "logo": "/static/zain_bh.png", "accent": "#7E22CE", "text_dark": False},
    "stc_bh": {"label": "stc البحرين", "badge": "stc", "decimals": 3, "logo": "/static/stc_bh.png", "accent": "#4F008C", "text_dark": False},
    "batelco_bh": {"label": "باتلكو البحرين", "badge": "Batelco", "decimals": 3, "logo": "/static/batelco_bh.png", "accent": "#E11D48", "text_dark": False},
    "virgin_bh": {"label": "فيرجن ميجاستور البحرين", "badge": "Virgin", "decimals": 2, "logo": "/static/virgin_bh.png", "accent": "#B91C1C", "text_dark": False},
    "jarir_bh": {"label": "مكتبة جرير البحرين", "badge": "جرير", "decimals": 2, "logo": "/static/jarir_bh.png", "accent": "#DC2626", "text_dark": False},
    "sharafdg_bh": {"label": "شرف DG البحرين", "badge": "SDG", "decimals": 3, "logo": "/static/sharafdg_bh.png", "accent": "#D97706", "text_dark": False},
    "sharaf_bh": {"label": "شرف DG البحرين", "badge": "SDG", "decimals": 3, "logo": "/static/sharafdg_bh.png", "accent": "#D97706", "text_dark": False},
    "ourshopee_bh": {"label": "أور شوبي البحرين", "badge": "OurShopee", "decimals": 2, "logo": "/static/ourshopee_bh.png", "accent": "#6D28D9", "text_dark": False},
    "advancedpc_bh": {"label": "أدفانسد بي سي البحرين", "badge": "AdvPC", "decimals": 3, "logo": "/static/advancedpc_bh.png", "accent": "#1E40AF", "text_dark": False},
    "lulu_bh": {"label": "لولو هايبرماركت البحرين", "badge": "LuLu", "decimals": 3, "logo": "/static/lulu_bh.png", "accent": "#15803D", "text_dark": False},
    "ansar_bh": {"label": "أنصار جاليري البحرين", "badge": "Ansar", "decimals": 3, "logo": "/static/ansar_bh.png", "accent": "#DB2777", "text_dark": False},
    "baraka_bh": {"label": "البركة للرياضة البحرين", "badge": "Baraka", "decimals": 3, "logo": "/static/albaraka_bh.png", "accent": "#0F766E", "text_dark": False},
    "albayan_bh": {"label": "البيان البحرين", "badge": "AlBayan", "decimals": 3, "logo": "/static/Albayan_bh.png", "accent": "#991B1B", "text_dark": False},
    "ishop_bh": {"label": "آي شوب البحرين", "badge": "iShop", "decimals": 3, "logo": "/static/ishop_bh.png", "accent": "#0F172A", "text_dark": False},
    "aivi_bh": {"label": "أيفي البحرين", "badge": "AIVI", "decimals": 3, "logo": "/static/aivi_bh.png", "accent": "#111827", "text_dark": False},
    "soko_bh": {"label": "سوكو البحرين", "badge": "SOKO", "decimals": 3, "logo": "/static/soko_bh.png", "accent": "#2563EB", "text_dark": False},
    "talabat_mart_bh": {"label": "طلبات مارت البحرين", "badge": "Mart", "decimals": 3, "logo": "/static/talabat_mart_bh.png", "accent": "#FF5A00", "text_dark": False},
    "flormar_bh": {"label": "فلورمار البحرين", "badge": "Flormar", "decimals": 3, "logo": "/static/flormar_bh.png", "accent": "#E11D48", "text_dark": False},
    "ninja_bh": {"label": "نينجا البحرين", "badge": "Ninja", "decimals": 3, "logo": "/static/ninja_bh.png", "accent": "#7C3AED", "text_dark": False},
    "asq_bh": {"label": "عبد الصمد القرشي البحرين", "badge": "ASQ", "decimals": 3, "logo": "/static/asq_bh.png", "accent": "#78350F", "text_dark": False},
    "almajed4oud_bh": {"label": "الماجد للعود البحرين", "badge": "Almajed", "decimals": 3, "logo": "/static/almajed4oud_bh.png", "accent": "#7C2D12", "text_dark": False},
    "bbw_bh": {"label": "باث آند بودي وركس البحرين", "badge": "BBW", "decimals": 3, "logo": "/static/bbw_bh.png", "accent": "#1D4ED8", "text_dark": False},
    "miniso_bh": {"label": "مينيسو البحرين", "badge": "MINISO", "decimals": 3, "logo": "/static/miniso_bh.png", "accent": "#E11D2E", "text_dark": False},
}


def _create_png_bytes(width: int = 128, height: int = 128, bg_rgb: tuple[int, int, int] = (17, 24, 39), accent_rgb: tuple[int, int, int] = (255, 42, 68)) -> bytes:
    def chunk(tag: bytes, data: bytes) -> bytes:
        crc = zlib.crc32(tag + data) & 0xFFFFFFFF
        return struct.pack("!I", len(data)) + tag + data + struct.pack("!I", crc)

    raw_rows = bytearray()
    cx, cy = width / 2.0, height / 2.0
    max_r = min(width, height) * 0.34
    for y in range(height):
        raw_rows.append(0)
        for x in range(width):
            dx = x - cx
            dy = y - cy
            dist = (dx * dx + dy * dy) ** 0.5
            if dist <= max_r:
                r, g, b = accent_rgb
            else:
                r, g, b = bg_rgb
            raw_rows.extend((r, g, b))

    ihdr = struct.pack("!IIBBBBB", width, height, 8, 2, 0, 0, 0)
    idat = zlib.compress(bytes(raw_rows), level=6)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")


def ensure_aivi_bh_image() -> None:
    try:
        if AIVI_IMAGE_PATH.exists() and AIVI_IMAGE_PATH.stat().st_size > 100:
            return
        AIVI_IMAGE_PATH.write_bytes(_create_png_bytes(128, 128, (17, 24, 39), (225, 29, 72)))
    except Exception:
        pass


def ensure_soko_bh_image() -> None:
    try:
        if SOKO_IMAGE_PATH.exists() and SOKO_IMAGE_PATH.stat().st_size > 100:
            return
        SOKO_IMAGE_PATH.write_bytes(_create_png_bytes(128, 128, (15, 23, 42), (56, 189, 248)))
    except Exception:
        pass


def ensure_talabat_mart_bh_image() -> None:
    try:
        if TALABAT_MART_IMAGE_PATH.exists() and TALABAT_MART_IMAGE_PATH.stat().st_size > 100:
            return
        TALABAT_MART_IMAGE_PATH.write_bytes(_create_png_bytes(128, 128, (24, 24, 27), (255, 90, 0)))
    except Exception:
        pass


def ensure_flormar_bh_image() -> None:
    try:
        if FLORMAR_IMAGE_PATH.exists() and FLORMAR_IMAGE_PATH.stat().st_size > 100:
            return
        FLORMAR_IMAGE_PATH.write_bytes(_create_png_bytes(128, 128, (31, 16, 26), (225, 29, 72)))
    except Exception:
        pass


def ensure_ninja_bh_image() -> None:
    try:
        if NINJA_IMAGE_PATH.exists() and NINJA_IMAGE_PATH.stat().st_size > 100:
            return
        NINJA_IMAGE_PATH.write_bytes(_create_png_bytes(128, 128, (18, 16, 36), (124, 58, 237)))
    except Exception:
        pass


def ensure_asq_bh_image() -> None:
    try:
        if ASQ_IMAGE_PATH.exists() and ASQ_IMAGE_PATH.stat().st_size > 100:
            return
        ASQ_IMAGE_PATH.write_bytes(_create_png_bytes(128, 128, (38, 22, 12), (217, 119, 6)))
    except Exception:
        pass


def ensure_almajed4oud_bh_image() -> None:
    try:
        if ALMAJED_IMAGE_PATH.exists() and ALMAJED_IMAGE_PATH.stat().st_size > 100:
            return
        ALMAJED_IMAGE_PATH.write_bytes(_create_png_bytes(128, 128, (42, 18, 10), (180, 83, 9)))
    except Exception:
        pass


def ensure_bbw_bh_image() -> None:
    try:
        if BBW_IMAGE_PATH.exists() and BBW_IMAGE_PATH.stat().st_size > 100:
            return
        BBW_IMAGE_PATH.write_bytes(_create_png_bytes(128, 128, (29, 78, 216), (255, 255, 255)))
    except Exception:
        pass


def ensure_miniso_bh_image() -> None:
    try:
        if MINISO_IMAGE_PATH.exists() and MINISO_IMAGE_PATH.stat().st_size > 100:
            return
        MINISO_IMAGE_PATH.write_bytes(_create_png_bytes(128, 128, (225, 29, 46), (255, 255, 255)))
    except Exception:
        pass


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
    ensure_aivi_bh_image()
    ensure_soko_bh_image()
    ensure_talabat_mart_bh_image()
    ensure_flormar_bh_image()
    ensure_ninja_bh_image()
    ensure_asq_bh_image()
    ensure_almajed4oud_bh_image()
    ensure_bbw_bh_image()
    ensure_miniso_bh_image()
    ensure_db_ready()
    yield


app = FastAPI(title="صيدة — لقطات وخصومات البحرين", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
setup_google_auth(app)
app.router.routes = [r for r in app.router.routes if getattr(r, "path", None) != "/wishlist"]


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
        cur.execute(_sql(conn, "SELECT deal_key FROM saved_deals WHERE user_id = ?"), (int(user_id),))
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
    if store_str == "microless_bh":
        if sku_str:
            safe_sku = "".join(ch for ch in sku_str if ch.isalnum() or ch in {"_", "-"})
            if safe_sku:
                for ext in (".jpg", ".jpeg", ".png", ".webp"):
                    img_file = MICROLESS_IMAGES_DIR / f"{safe_sku}{ext}"
                    if img_file.exists() and img_file.stat().st_size > 500:
                        return f"/static/images/microless/{safe_sku}{ext}"
        if (STATIC_DIR / "microless_bh.png").exists():
            return "/static/microless_bh.png"
    elif store_str == "aivi_bh":
        ensure_aivi_bh_image()
        if AIVI_IMAGE_PATH.exists():
            return "/static/aivi_bh.png"
    elif store_str == "soko_bh":
        ensure_soko_bh_image()
        if SOKO_IMAGE_PATH.exists():
            return "/static/soko_bh.png"
    elif store_str == "talabat_mart_bh":
        ensure_talabat_mart_bh_image()
        if TALABAT_MART_IMAGE_PATH.exists():
            return "/static/talabat_mart_bh.png"
    elif store_str == "flormar_bh":
        ensure_flormar_bh_image()
        if FLORMAR_IMAGE_PATH.exists():
            return "/static/flormar_bh.png"
    elif store_str == "ninja_bh":
        ensure_ninja_bh_image()
        if NINJA_IMAGE_PATH.exists():
            return "/static/ninja_bh.png"
    elif store_str == "asq_bh":
        ensure_asq_bh_image()
        if ASQ_IMAGE_PATH.exists():
            return "/static/asq_bh.png"
    elif store_str == "almajed4oud_bh":
        ensure_almajed4oud_bh_image()
        if ALMAJED_IMAGE_PATH.exists():
            return "/static/almajed4oud_bh.png"
    elif store_str == "bbw_bh":
        ensure_bbw_bh_image()
        if BBW_IMAGE_PATH.exists():
            return "/static/bbw_bh.png"
    elif store_str == "miniso_bh":
        ensure_miniso_bh_image()
        if MINISO_IMAGE_PATH.exists():
            return "/static/miniso_bh.png"
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
        and not host.endswith(".alnasser.net")
        and not host.endswith(".randbfashion.com")
        and not host.endswith(".shopify.com")
        and not host.endswith(".albayanperfumes.com")
        and not host.endswith(".akinoncloudcdn.com")
        and not host.endswith(".ramezshopping.com")
        and not host.endswith(".hypermax.com.bh")
        and not host.endswith(".mafrservices.com")
        and not host.endswith(".mafretailproxy.com")
        and not host.endswith(".amazonaws.com")
        and not host.endswith(".ansargallery.bh")
        and not host.endswith(".baraka-sports.com")
        and not host.endswith(".namshi.com")
        and not host.endswith(".nooncdn.com")
        and not host.endswith(".aivi.com")
        and not host.endswith(".sokostore.com")
        and not host.endswith(".talabat.com")
        and not host.endswith(".dhmedia.io")
        and not host.endswith(".flormarbh.com")
        and not host.endswith(".ananinja.com")
        and not host.endswith(".abdulsamadalqurashi.com")
        and not host.endswith(".almajed4oud.com")
        and not host.endswith(".salla.sa")
        and not host.endswith(".bathandbodyworks.com.bh")
        and not host.endswith(".alshaya.com")
        and not host.endswith(".miniso-bh.com")
    ):
        return Response(status_code=403)

    if "microless.com" in host:
        referer = "https://bahrain.microless.com/"
    elif "alershadonline.com" in host:
        referer = "https://bahrain.alershadonline.com/"
    elif "alnasser.net" in host:
        referer = "https://bh.alnasser.net/"
    elif "randbfashion.com" in host:
        referer = "https://randbfashion.com/"
    elif "albayanperfumes.com" in host:
        referer = "https://albayanperfumes.com/"
    elif "ansargallery.bh" in host:
        referer = "https://www.ansargallery.bh/"
    elif "baraka-sports.com" in host:
        referer = "https://baraka-sports.com/"
    elif "hypermax.com.bh" in host or "mafrservices.com" in host or "mafretailproxy.com" in host:
        referer = "https://www.hypermax.com.bh/"
    elif "ramezshopping.com" in host or "amazonaws.com" in host:
        referer = "https://ramezshopping.com/"
    elif "akinoncloudcdn.com" in host or "luluhypermarket.com" in host:
        referer = "https://gcc.luluhypermarket.com/"
    elif "namshi.com" in host or "nooncdn.com" in host:
        referer = "https://www.namshi.com/"
    elif "aivi.com" in host:
        referer = "https://ar-bh.aivi.com/"
    elif "sokostore.com" in host:
        referer = "https://sokostore.com/"
    elif "talabat.com" in host or "dhmedia.io" in host:
        referer = "https://www.talabat.com/"
    elif "flormarbh.com" in host or "shopify.com" in host:
        referer = "https://flormarbh.com/"
    elif "ananinja.com" in host:
        referer = "https://ananinja.com/bh/ar"
    elif "almajed4oud.com" in host:
        referer = "https://bh.almajed4oud.com/"
    elif "abdulsamadalqurashi.com" in host or "salla.sa" in host:
        referer = "https://bh.abdulsamadalqurashi.com/"
    elif "bathandbodyworks.com.bh" in host or "alshaya.com" in host:
        referer = "https://www.bathandbodyworks.com.bh/"
    elif "miniso-bh.com" in host:
        referer = "https://miniso-bh.com/"
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


def _store_where_clause(store: str) -> tuple[str, list[Any]]:
    st_clean = (store or "").strip().lower()
    if not st_clean:
        return "", []
    if st_clean == "sharafdg_bh":
        return " AND LOWER(TRIM(COALESCE(store, ''))) IN ('sharafdg_bh', 'sharaf_bh')", []
    return " AND LOWER(TRIM(COALESCE(store, ''))) = ?", [st_clean]


@app.get("/api/summary")
def api_summary(store: str = ""):
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
        st_key = (r.get("store") or "noon_bh").strip()
        stores_stats[st_key] = {
            "count": int(r.get("cnt") or 0),
            "max_discount": round(float(r.get("max_disc") or 0), 1),
        }

    st_clause, st_params = _store_where_clause(store)
    cur.execute(
        _sql(conn, f"""
            SELECT category, COUNT(*) AS cnt, COALESCE(MAX(discount_pct), 0) AS max_disc
            FROM products
            WHERE in_stock = 1 AND category IS NOT NULL AND category != ''{st_clause}
            GROUP BY category
            ORDER BY cnt DESC
        """),
        st_params,
    )
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
        st_clean = store.strip().lower()
        if st_clean == "sharafdg_bh":
            where.append("LOWER(TRIM(COALESCE(store, ''))) IN ('sharafdg_bh', 'sharaf_bh')")
        else:
            where.append("LOWER(TRIM(COALESCE(store, ''))) = ?")
            params.append(st_clean)
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
        st_key = (d.get("store") or ("ansar_bh" if str(d.get("sku") or "").startswith("ANSAR_") else "noon_bh")).strip()
        dec = STORE_META.get(st_key, {}).get("decimals", 2)
        d["store"] = st_key
        local_img = resolve_local_product_image(d.get("sku"), st_key)
        if local_img and st_key == "microless_bh":
            d["image_url"] = local_img
        elif st_key == "microless_bh" and (STATIC_DIR / "microless_bh.png").exists():
            d["image_url"] = "/static/microless_bh.png"
        elif st_key == "aivi_bh" and not (d.get("image_url") or "").strip():
            d["image_url"] = "/static/aivi_bh.png"
        elif st_key == "soko_bh" and not (d.get("image_url") or "").strip():
            d["image_url"] = "/static/soko_bh.png"
        elif st_key == "talabat_mart_bh" and not (d.get("image_url") or "").strip():
            d["image_url"] = "/static/talabat_mart_bh.png"
        elif st_key == "flormar_bh" and not (d.get("image_url") or "").strip():
            d["image_url"] = "/static/flormar_bh.png"
        elif st_key == "ninja_bh" and not (d.get("image_url") or "").strip():
            d["image_url"] = "/static/ninja_bh.png"
        elif st_key == "asq_bh" and not (d.get("image_url") or "").strip():
            d["image_url"] = "/static/asq_bh.png"
        elif st_key == "almajed4oud_bh" and not (d.get("image_url") or "").strip():
            d["image_url"] = "/static/almajed4oud_bh.png"
        elif st_key == "bbw_bh" and not (d.get("image_url") or "").strip():
            d["image_url"] = "/static/bbw_bh.png"
        elif st_key == "miniso_bh" and not (d.get("image_url") or "").strip():
            d["image_url"] = "/static/miniso_bh.png"
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
        return JSONResponse(status_code=404, content={"error": "هالمنتج مو موجود الحين"})

    prod_dict = _row_to_dict(prod)
    st_key = (prod_dict.get("store") or ("ansar_bh" if str(prod_dict.get("sku") or "").startswith("ANSAR_") else "noon_bh")).strip()
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


@app.get("/api/wishlist")
def api_wishlist_list(request: Request):
    user = get_current_user(request)
    if not user or not user.get("id"):
        return JSONResponse(status_code=401, content={"ok": False, "error": "unauthorized", "items": []})

    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute(
            _sql(conn, "SELECT deal_key, title, price, url, created_at FROM saved_deals WHERE user_id = ? ORDER BY created_at DESC"),
            (int(user["id"]),),
        )
        items = []
        for raw_r in cur.fetchall():
            r = _row_to_dict(raw_r)
            r["url"] = apply_affiliate(str(r.get("url") or ""))
            r["saved_ago"] = format_time_ago(r.get("created_at"))
            items.append(r)
        return {"ok": True, "count": len(items), "items": items}
    finally:
        conn.close()


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
            <svg viewBox="0 0 64 64" width="46" height="46">
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
            --bh-red-bright: #FF2A44;
            --bh-red-soft: rgba(255, 42, 68, 0.16);
            --bh-gold: #F59E0B;
            --bh-green: #10B981;
            --bh-cyan: #38BDF8;
            --radius-xl: 24px;
            --radius-lg: 18px;
            --radius-md: 12px;
            --transition: all 0.25s cubic-bezier(0.22, 1, 0.36, 1);
        }}

        html[data-theme="dark"] {{
            --bg-main: #070A10;
            --bg-surface: #0F1522;
            --bg-card: #151D2E;
            --bg-card-hover: #1D2840;
            --bg-input: #0A0E17;
            --border-color: rgba(255, 255, 255, 0.09);
            --border-strong: rgba(255, 42, 68, 0.45);
            --text-primary: #F8FAFC;
            --text-secondary: #94A3B8;
            --text-muted: #64748B;
            --shadow-card: 0 16px 38px rgba(0, 0, 0, 0.46);
            --header-bg: rgba(10, 14, 23, 0.88);
        }}

        html[data-theme="light"] {{
            --bg-main: #F3F6FB;
            --bg-surface: #FFFFFF;
            --bg-card: #FFFFFF;
            --bg-card-hover: #FFF6F7;
            --bg-input: #EDF2F8;
            --border-color: rgba(15, 23, 42, 0.09);
            --border-strong: rgba(206, 17, 38, 0.38);
            --text-primary: #0F172A;
            --text-secondary: #475569;
            --text-muted: #64748B;
            --shadow-card: 0 14px 32px rgba(15, 23, 42, 0.08);
            --header-bg: rgba(255, 255, 255, 0.9);
        }}

        @keyframes pulseGlow {{
            0%, 100% {{ transform: scale(1); box-shadow: 0 0 0 0 rgba(255, 42, 68, 0.5); }}
            50% {{ transform: scale(1.16); box-shadow: 0 0 0 7px rgba(255, 42, 68, 0); }}
        }}

        @keyframes floatSoft {{
            0%, 100% {{ transform: translateY(0px); }}
            50% {{ transform: translateY(-5px); }}
        }}

        @keyframes seedaOrbDance {{
            0% {{ transform: translateY(0px) rotate(0deg) scale(1); box-shadow: 0 0 0 0 rgba(255, 42, 68, 0.45), 0 12px 28px rgba(255, 42, 68, 0.36); }}
            25% {{ transform: translateY(-8px) rotate(8deg) scale(1.05); }}
            50% {{ transform: translateY(0px) rotate(0deg) scale(1.09); box-shadow: 0 0 0 12px rgba(245, 158, 11, 0), 0 16px 32px rgba(255, 42, 68, 0.52); }}
            75% {{ transform: translateY(-7px) rotate(-8deg) scale(1.05); }}
            100% {{ transform: translateY(0px) rotate(0deg) scale(1); box-shadow: 0 0 0 0 rgba(255, 42, 68, 0), 0 12px 28px rgba(255, 42, 68, 0.36); }}
        }}

        @keyframes seedaOrbSpinRing {{
            from {{ transform: rotate(0deg); }}
            to {{ transform: rotate(360deg); }}
        }}

        @keyframes fadeUp {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Cairo', sans-serif;
        }}

        body {{
            background:
                radial-gradient(circle at 10% 6%, rgba(255, 42, 68, 0.13), transparent 36%),
                radial-gradient(circle at 90% 14%, rgba(56, 189, 248, 0.10), transparent 36%),
                radial-gradient(circle at 50% 85%, rgba(245, 158, 11, 0.06), transparent 40%),
                var(--bg-main);
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
            max-width: 1380px;
            margin: 0 auto;
            padding: 0 20px;
        }}

        .navbar {{
            position: sticky;
            top: 0;
            z-index: 60;
            backdrop-filter: blur(18px);
            background: var(--header-bg);
            border-bottom: 1px solid var(--border-color);
            box-shadow: 0 6px 24px rgba(0, 0, 0, 0.14);
        }}

        .navbar-inner {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 14px;
            min-height: 76px;
            flex-wrap: wrap;
            padding: 10px 0;
        }}

        .brand-link {{
            display: flex;
            align-items: center;
            gap: 12px;
            flex-shrink: 0;
            transition: var(--transition);
        }}

        .brand-link:hover {{
            transform: translateY(-1px) scale(1.03);
        }}

        .brand-logo-img {{
            height: 50px;
            width: auto;
            max-width: 150px;
            border-radius: 13px;
            object-fit: contain;
            filter: drop-shadow(0 6px 14px rgba(255, 42, 68, 0.28));
            transition: var(--transition);
        }}

        .brand-link:hover .brand-logo-img {{
            transform: scale(1.06) rotate(-2deg);
        }}

        .bahrain-chili-mark {{
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 8px 20px rgba(206, 17, 38, 0.38);
            border-radius: 14px;
        }}

        .brand-text {{
            display: flex;
            flex-direction: column;
            line-height: 1.15;
        }}

        .brand-title {{
            font-size: 1.38rem;
            font-weight: 900;
            letter-spacing: -0.3px;
            display: flex;
            align-items: center;
            gap: 6px;
        }}

        .brand-title span {{
            background: linear-gradient(135deg, #FF2A44, #FF7A45);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .brand-sub {{
            font-size: 0.74rem;
            color: var(--text-secondary);
            font-weight: 600;
        }}

        .seeda-animated-orb {{
            position: relative;
            width: 96px;
            height: 96px;
            border-radius: 50%;
            background: linear-gradient(135deg, rgba(255, 42, 68, 0.24), rgba(245, 158, 11, 0.24));
            border: 3px solid var(--bh-red-bright);
            display: inline-flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            animation: seedaOrbDance 3.2s ease-in-out infinite;
            transition: transform 0.3s cubic-bezier(0.22, 1, 0.36, 1), box-shadow 0.3s ease, border-color 0.3s ease;
            flex-shrink: 0;
        }}

        .seeda-animated-orb::before {{
            content: "";
            position: absolute;
            inset: -8px;
            border-radius: 50%;
            border: 2.5px dashed rgba(255, 42, 68, 0.72);
            animation: seedaOrbSpinRing 6s linear infinite;
            pointer-events: none;
        }}

        .seeda-animated-orb:hover {{
            animation-play-state: paused;
            transform: scale(1.16) rotate(14deg);
            border-color: #FBBF24;
            box-shadow: 0 0 32px rgba(255, 42, 68, 0.78), 0 0 18px rgba(251, 191, 36, 0.6);
        }}

        .seeda-animated-orb:hover::before {{
            animation-duration: 1.5s;
            border-color: #FBBF24;
        }}

        .seeda-orb-img {{
            width: 76px;
            height: 76px;
            border-radius: 50%;
            object-fit: cover;
            display: block;
            transition: transform 0.3s ease;
        }}

        .seeda-orb-svg {{
            width: 72px;
            height: 72px;
            display: block;
        }}

        .seeda-animated-orb:hover .seeda-orb-img {{
            transform: scale(1.06) rotate(-14deg);
        }}

        .nav-search {{
            flex: 1;
            min-width: 220px;
            max-width: 410px;
            position: relative;
        }}

        .nav-search input {{
            width: 100%;
            background: var(--bg-input);
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            padding: 9px 42px 9px 14px;
            border-radius: 999px;
            font-size: 0.88rem;
            outline: none;
            transition: var(--transition);
        }}

        .nav-search input:focus {{
            border-color: var(--bh-red-bright);
            box-shadow: 0 0 0 4px var(--bh-red-soft);
            transform: translateY(-1px);
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
            transition: var(--transition);
        }}

        .nav-search button:hover {{
            transform: translateY(-50%) scale(1.18);
        }}

        .nav-links {{
            display: flex;
            align-items: center;
            gap: 6px;
            flex-wrap: wrap;
        }}

        .nav-link {{
            padding: 7px 13px;
            border-radius: 12px;
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
            transform: translateY(-2px);
        }}

        .nav-link.active {{
            color: #FFFFFF;
            background: linear-gradient(135deg, #CE1126, #FF2A44);
            box-shadow: 0 8px 20px rgba(206, 17, 38, 0.38);
        }}

        .live-dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #FF2A44;
            display: inline-block;
            animation: pulseGlow 1.9s infinite;
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
            border-radius: 11px;
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
            transform: translateY(-2px) rotate(12deg);
        }}

        .btn-outline {{
            padding: 8px 14px;
            border-radius: 12px;
            border: 1px solid var(--border-color);
            background: var(--bg-card);
            color: var(--text-primary);
            font-weight: 700;
            font-size: 0.84rem;
            transition: var(--transition);
            white-space: nowrap;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
        }}

        .btn-outline:hover {{
            border-color: var(--bh-red-bright);
            background: var(--bg-card-hover);
            transform: translateY(-2px);
        }}

        .btn-primary {{
            padding: 8px 15px;
            border-radius: 12px;
            border: none;
            background: linear-gradient(135deg, #CE1126, #FF2A44);
            color: #FFFFFF;
            font-weight: 800;
            font-size: 0.84rem;
            cursor: pointer;
            box-shadow: 0 8px 22px rgba(206, 17, 38, 0.36);
            transition: var(--transition);
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            white-space: nowrap;
        }}

        .btn-primary:hover {{
            transform: translateY(-2px) scale(1.025);
            box-shadow: 0 12px 26px rgba(255, 42, 68, 0.48);
        }}

        main {{
            flex: 1;
            padding: 24px 0 68px;
            animation: fadeUp 0.38s ease;
        }}

        .hero-box {{
            position: relative;
            overflow: visible;
            border-radius: 28px;
            background:
                radial-gradient(circle at 85% 20%, rgba(255, 42, 68, 0.22), transparent 45%),
                linear-gradient(135deg, rgba(255, 42, 68, 0.14) 0%, var(--bg-surface) 52%, rgba(56, 189, 248, 0.09) 100%);
            border: 1px solid var(--border-strong);
            padding: 36px 34px;
            margin-bottom: 38px;
            box-shadow: var(--shadow-card);
            display: grid;
            grid-template-columns: 1.45fr 1fr;
            gap: 28px;
            align-items: center;
            transition: var(--transition);
        }}

        .hero-box:hover {{
            box-shadow: 0 22px 48px rgba(206, 17, 38, 0.22);
            transform: translateY(-2px);
        }}

        .hero-badge {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: var(--bh-red-soft);
            color: var(--bh-red-bright);
            border: 1px solid rgba(255, 42, 68, 0.35);
            padding: 6px 14px;
            border-radius: 999px;
            font-size: 0.82rem;
            font-weight: 800;
            margin-bottom: 14px;
        }}

        .hero-title {{
            font-size: 2.2rem;
            font-weight: 900;
            line-height: 1.25;
            margin-bottom: 12px;
        }}

        .hero-title span {{
            background: linear-gradient(135deg, #FF2A44, #FF8A3D);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .hero-desc {{
            color: var(--text-secondary);
            font-size: 0.98rem;
            line-height: 1.75;
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
            display: grid;
            grid-template-columns: repeat(4, minmax(110px, 1fr));
            gap: 12px;
            padding-top: 18px;
            border-top: 1px solid var(--border-color);
        }}

        .stat-item {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 15px;
            padding: 12px 14px;
            transition: var(--transition);
        }}

        .stat-item:hover {{
            transform: translateY(-3px);
            border-color: var(--bh-red-bright);
        }}

        .stat-item strong {{
            display: block;
            font-size: 1.28rem;
            font-weight: 900;
            color: var(--text-primary);
        }}

        .stat-item span {{
            font-size: 0.76rem;
            color: var(--text-secondary);
        }}

        .hero-showcase {{
            position: relative;
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 22px;
            padding: 22px 20px 20px;
            display: flex;
            flex-direction: column;
            gap: 14px;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.06);
        }}

        .showcase-orb-banner {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 14px;
            background: linear-gradient(135deg, rgba(255, 42, 68, 0.12), rgba(245, 158, 11, 0.08));
            border: 1px solid rgba(255, 42, 68, 0.25);
            border-radius: 18px;
            padding: 14px 16px;
        }}

        .showcase-orb-info {{
            display: flex;
            flex-direction: column;
            gap: 6px;
            align-items: flex-start;
        }}

        .showcase-top {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 10px;
            flex-wrap: wrap;
        }}

        .tag-pill {{
            background: rgba(16, 185, 129, 0.15);
            color: var(--bh-green);
            border: 1px solid rgba(16, 185, 129, 0.3);
            padding: 5px 12px;
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 800;
            white-space: nowrap;
        }}

        .showcase-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: var(--bg-input);
            padding: 12px 14px;
            border-radius: 15px;
            border: 1px solid var(--border-color);
            transition: var(--transition);
        }}

        .showcase-row:hover {{
            transform: translateX(-4px);
            border-color: var(--bh-red-bright);
            background: var(--bg-card-hover);
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
            font-size: 1.38rem;
            font-weight: 900;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .sec-sub {{
            font-size: 0.86rem;
            color: var(--text-secondary);
            margin-top: 2px;
        }}

        .sec-head-actions {{
            display: flex;
            align-items: center;
            gap: 8px;
            flex-wrap: wrap;
        }}

        .strip-wrap {{
            position: relative;
            margin-bottom: 38px;
        }}

        .strip-controls {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }}

        .strip-arrow {{
            width: 36px;
            height: 36px;
            border-radius: 11px;
            border: 1px solid var(--border-color);
            background: var(--bg-card);
            color: var(--text-primary);
            font-weight: 900;
            font-size: 1rem;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            transition: var(--transition);
        }}

        .strip-arrow:hover {{
            border-color: var(--bh-red-bright);
            background: var(--bg-card-hover);
            transform: translateY(-2px) scale(1.06);
        }}

        .stores-strip {{
            display: flex;
            flex-direction: row;
            flex-wrap: nowrap;
            gap: 14px;
            overflow-x: auto;
            overflow-y: hidden;
            scroll-snap-type: x mandatory;
            scroll-behavior: smooth;
            padding: 6px 4px 14px;
            cursor: grab;
            -webkit-overflow-scrolling: touch;
            scrollbar-width: thin;
            scrollbar-color: rgba(255, 42, 68, 0.45) transparent;
        }}

        .stores-strip:active {{
            cursor: grabbing;
        }}

        .stores-strip::-webkit-scrollbar {{
            height: 7px;
        }}

        .stores-strip::-webkit-scrollbar-thumb {{
            background: rgba(255, 42, 68, 0.45);
            border-radius: 999px;
        }}

        .stores-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(210px, 1fr));
            gap: 16px;
            margin-bottom: 32px;
        }}

        .stores-grid .store-card {{
            flex: none;
            min-width: 0;
            width: 100%;
        }}

        .store-card {{
            flex: 0 0 212px;
            min-width: 212px;
            scroll-snap-align: start;
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-lg);
            padding: 18px 14px;
            text-align: center;
            transition: var(--transition);
            position: relative;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            box-shadow: var(--shadow-card);
            user-select: none;
        }}

        .store-card:hover {{
            transform: translateY(-6px) scale(1.025);
            border-color: var(--bh-red-bright);
            background: var(--bg-card-hover);
            box-shadow: 0 18px 34px rgba(255, 42, 68, 0.22);
        }}

        .store-icon-box {{
            width: 66px;
            height: 66px;
            border-radius: 18px;
            margin: 0 auto 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 7px;
            overflow: hidden;
            background: #FFFFFF;
            border: 2px solid rgba(255, 255, 255, 0.14);
            box-shadow: 0 8px 18px rgba(0, 0, 0, 0.25);
            transition: var(--transition);
        }}

        .store-card:hover .store-icon-box {{
            transform: scale(1.08) rotate(-2deg);
        }}

        .store-logo-img {{
            width: 100%;
            height: 100%;
            object-fit: contain;
            display: block;
        }}

        .store-fallback-badge {{
            width: 100%;
            height: 100%;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 900;
            font-size: 0.78rem;
            text-align: center;
            padding: 2px;
        }}

        .store-name {{
            font-weight: 800;
            font-size: 0.98rem;
            margin-bottom: 4px;
            line-height: 1.3;
        }}

        .store-meta {{
            font-size: 0.78rem;
            color: var(--bh-green);
            font-weight: 700;
        }}

        .cats-strip {{
            display: flex;
            flex-direction: row;
            flex-wrap: nowrap;
            gap: 14px;
            overflow-x: auto;
            overflow-y: hidden;
            scroll-snap-type: x mandatory;
            scroll-behavior: smooth;
            padding: 6px 4px 14px;
            cursor: grab;
            -webkit-overflow-scrolling: touch;
            scrollbar-width: thin;
            scrollbar-color: rgba(255, 42, 68, 0.45) transparent;
        }}

        .cats-strip:active {{
            cursor: grabbing;
        }}

        .cats-strip::-webkit-scrollbar {{
            height: 7px;
        }}

        .cats-strip::-webkit-scrollbar-thumb {{
            background: rgba(255, 42, 68, 0.45);
            border-radius: 999px;
        }}

        .categories-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(265px, 1fr));
            gap: 16px;
            margin-bottom: 32px;
        }}

        .categories-grid .cat-card {{
            flex: none;
            min-width: 0;
            width: 100%;
        }}

        .cat-card {{
            flex: 0 0 268px;
            min-width: 268px;
            scroll-snap-align: start;
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-lg);
            padding: 15px 17px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            transition: var(--transition);
            box-shadow: var(--shadow-card);
            user-select: none;
        }}

        .cat-card:hover {{
            border-color: var(--bh-red-bright);
            background: var(--bg-card-hover);
            transform: translateY(-5px) scale(1.02);
            box-shadow: 0 16px 30px rgba(255, 42, 68, 0.2);
        }}

        .cat-badge-icon {{
            width: 46px;
            height: 46px;
            border-radius: 14px;
            background: var(--bh-red-soft);
            color: var(--bh-red-bright);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.25rem;
            flex-shrink: 0;
            transition: var(--transition);
        }}

        .cat-card:hover .cat-badge-icon {{
            transform: scale(1.12) rotate(6deg);
            background: linear-gradient(135deg, #CE1126, #FF2A44);
            color: #FFFFFF;
        }}

        .cat-arrow {{
            font-weight: 900;
            color: var(--bh-red-bright);
            transition: var(--transition);
        }}

        .cat-card:hover .cat-arrow {{
            transform: translateX(-4px);
        }}

        .directory-search-box {{
            position: relative;
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 12px 16px;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
            box-shadow: var(--shadow-card);
            transition: var(--transition);
        }}

        .directory-search-box:focus-within {{
            border-color: var(--bh-red-bright);
            box-shadow: 0 0 0 4px var(--bh-red-soft);
        }}

        .directory-search-box input {{
            flex: 1;
            background: var(--bg-input);
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            padding: 10px 14px;
            border-radius: 12px;
            font-size: 0.92rem;
            outline: none;
        }}

        .directory-search-box input:focus {{
            border-color: var(--bh-red-bright);
        }}

        .products-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(255px, 1fr));
            gap: 18px;
        }}

        .deal-card {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 20px;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            transition: var(--transition);
            box-shadow: var(--shadow-card);
            animation: fadeUp 0.35s ease;
        }}

        .deal-card:hover {{
            transform: translateY(-7px) scale(1.015);
            border-color: var(--bh-red-bright);
            box-shadow: 0 20px 38px rgba(255, 42, 68, 0.2);
        }}

        .deal-thumb {{
            position: relative;
            height: 205px;
            background: #FFFFFF;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 14px;
            overflow: hidden;
        }}

        .deal-thumb img {{
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
            transition: transform 0.35s cubic-bezier(0.22, 1, 0.36, 1);
        }}

        .deal-card:hover .deal-thumb img {{
            transform: scale(1.08);
        }}

        .badges-top-right {{
            position: absolute;
            top: 10px;
            right: 10px;
            display: flex;
            flex-direction: column;
            gap: 5px;
            z-index: 2;
        }}

        .badge-disc {{
            background: linear-gradient(135deg, #CE1126, #FF2A44);
            color: #FFFFFF;
            font-weight: 900;
            font-size: 0.78rem;
            padding: 3px 9px;
            border-radius: 8px;
            box-shadow: 0 4px 10px rgba(206, 17, 38, 0.35);
            width: fit-content;
        }}

        .badge-promo {{
            background: linear-gradient(135deg, #D97706, #F59E0B);
            color: #111827;
            font-weight: 900;
            font-size: 0.74rem;
            padding: 3px 9px;
            border-radius: 8px;
            box-shadow: 0 4px 10px rgba(245, 158, 11, 0.35);
            width: fit-content;
        }}

        .badge-real {{
            background: #10B981;
            color: #FFFFFF;
            font-weight: 800;
            font-size: 0.74rem;
            padding: 3px 9px;
            border-radius: 8px;
            width: fit-content;
        }}

        .badge-store {{
            position: absolute;
            bottom: 10px;
            left: 10px;
            background: rgba(15, 23, 42, 0.88);
            color: #FDE047;
            font-size: 0.72rem;
            font-weight: 800;
            padding: 4px 10px;
            border-radius: 8px;
            z-index: 2;
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
            font-size: 0.94rem;
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
            padding: 8px 10px;
            border-radius: 10px;
            border: 1px solid var(--border-color);
        }}

        .card-actions {{
            display: grid;
            grid-template-columns: 1fr auto auto;
            gap: 6px;
        }}

        .btn-buy {{
            background: linear-gradient(135deg, #CE1126, #FF2A44);
            color: #FFFFFF;
            text-align: center;
            padding: 9px 10px;
            border-radius: 10px;
            font-weight: 800;
            font-size: 0.82rem;
            transition: var(--transition);
        }}

        .btn-buy:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 18px rgba(255, 42, 68, 0.38);
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
            transform: translateY(-2px) scale(1.04);
        }}

        .btn-save.saved {{
            background: rgba(16, 185, 129, 0.18);
            border-color: #10B981;
            color: #10B981;
        }}

        .wishlist-banner {{
            background:
                radial-gradient(circle at 15% 20%, rgba(255, 42, 68, 0.2), transparent 45%),
                linear-gradient(135deg, var(--bg-surface) 0%, var(--bg-card) 65%, rgba(245, 158, 11, 0.12) 100%);
            border: 1px solid var(--border-strong);
            border-radius: 26px;
            padding: 26px 28px;
            margin-bottom: 24px;
            box-shadow: var(--shadow-card);
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 16px;
        }}

        .wishlist-card {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 20px;
            padding: 18px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            gap: 14px;
            box-shadow: var(--shadow-card);
            transition: var(--transition);
            animation: fadeUp 0.35s ease;
        }}

        .wishlist-card:hover {{
            transform: translateY(-6px) scale(1.015);
            border-color: var(--bh-red-bright);
            box-shadow: 0 20px 36px rgba(255, 42, 68, 0.2);
        }}

        .wishlist-top-row {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 8px;
        }}

        .wishlist-badge {{
            background: rgba(245, 158, 11, 0.16);
            color: #FBBF24;
            border: 1px solid rgba(245, 158, 11, 0.35);
            padding: 4px 10px;
            border-radius: 999px;
            font-size: 0.75rem;
            font-weight: 800;
        }}

        .wishlist-empty {{
            background: var(--bg-card);
            border: 1px dashed var(--border-strong);
            border-radius: 24px;
            padding: 46px 24px;
            text-align: center;
            box-shadow: var(--shadow-card);
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
            box-shadow: var(--shadow-card);
        }}

        .filter-bar select, .filter-bar input {{
            background: var(--bg-input);
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            padding: 9px 14px;
            border-radius: 11px;
            font-size: 0.88rem;
            outline: none;
            transition: var(--transition);
        }}

        .filter-bar select:focus, .filter-bar input:focus {{
            border-color: var(--bh-red-bright);
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
            transition: var(--transition);
        }}

        .chip-toggle:hover {{
            transform: translateY(-2px);
            border-color: var(--bh-red-bright);
        }}

        .chip-toggle.active {{
            background: rgba(16, 185, 129, 0.16);
            border-color: #10B981;
            color: #10B981;
        }}

        .coupon-card {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-top: 4px solid var(--bh-red-bright);
            border-radius: 18px;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 14px;
            box-shadow: var(--shadow-card);
            transition: var(--transition);
        }}

        .coupon-card:hover {{
            transform: translateY(-4px);
            border-color: var(--bh-red-bright);
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
            transition: var(--transition);
        }}

        .coupon-code-box:hover {{
            transform: scale(1.02);
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
            backdrop-filter: blur(6px);
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
            animation: fadeUp 0.25s ease;
        }}

        .float-tg {{
            position: fixed;
            bottom: 20px;
            left: 20px;
            z-index: 90;
            background: linear-gradient(135deg, #0088cc, #229ED9);
            color: #FFFFFF;
            padding: 11px 17px;
            border-radius: 999px;
            font-weight: 800;
            font-size: 0.85rem;
            box-shadow: 0 12px 26px rgba(0, 136, 204, 0.44);
            display: inline-flex;
            align-items: center;
            gap: 8px;
            transition: var(--transition);
            animation: floatSoft 3.2s ease-in-out infinite;
        }}

        .float-tg:hover {{
            transform: translateY(-4px) scale(1.04);
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

        .footer-col ul a {{
            transition: var(--transition);
            display: inline-block;
        }}

        .footer-col ul a:hover {{
            color: var(--bh-red-bright);
            transform: translateX(-3px);
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
            .hero-stats {{
                grid-template-columns: repeat(2, minmax(120px, 1fr));
            }}
            .footer-grid {{
                grid-template-columns: 1fr 1fr;
            }}
        }}

        @media (max-width: 600px) {{
            .container {{
                padding: 0 10px;
            }}
            .navbar-inner {{
                min-height: auto;
                gap: 8px;
                padding: 8px 0;
            }}
            .brand-logo-img {{
                height: 38px;
            }}
            .brand-title {{
                font-size: 1.12rem;
            }}
            .brand-sub {{
                display: none;
            }}
            .seeda-animated-orb {{
                width: 72px;
                height: 72px;
            }}
            .seeda-orb-img {{
                width: 56px;
                height: 56px;
            }}
            .seeda-orb-svg {{
                width: 54px;
                height: 54px;
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
                padding: 6px 10px;
                font-size: 0.76rem;
                border-radius: 9px;
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
            .store-card {{
                flex: 0 0 168px;
                min-width: 168px;
                padding: 14px 10px;
            }}
            .store-icon-box {{
                width: 56px;
                height: 56px;
            }}
            .cat-card {{
                flex: 0 0 228px;
                min-width: 228px;
                padding: 13px 14px;
            }}
            .stores-grid {{
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 10px;
            }}
            .categories-grid {{
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 10px;
            }}
            .products-grid {{
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 10px;
            }}
            .deal-card {{
                border-radius: 15px;
            }}
            .deal-thumb {{
                height: 142px;
                padding: 8px;
            }}
            .badges-top-right {{
                top: 6px;
                right: 6px;
                gap: 3px;
            }}
            .badge-disc, .badge-promo, .badge-real {{
                font-size: 0.64rem;
                padding: 2px 6px;
                border-radius: 6px;
            }}
            .badge-store {{
                bottom: 6px;
                left: 6px;
                font-size: 0.62rem;
                padding: 2px 7px;
            }}
            .deal-body {{
                padding: 9px;
                gap: 6px;
            }}
            .deal-cat {{
                font-size: 0.66rem;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }}
            .deal-title {{
                font-size: 0.8rem;
                line-height: 1.35;
                min-height: 2.15em;
            }}
            .price-now {{
                font-size: 0.96rem;
            }}
            .price-old {{
                font-size: 0.72rem;
            }}
            .history-mini {{
                flex-direction: column;
                gap: 2px;
                font-size: 0.65rem;
                padding: 5px 7px;
            }}
            .card-actions {{
                grid-template-columns: 1fr auto auto;
                gap: 4px;
            }}
            .btn-buy {{
                padding: 6px 6px;
                font-size: 0.7rem;
                border-radius: 8px;
            }}
            .btn-hist {{
                padding: 6px 6px;
                font-size: 0.68rem;
                border-radius: 8px;
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
                        <li><a href="/deals?store=namshi_bh">🖤 نمشي البحرين (شغال)</a></li>
                        <li><a href="/deals?store=extra_bh">🔵 إكسترا البحرين (شغال)</a></li>
                        <li><a href="/deals?store=microless_bh">🟠 ميكروليس البحرين (شغال)</a></li>
                        <li><a href="/deals?store=alershad_bh">🟤 الإرشاد البحرين (شغال)</a></li>
                        <li><a href="/deals?store=alnasser_bh">🔴 النصر البحرين (شغال)</a></li>
                        <li><a href="/deals?store=randb_bh">🖤 آر أند بي البحرين (شغال)</a></li>
                        <li><a href="/deals?store=max_bh">🔴 ماكس البحرين (شغال)</a></li>
                        <li><a href="/deals?store=splash_bh">🔴 سبلاش البحرين (شغال)</a></li>
                        <li><a href="/deals?store=ramez_bh">🔴 رامز البحرين (شغال)</a></li>
                        <li><a href="/deals?store=hypermax_bh">🔴 هايبرماكس البحرين (شغال)</a></li>
                        <li><a href="/deals?store=ansar_bh">🩷 أنصار جاليري البحرين (شغال)</a></li>
                        <li><a href="/deals?store=baraka_bh">🟩 البركة للرياضة البحرين (شغال)</a></li>
                        <li><a href="/deals?store=albayan_bh">🌹 البيان البحرين (شغال)</a></li>
                        <li><a href="/deals?store=zain_bh">🟣 زين البحرين (شغال)</a></li>
                        <li><a href="/deals?store=stc_bh">🟪 stc البحرين (شغال)</a></li>
                        <li><a href="/deals?store=batelco_bh">🔴 باتلكو البحرين (شغال)</a></li>
                        <li><a href="/deals?store=virgin_bh">🟥 فيرجن ميجاستور البحرين (شغال)</a></li>
                        <li><a href="/deals?store=jarir_bh">📕 مكتبة جرير البحرين (شغال)</a></li>
                        <li><a href="/deals?store=sharafdg_bh">🟨 شرف DG البحرين (شغال)</a></li>
                        <li><a href="/deals?store=ourshopee_bh">🟪 أور شوبي البحرين (شغال)</a></li>
                        <li><a href="/deals?store=advancedpc_bh">🟦 أدفانسد بي سي البحرين (شغال)</a></li>
                        <li><a href="/deals?store=lulu_bh">🟩 لولو هايبرماركت البحرين (شغال)</a></li>
                        <li><a href="/deals?store=ishop_bh">🛍️ آي شوب البحرين (شغال)</a></li>
                        <li><a href="/deals?store=aivi_bh">🛍️ أيفي البحرين (شغال)</a></li>
                        <li><a href="/deals?store=soko_bh">🛍️ سوكو البحرين (شغال)</a></li>
                        <li><a href="/deals?store=talabat_mart_bh">🧡 طلبات مارت البحرين (شغال)</a></li>
                        <li><a href="/deals?store=flormar_bh">💄 فلورمار البحرين (شغال)</a></li>
                        <li><a href="/deals?store=ninja_bh">🥷 نينجا البحرين (شغال)</a></li>
                        <li><a href="/deals?store=asq_bh">🕌 عبد الصمد القرشي البحرين (شغال)</a></li>
                        <li><a href="/deals?store=almajed4oud_bh">🪵 الماجد للعود البحرين (شغال)</a></li>
                        <li><a href="/deals?store=bbw_bh">🛁 باث آند بودي وركس البحرين (شغال)</a></li>
                        <li><a href="/deals?store=miniso_bh">🧸 مينيسو البحرين (شغال)</a></li>
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
                        الأسعار وتوفر المنتجات يتحدثون باستمرار، والسعر النهائي هو اللي يطلعلك في صفحة المتجر وقت الدفع. بعض الروابط ممكن تكون روابط عمولة بدون أي زيادة عليك.
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

        const STORE_VISUALS = {{
            noon_bh: {{ label: 'نون البحرين', badge: 'noon', logo: '/static/noon_bh.png', bg: '#FACC15', fg: '#111827', border: 'rgba(250, 204, 21, 0.55)' }},
            namshi_bh: {{ label: 'نمشي البحرين', badge: 'Namshi', logo: '/static/namshi_bh.png', bg: '#111827', fg: '#FFFFFF', border: 'rgba(148, 163, 184, 0.55)' }},
            extra_bh: {{ label: 'إكسترا البحرين', badge: 'eXtra', logo: '/static/extra_bh.png', bg: '#1D4ED8', fg: '#FFFFFF', border: 'rgba(59, 130, 246, 0.55)' }},
            microless_bh: {{ label: 'ميكروليس البحرين', badge: 'Microless', logo: '/static/microless_bh.png', bg: '#EA580C', fg: '#FFFFFF', border: 'rgba(249, 115, 22, 0.55)' }},
            alershad_bh: {{ label: 'الإرشاد البحرين', badge: 'AlErshad', logo: '/static/alershad_bh.png', bg: '#92400E', fg: '#FFFFFF', border: 'rgba(180, 83, 9, 0.55)' }},
            alnasser_bh: {{ label: 'النصر البحرين', badge: 'AlNasser', logo: '/static/alnasser_bh.png', bg: '#B91C1C', fg: '#FFFFFF', border: 'rgba(220, 38, 38, 0.55)' }},
            randb_bh: {{ label: 'آر أند بي البحرين', badge: 'R&B', logo: '/static/randb_bh.png', bg: '#111827', fg: '#FFFFFF', border: 'rgba(148, 163, 184, 0.55)' }},
            max_bh: {{ label: 'ماكس البحرين', badge: 'MAX', logo: '/static/max_bh.png', bg: '#DC2626', fg: '#FFFFFF', border: 'rgba(239, 68, 68, 0.55)' }},
            splash_bh: {{ label: 'سبلاش البحرين', badge: 'Splash', logo: '/static/splash_bh.png', bg: '#E11D48', fg: '#FFFFFF', border: 'rgba(244, 63, 94, 0.55)' }},
            ramez_bh: {{ label: 'رامز البحرين', badge: 'Ramez', logo: '/static/ramez_bh.png', bg: '#B91C1C', fg: '#FFFFFF', border: 'rgba(220, 38, 38, 0.55)' }},
            hypermax_bh: {{ label: 'هايبرماكس البحرين', badge: 'HyperMax', logo: '/static/hypermax_bh.png', bg: '#DC2626', fg: '#FFFFFF', border: 'rgba(239, 68, 68, 0.55)' }},
            ansar_bh: {{ label: 'أنصار جاليري البحرين', badge: 'Ansar', logo: '/static/ansar_bh.png', bg: '#DB2777', fg: '#FFFFFF', border: 'rgba(236, 72, 153, 0.55)' }},
            baraka_bh: {{ label: 'البركة للرياضة البحرين', badge: 'Baraka', logo: '/static/albaraka_bh.png', bg: '#0F766E', fg: '#FFFFFF', border: 'rgba(15, 118, 110, 0.55)' }},
            albayan_bh: {{ label: 'البيان البحرين', badge: 'AlBayan', logo: '/static/Albayan_bh.png', bg: '#991B1B', fg: '#FFFFFF', border: 'rgba(185, 28, 28, 0.55)' }},
            zain_bh: {{ label: 'زين البحرين', badge: 'zain', logo: '/static/zain_bh.png', bg: '#7E22CE', fg: '#FFFFFF', border: 'rgba(168, 85, 247, 0.55)' }},
            stc_bh: {{ label: 'stc البحرين', badge: 'stc', logo: '/static/stc_bh.png', bg: '#4F008C', fg: '#FFFFFF', border: 'rgba(192, 38, 211, 0.55)' }},
            batelco_bh: {{ label: 'باتلكو البحرين', badge: 'Batelco', logo: '/static/batelco_bh.png', bg: '#E11D48', fg: '#FFFFFF', border: 'rgba(225, 29, 72, 0.55)' }},
            virgin_bh: {{ label: 'فيرجن ميجاستور البحرين', badge: 'Virgin', logo: '/static/virgin_bh.png', bg: '#B91C1C', fg: '#FFFFFF', border: 'rgba(239, 68, 68, 0.55)' }},
            jarir_bh: {{ label: 'مكتبة جرير البحرين', badge: 'جرير', logo: '/static/jarir_bh.png', bg: '#DC2626', fg: '#FFFFFF', border: 'rgba(220, 38, 38, 0.55)' }},
            sharafdg_bh: {{ label: 'شرف DG البحرين', badge: 'SDG', logo: '/static/sharafdg_bh.png', bg: '#D97706', fg: '#FFFFFF', border: 'rgba(245, 158, 11, 0.55)' }},
            sharaf_bh: {{ label: 'شرف DG البحرين', badge: 'SDG', logo: '/static/sharafdg_bh.png', bg: '#D97706', fg: '#FFFFFF', border: 'rgba(245, 158, 11, 0.55)' }},
            ourshopee_bh: {{ label: 'أور شوبي البحرين', badge: 'OurShopee', logo: '/static/ourshopee_bh.png', bg: '#6D28D9', fg: '#FFFFFF', border: 'rgba(124, 58, 237, 0.55)' }},
            advancedpc_bh: {{ label: 'أدفانسد بي سي البحرين', badge: 'AdvPC', logo: '/static/advancedpc_bh.png', bg: '#1E40AF', fg: '#FFFFFF', border: 'rgba(37, 99, 235, 0.55)' }},
            lulu_bh: {{ label: 'لولو هايبرماركت البحرين', badge: 'LuLu', logo: '/static/lulu_bh.png', bg: '#15803D', fg: '#FFFFFF', border: 'rgba(22, 163, 74, 0.55)' }},
            ishop_bh: {{ label: 'آي شوب البحرين', badge: 'iShop', logo: '/static/ishop_bh.png', bg: '#0F172A', fg: '#FFFFFF', border: 'rgba(56, 189, 248, 0.55)' }},
            aivi_bh: {{ label: 'أيفي البحرين', badge: 'AIVI', logo: '/static/aivi_bh.png', bg: '#111827', fg: '#FFFFFF', border: 'rgba(255, 42, 68, 0.55)' }},
            soko_bh: {{ label: 'سوكو البحرين', badge: 'SOKO', logo: '/static/soko_bh.png', bg: '#2563EB', fg: '#FFFFFF', border: 'rgba(56, 189, 248, 0.55)' }},
            talabat_mart_bh: {{ label: 'طلبات مارت البحرين', badge: 'Mart', logo: '/static/talabat_mart_bh.png', bg: '#FF5A00', fg: '#FFFFFF', border: 'rgba(255, 90, 0, 0.55)' }},
            flormar_bh: {{ label: 'فلورمار البحرين', badge: 'Flormar', logo: '/static/flormar_bh.png', bg: '#E11D48', fg: '#FFFFFF', border: 'rgba(225, 29, 72, 0.55)' }},
            ninja_bh: {{ label: 'نينجا البحرين', badge: 'Ninja', logo: '/static/ninja_bh.png', bg: '#7C3AED', fg: '#FFFFFF', border: 'rgba(124, 58, 237, 0.55)' }},
            asq_bh: {{ label: 'عبد الصمد القرشي البحرين', badge: 'ASQ', logo: '/static/asq_bh.png', bg: '#78350F', fg: '#FFFFFF', border: 'rgba(217, 119, 6, 0.55)' }},
            almajed4oud_bh: {{ label: 'الماجد للعود البحرين', badge: 'Almajed', logo: '/static/almajed4oud_bh.png', bg: '#7C2D12', fg: '#FFFFFF', border: 'rgba(180, 83, 9, 0.55)' }},
            bbw_bh: {{ label: 'باث آند بودي وركس البحرين', badge: 'BBW', logo: '/static/bbw_bh.png', bg: '#1D4ED8', fg: '#FFFFFF', border: 'rgba(59, 130, 246, 0.55)' }},
            miniso_bh: {{ label: 'مينيسو البحرين', badge: 'MINISO', logo: '/static/miniso_bh.png', bg: '#E11D2E', fg: '#FFFFFF', border: 'rgba(225, 29, 46, 0.55)' }}
        }};

        function getStoreLabel(storeKey) {{
            if (STORE_VISUALS[storeKey]) return STORE_VISUALS[storeKey].label;
            const map = {{
                ashraf_bh: 'أشرف البحرين',
                talabat_bh: 'طلبات البحرين'
            }};
            return map[storeKey] || 'نون البحرين';
        }}

        function getStoreLogo(storeKey) {{
            if (STORE_VISUALS[storeKey] && STORE_VISUALS[storeKey].logo) {{
                return STORE_VISUALS[storeKey].logo;
            }}
            return '/favicon.svg';
        }}

        function renderStoreIconHtml(storeKey) {{
            const info = STORE_VISUALS[storeKey] || {{ badge: 'BH', logo: '/favicon.svg', bg: '#CE1126', fg: '#FFFFFF' }};
            return `
                <div class="store-icon-box">
                    <img
                        src="${{escapeHtml(info.logo)}}"
                        alt="${{escapeHtml(info.badge)}}"
                        class="store-logo-img"
                        onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';"
                    />
                    <span class="store-fallback-badge" style="display:none; background:${{info.bg}}; color:${{info.fg}};">${{escapeHtml(info.badge)}}</span>
                </div>
            `;
        }}

        function scrollHorizontalStrip(containerId, direction) {{
            const el = document.getElementById(containerId);
            if (!el) return;
            const amount = Math.max(260, Math.round(el.clientWidth * 0.72));
            el.scrollBy({{ left: direction * amount, behavior: 'smooth' }});
        }}

        function enableDragScroll(containerId) {{
            const el = document.getElementById(containerId);
            if (!el) return;
            let isDown = false;
            let startX = 0;
            let scrollLeft = 0;
            let moved = false;

            el.addEventListener('mousedown', (e) => {{
                if (e.button !== 0) return;
                isDown = true;
                moved = false;
                startX = e.pageX - el.offsetLeft;
                scrollLeft = el.scrollLeft;
            }});

            window.addEventListener('mouseup', () => {{
                isDown = false;
            }});

            el.addEventListener('mouseleave', () => {{
                isDown = false;
            }});

            el.addEventListener('mousemove', (e) => {{
                if (!isDown) return;
                e.preventDefault();
                const x = e.pageX - el.offsetLeft;
                const walk = (x - startX) * 1.35;
                if (Math.abs(walk) > 6) moved = true;
                el.scrollLeft = scrollLeft - walk;
            }});

            el.addEventListener('click', (e) => {{
                if (moved) {{
                    e.preventDefault();
                    e.stopPropagation();
                    moved = false;
                }}
            }}, true);
        }}

        function getDecimalsByStore(storeKey) {{
            return (
                storeKey === 'extra_bh' ||
                storeKey === 'microless_bh' ||
                storeKey === 'alershad_bh' ||
                storeKey === 'alnasser_bh' ||
                storeKey === 'randb_bh' ||
                storeKey === 'max_bh' ||
                storeKey === 'splash_bh' ||
                storeKey === 'ramez_bh' ||
                storeKey === 'hypermax_bh' ||
                storeKey === 'ansar_bh' ||
                storeKey === 'baraka_bh' ||
                storeKey === 'albayan_bh' ||
                storeKey === 'zain_bh' ||
                storeKey === 'stc_bh' ||
                storeKey === 'batelco_bh' ||
                storeKey === 'sharafdg_bh' ||
                storeKey === 'sharaf_bh' ||
                storeKey === 'advancedpc_bh' ||
                storeKey === 'lulu_bh' ||
                storeKey === 'ishop_bh' ||
                storeKey === 'aivi_bh' ||
                storeKey === 'soko_bh' ||
                storeKey === 'talabat_mart_bh' ||
                storeKey === 'flormar_bh' ||
                storeKey === 'ninja_bh' ||
                storeKey === 'asq_bh' ||
                storeKey === 'almajed4oud_bh' ||
                storeKey === 'bbw_bh' ||
                storeKey === 'miniso_bh'
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
            if (step <= 2 && imgEl.dataset.storeLogo) {{
                imgEl.dataset.imgStep = '3';
                imgEl.src = imgEl.dataset.storeLogo;
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

        function extractPromoFromTitle(rawName) {{
            const name = String(rawName || '').trim();
            const splitMatch = name.match(/^(.*?)\\s*\\|\\s*🎁\\s*(.+)$/);
            if (splitMatch) {{
                return {{ cleanTitle: splitMatch[1].trim(), promoText: splitMatch[2].trim() }};
            }}
            const inlinePatterns = [
                /(\\d+\\s*\\+\\s*\\d+\\s*مجان[اًا]?)/i,
                /(\\d+\\s*\\+\\s*\\d+\\s*free)/i,
                /(اختر\\s*أي\\s*\\d+[^|،]{{2,32}})/i,
                /(اشترِ?\\s*\\d+[^|،]{{2,32}})/i,
                /(هدية\\s*مجان[اًا]?[^|،]{{0,22}})/i,
                /(كاش\\s*باك[^|،]{{0,22}})/i,
                /(شحن\\s*مجان[اًا]?[^|،]{{0,18}})/i
            ];
            for (const pat of inlinePatterns) {{
                const m = name.match(pat);
                if (m) {{
                    return {{ cleanTitle: name, promoText: m[1].trim() }};
                }}
            }}
            return {{ cleanTitle: name, promoText: '' }};
        }}

        function renderProductCard(p) {{
            const storeKey = p.store || (String(p.sku || '').startsWith('ANSAR_') ? 'ansar_bh' : 'noon_bh');
            const storeLabel = getStoreLabel(storeKey);
            const storeLogo = getStoreLogo(storeKey);
            const currStr = fmtPrice(p.current_price, storeKey);
            const oldStr = p.old_price ? fmtPrice(p.old_price, storeKey) : null;
            const lowStr = fmtPrice(p.lowest_price, storeKey);
            const avgStr = fmtPrice(p.avg_price, storeKey);
            const unitSuffix = 'د.ب';

            const parsedTitle = extractPromoFromTitle(p.name || '');
            const displayName = parsedTitle.cleanTitle || (p.name || '');
            const promoOffer = String(p.promo_offer || parsedTitle.promoText || '').trim();

            const rawImg = String(p.image_url || '').trim();
            const isLocalImg = rawImg.startsWith('/static/') && !isBannedBannerUrl(rawImg);
            const isHttpImg = /^https?:\\/\\//i.test(rawImg) && !isBannedBannerUrl(rawImg);

            const localSrc = isLocalImg ? rawImg : '';
            const originImg = isHttpImg ? rawImg : '';
            const proxyImg = isHttpImg ? ('/img-proxy?url=' + encodeURIComponent(rawImg)) : '';

            const primaryImg = (storeKey === 'microless_bh')
                ? (localSrc || storeLogo || proxyImg || originImg || '/favicon.svg')
                : (proxyImg || originImg || localSrc || storeLogo || '/favicon.svg');
            const initialStep = localSrc ? '0' : (proxyImg ? '1' : (originImg ? '2' : (storeLogo ? '3' : '4')));

            const oldHtml = oldStr ? `<span class="price-old">${{oldStr}} ${{unitSuffix}}</span>` : '';
            const discHtml = p.discount_pct > 0 ? `<span class="badge-disc">-${{Math.round(p.discount_pct)}}%</span>` : '';
            const promoHtml = promoOffer ? `<span class="badge-promo">🎁 ${{escapeHtml(promoOffer)}}</span>` : '';
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
                        <div class="badges-top-right">${{discHtml}}${{promoHtml}}${{realHtml}}</div>
                        <span class="badge-store">${{escapeHtml(storeLabel)}}</span>
                        <img src="${{escapeHtml(primaryImg)}}" data-proxy="${{escapeHtml(proxyImg)}}" data-origin="${{escapeHtml(originImg)}}" data-store-logo="${{escapeHtml(storeLogo)}}" data-img-step="${{initialStep}}" alt="${{escapeHtml(displayName)}}" loading="lazy" onerror="handleProductImageError(this)" />
                    </div>
                    <div class="deal-body">
                        <div class="deal-cat">${{escapeHtml(p.category || 'عام')}} • ${{escapeHtml(p.updated_ago || '')}}</div>
                        <h3 class="deal-title" title="${{escapeHtml(p.name)}}">${{escapeHtml(displayName)}}</h3>
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
                            <button type="button" class="btn-hist btn-save ${{isSaved ? 'saved' : ''}}" onclick='toggleSaveDeal(this, ${{savePayload}})' title="احفظه في المفضلة">${{isSaved ? '⭐ محفوظ' : '☆ احفظه'}}</button>
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
                            borderColor: '#FF2A44',
                            backgroundColor: 'rgba(255, 42, 68, 0.16)',
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
    has_custom_logo = (BASE_DIR / "logo.png").exists()
    orb_logo_html = (
        '<img src="/logo.png" alt="صيدة" class="seeda-orb-img" />'
        if has_custom_logo
        else r"""
        <svg viewBox="0 0 64 64" class="seeda-orb-svg" aria-hidden="true">
            <defs>
                <linearGradient id="homeOrbGrad" x1="0" y1="0" x2="1" y2="1">
                    <stop offset="0%" stop-color="#FF2A44"/>
                    <stop offset="100%" stop-color="#F59E0B"/>
                </linearGradient>
            </defs>
            <circle cx="32" cy="32" r="28" fill="url(#homeOrbGrad)"/>
            <circle cx="32" cy="32" r="18" fill="none" stroke="#FFFFFF" stroke-width="2.5" stroke-dasharray="6 4"/>
            <circle cx="32" cy="32" r="7" fill="#FFFFFF"/>
            <circle cx="32" cy="32" r="3" fill="#CE1126"/>
        </svg>
        """
    )

    store_order = [
        "noon_bh", "namshi_bh", "extra_bh", "microless_bh", "alershad_bh",
        "alnasser_bh", "randb_bh", "max_bh", "splash_bh", "ramez_bh", "hypermax_bh", "ansar_bh",
        "baraka_bh", "albayan_bh", "zain_bh", "stc_bh", "batelco_bh",
        "virgin_bh", "jarir_bh", "sharafdg_bh", "ourshopee_bh",
        "advancedpc_bh", "lulu_bh", "ishop_bh", "aivi_bh", "soko_bh", "talabat_mart_bh",
        "flormar_bh", "ninja_bh", "asq_bh", "almajed4oud_bh", "bbw_bh", "miniso_bh"
    ]
    store_cards_parts = []
    for k in store_order:
        meta = STORE_META[k]
        icon_html = f"""
            <div class="store-icon-box">
                <img src="{meta['logo']}" alt="{html.escape(meta['badge'])}" class="store-logo-img"
                     onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';" />
                <span class="store-fallback-badge" style="display:none; background:{meta['accent']}; color:{'#111827' if meta['text_dark'] else '#FFFFFF'};">{html.escape(meta['badge'])}</span>
            </div>
        """
        store_cards_parts.append(f"""
            <a href="/deals?store={k}" class="store-card" style="border-color: rgba(255, 255, 255, 0.12);">
                {icon_html}
                <div class="store-name">{html.escape(meta['label'])}</div>
                <div class="store-meta" id="homeMeta_{k}">شغال الحين • BHD</div>
            </a>
        """)
    stores_cards_html = "".join(store_cards_parts)

    body = f"""
    <section class="hero-box">
        <div>
            <div class="hero-badge"><span class="live-dot"></span> صيدة البحرين • متابعة فورية للأسعار</div>
            <h1 class="hero-title">أقوى صيدات البحرين... <span>أول ما تنزل 🎯</span></h1>
            <p class="hero-desc">
                نراقب الأسعار بالدينار البحريني (BHD / د.ب) في متاجر البحرين ونوريك تاريخ السعر عشان تعرف إذا الخصم صج يسوى ولا بس حجي.
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
            <div class="showcase-orb-banner">
                <div class="showcase-orb-info">
                    <span class="tag-pill">شغال 24/7</span>
                    <div style="font-weight:900; font-size:1rem; line-height:1.35;">رادار صيدة الذكي 🎯</div>
                    <div style="font-size:0.78rem; color:var(--text-secondary);">اضغط على اللوجو ودش على الصيدات الصجية</div>
                </div>
                <a href="/deals?real_only=1" class="seeda-animated-orb" title="لوجو صيدة المتحرك — چوف الصيدات">
                    {orb_logo_html}
                </a>
            </div>
            <div class="showcase-top">
                <span style="font-weight:800; font-size:0.95rem;">📊 شلون نعرف الصيدة الصجية؟</span>
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

    <section class="strip-wrap">
        <div class="sec-head">
            <div>
                <h2 class="sec-title">🏬 المتاجر في البحرين</h2>
                <div class="sec-sub">اسحب يمين ويسار في الشريط أو دوس على أي متجر أو افتح صفحة كل المتاجر</div>
            </div>
            <div class="sec-head-actions">
                <div class="strip-controls">
                    <button type="button" class="strip-arrow" onclick="scrollHorizontalStrip('homeStoresStrip', 1)" aria-label="اللي عقبه">→</button>
                    <button type="button" class="strip-arrow" onclick="scrollHorizontalStrip('homeStoresStrip', -1)" aria-label="اللي قبله">←</button>
                </div>
                <a href="/stores" class="btn-outline">كل المتاجر ←</a>
            </div>
        </div>
        <div class="stores-strip" id="homeStoresStrip">
            {stores_cards_html}
        </div>
    </section>

    <section class="strip-wrap">
        <div class="sec-head">
            <div>
                <h2 class="sec-title">📂 الأقسام</h2>
                <div class="sec-sub">قلّب في شريط الأقسام وافتح القسم اللي تبيه بضغطة وحدة</div>
            </div>
            <div class="sec-head-actions">
                <div class="strip-controls">
                    <button type="button" class="strip-arrow" onclick="scrollHorizontalStrip('homeCatsGrid', 1)" aria-label="اللي عقبه">→</button>
                    <button type="button" class="strip-arrow" onclick="scrollHorizontalStrip('homeCatsGrid', -1)" aria-label="اللي قبله">←</button>
                </div>
                <a href="/categories" class="btn-outline">كل الأقسام ←</a>
            </div>
        </div>
        <div class="cats-strip" id="homeCatsGrid"></div>
    </section>

    <section style="margin-bottom: 38px;">
        <div class="sec-head">
            <div>
                <h2 class="sec-title"><span class="live-dot"></span> صيدات نازلة الحين</h2>
                <div class="sec-sub">أجدد المنتجات اللي نزلت أسعارها أو عليها خصم يسوى</div>
            </div>
            <a href="/deals" class="btn-primary">چوف الكل ←</a>
        </div>
        <div class="products-grid" id="homeDealsGrid"></div>
    </section>
    """

    script = """
    <script>
        enableDragScroll('homeStoresStrip');
        enableDragScroll('homeCatsGrid');

        function bindStoreMeta(sum) {
            const st = sum.stores || {};
            Object.keys(st).forEach(k => {
                const el = document.getElementById('homeMeta_' + k);
                if (el) {
                    el.textContent = `${st[k].count} منتج • خصم لحد ${st[k].max_discount}%`;
                }
            });
            const sdg = st.sharafdg_bh || st.sharaf_bh;
            const sdgEl = document.getElementById('homeMeta_sharafdg_bh');
            if (sdg && sdgEl) {
                sdgEl.textContent = `${sdg.count} منتج • خصم لحد ${sdg.max_discount}%`;
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
                catsGrid.innerHTML = sum.categories.map(c => `
                    <a href="/deals?category=${encodeURIComponent(c.name)}" class="cat-card">
                        <div style="display:flex; align-items:center; gap:12px; min-width:0;">
                            <div class="cat-badge-icon">🎯</div>
                            <div style="min-width:0;">
                                <div style="font-weight:800; font-size:0.95rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${escapeHtml(c.name)}</div>
                                <div style="font-size:0.78rem; color:var(--text-secondary);">${c.count} منتج • خصم لحد ${c.max_discount}%</div>
                            </div>
                        </div>
                        <span class="cat-arrow">←</span>
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
            <option value="namshi_bh">نمشي البحرين</option>
            <option value="extra_bh">إكسترا البحرين</option>
            <option value="microless_bh">ميكروليس البحرين</option>
            <option value="alershad_bh">الإرشاد البحرين</option>
            <option value="alnasser_bh">النصر البحرين</option>
            <option value="randb_bh">آر أند بي البحرين</option>
            <option value="max_bh">ماكس البحرين</option>
            <option value="splash_bh">سبلاش البحرين</option>
            <option value="ramez_bh">رامز البحرين</option>
            <option value="hypermax_bh">هايبرماكس البحرين</option>
            <option value="ansar_bh">أنصار جاليري البحرين</option>
            <option value="baraka_bh">البركة للرياضة البحرين</option>
            <option value="albayan_bh">البيان البحرين</option>
            <option value="zain_bh">زين البحرين</option>
            <option value="stc_bh">stc البحرين</option>
            <option value="batelco_bh">باتلكو البحرين</option>
            <option value="virgin_bh">فيرجن ميجاستور البحرين</option>
            <option value="jarir_bh">مكتبة جرير البحرين</option>
            <option value="sharafdg_bh">شرف DG البحرين</option>
            <option value="ourshopee_bh">أور شوبي البحرين</option>
            <option value="advancedpc_bh">أدفانسد بي سي البحرين</option>
            <option value="lulu_bh">لولو هايبرماركت البحرين</option>
            <option value="ishop_bh">آي شوب البحرين</option>
            <option value="aivi_bh">أيفي البحرين</option>
            <option value="soko_bh">سوكو البحرين</option>
            <option value="talabat_mart_bh">طلبات مارت البحرين</option>
            <option value="flormar_bh">فلورمار البحرين</option>
            <option value="ninja_bh">نينجا البحرين</option>
            <option value="asq_bh">عبد الصمد القرشي البحرين</option>
            <option value="almajed4oud_bh">الماجد للعود البحرين</option>
            <option value="bbw_bh">باث آند بودي وركس البحرين</option>
            <option value="miniso_bh">مينيسو البحرين</option>
        </select>
        <select id="filterCat">
            <option value="">كل الأقسام</option>
        </select>
        <select id="filterSort">
            <option value="recent">الأجدد نزولاً</option>
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
        let preferredCat = urlParams.get('category') || '';

        document.getElementById('filterQ').value = urlParams.get('q') || '';
        document.getElementById('filterStore').value = urlParams.get('store') || '';
        document.getElementById('filterSort').value = urlParams.get('sort') || 'recent';
        if (realOnly) document.getElementById('toggleRealBtn').classList.add('active');

        document.getElementById('toggleRealBtn').addEventListener('click', function() {
            realOnly = realOnly ? 0 : 1;
            this.classList.toggle('active', realOnly === 1);
            applyFilters(1);
        });

        document.getElementById('filterStore').addEventListener('change', async function() {
            preferredCat = '';
            await initCategoriesFilter(this.value);
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

        async function initCategoriesFilter(storeVal = '') {
            const qs = storeVal ? ('?store=' + encodeURIComponent(storeVal)) : '';
            const res = await fetch('/api/summary' + qs);
            const data = await res.json();
            const sel = document.getElementById('filterCat');
            sel.innerHTML = '<option value="">كل الأقسام</option>';
            let matched = false;
            data.categories.forEach(c => {
                if (!c.name) return;
                const opt = document.createElement('option');
                opt.value = c.name;
                opt.textContent = `${c.name} (${c.count})`;
                if (preferredCat && c.name === preferredCat) {
                    opt.selected = true;
                    matched = true;
                }
                sel.appendChild(opt);
            });
            if (!matched) {
                sel.value = '';
            }
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
                    pag.innerHTML += `<button class="btn-outline" onclick="applyFilters(${page + 1})">اللي عقبه</button>`;
                }
            }
        }

        const initialStore = document.getElementById('filterStore').value;
        initCategoriesFilter(initialStore).then(() => applyFilters(1));
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
            <div class="sec-sub">تصفح كل الأقسام بترتيب مريح أو دوّر باسم القسم على طول</div>
        </div>
        <div id="catsCountBadge" class="tag-pill">قاعدين نحمّل...</div>
    </div>

    <div class="directory-search-box">
        <span style="font-size:1.15rem;" aria-hidden="true">🔍</span>
        <input type="text" id="categorySearchInput" placeholder="اكتب اسم القسم عشان تلاقيه بسرعة..." autocomplete="off" autofocus />
    </div>

    <div class="categories-grid" id="allCatsGrid"></div>
    """
    script = """
    <script>
        let allCategoriesData = [];

        function renderFilteredCategories(queryText = '') {
            const q = String(queryText || '').trim().toLowerCase();
            const grid = document.getElementById('allCatsGrid');
            const badge = document.getElementById('catsCountBadge');
            const filtered = q
                ? allCategoriesData.filter(c => String(c.name || '').toLowerCase().includes(q))
                : allCategoriesData;

            badge.textContent = `${filtered.length} قسم`;
            if (!filtered.length) {
                grid.innerHTML = '<p style="color:var(--text-secondary); grid-column:1/-1;">ما لقينا قسم يطابق بحثك.</p>';
                return;
            }
            grid.innerHTML = filtered.map(c => `
                <a href="/deals?category=${encodeURIComponent(c.name)}" class="cat-card">
                    <div style="display:flex; align-items:center; gap:14px; min-width:0;">
                        <div class="cat-badge-icon">🎯</div>
                        <div style="min-width:0;">
                            <div style="font-weight:800; font-size:1rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${escapeHtml(c.name)}</div>
                            <div style="font-size:0.8rem; color:var(--text-secondary);">${c.count} منتج • خصم لحد ${c.max_discount}%</div>
                        </div>
                    </div>
                    <span class="cat-arrow">←</span>
                </a>
            `).join('');
        }

        document.getElementById('categorySearchInput').addEventListener('input', function() {
            renderFilteredCategories(this.value);
        });

        fetch('/api/summary').then(r => r.json()).then(data => {
            allCategoriesData = Array.isArray(data.categories) ? data.categories : [];
            renderFilteredCategories(document.getElementById('categorySearchInput').value);
        });
    </script>
    """
    return render_layout("الأقسام", "categories", body, script, user=user)


@app.get("/stores", response_class=HTMLResponse)
def page_stores(request: Request):
    user = get_current_user(request)
    store_order = [
        "noon_bh", "namshi_bh", "extra_bh", "microless_bh", "alershad_bh",
        "alnasser_bh", "randb_bh", "max_bh", "splash_bh", "ramez_bh", "hypermax_bh", "ansar_bh",
        "baraka_bh", "albayan_bh", "zain_bh", "stc_bh", "batelco_bh",
        "virgin_bh", "jarir_bh", "sharafdg_bh", "ourshopee_bh",
        "advancedpc_bh", "lulu_bh", "ishop_bh", "aivi_bh", "soko_bh", "talabat_mart_bh",
        "flormar_bh", "ninja_bh", "asq_bh", "almajed4oud_bh", "bbw_bh", "miniso_bh"
    ]
    cards = []
    for k in store_order:
        meta = STORE_META[k]
        search_terms = html.escape(f"{meta['label']} {meta['badge']} {k}".lower())
        cards.append(f"""
            <a href="/deals?store={k}" class="store-card" data-store-search="{search_terms}" style="border-color: rgba(255, 255, 255, 0.14);">
                <div class="store-icon-box">
                    <img src="{meta['logo']}" alt="{html.escape(meta['badge'])}" class="store-logo-img"
                         onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';" />
                    <span class="store-fallback-badge" style="display:none; background:{meta['accent']}; color:{'#111827' if meta['text_dark'] else '#FFFFFF'};">{html.escape(meta['badge'])}</span>
                </div>
                <div class="store-name">{html.escape(meta['label'])}</div>
                <div style="font-size:0.76rem; color:var(--text-secondary); margin-bottom:6px;">BH البحرين • عملة BHD</div>
                <div class="store-meta" id="pageStoreMeta_{k}">شغال الحين</div>
            </a>
        """)
    body = f"""
    <div class="sec-head">
        <div>
            <h1 class="sec-title">🏬 المتاجر في البحرين 🇧🇭</h1>
            <div class="sec-sub">كل المتاجر مرتبة في صفوف أو دوّر باسم المتجر على طول</div>
        </div>
        <div id="storesCountBadge" class="tag-pill">{len(store_order)} متجر</div>
    </div>

    <div class="directory-search-box">
        <span style="font-size:1.15rem;" aria-hidden="true">🔍</span>
        <input type="text" id="storeSearchInput" placeholder="اكتب اسم المتجر عشان تلاقيه بسرعة (نون، نمشي، إكسترا، طلبات...)" autocomplete="off" autofocus />
    </div>

    <div class="stores-grid" id="allStoresGrid">
        {"".join(cards)}
    </div>
    """
    script = """
    <script>
        function filterStoresGrid(queryText = '') {
            const q = String(queryText || '').trim().toLowerCase();
            const cards = Array.from(document.querySelectorAll('#allStoresGrid .store-card'));
            let visibleCount = 0;
            cards.forEach(card => {
                const hay = (card.getAttribute('data-store-search') || card.textContent || '').toLowerCase();
                const match = !q || hay.includes(q);
                card.style.display = match ? '' : 'none';
                if (match) visibleCount += 1;
            });
            const badge = document.getElementById('storesCountBadge');
            if (badge) badge.textContent = `${visibleCount} متجر`;
        }

        document.getElementById('storeSearchInput').addEventListener('input', function() {
            filterStoresGrid(this.value);
        });

        fetch('/api/summary').then(r => r.json()).then(d => {
            const st = d.stores || {};
            Object.keys(st).forEach(k => {
                const el = document.getElementById('pageStoreMeta_' + k);
                if (el) {
                    el.textContent = `${st[k].count} منتج • خصومات لحد ${st[k].max_discount}%`;
                }
            });
            const sdg = st.sharafdg_bh || st.sharaf_bh;
            const sdgEl = document.getElementById('pageStoreMeta_sharafdg_bh');
            if (sdg && sdgEl) {
                sdgEl.textContent = `${sdg.count} منتج • خصومات لحد ${sdg.max_discount}%`;
            }
        });
    </script>
    """
    return render_layout("المتاجر", "stores", body, script, user=user)


@app.get("/wishlist", response_class=HTMLResponse)
def page_wishlist(request: Request):
    user = get_current_user(request)
    if not user or not user.get("id"):
        body = """
        <div class="wishlist-empty">
            <div style="font-size:2.4rem; margin-bottom:10px;">⭐</div>
            <h1 style="font-size:1.45rem; font-weight:900; margin-bottom:8px;">سجّل دخولك عشان تفتح قائمة المفضلة</h1>
            <p style="color:var(--text-secondary); font-size:0.94rem; margin-bottom:20px;">
                احفظ عروضك المفضلة وتابع أسعارها في البحرين بكل سهولة.
            </p>
            <div style="display:flex; justify-content:center; gap:10px; flex-wrap:wrap;">
                <a href="/login/google?next=%2Fwishlist" class="btn-primary">دخول سريع بقوقل</a>
                <a href="/login" class="btn-outline">دخول بالإيميل</a>
            </div>
        </div>
        """
        return render_layout("المفضلة", "deals", body, user=None)

    conn = get_db()
    cur = conn.cursor()
    saved_items = []
    try:
        cur.execute(
            _sql(conn, "SELECT deal_key, title, price, url, created_at FROM saved_deals WHERE user_id = ? ORDER BY created_at DESC"),
            (int(user["id"]),),
        )
        saved_items = [_row_to_dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

    if not saved_items:
        cards_html = """
            <div class="wishlist-empty" style="grid-column: 1 / -1;">
                <div style="font-size:2.3rem; margin-bottom:10px;">⭐</div>
                <h2 style="font-size:1.25rem; font-weight:900; margin-bottom:8px;">قائمة المفضلة فاضية الحين</h2>
                <p style="color:var(--text-secondary); font-size:0.92rem; margin-bottom:18px;">
                    احفظ أي عرض يعجبك من صفحة العروض عشان ترجعله بسرعة وتتابع سعره.
                </p>
                <a href="/deals" class="btn-primary">🔥 چوف العروض الحين</a>
            </div>
        """
    else:
        parts = []
        for it in saved_items:
            raw_key = str(it.get("deal_key") or "")
            d_key = html.escape(raw_key)
            d_title = html.escape(str(it.get("title") or "منتج محفوظ"))
            d_price = html.escape(str(it.get("price") or ""))
            d_url = html.escape(apply_affiliate(str(it.get("url") or "#")))
            d_ago = html.escape(format_time_ago(it.get("created_at")))
            parts.append(f"""
                <article class="wishlist-card">
                    <div style="display:flex; flex-direction:column; gap:10px;">
                        <div class="wishlist-top-row">
                            <span class="wishlist-badge">⭐ محفوظ في المفضلة</span>
                            <span style="font-size:0.75rem; color:var(--text-secondary); font-weight:700;">{d_ago}</span>
                        </div>
                        <h3 class="deal-title" title="{d_title}">{d_title}</h3>
                    </div>
                    <div style="display:flex; flex-direction:column; gap:12px;">
                        <div class="price-row" style="background:var(--bg-input); padding:10px 12px; border-radius:12px; border:1px solid var(--border-color); justify-content:space-between;">
                            <span class="price-now">{d_price}</span>
                            <span style="font-size:0.74rem; color:var(--text-muted); font-weight:700;">BHD</span>
                        </div>
                        <div class="card-actions" style="grid-template-columns: 1fr auto auto;">
                            <a href="{d_url}" target="_blank" rel="noopener" class="btn-buy">روح للعرض ↗</a>
                            <button type="button" class="btn-hist" onclick="openHistoryModal('{d_key}')" title="چوف تاريخ السعر">📊</button>
                            <button type="button" class="btn-hist btn-save saved" onclick="removeSavedItem(this, '{d_key}')">حذف</button>
                        </div>
                    </div>
                </article>
            """)
        cards_html = "".join(parts)

    safe_user_name = html.escape(str(user.get("name") or ""))
    body = f"""
    <section class="wishlist-banner">
        <div>
            <div class="hero-badge" style="margin-bottom:8px;">⭐ قائمة المتابعة مالتك</div>
            <h1 class="sec-title" style="font-size:1.55rem;">عروضي المفضلة {f"— {safe_user_name}" if safe_user_name else ""}</h1>
            <div class="sec-sub">كل المنتجات اللي حفظتها في مكان واحد مرتب عشان تتابع السعر وتروح للمتجر على طول</div>
        </div>
        <div class="sec-head-actions">
            <span class="tag-pill" id="wishlistCountPill">{len(saved_items)} منتج محفوظ</span>
            <a href="/deals" class="btn-primary">⚡ ضيف عروض يديدة</a>
            <a href="/logout" class="btn-outline">خروج</a>
        </div>
    </section>

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
                const card = btn.closest('.wishlist-card');
                if (card) card.remove();
                const remaining = document.querySelectorAll('#wishlistGrid .wishlist-card').length;
                const pill = document.getElementById('wishlistCountPill');
                if (pill) pill.textContent = `${remaining} منتج محفوظ`;
                if (remaining === 0) {
                    document.getElementById('wishlistGrid').innerHTML = `
                        <div class="wishlist-empty" style="grid-column: 1 / -1;">
                            <div style="font-size:2.3rem; margin-bottom:10px;">⭐</div>
                            <h2 style="font-size:1.25rem; font-weight:900; margin-bottom:8px;">قائمة المفضلة فاضية الحين</h2>
                            <p style="color:var(--text-secondary); font-size:0.92rem; margin-bottom:18px;">
                                احفظ أي عرض يعجبك من صفحة العروض عشان ترجعله بسرعة وتتابع سعره.
                            </p>
                            <a href="/deals" class="btn-primary">🔥 چوف العروض الحين</a>
                        </div>
                    `;
                }
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
                    <div class="store-icon-box" style="width:46px; height:46px; margin:0; padding:5px;">
                        <img src="/static/noon_bh.png" alt="noon" class="store-logo-img" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';" />
                        <span class="store-fallback-badge" style="display:none; background:#FACC15; color:#111;">noon</span>
                    </div>
                    <div>
                        <div style="font-weight:800;">كوبون نون البحرين</div>
                        <div style="font-size:0.78rem; color:var(--text-secondary);">كود يتحدث باستمرار</div>
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

    <div style="background:linear-gradient(135deg, #0088cc, #0284c7); color:#fff; border-radius:20px; padding:24px; display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:16px; box-shadow:var(--shadow-card);">
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
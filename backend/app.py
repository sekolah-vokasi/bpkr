import json
import os
import secrets
from datetime import datetime
from time import monotonic
from html import escape
from pathlib import Path
from typing import Optional

import bleach
from fastapi import FastAPI, Depends, HTTPException, Request, Response, UploadFile, File, Query, BackgroundTasks
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from db import SessionLocal, init_db, User, Post, Entry, Meeting, Letter, Setting, AuditLog, utcnow
from logic import slugify, parse_meeting_notes, letter_body
from security import hash_password, verify_password, create_token, read_token

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "frontend" / "dist"
UPLOADS = ROOT / "uploads"
UPLOADS.mkdir(exist_ok=True)
BASE_URL = os.environ.get("BPKR_PUBLIC_URL", "https://bpkr.otomasi.app").rstrip("/")
ROLES = ["pimpinan", "sekretaris", "keuangan", "kerjasama", "dosen", "laboran", "tendik", "mahasiswa", "superadmin", "admin"]
POWER = {"admin", "superadmin"}
EDITOR = POWER | {"pimpinan", "sekretaris", "kerjasama"}
MEETING_EDITORS = POWER | {"pimpinan", "sekretaris"}
MEETING_READERS = set(ROLES) - {"mahasiswa"}
APPROVERS = POWER | {"pimpinan"}
LOGIN_FAILURES = {}
LETTER_EDITORS = POWER | {"pimpinan", "sekretaris", "tendik"}
MODULE_PERMISSIONS = {
    "agenda": set(ROLES),
    "administrasi": POWER | {"pimpinan", "sekretaris", "tendik"},
    "keuangan": POWER | {"pimpinan", "keuangan"},
    "kerjasama": POWER | {"pimpinan", "kerjasama"},
    "akademik": POWER | {"pimpinan", "dosen", "sekretaris"},
    "laboratorium": POWER | {"pimpinan", "laboran", "dosen"},
    "sarpras": POWER | {"pimpinan", "laboran", "tendik", "sekretaris"},
    "mahasiswa": POWER | {"pimpinan", "mahasiswa", "dosen", "tendik"},
}
MODULE_EDITORS = {
    "agenda": MEETING_EDITORS,
    "administrasi": POWER | {"pimpinan", "sekretaris", "tendik"},
    "keuangan": POWER | {"pimpinan", "keuangan"},
    "kerjasama": POWER | {"pimpinan", "kerjasama"},
    "akademik": POWER | {"pimpinan", "dosen"},
    "laboratorium": POWER | {"pimpinan", "laboran"},
    "sarpras": POWER | {"pimpinan", "laboran", "tendik"},
    "mahasiswa": POWER | {"pimpinan", "tendik", "mahasiswa"},
}
app = FastAPI(title="BPKR API", version="1.0.0", docs_url="/api/docs", openapi_url="/api/openapi.json", redoc_url=None)

@app.on_event("startup")
def startup():
    init_db()

def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def current_user(request: Request, db: Session = Depends(db_session)) -> User:
    token = request.cookies.get("bpkr_session")
    if not token:
        raise HTTPException(401, "Silakan masuk terlebih dahulu")
    payload = read_token(token)
    user = db.get(User, payload.get("sub"))
    if not user or not user.is_active or payload.get("ver") != user.password_hash[-20:]:
        raise HTTPException(401, "Sesi berakhir, silakan masuk lagi")
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        csrf_cookie = request.cookies.get("bpkr_csrf")
        csrf_header = request.headers.get("x-csrf-token")
        if not csrf_cookie or not csrf_header or not secrets.compare_digest(csrf_cookie, csrf_header):
            raise HTTPException(403, "CSRF token tidak cocok")
        if user.must_change_password and request.url.path != "/api/auth/change-password":
            raise HTTPException(403, "Ganti kata sandi awal sebelum mengakses fitur")
    return user

def require(user: User, allowed: set[str]):
    if user.role not in allowed:
        raise HTTPException(403, "Role tidak memiliki izin untuk tindakan ini")

def track(db: Session, user: User, action: str, entity: str, entity_id: int = None):
    db.add(AuditLog(actor_id=user.id, action=action, entity=entity, entity_id=entity_id))

def ser(model, fields):
    data = {k: getattr(model, k) for k in fields}
    for k, v in data.items():
        if isinstance(v, datetime):
            data[k] = v.isoformat()
        elif hasattr(v, "as_tuple"):
            data[k] = float(v)
    return data

POST_KEYS = ("id", "type", "title", "slug", "excerpt", "content", "image_url", "category", "tags", "seo_title", "seo_description", "status", "author_id", "created_at", "updated_at", "published_at")
ENTRY_KEYS = ("id", "module", "title", "body", "status", "amount", "due_at", "assigned_to", "details", "created_by", "created_at", "updated_at")
MEETING_KEYS = ("id", "title", "date", "time", "place", "participants", "notes", "discussions", "decisions", "tasks", "status", "created_by", "created_at", "updated_at")
LETTER_KEYS = ("id", "kind", "recipient", "subject", "instructions", "signer", "number", "attachment", "date", "body", "status", "created_by", "created_at", "updated_at")
USER_KEYS = ("id", "username", "full_name", "email", "role", "is_active", "must_change_password", "created_at")

class LoginIn(BaseModel):
    username: str
    password: str

class PasswordIn(BaseModel):
    old_password: str
    new_password: str = Field(min_length=12, max_length=128)

class UserIn(BaseModel):
    username: str = Field(min_length=3, max_length=80)
    full_name: str = Field(min_length=2, max_length=180)
    role: str
    email: Optional[str] = None
    password: str = ""
    is_active: bool = True

class PostIn(BaseModel):
    type: str = "news"
    title: str = Field(min_length=3, max_length=220)
    slug: str = ""
    excerpt: str = ""
    content: str = ""
    image_url: str = ""
    category: str = "Berita"
    tags: str = ""
    seo_title: str = ""
    seo_description: str = ""
    status: str = "draft"

class EntryIn(BaseModel):
    module: str
    title: str = Field(min_length=2, max_length=220)
    body: str = ""
    status: str = "baru"
    amount: Optional[float] = None
    due_at: str = ""
    assigned_to: str = ""
    details: dict = Field(default_factory=dict)

class MeetingIn(BaseModel):
    title: str = Field(min_length=3, max_length=220)
    date: str = ""
    time: str = ""
    place: str = ""
    participants: str = ""
    notes: str = ""
    discussions: list[str] = Field(default_factory=list)
    decisions: list[str] = Field(default_factory=list)
    tasks: list[dict] = Field(default_factory=list)
    status: str = "draft"

class LetterIn(BaseModel):
    kind: str = "Surat keluar"
    recipient: str = Field(min_length=2, max_length=300)
    subject: str = Field(min_length=3, max_length=300)
    instructions: str = ""
    signer: str = ""
    number: str = ""
    attachment: str = ""
    date: str = ""
    body: str = ""
    status: str = "draft"

@app.get("/api/health")
def health(db: Session = Depends(db_session)):
    db.query(func.count(User.id)).scalar()
    return {"ok": True, "service": "bpkr", "database": "postgresql", "version": "1.0.0"}

@app.post("/api/auth/login")
def login(data: LoginIn, response: Response, request: Request, db: Session = Depends(db_session)):
    ip = request.headers.get("cf-connecting-ip") or (request.client.host if request.client else "local")
    now = monotonic()
    failures = [t for t in LOGIN_FAILURES.get(ip, []) if now - t < 900]
    if len(failures) >= 20:
        raise HTTPException(429, "Terlalu banyak percobaan masuk. Coba kembali nanti")
    user = db.query(User).filter_by(username=data.username.strip().lower()).first()
    if not user or not user.is_active or not verify_password(data.password, user.password_hash):
        LOGIN_FAILURES[ip] = failures + [now]
        raise HTTPException(401, "Username atau kata sandi salah")
    LOGIN_FAILURES.pop(ip, None)
    token = create_token(user.id, user.password_hash[-20:])
    csrf = secrets.token_urlsafe(32)
    secure = os.environ.get("BPKR_COOKIE_SECURE", "1") == "1"
    response.set_cookie("bpkr_session", token, httponly=True, secure=secure, samesite="strict", max_age=28800, path="/")
    response.set_cookie("bpkr_csrf", csrf, httponly=False, secure=secure, samesite="strict", max_age=28800, path="/")
    return {"user": ser(user, USER_KEYS)}

@app.get("/api/auth/me")
def me(user: User = Depends(current_user)):
    return ser(user, USER_KEYS)

@app.post("/api/auth/change-password")
def change_password(data: PasswordIn, response: Response, user: User = Depends(current_user), db: Session = Depends(db_session)):
    if not verify_password(data.old_password, user.password_hash):
        raise HTTPException(400, "Kata sandi saat ini salah")
    if data.old_password == data.new_password:
        raise HTTPException(400, "Kata sandi baru harus berbeda")
    user.password_hash = hash_password(data.new_password)
    user.must_change_password = False
    track(db, user, "change_password", "users", user.id)
    db.commit()
    secure = os.environ.get("BPKR_COOKIE_SECURE", "1") == "1"
    response.set_cookie("bpkr_session", create_token(user.id, user.password_hash[-20:]), httponly=True, secure=secure, samesite="strict", max_age=28800, path="/")
    return {"ok": True}

@app.post("/api/auth/logout")
def logout(response: Response):
    response.delete_cookie("bpkr_session", path="/")
    response.delete_cookie("bpkr_csrf", path="/")
    return {"ok": True}

@app.get("/api/site")
def get_site(db: Session = Depends(db_session)):
    return {item.key: item.value for item in db.query(Setting).all()}

@app.put("/api/site")
def update_site(payload: dict, user: User = Depends(current_user), db: Session = Depends(db_session)):
    require(user, POWER)
    allowed = {"site_name", "tagline", "hero_title", "hero_description", "hero_image_1", "hero_image_2", "hero_slide_2_title", "hero_slide_2_description", "contact_email", "contact_phone", "contact_address", "footer_text", "menus"}
    for key, value in payload.items():
        if key not in allowed or not isinstance(value, str) or len(value) > 5000:
            raise HTTPException(422, "Field pengaturan tidak valid")
        if key == "menus":
            try:
                menus = json.loads(value)
                if not isinstance(menus, list) or len(menus) > 20:
                    raise ValueError("menu")
                for item in menus:
                    if not isinstance(item, dict) or not isinstance(item.get("title"), str):
                        raise ValueError("menu")
                    url = item.get("url")
                    if not isinstance(url, str) or not url.startswith("/") or url.startswith("//"):
                        raise ValueError("menu")
                    children = item.get("children", [])
                    if not isinstance(children, list) or len(children) > 20:
                        raise ValueError("menu")
                    for child in children:
                        if not isinstance(child, dict) or not isinstance(child.get("title"), str):
                            raise ValueError("menu")
                        child_url = child.get("url")
                        if not isinstance(child_url, str) or not child_url.startswith("/") or child_url.startswith("//"):
                            raise ValueError("menu")
            except (ValueError, TypeError, AttributeError):
                raise HTTPException(422, "Format navigasi harus berupa daftar URL internal")
        setting = db.get(Setting, key)
        if setting:
            setting.value = value
        else:
            db.add(Setting(key=key, value=value))
    track(db, user, "update", "settings")
    db.commit()
    return get_site(db)

@app.get("/api/posts")
def list_posts(q: str = "", category: str = "", all: bool = False, page: int = Query(1, ge=1), limit: int = Query(12, ge=1, le=60),
               db: Session = Depends(db_session), request: Request = None):
    query = db.query(Post)
    if all:
        try:
            user = current_user(request, db)
            require(user, EDITOR)
        except HTTPException:
            raise HTTPException(403, "Diperlukan izin editor")
    else:
        query = query.filter(Post.status == "published")
    if q:
        query = query.filter(or_(Post.title.ilike("%" + q + "%"), Post.excerpt.ilike("%" + q + "%")))
    if category:
        query = query.filter(Post.category == category)
    total = query.count()
    rows = query.order_by(Post.published_at.desc().nullslast(), Post.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    return {"items": [ser(x, POST_KEYS) for x in rows], "total": total, "page": page, "limit": limit}

@app.get("/api/posts/slug/{slug}")
def get_post_by_slug(slug: str, db: Session = Depends(db_session)):
    post = db.query(Post).filter_by(slug=slug, status="published").first()
    if not post:
        raise HTTPException(404, "Artikel tidak ditemukan")
    return ser(post, POST_KEYS)

def unique_slug(db: Session, proposed: str, exclude: int = None):
    base = slugify(proposed)
    slug = base
    i = 2
    while db.query(Post).filter(Post.slug == slug, *( [Post.id != exclude] if exclude else [] )).first():
        slug = base + "-" + str(i)
        i += 1
    return slug

def sanitize_post(data: PostIn):
    if data.type not in {"news", "page"} or data.status not in {"draft", "published", "archived"}:
        raise HTTPException(422, "Tipe/status konten tidak valid")
    return {
        "type": data.type, "title": data.title.strip(), "excerpt": data.excerpt[:800],
        "content": bleach.clean(data.content, tags=["p", "br", "h2", "h3", "h4", "b", "strong", "em", "i", "u", "a", "ul", "ol", "li", "blockquote", "figure", "figcaption", "img", "div", "span"],
            attributes={"a": ["href", "title", "rel"], "img": ["src", "alt", "loading"], "figure": ["class"], "div": ["class"], "span": ["class"]},
            protocols=["https", "http"], strip=True),
        "image_url": data.image_url[:1024], "category": data.category[:100], "tags": data.tags[:300],
        "seo_title": data.seo_title[:220], "seo_description": data.seo_description[:400], "status": data.status,
    }

@app.post("/api/posts")
def create_post(data: PostIn, background_tasks: BackgroundTasks, user: User = Depends(current_user), db: Session = Depends(db_session)):
    require(user, EDITOR)
    attrs = sanitize_post(data)
    row = Post(**attrs, slug=unique_slug(db, data.slug or data.title), author_id=user.id,
               published_at=utcnow() if data.status == "published" else None)
    db.add(row)
    db.flush()
    track(db, user, "create", "posts", row.id)
    db.commit()
    if row.status == "published":
        background_tasks.add_task(notify_indexnow, public_post_path(row))
    return ser(row, POST_KEYS)

@app.put("/api/posts/{post_id}")
def update_post(post_id: int, data: PostIn, background_tasks: BackgroundTasks, user: User = Depends(current_user), db: Session = Depends(db_session)):
    require(user, EDITOR)
    row = db.get(Post, post_id)
    if not row:
        raise HTTPException(404, "Artikel tidak ditemukan")
    previous_path = public_post_path(row) if row.status == "published" else None
    for k, v in sanitize_post(data).items():
        setattr(row, k, v)
    if data.slug and slugify(data.slug) != row.slug:
        row.slug = unique_slug(db, data.slug, row.id)
    if data.status == "published" and not row.published_at:
        row.published_at = utcnow()
    track(db, user, "update", "posts", row.id)
    db.commit()
    current_path = public_post_path(row) if row.status == "published" else None
    if previous_path and previous_path != current_path:
        background_tasks.add_task(notify_indexnow, previous_path)
    if current_path:
        background_tasks.add_task(notify_indexnow, current_path)
    return ser(row, POST_KEYS)

@app.delete("/api/posts/{post_id}")
def delete_post(post_id: int, background_tasks: BackgroundTasks, user: User = Depends(current_user), db: Session = Depends(db_session)):
    require(user, EDITOR)
    row = db.get(Post, post_id)
    if not row:
        raise HTTPException(404, "Artikel tidak ditemukan")
    removed_path = public_post_path(row) if row.status == "published" else None
    db.delete(row)
    track(db, user, "delete", "posts", post_id)
    db.commit()
    if removed_path:
        background_tasks.add_task(notify_indexnow, removed_path)
    return {"ok": True}

@app.post("/api/media")
async def upload_media(file: UploadFile = File(...), user: User = Depends(current_user)):
    require(user, EDITOR)
    allowed = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "image/gif": ".gif"}
    if file.content_type not in allowed:
        raise HTTPException(415, "Hanya gambar JPG, PNG, WEBP, GIF")
    raw = await file.read(5 * 1024 * 1024 + 1)
    if len(raw) > 5 * 1024 * 1024:
        raise HTTPException(413, "Maksimal 5 MB")
    # Pemeriksaan signature mencegah file non-gambar diunggah sebagai gambar.
    if not (raw.startswith(b"\xff\xd8\xff") or raw.startswith(b"\x89PNG\r\n\x1a\n") or raw.startswith(b"GIF8") or (len(raw) > 12 and raw[:4] == b"RIFF" and raw[8:12] == b"WEBP")):
        raise HTTPException(415, "Konten gambar tidak valid")
    name = secrets.token_hex(16) + allowed[file.content_type]
    (UPLOADS / name).write_bytes(raw)
    return {"url": "/media/" + name}

@app.get("/api/users")
def list_users(user: User = Depends(current_user), db: Session = Depends(db_session)):
    require(user, POWER)
    return [ser(x, USER_KEYS) for x in db.query(User).order_by(User.id).all()]

@app.post("/api/users")
def create_user(data: UserIn, user: User = Depends(current_user), db: Session = Depends(db_session)):
    require(user, POWER)
    if data.role not in ROLES or (data.role == "superadmin" and user.role != "superadmin"):
        raise HTTPException(403, "Tidak dapat menetapkan role ini")
    if len(data.password) < 12:
        raise HTTPException(422, "Kata sandi minimal 12 karakter")
    if db.query(User).filter_by(username=data.username.lower()).first():
        raise HTTPException(409, "Username sudah terpakai")
    row = User(username=data.username.lower(), full_name=data.full_name, email=data.email or None, role=data.role,
               password_hash=hash_password(data.password), is_active=data.is_active, must_change_password=True)
    db.add(row)
    db.flush()
    track(db, user, "create", "users", row.id)
    db.commit()
    return ser(row, USER_KEYS)

@app.put("/api/users/{user_id}")
def update_user(user_id: int, data: UserIn, user: User = Depends(current_user), db: Session = Depends(db_session)):
    require(user, POWER)
    row = db.get(User, user_id)
    if not row:
        raise HTTPException(404, "Pengguna tidak ditemukan")
    if data.role not in ROLES:
        raise HTTPException(422, "Role tidak valid")
    if (row.role == "superadmin" or data.role == "superadmin") and user.role != "superadmin":
        raise HTTPException(403, "Role superadmin dilindungi")
    if user.id == row.id and not data.is_active:
        raise HTTPException(400, "Tidak boleh menonaktifkan akun sendiri")
    duplicate = db.query(User).filter(User.username == data.username.lower(), User.id != user_id).first()
    if duplicate:
        raise HTTPException(409, "Username sudah digunakan")
    for key, value in {"username": data.username.lower(), "full_name": data.full_name, "email": data.email or None, "role": data.role, "is_active": data.is_active}.items():
        setattr(row, key, value)
    if data.password.strip():
        if len(data.password) < 12:
            raise HTTPException(422, "Kata sandi minimal 12 karakter")
        row.password_hash = hash_password(data.password)
        row.must_change_password = True
    track(db, user, "update", "users", row.id)
    db.commit()
    return ser(row, USER_KEYS)

def verify_module(module: str, role: str, write=False):
    matrix = MODULE_EDITORS if write else MODULE_PERMISSIONS
    if module not in matrix:
        raise HTTPException(404, "Modul tidak tersedia")
    if role not in matrix[module]:
        raise HTTPException(403, "Tidak ada akses ke modul")

@app.get("/api/modules")
def get_modules(user: User = Depends(current_user)):
    return [{"key": m, "can_write": user.role in MODULE_EDITORS[m]} for m in MODULE_PERMISSIONS if user.role in MODULE_PERMISSIONS[m]]

@app.get("/api/entries")
def list_entries(module: str, q: str = "", user: User = Depends(current_user), db: Session = Depends(db_session)):
    verify_module(module, user.role)
    query = db.query(Entry).filter(Entry.module == module)
    if q:
        query = query.filter(Entry.title.ilike("%" + q + "%"))
    if user.role == "mahasiswa":
        query = query.filter(Entry.created_by == user.id)
    return [ser(x, ENTRY_KEYS) for x in query.order_by(Entry.created_at.desc()).limit(200).all()]

@app.post("/api/entries")
def create_entry(data: EntryIn, user: User = Depends(current_user), db: Session = Depends(db_session)):
    verify_module(data.module, user.role, True)
    if user.role == "mahasiswa" and data.status != "baru":
        raise HTTPException(403, "Pengajuan mahasiswa harus dimulai dengan status baru")
    row = Entry(**data.model_dump(), created_by=user.id)
    db.add(row)
    db.flush()
    track(db, user, "create", data.module, row.id)
    db.commit()
    return ser(row, ENTRY_KEYS)

@app.put("/api/entries/{entry_id}")
def update_entry(entry_id: int, data: EntryIn, user: User = Depends(current_user), db: Session = Depends(db_session)):
    row = db.get(Entry, entry_id)
    if not row:
        raise HTTPException(404, "Data tidak ditemukan")
    verify_module(row.module, user.role, True)
    if user.role == "mahasiswa" and (row.created_by != user.id or row.status != "baru" or data.status != "baru"):
        raise HTTPException(403, "Mahasiswa hanya dapat mengubah pengajuannya sendiri yang belum diproses")
    if data.module != row.module:
        raise HTTPException(422, "Modul tidak boleh diubah")
    for key, value in data.model_dump().items():
        setattr(row, key, value)
    track(db, user, "update", row.module, row.id)
    db.commit()
    return ser(row, ENTRY_KEYS)

@app.delete("/api/entries/{entry_id}")
def delete_entry(entry_id: int, user: User = Depends(current_user), db: Session = Depends(db_session)):
    row = db.get(Entry, entry_id)
    if not row:
        raise HTTPException(404, "Data tidak ditemukan")
    verify_module(row.module, user.role, True)
    if user.role == "mahasiswa" and (row.created_by != user.id or row.status != "baru"):
        raise HTTPException(403, "Mahasiswa hanya dapat menghapus pengajuannya sendiri yang belum diproses")
    track(db, user, "delete", row.module, row.id)
    db.delete(row)
    db.commit()
    return {"ok": True}

@app.post("/api/meetings/parse")
def parse_meeting(payload: dict, user: User = Depends(current_user)):
    require(user, MEETING_EDITORS)
    return parse_meeting_notes(str(payload.get("notes", ""))[:100000])

@app.get("/api/meetings")
def list_meetings(user: User = Depends(current_user), db: Session = Depends(db_session)):
    require(user, MEETING_READERS)
    return [ser(x, MEETING_KEYS) for x in db.query(Meeting).order_by(Meeting.created_at.desc()).limit(150).all()]

@app.post("/api/meetings")
def create_meeting(data: MeetingIn, user: User = Depends(current_user), db: Session = Depends(db_session)):
    require(user, MEETING_EDITORS)
    if data.status not in {"draft", "review", "approved"}:
        raise HTTPException(422, "Status rapat tidak valid")
    if data.status == "approved":
        require(user, APPROVERS)
    payload = data.model_dump()
    if not payload["decisions"] and not payload["tasks"] and payload["notes"]:
        payload.update(parse_meeting_notes(payload["notes"]))
    row = Meeting(**payload, created_by=user.id)
    db.add(row)
    db.flush()
    track(db, user, "create", "meetings", row.id)
    db.commit()
    return ser(row, MEETING_KEYS)

@app.put("/api/meetings/{meeting_id}")
def update_meeting(meeting_id: int, data: MeetingIn, user: User = Depends(current_user), db: Session = Depends(db_session)):
    require(user, MEETING_EDITORS)
    if data.status not in {"draft", "review", "approved"}:
        raise HTTPException(422, "Status rapat tidak valid")
    if data.status == "approved":
        require(user, APPROVERS)
    row = db.get(Meeting, meeting_id)
    if not row:
        raise HTTPException(404, "Rapat tidak ditemukan")
    if row.status == "approved":
        require(user, APPROVERS)
    for k, v in data.model_dump().items():
        setattr(row, k, v)
    track(db, user, "update", "meetings", row.id)
    db.commit()
    return ser(row, MEETING_KEYS)

@app.delete("/api/meetings/{meeting_id}")
def delete_meeting(meeting_id: int, user: User = Depends(current_user), db: Session = Depends(db_session)):
    require(user, MEETING_EDITORS)
    row = db.get(Meeting, meeting_id)
    if not row:
        raise HTTPException(404, "Rapat tidak ditemukan")
    db.delete(row)
    track(db, user, "delete", "meetings", meeting_id)
    db.commit()
    return {"ok": True}

@app.get("/api/letters")
def list_letters(user: User = Depends(current_user), db: Session = Depends(db_session)):
    query = db.query(Letter)
    if user.role not in LETTER_EDITORS:
        query = query.filter(Letter.created_by == user.id)
    return [ser(x, LETTER_KEYS) for x in query.order_by(Letter.created_at.desc()).limit(150).all()]

@app.post("/api/letters")
def create_letter(data: LetterIn, user: User = Depends(current_user), db: Session = Depends(db_session)):
    require(user, LETTER_EDITORS)
    if data.status not in {"draft", "review", "approved"}:
        raise HTTPException(422, "Status surat tidak valid")
    if data.status == "approved":
        require(user, APPROVERS)
    payload = data.model_dump()
    if not payload["body"]:
        payload["body"] = letter_body(data.kind, data.recipient, data.subject, data.instructions, data.signer, data.date, data.number, data.attachment)
    row = Letter(**payload, created_by=user.id)
    db.add(row)
    db.flush()
    track(db, user, "create", "letters", row.id)
    db.commit()
    return ser(row, LETTER_KEYS)

@app.put("/api/letters/{letter_id}")
def update_letter(letter_id: int, data: LetterIn, user: User = Depends(current_user), db: Session = Depends(db_session)):
    require(user, LETTER_EDITORS)
    if data.status not in {"draft", "review", "approved"}:
        raise HTTPException(422, "Status surat tidak valid")
    if data.status == "approved":
        require(user, APPROVERS)
    row = db.get(Letter, letter_id)
    if not row:
        raise HTTPException(404, "Surat tidak ditemukan")
    if row.status == "approved":
        require(user, APPROVERS)
    payload = data.model_dump()
    if not payload["body"]:
        payload["body"] = letter_body(data.kind, data.recipient, data.subject, data.instructions, data.signer, data.date, data.number, data.attachment)
    for k, v in payload.items():
        setattr(row, k, v)
    track(db, user, "update", "letters", row.id)
    db.commit()
    return ser(row, LETTER_KEYS)

@app.delete("/api/letters/{letter_id}")
def delete_letter(letter_id: int, user: User = Depends(current_user), db: Session = Depends(db_session)):
    require(user, LETTER_EDITORS)
    row = db.get(Letter, letter_id)
    if not row:
        raise HTTPException(404, "Surat tidak ditemukan")
    db.delete(row)
    track(db, user, "delete", "letters", letter_id)
    db.commit()
    return {"ok": True}

@app.get("/api/dashboard")
def dashboard(user: User = Depends(current_user), db: Session = Depends(db_session)):
    accessible = [k for k in MODULE_PERMISSIONS if user.role in MODULE_PERMISSIONS[k]]
    counts = {k: db.query(func.count(Entry.id)).filter(Entry.module == k).scalar() for k in accessible}
    meetings = db.query(func.count(Meeting.id)).scalar()
    letters = db.query(func.count(Letter.id)).scalar() if user.role in LETTER_EDITORS else 0
    published = db.query(func.count(Post.id)).filter(Post.status == "published").scalar()
    recent = db.query(Entry).filter(Entry.module.in_(accessible)).order_by(Entry.created_at.desc()).limit(6).all()
    return {"role": user.role, "modules": counts, "meetings": meetings, "letters": letters, "news": published,
            "recent": [ser(x, ENTRY_KEYS) for x in recent]}

@app.get("/api/audit")
def audit(user: User = Depends(current_user), db: Session = Depends(db_session)):
    require(user, POWER)
    return [ser(x, ("id", "actor_id", "action", "entity", "entity_id", "at")) for x in db.query(AuditLog).order_by(AuditLog.id.desc()).limit(150).all()]

def absolute_url(path: str) -> str:
    if path.startswith("https://") or path.startswith("http://"):
        return path
    return BASE_URL + (path if path.startswith("/") else "/" + path)


def public_post_path(post: Post) -> str:
    if post.type == "page":
        return "/halaman/" + post.slug
    if "artikel" in (post.category or "").lower():
        return "/artikel/" + post.slug
    return "/berita/" + post.slug

def notify_indexnow(path: str):
    """Notify IndexNow participants after publishing, updating or removing public content."""
    key = os.environ.get("BPKR_INDEXNOW_KEY", "").strip()
    if not key:
        return
    from urllib.request import Request as UrlRequest, urlopen
    import logging

    url = absolute_url(path)
    payload = json.dumps({"host": "bpkr.otomasi.app", "key": key,
                          "keyLocation": BASE_URL + "/indexnow-key.txt",
                          "urlList": [url]}).encode("utf-8")
    req = UrlRequest("https://api.indexnow.org/indexnow", data=payload,
                     headers={"Content-Type": "application/json; charset=utf-8"},
                     method="POST")
    try:
        with urlopen(req, timeout=8) as response:
            if response.status not in {200, 202}:
                logging.warning("IndexNow response HTTP %s", response.status)
    except Exception as exc:
        logging.warning("IndexNow notification failed: %s", type(exc).__name__)


@app.get("/indexnow-key.txt", response_class=PlainTextResponse, include_in_schema=False)
def indexnow_key():
    key = os.environ.get("BPKR_INDEXNOW_KEY", "").strip()
    if not key:
        raise HTTPException(404, "IndexNow belum dikonfigurasi")
    return PlainTextResponse(key, headers={"Cache-Control": "public, max-age=3600"})


@app.get("/robots.txt", response_class=PlainTextResponse)
def robots():
    return "User-agent: *\nAllow: /\nDisallow: /dashboard\nDisallow: /login\nDisallow: /api/\nSitemap: " + BASE_URL + "/sitemap.xml\n"

@app.get("/sitemap.xml")
def sitemap(db: Session = Depends(db_session)):
    posts = db.query(Post).filter_by(status="published").order_by(Post.updated_at.desc()).all()
    public_pages = ["/", "/berita", "/artikel", "/tentang", "/visi-misi",
                    "/struktur", "/pimpinan", "/sejarah", "/pengembangan",
                    "/program-studi", "/layanan", "/kontak"]
    paths = [(item, None) for item in public_pages]
    paths += [(public_post_path(p), p.updated_at or p.published_at or p.created_at)
              for p in posts]
    items = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for path, lastmod in paths:
        items.append("<url><loc>" + escape(BASE_URL + path) + "</loc>"
                     + ("<lastmod>" + lastmod.date().isoformat() + "</lastmod>" if lastmod else "")
                     + "</url>")
    items.append("</urlset>")
    return Response("".join(items), media_type="application/xml",
                    headers={"Cache-Control": "public, max-age=300"})


@app.get("/feed.xml", include_in_schema=False)
def feed(db: Session = Depends(db_session)):
    from email.utils import format_datetime
    from datetime import timezone

    posts = (db.query(Post).filter_by(type="news", status="published")
             .order_by(Post.published_at.desc()).limit(30).all())
    items = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<rss version="2.0"><channel>',
             '<title>BPKR Kampus Rembang — Universitas Diponegoro</title>',
             '<link>' + escape(BASE_URL) + '</link>',
             '<description>Berita dan publikasi Badan Pengelola Kampus Rembang UNDIP</description>',
             '<language>id-id</language>']
    for post in posts:
        link = BASE_URL + public_post_path(post)
        date = post.published_at or post.created_at
        if date.tzinfo is None:
            date = date.replace(tzinfo=timezone.utc)
        items += ["<item><title>" + escape(post.title) + "</title>",
                  "<link>" + escape(link) + "</link>",
                  "<guid isPermaLink=\"true\">" + escape(link) + "</guid>",
                  "<description>" + escape(post.excerpt or post.title) + "</description>",
                  "<pubDate>" + format_datetime(date) + "</pubDate></item>"]
    items.append("</channel></rss>")
    return Response("".join(items), media_type="application/rss+xml",
                    headers={"Cache-Control": "public, max-age=300"})


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/images/undip-logo.png", status_code=301)

def render_article(post: Post):
    title = escape(post.seo_title or post.title)
    desc = escape(post.seo_description or post.excerpt or post.title)
    img = escape(absolute_url(post.image_url or "/images/kampus-rembang.jpg"))
    link = absolute_url(public_post_path(post))
    structured = json.dumps({"@context": "https://schema.org", "@type": "NewsArticle" if post.type == "news" else "WebPage",
                             "headline": post.title, "description": post.seo_description or post.excerpt,
                             "datePublished": (post.published_at or post.created_at).isoformat(),
                             "dateModified": (post.updated_at or post.created_at).isoformat(),
                             "mainEntityOfPage": link, "inLanguage": "id-ID",
                             "publisher": {"@type": "Organization", "name": "Badan Pengelola Kampus Rembang - Universitas Diponegoro",
                                           "url": BASE_URL, "logo": {"@type": "ImageObject", "url": BASE_URL + "/images/undip-logo.png"}},
                             "image": [absolute_url(post.image_url or "/images/kampus-rembang.jpg")]},
                            ensure_ascii=False).replace("<", "\\u003c")
    from urllib.parse import quote
    share_link = quote(link, safe="")
    share_title = quote(post.title, safe="")
    share_nav = (
        '<nav class="share-buttons" aria-label="Bagikan artikel">'
        '<strong>Bagikan artikel:</strong>'
        '<a target="_blank" rel="noopener noreferrer" href="https://wa.me/?text=' +
        share_title + '%20' + share_link + '">WhatsApp</a>'
        '<a target="_blank" rel="noopener noreferrer" href="https://www.facebook.com/sharer/sharer.php?u=' +
        share_link + '">Facebook</a>'
        '<a target="_blank" rel="noopener noreferrer" href="https://www.linkedin.com/sharing/share-offsite/?url=' +
        share_link + '">LinkedIn</a>'
        '<a target="_blank" rel="noopener noreferrer" href="https://twitter.com/intent/tweet?url=' +
        share_link + '&text=' + share_title + '">X</a>'
        '</nav>'
    )
    body = post.content
    return HTMLResponse(f"""<!doctype html><html lang="id"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} | BPKR UNDIP</title><meta name="description" content="{desc}"><link rel="canonical" href="{escape(link)}">
<meta property="og:type" content="article"><meta property="og:title" content="{title}"><meta property="og:description" content="{desc}">
<meta property="og:url" content="{escape(link)}"><meta property="og:image" content="{img}">
<meta property="og:site_name" content="BPKR Kampus Rembang UNDIP"><meta property="og:locale" content="id_ID">
<meta property="og:image:alt" content="{escape(post.title)}">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{desc}"><meta name="twitter:image" content="{img}">
<link rel="alternate" type="application/rss+xml" title="Berita BPKR" href="/feed.xml">
<script type="application/ld+json">{structured}</script>
<style>body{{margin:0;background:#f7f9fd;color:#183657;font:16px/1.85 system-ui,Arial,sans-serif}}*{{box-sizing:border-box}}a{{color:#0a4e94;text-decoration:none}}header{{height:88px;background:white;padding:0 max(20px,5%);display:flex;align-items:center;justify-content:space-between;gap:20px;border-bottom:1px solid #e1e8f2;position:relative;z-index:2}}header a.brand{{display:flex;align-items:center;gap:13px;color:#07366b;line-height:1.25;font-size:16px}}header img{{width:45px;height:56px;object-fit:contain}}header b,header small{{display:block}}header small{{color:#5c7290;font-size:12px;font-weight:600}}header nav{{display:flex;gap:22px;font-size:13px;font-weight:800}}.article-banner{{height:260px;background:linear-gradient(90deg,#063569ed,#07366b7d),url('/images/kampus-rembang.jpg') center 45%/cover no-repeat;position:relative;border-bottom:6px solid #ffca27}}.article-banner span{{position:absolute;top:78px;left:max(20px,calc((100% - 1040px)/2));color:#ffca27;letter-spacing:2px;font-size:12px;font-weight:800}}main{{position:relative;max-width:960px;margin:-86px auto 50px;background:white;padding:clamp(24px,5vw,65px);border-radius:16px;box-shadow:0 13px 45px #0d35601a}}main>small{{color:#0b5699;font-weight:800;letter-spacing:1px;font-size:11px}}h1{{font-size:clamp(29px,4vw,48px);line-height:1.24;letter-spacing:-.04em;color:#092f60;margin:17px 0}}.meta{{color:#667b95;font-size:13px;border-bottom:1px solid #e1e9f3;padding-bottom:22px}}.hero{{width:100%;max-height:470px;object-fit:cover;border-radius:12px;margin:22px 0}}.article img{{max-width:100%;height:auto}}.article{{overflow-wrap:anywhere}}.article h2,.article h3{{color:#07366b}}main>p:last-child{{margin-top:32px;border-top:1px solid #e0e8f2;padding-top:19px;font-weight:800}}footer{{text-align:center;background:#07366b;padding:25px;color:#d8e7f7;font-size:12px}}@media(max-width:700px){{header{{height:74px;padding:0 16px}}header a.brand{{font-size:12px}}header img{{width:38px;height:46px}}header nav{{gap:12px;font-size:11px}}.article-banner{{height:180px}}.article-banner span{{left:20px;top:45px}}main{{margin:-45px 13px 25px}}}}.share-buttons{{display:flex;flex-wrap:wrap;align-items:center;gap:10px;margin:28px 0;padding:20px 0;border-top:1px solid #e0e8f2;border-bottom:1px solid #e0e8f2}}
.share-buttons strong{{font-size:14px;margin-right:8px}}
.share-buttons a{{display:inline-block;border:1px solid #b6c7dd;border-radius:8px;padding:6px 12px;font-size:13px;font-weight:700}}
.share-buttons a:hover{{background:#eef4fc}}</style>
</head><body><header><a class="brand" href="/"><img src="/images/undip-logo.png" alt="Lambang Universitas Diponegoro"><span><b>UNIVERSITAS DIPONEGORO</b><small>Kampus Rembang · BPKR</small></span></a><nav><a href="/">Beranda</a><a href="/berita">Berita</a></nav></header><div class="article-banner"><span>BPKR · PUBLIKASI KAMPUS REMBANG</span></div><main><small>{escape(post.category)}</small><h1>{escape(post.title)}</h1><p class="meta">{(post.published_at or post.created_at).strftime("%d %B %Y")}</p>
{('<img class="hero" alt="' + escape(post.title) + '" src="' + escape(post.image_url) + '">') if post.image_url else ''}
<article class="article">{body}</article>{share_nav}<p><a href="/berita">← Kembali ke berita</a></p></main><footer>Badan Pengelola Kampus Rembang · Universitas Diponegoro</footer></body></html>""")


def render_reflective_article(post: Post):
    from urllib.parse import quote

    link = absolute_url("/artikel/" + post.slug)
    title = escape(post.seo_title or post.title)
    desc = escape(post.seo_description or post.excerpt or post.title)
    cover = escape(absolute_url(post.image_url or "/images/kampus-rembang-2.jpg"))
    date = post.published_at or post.created_at
    months = ("Januari", "Februari", "Maret", "April", "Mei", "Juni",
              "Juli", "Agustus", "September", "Oktober", "November", "Desember")
    display_date = f"{date.day} {months[date.month - 1]} {date.year}"
    share_link = quote(link, safe="")
    share_title = quote(post.title + " " + link, safe="")
    structured = json.dumps({
        "@context": "https://schema.org", "@type": "Article",
        "headline": post.title, "description": post.seo_description or post.excerpt,
        "datePublished": date.isoformat(),
        "dateModified": (post.updated_at or date).isoformat(),
        "mainEntityOfPage": link, "inLanguage": "id-ID",
        "publisher": {"@type": "Organization", "name": "Badan Pengelola Kampus Rembang - Universitas Diponegoro",
                      "url": BASE_URL, "logo": {"@type": "ImageObject", "url": BASE_URL + "/images/undip-logo.png"}},
        "image": [absolute_url(post.image_url or "/images/kampus-rembang-2.jpg")]
    }, ensure_ascii=False).replace("<", "\\u003c")
    return HTMLResponse(f"""<!doctype html>
<html lang="id"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} | BPKR UNDIP</title><meta name="description" content="{desc}"><link rel="canonical" href="{escape(link)}">
<meta property="og:type" content="article"><meta property="og:locale" content="id_ID"><meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}"><meta property="og:image" content="{cover}"><meta property="og:url" content="{escape(link)}">
<meta name="twitter:card" content="summary_large_image"><link rel="icon" href="/images/undip-logo.png">
<script type="application/ld+json">{structured}</script><link rel="stylesheet" href="/design/reflective-article.css"></head>
<body><header><a class="header-brand" href="/"><img src="/images/undip-logo.png" alt="Logo UNDIP"><span>UNIVERSITAS<br>DIPONEGORO</span><span class="divider"></span><span>Kampus<br><small>Rembang</small></span></a>
<nav><a href="/">Beranda</a><a href="/tentang">Tentang BPKR</a><a class="active" href="/artikel">Artikel</a><a href="/berita">Berita</a><a href="/kontak">Kontak</a></nav></header>
<section class="cover"><div class="cover-inner"><span class="cover-kicker">ARTIKEL REFLEKTIF</span><h1>{escape(post.title)}</h1><span class="cover-rule"></span></div></section>
<div class="meta-wrap"><div class="meta"><span>▦ &nbsp; {display_date}</span><span>◇ &nbsp; Artikel Reflektif</span><span>▤ &nbsp; Badan Pengelola Kampus Rembang (BPKR)</span>
<div class="shares"><strong>Bagikan:</strong><a href="https://www.linkedin.com/sharing/share-offsite/?url={share_link}" target="_blank" rel="noopener noreferrer">LinkedIn</a><a href="https://api.whatsapp.com/send?text={share_title}" target="_blank" rel="noopener noreferrer">WhatsApp</a><a href="https://www.facebook.com/sharer/sharer.php?u={share_link}" target="_blank" rel="noopener noreferrer">Facebook</a></div></div></div>
<div class="page-layout"><aside><div class="leader-profile"><img src="/images/prof-budiyono.jpg" alt="Foto Prof. Dr. Ir. Budiyono, M.Si." loading="eager">
<div class="leader-caption"><strong>Prof. Dr. Ir. Budiyono, M.Si.</strong><span>Kepala Badan Pengelola Kampus Rembang (BPKR)<br>Universitas Diponegoro</span></div></div>
<div class="aside-vision"><div class="quote-mark">“</div><small>Visi BPKR</small><p>Mewujudkan Kampus Rembang UNDIP yang unggul dalam tata kelola, inovatif, dan berkelanjutan untuk menghadirkan dampak nyata bagi masyarakat.</p><span class="quote-rule"></span></div></aside>
<main><article class="article">{post.content}</article><a class="back-link" href="/artikel">← Kembali ke daftar artikel</a></main></div>
<footer>Badan Pengelola Kampus Rembang · Universitas Diponegoro<br>Jalan Sawah, Desa Turus Gede, Kecamatan Rembang, Kabupaten Rembang, Jawa Tengah 59219</footer></body></html>""")


@app.get("/artikel/{slug}", response_class=HTMLResponse)
def reflective_article(slug: str, db: Session = Depends(db_session)):
    post = db.query(Post).filter_by(slug=slug, type="news", status="published").first()
    if not post or "artikel" not in post.category.lower():
        raise HTTPException(404, "Artikel tidak ditemukan")
    return render_reflective_article(post)

@app.get("/berita/{slug}", response_class=HTMLResponse)
def article(slug: str, db: Session = Depends(db_session)):
    post = db.query(Post).filter_by(slug=slug, type="news", status="published").first()
    if not post:
        raise HTTPException(404, "Berita tidak ditemukan")
    return render_article(post)

@app.get("/halaman/{slug}", response_class=HTMLResponse)
def page(slug: str, db: Session = Depends(db_session)):
    post = db.query(Post).filter_by(slug=slug, type="page", status="published").first()
    if not post:
        raise HTTPException(404, "Halaman tidak ditemukan")
    return render_article(post)

app.mount("/media", StaticFiles(directory=str(UPLOADS)), name="media")
if (STATIC / "design").exists():
    app.mount("/design", StaticFiles(directory=str(STATIC / "design")), name="design")
if (STATIC / "images").exists():
    app.mount("/images", StaticFiles(directory=str(STATIC / "images")), name="images")
if (STATIC / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(STATIC / "assets")), name="assets")

@app.get("/llms.txt", response_class=PlainTextResponse, include_in_schema=False)
def llms_txt():
    return ("# BPKR — Badan Pengelola Kampus Rembang, Universitas Diponegoro\n"
            "Portal berita, layanan kampus, kerja sama, fasilitas, dan kegiatan akademik.\n"
            "Sumber informasi resmi: " + BASE_URL + "\n"
            "Berita dan publikasi: " + BASE_URL + "/berita\n"
            "Daftar URL: " + BASE_URL + "/sitemap.xml\n"
            "Halaman publik dapat dikutip dengan menyebut sumber BPKR.\n"
            "Konten dashboard dan API privat tidak tersedia bagi publik.\n")

@app.api_route("/{path:path}", methods=["GET", "HEAD"], include_in_schema=False)
def spa(path: str, request: Request, db: Session = Depends(db_session)):
    if path.startswith(("api/", "media/", "assets/", "images/", "design/")):
        raise HTTPException(404, "Rute tidak tersedia")
    index = STATIC / "index.html"
    if not index.exists():
        return HTMLResponse("<h1>BPKR frontend belum dibangun</h1>", status_code=503)
    if request.method == "HEAD":
        return Response(status_code=200, media_type="text/html")
    html = index.read_text(encoding="utf-8")
    if path in {"", "berita", "artikel", "tentang", "visi-misi", "struktur",
                "pimpinan", "sejarah", "pengembangan", "program-studi",
                "layanan", "kontak"}:
        headings = {
            "": ("BPKR Kampus Rembang UNDIP | Berita, Layanan dan Kolaborasi", "Portal informasi, berita, layanan, dan kolaborasi Badan Pengelola Kampus Rembang Universitas Diponegoro."),
            "berita": ("Berita BPKR Kampus Rembang | UNDIP", "Berita dan informasi resmi terbaru seputar kegiatan, layanan, dan perkembangan Kampus Rembang UNDIP."),
            "artikel": ("Artikel BPKR Kampus Rembang | UNDIP", "Artikel dan wawasan tentang tata kelola, pendidikan, inovasi, dan pengembangan Kampus Rembang UNDIP."),
            "visi-misi": ("Visi dan Misi BPKR | Kampus Rembang UNDIP", "Visi, misi, tata kelola dan arah pengembangan Badan Pengelola Kampus Rembang UNDIP."),
            "struktur": ("Struktur Organisasi BPKR | UNDIP", "Informasi organisasi dan tata kelola Badan Pengelola Kampus Rembang Universitas Diponegoro."),
            "pimpinan": ("Pimpinan BPKR Kampus Rembang | UNDIP", "Profil pimpinan dan pengelola Kampus Rembang Universitas Diponegoro."),
            "sejarah": ("Sejarah Kampus Rembang | Universitas Diponegoro", "Sejarah dan perkembangan Kampus Rembang Universitas Diponegoro."),
            "pengembangan": ("Arah Pengembangan Kampus Rembang | UNDIP", "Pengembangan tata kelola digital, akademik, kemitraan dan keberlanjutan Kampus Rembang."),
            "program-studi": ("Program Studi Kampus Rembang | UNDIP", "Informasi program studi dan pendidikan tinggi di Kampus Rembang Universitas Diponegoro."),
            "tentang": ("Tentang BPKR | Kampus Rembang UNDIP", "Kenali peran dan layanan Badan Pengelola Kampus Rembang Universitas Diponegoro."),
            "layanan": ("Layanan BPKR | Akademik, Fasilitas dan Kemitraan", "Informasi layanan administrasi, akademik, fasilitas, laboratorium, dan kemitraan BPKR UNDIP."),
            "kontak": ("Hubungi BPKR Kampus Rembang", "Informasi alamat dan kontak Badan Pengelola Kampus Rembang Universitas Diponegoro."),
        }
        title, desc = headings[path]
        canonical = BASE_URL + ("/" + path if path else "/")
        html = html.replace("<title>BPKR · Kampus Rembang UNDIP</title>", "<title>" + escape(title) + "</title>")
        html = html.replace('<meta name="description" content="Portal berita, layanan, dan kolaborasi Badan Pengelola Kampus Rembang Universitas Diponegoro.">',
                            '<meta name="description" content="' + escape(desc) + '">')
        html = html.replace('href="https://bpkr.otomasi.app/"', 'href="' + escape(canonical) + '"')
        image_url = BASE_URL + "/images/kampus-rembang.jpg"
        page_type = "CollectionPage" if path in {"berita", "artikel"} else "WebPage"
        website_schema = {
            "@context": "https://schema.org",
            "@graph": [
                {"@type": "Organization", "@id": BASE_URL + "/#organization",
                 "name": "Badan Pengelola Kampus Rembang - Universitas Diponegoro",
                 "alternateName": "BPKR UNDIP", "url": BASE_URL,
                 "logo": BASE_URL + "/images/undip-logo.png",
                 "parentOrganization": {"@type": "CollegeOrUniversity",
                                        "name": "Universitas Diponegoro",
                                        "url": "https://undip.ac.id/"}},
                {"@type": "WebSite", "@id": BASE_URL + "/#website",
                 "name": "BPKR Kampus Rembang UNDIP", "url": BASE_URL,
                 "inLanguage": "id-ID", "publisher": {"@id": BASE_URL + "/#organization"}},
                {"@type": page_type, "@id": canonical + "#webpage",
                 "name": title, "description": desc, "url": canonical,
                 "inLanguage": "id-ID", "isPartOf": {"@id": BASE_URL + "/#website"}}
            ]
        }
        schema_json = json.dumps(website_schema, ensure_ascii=False).replace("<", r"\u003c")
        social = ('<meta property="og:type" content="website">'
                  '<meta property="og:site_name" content="BPKR Kampus Rembang UNDIP">'
                  '<meta property="og:locale" content="id_ID">'
                  '<meta property="og:title" content="' + escape(title) + '">'
                  '<meta property="og:description" content="' + escape(desc) + '">'
                  '<meta property="og:url" content="' + escape(canonical) + '">'
                  '<meta property="og:image" content="' + escape(image_url) + '">'
                  '<meta property="og:image:alt" content="Kampus Rembang Universitas Diponegoro">'
                  '<meta name="twitter:card" content="summary_large_image">'
                  '<meta name="twitter:title" content="' + escape(title) + '">'
                  '<meta name="twitter:description" content="' + escape(desc) + '">'
                  '<meta name="twitter:image" content="' + escape(image_url) + '">'
                  '<link rel="alternate" type="application/rss+xml" title="Berita BPKR" href="/feed.xml">'
                  '<script type="application/ld+json">' + schema_json + '</script>')
        html = html.replace("</head>", social + "</head>")
        title_html = '<h1>' + escape(title) + '</h1>'
        nav_html = ('<nav aria-label="Navigasi publik">'
                    '<a href="/">Beranda</a> | <a href="/berita">Berita</a> | '
                    '<a href="/artikel">Artikel</a> | <a href="/tentang">Tentang BPKR</a> | '
                    '<a href="/visi-misi">Visi dan Misi</a> | <a href="/struktur">Struktur</a> | '
                    '<a href="/pimpinan">Pimpinan</a> | <a href="/pengembangan">Pengembangan</a> | '
                    '<a href="/sejarah">Sejarah</a> | <a href="/program-studi">Program Studi</a> | '
                    '<a href="/layanan">Layanan</a> | <a href="/kontak">Kontak</a></nav>')
        links = ""
        if path in {"", "berita", "artikel"}:
            stories_query = db.query(Post).filter_by(type="news", status="published")
            if path == "artikel":
                stories_query = stories_query.filter(Post.category.ilike("%artikel%"))
            elif path == "berita":
                stories_query = stories_query.filter(~Post.category.ilike("%artikel%"))
            stories = stories_query.order_by(Post.published_at.desc()).limit(24).all()
            links = "<h2>Berita terbaru</h2><ul>" + "".join(
                '<li><a href="' + escape(public_post_path(p)) + '">' + escape(p.title) + '</a><p>' +
                escape(p.excerpt or "") + '</p></li>' for p in stories
            ) + "</ul>"
        elif path == "tentang":
            links = ("<h2>Peran BPKR</h2><p>BPKR mendukung pengelolaan Kampus Rembang "
                     "Universitas Diponegoro melalui layanan akademik, administrasi, fasilitas, "
                     "laboratorium, serta kerja sama dengan mitra.</p>")
        elif path == "layanan":
            links = ("<h2>Layanan kampus</h2><ul><li>Akademik</li>"
                     "<li>Sarana dan prasarana</li><li>Laboratorium</li>"
                     "<li>Administrasi</li><li>Keuangan</li><li>Kerja sama</li></ul>")
        elif path == "kontak":
            links = ("<h2>Alamat</h2><p>Kampus Rembang, Universitas Diponegoro</p>")
        html = html.replace('<div id="root"></div>',
                            '<div id="root"><main aria-label="Informasi BPKR">' +
                            nav_html + title_html + '<p>' + escape(desc) + '</p>' +
                            links + '</main></div>')
    elif path in {"dashboard", "login"} or path.startswith(("dashboard/", "login/")):
        html = html.replace("</head>", '<meta name="robots" content="noindex, nofollow"></head>')
        return HTMLResponse(html, headers={"Cache-Control": "private, no-store", "X-Robots-Tag": "noindex, nofollow"})
    else:
        raise HTTPException(404, "Halaman tidak ditemukan")
    return HTMLResponse(html, headers={"Cache-Control": "no-cache"})

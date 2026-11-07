import json
import os
import secrets
from datetime import datetime
from time import monotonic
from html import escape
from pathlib import Path
from typing import Optional

import bleach
from fastapi import FastAPI, Depends, HTTPException, Request, Response, UploadFile, File, Query
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
    "mahasiswa": POWER | {"pimpinan", "tendik"},
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
    allowed = {"site_name", "tagline", "hero_title", "hero_description", "contact_email", "contact_phone", "contact_address", "footer_text", "menus"}
    for key, value in payload.items():
        if key not in allowed or not isinstance(value, str) or len(value) > 5000:
            raise HTTPException(422, "Field pengaturan tidak valid")
        if key == "menus":
            try:
                menus = json.loads(value)
                if not isinstance(menus, list) or any(not str(x.get("url", "")).startswith("/") for x in menus):
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
        "content": bleach.clean(data.content, tags=["p", "br", "h2", "h3", "h4", "b", "strong", "em", "i", "u", "a", "ul", "ol", "li", "blockquote", "figure", "figcaption", "img"],
            attributes={"a": ["href", "title", "rel"], "img": ["src", "alt", "loading"], "figure": ["class"]},
            protocols=["https", "http"], strip=True),
        "image_url": data.image_url[:1024], "category": data.category[:100], "tags": data.tags[:300],
        "seo_title": data.seo_title[:220], "seo_description": data.seo_description[:400], "status": data.status,
    }

@app.post("/api/posts")
def create_post(data: PostIn, user: User = Depends(current_user), db: Session = Depends(db_session)):
    require(user, EDITOR)
    attrs = sanitize_post(data)
    row = Post(**attrs, slug=unique_slug(db, data.slug or data.title), author_id=user.id,
               published_at=utcnow() if data.status == "published" else None)
    db.add(row)
    db.flush()
    track(db, user, "create", "posts", row.id)
    db.commit()
    return ser(row, POST_KEYS)

@app.put("/api/posts/{post_id}")
def update_post(post_id: int, data: PostIn, user: User = Depends(current_user), db: Session = Depends(db_session)):
    require(user, EDITOR)
    row = db.get(Post, post_id)
    if not row:
        raise HTTPException(404, "Artikel tidak ditemukan")
    for k, v in sanitize_post(data).items():
        setattr(row, k, v)
    if data.slug and slugify(data.slug) != row.slug:
        row.slug = unique_slug(db, data.slug, row.id)
    if data.status == "published" and not row.published_at:
        row.published_at = utcnow()
    track(db, user, "update", "posts", row.id)
    db.commit()
    return ser(row, POST_KEYS)

@app.delete("/api/posts/{post_id}")
def delete_post(post_id: int, user: User = Depends(current_user), db: Session = Depends(db_session)):
    require(user, EDITOR)
    row = db.get(Post, post_id)
    if not row:
        raise HTTPException(404, "Artikel tidak ditemukan")
    db.delete(row)
    track(db, user, "delete", "posts", post_id)
    db.commit()
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

@app.get("/robots.txt", response_class=PlainTextResponse)
def robots():
    return "User-agent: *\nAllow: /\nDisallow: /dashboard\nDisallow: /login\nDisallow: /api/\nSitemap: " + BASE_URL + "/sitemap.xml\n"

@app.get("/sitemap.xml")
def sitemap(db: Session = Depends(db_session)):
    posts = db.query(Post).filter_by(status="published").all()
    paths = ["/"] + [("/berita/" if p.type == "news" else "/halaman/") + p.slug for p in posts]
    xml = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    for path in paths:
        xml += "<url><loc>" + escape(BASE_URL + path) + "</loc></url>"
    return Response(xml + "</urlset>", media_type="application/xml")

def render_article(post: Post):
    title = escape(post.seo_title or post.title)
    desc = escape(post.seo_description or post.excerpt or post.title)
    img = escape(absolute_url(post.image_url)) if post.image_url else ""
    link = absolute_url(("/berita/" if post.type == "news" else "/halaman/") + post.slug)
    structured = json.dumps({"@context": "https://schema.org", "@type": "NewsArticle" if post.type == "news" else "WebPage",
                             "headline": post.title, "description": post.seo_description or post.excerpt,
                             "datePublished": (post.published_at or post.created_at).isoformat(),
                             "dateModified": (post.updated_at or post.created_at).isoformat(),
                             "mainEntityOfPage": link, "image": [absolute_url(post.image_url)] if post.image_url else []},
                            ensure_ascii=False).replace("<", "\\u003c")
    body = post.content
    return HTMLResponse(f"""<!doctype html><html lang="id"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} | BPKR UNDIP</title><meta name="description" content="{desc}"><link rel="canonical" href="{escape(link)}">
<meta property="og:type" content="article"><meta property="og:title" content="{title}"><meta property="og:description" content="{desc}">
<meta property="og:url" content="{escape(link)}"><meta property="og:image" content="{img}">
<meta name="twitter:card" content="summary_large_image"><script type="application/ld+json">{structured}</script>
<style>body{{margin:0;background:#f7f9fc;color:#182e42;font:17px/1.8 system-ui,Arial}}header{{background:#102d46;color:white;padding:19px 7%}}header a{{color:white;text-decoration:none;font-weight:800}}main{{max-width:860px;margin:40px auto;background:white;padding:clamp(22px,5vw,60px);border-radius:15px}}h1{{font-size:clamp(28px,4vw,48px);line-height:1.2}}.meta{{color:#66778b;font-size:14px}}.hero{{width:100%;max-height:470px;object-fit:cover;border-radius:12px}}.article img{{max-width:100%;height:auto}}a{{color:#176780}}footer{{text-align:center;padding:25px;color:#69798b}}</style>
</head><body><header><a href="/">BPKR · UNDIP REMBANG</a></header><main><small>{escape(post.category)}</small><h1>{escape(post.title)}</h1><p class="meta">{(post.published_at or post.created_at).strftime("%d %B %Y")}</p>
{('<img class="hero" alt="' + escape(post.title) + '" src="' + escape(post.image_url) + '">') if post.image_url else ''}
<article class="article">{body}</article><p><a href="/berita">← Kembali ke berita</a></p></main><footer>Badan Pengelola Kampus Rembang · Universitas Diponegoro</footer></body></html>""")

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
    if path.startswith(("api/", "media/", "assets/")):
        raise HTTPException(404, "Rute tidak tersedia")
    index = STATIC / "index.html"
    if not index.exists():
        return HTMLResponse("<h1>BPKR frontend belum dibangun</h1>", status_code=503)
    if request.method == "HEAD":
        return Response(status_code=200, media_type="text/html")
    html = index.read_text(encoding="utf-8")
    if path in {"", "berita", "tentang", "layanan", "kontak"}:
        headings = {
            "": ("BPKR Kampus Rembang UNDIP | Berita, Layanan dan Kolaborasi", "Portal informasi, berita, layanan, dan kolaborasi Badan Pengelola Kampus Rembang Universitas Diponegoro."),
            "berita": ("Berita BPKR Kampus Rembang | UNDIP", "Berita dan informasi resmi terbaru seputar kegiatan, layanan, dan perkembangan Kampus Rembang UNDIP."),
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
        html = html.replace("</head>", '<meta property="og:title" content="' + escape(title) + '"><meta property="og:description" content="' +
                            escape(desc) + '"><meta property="og:url" content="' + escape(canonical) + '"></head>')
        title_html = '<h1>' + escape(title) + '</h1>'
        links = ""
        if path in {"", "berita"}:
            stories = db.query(Post).filter_by(type="news", status="published").order_by(Post.published_at.desc()).limit(24).all()
            links = "<h2>Berita terbaru</h2><ul>" + "".join(
                '<li><a href="/berita/' + escape(p.slug) + '">' + escape(p.title) + '</a><p>' +
                escape(p.excerpt or "") + '</p></li>' for p in stories
            ) + "</ul>"
        html = html.replace('<div id="root"></div>', '<div id="root"><main aria-label="Informasi BPKR">' + title_html + links + '</main></div>')
    elif path in {"dashboard", "login"} or path.startswith(("dashboard/", "login/")):
        html = html.replace("</head>", '<meta name="robots" content="noindex, nofollow"></head>')
    return HTMLResponse(html, headers={"Cache-Control": "no-cache"})

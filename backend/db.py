import os
from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Numeric, JSON, Index
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+psycopg2:///bpkr")
engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_size=5, max_overflow=10)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

def utcnow():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False, index=True)
    full_name = Column(String(180), nullable=False)
    email = Column(String(255), unique=True)
    role = Column(String(40), nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    must_change_password = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)

class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True)
    type = Column(String(12), nullable=False, default="news")
    title = Column(String(220), nullable=False)
    slug = Column(String(245), nullable=False, unique=True, index=True)
    excerpt = Column(Text, default="")
    content = Column(Text, default="")
    image_url = Column(String(1024), default="")
    category = Column(String(100), default="Berita")
    tags = Column(String(300), default="")
    seo_title = Column(String(220), default="")
    seo_description = Column(String(400), default="")
    status = Column(String(20), default="draft", nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    published_at = Column(DateTime(timezone=True))

class Entry(Base):
    __tablename__ = "entries"
    id = Column(Integer, primary_key=True)
    module = Column(String(32), nullable=False, index=True)
    title = Column(String(220), nullable=False)
    body = Column(Text, default="")
    status = Column(String(50), default="baru")
    amount = Column(Numeric(16, 2))
    due_at = Column(String(32), default="")
    assigned_to = Column(String(180), default="")
    details = Column(JSON, default=dict)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class Meeting(Base):
    __tablename__ = "meetings"
    id = Column(Integer, primary_key=True)
    title = Column(String(220), nullable=False)
    date = Column(String(30), default="")
    time = Column(String(60), default="")
    place = Column(String(220), default="")
    participants = Column(Text, default="")
    notes = Column(Text, default="")
    discussions = Column(JSON, default=list)
    decisions = Column(JSON, default=list)
    tasks = Column(JSON, default=list)
    status = Column(String(24), default="draft")
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class Letter(Base):
    __tablename__ = "letters"
    id = Column(Integer, primary_key=True)
    kind = Column(String(80), default="Surat keluar")
    recipient = Column(String(300), nullable=False)
    subject = Column(String(300), nullable=False)
    instructions = Column(Text, default="")
    signer = Column(String(220), default="")
    number = Column(String(100), default="")
    attachment = Column(String(120), default="")
    date = Column(String(30), default="")
    body = Column(Text, default="")
    status = Column(String(24), default="draft")
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class Setting(Base):
    __tablename__ = "settings"
    key = Column(String(100), primary_key=True)
    value = Column(Text, default="")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True)
    actor_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(100), nullable=False)
    entity = Column(String(80), nullable=False)
    entity_id = Column(Integer)
    at = Column(DateTime(timezone=True), default=utcnow)
    Index("ix_audit_logs_at", at)

def init_db():
    Base.metadata.create_all(engine)

import os
from db import SessionLocal, User, Setting, init_db
from security import hash_password

ROLES = ["pimpinan", "sekretaris", "keuangan", "kerjasama", "dosen", "laboran", "tendik", "mahasiswa", "superadmin", "admin"]
DEFAULT_SETTINGS = {
    "site_name": "BPKR | Kampus Rembang UNDIP",
    "tagline": "Bersama Membangun Kampus Rembang yang Unggul dan Berdampak",
    "hero_title": "Ruang Kolaborasi, Inovasi, dan Kemajuan Kampus Rembang.",
    "hero_description": "Informasi, layanan akademik, pengelolaan fasilitas, dan kolaborasi terintegrasi dalam satu platform Badan Pengelola Kampus Rembang.",
    "contact_email": "",
    "contact_phone": "",
    "contact_address": "Kampus Rembang, Universitas Diponegoro",
    "footer_text": "BPKR · Universitas Diponegoro · Kampus Rembang",
    "menus": '[{"title":"Beranda","url":"/"},{"title":"Berita","url":"/berita"},{"title":"Tentang","url":"/tentang"},{"title":"Layanan","url":"/layanan"},{"title":"Kontak","url":"/kontak"}]'
}

def seed():
    init_db()
    password = os.getenv("BPKR_INITIAL_PASSWORD")
    if not password:
        raise RuntimeError("BPKR_INITIAL_PASSWORD belum diatur")
    with SessionLocal() as db:
        for role in ROLES:
            if not db.query(User).filter_by(username=role).first():
                db.add(User(username=role, full_name=role.replace("_", " ").title() + " BPKR", role=role, password_hash=hash_password(password), must_change_password=True))
        for key, value in DEFAULT_SETTINGS.items():
            if db.get(Setting, key) is None:
                db.add(Setting(key=key, value=value))
        db.commit()

if __name__ == "__main__":
    seed()

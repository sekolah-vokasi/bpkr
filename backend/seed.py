import os
from db import SessionLocal, User, Setting, Post, init_db, utcnow
from security import hash_password

ROLES = ["pimpinan", "sekretaris", "keuangan", "kerjasama", "dosen", "laboran", "tendik", "mahasiswa", "superadmin", "admin"]
DEFAULT_SETTINGS = {
    "site_name": "BPKR | Kampus Rembang UNDIP",
    "tagline": "Bersama Membangun Kampus Rembang yang Unggul dan Berdampak",
    "hero_title": "Kampus Rembang",
    "hero_image_1": "/images/kampus-rembang.jpg",
    "hero_image_2": "/images/kampus-rembang-2.jpg",
    "hero_slide_2_title": "Bertumbuh, Berinovasi, Berdampak",
    "hero_slide_2_description": "Membangun ekosistem pendidikan tinggi yang adaptif, berbasis teknologi digital, dan berorientasi pada pelayanan serta pembangunan daerah.",
    "hero_description": "Kampus pengembangan UNDIP di pesisir utara Jawa yang mencetak talenta unggul, adaptif, dan berdampak bagi masyarakat.",
    "contact_email": "bpkr@live.undip.ac.id",
    "contact_phone": "",
    "contact_address": "Jalan Sawah, Desa Turus Gede, Kecamatan Rembang, Kabupaten Rembang, Jawa Tengah 59219, Indonesia.",
    "footer_text": "BPKR · Universitas Diponegoro · Kampus Rembang",
    "menus": '[{"title":"Beranda","url":"/"},{"title":"Tentang BPKR","url":"/tentang","children":[{"title":"Tentang BPKR","url":"/tentang"},{"title":"Visi & Misi","url":"/visi-misi"},{"title":"Struktur Organisasi","url":"/struktur"},{"title":"Pimpinan & Pengelola","url":"/pimpinan"}]},{"title":"Pengembangan","url":"/pengembangan","children":[{"title":"Arah Pengembangan","url":"/pengembangan"},{"title":"Sejarah Kampus","url":"/sejarah"},{"title":"Program Studi","url":"/program-studi"}]},{"title":"Artikel","url":"/artikel"},{"title":"Berita","url":"/berita"},{"title":"Kontak","url":"/kontak"}]'
}

DEFAULT_POSTS = [
    {
        "title": "UNDIP Lantik Kepala BPKR, Kampus Rembang Diarahkan Menjadi Percontohan Tata Kelola Modern",
        "slug": "undip-lantik-kepala-bpkr-kampus-rembang-tata-kelola-modern",
        "category": "Kabar Kampus",
        "excerpt": "Pelantikan pengelola Kampus Rembang pada 2 November 2026 menjadi titik awal penguatan tata kelola, digitalisasi layanan, dan kolaborasi di lingkungan UNDIP.",
        "content": """<p>Universitas Diponegoro (UNDIP) melantik pimpinan pengelola sejumlah kampus di daerah pada Senin, 2 November 2026, di Gedung SAMWA UNDIP, Semarang. Salah satu pejabat yang dilantik adalah Prof. Dr. Ir. Budiyono, M.Si. sebagai Kepala Badan Pengelola Kampus Rembang (BPKR).</p>
<p>Menurut laporan ANTARA Jateng yang diterbitkan pada 3 November 2026, pengembangan Kampus Rembang diarahkan untuk memperkuat tata kelola modern, layanan kampus yang responsif, serta proses administrasi yang lebih efektif. Pengelolaan fasilitas dan dukungan bagi kegiatan akademik menjadi bagian penting dari arah pengembangan tersebut.</p>
<h2>Transformasi digital dan layanan</h2>
<p>Rencana pengembangan menekankan digitalisasi administrasi, penggunaan data untuk pengambilan keputusan, penguatan layanan akademik dan nonakademik, serta peluang pemanfaatan kecerdasan artifisial secara bertanggung jawab. Pendekatan ini membuka ruang sinergi antara sivitas akademika, pemerintah, industri, dan masyarakat.</p>
<p>Dalam laporan yang sama, Rektor UNDIP menyampaikan harapan agar Kampus Rembang menjadi contoh pengelolaan kampus yang unggul. Arah tersebut merupakan target pengembangan, bukan capaian yang telah dinyatakan selesai.</p>
<p>Sumber informasi: <a href="https://jateng.antaranews.com/berita/651811/undip-lantik-pengelola-kampus-di-daerah-kampus-rembang-disiapkan-jadi-percontohan">ANTARA Jateng, 3 November 2026</a>. Artikel ini merupakan ringkasan dan parafrase dengan atribusi.</p>""",
        "tags": "BPKR, UNDIP, Kampus Rembang, Tata Kelola, Digitalisasi",
        "seo_description": "UNDIP melantik Kepala BPKR pada 2 November 2026. Kampus Rembang diarahkan menuju tata kelola modern, pelayanan prima, dan transformasi digital."
    },
    {
        "title": "Mengenal Portal Digital BPKR Kampus Rembang: Berita dan Layanan dalam Satu Tempat",
        "slug": "mengenal-portal-digital-bpkr-kampus-rembang",
        "category": "Informasi Layanan",
        "excerpt": "Portal BPKR menghadirkan berita publik, informasi layanan, serta dashboard kerja internal dengan pembagian akses berdasarkan peran pengguna.",
        "content": """<p>Portal digital BPKR dibuat sebagai titik akses informasi publik dan sarana pengelolaan internal Kampus Rembang. Pengunjung dapat mengikuti berita dan informasi layanan, sementara pengguna terdaftar mengakses dashboard sesuai kewenangannya.</p>
<h2>Dua ruang dalam satu platform</h2>
<p>Bagian publik memuat halaman beranda, berita, pengenalan BPKR, layanan, dan kontak. Redaksi dapat menerbitkan artikel dengan judul, kategori, gambar, tautan, serta metadata untuk membantu mesin pencari memahami informasi.</p>
<p>Bagian internal menyediakan modul administrasi, agenda, akademik, keuangan, kerja sama, laboratorium, sarana prasarana, dan layanan mahasiswa. Fitur yang tampil disesuaikan dengan role akun, termasuk pimpinan, sekretaris, keuangan, kerja sama, dosen, laboran, tenaga kependidikan, mahasiswa, dan administrator.</p>
<p>Pemanfaatan portal tetap mengikuti kewenangan masing-masing unit. Untuk pertama kali masuk, setiap akun diwajibkan mengganti kata sandi awal demi keamanan akses.</p>""",
        "tags": "Portal BPKR, Sistem Informasi, Kampus Rembang",
        "seo_description": "Kenali portal digital BPKR Kampus Rembang: berita, layanan publik, dan dashboard internal berbasis role untuk koordinasi kegiatan kampus."
    },
    {
        "title": "Dari Notula ke Tindak Lanjut: Penggunaan Modul Rapat dan Surat Digital BPKR",
        "slug": "modul-rapat-notula-surat-digital-bpkr",
        "category": "Panduan Sistem",
        "excerpt": "Kenali cara mengelola catatan rapat menjadi keputusan dan tindak lanjut, serta menyusun surat yang dapat ditinjau sebelum disahkan.",
        "content": """<p>Modul rapat digital BPKR membantu petugas menyimpan agenda, tanggal, lokasi, peserta, pembahasan, serta keputusan. Format baris yang terstruktur memudahkan pemisahan catatan menjadi daftar keputusan dan tugas yang perlu ditindaklanjuti.</p>
<h2>Format pencatatan yang praktis</h2>
<p>Untuk mencatat keputusan, awali baris dengan kata <strong>Keputusan:</strong>. Untuk tindak lanjut, gunakan format <strong>Tugas: uraian pekerjaan | PIC: penanggung jawab | Tenggat: YYYY-MM-DD</strong>. Setelah diproses, petugas dapat memeriksa hasil, memperbarui status, dan menyimpan notula.</p>
<h2>Alur dokumen surat</h2>
<p>Modul surat menyediakan pilihan surat keluar, undangan rapat, nota dinas, dan laporan kegiatan. Petugas memasukkan tujuan, perihal, instruksi, tanggal, dan pejabat penandatangan, lalu memeriksa dan menyunting naskah.</p>
<p>Pengolahan teks pada versi ini menggunakan aturan dan templat, bukan AI generatif. Keputusan rapat, substansi dokumen, nomor surat, dan persetujuan tetap memerlukan verifikasi manusia yang berwenang.</p>""",
        "tags": "Notula, Surat, Rapat, Administrasi Digital, BPKR",
        "seo_description": "Panduan modul rapat dan surat BPKR: olah notula, keputusan, PIC, tenggat, monitoring tugas, dan penyusunan surat untuk review."
    }
]

DEFAULT_POSTS.append({
    "title": "Membangun Kampus Rembang UNDIP: Dari Amanah, Idealisme, Menuju Kampus yang Berdampak",
    "slug": "membangun-kampus-rembang-undip",
    "category": "Artikel Reflektif",
    "excerpt": "Refleksi pengembangan Kampus Rembang UNDIP melalui tata kelola modern, transformasi digital, pendidikan berkualitas, dan kemitraan yang berdampak.",
    "image_url": "/images/kampus-rembang-2.jpg",
    "tags": "BPKR, Kampus Rembang, UNDIP, Pengembangan, Artikel Reflektif, Prof. Budiyono",
    "seo_description": "Gagasan dan arah pengembangan Kampus Rembang UNDIP untuk tata kelola modern, digital governance, pendidikan, inovasi, dan keberlanjutan.",
    "content": """<p><strong>Kampus Rembang Universitas Diponegoro</strong> merupakan bagian dari komitmen UNDIP dalam memperluas akses pendidikan tinggi berkualitas sekaligus meningkatkan kontribusi perguruan tinggi bagi pembangunan daerah dan masyarakat.</p>
<p>Penguatan pengelolaan melalui Badan Pengelola Kampus Rembang (BPKR) pada November 2026 menjadi langkah penting untuk menghadirkan kampus yang dikelola secara profesional, efektif, efisien, akuntabel, dan berorientasi pada manfaat nyata.</p>
<h2>Arah dan Visi Pengembangan</h2>
<p>Visi BPKR adalah <strong>“Mewujudkan Kampus Rembang UNDIP yang unggul dalam tata kelola, inovatif, dan berkelanjutan untuk menghadirkan dampak nyata bagi masyarakat.”</strong></p>
<p>Sinergi bidang administrasi publik, informatika, dan teknologi digital diarahkan untuk memperkuat ekosistem <strong>Digital Governance and Public Innovation</strong> yang mendukung layanan publik, tata kelola, dan pembangunan masyarakat.</p>
<div class="article-pill-grid">
<div><strong>Digital Governance</strong><span>Inovasi tata kelola dan pelayanan publik</span></div>
<div><strong>Smart Campus</strong><span>Integrasi teknologi dan efisiensi layanan</span></div>
<div><strong>Academic Excellence</strong><span>Lingkungan pendidikan yang berkualitas</span></div>
<div><strong>Strategic Partnership</strong><span>Kolaborasi pemerintah, industri, dan masyarakat</span></div>
<div><strong>Sustainability</strong><span>Pengelolaan kampus ramah lingkungan</span></div>
</div>
<h2>Strategi Pengelolaan</h2>
<p>Pengembangan Kampus Rembang dilakukan secara terintegrasi dan kolaboratif melalui enam prioritas:</p>
<div class="article-strategy-grid">
<div><strong>Transformasi Digital</strong><span>Sistem informasi, integrasi data, dan pengembangan smart campus.</span></div>
<div><strong>Pengelolaan Efektif</strong><span>Tata kelola profesional, transparan, akuntabel, dan berorientasi pada kinerja.</span></div>
<div><strong>Penguatan Akademik</strong><span>Pendidikan berkualitas yang relevan dengan kebutuhan masa depan.</span></div>
<div><strong>Pelayanan Prima</strong><span>Pelayanan akademik dan nonakademik yang responsif serta mudah diakses.</span></div>
<div><strong>Kemitraan & Inovasi</strong><span>Kerja sama dengan pemerintah, dunia usaha, industri, dan masyarakat.</span></div>
<div><strong>Kampus Berkelanjutan</strong><span>Fasilitas efisien, hemat energi, inklusif, dan ramah lingkungan.</span></div>
</div>
<h2>Menuju Kampus yang Lebih Bermakna</h2>
<p>Pengembangan Kampus Rembang tidak berhenti pada pertumbuhan fasilitas fisik. Penguatan pendidikan, penelitian, inovasi, pengabdian kepada masyarakat, dan kerja sama menjadi bagian dari upaya menghasilkan solusi terapan untuk tantangan nyata di daerah.</p>
<p>Dengan pengelolaan yang modern dan dukungan seluruh unsur Universitas Diponegoro, Kampus Rembang diharapkan terus bertumbuh sebagai lingkungan pendidikan tinggi yang unggul, adaptif, kolaboratif, dan memberikan manfaat luas bagi masyarakat.</p>
<p><small>Sumber substansi: dokumen profil Badan Pengelola Kampus Rembang Universitas Diponegoro.</small></p>"""
})

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
        author = db.query(User).filter_by(username="admin").first()
        for article in DEFAULT_POSTS:
            if not db.query(Post).filter_by(slug=article["slug"]).first():
                db.add(Post(**article, status="published", type="news", seo_title=article["title"],
                            author_id=author.id if author else None, published_at=utcnow()))
        db.commit()

if __name__ == "__main__":
    seed()

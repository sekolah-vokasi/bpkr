# BPKR — Portal Badan Pengelola Kampus Rembang

Portal internal dan publik Badan Pengelola Kampus Rembang (Universitas Diponegoro).

## Teknologi

- Frontend: React 19, Vite 6, Lucide Icons, CSS responsif.
- Backend: Python 3.10+, FastAPI, SQLAlchemy.
- Database: PostgreSQL `bpkr` dengan akun aplikasi khusus `bpkr_app` tanpa hak superuser.
- Akses publik: https://bpkr.otomasi.app via Cloudflare Tunnel ke `127.0.0.1:9787`.
- Satu origin: FastAPI menyajikan frontend Vite yang sudah dibuild dan seluruh `/api/*`.

## Struktur

```text
bpkr/
├── frontend/
│   ├── src/main.jsx
│   ├── src/style.css
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── backend/
│   ├── app.py
│   ├── db.py
│   ├── security.py
│   ├── logic.py
│   ├── seed.py
│   └── requirements.txt
├── uploads/                # unggahan gambar, tidak dikomit
├── .env.example            # contoh konfigurasi
├── .env                    # lokal, RAHASIA, tidak dikomit
├── .gitignore
├── server.sh
├── bpkr.service
└── README.md
```

## Instalasi mesin Linux

Prasyarat: PostgreSQL aktif, Python >= 3.10, Node.js >= 20, npm.

1. Siapkan database PostgreSQL `bpkr` dan role aplikasi non-superuser `bpkr_app` dengan autentikasi SCRAM-SHA-256. Berikan hak CONNECT untuk database, serta USAGE/CREATE schema, SELECT/INSERT/UPDATE/DELETE tabel, dan USAGE pada sekuens yang dibutuhkan.
2. Salin `.env.example` ke `.env`, isi `DATABASE_URL`, `BPKR_SECRET` acak minimal 32 karakter, `BPKR_INITIAL_PASSWORD`, dan opsi domain.
3. Jalankan `chmod +x server.sh && ./server.sh setup`.
4. Jalankan `./server.sh start` untuk menjalankan API dan UI pada `127.0.0.1:9787`.
5. Gunakan `./server.sh build` setelah mengubah frontend, dan `./server.sh seed` jika menambah akun role yang belum ada.

Untuk produksi, pertahankan `BPKR_COOKIE_SECURE=1` dan gunakan HTTPS di reverse proxy / Cloudflare Tunnel. Jangan membuka port PostgreSQL ke internet. Servis produksi telah disiapkan di `bpkr.service` (user systemd) dan diaktifkan dengan `systemctl --user enable --now bpkr.service`. Untuk melihat status: `systemctl --user status bpkr.service`; untuk memulai ulang: `systemctl --user restart bpkr.service`. Pengaturan `loginctl enable-linger sirobo` memastikan servis pengguna dapat aktif setelah reboot. Semua berkas source servis berada di root proyek.

## Role dan hak akses

Akun contoh diinisialisasi menggunakan username identik dengan nama role: `pimpinan`, `sekretaris`, `keuangan`, `kerjasama`, `dosen`, `laboran`, `tendik`, `mahasiswa`, `superadmin`, `admin`.

**Keamanan:** kata sandi inisial diberikan melalui variabel lokal `BPKR_INITIAL_PASSWORD` saat instalasi dan di-hash scrypt menggunakan salt unik di PostgreSQL. Semua akun **wajib mengganti password awal** (minimal 12 karakter). Setelah login, pengguna tetap dapat membuka dashboard dan semua tampilan sesuai role, serta melihat banner pengingat dan menu **Akun & Keamanan** untuk mengganti password. Sebelum penggantian dilakukan, backend membatasi operasi perubahan data (POST/PUT/PATCH/DELETE) kecuali penggantian password dan logout; penelusuran tampilan (GET) tetap tersedia. Dilarang menaruh file `.env` atau cookie sesi di GitHub. Di produksi, lakukan rotasi seluruh akun bootstrap secepatnya.

Akses menu:
- Pimpinan: ringkasan lintas modul, rapat, surat, editorial, dan aktivitas operasional.
- Sekretaris: administrasi, agenda, rapat, surat, editorial.
- Keuangan: pengelolaan catatan keuangan dan agenda.
- Kerja sama: catatan kemitraan, editorial, agenda.
- Dosen: akademik, laboratorium (baca), mahasiswa (baca), agenda.
- Laboran: laboratorium, sarana prasarana, agenda.
- Tendik: administrasi, sarana prasarana, surat, mahasiswa, agenda.
- Mahasiswa: melihat agenda serta membuat/mengubah/menghapus permohonannya sendiri selama berstatus `baru`; tidak dapat mengubah pengajuan orang lain atau data master.
- Admin: konfigurasi situs, pengguna non-superadmin, audit, serta administrasi.
- Superadmin: seluruh fungsi termasuk pengelolaan akun superadmin.

Izin diperiksa ulang pada setiap API backend (bukan hanya menyembunyikan tombol frontend).

## Berita, editor, dan SEO

Editor mengelola judul, isi rich text, gambar unggulan (unggah max 5 MB), kategori, tag, slug, judul SEO, deskripsi SEO, serta status `draft/published/archived`.

- Artikel publik: `/berita/<slug>`; halaman: `/halaman/<slug>`.
- Setiap artikel terbit disajikan sebagai HTML server-rendered dengan judul SEO, meta description, canonical URL, Open Graph, dan JSON-LD Schema.org.
- `/robots.txt` dan `/sitemap.xml` otomatis dari konten terbit; `/llms.txt` memberikan ringkasan sumber situs bagi crawler AI.
- Beranda dan katalog berita memiliki fallback HTML berisi tautan artikel untuk crawler tanpa JavaScript. Halaman login dan dashboard diberi `noindex`.
- Landing page publik, berita, tentang, layanan, kontak, dan customizer pengaturan website.
- Konten editor disanitasi dengan Bleach untuk mencegah HTML berbahaya.
- Struktur SEO membantu pengindeksan tetapi **tidak menjamin ranking Google atau keterbacaan semua mesin AI**. Untuk SEO optimal, terbitkan berita asli, foto dengan hak pakai, serta update yang relevan.

## Asisten Rapat dan Surat

Modul surat meniru fungsi demo yang diberikan pengguna: surat keluar, undangan rapat, nota dinas, laporan kegiatan; isian, draf teks, edit, simpan, dan persetujuan. Modul rapat memproses baris `Keputusan:` dan `Tugas: ... | PIC: ... | Tenggat: YYYY-MM-DD` menjadi keputusan dan tindak lanjut serta status.

**Keduanya menggunakan templat/aturan lokal, bukan model AI generatif**. Verifikasi informasi, otoritas, tata naskah, dan penandatangan harus dilakukan oleh petugas. Penyusunan berbasis model AI sungguhan memerlukan integrasi provider, regulasi privasi, serta persetujuan instansi.

## API

Dokumentasi interaktif (dengan autentikasi untuk API yang dilindungi): `/api/docs`.

Ringkasan endpoint: `/api/health`, `/api/auth/login`, `/api/auth/me`, `/api/auth/change-password`, `/api/auth/logout`, `/api/site`, `/api/posts`, `/api/posts/slug/{slug}`, `/api/media`, `/api/modules`, `/api/entries`, `/api/meetings`, `/api/meetings/parse`, `/api/letters`, `/api/users`, `/api/dashboard`, `/api/audit`.

Login menggunakan session cookie HttpOnly, SameSite=Strict dan pemeriksaan header CSRF untuk operasi yang mengubah data. Sesi memiliki masa berlaku 8 jam serta invalidasi setelah ganti kata sandi.

## Pengujian

Jalankan `./server.sh test` untuk kompilasi Python, `./server.sh build` untuk validasi kompilasi React, dan cek HTTP `/api/health`. Deployment BPKR telah diuji menggunakan Playwright Chromium dan integration test API; berkas test sementara dihapus setelah pengujian. Jalankan smoke test browser Playwright pada login, ubah password pertama kali, dashboard, artikel, proses rapat/surat, dan hak akses per role sebelum rilis.

## Catatan operasional

- Database memerlukan backup PostgreSQL berkala (misalnya `pg_dump -Fc bpkr`) pada lokasi backup resmi yang diatur admin.
- Gambar unggahan disimpan di `uploads/` dan perlu dibackup terpisah.
- Hindari upload rahasia ke bagian berita publik.
- Perlu ditambah bila akan dipakai skala institusi: alur persetujuan bertanda tangan elektronik, integrasi SSO, verifikasi kebijakan dan retensi dokumen, notifikasi email, pengaturan kuota, monitoring uptime, backup otomatis, dan migrasi skema formal (Alembic).

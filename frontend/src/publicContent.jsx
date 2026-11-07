import React from 'react';
import './publicContent.css';
import {
  ArrowRight, ArrowUpRight, BookOpen, Building2, CalendarDays,
  ClipboardList, GraduationCap, Handshake, HeartHandshake,
  Leaf, Mail, MapPin, Globe2, MonitorCog, Network, ShieldCheck, Sparkles,
  Workflow, Lightbulb, Landmark, Laptop, Clock,
} from 'lucide-react';

const priorities = [
  {title:'Tata Kelola Efektif',desc:'Pengelolaan profesional, transparan, akuntabel, efisien, dan berorientasi pada kinerja.',icon:ShieldCheck},
  {title:'Transformasi Digital',desc:'Integrasi data, layanan berbasis teknologi informasi, dan pengembangan smart campus.',icon:MonitorCog},
  {title:'Lingkungan Akademik',desc:'Pendidikan berkualitas serta program akademik yang relevan dengan kebutuhan masa depan.',icon:GraduationCap},
  {title:'Pelayanan Prima',desc:'Layanan akademik dan nonakademik yang mudah diakses, responsif, dan berorientasi pada pengguna.',icon:HeartHandshake},
  {title:'Inovasi & Kemitraan',desc:'Kolaborasi dengan pemerintah, dunia usaha, dunia industri, dan masyarakat.',icon:Handshake},
  {title:'Kampus Berkelanjutan',desc:'Sarana prasarana yang efisien, hemat energi, ramah lingkungan, dan nyaman.',icon:Leaf},
];

const missions = [
  'Mewujudkan tata kelola kampus yang unggul melalui pengelolaan profesional, efektif, efisien, transparan, akuntabel, dan berorientasi pada kinerja.',
  'Mengembangkan transformasi digital dan smart campus melalui teknologi informasi, kecerdasan artifisial, integrasi data, dan sistem pelayanan modern.',
  'Mendukung penguatan dan pengembangan akademik dengan lingkungan pendidikan berkualitas, adaptif, inovatif, dan relevan dengan kebutuhan masyarakat.',
  'Meningkatkan kualitas pelayanan dan pengelolaan sumber daya melalui pelayanan prima, penguatan sarana prasarana, serta fasilitas yang produktif dan efisien.',
  'Mendorong inovasi dan kemitraan strategis melalui kolaborasi pemerintah, dunia usaha, dunia industri, perguruan tinggi, dan masyarakat.',
  'Mewujudkan kampus yang berkelanjutan melalui lingkungan yang bersih, hijau, hemat energi, inklusif, dan berorientasi pada keberlanjutan.',
];

const development = [
  {title:'Digital Governance & Public Innovation',desc:'Mengintegrasikan administrasi publik, informatika, dan teknologi digital untuk inovasi tata kelola, pelayanan publik, industri, dan pembangunan masyarakat.',icon:Network},
  {title:'Smart & Efficient Campus Management',desc:'Pengelolaan kampus terintegrasi berbasis data, teknologi digital, dan kecerdasan artifisial, dengan fokus pada efisiensi, transparansi, dan pelayanan prima.',icon:Laptop},
  {title:'Academic Excellence & Institutional Growth',desc:'Peningkatan kualitas pendidikan, pengembangan program studi yang relevan, penguatan sumber daya akademik, dan perluasan akses pendidikan tinggi.',icon:GraduationCap},
  {title:'Innovation, Partnership & Real-World Impact',desc:'Kolaborasi strategis dengan pemerintah, dunia industri, dan masyarakat untuk menghasilkan inovasi, solusi terapan, serta manfaat nyata.',icon:Lightbulb},
  {title:'Sustainable & Future-Ready Campus',desc:'Lingkungan kampus yang aman, nyaman, inklusif, ramah lingkungan, hemat energi, dan adaptif terhadap kebutuhan masa depan.',icon:Leaf},
];

const timeline = [
  {year:'2018',title:'Awal Pengembangan',desc:'Kampus Rembang memulai pengembangan layanan pendidikan tinggi melalui Program Studi Diploma III (D3) Manajemen.'},
  {year:'Transformasi',title:'Penguatan Pendidikan Terapan',desc:'Program D3 Manajemen dihentikan secara bertahap sejalan dengan transformasi pendidikan vokasi menuju jenjang Sarjana Terapan (D4).'},
  {year:'Pengembangan Akademik',title:'Program Sarjana',desc:'Kampus Rembang menjadi lokasi penyelenggaraan Program Studi S1 Informatika dan S1 Administrasi Publik.'},
  {year:'November 2026',title:'Penguatan Pengelolaan BPKR',desc:'Universitas Diponegoro memperkuat pengelolaan Kampus Rembang melalui Badan Pengelola Kampus Rembang (BPKR).'},
];

const pages = {
  tentang:{kicker:'MENGENAL BPKR',title:'Tentang Badan Pengelola',accent:'Kampus Rembang',desc:'Mendukung pengelolaan, pengembangan, dan penyelenggaraan layanan kampus yang efektif, profesional, dan berkelanjutan.'},
  'visi-misi':{kicker:'FONDASI PENGEMBANGAN',title:'Visi, Misi &',accent:'Arah Pengembangan',desc:'Membangun tata kelola kampus yang unggul, inovatif, dan berorientasi pada manfaat nyata bagi masyarakat.'},
  struktur:{kicker:'TATA KELOLA ORGANISASI',title:'Struktur &',accent:'Pengorganisasian',desc:'Koordinasi lintas unsur Universitas Diponegoro untuk pelayanan kampus yang efektif, efisien, dan akuntabel.'},
  pimpinan:{kicker:'KEPEMIMPINAN BPKR',title:'Pimpinan &',accent:'Pengelola',desc:'Mengenal Kepala Badan Pengelola Kampus Rembang, Universitas Diponegoro.'},
  sejarah:{kicker:'JEJAK PENGEMBANGAN',title:'Sejarah',accent:'Kampus Rembang',desc:'Dari perluasan akses pendidikan tinggi pada 2018 menuju penguatan tata kelola kampus modern.'},
  pengembangan:{kicker:'STRATEGI MASA DEPAN',title:'Pengembangan',accent:'Kampus Rembang',desc:'Digital governance, layanan terpadu, keunggulan akademik, kemitraan, dan keberlanjutan.'},
  'program-studi':{kicker:'AKADEMIK KAMPUS REMBANG',title:'Program Studi &',accent:'Pendidikan',desc:'Program akademik dan arah penguatan pendidikan tinggi di Kampus Rembang UNDIP.'},
  layanan:{kicker:'LAYANAN TERINTEGRASI',title:'Layanan',accent:'Kampus',desc:'Pelayanan akademik, fasilitas, administrasi, dan kemitraan yang terkoordinasi melalui BPKR.'},
  kontak:{kicker:'TERHUBUNG DENGAN KAMI',title:'Kontak',accent:'BPKR',desc:'Informasi alamat, email, dan komunikasi resmi Badan Pengelola Kampus Rembang UNDIP.'},
};

function ActionLink({to,children,onNavigate,solid=false}) {
  return <button type="button" onClick={()=>onNavigate(to)} className={'content-action '+(solid?'solid':'')}>{children}<ArrowRight size={17}/></button>;
}
function SectionHead({eyebrow,title,desc}) {
  return <div className="content-heading"><span>{eyebrow}</span><h2>{title}</h2>{desc&&<p>{desc}</p>}</div>;
}
function Tiles({items}) {
  return <div className="content-tile-grid">{items.map(({title,desc,icon:Icon})=><article key={title} className="content-tile"><div className="content-tile-icon"><Icon size={24}/></div><h3>{title}</h3><p>{desc}</p></article>)}</div>;
}
function Profile({compact=false}) {
  return <div className={'leader-card '+(compact?'compact':'')}>
    <img src="/images/prof-budiyono.jpg" alt="Foto Prof. Dr. Ir. Budiyono, M.Si., Kepala BPKR" loading="lazy"/>
    <div className="leader-card-caption">
      <span>KEPALA BPKR</span>
      <strong>Prof. Dr. Ir. Budiyono, M.Si.</strong>
      <small>Universitas Diponegoro · Mulai 2 November 2026</small>
    </div>
  </div>;
}
function PageHeader({details}) {
  return <section className="page-banner"><div className="public-container page-banner-inner"><span className="hero-rule"/><span className="page-banner-kicker">{details.kicker}</span><h1>{details.title} <em>{details.accent}</em></h1><p>{details.desc}</p></div><svg className="page-banner-wave" viewBox="0 0 1440 66" preserveAspectRatio="none" aria-hidden="true"><path d="M0 42 C270 4 480 80 730 48 S1100 20 1440 36 L1440 66 L0 66 Z" fill="#f7f9fd" stroke="#ffca27" strokeWidth="5"/></svg></section>;
}
function Intro() {
  return <div className="content-intro-grid">
    <div><span className="content-eyebrow">BADAN PENGELOLA KAMPUS REMBANG</span><h2>Pengelolaan kampus yang <em>profesional dan berdampak.</em></h2></div>
    <div className="content-prose"><p>Badan Pengelola Kampus Rembang (BPKR) merupakan unit pengelola di lingkungan Universitas Diponegoro yang mendukung pengelolaan, pengembangan, dan penyelenggaraan layanan Kampus Rembang secara efektif, efisien, profesional, dan berkelanjutan.</p>
    <p>Kehadiran BPKR menjadi bagian dari komitmen UNDIP untuk memperluas akses pendidikan tinggi berkualitas, memperkuat pelayanan akademik, dan meningkatkan kontribusi perguruan tinggi bagi masyarakat serta pembangunan daerah.</p></div>
  </div>;
}
function About({onNavigate}) {
  return <>
    <Intro/>
    <section className="content-section"><SectionHead eyebrow="PRIORITAS PENGELOLAAN" title="Enam pilar utama BPKR" desc="Penguatan tata kelola, akademik, layanan, inovasi, dan keberlanjutan menjadi prioritas pengembangan Kampus Rembang."/><Tiles items={priorities}/></section>
    <section className="content-section content-split"><div className="content-photo"><img src="/images/kampus-rembang-2.jpg" alt="Gedung Kampus Rembang Universitas Diponegoro" loading="lazy"/></div><div className="content-prose"><span className="content-eyebrow">KOMITMEN KAMI</span><h2>Menumbuhkan kampus yang unggul dan adaptif.</h2><p>BPKR berkomitmen membangun lingkungan kampus yang mendukung keunggulan akademik, inovasi, pelayanan prima, dan pemanfaatan teknologi secara bertanggung jawab.</p><p>Pengembangan kampus ditujukan untuk menghadirkan kontribusi nyata bagi ilmu pengetahuan, masyarakat, dan pembangunan Indonesia.</p><ActionLink to="/visi-misi" onNavigate={onNavigate} solid>Baca visi & misi BPKR</ActionLink></div></section>
    <section className="content-section"><SectionHead eyebrow="KEPEMIMPINAN" title="Mengenal Kepala BPKR"/><div className="content-leadership-strip"><Profile compact/><div className="content-prose"><h3>Prof. Dr. Ir. Budiyono, M.Si.</h3><p>Guru Besar Teknik Kimia Universitas Diponegoro, dipercaya mengemban amanah sebagai Kepala BPKR sejak 2 November 2026. Sebelumnya beliau menjabat sebagai Dekan Sekolah Vokasi UNDIP selama dua periode.</p><ActionLink to="/pimpinan" onNavigate={onNavigate}>Lihat profil pimpinan</ActionLink></div></div></section>
  </>;
}
function Vision() {
  return <>
    <section className="content-vision"><span>VISI BPKR</span><blockquote>“Mewujudkan Kampus Rembang UNDIP yang unggul dalam tata kelola, inovatif, dan berkelanjutan untuk menghadirkan dampak nyata bagi masyarakat.”</blockquote><div>Efficient Governance • Digital Transformation • Innovation • Sustainability</div></section>
    <section className="content-section"><SectionHead eyebrow="MISI BPKR" title="Enam misi untuk dampak nyata"/><div className="content-number-grid">{missions.map((desc,i)=><article key={desc}><span>{String(i+1).padStart(2,'0')}</span><p>{desc}</p></article>)}</div></section>
    <section className="content-section"><SectionHead eyebrow="ARAH PENGEMBANGAN" title="Peta jalan kampus masa depan"/><Tiles items={development}/></section>
  </>;
}
function Organization({onNavigate}) {
  return <>
    <section className="content-leadership-strip content-section"><Profile compact/><div className="content-prose"><span className="content-eyebrow">PIMPINAN BPKR</span><h2>Prof. Dr. Ir. Budiyono, M.Si.</h2><p>Badan Pengelola Kampus Rembang menjalankan fungsi pengelolaan dan pengembangan Kampus Rembang sesuai ketentuan organisasi dan kebijakan Universitas Diponegoro.</p><p>Pelaksanaan pengelolaan dilakukan melalui koordinasi dengan pimpinan universitas, fakultas dan sekolah pengampu program studi, serta unit-unit terkait sesuai kewenangannya.</p><ActionLink to="/pimpinan" onNavigate={onNavigate} solid>Profil kepala BPKR</ActionLink></div></section>
    <section className="content-section"><SectionHead eyebrow="PRINSIP PENGORGANISASIAN" title="Struktur kerja yang kolaboratif"/><Tiles items={[
      {title:'Efisiensi Organisasi',desc:'Pembagian tugas yang jelas, koordinasi sederhana, dan optimalisasi sumber daya.',icon:Workflow},
      {title:'Pelayanan Terpadu',desc:'Integrasi layanan administrasi, fasilitas, dan kebutuhan operasional kampus.',icon:HeartHandshake},
      {title:'Transformasi Digital',desc:'Pemanfaatan sistem informasi, integrasi data, dan teknologi untuk mendukung pengelolaan.',icon:MonitorCog},
      {title:'Koordinasi Akademik',desc:'Sinergi dengan fakultas dan sekolah pengampu program studi.',icon:GraduationCap},
      {title:'Akuntabilitas Kinerja',desc:'Penetapan tanggung jawab, indikator kinerja, dan evaluasi berkala.',icon:ShieldCheck},
    ]}/></section>
    <div className="content-note">Susunan personel lengkap dan pembagian tugas mengikuti ketetapan resmi Universitas Diponegoro. Informasi yang belum tersedia tidak ditampilkan sebagai susunan organisasi definitif.</div>
  </>;
}
function Leadership() {
  return <><div className="leader-profile-layout content-section"><Profile/><div className="content-prose"><span className="content-eyebrow">KEPALA BADAN PENGELOLA KAMPUS REMBANG</span><h2>Prof. Dr. Ir. Budiyono, M.Si.</h2><div className="leader-term"><CalendarDays size={19}/> Menjabat sejak 2 November 2026</div><p>Prof. Dr. Ir. Budiyono, M.Si. merupakan Guru Besar Teknik Kimia Universitas Diponegoro yang dipercaya mengemban amanah sebagai Kepala Badan Pengelola Kampus Rembang (BPKR) sejak 2 November 2026.</p><p>Sebelum menjalankan amanah tersebut, beliau menjabat sebagai Dekan Sekolah Vokasi Universitas Diponegoro selama dua periode, yaitu 2016–2021 dan 2021–2026.</p><p>Selama memimpin Sekolah Vokasi UNDIP, beliau berperan dalam pengembangan pendidikan vokasi terapan, transformasi program pendidikan, penguatan tata kelola, peningkatan mutu dan akreditasi, pengembangan kerja sama industri dan internasional, serta inovasi pembelajaran berbasis praktik dan teknologi.</p><p>Dalam pengelolaan BPKR, beliau mendorong tata kelola profesional, efektif, efisien, berbasis teknologi digital, berorientasi pada pelayanan prima, inovasi, dan keberlanjutan.</p></div></div>
    <section className="content-section"><SectionHead eyebrow="FOKUS KEPEMIMPINAN" title="Arah tata kelola dan pengembangan"/><Tiles items={[
      {title:'Pelayanan Prima',desc:'Layanan kampus yang mudah diakses, responsif, dan berorientasi pada kebutuhan pengguna.',icon:HeartHandshake},
      {title:'Transformasi Digital',desc:'Penggunaan teknologi digital dan integrasi data untuk tata kelola yang lebih efektif.',icon:MonitorCog},
      {title:'Kolaborasi Akademik',desc:'Pengembangan lingkungan pendidikan yang adaptif, inovatif, dan berorientasi pada kontribusi nyata.',icon:GraduationCap},
    ]}/></section></>;
}
function History() {
  return <>
    <section className="content-section"><SectionHead eyebrow="JEJAK PERJALANAN" title="Bertumbuh dari waktu ke waktu" desc="Pengembangan Kampus Rembang merupakan bagian dari perluasan akses pendidikan tinggi oleh Universitas Diponegoro."/><div className="history-timeline">{timeline.map((item)=><article key={item.year}><div className="timeline-year">{item.year}</div><div><h3>{item.title}</h3><p>{item.desc}</p></div></article>)}</div></section>
    <section className="content-section content-split"><div className="content-photo"><img src="/images/kampus-rembang-2.jpg" alt="Gedung Kampus Rembang UNDIP" loading="lazy"/></div><div className="content-prose"><span className="content-eyebrow">BABAK BARU</span><h2>Transformasi menuju kampus yang berdampak.</h2><p>Sejalan dengan pengembangan fasilitas dan infrastruktur, Kampus Rembang diarahkan menjadi lingkungan pendidikan tinggi yang modern, inovatif, nyaman, dan adaptif.</p><p>Sinergi S1 Informatika dan S1 Administrasi Publik membuka peluang pengembangan bidang Digital Governance and Public Innovation.</p></div></section>
  </>;
}
function Development() {
  return <>
    <div className="content-intro-grid"><div><span className="content-eyebrow">DIRECTION & IMPACT</span><h2>Pendidikan, inovasi, dan layanan untuk <em>masa depan.</em></h2></div><div className="content-prose"><p>Pengembangan Kampus Rembang diarahkan untuk membangun ekosistem pendidikan tinggi yang unggul, modern, adaptif, dan berorientasi pada inovasi serta dampak nyata.</p><p>Sinergi bidang administrasi publik, informatika, dan teknologi digital menjadi fondasi penguatan ekosistem Digital Governance and Public Innovation.</p></div></div>
    <section className="content-section"><SectionHead eyebrow="LIMA ARAH PENGEMBANGAN" title="Prioritas strategis"/><div className="development-grid">{development.map(({title,desc,icon:Icon},i)=><article key={title}><span className="development-num">0{i+1}</span><div><Icon size={29}/></div><h3>{title}</h3><p>{desc}</p></article>)}</div></section>
  </>;
}
function StudyPrograms() {
  return <>
    <section className="content-section"><SectionHead eyebrow="PROGRAM AKADEMIK" title="Bidang studi di Kampus Rembang" desc="Program yang disebut dalam dokumen profil BPKR dan arah pengembangannya."/><div className="content-tile-grid">
      <article className="content-tile"><div className="content-tile-icon"><Laptop size={24}/></div><span className="program-status">PROGRAM S1</span><h3>Informatika</h3><p>Penguatan bidang teknologi informasi dan ilmu informatika sebagai bagian dari sinergi teknologi dan inovasi digital.</p></article>
      <article className="content-tile"><div className="content-tile-icon"><Landmark size={24}/></div><span className="program-status">PROGRAM S1</span><h3>Administrasi Publik</h3><p>Pendidikan di bidang administrasi publik, tata kelola, dan inovasi pelayanan masyarakat.</p></article>
      <article className="content-tile planned"><div className="content-tile-icon"><ClipboardList size={24}/></div><span className="program-status">RENCANA PENGEMBANGAN</span><h3>D4 Manajemen dan Administrasi Logistik</h3><p>Rencana program Sarjana Terapan di bawah Sekolah Vokasi UNDIP; tidak dinyatakan sebagai program yang sudah dibuka.</p></article>
    </div></section>
    <div className="content-note">Informasi penerimaan mahasiswa, kurikulum, dan status pembukaan program studi mengikuti pengumuman resmi Universitas Diponegoro serta fakultas atau sekolah terkait.</div>
  </>;
}
function Services({onNavigate}) {
  return <><section className="content-section"><SectionHead eyebrow="LAYANAN BPKR" title="Layanan kampus dalam satu ekosistem" desc="BPKR mendukung koordinasi dan pengelolaan layanan akademik serta nonakademik."/><Tiles items={[
      {title:'Layanan Akademik',desc:'Dukungan koordinasi kegiatan pendidikan dan kebutuhan akademik bersama fakultas atau sekolah pengampu.',icon:BookOpen},
      {title:'Administrasi',desc:'Koordinasi dokumen, kegiatan, layanan administrasi dan kebutuhan operasional kampus.',icon:ClipboardList},
      {title:'Sarana & Prasarana',desc:'Pengelolaan, pemeliharaan, dan optimalisasi fasilitas serta infrastruktur kampus.',icon:Building2},
      {title:'Laboratorium',desc:'Pendataan fasilitas dan dukungan kegiatan laboratorium sesuai kewenangan yang berlaku.',icon:Sparkles},
      {title:'Kemitraan Strategis',desc:'Kolaborasi dengan perguruan tinggi, pemerintah, industri, dan masyarakat.',icon:Handshake},
      {title:'Sistem Digital',desc:'Penguatan sistem informasi, integrasi data, dan pengembangan smart campus.',icon:MonitorCog},
    ]}/></section><section className="content-portal-cta"><div><span>PORTAL INTERNAL BPKR</span><h2>Sudah memiliki akun pengelola?</h2><p>Masuk ke dashboard untuk menggunakan layanan sesuai kewenangan dan role akun.</p></div><ActionLink to="/login" onNavigate={onNavigate} solid>Masuk Portal BPKR</ActionLink></section></>;
}
function Contact({site}) {
  return <>
    <section className="content-section"><SectionHead eyebrow="HUBUNGI KAMI" title="Informasi & kerja sama" desc="BPKR berkomitmen melayani mahasiswa, dosen, tenaga kependidikan, mitra, dan masyarakat secara terbuka, responsif, dan profesional."/><div className="contact-detail-grid">
      <div className="contact-detail"><MapPin size={27}/><h3>Alamat Kantor</h3><p>{site.contact_address||'Jalan Sawah, Desa Turus Gede, Kecamatan Rembang, Kabupaten Rembang, Jawa Tengah 59219, Indonesia.'}</p></div>
      <div className="contact-detail"><Mail size={27}/><h3>Email Resmi BPKR</h3><a href={'mailto:'+(site.contact_email||'bpkr@live.undip.ac.id')}>{site.contact_email||'bpkr@live.undip.ac.id'}</a></div>
      <div className="contact-detail"><Globe2 size={27}/><h3>Website BPKR</h3><p>www.bpkr.undip.ac.id</p></div>
      <div className="contact-detail"><Clock size={27}/><h3>Jam Pelayanan</h3><p>Senin–Jumat, mengikuti ketentuan jam kerja dan pelayanan Universitas Diponegoro.</p></div>
    </div></section>
    <section className="content-split content-section"><div className="content-photo"><img src="/images/kampus-rembang-2.jpg" alt="Gedung Kampus Rembang Universitas Diponegoro" loading="lazy"/></div><div className="content-prose"><span className="content-eyebrow">BERSAMA KAMPUS REMBANG</span><h2>Terbuka untuk komunikasi dan kolaborasi.</h2><p>Permohonan informasi mengenai layanan administrasi, fasilitas kampus, maupun usulan kerja sama dengan pemerintah, perguruan tinggi, dunia usaha, dunia industri, dan masyarakat dapat disampaikan melalui email resmi BPKR.</p><a className="content-action solid" href={'mailto:'+(site.contact_email||'bpkr@live.undip.ac.id')}>Kirim email ke BPKR <ArrowUpRight size={17}/></a></div></section>
  </>;
}
export default function PublicContentPage({kind,site={},navigate}) {
  const details=pages[kind]||pages.tentang;
  return <><PageHeader details={details}/><main className="public-container content-main">
    {kind==='tentang'&&<About onNavigate={navigate}/>}
    {kind==='visi-misi'&&<Vision/>}
    {kind==='struktur'&&<Organization onNavigate={navigate}/>}
    {kind==='pimpinan'&&<Leadership/>}
    {kind==='sejarah'&&<History/>}
    {kind==='pengembangan'&&<Development/>}
    {kind==='program-studi'&&<StudyPrograms/>}
    {kind==='layanan'&&<Services onNavigate={navigate}/>}
    {kind==='kontak'&&<Contact site={site}/>}
  </main></>;
}

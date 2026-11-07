import React, { useEffect, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import {
  ArrowRight, ArrowUpRight, BookOpen, Building2, CalendarDays,
  ChevronDown, ClipboardList, FileText, Globe2, Handshake,
  ImagePlus, LayoutDashboard, LogIn, LogOut, Mail, Menu, Microscope,
  Newspaper, Plus, Search, Settings, ShieldCheck, Sparkles, Trash2,
  Users, Wallet, X, CheckCircle2, Save,
  GraduationCap, MapPin, Phone, LockKeyhole, Leaf,
  ExternalLink, Eye, Pencil, RotateCcw
} from 'lucide-react';
import './style.css';

const roleLabels = {
  pimpinan: 'Pimpinan', sekretaris: 'Sekretaris', keuangan: 'Keuangan',
  kerjasama: 'Kerja Sama', dosen: 'Dosen', laboran: 'Laboran',
  tendik: 'Tenaga Kependidikan', mahasiswa: 'Mahasiswa',
  superadmin: 'Super Admin', admin: 'Admin'
};
const moduleLabels = {
  agenda: 'Agenda & Kegiatan', administrasi: 'Administrasi', keuangan: 'Keuangan & Anggaran',
  kerjasama: 'Mitra & Kerja Sama', akademik: 'Akademik', laboratorium: 'Laboratorium',
  sarpras: 'Sarana & Prasarana', mahasiswa: 'Layanan Mahasiswa'
};
const moduleIcons = {
  agenda: CalendarDays, administrasi: ClipboardList, keuangan: Wallet,
  kerjasama: Handshake, akademik: BookOpen, laboratorium: Microscope,
  sarpras: Building2, mahasiswa: GraduationCap
};
const emptyPost = { type:'news', title:'', slug:'', excerpt:'', content:'', image_url:'', category:'Berita', tags:'', seo_title:'', seo_description:'', status:'draft' };
const emptyEntry = { module:'agenda', title:'', body:'', status:'baru', amount:null, due_at:'', assigned_to:'', details:{} };
const emptyMeeting = { title:'', date:'', time:'', place:'', participants:'', notes:'', discussions:[], decisions:[], tasks:[], status:'draft' };
const emptyLetter = { kind:'Surat keluar', recipient:'', subject:'', instructions:'', signer:'Kepala Badan Pengelola Kampus Rembang', number:'', attachment:'', date:'', body:'', status:'draft' };

function cookie(name) {
  return document.cookie.split('; ').find(x => x.startsWith(name + '='))?.split('=').slice(1).join('=') || '';
}
async function api(path, options = {}) {
  const method = options.method || 'GET';
  const headers = {...(options.body instanceof FormData ? {} : {'Content-Type':'application/json'}), ...(options.headers || {})};
  if (method !== 'GET') headers['x-csrf-token'] = decodeURIComponent(cookie('bpkr_csrf'));
  const response = await fetch('/api' + path, {...options, headers, credentials:'same-origin'});
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Permintaan gagal (' + response.status + ')');
  return data;
}
function formatDate(value) {
  if (!value) return '';
  const d = new Date(value);
  return Number.isNaN(+d) ? String(value) : new Intl.DateTimeFormat('id-ID', {day:'numeric',month:'long',year:'numeric'}).format(d);
}
function plainText(value) {
  return String(value || '').replace(/<[^>]*>/g, '').replace(/&nbsp;/g, ' ').slice(0, 200);
}
function IconButton({icon:Icon, children, onClick, kind='light', disabled=false, type='button'}) {
  return <button type={type} className={'btn btn-' + kind} onClick={onClick} disabled={disabled}>{Icon && <Icon size={17}/>} {children}</button>;
}
function Tag({children, color=''}) { return <span className={'tag ' + color}>{children}</span>; }
function Input({label, value, onChange, placeholder='', type='text', required=false, ...rest}) {
  return <label className="field"><span>{label}</span><input type={type} value={value ?? ''} onChange={e=>onChange(e.target.value)} placeholder={placeholder} required={required} {...rest}/></label>;
}
function Textarea({label, value, onChange, rows=4, placeholder=''}) {
  return <label className="field"><span>{label}</span><textarea rows={rows} value={value ?? ''} onChange={e=>onChange(e.target.value)} placeholder={placeholder}/></label>;
}
function SelectField({label, value, onChange, options}) {
  return <label className="field"><span>{label}</span><select value={value} onChange={e=>onChange(e.target.value)}>{options.map(x=><option key={Array.isArray(x)?x[0]:x} value={Array.isArray(x)?x[0]:x}>{Array.isArray(x)?x[1]:x}</option>)}</select></label>;
}
function Empty({title,subtitle}) {
  return <div className="empty"><span className="empty-circle"><FileText size={26}/></span><h3>{title}</h3><p>{subtitle}</p></div>;
}

function App() {
  const [path, setPath] = useState(location.pathname);
  const [site, setSite] = useState({});
  const [posts, setPosts] = useState([]);
  const [user, setUser] = useState(null);
  const [login, setLogin] = useState({username:'',password:''});
  const [passwords, setPasswords] = useState({old_password:'',new_password:''});
  const [menuOpen, setMenuOpen] = useState(false);
  const [heroSlide, setHeroSlide] = useState(0);
  const [busy, setBusy] = useState(false);
  const [toast, setToast] = useState('');
  const [error, setError] = useState('');
  const [section, setSection] = useState('overview');
  const [dashboard, setDashboard] = useState(null);
  const [modules, setModules] = useState([]);
  const [entries, setEntries] = useState([]);
  const [entry, setEntry] = useState({...emptyEntry});
  const [meetings, setMeetings] = useState([]);
  const [meeting, setMeeting] = useState({...emptyMeeting});
  const [letters, setLetters] = useState([]);
  const [letter, setLetter] = useState({...emptyLetter});
  const [cmsPosts, setCmsPosts] = useState([]);
  const [editPost, setEditPost] = useState({...emptyPost});
  const [users, setUsers] = useState([]);
  const [editUser, setEditUser] = useState({username:'',full_name:'',role:'tendik',email:'',password:'',is_active:true});
  const [audit, setAudit] = useState([]);
  const [search, setSearch] = useState('');
  const editorRef = useRef(null);

  function navigate(to) {
    history.pushState({}, '', to);
    setPath(to);
    setMenuOpen(false);
    window.scrollTo({top:0, behavior:'instant'});
  }
  useEffect(() => {
    if (path !== '/') return;
    const interval = setInterval(() => setHeroSlide(current => (current + 1) % 3), 8000);
    return () => clearInterval(interval);
  }, [path]);
  useEffect(() => {
    const pop = () => setPath(location.pathname);
    window.addEventListener('popstate',pop);
    Promise.allSettled([api('/site'),api('/posts?limit=24'),api('/auth/me')]).then(results=>{
      if(results[0].status==='fulfilled')setSite(results[0].value);
      if(results[1].status==='fulfilled')setPosts(results[1].value.items);
      if(results[2].status==='fulfilled')setUser(results[2].value);
    });
    return ()=>window.removeEventListener('popstate',pop);
  }, []);
  useEffect(() => {
    if (!user || path !== '/dashboard') return;
    Promise.allSettled([api('/dashboard'),api('/modules')]).then(res=>{
      if(res[0].status==='fulfilled')setDashboard(res[0].value);
      if(res[1].status==='fulfilled')setModules(res[1].value);
    });
  }, [user, path]);
  useEffect(() => {
    if (!user || path !== '/dashboard') return;
    if (moduleLabels[section]) {
      api('/entries?module=' + section).then(setEntries).catch(e=>setError(e.message));
      setEntry({...emptyEntry, module:section});
    }
    if (section==='meetings') api('/meetings').then(setMeetings).catch(e=>setError(e.message));
    if (section==='letters') api('/letters').then(setLetters).catch(e=>setError(e.message));
    if (section==='cms') api('/posts?all=true&limit=60').then(r=>setCmsPosts(r.items)).catch(e=>setError(e.message));
    if (section==='users') api('/users').then(setUsers).catch(e=>setError(e.message));
    if (section==='audit') api('/audit').then(setAudit).catch(e=>setError(e.message));
  }, [user, path, section]);
  async function action(fn, message='Data berhasil disimpan') {
    setBusy(true); setError(''); setToast('');
    try {await fn();setToast(message);}
    catch(e){setError(e.message);}
    finally{setBusy(false);}
  }
  async function loginSubmit(e) {
    e.preventDefault();
    await action(async()=>{
      const data = await api('/auth/login',{method:'POST',body:JSON.stringify(login)});
      setUser(data.user); setLogin({username:'',password:''});
      setSection('overview'); navigate('/dashboard');
    },'Selamat datang di portal BPKR');
  }
  async function changePassword(e) {
    e.preventDefault();
    await action(async()=>{
      await api('/auth/change-password',{method:'POST',body:JSON.stringify(passwords)});
      setPasswords({old_password:'',new_password:''});
      setUser(await api('/auth/me'));
    },'Kata sandi berhasil diperbarui');
  }
  async function logout() {
    await action(async()=>{await api('/auth/logout',{method:'POST'});setUser(null);navigate('/');},'Anda telah keluar');
  }
  async function reloadPosts() {const result=await api('/posts?limit=24');setPosts(result.items);}
  async function savePost() {
    const payload={...editPost,content:editorRef.current?.innerHTML || editPost.content};
    await action(async()=>{
      if(editPost.id) await api('/posts/' + editPost.id,{method:'PUT',body:JSON.stringify(payload)});
      else await api('/posts',{method:'POST',body:JSON.stringify(payload)});
      setCmsPosts((await api('/posts?all=true&limit=60')).items);
      await reloadPosts();setEditPost({...emptyPost});
    },'Artikel berhasil disimpan');
  }
  async function deletePost(id) {
    if(!confirm('Hapus artikel ini secara permanen?'))return;
    await action(async()=>{await api('/posts/'+id,{method:'DELETE'});setCmsPosts((await api('/posts?all=true&limit=60')).items);await reloadPosts();},'Artikel dihapus');
  }
  async function uploadImage(file) {
    if(!file)return;
    await action(async()=>{
      const body=new FormData();body.append('file',file);
      const result=await api('/media',{method:'POST',body});
      setEditPost(p=>({...p,image_url:result.url}));
    },'Gambar berhasil diunggah');
  }
  async function saveEntry() {
    await action(async()=>{
      const payload={...entry,module:section};
      if(entry.id)await api('/entries/'+entry.id,{method:'PUT',body:JSON.stringify(payload)});
      else await api('/entries',{method:'POST',body:JSON.stringify(payload)});
      setEntries(await api('/entries?module='+section));setEntry({...emptyEntry,module:section});
    });
  }
  async function deleteEntry(id) {
    if(!confirm('Hapus data ini?'))return;
    await action(async()=>{await api('/entries/'+id,{method:'DELETE'});setEntries(await api('/entries?module='+section));},'Data dihapus');
  }
  async function parseMeeting() {
    await action(async()=>{
      const result=await api('/meetings/parse',{method:'POST',body:JSON.stringify({notes:meeting.notes})});
      setMeeting(p=>({...p,...result}));
    },'Catatan berhasil dipisahkan menjadi pembahasan, keputusan dan tugas');
  }
  async function saveMeeting() {
    await action(async()=>{
      if(meeting.id)await api('/meetings/'+meeting.id,{method:'PUT',body:JSON.stringify(meeting)});
      else await api('/meetings',{method:'POST',body:JSON.stringify(meeting)});
      setMeetings(await api('/meetings'));setMeeting({...emptyMeeting});
    },'Rapat dan tugas berhasil disimpan');
  }
  async function deleteMeeting(id) {
    if(!confirm('Hapus rapat dan tindak lanjutnya?'))return;
    await action(async()=>{await api('/meetings/'+id,{method:'DELETE'});setMeetings(await api('/meetings'));},'Rapat dihapus');
  }
  async function saveLetter() {
    await action(async()=>{
      if(letter.id)await api('/letters/'+letter.id,{method:'PUT',body:JSON.stringify(letter)});
      else await api('/letters',{method:'POST',body:JSON.stringify(letter)});
      setLetters(await api('/letters'));setLetter({...emptyLetter});
    },'Dokumen disimpan');
  }
  async function deleteLetter(id) {
    if(!confirm('Hapus dokumen ini?'))return;
    await action(async()=>{await api('/letters/'+id,{method:'DELETE'});setLetters(await api('/letters'));},'Dokumen dihapus');
  }
  async function saveUser() {
    await action(async()=>{
      if(editUser.id) await api('/users/'+editUser.id,{method:'PUT',body:JSON.stringify({...editUser,password:editUser.password || ''})});
      else await api('/users',{method:'POST',body:JSON.stringify(editUser)});
      setUsers(await api('/users'));setEditUser({username:'',full_name:'',role:'tendik',email:'',password:'',is_active:true});
    },'Akun disimpan');
  }
  async function saveSite() {
    await action(async()=>{setSite(await api('/site',{method:'PUT',body:JSON.stringify(site)}));},'Pengaturan website diperbarui');
  }
  function updateEntry(key,val){setEntry(p=>({...p,[key]:val}));}
  function updateMeeting(key,val){setMeeting(p=>({...p,[key]:val}));}
  function updateLetter(key,val){setLetter(p=>({...p,[key]:val}));}
  function updatePost(key,val){setEditPost(p=>({...p,[key]:val}));}
  const isEditor=['pimpinan','sekretaris','kerjasama','superadmin','admin'].includes(user?.role);
  const isAdmin=['superadmin','admin'].includes(user?.role);
  const canMeet=['pimpinan','sekretaris','superadmin','admin'].includes(user?.role);
  const canLetters=['pimpinan','sekretaris','tendik','superadmin','admin'].includes(user?.role);
  const menus=(()=>{try{return JSON.parse(site.menus||'[]')}catch{return []}})();
  const showArticle = (post) => '/'+(post.type==='page'?'halaman':'berita')+'/'+post.slug;

  function Navbar() {
    return <header className="site-header">
      <div className="header-inner">
        <button className="brand" onClick={()=>navigate('/')} aria-label="Beranda Universitas Diponegoro Kampus Rembang">
          <img className="brand-logo" src="/images/undip-logo.png" alt="Lambang Universitas Diponegoro"/>
          <span className="brand-university">UNIVERSITAS<br/>DIPONEGORO</span>
          <span className="brand-separator"/>
          <span className="brand-campus">Kampus<br/><strong>Rembang</strong></span>
        </button>
        <nav className={'nav-links '+(menuOpen?'opened':'')}>
          {(menus.length?menus:[{title:'Beranda',url:'/'},{title:'Berita',url:'/berita'},{title:'Tentang',url:'/tentang'},{title:'Layanan',url:'/layanan'},{title:'Kontak',url:'/kontak'}]).map((m,i)=><button key={i} className={path===m.url?'active':''} onClick={()=>navigate(m.url)}>{m.title}</button>)}
        </nav>
        <div className="header-actions">
          <a className="undip-link" href="https://undip.ac.id/" target="_blank" rel="noopener noreferrer">UNDIP <ExternalLink size={15}/></a>
          <IconButton icon={user?LayoutDashboard:LogIn} kind="nav" onClick={()=>navigate(user?'/dashboard':'/login')}>{user?'Dashboard':'Portal BPKR'}</IconButton>
          <button className="menu-toggle" aria-label="Buka menu" onClick={()=>setMenuOpen(x=>!x)}>{menuOpen?<X/>:<Menu/>}</button>
        </div>
      </div>
    </header>;
  }
  function Footer() {
    return <footer className="footer-public"><div className="public-container">
      <div className="footer-grid"><div><div className="footer-brand"><img src="/images/undip-logo.png" alt="Logo UNDIP"/>BPKR<span className="accent-dot">.</span></div><p>{site.tagline||'Kolaborasi untuk Kampus Rembang'}</p><div className="footer-social"><Globe2 size={19}/> Universitas Diponegoro</div></div>
      <div><h4>Jelajahi</h4><button onClick={()=>navigate('/')}>Beranda</button><button onClick={()=>navigate('/berita')}>Berita & Publikasi</button><button onClick={()=>navigate('/layanan')}>Layanan Terpadu</button></div>
      <div><h4>Informasi</h4><button onClick={()=>navigate('/tentang')}>Tentang BPKR</button><button onClick={()=>navigate('/kontak')}>Hubungi Kami</button><button onClick={()=>navigate('/login')}>Login Sistem</button></div>
      <div><h4>Alamat & Kontak</h4><p><MapPin size={15}/> {site.contact_address||'Kampus Rembang, Universitas Diponegoro'}</p>{site.contact_email&&<p><Mail size={15}/> {site.contact_email}</p>}{site.contact_phone&&<p><Phone size={15}/> {site.contact_phone}</p>}</div></div>
      <div className="footer-bottom"><span>© {new Date().getFullYear()} {site.footer_text||'BPKR · Universitas Diponegoro'}</span><span>Built for collaboration & real impact</span></div>
    </div></footer>;
  }
  function StoryCard({post,featured=false}) {
    return <a className={'story-card '+(featured?'featured':'')} href={showArticle(post)}>
      <div className="story-image">{post.image_url?<img loading="lazy" src={post.image_url} alt={post.title}/>:<div className="story-image-placeholder"><Newspaper size={45}/></div>}<span className="story-category">{post.category}</span></div>
      <div className="story-info"><small>{formatDate(post.published_at||post.created_at)}</small><h3>{post.title}</h3><p>{post.excerpt||plainText(post.content)}</p><span className="read-more">Baca selengkapnya <ArrowUpRight size={16}/></span></div>
    </a>;
  }
  function HomePage() {
    const heroSlides = [
      {eyebrow:'BADAN PENGELOLA KAMPUS REMBANG',pretitle:'Universitas Diponegoro',title:site.hero_title||'Kampus Rembang',description:site.hero_description||'Kampus pengembangan UNDIP di pesisir utara Jawa yang mencetak talenta unggul, adaptif, dan berdampak bagi masyarakat.'},
      {eyebrow:'LAYANAN KAMPUS TERPADU',pretitle:'Pengelolaan Kampus',title:'Melayani dengan Sepenuh Hati',description:'Akses informasi akademik, administrasi, fasilitas, dan berbagai layanan Kampus Rembang melalui satu portal.'},
      {eyebrow:'RISET, INOVASI & KEMITRAAN',pretitle:'Bersama Kampus Rembang',title:'Berkolaborasi dan Berdampak',description:'Memperkuat sinergi pendidikan, industri, pemerintah, dan masyarakat untuk masa depan yang berkelanjutan.'}
    ];
    const currentHero = heroSlides[heroSlide];
    return <><main>
      <section className="hero" aria-label="Profil Kampus Rembang">
        <div className="hero-photo" aria-hidden="true"/>
        <div className="public-container hero-grid">
          <div className="hero-content" key={heroSlide}>
            <span className="hero-rule"/>
            <div className="hero-subtitle">{currentHero.pretitle}</div>
            <h1>{currentHero.title}</h1>
            <p>{currentHero.description}</p>
            <div className="hero-values">
              <span><GraduationCap size={26}/> Pendidikan<br/>Berkualitas</span>
              <span><Handshake size={26}/> Kemitraan<br/>Berdampak</span>
              <span><Leaf size={26}/> Kampus<br/>Berkelanjutan</span>
            </div>
            <div className="hero-cta"><IconButton kind="gold" icon={ArrowRight} onClick={()=>navigate('/tentang')}>Profil Kampus</IconButton><button className="hero-link" onClick={()=>navigate('/layanan')}>Layanan Kampus <ArrowRight size={18}/></button></div>
          </div>
        </div>
        <div className="hero-pagination" aria-label="Pilih slide utama">{heroSlides.map((slide,i)=><button key={slide.eyebrow} type="button" aria-label={'Tampilkan slide '+(i+1)} aria-pressed={heroSlide===i} className={heroSlide===i?'active':''} onClick={()=>setHeroSlide(i)}/>)}</div>
        <svg className="hero-wave" viewBox="0 0 1440 100" preserveAspectRatio="none" aria-hidden="true"><path d="M0 40 C180 2 325 72 520 78 S900 95 1110 74 S1300 45 1440 8 L1440 100 L0 100 Z" fill="#07366B" stroke="#FFCA27" strokeWidth="8"/></svg>
      </section>
      <section className="trust-strip"><div className="public-container trust-inner"><div><span className="trust-small">DIPONEGORO UNIVERSITY</span><b>Kampus Rembang</b></div><span className="trust-divider"/><div><span className="trust-small">PILAR LAYANAN</span><b>Akademik · Fasilitas · Kemitraan</b></div><span className="trust-divider"/><div><span className="trust-small">PRINSIP KERJA</span><b>Efektif dan Akuntabel</b></div></div></section>
      <section className="public-section public-container"><div className="section-heading"><div><div className="section-kicker">WHAT WE DO <span>✦</span></div><h2>Solusi terpadu untuk<br/><i>kemajuan bersama.</i></h2></div><p>Dari pengelolaan internal hingga kolaborasi eksternal, layanan kampus lebih mudah dijangkau dan dipantau.</p></div>
      <div className="service-grid">
        <button className="service-card service-a" onClick={()=>navigate('/layanan')}><div className="service-top"><span>01 / LAYANAN</span><ArrowUpRight/></div><span className="service-emoji"><BookOpen size={34}/></span><h3>Layanan Akademik</h3><p>Koordinasi kegiatan, informasi akademik, dan dukungan proses pembelajaran.</p></button>
        <button className="service-card service-b" onClick={()=>navigate('/layanan')}><div className="service-top"><span>02 / FASILITAS</span><ArrowUpRight/></div><span className="service-emoji"><Building2 size={34}/></span><h3>Fasilitas Kampus</h3><p>Pengelolaan sarana, ruang, laboratorium, dan kebutuhan operasional.</p></button>
        <button className="service-card service-c" onClick={()=>navigate('/layanan')}><div className="service-top"><span>03 / KEMITRAAN</span><ArrowUpRight/></div><span className="service-emoji"><Handshake size={34}/></span><h3>Kolaborasi Strategis</h3><p>Menghubungkan civitas akademika, industri, pemerintah, dan masyarakat.</p></button>
      </div></section>
      <section className="news-section"><div className="public-container"><div className="section-heading"><div><div className="section-kicker">STORIES & UPDATES <span>✦</span></div><h2>Kabar terbaru dari <i>Rembang.</i></h2></div><button className="all-stories" onClick={()=>navigate('/berita')}>Semua berita <ArrowUpRight size={18}/></button></div>
      {posts.length?<div className="stories-grid">{posts.slice(0,3).map((p,i)=><StoryCard key={p.id} post={p} featured={i===0}/>)}</div>:<Empty title="Berita akan segera hadir" subtitle="Publikasi resmi BPKR akan muncul setelah editor menerbitkan artikel melalui dashboard."/>}</div></section>
      <section className="cta-band"><div className="public-container cta-grid"><span className="cta-big-icon"><Handshake size={49}/></span><div><span>LET'S WORK TOGETHER</span><h2>Bangun dampak bersama<br/>Kampus Rembang.</h2></div><IconButton kind="dark" icon={ArrowUpRight} onClick={()=>navigate('/kontak')}>Hubungi Kami</IconButton></div></section>
    </main><Footer/></>;
  }
  function PageBanner({kicker,title,accent,description}) {
    return <section className="page-banner"><div className="public-container page-banner-inner"><span className="hero-rule"/><span className="page-banner-kicker">{kicker}</span><h1>{title} <em>{accent}</em></h1><p>{description}</p></div><svg className="page-banner-wave" viewBox="0 0 1440 66" preserveAspectRatio="none" aria-hidden="true"><path d="M0 42 C270 4 480 80 730 48 S1100 20 1440 36 L1440 66 L0 66 Z" fill="#f7f9fd" stroke="#ffca27" strokeWidth="5"/></svg></section>;
  }
  function NewsPage() {
    const filtered=posts.filter(p=>p.title.toLowerCase().includes(search.toLowerCase())||p.category.toLowerCase().includes(search.toLowerCase()));
    return <><PageBanner kicker="PUBLIKASI & INFORMASI" title="Berita" accent="& Cerita" description="Ruang berbagi perkembangan, capaian, dan kegiatan Kampus Rembang Universitas Diponegoro."/><main className="page-main public-container"><div className="news-tools"><div className="searchbox"><Search size={19}/><input placeholder="Cari berita atau kategori..." value={search} onChange={e=>setSearch(e.target.value)}/></div><Tag>{filtered.length} Artikel</Tag></div>{filtered.length?<div className="stories-grid">{filtered.map(p=><StoryCard key={p.id} post={p}/>)}</div>:<Empty title="Belum ada berita" subtitle="Coba kata kunci lain atau kunjungi kembali nanti."/>}</main><Footer/></>;
  }
  function InfoPage({kind}) {
    const isAbout=kind==='tentang',isContact=kind==='kontak';
    return <><PageBanner kicker="BPKR · KAMPUS REMBANG" title={isAbout?'Tentang':isContact?'Hubungi':'Layanan'} accent={isAbout?'Kami':isContact?'BPKR':'Terpadu'} description={isAbout?'Mendukung tata kelola, layanan, dan pengembangan Kampus Rembang Universitas Diponegoro.':isContact?'Terhubung dan berkolaborasi bersama Badan Pengelola Kampus Rembang.':'Akses berbagai layanan administrasi, akademik, serta operasional melalui portal yang terintegrasi.'}/><main className="page-main public-container">
      {isContact?<div className="contact-cards"><div className="info-card"><MapPin/><h3>Alamat</h3><p>{site.contact_address||'Kampus Rembang, Universitas Diponegoro'}</p></div>{site.contact_email&&<div className="info-card"><Mail/><h3>Email</h3><p>{site.contact_email}</p></div>}{site.contact_phone&&<div className="info-card"><Phone/><h3>Telepon</h3><p>{site.contact_phone}</p></div>}</div>:isAbout?<div className="about-layout"><div className="about-visual"><span>Kampus<br/>Rembang</span><small>UNIVERSITAS DIPONEGORO</small></div><div className="about-text"><div className="section-kicker">OUR COMMITMENT</div><h2>{site.tagline}</h2><p>BPKR menyediakan ruang koordinasi pengelolaan Kampus Rembang, meliputi komunikasi layanan, fasilitas, administrasi, kolaborasi, serta dokumentasi kegiatan.</p><p>Portal ini memisahkan informasi publik dan akses operasional internal, dengan pembagian kewenangan sesuai role pengguna.</p></div></div>:<div className="contact-cards">{[['Akademik',BookOpen,'Koordinasi pembelajaran dan layanan akademik'],['Sarana & Prasarana',Building2,'Penggunaan ruang, fasilitas, dan kebutuhan kampus'],['Laboratorium',Microscope,'Pendataan laboratorium dan aktivitas pendukung'],['Administrasi',ClipboardList,'Surat, dokumen, rapat, serta tindak lanjut'],['Keuangan',Wallet,'Pengelolaan administrasi anggaran sesuai akses'],['Kerja Sama',Handshake,'Koordinasi mitra dan kegiatan kemitraan']].map(([name,I,desc])=><div className="info-card" key={name}><I/><h3>{name}</h3><p>{desc}</p></div>)}</div>}
      <div className="info-action"><p>Sudah memiliki akun BPKR?</p><IconButton icon={LogIn} kind="primary" onClick={()=>navigate('/login')}>Masuk ke Dashboard</IconButton></div>
    </main><Footer/></>;
  }
  function LoginPage() {
    return <main className="auth-page"><div className="auth-aside"><img className="auth-aside-logo" src="/images/undip-logo.png" alt="Lambang Universitas Diponegoro"/><div className="auth-aside-content"><span>UNIVERSITAS DIPONEGORO</span><h2>Kampus Rembang.<br/>Melayani & Berdampak.</h2><p>Portal operasional terpadu untuk seluruh unsur Badan Pengelola Kampus Rembang.</p></div><div className="auth-aside-foot">BPKR · Universitas Diponegoro · Kampus Rembang</div></div><div className="auth-form-wrap"><button className="back-link" onClick={()=>navigate('/')}><ArrowRight size={15}/> Kembali ke website</button><div className="auth-form"><div className="auth-icon"><LockKeyhole size={25}/></div><span className="section-kicker">SECURE WORKSPACE</span><h1>Selamat datang <i>kembali.</i></h1><p>Masuk menggunakan akun sesuai peran Anda di BPKR.</p><form onSubmit={loginSubmit}><Input label="Username" required autoComplete="username" value={login.username} onChange={v=>setLogin(p=>({...p,username:v}))} placeholder="Contoh: sekretaris"/><Input label="Kata sandi" required type="password" autoComplete="current-password" value={login.password} onChange={v=>setLogin(p=>({...p,password:v}))} placeholder="Masukkan kata sandi"/><button className="btn btn-primary login-submit" disabled={busy} type="submit">Masuk ke Dashboard <ArrowRight size={18}/></button></form><p className="auth-note"><ShieldCheck size={16}/> Akses diawasi dan disesuaikan dengan role pengguna.</p></div></div></main>;
  }
  function DashboardOverview() {
    const stats=[['Artikel Terbit',dashboard?.news??0,Newspaper],['Rapat Tercatat',dashboard?.meetings??0,CalendarDays],['Dokumen Surat',dashboard?.letters??0,FileText],['Modul Tersedia',modules.length,LayoutDashboard]];
    return <><div className="dash-welcome"><div><span className="dash-kicker">WORKSPACE OVERVIEW</span><h1>Halo, {user?.full_name?.split(' ')[0]} <span>✳</span></h1><p>Selamat datang di sistem terintegrasi BPKR. Kelola aktivitas dan kolaborasi dengan lebih terarah.</p></div><div className="welcome-decoration"><Sparkles size={50}/></div></div><div className="stat-grid">{stats.map(([name,count,I])=><div className="stat-box" key={name}><div className="stat-icon"><I size={21}/></div><span>{name}</span><strong>{count}</strong></div>)}</div><div className="dash-section-title"><div><h2>Modul kerja Anda</h2><p>Layanan dan pengelolaan sesuai kewenangan akun</p></div></div><div className="dash-module-grid">{modules.map(m=>{const I=moduleIcons[m.key];return <button className="module-card" key={m.key} onClick={()=>setSection(m.key)}><span className="module-icon"><I size={25}/></span><span className="module-card-label">{moduleLabels[m.key]}</span><span className="module-count">{dashboard?.modules?.[m.key]||0} catatan <ArrowUpRight size={15}/></span></button>})}</div><div className="dash-section-title"><div><h2>Aktivitas terbaru</h2><p>Ringkasan data terkini dalam modul yang dapat Anda akses</p></div></div><div className="panel">{dashboard?.recent?.length?<div className="clean-list">{dashboard.recent.map(e=><div key={e.id}><div className="list-icon"><ClipboardList size={18}/></div><div><strong>{e.title}</strong><small>{moduleLabels[e.module]} · {formatDate(e.created_at)}</small></div><Tag>{e.status}</Tag></div>)}</div>:<Empty title="Belum ada aktivitas" subtitle="Entri yang ditambahkan pada modul kerja akan terlihat di sini."/>}</div></>;
  }
  function ModulesPage() {
    const canWrite=modules.find(m=>m.key===section)?.can_write;
    return <><div className="section-title"><div><span className="dash-kicker">MANAJEMEN DATA</span><h1>{moduleLabels[section]}</h1><p>Kelola catatan kegiatan, dokumen, target, dan penanggung jawab.</p></div></div>
      {canWrite&&<div className="panel form-panel"><h2>{entry.id?'Ubah':'Tambah'} catatan {moduleLabels[section]}</h2><div className="form-grid"><Input label="Judul" value={entry.title} onChange={v=>updateEntry('title',v)} placeholder="Judul catatan"/><Input label="Penanggung jawab" value={entry.assigned_to} onChange={v=>updateEntry('assigned_to',v)}/><SelectField label="Status" value={entry.status} onChange={v=>updateEntry('status',v)} options={user?.role==='mahasiswa'?['baru']:['baru','diproses','menunggu','selesai','dibatalkan']}/><Input type="date" label="Target tanggal" value={entry.due_at} onChange={v=>updateEntry('due_at',v)}/>{section==='keuangan'&&<Input type="number" label="Nominal (Rp)" value={entry.amount??''} onChange={v=>updateEntry('amount',v===''?null:Number(v))}/>}</div><Textarea label="Deskripsi / catatan" value={entry.body} onChange={v=>updateEntry('body',v)} rows={3}/><div className="form-actions"><IconButton icon={Save} kind="primary" disabled={busy||!entry.title.trim()} onClick={saveEntry}>{entry.id?'Simpan Perubahan':'Tambah Data'}</IconButton>{entry.id&&<IconButton icon={X} onClick={()=>setEntry({...emptyEntry,module:section})}>Batal</IconButton>}</div></div>}
      <div className="panel"><div className="panel-header"><h2>Daftar catatan <Tag>{entries.length}</Tag></h2></div>{entries.length?<div className="data-table-wrap"><table className="data-table"><thead><tr><th>Judul</th><th>Status</th><th>PIC</th><th>Target</th><th>Tindakan</th></tr></thead><tbody>{entries.map(e=><tr key={e.id}><td><strong>{e.title}</strong><small>{e.body}</small></td><td><Tag>{e.status}</Tag></td><td>{e.assigned_to||'—'}</td><td>{e.due_at||'—'}</td><td>{canWrite&&<div className="table-actions"><button onClick={()=>{setEntry({...e});window.scrollTo({top:0,behavior:'smooth'})}}><Pencil size={16}/></button><button onClick={()=>deleteEntry(e.id)}><Trash2 size={16}/></button></div>}</td></tr>)}</tbody></table></div>:<Empty title="Belum ada data" subtitle="Catatan dan pengajuan yang ditambahkan akan muncul pada daftar ini."/>}</div></>;
  }
  function MeetingsPage() {
    const done=meeting.tasks.filter(x=>x.status==='Selesai').length;
    return <><div className="section-title"><div><span className="dash-kicker">MEETING INTELLIGENCE</span><h1>Rapat & Tindak Lanjut</h1><p>Ubah catatan menjadi notula, keputusan, PIC, tenggat, dan progres yang terpantau.</p></div></div>
      {canMeet&&<div className="panel form-panel"><div className="panel-header"><h2>{meeting.id?'Edit Rapat':'Agenda Rapat Baru'}</h2><Tag color="softgold">Pemrosesan teks berbasis aturan</Tag></div><div className="form-grid"><Input label="Agenda Rapat" value={meeting.title} onChange={v=>updateMeeting('title',v)} placeholder="Rapat koordinasi BPKR"/><Input label="Tanggal" type="date" value={meeting.date} onChange={v=>updateMeeting('date',v)}/><Input label="Waktu" value={meeting.time} onChange={v=>updateMeeting('time',v)} placeholder="09.00–11.00 WIB"/><Input label="Tempat" value={meeting.place} onChange={v=>updateMeeting('place',v)}/></div><Input label="Peserta" value={meeting.participants} onChange={v=>updateMeeting('participants',v)}/><Textarea label="Catatan / Transkrip Rapat" rows={7} value={meeting.notes} onChange={v=>updateMeeting('notes',v)} placeholder="Pembahasan: ...\nKeputusan: ...\nTugas: ... | PIC: ... | Tenggat: 2026-11-30"/><div className="form-actions"><IconButton icon={Sparkles} kind="gold" disabled={!meeting.notes} onClick={parseMeeting}>Olah Catatan Rapat</IconButton><SelectField label="Status" value={meeting.status} onChange={v=>updateMeeting('status',v)} options={['draft','review',...((user.role==='pimpinan'||isAdmin)?['approved']:[])]}/></div>
      {(meeting.decisions.length>0||meeting.tasks.length>0||meeting.discussions.length>0)&&<div className="meeting-results"><div className="mini-stat-grid"><span><b>{meeting.decisions.length}</b> keputusan</span><span><b>{meeting.tasks.length}</b> tindak lanjut</span><span><b>{done}</b> selesai</span><span><b>{meeting.tasks.length?Math.round(done/meeting.tasks.length*100):0}%</b> progres</span></div><h3>Pokok pembahasan</h3>{meeting.discussions.map((x,i)=><p key={i}>• {x}</p>)}<h3>Keputusan</h3>{meeting.decisions.map((x,i)=><div className="decision" key={i}>{i+1}. {x}</div>)}<h3>Monitoring Tugas</h3>{meeting.tasks.map((task,i)=><div className="task-editor" key={i}><div className="form-grid"><Input label="Tindak lanjut" value={task.title||''} onChange={v=>setMeeting(p=>({...p,tasks:p.tasks.map((t,j)=>i===j?{...t,title:v}:t)}))}/><Input label="PIC" value={task.owner||''} onChange={v=>setMeeting(p=>({...p,tasks:p.tasks.map((t,j)=>i===j?{...t,owner:v}:t)}))}/><Input label="Tenggat" value={task.due||''} onChange={v=>setMeeting(p=>({...p,tasks:p.tasks.map((t,j)=>i===j?{...t,due:v}:t)}))}/><SelectField label="Status" value={task.status||'Belum mulai'} onChange={v=>setMeeting(p=>({...p,tasks:p.tasks.map((t,j)=>i===j?{...t,status:v}:t)}))} options={['Belum mulai','Proses','Selesai','Tertunda']}/></div><Input label="Catatan perkembangan" value={task.remark||''} onChange={v=>setMeeting(p=>({...p,tasks:p.tasks.map((t,j)=>i===j?{...t,remark:v}:t)}))}/></div>)}</div>}
      <div className="form-actions"><IconButton icon={Save} kind="primary" disabled={busy||!meeting.title.trim()} onClick={saveMeeting}>{meeting.id?'Simpan Perubahan':'Simpan Rapat'}</IconButton>{meeting.id&&<IconButton icon={RotateCcw} onClick={()=>setMeeting({...emptyMeeting})}>Rapat Baru</IconButton>}</div></div>}
      <div className="panel"><div className="panel-header"><h2>Arsip Rapat <Tag>{meetings.length}</Tag></h2></div>{meetings.length?<div className="clean-list">{meetings.map(m=><div key={m.id}><div className="list-icon"><CalendarDays/></div><div><strong>{m.title}</strong><small>{m.date} · {m.place} · {m.tasks?.filter(t=>t.status==='Selesai').length||0}/{m.tasks?.length||0} tugas selesai</small></div><Tag>{m.status}</Tag>{canMeet&&<div className="table-actions"><button onClick={()=>{setMeeting({...m});window.scrollTo(0,0)}} aria-label="Edit rapat"><Pencil size={16}/></button><button onClick={()=>deleteMeeting(m.id)} aria-label="Hapus rapat"><Trash2 size={16}/></button></div>}</div>)}</div>:<Empty title="Belum ada rapat tersimpan" subtitle="Notula dan rencana tindak lanjut akan tersedia di sini."/>}</div></>;
  }
  function LettersPage() {
    return <><div className="section-title"><div><span className="dash-kicker">DOCUMENT ASSISTANT</span><h1>Surat & Dokumen</h1><p>Susun, edit, review, dan simpan dokumen formal dalam alur administrasi.</p></div></div>
      {canLetters&&<div className="letter-grid"><div className="panel form-panel"><h2>{letter.id?'Edit Dokumen':'Susun Dokumen Baru'}</h2><SelectField label="Jenis dokumen" value={letter.kind} onChange={v=>updateLetter('kind',v)} options={['Surat keluar','Undangan rapat','Nota dinas','Laporan kegiatan']}/><Input label="Penerima" value={letter.recipient} onChange={v=>updateLetter('recipient',v)}/><Input label="Perihal" value={letter.subject} onChange={v=>updateLetter('subject',v)}/><Input label="Tanggal" type="date" value={letter.date} onChange={v=>updateLetter('date',v)}/><Textarea rows={5} label="Isi / instruksi dokumen" value={letter.instructions} onChange={v=>updateLetter('instructions',v)}/><Input label="Penandatangan (jabatan)" value={letter.signer} onChange={v=>updateLetter('signer',v)}/><div className="form-grid"><Input label="Nomor surat" value={letter.number} onChange={v=>updateLetter('number',v)}/><Input label="Lampiran" value={letter.attachment} onChange={v=>updateLetter('attachment',v)}/></div><SelectField label="Status persetujuan" value={letter.status} onChange={v=>updateLetter('status',v)} options={['draft','review',...((user.role==='pimpinan'||isAdmin)?['approved']:[])]}/><div className="form-actions"><IconButton icon={Save} kind="primary" disabled={busy||!letter.recipient.trim()||!letter.subject.trim()} onClick={saveLetter}>Simpan Dokumen</IconButton>{letter.id&&<IconButton icon={Plus} onClick={()=>setLetter({...emptyLetter})}>Baru</IconButton>}</div></div><div className="panel letter-preview-panel"><div className="panel-header"><h2>Pratinjau Dokumen</h2><Tag>{letter.status}</Tag></div><p className="hint">Isi pratinjau dapat disunting. Dokumen belum resmi sampai disahkan pejabat berwenang.</p><textarea className="letter-paper" aria-label="Isi dokumen" value={letter.body} onChange={e=>updateLetter('body',e.target.value)} placeholder="Pratinjau akan tampil setelah data disimpan. Konten dapat diedit langsung sebelum persetujuan."/><div className="form-actions"><IconButton icon={ClipboardList} onClick={()=>navigator.clipboard.writeText(letter.body||'')}>Salin</IconButton><IconButton icon={FileText} onClick={()=>window.print()}>Cetak / PDF</IconButton></div></div></div>}
      <div className="panel"><div className="panel-header"><h2>Arsip Dokumen <Tag>{letters.length}</Tag></h2></div>{letters.length?<div className="clean-list">{letters.map(l=><div key={l.id}><div className="list-icon"><FileText/></div><div><strong>{l.subject}</strong><small>{l.kind} · {l.recipient} · {l.date}</small></div><Tag>{l.status}</Tag>{canLetters&&<div className="table-actions"><button onClick={()=>{setLetter({...l});window.scrollTo(0,0)}}><Pencil size={16}/></button><button onClick={()=>deleteLetter(l.id)}><Trash2 size={16}/></button></div>}</div>)}</div>:<Empty title="Belum ada dokumen" subtitle="Surat dan dokumen akan tersimpan dan dapat ditinjau pada bagian ini."/>}</div></>;
  }
  function CMSPage() {
    return <><div className="section-title"><div><span className="dash-kicker">EDITORIAL WORKSPACE</span><h1>Manajemen Berita & Halaman</h1><p>Editor ala WordPress: konten kaya teks, gambar unggulan, kategori, slug, dan optimasi SEO.</p></div><IconButton kind="primary" icon={Plus} onClick={()=>{setEditPost({...emptyPost});window.scrollTo(0,0)}}>Artikel Baru</IconButton></div>
      <div className="panel form-panel"><div className="panel-header"><h2>{editPost.id?'Sunting Konten':'Tulis Artikel Baru'}</h2><Tag color="softgold">{editPost.status}</Tag></div><div className="form-grid"><SelectField label="Jenis konten" value={editPost.type} onChange={v=>updatePost('type',v)} options={[['news','Berita'],['page','Halaman']]}/><SelectField label="Status publikasi" value={editPost.status} onChange={v=>updatePost('status',v)} options={[['draft','Draf'],['published','Terbit'],['archived','Arsip']]}/></div><Input label="Judul artikel" value={editPost.title} onChange={v=>updatePost('title',v)} placeholder="Tuliskan judul informatif dan menarik"/><div className="form-grid"><Input label="Slug URL (otomatis bila kosong)" value={editPost.slug} onChange={v=>updatePost('slug',v)} placeholder="judul-artikel"/><Input label="Kategori" value={editPost.category} onChange={v=>updatePost('category',v)} placeholder="Kegiatan"/><Input label="Tag (pisahkan koma)" value={editPost.tags} onChange={v=>updatePost('tags',v)} placeholder="Rembang, UNDIP, Kolaborasi"/></div><Textarea label="Ringkasan / Excerpt" rows={3} value={editPost.excerpt} onChange={v=>updatePost('excerpt',v)} placeholder="Ringkasan singkat untuk kartu berita"/><label className="field"><span>Isi artikel (editor visual)</span></label><div className="editor-toolbar">{[['bold','B'],['italic','I'],['underline','U'],['insertUnorderedList','• List'],['insertOrderedList','1. List'],['formatBlock','H2']].map(([cmd,label])=><button key={cmd} onMouseDown={e=>e.preventDefault()} onClick={()=>{editorRef.current?.focus();document.execCommand(cmd,false,cmd==='formatBlock'?'h2':undefined)}}>{label}</button>)}<button onMouseDown={e=>e.preventDefault()} onClick={()=>{const url=prompt('URL tautan (https://)');if(url?.startsWith('https://')){editorRef.current?.focus();document.execCommand('createLink',false,url)}}}>Tautan</button></div>
      <div key={editPost.id||'new'} className="wysiwyg" ref={node=>{if(node&&!node.dataset.loaded){node.innerHTML=editPost.content||'';node.dataset.loaded='1'}}} contentEditable suppressContentEditableWarning data-placeholder="Mulai menulis artikel di sini..."/>
      <div className="image-field"><div className="form-grid"><Input label="URL gambar unggulan" value={editPost.image_url} onChange={v=>updatePost('image_url',v)} placeholder="/media/..." /><label className="upload-button"><ImagePlus size={18}/> Unggah gambar <input type="file" accept="image/jpeg,image/png,image/webp,image/gif" hidden onChange={e=>uploadImage(e.target.files[0])}/></label></div>{editPost.image_url&&<img src={editPost.image_url} alt="Pratinjau gambar unggulan" className="image-preview"/>}</div>
      <div className="form-grid"><Input label="SEO title" value={editPost.seo_title} onChange={v=>updatePost('seo_title',v)} placeholder="Opsional: judul untuk hasil pencarian"/><Input label="SEO description" value={editPost.seo_description} onChange={v=>updatePost('seo_description',v)} placeholder="Ringkasan meta Google dan AI"/></div>
      <div className="form-actions"><IconButton icon={Save} kind="primary" disabled={busy||editPost.title.trim().length<3} onClick={savePost}>Simpan Konten</IconButton>{editPost.id&&<IconButton icon={Plus} onClick={()=>setEditPost({...emptyPost})}>Konten Baru</IconButton>}</div></div>
      <div className="panel"><div className="panel-header"><h2>Semua Konten <Tag>{cmsPosts.length}</Tag></h2></div>{cmsPosts.length?<div className="data-table-wrap"><table className="data-table"><thead><tr><th>Judul</th><th>Kategori</th><th>Status</th><th>Diperbarui</th><th>Aksi</th></tr></thead><tbody>{cmsPosts.map(p=><tr key={p.id}><td><strong>{p.title}</strong><small>{p.slug}</small></td><td>{p.category}</td><td><Tag>{p.status}</Tag></td><td>{formatDate(p.updated_at)}</td><td><div className="table-actions"><button onClick={()=>{setEditPost({...p});window.scrollTo(0,0)}}><Pencil size={16}/></button>{p.status==='published'&&<a href={showArticle(p)} target="_blank" rel="noreferrer" aria-label="Lihat artikel"><Eye size={16}/></a>}<button onClick={()=>deletePost(p.id)}><Trash2 size={16}/></button></div></td></tr>)}</tbody></table></div>:<Empty title="Belum ada konten" subtitle="Tulis artikel untuk mengisi portal berita publik BPKR."/>}</div></>;
  }
  function UsersPage() {
    return <><div className="section-title"><div><span className="dash-kicker">ACCESS MANAGEMENT</span><h1>Pengguna & Role</h1><p>Kelola akses sistem dengan 10 peran dan pembatasan izin.</p></div></div><div className="panel form-panel"><h2>{editUser.id?'Edit Akun':'Tambah Pengguna'}</h2><div className="form-grid"><Input label="Username" value={editUser.username} onChange={v=>setEditUser(p=>({...p,username:v}))}/><Input label="Nama lengkap" value={editUser.full_name} onChange={v=>setEditUser(p=>({...p,full_name:v}))}/><Input label="Email (opsional)" type="email" value={editUser.email} onChange={v=>setEditUser(p=>({...p,email:v}))}/><SelectField label="Role" value={editUser.role} onChange={v=>setEditUser(p=>({...p,role:v}))} options={Object.entries(roleLabels).filter(([r])=>user.role==='superadmin'||r!=='superadmin').map(([r,label])=>[r,label])}/><Input type="password" label={editUser.id?'Kata sandi baru (kosong = tidak diubah)':'Kata sandi awal (min. 12 karakter)'} value={editUser.password} onChange={v=>setEditUser(p=>({...p,password:v}))}/></div><label className="checkbox-field"><input type="checkbox" checked={editUser.is_active} onChange={e=>setEditUser(p=>({...p,is_active:e.target.checked}))}/> Akun aktif</label><div className="form-actions"><IconButton kind="primary" icon={Save} disabled={busy||!editUser.username||!editUser.full_name||(!editUser.id&&editUser.password.length<12)} onClick={saveUser}>Simpan Akun</IconButton>{editUser.id&&<IconButton icon={X} onClick={()=>setEditUser({username:'',full_name:'',role:'tendik',email:'',password:'',is_active:true})}>Batal</IconButton>}</div></div>
      <div className="panel"><h2>Daftar Akun <Tag>{users.length}</Tag></h2><div className="data-table-wrap"><table className="data-table"><thead><tr><th>Username</th><th>Nama</th><th>Role</th><th>Status</th><th>Aksi</th></tr></thead><tbody>{users.map(u=><tr key={u.id}><td><strong>{u.username}</strong></td><td>{u.full_name}</td><td>{roleLabels[u.role]}</td><td><Tag>{u.is_active?'Aktif':'Nonaktif'}</Tag></td><td><div className="table-actions"><button onClick={()=>setEditUser({...u,password:''})}><Pencil size={16}/></button></div></td></tr>)}</tbody></table></div></div></>;
  }
  function SitePage() {
    return <><div className="section-title"><div><span className="dash-kicker">WEBSITE CUSTOMIZER</span><h1>Pengaturan Website</h1><p>Ubah identitas, headline, navigasi, dan informasi kontak seperti CMS WordPress.</p></div></div><div className="panel form-panel"><h2>Identitas & Landing Page</h2><div className="form-grid">{[['site_name','Nama Website'],['tagline','Tagline'],['hero_title','Judul Hero'],['hero_description','Deskripsi Hero'],['contact_email','Email'],['contact_phone','Nomor Telepon'],['contact_address','Alamat'],['footer_text','Teks Footer']].map(([key,label])=><Input key={key} label={label} value={site[key]||''} onChange={v=>setSite(p=>({...p,[key]:v}))}/>)}</div><Textarea label="Menu navigasi (JSON daftar title dan url internal)" rows={5} value={site.menus||''} onChange={v=>setSite(p=>({...p,menus:v}))}/><div className="form-actions"><IconButton kind="primary" icon={Save} disabled={busy} onClick={saveSite}>Simpan Pengaturan</IconButton><IconButton icon={ExternalLink} onClick={()=>navigate('/')}>Lihat Website</IconButton></div></div></>;
  }
  function AuditPage() {
    return <><div className="section-title"><div><span className="dash-kicker">ACCOUNTABILITY</span><h1>Audit Aktivitas</h1><p>Riwayat tindakan sistem untuk mendukung tata kelola.</p></div></div><div className="panel"><div className="data-table-wrap"><table className="data-table"><thead><tr><th>Waktu</th><th>Aktor ID</th><th>Perubahan</th><th>Entitas</th><th>Data ID</th></tr></thead><tbody>{audit.map(a=><tr key={a.id}><td>{formatDate(a.at)}</td><td>{a.actor_id}</td><td>{a.action}</td><td>{a.entity}</td><td>{a.entity_id}</td></tr>)}</tbody></table></div></div></>;
  }
  function AccountPage() {
    return <><div className="section-title"><div><span className="dash-kicker">ACCOUNT SECURITY</span><h1>Akun & Keamanan</h1><p>Atur kata sandi pribadi tanpa kehilangan akses ke menu dashboard sesuai role Anda.</p></div></div>
      <div className="panel account-panel">
        <div className="account-profile"><span className="user-avatar">{user?.full_name?.charAt(0)?.toUpperCase()||'B'}</span><div><strong>{user?.full_name}</strong><small>@{user?.username} · {roleLabels[user?.role]}</small></div><Tag color={user?.must_change_password?'softgold':''}>{user?.must_change_password?'Wajib ganti password':'Password sudah diganti'}</Tag></div>
        <h2>Ganti kata sandi</h2>
        <p className="hint">{user?.must_change_password?'Anda boleh melihat semua tampilan yang tersedia sesuai role. Untuk menjaga keamanan, ganti kata sandi awal sebelum membuat atau mengubah data.':'Anda dapat memperbarui kata sandi kapan saja melalui formulir berikut.'}</p>
        <form onSubmit={changePassword} className="account-password-form">
          <Input label="Kata sandi saat ini" type="password" required autoComplete="current-password" value={passwords.old_password} onChange={v=>setPasswords(p=>({...p,old_password:v}))}/>
          <Input label="Kata sandi baru (minimal 12 karakter)" type="password" required minLength={12} autoComplete="new-password" value={passwords.new_password} onChange={v=>setPasswords(p=>({...p,new_password:v}))}/>
          <IconButton type="submit" icon={ShieldCheck} kind="primary" disabled={busy||!passwords.old_password||passwords.new_password.length<12}>Perbarui Kata Sandi</IconButton>
        </form>
      </div></>;
  }
  function DashboardPage() {
    const nav=[['overview','Ringkasan',LayoutDashboard],...modules.map(m=>[m.key,moduleLabels[m.key],moduleIcons[m.key]]),
      ...(user?.role==='mahasiswa'?[]:[['meetings','Rapat & Tindak Lanjut',CalendarDays]]), ...(canLetters?[['letters','Surat & Dokumen',FileText]]:[]),
      ...(isEditor?[['cms','Berita & Halaman',Newspaper]]:[]),
      ...(isAdmin?[['site','Pengaturan Website',Settings],['users','Pengguna & Role',Users],['audit','Audit Aktivitas',ShieldCheck]]:[]),['account','Akun & Keamanan',LockKeyhole]];
    return <div className="dash-layout"><aside className="dash-sidebar"><div className="dash-logo"><img className="dash-logo-mark" src="/images/undip-logo.png" alt="Logo UNDIP"/><div><b>BPKR PORTAL</b><small>UNDIP · Kampus Rembang</small></div></div><div className="sidebar-label">WORKSPACE</div><nav>{nav.map(([key,title,I])=><button key={key} className={section===key?'selected':''} onClick={()=>{setSection(key);setError('');setToast('')}}><I size={19}/><span>{title}</span>{section===key&&<span className="selected-dot"/>}</button>)}</nav><div className="sidebar-bottom"><button onClick={()=>navigate('/')}><Globe2 size={18}/> Lihat Website</button><button onClick={logout}><LogOut size={18}/> Keluar</button></div></aside>
      <div className="dash-workspace"><div className="dash-topbar"><div className="dash-breadcrumb">BPKR / <strong>{section==='overview'?'Dashboard':moduleLabels[section]||nav.find(n=>n[0]===section)?.[1]}</strong></div><div className="top-user"><span className="user-avatar">{user?.full_name?.charAt(0)?.toUpperCase()||'B'}</span><span><strong>{user?.full_name}</strong><small>{roleLabels[user?.role]}</small></span><ChevronDown size={16}/></div></div>
      <div className="dash-main">
      {user?.must_change_password&&<div className="password-reminder" role="status"><div className="password-reminder-icon"><LockKeyhole size={21}/></div><div><strong>Kata sandi awal belum diganti</strong><p>Semua tampilan sesuai role tetap dapat dibuka. Ganti kata sandi untuk mengaktifkan fitur penyimpanan dan perubahan data.</p></div><button type="button" onClick={()=>setSection('account')}>Ganti sekarang <ArrowRight size={16}/></button></div>}
      {section==='overview'&&DashboardOverview()}{moduleLabels[section]&&ModulesPage()}{section==='meetings'&&MeetingsPage()}{section==='letters'&&LettersPage()}{section==='cms'&&CMSPage()}{section==='users'&&UsersPage()}{section==='site'&&SitePage()}{section==='audit'&&AuditPage()}{section==='account'&&AccountPage()}{error&&<div className="alert error" role="alert"><X size={17}/>{error}<button onClick={()=>setError('')}><X size={15}/></button></div>}{toast&&<div className="alert success"><CheckCircle2 size={17}/>{toast}<button onClick={()=>setToast('')}><X size={15}/></button></div>}</div></div></div>;
  }
  return <>{path==='/dashboard' ? (user? DashboardPage() : <>{Navbar()}{LoginPage()}</>) : <>{Navbar()}{path==='/login'?LoginPage():path==='/berita'?NewsPage():path==='/tentang'||path==='/layanan'||path==='/kontak'?InfoPage({kind:path.slice(1)}):HomePage()}</>}{path!=='/dashboard'&&error&&<div className="alert error" role="alert">{error}</div>}{path!=='/dashboard'&&toast&&<div className="alert success">{toast}</div>}</>;
}
createRoot(document.getElementById('root')).render(<App/>);

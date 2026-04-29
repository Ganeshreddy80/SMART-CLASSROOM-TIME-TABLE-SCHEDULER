
/* ═══════════════════════════════════════
   DATA — Single Source of Truth
   ═══════════════════════════════════════ */
const DATA={{ DATA | safe }};

/* ═══ GLOBALS ═══ */
let currentFaculty=null,currentRole=null,selectedLoginRole='faculty';
let attMarks={};
const SLOTS=["9-10","10-11","11-12","12-1","2-3","3-4","4-5"];
const DAYS=["Mon","Tue","Wed","Thu","Fri"];
const $=id=>document.getElementById(id);

/* ═══ UTILS ═══ */
function getInitials(n){return n.replace(/^Dr\.\s*/i,'').split(' ').map(w=>w[0]).join('').toUpperCase().slice(0,2)}
function getTodayKey(){return new Date().toISOString().split('T')[0]}
function getTodayDay(){return['Sun','Mon','Tue','Wed','Thu','Fri','Sat'][new Date().getDay()]}
function getSlotOrder(s){return SLOTS.indexOf(s)}
function getSlotStatus(s){const h=new Date().getHours();const p=s.split('-');let sh=+p[0],eh=+p[1];if(sh<8)sh+=12;if(eh<8||eh<=sh)eh+=12;if(h>=eh)return'done';if(h>=sh&&h<eh)return'ongoing';return'upcoming'}
function getGreeting(){const h=new Date().getHours();return h<12?'morning':h<17?'afternoon':'evening'}
function isFacultyAbsent(fid,d){const c=DATA.facultyAbsence[fid]&&DATA.facultyAbsence[fid][d];return Array.isArray(c)&&c.length>0;}
function isSlotCancelled(fid,d,slot){const c=DATA.facultyAbsence[fid]&&DATA.facultyAbsence[fid][d];return Array.isArray(c)&&c.includes(slot);}
function formatDate(d){return new Date(d||Date.now()).toLocaleDateString('en-IN',{weekday:'long',day:'numeric',month:'long',year:'numeric'})}
function getDayFromDate(d){return['Sun','Mon','Tue','Wed','Thu','Fri','Sat'][new Date(d).getDay()]}
function courseName(c){const co=DATA.courses.find(x=>x.code===c);return co?co.name:c}
function facName(fid){const f=DATA.faculty.find(x=>x.id===fid);return f?f.name:fid}
function avatarHtml(photo,name,size){
  const s=size||44;
  if(photo) return `<img src="${photo}" style="width:${s}px;height:${s}px;border-radius:50%;object-fit:cover">`;
  return `<div class="initials" style="width:${s}px;height:${s}px;border-radius:50%;background:linear-gradient(135deg,#7c3aed,#4f8ef7);color:#fff;font-size:${s*.35}px;font-weight:700;display:flex;align-items:center;justify-content:center">${getInitials(name)}</div>`;
}
function showToast(msg,type='default'){
  const w=$('toastWrap'),t=document.createElement('div');
  t.className='toast'+(type==='success'?' ts':type==='error'?' te':type==='warning'?' tw':type==='faculty'?' tf':'');
  t.textContent=msg;w.appendChild(t);
  setTimeout(()=>{t.style.transition='opacity .3s';t.style.opacity='0';setTimeout(()=>t.remove(),300)},2800);
}
function myTimetable(){return DATA.timetable.filter(t=>t.faculty===currentFaculty.id)}
function myTodayClasses(){const d=getTodayDay();return myTimetable().filter(t=>t.day===d).sort((a,b)=>getSlotOrder(a.slot)-getSlotOrder(b.slot))}

/* ═══ LOGIN ═══ */
function setRole(btn,role){
  document.querySelectorAll('.role-tab').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');selectedLoginRole=role;
  const hints={admin:['admin@srmap.edu.in','admin123'],faculty:['arun.kumar@srmap.edu.in','arun.kumar@123'],student:['manish.singh@srmap.edu.in','student123']};
  $('logEmail').placeholder=hints[role][0];$('logPass').placeholder=hints[role][1];
}
function doLogin(){
  const e=$('logEmail').value.trim().toLowerCase(),p=$('logPass').value.trim();
  if(!e||!p){showToast('❌ Please fill in both fields','error');return}
  // All roles: POST to Flask /login for proper session auth
  showToast('🔄 Redirecting...','faculty');
  const form=document.createElement('form');
  form.method='POST';form.action='/login';form.style.display='none';
  const emailIn=document.createElement('input');emailIn.name='email';emailIn.value=e;form.appendChild(emailIn);
  const passIn=document.createElement('input');passIn.name='password';passIn.value=p;form.appendChild(passIn);
  document.body.appendChild(form);
  setTimeout(()=>form.submit(),400);
}
function doLogout(){currentFaculty=currentRole=null;$('appView').style.display='none';$('loginView').style.display='flex';$('logEmail').value='';$('logPass').value=''}

/* ═══ INIT ═══ */
function initApp(){
  const _sp = localStorage.getItem('faculty_photo_' + currentFaculty.id);
  if (_sp) { currentFaculty.photo = _sp; DATA.faculty.find(f => f.id === currentFaculty.id).photo = _sp; }
  $('loginView').style.display='none';$('appView').style.display='block';
  buildSidebar();buildTopbar();showPage('dashboard');
}

/* ═══ SIDEBAR ═══ */
function buildSidebar(){
  const f=currentFaculty;
  $('sidebar').innerHTML=`
  <div class="sb-brand"><span class="sb-icon">📅</span><span class="sb-title">UniSchedule</span><span class="sb-sub">Faculty Portal</span></div>
  <div class="sb-section">OVERVIEW</div>
  <ul class="sb-nav">
    <li><a class="active" data-page="dashboard" onclick="showPage('dashboard')">🏠 Dashboard</a></li>
  </ul>
  <div class="sb-section">TIMETABLE</div>
  <ul class="sb-nav">
    <li><a data-page="mytt" onclick="showPage('mytt')">📅 My Timetable</a></li>
    <li><a data-page="fulltt" onclick="showPage('fulltt')">📆 Full Timetable</a></li>
  </ul>
  <div class="sb-section">MY SECTIONS</div>
  <ul class="sb-nav">
    <li><a data-page="sections" onclick="showPage('sections')">👥 My Sections</a></li>
    <li><a data-page="stutt" onclick="showPage('stutt')">🎓 Student Timetable</a></li>
  </ul>
  <div class="sb-section">ATTENDANCE</div>
  <ul class="sb-nav">
    <li><a data-page="markatt" onclick="showPage('markatt')">📝 Mark Attendance</a></li>
  </ul>
  <div class="sb-section">ABSENCE</div>
  <ul class="sb-nav">
    <li><a data-page="absence" onclick="showPage('absence')">🚫 Report Absence</a></li>
  </ul>
  <div class="sb-footer" id="sbFooter">
    <div class="sb-footer-avatar" id="sbAvatar">${f.photo?`<img src="${f.photo}">`:`<div class="initials">${getInitials(f.name)}</div>`}</div>
    <div class="sb-footer-info">
      <div class="sb-fn">${f.name}</div>
      <div class="sb-desig">${f.designation}</div>
      <div class="sb-dept-pill">${f.dept}</div>
    </div>
  </div>`;
}
function buildTopbar(){
  const f=currentFaculty;
  $('topbar').innerHTML=`
  <input class="tb-search" placeholder="🔍 Search resources, students...">
  <div class="tb-right">
    <span class="tb-bell">🔔</span>
    <div class="tb-user">
      <div class="tb-user-av" id="tbAvatar">${f.photo?`<img src="${f.photo}">`:`<div class="initials">${getInitials(f.name)}</div>`}</div>
      <span>${f.name} <small>(Faculty)</small></span>
    </div>
    <button class="btn-logout" onclick="doLogout()">🚪 Logout</button>
  </div>`;
}

/* ═══ PAGE ROUTING ═══ */
let currentPageArgs={};
function showPage(page,args){
  currentPageArgs=args||{};
  document.querySelectorAll('.sb-nav a').forEach(a=>{a.classList.toggle('active',a.dataset.page===page)});
  const m=$('mainArea');
  switch(page){
    case'dashboard':m.innerHTML=`<div class="page">${pgDashboard()}</div>`;break;
    case'mytt':m.innerHTML=`<div class="page">${pgMyTimetable()}</div>`;break;
    case'fulltt':m.innerHTML=`<div class="page">${pgFullTimetable()}</div>`;break;
    case'sections':m.innerHTML=`<div class="page">${pgSections()}</div>`;setTimeout(()=>renderSectionStudents(currentPageArgs.secId),50);break;
    case'stutt':m.innerHTML=`<div class="page">${pgStudentTimetable()}</div>`;break;
    case'markatt':m.innerHTML=`<div class="page">${pgMarkAttendance()}</div>`;break;
    case'absence':m.innerHTML=`<div class="page">${pgAbsence()}</div>`;break;
  }
}

/* ═══ PHOTO UPLOAD ═══ */
$('photoInput').addEventListener('change',function(e){
  const file=e.target.files[0];if(!file)return;
  if(!file.type.startsWith('image/')){showToast('Please select an image file','error');return}
  if(file.size>5*1024*1024){showToast('Photo too large. Max 5MB.','error');return}
  const reader=new FileReader();
  reader.onload=ev=>{
    currentFaculty.photo=ev.target.result;
    localStorage.setItem('faculty_photo_' + currentFaculty.id, ev.target.result);
    DATA.faculty.find(f=>f.id===currentFaculty.id).photo=ev.target.result;
    rerenderPhotoEverywhere();
    showToast('✅ Profile photo updated!','success');
  };
  reader.readAsDataURL(file);
  e.target.value='';
});
function triggerPhotoUpload(){$('photoInput').click()}
function rerenderPhotoEverywhere(){
  const f=currentFaculty;const img=f.photo?`<img src="${f.photo}">`:`<div class="initials">${getInitials(f.name)}</div>`;
  const sa=$('sbAvatar');if(sa)sa.innerHTML=img;
  const ta=$('tbAvatar');if(ta)ta.innerHTML=img;
  const hc=document.getElementById('heroPhotoCircle');if(hc)hc.innerHTML=f.photo?`<img src="${f.photo}">`:`<div class="initials" style="font-size:40px">${getInitials(f.name)}</div>`;
}

/* ═══════════════════════════════════════
   PAGE 0 — DASHBOARD
   ═══════════════════════════════════════ */
function pgDashboard(){
  const f=currentFaculty,tt=myTimetable(),today=myTodayClasses();
  const absent=isFacultyAbsent(f.id,getTodayKey());
  const mySecs=f.assignedSections.map(sid=>DATA.sections.find(s=>s.id===sid)).filter(Boolean);
  return `
  <!-- HERO -->
  <div class="hero-card">
    <div class="hero-photo">
      <div class="photo-circle" id="heroPhotoCircle" onclick="triggerPhotoUpload()">
        ${f.photo?`<img src="${f.photo}">`:`<div class="initials" style="font-size:40px">${getInitials(f.name)}</div>`}
        <div class="photo-overlay"><span>📷</span><small>Change Photo</small></div>
      </div>
      ${!f.photo ? `<button class="upload-btn" onclick="triggerPhotoUpload()">📷 Upload Photo</button>` : ''}
    </div>
    <div class="hero-info">
      <h1>${f.name}</h1>
      <span class="hero-id">${f.id}</span>
      <div class="hero-sub">${f.designation} · ${f.dept}</div>
      <div class="hero-spec">Specialization: ${f.specialization}</div>
      <div class="hero-contact"><span>📧 ${f.email}</span><span>📞 ${f.phone}</span><span>🚪 ${f.cabinNo}</span></div>
    </div>
    <div class="hero-stats">
      <div class="hstat"><div class="hv">${tt.length}</div><div class="hl">📅 Classes/Week</div></div>
      <div class="hstat"><div class="hv">${f.canTeach.length}</div><div class="hl">📚 Courses</div></div>
      <div class="hstat"><div class="hv">${f.assignedSections.length}</div><div class="hl">👥 Sections</div></div>
      <div class="hstat"><div class="hv">${absent?'—':today.length}</div><div class="hl">⚡ Today</div></div>
    </div>
    ${absent?'<div class="absent-banner">🚫 You are marked absent today — Classes cancelled for students</div>':''}
  </div>

  <!-- DETAILS -->
  <div class="det-grid">
    <div class="det-card">
      <h3>👤 Personal Information</h3>
      ${[['Full Name',f.name],['Faculty ID',f.id],['Designation',f.designation],['Email',f.email],['Phone',f.phone],['Cabin',f.cabinNo],['Joining Date',f.joiningDate],['Experience',f.experience]].map(r=>`<div class="det-row"><span class="det-l">${r[0]}</span><span class="det-v">${r[1]}</span></div>`).join('')}
    </div>
    <div class="det-card">
      <h3>🎓 Academic Information</h3>
      <div class="det-row"><span class="det-l">Department</span><span class="det-v">${f.dept}</span></div>
      <div class="det-row"><span class="det-l">Specialization</span><span class="det-v">${f.specialization}</span></div>
      <div class="det-row"><span class="det-l">Courses Teaching</span><span class="det-v">${f.canTeach.map(c=>`<span class="pill pill-purple">${c}</span>`).join('')}</span></div>
      <div class="det-row"><span class="det-l">Assigned Sections</span><span class="det-v">${mySecs.map(s=>`<span class="pill pill-gold" style="cursor:pointer" onclick="showPage('sections',{secId:'${s.id}'})">${s.name}</span>`).join('')}</span></div>
    </div>
  </div>

  <!-- ASSIGNED SECTIONS -->
  <div class="section-title">👥 My Assigned Sections</div>
  ${mySecs.map(sec=>{
    const stuList=sec.students.map(sid=>DATA.students.find(s=>s.id===sid)).filter(Boolean);
    const myClassesHere=DATA.timetable.filter(t=>t.section===sec.id&&t.faculty===f.id);
    const myCourses=[...new Set(myClassesHere.map(t=>t.course))];
    return `<div class="sec-card">
      <div class="sec-card-top">
        <h3>${sec.name}</h3><span class="pill pill-purple">${sec.dept}</span><span class="pill pill-gold">Sem ${sec.semester} · Year ${sec.year}</span>
      </div>
      <div class="sec-stats">
        <span class="sec-stat">👥 <strong>${stuList.length}</strong> Students</span>
        <span class="sec-stat">📚 <strong>${sec.courses.length}</strong> Courses</span>
        <span class="sec-stat">⚡ <strong>${myClassesHere.length}</strong> My Classes/Week</span>
      </div>
      <div class="sec-courses"><div class="sec-courses-label">Courses you teach here:</div>${myCourses.map(c=>`<span class="pill pill-purple">${c} — ${courseName(c)}</span>`).join('')}</div>
      <div style="margin: 10px 0; padding: 10px; background: var(--surface2); border-radius: 8px;">
        <div style="font-size: 0.75rem; font-weight: 700; margin-bottom: 6px; color: var(--navy);">📈 Class-wise Attendance</div>
        ${myCourses.map(c => {
            const att = DATA.attendance[`${c}_${sec.id}`];
            const pct = att ? att.pct : 0;
            const color = pct < 75 ? 'var(--danger)' : 'var(--success)';
            return `<div style="display:flex; justify-content:space-between; font-size: 0.75rem; padding: 4px 0;">
                <span>${c}</span>
                <span style="color: ${color}; font-weight: 700;">${pct}%</span>
            </div>`;
        }).join('') || '<div style="font-size:0.75rem; color:var(--muted);">No attendance data</div>'}
      </div>
      <div class="sec-avatars">${stuList.slice(0,3).map(s=>`<div class="sec-av">${getInitials(s.name)}</div>`).join('')}${stuList.length>3?`<div class="sec-av sec-av-more">+${stuList.length-3}</div>`:''}</div>
      <div class="sec-actions">
        <button class="btn btn-purple-o" onclick="showPage('sections',{secId:'${sec.id}'})">👥 View Students →</button>
        <button class="btn btn-purple" onclick="showPage('markatt',{secId:'${sec.id}'})">📝 Mark Attendance →</button>
        <button class="btn btn-gold-o" onclick="showPage('stutt',{secId:'${sec.id}'})">🎓 Student Timetable →</button>
      </div>
    </div>`;
  }).join('')}

  <!-- TODAY'S SCHEDULE -->
  <div class="card">
    <div class="card-title">📅 Today's Schedule — ${getTodayDay()}</div>
    <div style="font-size:.8rem;color:var(--muted);margin-bottom:14px">${formatDate()}</div>
    ${today.length===0||getTodayDay()==='Sun'||getTodayDay()==='Sat'?
      `<div class="empty-state" style="border:2px dashed var(--gold);border-radius:14px"><span class="es-icon">🎉</span>No classes scheduled today. Enjoy your day!</div>`:
      `<div style="display:flex;gap:10px;flex-wrap:wrap">${today.map(t=>{
        const st=getSlotStatus(t.slot),sec=DATA.sections.find(s=>s.id===t.section);
        const slotCancel=isSlotCancelled(f.id,getTodayKey(),t.slot);
        const cls=slotCancel?'cancelled':'';
        return `<div class="tl-card ${cls}" style="min-width:200px;flex:1">
          <div style="font-weight:700;font-size:.85rem">${t.slot.replace('-',' – ')}</div>
          <div><span class="pill pill-purple">${t.course}</span> <span class="pill pill-gold">${sec?.name||t.section}</span></div>
          <div style="font-size:.75rem;color:var(--muted);margin-top:4px">📍 ${t.room}</div>
          <span class="tl-status ${slotCancel?'cancel':st}">${slotCancel?'🚫 CANCELLED':st==='ongoing'?'🟢 ONGOING':st==='done'?'✅ DONE':'🔵 UPCOMING'}</span>
        </div>`;
      }).join('')}</div>`}
  </div>`;
}

/* ═══════════════════════════════════════
   PAGE 1 — MY TIMETABLE (today view)
   ═══════════════════════════════════════ */
function pgMyTimetable(){
  const f=currentFaculty,today=myTodayClasses(),d=getTodayDay(),absent=isFacultyAbsent(f.id,getTodayKey());
  const firstName=f.name.replace(/^Dr\.\s*/i,'').split(' ')[0];
  let html=`<h2 style="margin-bottom:4px">Good ${getGreeting()}, ${firstName}! 👋</h2>
  <div style="font-size:.88rem;color:var(--muted);margin-bottom:18px">${formatDate()}</div>`;
  if(absent) html+=`<div style="background:#fee2e2;border:1px solid rgba(239,68,68,.3);border-radius:14px;padding:14px 20px;margin-bottom:18px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px">
    <span style="font-size:.85rem;color:#dc2626;font-weight:600">🚫 You have declared absence for today. All classes cancelled.</span>
    <button class="btn btn-purple-o" onclick="undoFacultyAbsence()">↩️ Undo — I Am Coming</button></div>`;
  if(today.length===0||d==='Sun'||d==='Sat'){
    html+=`<div class="card"><div class="empty-state" style="border:2px dashed var(--gold);border-radius:14px"><span class="es-icon">🎉</span>No classes today! Enjoy your day off.</div></div>`;
  } else {
    html+=`<div class="timeline">`;
    const morning=today.filter(t=>getSlotOrder(t.slot)<3),afternoon=today.filter(t=>getSlotOrder(t.slot)>=4);
    [morning,afternoon].forEach((group,gi)=>{
      if(gi===1&&morning.length>0) html+=`<div class="lunch-card">🍽️ Lunch Break · 12:00 – 1:00 PM</div>`;
      group.forEach(t=>{
        const st=getSlotStatus(t.slot),sec=DATA.sections.find(s=>s.id===t.section),stuCount=sec?sec.students.length:0;
        const slotCancel=isSlotCancelled(f.id,getTodayKey(),t.slot);
        const cls=slotCancel?'cancelled':'';
        html+=`<div class="tl-item"><div class="tl-dot"></div>
          <div class="tl-time">${t.slot.replace('-',' – ')} · 1 hr</div>
          <div class="tl-card ${cls}">
            <span class="tl-status ${slotCancel?'cancel':st}">${slotCancel?'🚫 CANCELLED':st==='ongoing'?'🟢 ONGOING':st==='done'?'✅ DONE':'🔵 UPCOMING'}</span>
            <div><span class="pill pill-purple">${t.course}</span> <strong style="font-size:.88rem">${courseName(t.course)}</strong></div>
            <div style="margin-top:6px"><span class="pill pill-gold">${sec?.name||t.section}</span> <span style="font-size:.78rem;color:var(--muted)">📍 ${t.room}</span></div>
            <div style="font-size:.75rem;color:var(--muted);margin-top:4px">👥 ${stuCount} students</div>
            ${slotCancel?'<div style="background:#fee2e2;border-radius:8px;padding:6px 10px;margin-top:8px;font-size:.75rem;color:#dc2626;font-weight:600">Class cancelled — Faculty absent</div>':''}
          </div></div>`;
      });
    });
    html+=`</div>`;
  }
  html+=`<div style="margin-top:18px"><button class="btn btn-purple" onclick="showPage('fulltt')">📆 View Full Week Timetable →</button></div>`;
  return html;
}

/* ═══════════════════════════════════════
   PAGE 2 — FULL TIMETABLE (week grid)
   ═══════════════════════════════════════ */
function pgFullTimetable(){
  const f=currentFaculty,tt=myTimetable(),d=getTodayDay();
  const totalStudents=[...new Set(f.assignedSections.flatMap(sid=>{const s=DATA.sections.find(x=>x.id===sid);return s?s.students:[]}))].length;
  let html=`<div class="section-title">📆 My Full Timetable</div>
  <div style="font-size:.82rem;color:var(--muted);margin-bottom:16px">You teach <strong>${totalStudents}</strong> students across <strong>${f.assignedSections.length}</strong> sections</div>
  <div class="tt-grid">`;
  html+=`<div class="tt-hdr"></div>`;
  DAYS.forEach(day=>html+=`<div class="tt-hdr ${day===d?'today-col':''}">${day}</div>`);
  SLOTS.forEach(slot=>{
    if(slot==='12-1'){
      html+=`<div class="tt-time">12–1</div>`;
      DAYS.forEach(day=>html+=`<div class="tt-cell lunch ${day===d?'today-col':''}">🍽️ Lunch</div>`);
      return;
    }
    html+=`<div class="tt-time">${slot}</div>`;
    DAYS.forEach(day=>{
      const entry=tt.find(t=>t.day===day&&t.slot===slot);
      const isToday=day===d;
      if(entry){
        const sec=DATA.sections.find(s=>s.id===entry.section);
        const cancelled=isSlotCancelled(f.id,getTodayKey(),slot)&&isToday;
        html+=`<div class="tt-cell ${isToday?'today-col':''} ${cancelled?'cancelled':''}">
          <div class="cc">${entry.course}</div>
          <div class="cn">${courseName(entry.course)}</div>
          <div><span class="pill pill-gold" style="font-size:.55rem;padding:1px 6px">${sec?.name||entry.section}</span></div>
          <div class="cr">📍 ${entry.room}</div>
          ${cancelled?'<div style="color:var(--danger);font-size:.6rem;font-weight:700">🚫 Cancelled</div>':''}
        </div>`;
      } else {
        html+=`<div class="tt-cell empty ${isToday?'today-col':''}">—</div>`;
      }
    });
  });
  html+=`</div>`;
  return html;
}

/* ═══════════════════════════════════════
   PAGE 3 — MY SECTIONS
   ═══════════════════════════════════════ */
function pgSections(){
  const f=currentFaculty,secs=f.assignedSections.map(sid=>DATA.sections.find(s=>s.id===sid)).filter(Boolean);
  const defSec=currentPageArgs.secId||secs[0]?.id||'';
  return `<div class="section-title">👥 My Sections</div>
  <div style="font-size:.82rem;color:var(--muted);margin-bottom:16px">Students in your assigned sections</div>
  <div class="sec-tabs" id="secTabs">${secs.map(s=>`<button class="sec-tab ${s.id===defSec?'active':''}" onclick="switchSecTab('${s.id}')">${s.name}</button>`).join('')}</div>
  <div id="secInfoBanner"></div>
  <input class="search-input" id="secSearch" placeholder="🔍 Search students by name or reg no..." oninput="filterSectionStudents()">
  <div id="secStudentList"></div>`;
}
function switchSecTab(secId){
  document.querySelectorAll('.sec-tab').forEach(t=>t.classList.toggle('active',t.textContent===DATA.sections.find(s=>s.id===secId)?.name));
  renderSectionStudents(secId);
}
function renderSectionStudents(secId){
  const f=currentFaculty;
  const secs=f.assignedSections.map(sid=>DATA.sections.find(s=>s.id===sid)).filter(Boolean);
  const sec=secId?DATA.sections.find(s=>s.id===secId):secs[0];
  if(!sec)return;
  // Update tab active
  document.querySelectorAll('.sec-tab').forEach(t=>t.classList.toggle('active',t.textContent===sec.name));
  const banner=$('secInfoBanner');
  if(banner) banner.innerHTML=`<div class="sec-info-banner"><h3>${sec.name}</h3><div class="sib-details"><span>${sec.dept}</span><span>Semester ${sec.semester}</span><span>Year ${sec.year}</span><span>👥 ${sec.students.length} Students</span><span>📚 ${sec.courses.length} Courses</span></div></div>`;
  const list=$('secStudentList');
  if(!list)return;
  const stuList=sec.students.map(sid=>DATA.students.find(s=>s.id===sid)).filter(Boolean);
  list.innerHTML=`<div style="font-size:.78rem;color:var(--muted);margin-bottom:10px">Showing ${stuList.length} students</div>`+
  stuList.map(s=>`<div class="stu-card" data-name="${s.name.toLowerCase()}" data-reg="${s.regNo.toLowerCase()}">
    <div class="stu-av">${avatarHtml(s.photo,s.name,44)}</div>
    <div class="stu-info">
      <div class="sn">${s.name}</div>
      <div class="sr">${s.regNo}</div>
      <span class="pill pill-purple">${s.dept}</span> <span class="pill pill-gold">CGPA: ${s.cgpa}</span>
    </div>
    <div class="stu-actions">
      <button class="btn btn-purple-o" style="font-size:.7rem;padding:6px 10px" onclick="showPage('stutt',{secId:'${sec.id}',stuId:'${s.id}'})">🎓 Timetable</button>
    </div>
  </div>`).join('');
  // Store current sec for search
  list.dataset.secId=sec.id;
}
function filterSectionStudents(){
  const q=$('secSearch').value.toLowerCase();
  document.querySelectorAll('.stu-card').forEach(c=>{
    const n=c.dataset.name,r=c.dataset.reg;
    c.style.display=(n.includes(q)||r.includes(q))?'flex':'none';
  });
}

/* ═══════════════════════════════════════
   PAGE 4 — STUDENT TIMETABLE VIEWER
   ═══════════════════════════════════════ */
function pgStudentTimetable(){
  const f=currentFaculty,secs=f.assignedSections.map(sid=>DATA.sections.find(s=>s.id===sid)).filter(Boolean);
  const defSec=currentPageArgs.secId||'';
  return `<div class="section-title">🎓 Student Timetable Viewer</div>
  <div style="font-size:.82rem;color:var(--muted);margin-bottom:18px">View any student's timetable from your sections</div>
  <div class="step-card">
    <div class="step-label">Step 1: Choose Section</div>
    <select class="sel" id="stvSecSel" onchange="stvLoadStudents()">
      <option value="">— Select Section —</option>
      ${secs.map(s=>`<option value="${s.id}" ${s.id===defSec?'selected':''}>${s.name}</option>`).join('')}
    </select>
  </div>
  <div id="stvStep2"></div>
  <div id="stvStep3"></div>`;
}
// Auto-trigger if pre-selected
function stvAutoLoad(){setTimeout(()=>{if($('stvSecSel')&&$('stvSecSel').value)stvLoadStudents()},100)}
function stvLoadStudents(){
  const secId=$('stvSecSel').value;
  const step2=$('stvStep2'),step3=$('stvStep3');
  step3.innerHTML='';
  if(!secId){step2.innerHTML='';return}
  const sec=DATA.sections.find(s=>s.id===secId);
  if(!sec){step2.innerHTML='';return}
  const stuList=sec.students.map(sid=>DATA.students.find(s=>s.id===sid)).filter(Boolean);
  const defStu=currentPageArgs.stuId||'';
  
  step2.innerHTML=`
  <div style="font-size:.78rem;color:var(--muted);margin-bottom:10px">Showing ${stuList.length} students</div>
  <div id="stvStudentList" style="animation:slideUp .4s">
  ${stuList.map(s=>`<div class="stu-card" data-name="${s.name.toLowerCase()}" data-reg="${s.regNo.toLowerCase()}">
    <div class="stu-av">${avatarHtml(s.photo,s.name,44)}</div>
    <div class="stu-info">
      <div class="sn">${s.name}</div>
      <div class="sr">${s.regNo}</div>
      <span class="pill pill-purple">${s.dept}</span> <span class="pill pill-gold">CGPA: ${s.cgpa}</span>
    </div>
    <div class="stu-actions">
      <button class="btn btn-purple-o" style="font-size:.7rem;padding:6px 10px" onclick="stvShowTimetableFor('${sec.id}', '${s.id}')">🎓 View Timetable</button>
    </div>
  </div>`).join('')}
  </div>`;
  
  if(defStu)setTimeout(()=>stvShowTimetableFor(sec.id, defStu),100);
}
function stvShowTimetableFor(secId, stuId){
  const step3=$('stvStep3');
  if(!stuId){step3.innerHTML='';return}
  const stu=DATA.students.find(s=>s.id===stuId);
  const sec=DATA.sections.find(s=>s.id===secId);
  if(!stu||!sec){step3.innerHTML='';return}
  const entries=DATA.timetable.filter(t=>t.section===secId);
  const d=getTodayDay();
  let html=`<div class="stv-student-banner" style="animation:slideUp .4s">
    <div class="stv-av">${avatarHtml(stu.photo,stu.name,60)}</div>
    <div class="stv-info"><h3>${stu.name}</h3><span class="stv-reg">${stu.regNo}</span><p>${sec.name} · ${stu.dept} · Semester ${stu.semester}</p></div>
  </div>`;
  // Grid
  html+=`<div class="tt-grid">`;
  html+=`<div class="tt-hdr"></div>`;
  DAYS.forEach(day=>html+=`<div class="tt-hdr ${day===d?'today-col':''}">${day}</div>`);
  SLOTS.forEach(slot=>{
    if(slot==='12-1'){
      html+=`<div class="tt-time">12–1</div>`;
      DAYS.forEach(day=>html+=`<div class="tt-cell lunch ${day===d?'today-col':''}">🍽️ Lunch</div>`);
      return;
    }
    html+=`<div class="tt-time">${slot}</div>`;
    DAYS.forEach(day=>{
      const entry=entries.find(t=>t.day===day&&t.slot===slot);
      const isToday=day===d;
      if(entry){
        const co=DATA.courses.find(c=>c.code===entry.course);
        const cancelled=isSlotCancelled(entry.faculty,getTodayKey(),slot)&&isToday;
        const cellType=co&&co.type==='Lab'?'background:rgba(124,58,237,.04)':'background:rgba(79,142,247,.04)';
        html+=`<div class="tt-cell ${isToday?'today-col':''} ${cancelled?'cancelled':''}" style="${cancelled?'':cellType}">
          <div class="cc">${entry.course}</div>
          <div class="cn">${facName(entry.faculty)}</div>
          <div class="cr">📍 ${entry.room}</div>
          ${cancelled?'<div style="color:var(--danger);font-size:.58rem;font-weight:700">🚫</div>':''}
        </div>`;
      } else {
        html+=`<div class="tt-cell empty ${isToday?'today-col':''}">—</div>`;
      }
    });
  });
  html+=`</div>`;
  step3.innerHTML=html;
  step3.scrollIntoView({behavior: "smooth", block: "start"});
  currentPageArgs={};
}

/* ═══════════════════════════════════════
   PAGE 5 — MARK ATTENDANCE
   ═══════════════════════════════════════ */
function pgMarkAttendance(){
  const f=currentFaculty,secs=f.assignedSections.map(sid=>DATA.sections.find(s=>s.id===sid)).filter(Boolean);
  const defSec=currentPageArgs.secId||'';
  return `<div class="section-title">📝 Mark Attendance</div>
  <div style="font-size:.82rem;color:var(--muted);margin-bottom:16px">Call students by name and mark their attendance</div>
  <div class="card">
    <div class="ctrl-grid">
      <div><div class="step-label">Select Section</div><select class="sel" id="attSecSel" onchange="attUpdateSlots()" style="width:100%">
        <option value="">— Section —</option>
        ${secs.map(s=>`<option value="${s.id}" ${s.id===defSec?'selected':''}>${s.name}</option>`).join('')}
      </select></div>
      <div><div class="step-label">Date</div><input type="date" class="sel" id="attDate" value="${getTodayKey()}" max="${getTodayKey()}" onchange="attUpdateSlots()" style="width:100%"></div>
      <div><div class="step-label">Select Class Slot</div><select class="sel" id="attSlotSel" style="width:100%"><option value="">— select section first —</option></select></div>
    </div>
    <button class="btn btn-purple btn-full btn-lg" id="loadRollBtn" onclick="loadAttendanceRollCall()" style="margin-top:8px" disabled>📋 Load Students</button>
  </div>
  <div id="attBanner"></div>
  <div id="attRollArea"></div>`;
}
function attUpdateSlots(){
  const secId=$('attSecSel').value,dateStr=$('attDate').value;
  const slotSel=$('attSlotSel'),loadBtn=$('loadRollBtn');
  slotSel.innerHTML='<option value="">— no slots —</option>';
  loadBtn.disabled=true;
  if(!secId||!dateStr)return;
  const day=getDayFromDate(dateStr);
  if(day==='Sun'||day==='Sat'){slotSel.innerHTML='<option value="">No classes on weekends</option>';return}
  const slots=DATA.timetable.filter(t=>t.section===secId&&t.faculty===currentFaculty.id&&t.day===day).sort((a,b)=>getSlotOrder(a.slot)-getSlotOrder(b.slot));
  if(slots.length===0){slotSel.innerHTML='<option value="">No classes for this section on '+day+'</option>';return}
  slotSel.innerHTML='<option value="">— Select Slot —</option>'+slots.map(s=>`<option value="${s.slot}" data-course="${s.course}">${s.slot.replace('-',' – ')} — ${courseName(s.course)}</option>`).join('');
  slotSel.onchange=()=>{loadBtn.disabled=!slotSel.value};
}
function loadAttendanceRollCall(){
  const secId=$('attSecSel').value,dateStr=$('attDate').value,slot=$('attSlotSel').value;
  if(!secId||!dateStr||!slot)return;
  const courseOpt=$('attSlotSel').selectedOptions[0];
  const courseCode=courseOpt.dataset.course;
  const sec=DATA.sections.find(s=>s.id===secId);
  if(!sec)return;
  const entry=DATA.timetable.find(t=>t.section===secId&&t.faculty===currentFaculty.id&&t.day===getDayFromDate(dateStr)&&t.slot===slot);
  if(!entry)return;
  const stuList=sec.students.map(sid=>DATA.students.find(s=>s.id===sid)).filter(Boolean).sort((a,b)=>a.name.localeCompare(b.name));
  // Check existing
  let hasExisting=false;
  attMarks={};
  stuList.forEach(s=>{
    const existing=DATA.attendance[s.id]?.[courseCode]?.[dateStr];
    if(existing){hasExisting=true;attMarks[s.id]=existing}
  });
  const banner=$('attBanner');
  banner.innerHTML=`<div class="att-header">
    <div class="att-icon">📝</div>
    <div class="att-header-info"><h3>${courseName(courseCode)} (${courseCode})</h3><p>${sec.name} · ${formatDate(dateStr)} · ${slot.replace('-',' – ')} · 📍 ${entry.room}</p></div>
    <span class="att-badge ${hasExisting?'existing':'new'}">${hasExisting?'⚠️ Already Marked':'✨ New Session'}</span>
  </div>
  ${hasExisting?'<div style="background:#fef9c3;border:1px solid rgba(245,158,11,.3);border-radius:12px;padding:10px 16px;margin-bottom:12px;font-size:.78rem;color:#92400e">⚠️ Attendance already marked. Current marks are pre-loaded. Saving will overwrite.</div>':''}
  <div class="progress-label" id="progLabel">0 of ${stuList.length} students marked</div>
  <div class="progress-bar"><div class="progress-fill" id="progFill" style="width:0%"></div></div>`;
  const area=$('attRollArea');
  area.innerHTML=`<div style="display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap">
    <button class="btn btn-green" onclick="markAll('P')">✅ Mark All Present</button>
    <button class="btn btn-red-o" onclick="markAll('A')">❌ Mark All Absent</button>
  </div>
  <input class="search-input" id="rollSearch" placeholder="🔍 Search student..." oninput="filterRoll()">
  <div id="rollList">${stuList.map((s,i)=>{
    const m=attMarks[s.id]||'';
    return `<div class="roll-row" id="roll-${s.id}" data-name="${s.name.toLowerCase()}" data-reg="${s.regNo.toLowerCase()}">
      <div class="roll-num">${i+1}</div>
      <div class="stu-av">${avatarHtml(s.photo,s.name,44)}</div>
      <div class="roll-info"><div class="rn">${s.name}</div><div class="rr">${s.regNo}</div></div>
      <div class="roll-btns">
        <button class="att-btn ${m==='P'?'sel-p':''}" onclick="setMark('${s.id}','P',this)">✅ Present</button>
        <button class="att-btn ${m==='A'?'sel-a':''}" onclick="setMark('${s.id}','A',this)">❌ Absent</button>
        <button class="att-btn ${m==='OD'?'sel-od':''}" onclick="setMark('${s.id}','OD',this)">📋 OD/ML</button>
      </div>
    </div>`;
  }).join('')}</div>
  <div class="sticky-save" id="stickyBar">
    <div class="save-summary" id="saveSummary"></div>
    <button class="btn btn-save" id="saveBtn" onclick="saveAttendance()">💾 Save Attendance</button>
  </div>`;
  // Store context
  area.dataset.secId=secId;area.dataset.date=dateStr;area.dataset.course=courseCode;area.dataset.count=stuList.length;
  updateProgressBar();
}
function setMark(stuId,mark,btn){
  if(attMarks[stuId]===mark){delete attMarks[stuId]}else{attMarks[stuId]=mark}
  const row=document.getElementById('roll-'+stuId);
  if(row){
    row.querySelectorAll('.att-btn').forEach(b=>{b.className='att-btn'});
    if(attMarks[stuId]){
      btn.className='att-btn sel-'+(mark==='P'?'p':mark==='A'?'a':'od');
    }
    row.classList.remove('unmarked-highlight');
  }
  updateProgressBar();
}
function markAll(mark){
  const area=$('attRollArea');
  const sec=DATA.sections.find(s=>s.id===area.dataset.secId);
  if(!sec)return;
  sec.students.forEach(sid=>{attMarks[sid]=mark});
  document.querySelectorAll('.roll-row').forEach(row=>{
    const sid=row.id.replace('roll-','');
    row.querySelectorAll('.att-btn').forEach(b=>b.className='att-btn');
    const sel=mark==='P'?0:mark==='A'?1:2;
    row.querySelectorAll('.att-btn')[sel].className='att-btn sel-'+(mark==='P'?'p':mark==='A'?'a':'od');
    row.classList.remove('unmarked-highlight');
  });
  updateProgressBar();
}
function updateProgressBar(){
  const area=$('attRollArea');if(!area.dataset.count)return;
  const total=+area.dataset.count;
  let p=0,a=0,od=0;
  Object.values(attMarks).forEach(v=>{if(v==='P')p++;else if(v==='A')a++;else if(v==='OD')od++});
  const marked=p+a+od,unmarked=total-marked;
  const pct=total>0?Math.round(marked/total*100):0;
  const fill=$('progFill');if(fill)fill.style.width=pct+'%';
  const label=$('progLabel');if(label)label.textContent=`${marked} of ${total} students marked`;
  const summary=$('saveSummary');
  if(summary) summary.innerHTML=`<span>✅ <span class="sc sc-p">${p}</span> Present</span>
    <span>❌ <span class="sc sc-a">${a}</span> Absent</span>
    <span>📋 <span class="sc sc-od">${od}</span> OD/ML</span>
    <span>⬜ <span class="sc sc-u">${unmarked}</span> Unmarked</span>`;
}
function saveAttendance(){
  const area=$('attRollArea'),secId=area.dataset.secId,dateStr=area.dataset.date,courseCode=area.dataset.course;
  const sec=DATA.sections.find(s=>s.id===secId);if(!sec)return;
  // Validate
  const unmarked=sec.students.filter(sid=>!attMarks[sid]);
  if(unmarked.length>0){
    unmarked.forEach(sid=>{const row=document.getElementById('roll-'+sid);if(row)row.classList.add('unmarked-highlight')});
    const first=document.getElementById('roll-'+unmarked[0]);if(first)first.scrollIntoView({behavior:'smooth',block:'center'});
    showToast(`⚠️ ${unmarked.length} students not yet marked!`,'warning');return;
  }
  // Save
  sec.students.forEach(sid=>{
    if(!DATA.attendance[sid])DATA.attendance[sid]={};
    if(!DATA.attendance[sid][courseCode])DATA.attendance[sid][courseCode]={};
    DATA.attendance[sid][courseCode][dateStr]=attMarks[sid];
  });
  const btn=$('saveBtn');
  btn.className='btn btn-save saved';btn.innerHTML='✅ Saved Successfully!';
  setTimeout(()=>{btn.className='btn btn-save';btn.innerHTML='💾 Save Attendance'},2500);
  let p=0,a=0,od=0;
  Object.values(attMarks).forEach(v=>{if(v==='P')p++;else if(v==='A')a++;else if(v==='OD')od++});
  const secName=sec.name;
  showToast(`✅ Attendance saved! ${p} Present, ${a} Absent, ${od} OD/ML — ${secName} · ${courseCode} · ${dateStr}`,'success');
}
function filterRoll(){
  const q=$('rollSearch').value.toLowerCase();
  document.querySelectorAll('.roll-row').forEach(r=>{
    r.style.display=(r.dataset.name.includes(q)||r.dataset.reg.includes(q))?'flex':'none';
  });
}

/* ═══════════════════════════════════════
   PAGE 6 — REPORT ABSENCE
   ═══════════════════════════════════════ */
function pgAbsence(){
  const f=currentFaculty,today=getTodayKey(),absent=isFacultyAbsent(f.id,today);
  const todayClasses=myTodayClasses();
  if(absent){
    return `<div class="section-title">🚫 Report My Absence</div>
    <div class="absence-card absence-active" style="animation:fadeUp .4s">
      <h3 style="color:var(--danger);margin-bottom:8px">🚫 You are currently marked absent for today</h3>
      <p style="font-size:.82rem;color:var(--muted)">${formatDate()}</p>
      <div class="absence-class-list">${todayClasses.length>0?todayClasses.map(t=>{
        const sec=DATA.sections.find(s=>s.id===t.section);
        return `<div class="absence-class"><span class="pill pill-red">${t.slot}</span> <strong>${courseName(t.course)}</strong> <span class="pill pill-gold">${sec?.name||t.section}</span> <span style="color:var(--muted);font-size:.78rem">📍 ${t.room}</span></div>`;
      }).join(''):'<div class="empty-state">No classes were scheduled today.</div>'}</div>
      <div style="display:flex;gap:10px;margin-top:14px">
        <button class="btn btn-navy btn-lg" onclick="undoFacultyAbsence()">↩️ Undo — I Am Coming</button>
        <button class="btn" style="background:var(--surface2);color:var(--muted);padding:12px 20px;cursor:default">✅ Absence Confirmed</button>
      </div>
    </div>`;
  }
  return `<div class="section-title">🚫 Report My Absence</div>
  <div style="font-size:.82rem;color:var(--muted);margin-bottom:18px">Notify students that you won't attend today</div>
  ${todayClasses.length>0?`<div class="card" style="border-left:4px solid var(--warning)">
    <h3 style="font-size:.9rem;color:var(--warning);margin-bottom:10px">⚠️ These classes will be marked CANCELLED:</h3>
    ${todayClasses.map(t=>{
      const sec=DATA.sections.find(s=>s.id===t.section);
      return `<div class="absence-class"><span class="pill pill-amber">${t.slot}</span> <strong>${courseName(t.course)}</strong> <span class="pill pill-gold">${sec?.name||t.section}</span> <span style="color:var(--muted);font-size:.78rem">📍 ${t.room}</span></div>`;
    }).join('')}
  </div>`:`<div class="card"><div class="empty-state"><span class="es-icon">🎉</span>No classes today — no need to report absence.</div></div>`}
  ${todayClasses.length>0?`<button class="btn btn-red btn-full btn-lg" onclick="showAbsenceModal()" style="animation:pulse 2s infinite">🚫 Confirm — Today I Am Not Coming</button>`:''}
  <div class="absence-notes">
    <strong>Important Notes:</strong>
    <ul style="margin-top:6px">
      <li>Students see CANCELLED immediately</li>
      <li>You can undo at any time before end of day</li>
      <li>Admin will be notified</li>
      <li>Attendance cannot be marked while absent</li>
    </ul>
  </div>`;
}
function showAbsenceModal(){
  const classes=myTodayClasses();
  $('absenceClassChecks').innerHTML=classes.map(t=>`
    <label style="display:flex;align-items:center;gap:10px;padding:7px 0;border-bottom:1px solid #eee;cursor:pointer;font-size:.83rem">
      <input type="checkbox" class="abs-chk" value="${t.slot}" style="width:15px;height:15px;accent-color:#dc2626">
      <span class="pill pill-amber">${t.slot}</span>
      <strong>${courseName(t.course)}</strong>
      <span style="color:#999;font-size:.76rem">📍 ${t.room}</span>
    </label>`).join('');
  $('absenceModal').classList.add('show');
}
function hideAbsenceModal(){$('absenceModal').classList.remove('show')}
function confirmAbsence(){
  const checked=[...document.querySelectorAll('.abs-chk:checked')].map(c=>c.value);
  if(!checked.length){showToast('⚠️ Select at least one class','warning');return;}
  hideAbsenceModal();
  if(!DATA.facultyAbsence[currentFaculty.id])DATA.facultyAbsence[currentFaculty.id]={};
  const prev=DATA.facultyAbsence[currentFaculty.id][getTodayKey()]||[];
  DATA.facultyAbsence[currentFaculty.id][getTodayKey()]=[...new Set([...prev,...checked])];
  showToast(`🚫 ${checked.length} class(es) cancelled.`,'error');
  showPage('absence');
}
function undoFacultyAbsence(){
  DATA.facultyAbsence[currentFaculty.id][getTodayKey()]=[];
  showToast('✅ Absence undone! You are back on duty.','success');
  showPage('absence');
}

/* ═══ AUTO INIT ═══ */
// If page args need auto-load after render
const origShowPage=showPage;
showPage=function(page,args){
  origShowPage(page,args);
  if(page==='stutt')setTimeout(()=>{if($('stvSecSel')&&$('stvSecSel').value)stvLoadStudents()},100);
  if(page==='markatt')setTimeout(()=>{if($('attSecSel')&&$('attSecSel').value)attUpdateSlots()},100);
};

/* ═══ AUTO-LOGIN FROM FLASK ═══ */
(function(){
  const autoEmail="{{ current_email }}";
  if(autoEmail){
    const fac=DATA.faculty.find(f=>f.email===autoEmail.toLowerCase());
    if(fac){
      currentFaculty=fac;
      currentRole='faculty';
      initApp();
      return;
    }
  }
})();



let facChatHistory = [];
let facChatOpen = false;

function toggleFacChat() {
    facChatOpen = !facChatOpen;
    document.getElementById('facChatPanel').classList.toggle('open', facChatOpen);
    if(facChatOpen) document.getElementById('facChatInput').focus();
}

async function handleFacChat(e) {
    e.preventDefault();
    const input = document.getElementById('facChatInput');
    const msg = input.value.trim();
    if(!msg) return;
    
    sendFacChat(msg);
    input.value = '';
}

async function sendFacChat(msg) {
    appendFacMsg('user', msg);
    facChatHistory.push({ role: 'user', content: msg });
    
    const typing = document.createElement('div');
    typing.className = 'chat-msg bot';
    typing.id = 'facTyping';
    typing.innerHTML = `<div class="typing-indicator"><div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div></div>`;
    document.getElementById('facChatMessages').appendChild(typing);
    scrollFacChat();
    
    try {
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';
        const res = await fetch('/api/chatbot/faculty', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ messages: facChatHistory.slice(-10) })
        });
        const data = await res.json();
        const typingEl = document.getElementById('facTyping');
        if(typingEl) typingEl.remove();
        
        if(data.reply) {
            const actionMatch = data.reply.match(/```action\s*\n([\s\S]*?)```/);
            let displayText = data.reply;
            let actionHtml = '';
            
            if (actionMatch) {
                try {
                    const actionJson = JSON.parse(actionMatch[1]);
                    displayText = data.reply.replace(actionMatch[0], '');
                    actionHtml = `<div class="action-overlay" style="background:rgba(124,58,237,0.1);border:1px solid var(--faculty-purple);padding:12px;border-radius:8px;margin-top:8px;">
                        <strong style="color:var(--faculty-purple)">⚡ AI Suggestion:</strong> ${actionJson.action}
                        <button class="lbtn" style="padding:8px;margin-top:8px;font-size:0.8rem;background:var(--faculty-purple);color:#fff" onclick="executeFacAction('${encodeURIComponent(JSON.stringify(actionJson))}')">Execute Action</button>
                    </div>`;
                } catch (e) { console.error(e); }
            }
            
            appendFacMsg('bot', displayText, actionHtml);
            facChatHistory.push({ role: 'assistant', content: data.reply });
        } else {
            appendFacMsg('bot', 'Error: ' + (data.error || 'Unknown error'));
        }
    } catch(err) {
        const typingEl = document.getElementById('facTyping');
        if(typingEl) typingEl.remove();
        appendFacMsg('bot', '❌ Connection error.');
    }
}

async function executeFacAction(encoded) {
    const action = JSON.parse(decodeURIComponent(encoded));
    if(!confirm(`Do you want to execute ${action.action}?`)) return;
    
    showToast(`AI is executing ${action.action}...`, 'info');
    
    try {
        if(action.action === 'get_my_schedule') {
            showPage('timetable');
        } else if(action.action === 'mark_attendance') {
            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';
            const res = await fetch('/api/attendance/mark', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
                body: JSON.stringify(action)
            });
            const data = await res.json();
            showToast(data.message || 'Attendance marked!', 'success');
            sendFacChat(`Result of marking attendance: ${data.message || 'Success'}`);
        } else if(action.action === 'get_section_students') {
            showPage('stutt', { section_id: action.section_id });
        } else if(action.action === 'get_attendance_summary' || action.action === 'get_students_below_threshold') {
            showPage('dashboard');
        } else {
            showToast(`Action ${action.action} handled.`, 'success');
        }
    } catch(e) {
        showToast('Action execution failed', 'error');
    }
}

function appendFacMsg(role, text, extraHtml = '') {
    const container = document.getElementById('facChatMessages');
    const div = document.createElement('div');
    div.className = `chat-msg ${role}`;
    
    let html = text
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        .replace(/\n/g, '<br>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/### (.*?)<br>/g, '<h4>$1</h4>')
        .replace(/## (.*?)<br>/g, '<h3>$1</h3>');
    
    if (text.includes('|')) {
        const lines = text.split('\n');
        let inTable = false;
        let tableHtml = '<table>';
        let newHtml = '';
        
        lines.forEach(line => {
            if (line.trim().startsWith('|')) {
                if (!inTable) { inTable = true; tableHtml = '<table>'; }
                const cells = line.split('|').filter(c => c.trim() !== '' || line.indexOf(c) > 0 && line.indexOf(c) < line.length - 1);
                if (line.includes('---')) return;
                tableHtml += '<tr>' + cells.map(c => `<td>${c.trim()}</td>`).join('') + '</tr>';
            } else {
                if (inTable) { inTable = false; tableHtml += '</table>'; newHtml += tableHtml; }
                newHtml += line + '<br>';
            }
        });
        if (inTable) { tableHtml += '</table>'; newHtml += tableHtml; }
        html = newHtml;
    }

    div.innerHTML = `<div class="chat-bubble">${html}${extraHtml}</div>`;
    container.appendChild(div);
    scrollFacChat();
}

function scrollFacChat() {
    const el = document.getElementById('facChatMessages');
    el.scrollTop = el.scrollHeight;
}



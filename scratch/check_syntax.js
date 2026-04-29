
    /* ══════════ STATE ══════════ */
    let PROFILE = {}, COURSES = [], TIMETABLE = [], ATTENDANCE = {}, TODAY_ATT = [], MARKS = [], FACULTY_ABSENCE = {};
    const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'];
    const SLOTS = ['9-10', '10-11', '11-12', '12-1', '2-3', '3-4', '4-5'];

    /* ══════════ UTILS ══════════ */
    const $ = id => document.getElementById(id);
    function initials(n) { return (n || '').replace(/^Dr\.\s*/i, '').split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2); }
    function todayKey() { return new Date().toISOString().split('T')[0]; }
    function todayDay() { return ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'][new Date().getDay()]; }
    function slotOrder(s) { return SLOTS.indexOf(s); }
    function slotStatus(s) {
      const h = new Date().getHours(); const p = s.split('-');
      let sh = +p[0], eh = +p[1]; if (sh < 8) sh += 12; if (eh < 8 || eh <= sh) eh += 12;
      if (h >= eh) return 'done'; if (h >= sh && h < eh) return 'ongoing'; return 'upcoming';
    }
    function isSlotCancelled(fid, date, slot) {
      const c = FACULTY_ABSENCE[fid] && FACULTY_ABSENCE[fid][date];
      return Array.isArray(c) && c.includes(slot);
    }
    function attColor(pct) { return pct < 75 ? '#dc2626' : pct <= 80 ? '#ea580c' : '#16a34a'; }
    function attBg(pct) { return pct < 75 ? '#fee2e2' : pct <= 80 ? '#ffedd5' : '#dcfce7'; }
    function attLabel(pct) { return pct < 75 ? '⚠️ Shortage' : pct <= 80 ? '🟠 Warning' : '✅ Safe'; }
    function courseName(code) { const c = COURSES.find(x => x.code === code); return c ? c.name : code; }
    function formatDate() { return new Date().toLocaleDateString('en-IN', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' }); }

    /* ══════════ PHOTO ══════════ */
    function updateSidebarPhoto() {
      const av = $('sb-av');
      const cached = localStorage.getItem('student_photo_' + PROFILE.id);
      const photo = PROFILE.photo || cached || '';
      if (photo) { av.innerHTML = `<img src="${photo}" style="width:100%;height:100%;object-fit:cover;border-radius:50%">`; }
      else { av.innerHTML = `<div class="initials-av">${initials(PROFILE.name)}</div>`; }
    }
    $('photoInput').addEventListener('change', function (e) {
      const file = e.target.files[0]; if (!file) return;
      if (!file.type.startsWith('image/')) { showToast('Select an image file', 'warning'); return; }
      if (file.size > 5 * 1024 * 1024) { showToast('Max 5MB', 'warning'); return; }
      const r = new FileReader();
      r.onload = async ev => {
        const b64 = ev.target.result;
        PROFILE.photo = b64;
        localStorage.setItem('student_photo_' + PROFILE.id, b64);
        updateSidebarPhoto();
        rerenderHeroPhoto();
        const _csrf = document.querySelector('meta[name="csrf-token"]')?.content || '';
        await fetch('/student/upload-photo', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': _csrf }, body: JSON.stringify({ photo: b64 }) });
      };
      r.readAsDataURL(file); e.target.value = '';
    });
    function rerenderHeroPhoto() {
      const el = $('hero-av-inner'); if (!el) return;
      const photo = PROFILE.photo || localStorage.getItem('student_photo_' + PROFILE.id) || '';
      el.innerHTML = photo
        ? `<img src="${photo}" style="width:100%;height:100%;object-fit:cover">`
        : `<div style="width:100%;height:100%;display:flex;align-items:center;justify-content:center;font-size:2.5rem;font-weight:900;color:#fff">${initials(PROFILE.name)}</div>`;
      const btn = $('upload-btn-hero');
      if (btn) btn.style.display = photo ? 'none' : 'block';
    }

    /* ══════════ DATA LOAD ══════════ */
    async function fetchApi(url) {
      const res = await fetch(url, { headers: { 'Accept': 'application/json' } });
      if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
      const text = await res.text();
      try {
        return JSON.parse(text);
      } catch (e) {
        throw new Error(`Failed to parse JSON from ${url}`);
      }
    }

    async function loadAll() {
      // 10-second timeout safety net
      let loading = true;
      const timeoutId = setTimeout(() => {
        if (loading) {
          loading = false;
          $('page-content').innerHTML = `
            <div style="padding: 40px; text-align: center; color: var(--red);">
              <h2>⚠️ Timeout Error</h2>
              <p style="margin-top: 10px;">Failed to load data within 10 seconds. Please refresh.</p>
              <button onclick="location.reload()" style="margin-top: 20px; padding: 10px 20px; background: var(--blue); color: white; border: none; border-radius: 6px; cursor: pointer;">Refresh</button>
            </div>
          `;
          $('sb-name').textContent = 'Timeout Error';
        }
      }, 10000);

      try {
        const [p, c, tt, att, ta, m, fa] = await Promise.all([
          fetchApi('/student/api/profile'),
          fetchApi('/student/api/courses'),
          fetchApi('/student/api/timetable'),
          fetchApi('/student/api/attendance'),
          fetchApi('/student/api/today-attendance'),
          fetchApi('/student/api/marks'),
          fetchApi('/student/api/faculty-absence')
        ]);
        
        if (p && p.error) {
          throw new Error(p.error);
        }
        
        // Auth / Session Check Guard
        if (!p || !p.id) {
          throw new Error("Session expired. Please login again.");
        }
        
        PROFILE = p || {}; COURSES = c || []; TIMETABLE = tt || []; ATTENDANCE = att || {}; TODAY_ATT = ta || []; MARKS = m || []; FACULTY_ABSENCE = fa || {};
        
        // Restore photo: DB wins, else localStorage cache
        const cached = localStorage.getItem('student_photo_' + PROFILE.id);
        if (!PROFILE.photo && cached) PROFILE.photo = cached;
        if (PROFILE.photo) localStorage.setItem('student_photo_' + PROFILE.id, PROFILE.photo);
        
        $('sb-name').textContent = PROFILE.name || 'Unknown Student';
        $('sb-reg').textContent = PROFILE.regNo || '';
        $('tb-date').textContent = formatDate();
        updateSidebarPhoto();
        
        // Exit loading state
        loading = false;
        clearTimeout(timeoutId);
        showPage('dashboard');
      } catch (err) {
        if (!loading) return; // if timeout already fired
        loading = false;
        clearTimeout(timeoutId);
        console.error("Dashboard Data Load Error:", err);
        
        const isSessionErr = err.message.includes("Session expired") || err.message.includes("Unauthorized");
        const actionBtn = isSessionErr 
            ? `<button onclick="window.location.href='/login'" style="margin-top: 20px; padding: 10px 20px; background: var(--blue); color: white; border: none; border-radius: 6px; cursor: pointer;">Login Again</button>`
            : `<button onclick="location.reload()" style="margin-top: 20px; padding: 10px 20px; background: var(--blue); color: white; border: none; border-radius: 6px; cursor: pointer;">Retry</button>`;
            
        $('page-content').innerHTML = `
          <div style="padding: 40px; text-align: center; color: var(--red);">
            <h2>⚠️ Failed to load dashboard data</h2>
            <p style="margin-top: 10px;">${err.message}</p>
            ${actionBtn}
          </div>
        `;
        $('sb-name').textContent = isSessionErr ? 'Session Expired' : 'Error Loading Data';
      }
    }

    /* ══════════ ROUTER ══════════ */
    const PAGE_TITLES = { dashboard: 'Dashboard', today: "Today's Timetable", fulltable: 'Full Timetable', attendance: 'Attendance', marks: 'Exam Marks & CGPA', courses: 'My Courses', hostel: 'Hostel & Transport' };
    function showPage(page) {
      document.querySelectorAll('.sb-nav a').forEach(a => a.classList.toggle('active', a.dataset.p === page));
      $('page-title').textContent = PAGE_TITLES[page] || '';
      const pages = { dashboard: pgDashboard, today: pgToday, fulltable: pgFullTT, attendance: pgAttendance, marks: pgMarks, courses: pgCourses, hostel: pgHostel };
      if (pages[page]) $('page-content').innerHTML = pages[page]();
    }

    /* ══════════ TIMETABLE TABLE BUILDER ══════════ */
    function buildTTTable(entries, showPresence = false) {
      if (!entries.length) return `<div class="loading">🎉 No classes scheduled!</div>`;
      return `
  <div style="overflow-x:auto">
  <table class="tt-table">
    <thead>
      <tr>
        <th style="width:100px">Time</th>
        <th>Course</th>
        <th>Faculty</th>
        <th>Room</th>
        <th>Status</th>
        ${showPresence ? '<th>Presence</th>' : ''}
      </tr>
    </thead>
    <tbody>
      ${entries.map(t => {
        const cancelled = isSlotCancelled(t.faculty, todayKey(), t.slot);
        const st = slotStatus(t.slot);
        let presHtml = '';
        if (showPresence) {
          const rec = TODAY_ATT.find(x => x.slot === t.slot && x.course === t.course);
          if (rec) presHtml = rec.status === 'P' ? `<span class="pill pill-green">Present</span>` : `<span class="pill pill-red">Absent</span>`;
          else presHtml = '<span style="color:#94a3b8">—</span>';
        }

        return `
        <tr style="${st === 'done' ? 'opacity:.6' : ''}">
          <td><span class="slot">${t.slot}</span></td>
          <td>
            <div style="font-weight:700;color:#1e3a8a">${courseName(t.course)}</div>
            <div style="font-size:.65rem;color:var(--muted)">${t.course}</div>
          </td>
          <td style="font-size:.78rem">👨‍🏫 ${t.faculty}</td>
          <td><span class="pill pill-gray">📍 ${t.room}</span></td>
          <td>
            ${cancelled
            ? `<span class="pill pill-red">🚫 Cancelled</span>`
            : `<span class="pill ${st === 'ongoing' ? 'pill-green' : st === 'done' ? 'pill-gray' : 'pill-blue'}">${st === 'ongoing' ? '🟢 Ongoing' : st === 'done' ? '✅ Done' : 'Upcoming'}</span>`}
          </td>
          ${showPresence ? `<td>${presHtml}</td>` : ''}
        </tr>`;
      }).join('')}
    </tbody>
  </table>
  </div>`;
    }

    /* ══════════ PAGE: DASHBOARD ══════════ */
    function pgDashboard() {
      const todayTT = TIMETABLE.filter(t => t.day === todayDay()).sort((a, b) => slotOrder(a.slot) - slotOrder(b.slot));
      const photo = PROFILE.photo || localStorage.getItem('student_photo_' + PROFILE.id) || '';
      return `
  <div class="hero-card">
    <div class="hero-av-wrap">
      <div class="hero-av-circle" onclick="$('photoInput').click()">
        <div id="hero-av-inner">
          ${photo ? `<img src="${photo}" style="width:100%;height:100%;object-fit:cover">` : `<div style="width:100%;height:100%;display:flex;align-items:center;justify-content:center;font-size:2.5rem;font-weight:900;color:#fff">${initials(PROFILE.name)}</div>`}
        </div>
        <div class="av-overlay"><span>📷</span><small>Change</small></div>
      </div>
      <button class="upload-btn" id="upload-btn-hero" onclick="$('photoInput').click()" style="display:${photo ? 'none' : 'block'}">📷 Upload Photo</button>
    </div>
    <div class="hero-info">
      <h1>${PROFILE.name}</h1>
      <span class="regno">${PROFILE.regNo}</span>
      <div class="hero-meta">📚 ${PROFILE.sectionName} &nbsp;·&nbsp; ${PROFILE.dept} &nbsp;·&nbsp; Year ${PROFILE.year} · Sem ${PROFILE.semester}</div>
      <div class="hero-meta">🎓 Advisor: ${PROFILE.advisor} &nbsp;·&nbsp; 🩸 ${PROFILE.blood} &nbsp;·&nbsp; 🎂 ${PROFILE.dob}</div>
      <div class="hero-contact"><span>📧 ${PROFILE.email}</span><span>📞 ${PROFILE.phone}</span></div>
    </div>
  </div>
  <div class="stat-grid">
    <div class="stat"><div class="stat-v">${COURSES.length}</div><div class="stat-l">📚 Courses</div></div>
    <div class="stat"><div class="stat-v">${todayTT.length}</div><div class="stat-l">📅 Today's Classes</div></div>
    <div class="stat"><div class="stat-v">${PROFILE.cgpa}</div><div class="stat-l">⭐ CGPA</div></div>
    <div class="stat"><div class="stat-v">Sem ${PROFILE.semester}</div><div class="stat-l">📖 Current Sem</div></div>
  </div>
  <div class="card">
    <div class="card-title">📅 Today's Classes <span style="font-size:.72rem;font-weight:500;color:#64748b;margin-left:auto">${todayDay()} · ${todayKey()}</span></div>
    ${buildTTTable(todayTT, true)}
  </div>`;
    }

    /* ══════════ PAGE: TODAY TIMETABLE ══════════ */
    function pgToday() {
      const todayTT = TIMETABLE.filter(t => t.day === todayDay()).sort((a, b) => slotOrder(a.slot) - slotOrder(b.slot));
      return `<div class="card">
  <div class="card-title">📅 Today's Timetable <span style="font-size:.72rem;font-weight:500;color:#64748b;margin-left:auto">${todayDay()} · ${todayKey()}</span></div>
  ${buildTTTable(todayTT, true)}
  </div>`;
    }

    /* ══════════ PAGE: FULL TIMETABLE ══════════ */
    function pgFullTT() {
      return `
  <div class="card">
    <div class="card-title">📆 Weekly Timetable Grid</div>
    <div class="week-grid-wrap">
      <table class="week-grid">
        <thead>
          <tr>
            <th class="time-col">Slot</th>
            ${DAYS.map(d => `<th>${d}</th>`).join('')}
          </tr>
        </thead>
        <tbody>
          ${SLOTS.map(slot => `
            <tr>
              <td class="time-col">${slot}</td>
              ${DAYS.map(day => {
        const entry = TIMETABLE.find(t => t.day === day && t.slot === slot);
        if (!entry) return `<td class="empty"></td>`;
        return `
                <td>
                  <div class="grid-cell">
                    <div class="grid-course">${entry.course}</div>
                    <div class="grid-fac">${entry.faculty}</div>
                    <div class="grid-room">📍 ${entry.room}</div>
                  </div>
                </td>`;
      }).join('')}
            </tr>
          `).join('')}
        </tbody>
      </table>
    </div>
    <div style="margin-top:12px;font-size:.7rem;color:var(--muted)">* Empty slots indicate no scheduled classes for that period.</div>
  </div>`;
    }

    /* ══════════ PAGE: ATTENDANCE ══════════ */
    function pgAttendance() {
      return `<div class="card">
  <div class="card-title">📊 Attendance Details</div>
  <div style="overflow-x:auto">
  <table class="att-table">
    <thead><tr><th>Subject</th><th>Conducted</th><th>Present</th><th>Absent</th><th>Percentage</th><th>Status</th></tr></thead>
    <tbody>
    ${COURSES.map(c => {
        const a = ATTENDANCE[c.code];
        if (!a) return `<tr><td><div style="font-weight:700">${c.code}</div><div style="font-size:.74rem;color:#64748b">${c.name}</div></td><td colspan="4" style="color:#94a3b8;text-align:center">No data yet</td><td>—</td></tr>`;
        return `<tr>
        <td><div style="font-weight:700;font-size:.8rem">${c.code}</div><div style="font-size:.74rem;color:#64748b">${c.name}</div></td>
        <td>${a.total}</td>
        <td style="color:#16a34a;font-weight:700">${a.present}</td>
        <td style="color:#dc2626;font-weight:700">${a.absent}</td>
        <td><div style="display:flex;align-items:center;gap:8px"><div class="bar-wrap"><div class="bar" style="width:${a.pct}%;background:${attColor(a.pct)}"></div></div><span style="font-weight:800;color:${attColor(a.pct)};font-size:.82rem;min-width:36px">${a.pct}%</span></div></td>
        <td><span style="background:${attBg(a.pct)};color:${attColor(a.pct)};padding:3px 10px;border-radius:20px;font-size:.7rem;font-weight:700">${attLabel(a.pct)}</span></td>
      </tr>`;
      }).join('')}
    </tbody>
  </table></div>
  <div style="margin-top:14px;display:flex;gap:12px;flex-wrap:wrap;font-size:.76rem">
    <span style="background:#dcfce7;color:#16a34a;padding:4px 12px;border-radius:20px;font-weight:700">Above 80% ✅ Safe</span>
    <span style="background:#ffedd5;color:#ea580c;padding:4px 12px;border-radius:20px;font-weight:700">75–80% 🟠 Warning</span>
    <span style="background:#fee2e2;color:#dc2626;padding:4px 12px;border-radius:20px;font-weight:700">Below 75% ⚠️ Shortage</span>
  </div>
  <div style="margin-top:20px;">
    <div class="card-title">📉 Attendance Trend (Last 4 Weeks)</div>
    <canvas id="attTrendChart" style="max-height:250px;"></canvas>
  </div>
  <script>setTimeout(renderAttendanceTrend, 50);<\/script>
  </div>`;
  }

  async function renderAttendanceTrend() {
  const ctx = document.getElementById('attTrendChart');
  if(!ctx) return;

  try {
  const res = await fetch(`/api/attendance/trend/${PROFILE.id}`);
  const data = await res.json();

  new Chart(ctx, {
  type: 'line',
  data: {
  labels: data.map(d => d.week),
  datasets: [{
  label: 'Attendance %',
  data: data.map(d => d.pct),
  borderColor: '#6366f1',
  backgroundColor: 'rgba(99, 102, 241, 0.1)',
  fill: true,
  tension: 0.4
  }]
  },
  options: {
  responsive: true,
  plugins: { legend: { display: false } },
  scales: {
  y: { min: 0, max: 100 }
  }
  }
  });
  } catch(e) { console.error(e); }
  }

  /* ══════════ PAGE: MARKS ══════════ */
  function pgMarks(){
  if(!MARKS.length)return`<div class="card">
    <div class="loading">📭 No academic records found.</div>
  </div>`;
  return`
  <div class="cgpa-hero">
    <div>
      <div style="font-size:.78rem;color:rgba(255,255,255,.7);margin-bottom:4px">Overall CGPA — Year 1 to Year
        ${PROFILE.year}</div>
      <div class="cgpa-big">${PROFILE.cgpa}</div>
      <div style="font-size:.75rem;color:rgba(255,255,255,.65);margin-top:4px">${MARKS.length} Semesters Completed</div>
    </div>
    <div style="display:flex;gap:12px;flex-wrap:wrap">
      ${MARKS.map(sm=>`<div
        style="text-align:center;background:rgba(255,255,255,.12);padding:10px 16px;border-radius:12px">
        <div style="font-size:1.2rem;font-weight:900;color:#fff">${sm.sgpa}</div>
        <div style="font-size:.66rem;color:rgba(255,255,255,.7)">Sem ${sm.sem}</div>
      </div>`).join('')}
    </div>
  </div>
  ${MARKS.map(sm=>`<div class="sem-block">
    <div class="sem-head">
      <div style="font-weight:800;font-size:.88rem">Semester ${sm.sem}</div>
      <div style="display:flex;gap:10px;align-items:center">
        <span style="font-size:.78rem;color:#64748b">${sm.subjects.length} subjects</span>
        <span
          style="background:linear-gradient(90deg,#6366f1,#1e3a8a);color:#fff;padding:3px 12px;border-radius:20px;font-size:.78rem;font-weight:800">SGPA:
          ${sm.sgpa}</span>
      </div>
    </div>
    <div style="padding:14px">
      <table class="mark-table">
        <thead>
          <tr>
            <th>Code</th>
            <th>Subject</th>
            <th>Credits</th>
            <th>Grade</th>
            <th>Points</th>
            <th>Credit Points</th>
          </tr>
        </thead>
        <tbody>
          ${sm.subjects.map(sub=>`<tr>
            <td style="font-weight:700;color:#6366f1">${sub.code}</td>
            <td>${sub.name}</td>
            <td style="text-align:center">${sub.credits}</td>
            <td
              style="text-align:center;font-weight:800;color:${sub.points>=9?'#16a34a':sub.points>=7?'#ea580c':'#dc2626'}">
              ${sub.grade}</td>
            <td style="text-align:center">${sub.points}</td>
            <td style="text-align:center;font-weight:700;color:#1e3a8a">${sub.credits*sub.points}</td>
          </tr>`).join('')}
          <tr style="background:#f8fafc">
            <td colspan="2" style="font-weight:800">Total</td>
            <td style="text-align:center;font-weight:800">${sm.subjects.reduce((a,b)=>a+b.credits,0)}</td>
            <td></td>
            <td></td>
            <td style="text-align:center;font-weight:800;color:#6366f1">
              ${sm.subjects.reduce((a,b)=>a+b.credits*b.points,0)}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>`).join('')}`;
  }

  /* ══════════ PAGE: COURSES ══════════ */
  function pgCourses(){
  const total=COURSES.reduce((a,c)=>a+c.credits,0);
  return`<div class="card">
    <div class="card-title">📚 My Courses — Semester ${PROFILE.semester} <span
        style="margin-left:auto;font-size:.74rem;font-weight:500;color:#64748b">${COURSES.length} subjects · ${total}
        credits</span></div>
    <div class="course-grid">
      ${COURSES.map(c=>{
      const tt=TIMETABLE.find(t=>t.course===c.code);
      return`<div class="course-chip">
        <div class="course-code">${c.code}</div>
        <div class="course-name">${c.name}</div>
        <div class="course-meta">
          <span class="pill pill-purple">${c.credits} Credits</span>
          <span class="pill pill-blue">${c.type}</span>
          ${tt?`<span class="pill pill-gray">👨🏫 ${tt.faculty}</span>`:''}
        </div>
      </div>`;
      }).join('')}
    </div>
    <table class="att-table">
      <thead>
        <tr>
          <th>Code</th>
          <th>Subject Name</th>
          <th>Credits</th>
          <th>Type</th>
          <th>Faculty</th>
        </tr>
      </thead>
      <tbody>
        ${COURSES.map(c=>{const tt=TIMETABLE.find(t=>t.course===c.code);return`<tr>
          <td style="font-weight:800;color:#6366f1;text-align:left">${c.code}</td>
          <td style="text-align:left">${c.name}</td>
          <td>${c.credits}</td>
          <td><span class="pill pill-blue">${c.type}</span></td>
          <td style="font-size:.79rem">${tt?tt.faculty:'—'}</td>
        </tr>`;}).join('')}
        <tr style="background:#f8fafc;font-weight:800">
          <td colspan="2" style="text-align:left">Total</td>
          <td>${total}</td>
          <td></td>
          <td></td>
        </tr>
      </tbody>
    </table>
  </div>`;
  }

  /* ══════════ PAGE: HOSTEL ══════════ */
  function pgHostel(){
  const h=(PROFILE.hostel||'').toLowerCase();
  const type=h.includes('bus')?'bus':h.includes('day')||h===''?'dayscholar':'hostel';
  const cfg={
  hostel:{icon:'🏠',title:'Hostel Resident',bg:'linear-gradient(135deg,#f0fdf4,#dcfce7)',border:'#bbf7d0',tc:'#166534',nb:'#bbf7d0',nc:'#166534',note:'✅ You are a Hostel Resident. For hostel-related queries contact the warden.'},
  bus:{icon:'🚌',title:'Bus Commuter',bg:'linear-gradient(135deg,#eff6ff,#dbeafe)',border:'#bfdbfe',tc:'#1d4ed8',nb:'#bfdbfe',nc:'#1d4ed8',note:'🚌 You are a Bus Commuter. Contact the transport office for route and timing details.'},
  dayscholar:{icon:'🏡',title:'Day Scholar',bg:'linear-gradient(135deg,#fefce8,#fef9c3)',border:'#fde68a',tc:'#92400e',nb:'#fde68a',nc:'#92400e',note:'🏡 You are a Day Scholar. Arrive on time and sign the daily attendance register.'}
  }[type];
  return`<div class="hostel-card" style="background:${cfg.bg};border:1.5px solid ${cfg.border}">
    <div style="font-size:2.2rem;margin-bottom:8px">${cfg.icon}</div>
    <div style="font-weight:900;font-size:1.1rem;color:${cfg.tc};margin-bottom:14px">${cfg.title}</div>
    <div class="det-row"><span class="det-l">Student Name</span><span class="det-v">${PROFILE.name}</span></div>
    <div class="det-row"><span class="det-l">Registration No</span><span class="det-v">${PROFILE.regNo}</span></div>
    <div class="det-row"><span class="det-l">Department</span><span class="det-v">${PROFILE.dept}</span></div>
    <div class="det-row"><span class="det-l">Year / Semester</span><span class="det-v">Year ${PROFILE.year} · Sem
        ${PROFILE.semester}</span></div>
    <div class="det-row"><span class="det-l">Hostel / Transport</span><span class="det-v">${PROFILE.hostel||'Day Scholar'}</span></div>
    <div class="det-row"><span class="det-l">Advisor</span><span class="det-v">${PROFILE.advisor}</span></div>
    <div class="det-row"><span class="det-l">Phone</span><span class="det-v">${PROFILE.phone}</span></div>
    <div
      style="margin-top:14px;padding:12px;border-radius:12px;background:${cfg.nb};color:${cfg.nc};font-size:.78rem;font-weight:600">
      ${cfg.note}</div>
  </div>`;
  }

  /* ══════════ BOOT ══════════ */
  loadAll();
  


let stuChatHistory = [];
let stuChatOpen = false;
let stuInitialGreetingDone = false;

function toggleStuChat() {
    stuChatOpen = !stuChatOpen;
    document.getElementById('stuChatPanel').classList.toggle('open', stuChatOpen);
    if(stuChatOpen) {
        document.getElementById('stuChatInput').focus();
        if(!stuInitialGreetingDone) showStuInitialGreeting();
    }
}

function showStuInitialGreeting() {
    stuInitialGreetingDone = true;
    const container = document.getElementById('stuChatMessages');
    const todayCount = TIMETABLE.filter(e => e.day === todayDay()).length;

    let greetingHtml = `
        <div class="greeting-card">
            <h4>Hi ${PROFILE.name}! 👋</h4>
            <p>You have <strong>${todayCount}</strong> classes scheduled for today.</p>
        </div>
        `;
    
    const lowAtt = COURSES.filter(c => {
        const att = ATTENDANCE[c.code] || {percent: 0};
        return att.percent < 75;
    });
    
    if(lowAtt.length > 0) {
        greetingHtml += `
        <div class="chat-bubble" style="background:#fee2e2; border:1px solid #fecaca; color:#991b1b; margin-top:8px; font-size:0.85rem;">
                ⚠️ <strong>Attendance Alert:</strong> You are below 75% in ${lowAtt.length} subject(s). I can help you plan which classes to attend!
        </div>
        `;
    }
    
    const div = document.createElement('div');
    div.className = 'chat-msg bot';
    div.innerHTML = greetingHtml;
    container.appendChild(div);
}

async function handleStuChat(e) {
    e.preventDefault();
    const input = document.getElementById('stuChatInput');
    const msg = input.value.trim();
    if(!msg) return;
    
    sendStuChat(msg);
    input.value = '';
}

async function sendStuChat(msg) {
    appendStuMsg('user', msg);
    stuChatHistory.push({ role: 'user', content: msg });
    
    const typing = document.createElement('div');
    typing.className = 'chat-msg bot';
    typing.id = 'stuTyping';
    typing.innerHTML = `<div class="typing-indicator"><div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div></div>`;
    document.getElementById('stuChatMessages').appendChild(typing);
    scrollStuChat();
    
    try {
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';
        const res = await fetch('/api/chatbot/student', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ messages: stuChatHistory.slice(-10) })
        });
        const data = await res.json();
        const typingEl = document.getElementById('stuTyping');
        if(typingEl) typingEl.remove();
        
        if(data.reply) {
            // Read-only actions (simulation for student)
            const actionMatch = data.reply.match(/```action\s*\n([\s\S]*?)```/);
            let displayText = data.reply;
            let actionHtml = '';
            
            if (actionMatch) {
                try {
                    const actionJson = JSON.parse(actionMatch[1]);
                    displayText = data.reply.replace(actionMatch[0], '');
                    actionHtml = `<div class="action-overlay" style="background:rgba(99,102,241,0.1);border:1px solid var(--accent);padding:10px;border-radius:8px;margin-top:8px;">
        <strong style="color:var(--accent)">💡 Quick Access:</strong> ${actionJson.action.replace(/_/g, ' ')}
      <button class="lbtn" style="padding:6px 10px;margin-top:6px;font-size:0.75rem;background:var(--accent);color:#fff" onclick="executeStuAction('${encodeURIComponent(JSON.stringify(actionJson))}')">View Details</button>
                    </div>`;
                } catch (e) { console.error(e); }
            }
            
            appendStuMsg('bot', displayText, actionHtml);
            stuChatHistory.push({ role: 'assistant', content: data.reply });
        } else {
            appendStuMsg('bot', 'Error: ' + (data.error || 'Unknown error'));
        }
    } catch(err) {
        const typingEl = document.getElementById('stuTyping');
        if(typingEl) typingEl.remove();
        appendStuMsg('bot', '❌ Connection error.');
    }
}

function executeStuAction(encoded) {
    const action = JSON.parse(decodeURIComponent(encoded));
    if(action.action === 'get_my_timetable') showPage('fulltable');
    else if(action.action === 'get_attendance_report') showPage('attendance');
    else if(action.action === 'get_next_class') showPage('today');
    else if(action.action === 'get_course_details') showPage('courses');
    else if(action.action === 'get_low_attendance_alert') showPage('attendance');
}

function appendStuMsg(role, text, extraHtml = '') {
    const container = document.getElementById('stuChatMessages');
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
    scrollStuChat();
}

function scrollStuChat() {
    const el = document.getElementById('stuChatMessages');
    el.scrollTop = el.scrollHeight;
}

// Check for low attendance shortage on boot
window.addEventListener('load', () => {
    setTimeout(() => {
        if(!COURSES) return;
        const lowAtt = COURSES.filter(c => {
            const att = ATTENDANCE[c.code] || {percent: 0};
            return att.percent < 75;
        });
        if(lowAtt.length > 0) document.getElementById('stuChatWarning').style.display = 'block';
    }, 2000);
});
  


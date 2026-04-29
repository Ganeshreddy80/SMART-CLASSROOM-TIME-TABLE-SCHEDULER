
    /* ══════════ RESET & ROOT ══════════ */
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }

    :root {
      --blue: #1e3a8a;
      --indigo: #6366f1;
      --green: #22c55e;
      --orange: #f97316;
      --red: #ef4444;
      --dark: #0f172a;
      --muted: #64748b;
      --border: #e2e8f0;
      --bg: #f1f5f9;
    }

    body {
      font-family: 'Segoe UI', system-ui, sans-serif;
      background: var(--bg);
      display: flex;
      min-height: 100vh;
    }

    /* ══════════ SIDEBAR ══════════ */
    .sidebar {
      width: 245px;
      background: linear-gradient(160deg, #0f172a 0%, #1e1b4b 60%, #0f172a 100%);
      color: #fff;
      display: flex;
      flex-direction: column;
      height: 100vh;
      position: fixed;
      left: 0;
      top: 0;
      z-index: 100;
      overflow-y: auto;
    }

    .sb-brand {
      padding: 22px 18px 14px;
      border-bottom: 1px solid rgba(255, 255, 255, .07);
    }

    .sb-logo {
      font-size: 1.5rem;
    }

    .sb-title {
      font-size: 1rem;
      font-weight: 900;
      color: #fff;
      display: block;
    }

    .sb-sub {
      font-size: .68rem;
      color: #818cf8;
      display: block;
      font-weight: 600;
    }

    .sb-sec {
      font-size: .6rem;
      font-weight: 800;
      color: #4f46e5;
      letter-spacing: .1em;
      text-transform: uppercase;
      padding: 14px 18px 4px;
    }

    .sb-nav {
      list-style: none;
      padding: 0 10px;
      margin: 0 0 4px;
    }

    .sb-nav li a {
      display: flex;
      align-items: center;
      gap: 9px;
      padding: 9px 12px;
      border-radius: 10px;
      font-size: .8rem;
      color: #a5b4fc;
      cursor: pointer;
      transition: all .18s;
      margin-bottom: 2px;
      font-weight: 500;
      text-decoration: none;
    }

    .sb-nav li a:hover {
      background: rgba(99, 102, 241, .2);
      color: #fff;
    }

    .sb-nav li a.active {
      background: linear-gradient(90deg, #6366f1, #1e3a8a);
      color: #fff;
      font-weight: 700;
      box-shadow: 0 2px 12px rgba(99, 102, 241, .4);
    }

    .sb-foot {
      margin-top: auto;
      padding: 14px;
      border-top: 1px solid rgba(255, 255, 255, .07);
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .sb-av {
      width: 38px;
      height: 38px;
      border-radius: 50%;
      border: 2px solid #6366f1;
      overflow: hidden;
      flex-shrink: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      background: linear-gradient(135deg, #6366f1, #1e3a8a);
    }

    .sb-av img {
      width: 100%;
      height: 100%;
      object-fit: cover;
      border-radius: 50%;
    }

    .sb-name {
      font-size: .8rem;
      font-weight: 700;
      color: #fff;
      line-height: 1.2;
    }

    .sb-reg {
      font-size: .66rem;
      color: #818cf8;
    }

    /* ══════════ MAIN ══════════ */
    .main {
      margin-left: 245px;
      min-height: 100vh;
      background: var(--bg);
      padding: 24px;
      flex: 1;
    }

    .topbar {
      background: #fff;
      border-radius: 14px;
      padding: 13px 20px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 20px;
      box-shadow: 0 1px 6px rgba(0, 0, 0, .06);
    }

    .tb-title {
      font-size: 1rem;
      font-weight: 800;
      color: var(--dark);
    }

    .tb-right {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .tb-date {
      font-size: .75rem;
      color: var(--muted);
      background: #f8fafc;
      padding: 5px 12px;
      border-radius: 20px;
    }

    .logout-btn {
      background: linear-gradient(90deg, #6366f1, #1e3a8a);
      color: #fff;
      border: none;
      border-radius: 20px;
      padding: 6px 16px;
      font-size: .74rem;
      font-weight: 700;
      cursor: pointer;
    }

    .logout-btn:hover {
      opacity: .88;
    }

    #page-content {
      animation: fadeIn .25s ease;
    }

    @keyframes fadeIn {
      from {
        opacity: 0;
        transform: translateY(8px)
      }

      to {
        opacity: 1;
        transform: none
      }
    }

    /* ══════════ HERO ══════════ */
    .hero-card {
      background: linear-gradient(135deg, #4f46e5 0%, #1e3a8a 100%);
      border-radius: 20px;
      padding: 26px;
      display: flex;
      align-items: center;
      gap: 22px;
      flex-wrap: wrap;
      margin-bottom: 20px;
      box-shadow: 0 6px 24px rgba(79, 70, 229, .3);
    }

    .hero-av-wrap {
      position: relative;
      flex-shrink: 0;
    }

    .hero-av-circle {
      width: 108px;
      height: 108px;
      border-radius: 50%;
      border: 4px solid rgba(255, 255, 255, .4);
      overflow: hidden;
      cursor: pointer;
      position: relative;
      display: flex;
      align-items: center;
      justify-content: center;
      background: linear-gradient(135deg, #6366f1, #1e3a8a);
    }

    .hero-av-circle img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }

    .av-overlay {
      position: absolute;
      inset: 0;
      border-radius: 50%;
      background: rgba(0, 0, 0, .5);
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      opacity: 0;
      transition: .22s;
      cursor: pointer;
    }

    .hero-av-wrap:hover .av-overlay {
      opacity: 1;
    }

    .av-overlay span {
      font-size: 1.3rem;
    }

    .av-overlay small {
      color: #fff;
      font-size: .62rem;
    }

    .upload-btn {
      margin-top: 7px;
      background: rgba(255, 255, 255, .18);
      color: #fff;
      border: 1.5px solid rgba(255, 255, 255, .4);
      padding: 4px 12px;
      border-radius: 20px;
      font-size: .67rem;
      font-weight: 700;
      cursor: pointer;
      text-align: center;
      display: block;
      width: 100%;
    }

    .upload-btn:hover {
      background: rgba(255, 255, 255, .32);
    }

    .hero-info h1 {
      font-size: 1.45rem;
      font-weight: 900;
      color: #fff;
      margin-bottom: 4px;
    }

    .regno {
      background: rgba(255, 255, 255, .18);
      color: #fff;
      font-size: .7rem;
      font-weight: 700;
      padding: 3px 11px;
      border-radius: 20px;
      display: inline-block;
      margin-bottom: 8px;
    }

    .hero-meta {
      font-size: .79rem;
      color: rgba(255, 255, 255, .85);
      margin-bottom: 4px;
    }

    .hero-contact {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      font-size: .74rem;
      color: rgba(255, 255, 255, .75);
      margin-top: 6px;
    }

    .hero-contact span {
      background: rgba(255, 255, 255, .12);
      padding: 3px 10px;
      border-radius: 20px;
    }

    /* ══════════ STATS ══════════ */
    .stat-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(110px, 1fr));
      gap: 14px;
      margin-bottom: 20px;
    }

    .stat {
      background: #fff;
      border-radius: 14px;
      padding: 16px 14px;
      text-align: center;
      box-shadow: 0 1px 6px rgba(0, 0, 0, .05);
      border-top: 3px solid #6366f1;
    }

    .stat-v {
      font-size: 1.65rem;
      font-weight: 900;
      color: var(--dark);
    }

    .stat-l {
      font-size: .7rem;
      color: var(--muted);
      margin-top: 3px;
    }

    /* ══════════ CARDS ══════════ */
    .card {
      background: #fff;
      border-radius: 16px;
      padding: 20px;
      box-shadow: 0 1px 8px rgba(0, 0, 0, .06);
      margin-bottom: 18px;
    }

    .card-title {
      font-size: .92rem;
      font-weight: 800;
      color: var(--dark);
      margin-bottom: 16px;
      padding-bottom: 10px;
      border-bottom: 2px solid #f1f5f9;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    /* ══════════ TIMETABLE TABLE ══════════ */
    .tt-table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 10px;
      font-size: .82rem;
    }

    .tt-table th {
      background: #f8fafc;
      color: var(--dark);
      padding: 12px;
      text-align: left;
      font-weight: 700;
      border-bottom: 2px solid var(--border);
    }

    .tt-table td {
      padding: 12px;
      border-bottom: 1px solid #f1f5f9;
      vertical-align: middle;
    }

    .tt-table tr:hover td {
      background: #fcfdfe;
    }

    /* ══════════ WEEKLY GRID ══════════ */
    .week-grid-wrap {
      overflow-x: auto;
      margin-top: 10px;
      border-radius: 12px;
      border: 1px solid var(--border);
    }

    .week-grid {
      width: 100%;
      border-collapse: collapse;
      table-layout: fixed;
      font-size: .72rem;
      min-width: 700px;
    }

    .week-grid th {
      background: #0f172a;
      color: #fff;
      padding: 12px 5px;
      text-align: center;
      border: 1px solid #1e293b;
    }

    .week-grid td {
      height: 85px;
      border: 1px solid var(--border);
      padding: 5px;
      vertical-align: top;
      background: #fff;
    }

    .week-grid .time-col {
      width: 85px;
      background: #f8fafc;
      font-weight: 700;
      color: var(--muted);
      text-align: center;
      vertical-align: middle;
      font-size: .7rem;
    }

    .grid-cell {
      height: 100%;
      border-radius: 6px;
      padding: 6px;
      display: flex;
      flex-direction: column;
      gap: 3px;
      background: rgba(99, 102, 241, .05);
      border-left: 3px solid #6366f1;
      overflow: hidden;
      transition: .15s;
    }

    .grid-cell:hover {
      transform: scale(1.02);
      box-shadow: 0 2px 8px rgba(0, 0, 0, .1);
      z-index: 1;
    }

    .grid-cell.empty {
      background: transparent;
      border: none;
    }

    .grid-course {
      font-weight: 800;
      color: #1e3a8a;
      font-size: .68rem;
    }

    .grid-room {
      font-size: .6rem;
      color: var(--muted);
      margin-top: auto;
    }

    .grid-fac {
      font-size: .6rem;
      color: var(--muted);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    /* ══════════ ATTENDANCE ══════════ */
    .att-table {
      width: 100%;
      border-collapse: collapse;
      font-size: .8rem;
    }

    .att-table th {
      background: #0f172a;
      color: #fff;
      padding: 10px 12px;
      font-size: .73rem;
      font-weight: 700;
      text-align: center;
    }

    .att-table th:first-child {
      text-align: left;
    }

    .att-table td {
      padding: 10px 12px;
      text-align: center;
      border-bottom: 1px solid #f1f5f9;
      color: var(--dark);
    }

    .att-table td:first-child {
      text-align: left;
      font-weight: 600;
    }

    .att-table tr:hover td {
      background: #f8fafc;
    }

    .bar-wrap {
      background: #e2e8f0;
      border-radius: 20px;
      height: 8px;
      flex: 1;
      overflow: hidden;
      min-width: 60px;
    }

    .bar {
      height: 100%;
      border-radius: 20px;
      transition: width .5s;
    }

    /* ══════════ MARKS ══════════ */
    .cgpa-hero {
      background: linear-gradient(135deg, #4f46e5, #1e3a8a);
      border-radius: 16px;
      padding: 22px;
      color: #fff;
      margin-bottom: 16px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 12px;
    }

    .cgpa-big {
      font-size: 3.2rem;
      font-weight: 900;
      line-height: 1;
    }

    .sem-block {
      background: #fff;
      border-radius: 14px;
      border: 1px solid var(--border);
      margin-bottom: 12px;
      overflow: hidden;
    }

    .sem-head {
      padding: 14px 18px;
      background: #f8fafc;
      display: flex;
      align-items: center;
      justify-content: space-between;
      border-bottom: 1px solid var(--border);
    }

    .mark-table {
      width: 100%;
      border-collapse: collapse;
      font-size: .79rem;
    }

    .mark-table th {
      background: #f1f5f9;
      color: var(--dark);
      padding: 9px 12px;
      text-align: left;
      font-size: .72rem;
      font-weight: 700;
      border-bottom: 2px solid var(--border);
    }

    .mark-table td {
      padding: 9px 12px;
      border-bottom: 1px solid #f8fafc;
    }

    /* ══════════ COURSES ══════════ */
    .course-grid {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-bottom: 18px;
    }

    .course-chip {
      background: #f8fafc;
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 12px 16px;
      min-width: 200px;
      flex: 1;
      transition: .18s;
    }

    .course-chip:hover {
      border-color: #6366f1;
      box-shadow: 0 2px 10px rgba(99, 102, 241, .1);
    }

    .course-code {
      font-size: .75rem;
      font-weight: 800;
      color: #6366f1;
      margin-bottom: 3px;
    }

    .course-name {
      font-size: .82rem;
      font-weight: 700;
      color: var(--dark);
      margin-bottom: 6px;
    }

    .course-meta {
      display: flex;
      gap: 6px;
      flex-wrap: wrap;
    }

    /* ══════════ HOSTEL ══════════ */
    .hostel-card {
      border-radius: 16px;
      padding: 22px;
      margin-bottom: 14px;
    }

    .det-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 9px 0;
      border-bottom: 1px solid rgba(0, 0, 0, .05);
      font-size: .82rem;
    }

    .det-l {
      color: var(--muted);
    }

    .det-v {
      font-weight: 700;
      color: var(--dark);
    }

    /* ══════════ DAY LABEL ══════════ */
    .day-label {
      font-size: .75rem;
      font-weight: 800;
      color: #6366f1;
      text-transform: uppercase;
      letter-spacing: .06em;
      margin: 14px 0 6px;
    }

    .loading {
      text-align: center;
      padding: 32px;
      color: var(--muted);
      font-size: .88rem;
    }

    .initials-av {
      width: 100%;
      height: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 800;
      font-size: .85rem;
      color: #fff;
      background: linear-gradient(135deg, #6366f1, #1e3a8a);
      border-radius: 50%;
    }

    /* ─── AI Chatbot UI ────────────────────────────────────────────── */
    .chat-fab {
      position: fixed;
      bottom: 24px;
      right: 24px;
      width: 60px;
      height: 60px;
      background: var(--side);
      color: white;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 1.5rem;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
      cursor: pointer;
      z-index: 1000;
      transition: transform 0.2s, box-shadow 0.2s;
    }

    .chat-fab:hover {
      transform: translateY(-2px) scale(1.05);
      box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);
    }

    .chat-fab .warning-dot {
      position: absolute;
      top: 0;
      right: 0;
      width: 14px;
      height: 14px;
      background: var(--danger);
      border: 2px solid white;
      border-radius: 50%;
      display: none;
      animation: pulse 2s infinite;
    }

    .chat-panel {
      position: fixed;
      bottom: 96px;
      right: 24px;
      width: 380px;
      height: 500px;
      background: #fff;
      border-radius: 20px;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
      display: flex;
      flex-direction: column;
      z-index: 1000;
      overflow: hidden;
      transform: translateY(20px);
      opacity: 0;
      pointer-events: none;
      transition: all 0.3s ease;
    }

    .chat-panel.open {
      transform: translateY(0);
      opacity: 1;
      pointer-events: auto;
    }

    .chat-header {
      background: var(--side);
      color: #fff;
      padding: 16px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .chat-header h3 {
      margin: 0;
      font-size: 1.1rem;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .chat-close {
      background: transparent;
      border: none;
      color: #fff;
      font-size: 1.2rem;
      cursor: pointer;
      opacity: 0.7;
    }

    .chat-close:hover {
      opacity: 1;
    }

    .chat-messages {
      flex: 1;
      overflow-y: auto;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 12px;
      background: #f8fafc;
    }

    .greeting-card {
      background: linear-gradient(135deg, var(--side), var(--side-h));
      color: white;
      padding: 16px;
      border-radius: 14px;
      margin-bottom: 12px;
      font-size: 0.9rem;
    }

    .greeting-card h4 {
      margin-bottom: 4px;
    }

    .chat-bubble {
      max-width: 85%;
      padding: 12px 16px;
      border-radius: 12px;
      font-size: 0.9rem;
      line-height: 1.4;
      word-wrap: break-word;
    }

    .chat-bubble table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 8px;
      font-size: 0.8rem;
      background: white;
    }

    .chat-bubble th,
    .chat-bubble td {
      border: 1px solid var(--border);
      padding: 4px 6px;
      text-align: left;
    }

    .chat-bubble th {
      background: #f1f5f9;
    }

    .chat-msg.user {
      align-self: flex-end;
    }

    .chat-msg.user .chat-bubble {
      background: var(--side);
      color: #fff;
      border-bottom-right-radius: 4px;
    }

    .chat-msg.bot {
      align-self: flex-start;
    }

    .chat-msg.bot .chat-bubble {
      background: #fff;
      color: var(--text);
      border: 1px solid var(--border);
      border-bottom-left-radius: 4px;
    }

    .chat-input-area {
      padding: 16px;
      background: #fff;
      border-top: 1px solid var(--border);
      display: flex;
      gap: 8px;
    }

    .chat-input {
      flex: 1;
      border: 1px solid var(--border);
      border-radius: 30px;
      padding: 10px 16px;
      outline: none;
      background: #f8fafc;
      color: var(--text);
    }

    .chat-input:focus {
      border-color: var(--accent);
    }

    .chat-send-btn {
      background: var(--accent);
      color: white;
      border: none;
      width: 40px;
      height: 40px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
    }

    .typing-indicator {
      display: flex;
      gap: 4px;
      padding: 8px 12px;
      background: #fff;
      border: 1px solid var(--border);
      border-radius: 12px;
      border-bottom-left-radius: 4px;
      width: fit-content;
      align-self: flex-start;
    }

    .typing-dot {
      width: 6px;
      height: 6px;
      background: var(--muted);
      border-radius: 50%;
      animation: typing 1.4s infinite ease-in-out both;
    }

    .typing-dot:nth-child(1) {
      animation-delay: -0.32s;
    }

    .typing-dot:nth-child(2) {
      animation-delay: -0.16s;
    }

    @keyframes typing {

      0%,
      80%,
      100% {
        transform: scale(0);
      }

      40% {
        transform: scale(1);
      }
    }

    .chat-suggestions {
      padding: 10px 16px;
      background: #f8fafc;
      display: flex;
      gap: 8px;
      overflow-x: auto;
      border-top: 1px solid var(--border);
    }

    .chat-suggestions::-webkit-scrollbar {
      display: none;
    }

    .suggestion-chip {
      white-space: nowrap;
      padding: 6px 12px;
      background: #fff;
      border: 1px solid var(--border);
      border-radius: 20px;
      font-size: 0.75rem;
      color: var(--muted);
      cursor: pointer;
      transition: all 0.2s;
    }

    .suggestion-chip:hover {
      border-color: var(--side);
      color: var(--side);
      background: #f1f5f9;
    }





    /* ══════════ STATE ══════════ */
    let PROFILE = {}, COURSES = [], TIMETABLE = [], ATTENDANCE = {}, TODAY_ATT = [], MARKS = [], FACULTY_ABSENCE = {};
    const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'];
    const SLOTS = ['9-10', '10-11', '11-12', '12-1', '2-3', '3-4', '4-5'];

    /* ══════════ UTILS ══════════ */
    function todayKey() { return new Date().toISOString().split('T')[0]; }
    function todayDay() { return ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'][new Date().getDay()]; }
    function slotOrder(s) { return SLOTS.indexOf(s); }
    function slotStatus(s) {
      const h = new Date().getHours(); const p = s.split('-');
    }
    function isSlotCancelled(fid, date, slot) {
      const c = FACULTY_ABSENCE[fid] && FACULTY_ABSENCE[fid][date];
      return Array.isArray(c) && c.includes(slot);
    }
    function formatDate() { return new Date().toLocaleDateString('en-IN', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' }); }

    /* ══════════ PHOTO ══════════ */
    function updateSidebarPhoto() {
      const av = $('sb-av');
      const cached = localStorage.getItem('student_photo_' + PROFILE.id);
      const photo = PROFILE.photo || cached || '';
    }
    $('photoInput').addEventListener('change', function (e) {
      const file = e.target.files[0]; if (!file) return;
      if (!file.type.startsWith('image/')) { showToast('Select an image file', 'warning'); return; }
      const r = new FileReader();
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
        if (loading) {
          loading = false;
          $('page-content').innerHTML = `
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
            
        $('page-content').innerHTML = `
            ${actionBtn}
        `;
        $('sb-name').textContent = isSessionErr ? 'Session Expired' : 'Error Loading Data';
      }
    }

    /* ══════════ ROUTER ══════════ */
    const PAGE_TITLES = { dashboard: 'Dashboard', today: "Today's Timetable", fulltable: 'Full Timetable', attendance: 'Attendance', marks: 'Exam Marks & CGPA', courses: 'My Courses', hostel: 'Hostel & Transport' };
    function showPage(page) {
      $('page-title').textContent = PAGE_TITLES[page] || '';
      const pages = { dashboard: pgDashboard, today: pgToday, fulltable: pgFullTT, attendance: pgAttendance, marks: pgMarks, courses: pgCourses, hostel: pgHostel };
      if (pages[page]) $('page-content').innerHTML = pages[page]();
    }

    /* ══════════ TIMETABLE TABLE BUILDER ══════════ */
    function buildTTTable(entries, showPresence = false) {
      return `
        const cancelled = isSlotCancelled(t.faculty, todayKey(), t.slot);
        const st = slotStatus(t.slot);
        let presHtml = '';
        if (showPresence) {
        }

        return `
            ${cancelled
      }).join('')}
    }

    /* ══════════ PAGE: DASHBOARD ══════════ */
    function pgDashboard() {
      const photo = PROFILE.photo || localStorage.getItem('student_photo_' + PROFILE.id) || '';
      return `
    ${buildTTTable(todayTT, true)}
    }

    /* ══════════ PAGE: TODAY TIMETABLE ══════════ */
    function pgToday() {
  ${buildTTTable(todayTT, true)}
    }

    /* ══════════ PAGE: FULL TIMETABLE ══════════ */
    function pgFullTT() {
      return `
        return `
      }).join('')}
          `).join('')}
    }

    /* ══════════ PAGE: ATTENDANCE ══════════ */
    function pgAttendance() {
        const a = ATTENDANCE[c.code];
      }).join('')}
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
  datasets: [{
  label: 'Attendance %',
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
  return`
  }

  /* ══════════ PAGE: COURSES ══════════ */
  function pgCourses(){
      }).join('')}
  }

  /* ══════════ PAGE: HOSTEL ══════════ */
  function pgHostel(){
  const h=(PROFILE.hostel||'').toLowerCase();
  const type=h.includes('bus')?'bus':h.includes('day')||h===''?'dayscholar':'hostel';
  const cfg={
  hostel:{icon:'🏠',title:'Hostel
  Resident',bg:'linear-gradient(135deg,#f0fdf4,#dcfce7)',border:'#bbf7d0',tc:'#166534',nb:'#bbf7d0',nc:'#166534',note:'✅
  You are a Hostel Resident. For hostel-related queries contact the warden.'},
  bus:{icon:'🚌',title:'Bus
  Commuter',bg:'linear-gradient(135deg,#eff6ff,#dbeafe)',border:'#bfdbfe',tc:'#1d4ed8',nb:'#bfdbfe',nc:'#1d4ed8',note:'🚌
  You are a Bus Commuter. Contact the transport office for route and timing details.'},
  dayscholar:{icon:'🏡',title:'Day
  Scholar',bg:'linear-gradient(135deg,#fefce8,#fef9c3)',border:'#fde68a',tc:'#92400e',nb:'#fde68a',nc:'#92400e',note:'🏡
  You are a Day Scholar. Arrive on time and sign the daily attendance register.'}
  }[type];
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

    let greetingHtml = `
        `;
    
        const att = ATTENDANCE[c.code] || {percent: 0};
    });
    
        greetingHtml += `
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
            const actionMatch = data.reply.match(/```action\s *\n([\s\S] *?)```/);
            let displayText = data.reply;
            let actionHtml = '';
            
            if (actionMatch) {
                try {
                    const actionJson = JSON.parse(actionMatch[1]);
                    displayText = data.reply.replace(actionMatch[0], '');
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
    div.className = `chat - msg ${ role } `;
    
    let html = text
    
    if (text.includes('|')) {
        const lines = text.split('\n');
        let inTable = false;
        let newHtml = '';
        
            if (line.trim().startsWith('|')) {
                if (line.includes('---')) return;
            } else {
            }
        });
        html = newHtml;
    }

    container.appendChild(div);
    scrollStuChat();
}

function scrollStuChat() {
    const el = document.getElementById('stuChatMessages');
    el.scrollTop = el.scrollHeight;
}

// Check for low attendance shortage on boot
        if(!COURSES) return;
            const att = ATTENDANCE[c.code] || {percent: 0};
        });
    }, 2000);
});


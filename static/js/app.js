/* ─── Common API Helper ────────────────────────────────────── */
async function api(url, method = 'GET', body = null) {
    const opts = {
        method,
        headers: { 'Content-Type': 'application/json' }
    };
    if (body) opts.body = JSON.stringify(body);
    const res = await fetch(url, opts);
    return res.json();
}

/* ─── Toast Notification (Navy + Gold) ───────────────────────── */
function showToast(msg, type = 'success') {
    // Remove existing toasts
    document.querySelectorAll('.toast').forEach(t => t.remove());

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    const icons = { success: '✓', danger: '✕', warning: '⚠', info: 'ℹ' };
    toast.innerHTML = `<span style="font-weight:700;margin-right:8px;font-size:1.1rem">${icons[type] || '●'}</span>${msg}`;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.transition = 'all 0.3s ease';
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(20px)';
        setTimeout(() => toast.remove(), 300);
    }, 2800);
}

/* ─── Timetable Grid Renderer ────────────────────────────────── */
function renderTimetableGrid(containerId, entries, days, timeslots, mode = 'section') {
    const container = document.getElementById(containerId);
    if (!container) return;

    container.style.gridTemplateColumns = `100px repeat(${days.length}, 1fr)`;

    let html = '<div class="tt-header"></div>';
    days.forEach(d => { html += `<div class="tt-header">${d.substring(0, 3)}</div>`; });

    timeslots.forEach(ts => {
        html += `<div class="tt-time">${ts}</div>`;
        days.forEach(day => {
            const entry = entries.find(e => e.day === day && e.timeslot === ts);
            if (entry) {
                const deptIdx = (entry.course_id || 0) % 8;
                let clickAttr = '';
                if (mode === 'section_admin') {
                    clickAttr = `onclick="openEditRoomModal(${entry.id}, ${entry.section_id || entry.section}, '${entry.day}', '${entry.timeslot}')" style="cursor: pointer;" title="Click to change room"`;
                }
                
                html += `<div class="tt-cell dept-${deptIdx}" ${clickAttr}>
                    <div class="course-name">${entry.course_code || entry.course_name || entry.course}</div>
                    <div class="faculty-name">${entry.faculty_name || entry.faculty}</div>
                    <div class="room-name">${entry.room_number || entry.room}</div>
                </div>`;
            } else {
                html += '<div class="tt-cell empty">—</div>';
            }
        });
    });

    container.innerHTML = html;
}

/* ─── Print / Export ─────────────────────────────────────────── */
function exportPrint(elementId = 'timetableArea', filename = 'timetable.pdf') {
    const el = document.getElementById(elementId);
    if (!el) {
        window.print();
        return;
    }
    
    showToast('Preparing PDF...', 'info');
    
    const opt = {
        margin:       10,
        filename:     filename,
        image:        { type: 'jpeg', quality: 0.98 },
        html2canvas:  { scale: 2, useCORS: true },
        jsPDF:        { unit: 'mm', format: 'a4', orientation: 'landscape' }
    };
    
    html2pdf().set(opt).from(el).save().then(() => {
        showToast('PDF downloaded successfully!', 'success');
    }).catch(err => {
        console.error('PDF export error:', err);
        showToast('Failed to generate PDF. Falling back to print.', 'warning');
        window.print();
    });
}

/* ─── Multi-select helper (get selected values) ──────────────── */
function getSelectedValues(selectId) {
    const sel = document.getElementById(selectId);
    if (!sel) return [];
    return Array.from(sel.selectedOptions).map(o => parseInt(o.value));
}

/* ─── Populate a <select> with options ───────────────────────── */
function populateSelect(selectId, items, valueFn, labelFn, placeholder = '') {
    const sel = document.getElementById(selectId);
    if (!sel) return;
    sel.innerHTML = '';
    if (placeholder) {
        const opt = document.createElement('option');
        opt.value = '';
        opt.textContent = placeholder;
        sel.appendChild(opt);
    }
    items.forEach(item => {
        const opt = document.createElement('option');
        opt.value = valueFn(item);
        opt.textContent = labelFn(item);
        sel.appendChild(opt);
    });
}

/* ─── Confirmation dialog ────────────────────────────────────── */
function confirmAction(msg) {
    return confirm(msg);
}

/* ─── Close sidebar on mobile after navigation ───────────────── */
document.addEventListener('DOMContentLoaded', () => {
    // Auto-close sidebar on mobile when a link is clicked
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', () => {
            if (window.innerWidth <= 1024) {
                document.querySelector('.sidebar').classList.remove('open');
            }
        });
    });
});

/**
 * VisionAttend - Smart Face Recognition Attendance System
 * Frontend Application Script
 */

document.addEventListener('DOMContentLoaded', () => {
    initThemeToggle();
    initClock();
    initNavigation();
    initDashboard();
    initStudents();
    initReports();
    initRegistrationModal();
    initPollingForEvents();
});

/* ==========================================
   0. Neobrutalism Light/Dark Theme Toggle
   ========================================== */
function initThemeToggle() {
    const toggleBtn = document.getElementById('btn-theme-toggle');
    const iconEl = document.getElementById('theme-toggle-icon');
    const textEl = document.getElementById('theme-toggle-text');

    const savedTheme = localStorage.getItem('visionattend_theme') || 'light';
    applyTheme(savedTheme);

    if (toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            applyTheme(newTheme);
        });
    }

    function applyTheme(theme) {
        if (theme === 'dark') {
            document.documentElement.setAttribute('data-theme', 'dark');
            if (iconEl) iconEl.className = 'fa-solid fa-sun';
            if (textEl) textEl.textContent = 'Light Mode';
        } else {
            document.documentElement.removeAttribute('data-theme');
            if (iconEl) iconEl.className = 'fa-solid fa-moon';
            if (textEl) textEl.textContent = 'Dark Mode';
        }
        localStorage.setItem('visionattend_theme', theme);
    }
}

/* ==========================================
   1. Live Clock & Header Navigation
   ========================================== */
function initClock() {
    const clockEl = document.getElementById('clock-display');
    function updateClock() {
        const now = new Date();
        clockEl.textContent = now.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: true
        });
    }
    updateClock();
    setInterval(updateClock, 1000);
}

function initNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    const tabPanes = document.querySelectorAll('.tab-pane');
    const titleEl = document.getElementById('active-tab-title');
    const subtitleEl = document.getElementById('active-tab-subtitle');

    const tabMeta = {
        'tab-dashboard': {
            title: 'Dashboard Overview',
            subtitle: 'Real-time attendance analytics & system metrics'
        },
        'tab-kiosk': {
            title: 'Live Camera Verification Kiosk',
            subtitle: 'Automated face recognition camera stream & instant logging'
        },
        'tab-students': {
            title: 'Student Directory',
            subtitle: 'Registered profiles & facial feature embeddings'
        },
        'tab-reports': {
            title: 'Attendance Reports & Data Export',
            subtitle: 'Filter verification logs and export formatted Excel/CSV reports'
        }
    };

    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const targetTab = item.getAttribute('data-tab');

            navItems.forEach(nav => nav.classList.remove('active'));
            tabPanes.forEach(pane => pane.classList.remove('active'));

            item.classList.add('active');
            const targetPane = document.getElementById(targetTab);
            if (targetPane) targetPane.classList.add('active');

            if (tabMeta[targetTab]) {
                titleEl.textContent = tabMeta[targetTab].title;
                subtitleEl.textContent = tabMeta[targetTab].subtitle;
            }

            // Refresh tab data & camera lifecycle on view change
            if (targetTab === 'tab-dashboard') {
                stopBrowserKioskCamera();
                fetchDashboardStats();
            } else if (targetTab === 'tab-kiosk') {
                if (currentKioskMode === 'browser') {
                    startBrowserKioskCamera();
                }
            } else {
                stopBrowserKioskCamera();
                if (targetTab === 'tab-students') fetchStudents();
                if (targetTab === 'tab-reports') fetchReports();
            }
        });
    });
}

/* ==========================================
   2. Dashboard Analytics & Activity Feed
   ========================================== */
function initDashboard() {
    fetchDashboardStats();
    // Auto-refresh stats every 10 seconds
    setInterval(fetchDashboardStats, 10000);
}

async function fetchDashboardStats() {
    try {
        const res = await fetch('/api/dashboard/stats');
        if (!res.ok) return;
        const data = await res.json();

        document.getElementById('stat-total-students').textContent = data.total_students;
        document.getElementById('stat-present-today').textContent = data.present_today;
        document.getElementById('stat-absent-today').textContent = data.absent_today;
        document.getElementById('stat-rate-percent').textContent = `${data.attendance_rate}%`;
        document.getElementById('stat-present-sub').textContent = `${data.attendance_rate}% Attendance Rate`;

        if (data.today_date) {
            document.getElementById('today-date-badge').textContent = `Date: ${data.today_date}`;
        }

        // Render Recent Activity Logs
        renderActivityFeed(data.recent_logs);
        // Render Department breakdown
        renderDepartmentStats(data.department_stats);
        // Fetch ML model status
        fetchMLStatus();

    } catch (err) {
        console.error('Error fetching dashboard stats:', err);
    }
}

async function fetchMLStatus() {
    try {
        const res = await fetch('/api/ml/status');
        if (!res.ok) return;
        const data = await res.json();

        const statusText = document.getElementById('ml-status-text');
        const accBadge = document.getElementById('ml-acc-badge');
        if (statusText) {
            statusText.textContent = `Model: ${data.model_type} (${data.total_samples} samples trained)`;
        }
        if (accBadge) {
            accBadge.textContent = `${data.training_accuracy}% Accuracy`;
        }
    } catch (e) { }
}

// ML Retrain Button Listener
document.addEventListener('DOMContentLoaded', () => {
    const retrainBtn = document.getElementById('btn-retrain-ml');
    if (retrainBtn) {
        retrainBtn.addEventListener('click', async () => {
            retrainBtn.disabled = true;
            retrainBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Training...`;
            try {
                const res = await fetch('/api/ml/train', { method: 'POST' });
                const data = await res.json();
                if (res.ok) {
                    showToast(data.message || 'ML Model trained successfully!');
                    fetchMLStatus();
                }
            } catch (err) {
                console.error('ML train error:', err);
            } finally {
                retrainBtn.disabled = false;
                retrainBtn.innerHTML = `<i class="fa-solid fa-arrows-rotate"></i> Re-Train ML Model`;
            }
        });
    }
});

function renderActivityFeed(logs) {
    const container = document.getElementById('activity-feed');
    if (!logs || logs.length === 0) {
        container.innerHTML = `
            <div style="text-align:center; padding: 24px; color: var(--text-muted);">
                <i class="fa-regular fa-folder-open" style="font-size: 24px; margin-bottom:8px;"></i>
                <p>No attendance logs recorded for today yet.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = logs.map(log => `
        <div class="activity-item">
            <div class="user-info">
                <div class="user-details">
                    <h4>${log.student_name}</h4>
                    <span>${log.roll_no} • ${log.department} (${log.confidence}% match)</span>
                </div>
            </div>
            <div class="time-badge">
                <i class="fa-solid fa-check"></i> ${log.time}
            </div>
        </div>
    `).join('');
}

function renderDepartmentStats(deptStats) {
    const container = document.getElementById('dept-distribution-list');
    if (!deptStats || Object.keys(deptStats).length === 0) {
        container.innerHTML = `<p class="text-muted">No student profiles registered.</p>`;
        return;
    }

    container.innerHTML = Object.entries(deptStats).map(([dept, count]) => `
        <div class="dept-item">
            <span class="dept-name">${dept}</span>
            <span class="dept-count">${count} Students</span>
        </div>
    `).join('');
}

/* ==========================================
   3. Live Kiosk & Event Polling
   ========================================== */
let kioskWebcamStream = null;
let kioskStreamInterval = null;
let currentKioskMode = 'browser'; // 'browser' or 'server'

function initKioskCamera() {
    const btnBrowser = document.getElementById('btn-cam-mode-browser');
    const btnServer = document.getElementById('btn-cam-mode-server');

    btnBrowser?.addEventListener('click', () => {
        setKioskMode('browser');
    });

    btnServer?.addEventListener('click', () => {
        setKioskMode('server');
    });

    // Quick demo manual checkin button
    const simBtn = document.getElementById('btn-manual-sim');
    if (simBtn) {
        simBtn.addEventListener('click', async () => {
            try {
                // Fetch first available student dynamically
                const sRes = await fetch('/api/students');
                const students = sRes.ok ? await sRes.json() : [];
                if (!students || students.length === 0) {
                    showToast('No registered students available for demo log. Please register a student first.');
                    return;
                }
                const firstStudent = students[0];
                const formData = new FormData();
                formData.append('student_id', firstStudent.id);
                const res = await fetch('/api/attendance/manual', {
                    method: 'POST',
                    body: formData
                });
                const data = await res.json();
                if (res.ok) {
                    playSuccessChime();
                    showToast(`Demo Log: ${data.message}`);
                    if (data.log) prependKioskLog(data.log);
                    fetchDashboardStats();
                }
            } catch (err) {
                console.error('Demo trigger failed:', err);
            }
        });
    }

    // Browser camera will start when user navigates to Live Kiosk tab
}

function setKioskMode(mode) {
    currentKioskMode = mode;
    const btnBrowser = document.getElementById('btn-cam-mode-browser');
    const btnServer = document.getElementById('btn-cam-mode-server');
    const browserBox = document.getElementById('browser-cam-box');
    const serverImg = document.getElementById('video-stream-img');

    if (mode === 'browser') {
        btnBrowser.className = 'btn btn-sm btn-primary active';
        btnServer.className = 'btn btn-sm btn-outline';
        browserBox.style.display = 'block';
        serverImg.style.display = 'none';
        serverImg.src = ''; // Stop server stream
        startBrowserKioskCamera();
    } else {
        btnServer.className = 'btn btn-sm btn-primary active';
        btnBrowser.className = 'btn btn-sm btn-outline';
        browserBox.style.display = 'none';
        serverImg.style.display = 'block';
        stopBrowserKioskCamera();
        serverImg.src = '/api/video_feed?' + new Date().getTime();
    }
}

async function startBrowserKioskCamera() {
    stopBrowserKioskCamera();

    const video = document.getElementById('kiosk-browser-video');
    const processedImg = document.getElementById('kiosk-processed-img');
    const canvas = document.getElementById('kiosk-browser-canvas');
    if (!video || !canvas) return;

    try {
        kioskWebcamStream = await navigator.mediaDevices.getUserMedia({
            video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: 'user' },
            audio: false
        });
        video.srcObject = kioskWebcamStream;

        await new Promise((resolve) => {
            video.onloadedmetadata = () => {
                video.play();
                resolve();
            };
        });

        // Set up processing frame loop every 180ms
        let isProcessing = false;
        kioskStreamInterval = setInterval(async () => {
            if (isProcessing || !kioskWebcamStream) return;
            if (video.videoWidth === 0 || video.videoHeight === 0) return;

            isProcessing = true;
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

            const b64Data = canvas.toDataURL('image/jpeg', 0.65);

            try {
                const formData = new FormData();
                formData.append('photo_base64', b64Data);

                const res = await fetch('/api/process_frame', {
                    method: 'POST',
                    body: formData
                });

                if (res.ok) {
                    const data = await res.json();
                    if (data.success && data.annotated_frame) {
                        processedImg.src = data.annotated_frame;
                    }
                    if (data.events && data.events.length > 0) {
                        data.events.forEach(evt => {
                            playSuccessChime();
                            showToast(`Attendance Marked: ${evt.student_name} (${evt.roll_no}) at ${evt.time}`);
                            prependKioskLog(evt);
                        });
                        fetchDashboardStats();
                    }
                }
            } catch (err) {
                console.error('Frame process error:', err);
            } finally {
                isProcessing = false;
            }
        }, 180);

    } catch (err) {
        console.warn('Could not access browser webcam:', err);
        // Fallback to server stream / simulation mode if permission denied
        setKioskMode('server');
    }
}

function stopBrowserKioskCamera() {
    if (kioskStreamInterval) {
        clearInterval(kioskStreamInterval);
        kioskStreamInterval = null;
    }
    if (kioskWebcamStream) {
        kioskWebcamStream.getTracks().forEach(track => track.stop());
        kioskWebcamStream = null;
    }
}

function initPollingForEvents() {
    initKioskCamera();

    // Backup poll for events when server mode active
    setInterval(async () => {
        if (currentKioskMode !== 'server') return;
        try {
            const res = await fetch('/api/recognition/latest-event');
            if (res.ok) {
                const data = await res.json();
                if (data.event) {
                    playSuccessChime();
                    showToast(`Attendance Marked: ${data.event.student_name} (${data.event.roll_no}) at ${data.event.time}`);
                    prependKioskLog(data.event);
                    fetchDashboardStats();
                }
            }
        } catch (e) { }
    }, 1500);
}

function prependKioskLog(log) {
    const kioskList = document.getElementById('kiosk-live-logs');
    if (!kioskList) return;

    const item = document.createElement('div');
    item.className = 'activity-item';
    item.style.background = '#E8F8F0';
    item.innerHTML = `
        <div class="user-info">
            <div class="user-details">
                <h4>${log.student_name}</h4>
                <span>${log.roll_no} • ${log.department}</span>
            </div>
        </div>
        <div class="time-badge">
            ${log.time}
        </div>
    `;
    kioskList.prepend(item);
}

// Audio Synthesizer Chime for Instant Verification Feedback
function playSuccessChime() {
    try {
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();

        osc.type = 'sine';
        osc.frequency.setValueAtTime(587.33, audioCtx.currentTime); // D5
        osc.frequency.exponentialRampToValueAtTime(880, audioCtx.currentTime + 0.15); // A5

        gain.gain.setValueAtTime(0.3, audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.3);

        osc.connect(gain);
        gain.connect(audioCtx.destination);

        osc.start();
        osc.stop(audioCtx.currentTime + 0.3);
    } catch (e) {
        // AudioContext restricted before user gesture
    }
}

function showToast(msg) {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.innerHTML = `
        <i class="fa-solid fa-circle-check"></i>
        <div>
            <strong>Attendance Logged</strong>
            <p style="font-size:13px; color: var(--text-secondary); margin-top:2px;">${msg}</p>
        </div>
    `;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

/* ==========================================
   4. Student Directory
   ========================================== */
function initStudents() {
    fetchStudents();

    const searchInput = document.getElementById('search-student-input');
    const deptSelect = document.getElementById('filter-dept-select');

    if (searchInput) {
        searchInput.addEventListener('input', debounce(fetchStudents, 300));
    }
    if (deptSelect) {
        deptSelect.addEventListener('change', fetchStudents);
    }
}

async function fetchStudents() {
    const search = document.getElementById('search-student-input')?.value || '';
    const dept = document.getElementById('filter-dept-select')?.value || 'All';

    try {
        const url = `/api/students?search=${encodeURIComponent(search)}&department=${encodeURIComponent(dept)}`;
        const res = await fetch(url);
        if (!res.ok) return;
        const students = await res.json();
        renderStudentsGrid(students);
    } catch (err) {
        console.error('Error fetching students:', err);
    }
}

function renderStudentsGrid(students) {
    const container = document.getElementById('students-grid-container');
    if (!students || students.length === 0) {
        container.innerHTML = `
            <div style="grid-column: 1/-1; text-align:center; padding: 40px;" class="content-card">
                <i class="fa-solid fa-users-slash" style="font-size: 32px; color: var(--text-muted); margin-bottom:12px;"></i>
                <h3>No Students Found</h3>
                <p style="color:var(--text-muted); margin-top:4px;">Click "Register Student" to add new student profiles.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = students.map(s => `
        <div class="student-card">
            <button class="btn-delete-student" onclick="deleteStudent(${s.id}, '${s.name}')" title="Delete Student">
                <i class="fa-solid fa-trash-can"></i>
            </button>
            <img src="${s.photo_path || '/static/img/default_avatar.png'}" alt="${s.name}" onerror="this.src='/static/img/default_avatar.png';">
            <h3>${s.name}</h3>
            <span class="roll-badge">${s.roll_no}</span>
            <div class="dept-tag">${s.department} (${s.year})</div>
        </div>
    `).join('');
}

async function deleteStudent(studentId, name) {
    if (!confirm(`Are you sure you want to remove '${name}' from the system?`)) return;

    try {
        const res = await fetch(`/api/students/${studentId}`, { method: 'DELETE' });
        if (res.ok) {
            showToast(`Student '${name}' removed.`);
            fetchStudents();
            fetchDashboardStats();
        }
    } catch (err) {
        console.error('Delete error:', err);
    }
}

/* ==========================================
   5. Reports & Export
   ========================================== */
function initReports() {
    // Set default date input to today
    const dateInput = document.getElementById('report-date-input');
    if (dateInput) {
        dateInput.value = new Date().toISOString().split('T')[0];
        dateInput.addEventListener('change', fetchReports);
    }

    const deptSelect = document.getElementById('report-dept-select');
    if (deptSelect) deptSelect.addEventListener('change', fetchReports);

    // Export Action Handlers
    document.getElementById('btn-export-csv')?.addEventListener('click', () => {
        const dateVal = document.getElementById('report-date-input')?.value || '';
        window.location.href = `/api/reports/export/csv?filter_date=${dateVal}`;
    });

    document.getElementById('btn-export-excel')?.addEventListener('click', () => {
        const dateVal = document.getElementById('report-date-input')?.value || '';
        window.location.href = `/api/reports/export/excel?filter_date=${dateVal}`;
    });

    // Admin Clear Attendance Handler
    document.getElementById('btn-clear-attendance')?.addEventListener('click', clearAttendanceLogs);

    fetchReports();
}

async function fetchReports() {
    const filterDate = document.getElementById('report-date-input')?.value || '';
    const dept = document.getElementById('report-dept-select')?.value || 'All';

    try {
        const url = `/api/attendance/logs?filter_date=${filterDate}&department=${encodeURIComponent(dept)}`;
        const res = await fetch(url);
        if (!res.ok) return;
        const logs = await res.json();
        renderReportsTable(logs);
    } catch (err) {
        console.error('Error fetching reports:', err);
    }
}

function renderReportsTable(logs) {
    const tbody = document.getElementById('reports-table-body');
    if (!logs || logs.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="10" style="text-align:center; padding: 28px; color: var(--text-muted);">
                    No attendance records match the selected filters.
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = logs.map(log => `
        <tr>
            <td style="font-family:var(--font-code); color:var(--text-muted);">#${log.id}</td>
            <td><strong>${log.student_name}</strong></td>
            <td><span class="roll-badge">${log.roll_no}</span></td>
            <td>${log.department}</td>
            <td>${log.date}</td>
            <td style="font-family:var(--font-code);">${log.time}</td>
            <td><span class="pulse-dot" style="display:inline-block; margin-right:4px;"></span> ${log.status}</td>
            <td style="font-weight:600; color:var(--accent-cyan);">${log.confidence}%</td>
            <td><span class="badge badge-dark">${log.method}</span></td>
            <td style="text-align: center;">
                <button class="btn-delete-student" onclick="deleteAttendanceLog(${log.id})" title="Delete Attendance Log" style="position:static; display:inline-flex; width:28px; height:28px; font-size:12px;">
                    <i class="fa-solid fa-trash-can"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

async function deleteAttendanceLog(logId) {
    if (!confirm(`Are you sure you want to delete attendance record #${logId}?`)) return;

    try {
        const res = await fetch(`/api/attendance/logs/${logId}`, { method: 'DELETE' });
        if (res.ok) {
            const data = await res.json();
            showToast(data.message || `Attendance log #${logId} deleted.`);
            fetchReports();
            fetchDashboardStats();
        } else {
            alert('Failed to delete attendance record.');
        }
    } catch (err) {
        console.error('Delete attendance error:', err);
    }
}

async function clearAttendanceLogs() {
    const dateVal = document.getElementById('report-date-input')?.value || '';
    const confirmMsg = dateVal
        ? `Are you sure you want to delete ALL attendance records for date ${dateVal}?`
        : 'Are you sure you want to delete ALL attendance records in the system?';

    if (!confirm(confirmMsg)) return;

    try {
        const res = await fetch(`/api/attendance/logs?filter_date=${encodeURIComponent(dateVal)}`, { method: 'DELETE' });
        if (res.ok) {
            const data = await res.json();
            showToast(data.message || 'Attendance records cleared.');
            fetchReports();
            fetchDashboardStats();
        } else {
            alert('Failed to clear attendance records.');
        }
    } catch (err) {
        console.error('Clear attendance error:', err);
    }
}

/* ==========================================
   6. Student Registration Modal & Camera Snap
   ========================================== */
let webcamStream = null;

function initRegistrationModal() {
    const modal = document.getElementById('register-modal');
    const openBtn = document.getElementById('btn-open-register');
    const closeBtn = document.getElementById('btn-close-modal');
    const cancelBtn = document.getElementById('btn-cancel-modal');
    const form = document.getElementById('register-student-form');

    const tabFile = document.getElementById('tab-upload-file');
    const tabCam = document.getElementById('tab-webcam-snap');
    const secFile = document.getElementById('section-file-upload');
    const secCam = document.getElementById('section-webcam-snap');

    openBtn?.addEventListener('click', () => modal.classList.add('active'));
    closeBtn?.addEventListener('click', closeModal);
    cancelBtn?.addEventListener('click', closeModal);

    function closeModal() {
        modal.classList.remove('active');
        stopWebcamStream();
        form.reset();
    }

    // Photo input tab switching
    tabFile?.addEventListener('click', () => {
        tabFile.classList.add('active');
        tabCam.classList.remove('active');
        secFile.classList.add('active');
        secCam.classList.remove('active');
        stopWebcamStream();
    });

    tabCam?.addEventListener('click', async () => {
        tabCam.classList.add('active');
        tabFile.classList.remove('active');
        secCam.classList.add('active');
        secFile.classList.remove('active');
        startWebcamStream();
    });

    // Capture photo frame from registration webcam
    document.getElementById('btn-capture-frame')?.addEventListener('click', () => {
        const video = document.getElementById('registration-webcam');
        const canvas = document.getElementById('registration-canvas');
        if (!video || !webcamStream) return;

        canvas.width = video.videoWidth || 640;
        canvas.height = video.videoHeight || 480;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

        const dataUrl = canvas.toDataURL('image/jpeg');
        document.getElementById('photo_base64_input').value = dataUrl;
        showToast('Webcam snapshot captured successfully!');
    });

    // Handle Registration Form Submit
    form?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const submitBtn = document.getElementById('btn-submit-register');
        submitBtn.disabled = true;
        submitBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Extracting Face Encodings...`;

        try {
            const formData = new FormData(form);
            const fileInput = document.getElementById('student-photo-file');
            if (fileInput && fileInput.files[0]) {
                formData.append('photo', fileInput.files[0]);
            }

            const res = await fetch('/api/students', {
                method: 'POST',
                body: formData
            });

            const data = await res.json();
            if (res.ok) {
                showToast(`Success: ${data.message}`);
                closeModal();
                fetchStudents();
                fetchDashboardStats();
            } else {
                alert(`Registration Error: ${data.detail || 'Failed to register student'}`);
            }
        } catch (err) {
            console.error('Registration error:', err);
            alert('An unexpected error occurred during student registration.');
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = `<i class="fa-solid fa-check"></i> Register Student & Extract Face Encoding`;
        }
    });
}

async function startWebcamStream() {
    const video = document.getElementById('registration-webcam');
    try {
        webcamStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
        video.srcObject = webcamStream;
    } catch (err) {
        console.warn('Could not open registration webcam:', err);
    }
}

function stopWebcamStream() {
    if (webcamStream) {
        webcamStream.getTracks().forEach(track => track.stop());
        webcamStream = null;
    }
}

// Utility debounce helper
function debounce(fn, delay) {
    let timer = null;
    return function (...args) {
        clearTimeout(timer);
        timer = setTimeout(() => fn.apply(this, args), delay);
    };
}

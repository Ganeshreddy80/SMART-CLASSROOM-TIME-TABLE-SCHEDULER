# UniSchedule API Documentation

## Overview

This document describes all REST and HTML endpoints in the UniSchedule system across 10 blueprints (~92 routes total).

---

### Auth (`/`) — `blueprints/auth.py`

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET / POST | `/login` | No | Renders login HTML |
| GET | `/logout` | No | Clears session and redirects |
| GET | `/forgot-password` | No | Forgot password page |
| POST | `/api/forgot-password` | No | Send OTP to email |
| POST | `/api/verify-otp` | No | Verify 6-digit OTP |
| POST | `/api/reset-password` | No | Reset password with token |

**Example Request — Send OTP:**
```bash
curl -X POST http://localhost:5000/api/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"email": "user@srmap.edu.in"}'
```
**Response:**
```json
{"message": "OTP sent to your email. Check your inbox."}
```

---

### Admin (`/`) — `blueprints/admin.py`

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/admin/dashboard` | admin | Dashboard HTML |
| POST | `/api/schedule` | admin | Run timetable generator |

---

### API (`/`) — `blueprints/api.py`

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/dashboard` | login | Dashboard data |
| GET | `/university` | login | University details |
| POST | `/university` | admin | Update university |
| GET | `/departments` | login | List departments |
| POST | `/departments` | admin | Create department |
| PUT | `/departments/<id>` | admin | Update department |
| DELETE | `/departments/<id>` | admin | Delete department |
| GET | `/courses` | login | List courses |
| POST | `/courses` | admin | Create course |
| PUT | `/courses/<id>` | admin | Update course |
| DELETE | `/courses/<id>` | admin | Delete course |
| GET | `/faculty` | login | List faculty |
| POST | `/faculty` | admin | Create faculty |
| PUT | `/faculty/<id>` | admin | Update faculty |
| DELETE | `/faculty/<id>` | admin | Delete faculty |
| POST | `/faculty/<id>/photo` | admin | Upload faculty photo |
| GET | `/students` | login | List students |
| POST | `/students` | admin | Create student |
| PUT | `/students/<id>` | admin | Update student |
| POST | `/students/<id>/photo` | admin | Upload student photo |
| DELETE | `/students/<id>` | admin | Delete student |
| POST | `/sections/generate` | admin | Generate sections |
| GET | `/sections` | login | List sections |
| GET | `/classrooms` | login | List classrooms |
| POST | `/timetable/generate` | admin | Generate timetable |
| GET | `/timetable/section/<id>` | login | Section timetable |
| GET | `/timetable/faculty/<id>` | login | Faculty timetable |
| GET | `/timetable/student/<id>` | login | Student timetable |
| GET | `/attendance/student/<id>` | login | Student attendance |
| GET | `/attendance/low` | login | Low attendance list |
| POST | `/attendance/mark` | login | Mark attendance |
| GET | `/timetable/rooms` | login | Room list |
| GET | `/timetable/all` | login | Full timetable |
| GET | `/room-utilization` | admin | Utilization stats |
| GET | `/suggest-room` | login | Suggest available room |
| PUT | `/timetable/entry/<id>` | admin | Update entry |
| GET | `/attendance/trend/<id>` | login | Attendance trend |
| GET | `/attendance/stats` | login | Attendance stats |
| POST | `/chat` | login | AI chat (cached) |
| GET | `/faculty/absences` | login | Faculty absences |
| POST | `/admin/add-student` | admin | Add student |
| POST | `/faculty/report-absence` | faculty | Report absence |

**Example Request — AI Chat:**
```bash
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Show me faculty workload", "history": []}'
```
**Response:**
```json
{"response": "...AI-generated response..."}
```

---

### Faculty (`/`) — `blueprints/faculty.py`

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/faculty-app` | faculty | Dashboard HTML |
| GET | `/timetable/faculty` | faculty | Timetable HTML |
| GET | `/faculty/api/attendance` | faculty | Attendance data |
| GET | `/api/faculty-absences` | faculty | Absence records |
| GET | `/faculty/attendance-management` | faculty | Management UI |
| GET | `/api/faculty/performance-insights` | faculty | Performance analytics |

---

### Student (`/`) — `blueprints/student.py`

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/student-app` | student | Dashboard HTML |
| GET | `/timetable/student` | student | Timetable HTML |
| GET | `/attendance/student` | student | Attendance HTML |
| GET | `/student/logout` | student | Logout |
| POST | `/student/upload-photo` | student | Upload photo |
| GET | `/student/api/profile` | student | Student profile |
| GET | `/student/api/courses` | student | Enrolled courses |
| GET | `/student/api/timetable` | student | Timetable JSON |
| GET | `/student/api/attendance` | student | Attendance JSON |
| GET | `/student/api/today-attendance` | student | Today's attendance |
| GET | `/student/api/marks` | student | Academic marks |
| GET | `/student/api/faculty-absence` | student | Faculty absence updates |
| GET | `/api/student/attendance-risk` | student | Attendance risk analysis |

---

### Attendance (`/`) — `blueprints/attendance.py`

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/attendance/setup-data` | faculty | Section/student list |
| POST | `/api/attendance/session/start` | faculty | Start QR session |
| GET | `/api/attendance/session/qr/<token>` | No | Get QR code |
| GET | `/api/attendance/session/live/<token>` | faculty | Live session status |
| POST | `/api/attendance/session/stop` | faculty | Stop session |
| POST | `/api/attendance/manual-save` | faculty | Save manual attendance |
| POST | `/api/attendance/manual` | faculty | Manual attendance entry |
| PUT | `/api/attendance/update-student` | faculty | Update student status |
| GET | `/api/attendance/students-in-section` | faculty | Student list |
| GET | `/api/attendance/get-roll` | faculty | Roll number lookup |
| GET | `/api/attendance/active-session` | faculty | Check active session |
| POST | `/api/attendance/submit` | student | Student QR check-in |
| POST | `/api/attendance/verify-face` | student | Face verification |
| GET | `/attendance/faculty-qr` | faculty | QR page HTML |
| GET | `/attendance/student-scan` | student | Scan page HTML |

---

### Complaints (`/`) — `blueprints/complaints.py`

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/complaints` | login | Complaints page |
| POST | `/api/complaints` | login | Create complaint |
| GET | `/api/complaints` | login | List complaints |
| PUT | `/api/complaints/<id>/status` | admin | Update status |
| GET | `/api/complaints/stats` | login | Statistics |
| POST | `/api/complaints/analyze` | login | NLP analysis |
| GET | `/api/complaints/<id>/suggest-reply` | admin | AI reply suggestion |

---

### Anomalies (`/`) — `blueprints/anomalies.py`

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/anomalies` | admin | Detect anomalies |
| GET | `/api/anomalies/stats` | admin | Anomaly statistics |
| GET | `/anomalies` | admin | Dashboard HTML |
| PUT | `/api/anomalies/<id>/dismiss` | admin | Dismiss anomaly |
| PUT | `/api/anomalies/<id>/confirm` | admin | Confirm anomaly |

---

### Chatbots (`/`) — `blueprints/chatbot_*.py`

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/admin` | admin | Admin chatbot |
| POST | `/faculty` | faculty | Faculty chatbot |
| POST | `/student` | student | Student chatbot |

---

## Response Formats

All JSON responses follow:
```json
{
  "message": "Success",
  "data": {}
}
```

or on error:
```json
{
  "error": "Description"
}
```

## Authentication

Session-based cookies. Send `Content-Type: application/json` for API routes and include the `X-CSRFToken` header for state-changing requests (managed automatically by frontend for CSRF-exempt API routes).
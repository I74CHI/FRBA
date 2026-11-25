# VisionAttend: Technical Project Report Dossier

## Scope and Verification Basis

This report is based only on the repository files and SQLite database present in:

`C:\Users\I7ACHI\STUDY\Python_Project\PROJECTS\FRBA`

Verified observations:

- Database initialization completed successfully.
- The SQLite database contains `students` and `attendance_logs`.
- The database currently contains 0 student records and 0 attendance records.
- The dashboard API returned HTTP 200 with empty-state values.
- No project test suite or test scripts were found.
- Scikit-learn is imported dynamically but is not declared in `requirements.txt`.

---

# 1. PROJECT METADATA & OVERVIEW

## Project title

**VisionAttend – Smart Face Recognition Attendance System**

The HTML title is:

**Smart Face Recognition Attendance System | College Project**

## Repository name

**FRBA**

## Core problem statement

The system automates student attendance by:

1. Detecting faces in a webcam stream or uploaded image.
2. Converting a detected face into a 128-dimensional facial feature vector.
3. Comparing the vector with registered student encodings.
4. Creating or updating an attendance record.
5. Showing attendance statistics and exporting attendance reports.

## High-level end-to-end summary

1. FastAPI serves the web interface from `/`.
2. An operator registers a student by file upload or webcam snapshot.
3. The server saves the selected image under `static/uploads/`.
4. `face_recognition` extracts one 128-dimensional face encoding.
5. The encoding is stored as a JSON array in SQLite.
6. The encoding is loaded into an in-memory face recognition cache.
7. The browser sends webcam frames to `/api/process_frame`, or the server captures frames for `/api/video_feed`.
8. The face engine detects faces and performs recognition.
9. A matched student receives a daily attendance record.
10. The dashboard, directory, and reports retrieve records through FastAPI APIs.
11. Reports can be downloaded as CSV or XLSX.

## Primary objectives

- Register student profiles with facial feature data.
- Recognize faces in real time or through captured frames.
- Mark attendance automatically.
- Apply a five-minute in-memory recognition cooldown.
- Prevent duplicate attendance creation for the same student on the same date.
- Display attendance totals and department distribution.
- Search and filter students and attendance records.
- Export reports.
- Demonstrate operation without a physical webcam through a synthetic simulation mode.

## Target users and roles

The repository has no authentication or role system.

| Role suggested by the UI | Implemented role behavior |
|---|---|
| Attendance operator | Uses the kiosk and dashboard without a login |
| Student administrator | Registers and deletes students without a login |
| Report administrator | Views, deletes, and clears attendance without a login |
| Student | Stored as a database subject only; no student login exists |
| Administrator account | Not implemented |
| General authenticated user | Not implemented |

---

# 2. COMPLETE DIRECTORY & ARCHITECTURE OVERVIEW

## Directory tree

```text
FRBA/
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── face_engine.py
│   │   └── ml_model.py
│   └── db/
│       ├── database.py
│       ├── models.py
│       └── seed.py
├── data/
│   └── attendance.db
├── static/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── app.js
│   └── uploads/
│       ├── TEST_2026_999_1786200458.jpg
│       ├── 2300901530001_1786200932.jpg
│       ├── 2300901530001_1786200163.jpg
│       └── 2300901530002_1786200621.jpg
├── templates/
│   └── index.html
├── README.md
├── requirements.txt
└── run.py
```

Excluded from the source tree are `__pycache__`, virtual environments, `.git`, and generated build artifacts.

## System architecture

```text
+----------------------------------------------------------+
|                         Browser                          |
|                                                          |
|  index.html                                              |
|  - Dashboard                                             |
|  - Live Kiosk                                            |
|  - Student Directory                                     |
|  - Reports                                               |
|                                                          |
|  app.js                                                  |
|  - Navigation and theme                                  |
|  - Fetch API calls                                       |
|  - Browser webcam capture                                |
|  - Canvas frame conversion                               |
+------------------------------+---------------------------+
                               |
                 HTTP / multipart / MJPEG
                               |
+------------------------------v---------------------------+
|                    FastAPI Backend                       |
|                         app/main.py                      |
|                                                          |
|  Routes, form parsing, database dependency injection,   |
|  JSON responses, CSV export, XLSX export                |
+------------------------------+---------------------------+
                               |
       +-----------------------+-----------------------+
       |                                               |
       v                                               v
+-----------------------------+         +--------------------------------+
| Face / ML Processing        |         | SQLite through SQLAlchemy      |
|                             |         |                                |
| face_engine.py              |         | students                       |
| - face detection            |         | attendance_logs                |
| - 128D encoding extraction  |         |                                |
| - frame annotation          |         | face encoding stored as JSON   |
| - recognition cache         |         |                                |
| - attendance cooldown       |         |                                |
|                             |         +----------------+---------------+
| ml_model.py                 |                          |
| - KNN classifier            |                          |
| - Euclidean fallback        |                          |
| - pickle checkpoint         |                          |
+-------------+---------------+                          |
              |                                          |
              v                                          v
+----------------------------------------------------------+
|                       Storage                            |
|                                                          |
| data/attendance.db                                       |
| static/uploads/<student-photo>.jpg                       |
| data/face_classifier.pkl when model training occurs      |
+----------------------------------------------------------+
```

The `data/face_classifier.pkl` file is referenced by the source but was not present at extraction time.

---

# 3. TECH STACK, LIBRARIES & DEPENDENCIES

## Python and backend

| Technology | Declared version | Specific role |
|---|---:|---|
| Python | README: 3.10+ | Application runtime |
| FastAPI | `>=0.110.0` | REST API, HTML response, form handling |
| Uvicorn | `>=0.28.0` | ASGI server |
| Jinja2 | `>=3.1.0` | Template dependency; `/` reads the HTML file directly |
| python-multipart | `>=0.0.9` | Multipart forms and uploads |

## Database

| Technology | Declared version | Specific role |
|---|---:|---|
| SQLAlchemy | `>=2.0.0` | ORM, database sessions, relationships |
| SQLite | Built into Python | Persistent database |

Database URL:

```text
sqlite:///C:\Users\I7ACHI\STUDY\Python_Project\PROJECTS\FRBA\data\attendance.db
```

## Face recognition and image processing

| Technology | Declared version | Specific role |
|---|---:|---|
| `face-recognition` | `>=1.3.0` | Face locations and 128D encodings |
| `opencv-python` | `>=4.8.0` | Camera capture, decoding, resizing, drawing, JPEG encoding |
| NumPy | `>=1.24.0` | Arrays and Euclidean vector operations |
| Pillow | `>=10.0.0` | Declared dependency; no direct import found |
| dlib | Not separately listed | Underlying face-recognition dependency |

## Machine learning

| Technology | Declared version | Specific role |
|---|---:|---|
| scikit-learn | Not listed | Dynamically imports `KNeighborsClassifier` |
| NumPy | `>=1.24.0` | Fallback 1-nearest-neighbor matcher |

Classifier configuration:

- Model: `KNeighborsClassifier`
- Number of neighbors: 1
- Weighting: `distance`
- Metric: Euclidean
- Input: 128 values
- Output: student ID

## Reporting

| Technology | Declared version | Specific role |
|---|---:|---|
| pandas | `>=2.0.0` | Converts attendance dictionaries to tables |
| openpyxl | `>=3.1.0` | Creates XLSX files |

## Frontend

| Technology | Exact configuration | Specific role |
|---|---|---|
| HTML5 | `templates/index.html` | Single-page UI |
| Vanilla JavaScript | `static/js/app.js` | Navigation, API calls, camera handling |
| CSS3 | `static/css/style.css` | Responsive neobrutalist UI |
| Google Fonts | External CDN | Space Grotesk, Outfit, JetBrains Mono |
| Font Awesome | 6.5.1 CDN | Icons |
| Web Audio API | Browser API | Verification chime |
| `getUserMedia` | Browser API | Browser webcam access |
| HTML Canvas | Browser API | Frame capture and JPEG conversion |
| `localStorage` | Browser API | Theme preference |

No `package.json`, Node package manager, or frontend build pipeline is present.

---

# 4. DATABASE SCHEMA & DATA MODELS

## Database files

| File | Purpose |
|---|---|
| `data/attendance.db` | SQLite data |
| `app/db/database.py` | Engine, session factory, table creation |
| `app/db/models.py` | ORM entities |
| `app/db/seed.py` | Initialization and face-cache loading |

## Table: `students`

Model: `Student`

| Column | Type | Constraints and default |
|---|---|---|
| `id` | INTEGER | Primary key, indexed |
| `roll_no` | VARCHAR(50) | Not null, unique, indexed |
| `name` | VARCHAR(100) | Not null |
| `department` | VARCHAR(100) | Not null |
| `year` | VARCHAR(20) | Not null, default `3rd Year` |
| `email` | VARCHAR(100) | Nullable |
| `photo_path` | VARCHAR(255) | Nullable |
| `face_encoding` | TEXT | Nullable; JSON list of 128 floats |
| `is_active` | BOOLEAN | Default `True` |
| `created_at` | DATETIME | Default `datetime.now()` |

Relationships:

- `attendance_records` has relationship to `AttendanceLog`.
- Cascade is `all, delete-orphan`.
- `id` and `roll_no` are indexed.

## Table: `attendance_logs`

Model: `AttendanceLog`

| Column | Type | Constraints and default |
|---|---|---|
| `id` | INTEGER | Primary key, indexed |
| `student_id` | INTEGER | Foreign key to `students.id`, not null |
| `date` | DATE | Not null, indexed, default `date.today` |
| `time` | VARCHAR(20) | Not null |
| `timestamp` | DATETIME | Default `datetime.now()` |
| `status` | VARCHAR(20) | Default `Present` |
| `confidence` | FLOAT | Default `0.0` |
| `method` | VARCHAR(30) | Default `Face Recognition` |

Relationships:

- `student` is linked back to `Student.attendance_records`.
- No SQLite foreign-key enforcement is explicitly enabled.
- The schema has no unique `(student_id, date)` constraint; duplicate prevention is application-level.

## Dataset information

No external training/testing dataset is included.

Verified database state:

- 0 student rows.
- 0 attendance-log rows.
- Five sample student definitions exist in `SAMPLE_STUDENTS`, but `seed_database()` does not insert them.
- No attendance records are seeded.
- No train/validation/test split exists.
- ML training uses all valid active-student encodings currently in SQLite.

## Uploaded image artifacts

The repository contains four image files under `static/uploads/`.

No database record association or verified face encoding was established for these files during seed operations.

---

# 5. MODULE-BY-MODULE IMPLEMENTATION DETAILS

## A. Application startup

Files:

- `run.py`
- `app/main.py`

Behavior:

1. `python run.py --test-db` initializes and seeds the database.
2. Normal startup invokes Uvicorn with `app.main:app`.
3. The host is `127.0.0.1`.
4. The port is `8000`.
5. A background thread opens the browser after 1.5 seconds.
6. FastAPI startup creates tables and calls `seed_database()`.
7. `seed_database()` loads encodings and retrains ML.

## B. Database module

`app/db/database.py`:

- Creates `data/` if absent.
- Creates the SQLite engine.
- Enables `check_same_thread=False`.
- Defines `SessionLocal`.
- Provides `get_db()` for dependency injection.
- Calls `Base.metadata.create_all()` during initialization.

## C. Face engine

`app/core/face_engine.py`:

- Resizes frames to 25%.
- Converts frames from BGR to RGB.
- Detects face locations.
- Extracts face encodings.
- Matches against the ML classifier.
- Falls back to direct `face_recognition.face_distance`.
- Uses a match threshold of 0.50.
- Applies a 300-second per-student cooldown.
- Annotates frames with bounding boxes and labels.
- Uses green for recognized faces and amber for unknown faces.

Encoding extraction accepts:

- Filesystem paths.
- Raw image bytes.
- NumPy arrays.

It returns the first 128-element encoding or `None`.

Recognition confidence:

```text
confidence = max(0, (1 - Euclidean distance) × 100)
```

## D. Attendance logic

`_record_attendance()`:

1. Retrieves today's date.
2. Searches for an existing log for the student and date.
3. Creates a `Present` record if absent.
4. Updates the existing record's time and confidence if present.
5. Commits the SQLAlchemy transaction.

Attendance entries use:

- Status: `Present`
- Confidence: recognition percentage
- Method: face recognition or manual check-in

No check-out or non-present workflow is implemented.

## E. ML classifier

`app/core/ml_model.py`:

- Collects all active 128D encodings.
- Uses student IDs as targets.
- Initializes a 1-NN Euclidean classifier.
- Calculates in-sample training accuracy by predicting against training data.
- Saves a pickle checkpoint to `data/face_classifier.pkl`.
- Falls back to NumPy distance matching if scikit-learn is unavailable.

Training accuracy is resubstitution accuracy, not held-out test accuracy.

The ML module provides `load_model()`, but startup code does not call it automatically.

## F. API endpoints

No route implements authentication or authorization middleware.

| Method | Route | Request | Response |
|---|---|---|---|
| GET | `/` | None | HTML SPA |
| GET | `/api/video_feed` | None | MJPEG stream |
| POST | `/api/process_frame` | Multipart `photo_base64` | JSON success, annotated frame, events |
| GET | `/api/recognition/latest-event` | None | `{ "event": ... }`; event is cleared after retrieval |
| GET | `/api/ml/status` | None | Model type and training state |
| POST | `/api/ml/train` | No body | Training metrics |
| GET | `/api/dashboard/stats` | None | Dashboard metrics and recent logs |
| GET | `/api/students` | Optional `search`, `department` | Student list |
| POST | `/api/students` | Name, roll, department, year, email, photo | Registered student |
| DELETE | `/api/students/{student_id}` | `student_id` path value | Success message |
| GET | `/api/attendance/logs` | Optional date, department, search | Attendance list |
| DELETE | `/api/attendance/logs/{log_id}` | `log_id` path value | Success message |
| DELETE | `/api/attendance/logs` | Optional `filter_date` | Deleted count |
| POST | `/api/attendance/manual` | Form `student_id`, optional `status` | Attendance log |
| GET | `/api/reports/export/csv` | Optional `filter_date` | CSV download |
| GET | `/api/reports/export/excel` | Optional `filter_date` | XLSX download |

### Dashboard calculations

- Total students: all active students.
- Present today: records with today's date and `Present`.
- Absent today: `max(0, total students - present today)`.
- Attendance rate: present divided by total × 100.

The absent count assumes every active student without a present row is absent.

### Student registration

- Requires name and roll number.
- Requires department and photo.
- Rejects duplicate roll numbers for active students.
- Deletes inactive duplicate records before reusing a roll number.
- Stores uploaded/captured images under `static/uploads/`.
- Allows registration even when no face is detected.
- Reloads in-memory encodings after registration.
- Retrains ML after registration.

### Manual attendance

The route accepts `status`, but `_record_attendance()` ignores it and marks the record `Present`.

## G. Camera modes

### Browser mode

- Calls `navigator.mediaDevices.getUserMedia`.
- Requests ideal 640×480 video.
- Captures frames every 180 ms.
- Converts frames to JPEG data URLs.
- Sends frames to `/api/process_frame`.

### Server mode

- Attempts DirectShow capture on Windows.
- Falls back to default OpenCV capture.
- Processes real frames.
- Falls back to simulation after unavailable initialization or repeated read failure.

### Simulation mode

This is explicitly simulated:

- Generates synthetic 640×480 frames.
- Animates a scanning rectangle.
- Displays a demonstration-camera label.
- Does not detect or recognize faces.
- Does not mark attendance.

## H. Seed module

`seed_database()`:

- Creates database tables.
- Loads active student encodings.
- Retrains ML.

It does not insert `SAMPLE_STUDENTS`.

`create_avatar_image()` exists but is not called by seed logic.

## I. Frontend modules

The UI consists of:

- Light/dark theme toggle.
- Live clock.
- Tab navigation.
- Dashboard refresh every 10 seconds.
- ML status refresh.
- Browser and server camera modes.
- Event polling every 1.5 seconds in server mode.
- Student search with 300 ms debounce.
- Department filtering.
- Registration modal.
- CSV/XLSX export.
- Toast notifications.
- Web Audio success chime.

---

# 6. ENVIRONMENT VARIABLES & SECURITY CONFIGURATION

## Environment variables

No environment-variable file or template was found.

No references were found to:

- `process.env`
- `os.environ`
- `dotenv`
- `.env`
- Secret keys
- Password settings
- JWT settings
- Database URL variables
- CORS variables

## Hardcoded configuration

| Setting | Value |
|---|---|
| Host | `127.0.0.1` |
| Port | `8000` |
| Database | `data/attendance.db` |
| Upload directory | `static/uploads` |
| Face match threshold | `0.50` |
| Recognition cooldown | `300` seconds |
| ML checkpoint | `data/face_classifier.pkl` |
| Browser frame interval | `180` ms |
| Dashboard refresh | `10,000` ms |
| Event polling | `1,500` ms |

## Authentication and authorization

Not implemented:

- Login
- User table
- Password hashing
- Session management
- JWT or bearer tokens
- Cookies
- Role checks
- Protected route dependencies
- CSRF protection

## Input and network security

Implemented:

- Required FastAPI form fields.
- HTML required attributes.
- Student existence checks.
- Duplicate roll-number checks.
- Date parsing with invalid-date handling.
- Encoding-length validation.
- Frame decode validation.

Not implemented:

- Authentication and authorization.
- Upload MIME validation.
- Upload size limits.
- Email backend validation.
- Filename sanitization library.
- CORS configuration.
- API rate limiting.
- HTTPS configuration.

## Potential frontend risk

Several student and attendance values are inserted through `innerHTML` in `static/js/app.js`. Data is not explicitly HTML-escaped. If the backend is exposed to untrusted input, stored or reflected HTML could create an XSS risk.

---

# 7. UI PAGES, ROUTES & SCREENSHOT CHECKLIST

## UI route summary

There is only one web route:

| Frontend route | User role | Components |
|---|---|---|
| `/` | None | SPA shell, navigation, tabs, modal |

Dashboard, kiosk, students, and reports are client-side tab sections rather than separate URLs.

## Views

| View | URL | Role | Components |
|---|---|---|---|
| Dashboard | `/`, `tab-dashboard` | None | Four metrics, activity feed, department distribution, ML status |
| Live Kiosk | `/`, `tab-kiosk` | None | Camera controls, recognized video, verification feed |
| Student Directory | `/`, `tab-students` | None | Search, department filter, student cards |
| Reports | `/`, `tab-reports` | None | Date filter, department filter, table, exports |
| Registration Modal | Overlay at `/` | None | Student fields and photo options |

## Screenshot checklist

1. Startup page and address bar.
2. Dashboard in light mode.
3. Dashboard in dark mode.
4. Total-student metric card.
5. Present-today metric card.
6. Absent-today metric card.
7. Attendance-rate metric card.
8. Recent activity feed.
9. Department-distribution panel.
10. ML model status.
11. Re-training button interaction.
12. Live kiosk browser-webcam mode.
13. Camera permission prompt.
14. Live recognized face overlay.
15. Unknown-face overlay.
16. Verification feed.
17. Success toast and visual feedback.
18. Server-stream mode.
19. Simulation-stream fallback.
20. Quick demo attendance log.
21. Empty student directory.
22. Registration modal.
23. File-upload registration mode.
24. Webcam registration mode.
25. Webcam frame capture.
26. Newly registered student card.
27. Student search result.
28. Department-filtered student list.
29. Student deletion confirmation.
30. Empty reports view.
31. Attendance report table.
32. Date-filtered reports.
33. Department-filtered reports.
34. CSV download.
35. XLSX download.
36. Individual record deletion.
37. Clear-attendance confirmation.

---

# 8. TESTING, RESULTS, LIMITATIONS & FUTURE SCOPE

## Testing

No test suite or test scripts were found.

Missing test coverage includes:

- Unit tests.
- API tests.
- Database tests.
- Face recognition tests.
- ML tests.
- Frontend tests.
- Browser end-to-end tests.
- CI configuration.

`python run.py --test-db` initializes the database and loads face encodings. It is a startup check, not an assertion-based test suite.

## Metrics and outputs

| Metric | Implementation |
|---|---|
| Recognition confidence | `(1 - distance) × 100` |
| Match threshold | Distance `<= 0.50` |
| ML training accuracy | In-sample prediction accuracy |
| Attendance rate | Present / active students × 100 |
| Total samples | Valid 128D encodings |

No independent accuracy report, confusion matrix, precision, recall, F1, PSNR, SSIM, or latency benchmark is present.

The README's sub-50 ms matching statement is not supported by repository benchmarks.

## Current limitations

### Seed and database

- Sample student definitions are not inserted.
- Four uploaded image artifacts are not linked to database records.
- No migration framework is included.

### Recognition

- Requires clear face photographs.
- Stores only the first detected face at registration.
- No liveness or anti-spoofing.
- No pose or lighting validation.
- No external recognition benchmark.

### ML

- Scikit-learn is undeclared.
- Accuracy is in-sample.
- No dataset split.
- One encoding is normally stored per student.
- Checkpoint loading is not automatic.

### Attendance

- No check-out workflow.
- No leave or absence workflow.
- Manual attendance ignores submitted status.
- Existing daily logs are updated instead of creating repeated records.

### Security

- No authentication.
- No roles.
- No authorization.
- No HTTPS setup.
- No upload limits or MIME validation.
- No CSRF or rate limiting.

### UI

- Internal views have no separate URLs.
- No pagination.
- No server-side sorting.
- No role-specific UI.

## Mocked or bypassed features

| Feature | State |
|---|---|
| Sample students | Mocked/unused seed definitions |
| Synthetic avatars | Function exists but is not called |
| Webcam simulation | Explicit synthetic stream |
| Browser webcam | Implemented |
| Server webcam | Implemented with simulation fallback |
| ML classifier | Implemented with NumPy fallback |
| Training accuracy | In-sample result, not independent validation |
| Authentication | Not implemented |
| Manual attendance | Implemented as forced-present |
| Absent count | Calculated as student minus present count |
| Sub-50 ms claim | README-only claim |

## Future scope

- Add authentication and separate roles.
- Hash passwords and secure sessions or tokens.
- Add CSRF protection and rate limiting.
- Add upload limits and MIME validation.
- Store multiple face encodings per student.
- Add liveness and anti-spoofing detection.
- Add held-out recognition testing.
- Add precision, recall, F1, and confusion-matrix reporting.
- Add check-in/check-out events.
- Add leave and timetable workflows.
- Make seed initialization explicit and configurable.
- Add database migrations.
- Load the model checkpoint automatically.
- Add API and browser end-to-end tests.
- Add pagination and server-side sorting.
- Add environment-based configuration.
- Add Docker support.
- Clearly separate demonstration and production camera modes.

---

# 9. OFFICIAL REFERENCES

1. FastAPI Documentation. https://fastapi.tiangolo.com/
2. Uvicorn Documentation. https://www.uvicorn.org/
3. SQLAlchemy Documentation. https://docs.sqlalchemy.org/en/20/
4. SQLite Documentation. https://www.sqlite.org/docs.html
5. face_recognition Project. https://github.com/ageitgey/face_recognition
6. Dlib C++ Library. http://dlib.net/
7. OpenCV Documentation. https://docs.opencv.org/
8. NumPy Documentation. https://numpy.org/doc/
9. scikit-learn Documentation. https://scikit-learn.org/stable/
10. `KNeighborsClassifier` API Reference. https://scikit-learn.org/stable/modules/generated/sklearn.neighbors.KNeighborsClassifier.html
11. pandas Documentation. https://pandas.pydata.org/docs/
12. openpyxl Documentation. https://openpyxl.readthedocs.io/
13. Pillow Documentation. https://pillow.readthedocs.io/
14. Jinja Documentation. https://jinja.palletsprojects.com/
15. python-multipart Project. https://github.com/Kludex/python-multipart
16. MDN: `MediaDevices.getUserMedia()`. https://developer.mozilla.org/docs/Web/API/MediaDevices/getUserMedia
17. MDN: Canvas API. https://developer.mozilla.org/docs/Web/API/Canvas_API
18. MDN: Web Audio API. https://developer.mozilla.org/docs/Web/API/Web_Audio_API
19. Google Fonts: Space Grotesk. https://fonts.google.com/specimen/Space+Grotesk
20. Google Fonts: Outfit. https://fonts.google.com/specimen/Outfit
21. Google Fonts: JetBrains Mono. https://fonts.google.com/specimen/JetBrains+Mono
22. Font Awesome 6 Documentation. https://docs.fontawesome.com/

# VisionAttend - Face Recognition Attendance System 🎓

An intermediate-level, presentation-ready **Face Recognition Attendance System** designed for college project presentations. Powered by **Python FastAPI**, **OpenCV**, **dlib face_recognition**, **SQLite**, and a modern **Glassmorphism Web UI**.

![Version](https://img.shields.io/badge/Version-1.0.0-brightgreen.svg)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)
![Framework](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)

---

## ✨ Features

- 📷 **Live Face Recognition Kiosk**: Real-time webcam video stream with face bounding box, student details, and confidence percentage.
- ⚡ **Sub-50ms Vector Matching**: 128-dimensional face embedding extraction and RAM vector cache for instant recognition.
- 📊 **Interactive Dashboard**: Real-time analytics cards, department-wise attendance distribution, and recent activity logs.
- 👥 **Student Directory & Registration**: Add new student profiles via photo upload or live webcam snapshot with automatic face feature extraction.
- 📋 **Reports & One-Click Export**: Filter attendance logs by date and department, with direct **Export to Excel (`.xlsx`)** and **CSV**.
- 🔔 **Audio & Visual Feedback**: Web Audio API synthesized verification chime and toast notifications upon check-in.
- 🎓 **Presentation Mode**: Includes simulation fallback and pre-seeded student data so your project demo runs smoothly even without physical camera hardware.

---

## 🚀 Quick Start Instructions

### 1. Requirements Check
The project requires Python 3.10+ and standard packages:
```bash
pip install -r requirements.txt
```

### 2. Run the Application
Start the system with a single command:
```bash
python run.py
```
This will start the FastAPI backend server on `http://127.0.0.1:8000` and automatically open your default browser.

---

## 📁 Project Structure

```
FRBA/
├── app/
│   ├── main.py            # FastAPI Application & REST APIs
│   ├── core/
│   │   └── face_engine.py # Face Recognition Engine (OpenCV + face_recognition)
│   └── db/
│       ├── database.py    # SQLite engine & Session configuration
│       ├── models.py      # SQLAlchemy ORM Data Models
│       └── seed.py        # Demo data & student profiles seeder
├── templates/
│   └── index.html         # Modern SPA Web Interface
├── static/
│   ├── css/
│   │   └── style.css      # Custom Dark Theme Glassmorphism Design System
│   └── js/
│       └── app.js         # Frontend interactive logic & Web Audio API
├── run.py                 # One-click startup script
├── PRESENTATION_GUIDE.md  # Comprehensive College Presentation & Viva Cheat Sheet
├── requirements.txt       # Project Dependencies
└── README.md              # Project Documentation
```

---

## 📖 Presentation Guide
Refer to [PRESENTATION_GUIDE.md](file:///c:/Users/I7ACHI/STUDY/Python_Project/PROJECTS/FRBA/PRESENTATION_GUIDE.md) for:
- 30-second elevator pitch for evaluators
- Architectural & mathematical breakdown of 128D embeddings
- Step-by-step live demonstration script
- Sample viva questions and answers

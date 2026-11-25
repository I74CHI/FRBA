import os
import json
import numpy as np
import cv2
from datetime import datetime, date, timedelta
from app.db.database import SessionLocal, init_db
from app.db.models import Student, AttendanceLog
from app.core.face_engine import face_engine

STATIC_UPLOADS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "static", "uploads")
os.makedirs(STATIC_UPLOADS, exist_ok=True)

SAMPLE_STUDENTS = [
    {
        "roll_no": "CS-2024-001",
        "name": "Alex Morgan",
        "department": "Computer Science",
        "year": "3rd Year",
        "email": "alex.m@college.edu",
    },
    {
        "roll_no": "CS-2024-002",
        "name": "Sarah Connor",
        "department": "Computer Science",
        "year": "3rd Year",
        "email": "sarah.c@college.edu",
    },
    {
        "roll_no": "AI-2024-015",
        "name": "David Miller",
        "department": "Artificial Intelligence",
        "year": "4th Year",
        "email": "david.m@college.edu",
    },
    {
        "roll_no": "EC-2024-042",
        "name": "Emily Watson",
        "department": "Electronics & Comm.",
        "year": "2nd Year",
        "email": "emily.w@college.edu",
    },
    {
        "roll_no": "IT-2024-088",
        "name": "Rohan Gupta",
        "department": "Information Tech",
        "year": "3rd Year",
        "email": "rohan.g@college.edu",
    }
]

def create_avatar_image(name: str, filename: str) -> str:
    """Create a clean colored avatar placeholder image for sample student profile."""
    img_path = os.path.join(STATIC_UPLOADS, filename)
    img = np.zeros((300, 300, 3), dtype=np.uint8)
    
    # HSL-like background color derived from name string hash
    bg_color = (
        (hash(name) * 37) % 180 + 40,
        (hash(name) * 59) % 180 + 40,
        (hash(name) * 83) % 180 + 40
    )
    img[:] = bg_color

    # Draw initial circle avatar
    cv2.circle(img, (150, 120), 50, (255, 255, 255), -1)
    cv2.ellipse(img, (150, 240), (80, 60), 0, 0, 180, (255, 255, 255), -1)

    # Initials text
    initials = "".join([part[0].upper() for part in name.split()[:2]])
    cv2.putText(img, initials, (125, 135), cv2.FONT_HERSHEY_SIMPLEX, 1.2, bg_color, 3, cv2.LINE_AA)

    cv2.imwrite(img_path, img)
    return f"/static/uploads/{filename}"

def seed_database():
    init_db()
    db = SessionLocal()
    try:
        print("[Seed] Database initialized. Loading face encodings into cache.")
        face_engine.load_encodings_from_db(db)
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()

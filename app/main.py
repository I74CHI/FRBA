import os
import io
import json
import base64
from datetime import date, datetime
from typing import Optional, List

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import StreamingResponse, Response, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
import pandas as pd

from app.db.database import get_db, SessionLocal, init_db
from app.db.models import Student, AttendanceLog
from app.core.face_engine import face_engine
from app.db.seed import seed_database

# Base directory paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
UPLOADS_DIR = os.path.join(STATIC_DIR, "uploads")

os.makedirs(UPLOADS_DIR, exist_ok=True)

app = FastAPI(
    title="Face Recognition Attendance System",
    description="Intermediate level college presentation project for real-time face recognition attendance management.",
    version="1.0.0"
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

@app.on_event("startup")
def on_startup():
    init_db()
    seed_database()

@app.get("/", response_class=HTMLResponse)
def index_page():
    index_file = os.path.join(TEMPLATES_DIR, "index.html")
    with open(index_file, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/api/video_feed")
def video_feed():
    return StreamingResponse(
        face_engine.generate_camera_stream(SessionLocal),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@app.post("/api/process_frame")
async def process_browser_frame(
    photo_base64: str = Form(...),
    db: Session = Depends(get_db)
):
    result = face_engine.process_base64_frame(photo_base64, db)
    return result

@app.get("/api/recognition/latest-event")
def get_latest_event():
    event = face_engine.latest_recognition_event
    face_engine.latest_recognition_event = None # Reset after reading
    return {"event": event}

@app.get("/api/ml/status")
def get_ml_status():
    from app.core.ml_model import ml_classifier
    return ml_classifier.get_status()

@app.post("/api/ml/train")
def retrain_ml_model(db: Session = Depends(get_db)):
    from app.core.ml_model import ml_classifier
    result = ml_classifier.train_from_db(db)
    return result

@app.get("/api/dashboard/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    today_date = date.today()
    total_students = db.query(Student).filter(Student.is_active == True).count()
    
    present_today = db.query(AttendanceLog).filter(
        AttendanceLog.date == today_date,
        AttendanceLog.status == "Present"
    ).count()

    absent_today = max(0, total_students - present_today)
    attendance_rate = (present_today / total_students * 100) if total_students > 0 else 0.0

    # Department breakdown
    dept_query = db.query(
        Student.department, 
        func.count(Student.id).label("total")
    ).filter(Student.is_active == True).group_by(Student.department).all()

    dept_stats = {dept: count for dept, count in dept_query}

    # Recent 5 attendance logs
    recent_logs_objs = db.query(AttendanceLog).order_by(AttendanceLog.id.desc()).limit(6).all()
    recent_logs = [log.to_dict() for log in recent_logs_objs]

    return {
        "total_students": total_students,
        "present_today": present_today,
        "absent_today": absent_today,
        "attendance_rate": round(attendance_rate, 1),
        "department_stats": dept_stats,
        "recent_logs": recent_logs,
        "today_date": str(today_date)
    }

@app.get("/api/students")
def list_students(
    search: Optional[str] = None,
    department: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Student).filter(Student.is_active == True)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter((Student.name.like(search_pattern)) | (Student.roll_no.like(search_pattern)))
    
    if department and department != "All":
        query = query.filter(Student.department == department)

    students = query.order_by(Student.name.asc()).all()
    return [student.to_dict() for student in students]

@app.post("/api/students")
async def register_student(
    name: str = Form(...),
    roll_no: str = Form(...),
    department: str = Form(...),
    year: str = Form("3rd Year"),
    email: Optional[str] = Form(None),
    photo: Optional[UploadFile] = File(None),
    photo_base64: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    # Check duplicate roll_no (ignore soft-deleted inactive records)
    existing = db.query(Student).filter(Student.roll_no == roll_no).first()
    if existing:
        if not existing.is_active:
            # Purge inactive soft-deleted record so roll_no can be reused
            db.delete(existing)
            db.commit()
        else:
            raise HTTPException(status_code=400, detail=f"Roll Number '{roll_no}' is already registered!")

    image_bytes = None
    filename = f"{roll_no.replace('-', '_').replace('/', '_')}_{int(datetime.now().timestamp())}.jpg"
    file_path = os.path.join(UPLOADS_DIR, filename)
    photo_url = f"/static/uploads/{filename}"

    if photo and photo.filename:
        image_bytes = await photo.read()
        with open(file_path, "wb") as f:
            f.write(image_bytes)
    elif photo_base64 and photo_base64.strip():
        # Base64 camera snap
        if "," in photo_base64:
            photo_base64 = photo_base64.split(",")[1]
        image_bytes = base64.b64decode(photo_base64)
        with open(file_path, "wb") as f:
            f.write(image_bytes)
    else:
        raise HTTPException(status_code=400, detail="Student photo is required (file upload or webcam snapshot).")

    # Extract 128D face encoding vector
    encoding_list = face_engine.extract_encoding_from_image(image_bytes)
    encoding_json = json.dumps(encoding_list) if encoding_list else None

    student = Student(
        roll_no=roll_no,
        name=name,
        department=department,
        year=year,
        email=email,
        photo_path=photo_url,
        face_encoding=encoding_json,
        is_active=True
    )
    db.add(student)
    db.commit()
    db.refresh(student)

    # Reload face encodings in memory cache
    face_engine.load_encodings_from_db(db)

    msg = f"Student '{name}' registered successfully!"
    if not encoding_list:
        msg = f"Student '{name}' registered, but no face was detected in photo. Real-time matching requires a clear face photo."

    return {
        "message": msg,
        "student": student.to_dict(),
        "has_face_encoding": bool(encoding_list)
    }

@app.delete("/api/students/{student_id}")
def delete_student(student_id: int, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")
    
    # Delete uploaded photo file if present
    if student.photo_path:
        rel_path = student.photo_path.lstrip("/")
        if os.path.exists(rel_path):
            try:
                os.remove(rel_path)
            except Exception as e:
                print(f"[DeleteStudent] Photo cleanup error: {e}")

    # Perform hard delete from database so roll_no is completely freed
    db.delete(student)
    db.commit()
    
    # Refresh encodings in memory
    face_engine.load_encodings_from_db(db)
    return {"message": f"Student '{student.name}' removed successfully."}

@app.get("/api/attendance/logs")
def get_attendance_logs(
    filter_date: Optional[str] = None,
    department: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(AttendanceLog).join(Student)
    
    if filter_date:
        try:
            target_date = datetime.strptime(filter_date, "%Y-%m-%d").date()
            query = query.filter(AttendanceLog.date == target_date)
        except ValueError:
            pass

    if department and department != "All":
        query = query.filter(Student.department == department)

    if search:
        search_pattern = f"%{search}%"
        query = query.filter((Student.name.like(search_pattern)) | (Student.roll_no.like(search_pattern)))

    logs = query.order_by(AttendanceLog.id.desc()).all()
    return [log.to_dict() for log in logs]

@app.delete("/api/attendance/logs/{log_id}")
def delete_attendance_log(log_id: int, db: Session = Depends(get_db)):
    log = db.query(AttendanceLog).filter(AttendanceLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Attendance log entry not found.")
    
    db.delete(log)
    db.commit()
    return {"message": f"Attendance log #{log_id} deleted successfully."}

@app.delete("/api/attendance/logs")
def clear_attendance_logs(
    filter_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(AttendanceLog)
    if filter_date:
        try:
            target_date = datetime.strptime(filter_date, "%Y-%m-%d").date()
            query = query.filter(AttendanceLog.date == target_date)
        except ValueError:
            pass

    deleted_count = query.delete(synchronize_session=False)
    db.commit()
    return {"message": f"Cleared {deleted_count} attendance log record(s).", "count": deleted_count}

@app.post("/api/attendance/manual")
def manual_attendance_checkin(
    student_id: int = Form(...),
    status: str = Form("Present"),
    db: Session = Depends(get_db)
):
    student = db.query(Student).filter(Student.id == student_id, Student.is_active == True).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")

    log_dict = face_engine._record_attendance(db, student.id, 100.0, "Manual Check-in")
    return {"message": f"Manual check-in logged for {student.name}", "log": log_dict}

@app.get("/api/reports/export/csv")
def export_csv_report(filter_date: Optional[str] = None, db: Session = Depends(get_db)):
    logs_data = get_attendance_logs(filter_date=filter_date, db=db)
    if not logs_data:
        df = pd.DataFrame(columns=["ID", "Roll No", "Student Name", "Department", "Date", "Time", "Status", "Confidence (%)", "Method"])
    else:
        df = pd.DataFrame(logs_data)
        df = df.rename(columns={
            "id": "Log ID",
            "roll_no": "Roll Number",
            "student_name": "Student Name",
            "department": "Department",
            "date": "Date",
            "time": "Time",
            "status": "Attendance Status",
            "confidence": "Recognition Confidence (%)",
            "method": "Verification Method"
        })

    stream = io.StringIO()
    df.to_csv(stream, index=False)
    response = Response(content=stream.getvalue(), media_type="text/csv")
    filename = f"Attendance_Report_{filter_date or str(date.today())}.csv"
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    return response

@app.get("/api/reports/export/excel")
def export_excel_report(filter_date: Optional[str] = None, db: Session = Depends(get_db)):
    logs_data = get_attendance_logs(filter_date=filter_date, db=db)
    if not logs_data:
        df = pd.DataFrame(columns=["Log ID", "Roll Number", "Student Name", "Department", "Date", "Time", "Status", "Confidence (%)", "Method"])
    else:
        df = pd.DataFrame(logs_data)
        df = df[["id", "roll_no", "student_name", "department", "date", "time", "status", "confidence", "method"]]
        df.columns = ["Log ID", "Roll Number", "Student Name", "Department", "Date", "Time", "Status", "Confidence (%)", "Method"]

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="Attendance Report")
    
    output.seek(0)
    filename = f"Attendance_Report_{filter_date or str(date.today())}.xlsx"
    headers = {'Content-Disposition': f'attachment; filename="{filename}"'}
    return StreamingResponse(output, headers=headers, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

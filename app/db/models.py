from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Float, DateTime, Date, ForeignKey, Boolean, Text
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    roll_no = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    department = Column(String(100), nullable=False)
    year = Column(String(20), nullable=False, default="3rd Year")
    email = Column(String(100), nullable=True)
    photo_path = Column(String(255), nullable=True)
    face_encoding = Column(Text, nullable=True) # Stored as JSON string list of 128 floats
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)

    attendance_records = relationship("AttendanceLog", back_populates="student", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "roll_no": self.roll_no,
            "name": self.name,
            "department": self.department,
            "year": self.year,
            "email": self.email,
            "photo_path": self.photo_path,
            "is_active": self.is_active,
            "has_face_encoding": bool(self.face_encoding),
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None
        }

class AttendanceLog(Base):
    __tablename__ = "attendance_logs"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    date = Column(Date, nullable=False, default=date.today, index=True)
    time = Column(String(20), nullable=False)
    timestamp = Column(DateTime, default=datetime.now)
    status = Column(String(20), default="Present")
    confidence = Column(Float, default=0.0) # Percentage or distance score
    method = Column(String(30), default="Face Recognition") # "Face Recognition" or "Manual"

    student = relationship("Student", back_populates="attendance_records")

    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "student_name": self.student.name if self.student else "Unknown",
            "roll_no": self.student.roll_no if self.student else "N/A",
            "department": self.student.department if self.student else "N/A",
            "date": str(self.date),
            "time": self.time,
            "status": self.status,
            "confidence": round(self.confidence, 1),
            "method": self.method
        }

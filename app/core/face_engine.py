import os
import cv2
import json
import time
import base64
import numpy as np
import face_recognition
from datetime import datetime, date
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session

from app.db.models import Student, AttendanceLog

class FaceEngine:
    def __init__(self):
        self.known_face_encodings: List[np.ndarray] = []
        self.known_student_metadata: List[Dict] = []
        self.last_logged_time: Dict[int, float] = {} # student_id -> timestamp
        self.cooldown_seconds = 300 # 5 minutes default cooldown
        self.tolerance = 0.50 # Lower distance means stricter match
        self.is_camera_running = False
        self.camera = None
        self.latest_recognition_event = None # Temporary event for alert sound/toast

    def load_encodings_from_db(self, db: Session):
        """Load all student face encodings into memory for fast real-time matching."""
        self.known_face_encodings = []
        self.known_student_metadata = []

        students = db.query(Student).filter(Student.is_active == True).all()
        for student in students:
            if student.face_encoding:
                try:
                    encoding_list = json.loads(student.face_encoding)
                    encoding_arr = np.array(encoding_list, dtype=np.float64)
                    self.known_face_encodings.append(encoding_arr)
                    self.known_student_metadata.append({
                        "id": student.id,
                        "name": student.name,
                        "roll_no": student.roll_no,
                        "department": student.department
                    })
                except Exception as e:
                    print(f"[FaceEngine] Error loading encoding for student {student.id}: {e}")

        # Train / re-fit ML Classifier model
        try:
            from app.core.ml_model import ml_classifier
            ml_classifier.train_from_db(db)
        except Exception as e:
            print(f"[FaceEngine] ML model train error: {e}")

        print(f"[FaceEngine] Loaded {len(self.known_face_encodings)} student face encodings into memory.")

    def extract_encoding_from_image(self, image_input) -> Optional[List[float]]:
        """
        Extract 128D encoding vector from image path, bytes, or numpy array.
        Returns list of floats if face detected, else None.
        """
        try:
            if isinstance(image_input, str):
                image = face_recognition.load_image_file(image_input)
            elif isinstance(image_input, bytes):
                nparr = np.frombuffer(image_input, np.uint8)
                img_cv = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                image = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
            elif isinstance(image_input, np.ndarray):
                if len(image_input.shape) == 3 and image_input.shape[2] == 3:
                    image = cv2.cvtColor(image_input, cv2.COLOR_BGR2RGB)
                else:
                    image = image_input
            else:
                return None

            locations = face_recognition.face_locations(image)
            if not locations:
                return None

            encodings = face_recognition.face_encodings(image, known_face_locations=locations)
            if encodings:
                return encodings[0].tolist()
        except Exception as e:
            print(f"[FaceEngine] Extraction error: {e}")
        return None

    def process_frame(self, frame: np.ndarray, db: Session) -> Tuple[np.ndarray, List[Dict]]:
        """
        Process a single OpenCV BGR video frame:
        1. Detect faces & compute encodings.
        2. Match against stored encodings using ML Classifier & metric embeddings.
        3. Record attendance if matched & not in cooldown.
        4. Draw aesthetic bounding boxes and text overlays.
        """
        recognized_events = []
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            # Scale back face locations to original frame size
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4

            name = "Unknown"
            roll_no = "N/A"
            department = "Visitor"
            confidence = 0.0
            matched_student = None

            # Try Machine Learning Classifier prediction first
            try:
                from app.core.ml_model import ml_classifier
                ml_match = ml_classifier.predict(face_encoding.tolist(), max_distance_threshold=self.tolerance)
                if ml_match:
                    matched_student, confidence, _ = ml_match
                    name = matched_student["name"]
                    roll_no = matched_student["roll_no"]
                    department = matched_student["department"]
            except Exception as e:
                matched_student = None

            # Fallback distance matching if ML predictor returned None
            if not matched_student and len(self.known_face_encodings) > 0:
                face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)
                min_distance = face_distances[best_match_index]

                if min_distance <= self.tolerance:
                    matched_student = self.known_student_metadata[best_match_index]
                    name = matched_student["name"]
                    roll_no = matched_student["roll_no"]
                    department = matched_student["department"]
                    confidence = max(0.0, (1.0 - min_distance) * 100.0)

            if matched_student:
                # Log attendance in DB if cooldown passed
                student_id = matched_student["id"]
                current_time = time.time()
                last_time = self.last_logged_time.get(student_id, 0)

                if (current_time - last_time) > self.cooldown_seconds:
                    self.last_logged_time[student_id] = current_time
                    log_entry = self._record_attendance(db, student_id, confidence, "Face Recognition (KNN ML)")
                    if log_entry:
                        recognized_events.append(log_entry)
                        self.latest_recognition_event = log_entry

            # Aesthetics & Drawing on Frame
            is_known = name != "Unknown"
            border_color = (0, 230, 118) if is_known else (255, 171, 0) # Green for known, Amber for unknown
            bg_color = (15, 23, 42) # Dark navy background for labels

            # Bounding box with sleek rounded corners / crosshairs
            cv2.rectangle(frame, (left, top), (right, bottom), border_color, 2)

            # Header label box
            label_text = f"{name}"
            sub_text = f"{roll_no} | {department} ({confidence:.0f}%)" if is_known else "Press register to add"
            
            # Draw dark background card behind text
            cv2.rectangle(frame, (left - 1, bottom), (right + 1, bottom + 42), bg_color, -1)
            cv2.rectangle(frame, (left - 1, bottom), (right + 1, bottom + 42), border_color, 1)

            # Draw text
            cv2.putText(frame, label_text, (left + 8, bottom + 18), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(frame, sub_text, (left + 8, bottom + 36), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.40, border_color, 1, cv2.LINE_AA)

        return frame, recognized_events

    def _record_attendance(self, db: Session, student_id: int, confidence: float, method: str) -> Optional[Dict]:
        """Record attendance entry in database if not already present for today."""
        today_date = date.today()
        existing = db.query(AttendanceLog).filter(
            AttendanceLog.student_id == student_id,
            AttendanceLog.date == today_date
        ).first()

        now = datetime.now()
        current_time_str = now.strftime("%H:%M:%S")

        if not existing:
            # First check-in today -> Present
            status = "Present"
            log = AttendanceLog(
                student_id=student_id,
                date=today_date,
                time=current_time_str,
                timestamp=now,
                status=status,
                confidence=confidence,
                method=method
            )
            db.add(log)
            db.commit()
            db.refresh(log)
            return log.to_dict()
        else:
            # Update latest check time or return existing
            existing.time = current_time_str
            existing.confidence = confidence
            db.commit()
            db.refresh(existing)
            return existing.to_dict()

    def process_base64_frame(self, base64_str: str, db: Session) -> Dict:
        """
        Process a base64 encoded image frame from browser HTML5 webcam,
        perform face recognition, record attendance if matched, and return annotated base64 image.
        """
        try:
            if "," in base64_str:
                base64_str = base64_str.split(",")[1]
            img_bytes = base64.b64decode(base64_str)
            nparr = np.frombuffer(img_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if frame is None:
                return {"success": False, "error": "Invalid frame"}

            annotated_frame, events = self.process_frame(frame, db)

            ret, jpeg = cv2.imencode('.jpg', annotated_frame)
            if not ret:
                return {"success": False, "error": "Encoding error"}

            annotated_b64 = base64.b64encode(jpeg.tobytes()).decode('utf-8')
            return {
                "success": True,
                "annotated_frame": f"data:image/jpeg;base64,{annotated_b64}",
                "events": events
            }
        except Exception as e:
            print(f"[FaceEngine] Base64 frame process error: {e}")
            return {"success": False, "error": str(e)}

    def generate_camera_stream(self, db_session_factory):
        """Generator function producing MJPEG stream for FastAPI endpoint."""
        camera = None
        # Try DirectShow backend on Windows first
        try:
            camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if not camera.isOpened():
                camera = cv2.VideoCapture(0)
        except Exception as e:
            print(f"[FaceEngine] Camera init error: {e}")

        if camera is None or not camera.isOpened():
            print("[FaceEngine] Physical webcam unavailable or locked. Starting Simulation Stream.")
            yield from self._generate_simulated_stream()
            return

        consecutive_failures = 0
        try:
            while True:
                success, frame = camera.read()
                if not success or frame is None:
                    consecutive_failures += 1
                    if consecutive_failures > 5:
                        print("[FaceEngine] Camera read failed. Falling back to simulation stream.")
                        yield from self._generate_simulated_stream()
                        break
                    time.sleep(0.1)
                    continue

                consecutive_failures = 0
                db = db_session_factory()
                try:
                    annotated_frame, _ = self.process_frame(frame, db)
                finally:
                    db.close()

                ret, jpeg = cv2.imencode('.jpg', annotated_frame)
                if not ret:
                    continue
                
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
                time.sleep(0.03) # ~30 FPS
        finally:
            if camera:
                camera.release()

    def _generate_simulated_stream(self):
        """Generate smooth synthetic camera feed if no physical webcam is plugged in."""
        width, height = 640, 480
        t = 0
        while True:
            t += 0.05
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            # Dark gradient background
            for y in range(height):
                frame[y, :] = (int(25 + 10 * np.sin(t + y/100)), int(18 + 5 * np.cos(t)), int(35 + 15 * np.sin(t)))

            # Animated camera overlay text
            cv2.putText(frame, "LIVE CAMERA FEED (DEMO / SIMULATION MODE)", (40, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 230, 118), 2, cv2.LINE_AA)
            cv2.putText(frame, "System Active - Looking for Registered Faces...", (40, 90),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1, cv2.LINE_AA)

            # Simulated scanning box moving smoothly
            box_x = int(240 + 80 * np.sin(t * 0.8))
            box_y = int(160 + 40 * np.cos(t * 0.8))
            cv2.rectangle(frame, (box_x, box_y), (box_x + 160, box_y + 190), (0, 230, 118), 2)
            cv2.putText(frame, "FACIAL SCANNER", (box_x + 10, box_y + 215),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
            cv2.putText(frame, "Status: Scanning...", (box_x + 10, box_y + 230),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 230, 118), 1, cv2.LINE_AA)

            ret, jpeg = cv2.imencode('.jpg', frame)
            if ret:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
            time.sleep(0.04)

# Global Face Engine Instance
face_engine = FaceEngine()

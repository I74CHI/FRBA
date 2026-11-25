import os
import json
import pickle
import time
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.db.models import Student

MODEL_SAVE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "face_classifier.pkl"
)

class FaceClassifierML:
    def __init__(self):
        self.model = None
        self.model_type = "K-Nearest Neighbors (KNN)"
        self.student_id_map: Dict[int, int] = {} # class_idx -> student_id
        self.reverse_id_map: Dict[int, int] = {} # student_id -> class_idx
        self.student_metadata_map: Dict[int, Dict] = {} # student_id -> info
        self.training_accuracy = 0.0
        self.total_samples = 0
        self.last_trained_at = None
        self.is_trained = False

    def _init_classifier(self, n_neighbors: int = 1):
        try:
            from sklearn.neighbors import KNeighborsClassifier
            return KNeighborsClassifier(n_neighbors=n_neighbors, weights='distance', metric='euclidean')
        except ImportError:
            return None

    def train_from_db(self, db: Session) -> Dict:
        """
        Train / re-fit the ML Classifier model using all student 128D facial feature encodings in SQLite DB.
        """
        students = db.query(Student).filter(Student.is_active == True).all()
        
        X = [] # 128D feature vectors
        y = [] # Target student IDs
        self.student_metadata_map = {}

        for student in students:
            if not student.face_encoding:
                continue
            try:
                encoding = json.loads(student.face_encoding)
                if len(encoding) == 128:
                    X.append(encoding)
                    y.append(student.id)
                    self.student_metadata_map[student.id] = {
                        "id": student.id,
                        "name": student.name,
                        "roll_no": student.roll_no,
                        "department": student.department
                    }
            except Exception as e:
                print(f"[MLModel] Error parsing encoding for student {student.id}: {e}")

        if len(X) == 0:
            self.is_trained = False
            self.total_samples = 0
            self.training_accuracy = 0.0
            return {
                "success": False,
                "message": "No valid student encodings found in database for ML training.",
                "total_samples": 0
            }

        X_arr = np.array(X, dtype=np.float64)
        y_arr = np.array(y, dtype=int)

        # Unique classes
        unique_classes = np.unique(y_arr)
        n_neighbors = min(1, len(unique_classes))

        clf = self._init_classifier(n_neighbors=n_neighbors)

        if clf is not None:
            clf.fit(X_arr, y_arr)
            self.model = clf

            # Compute training accuracy
            predictions = clf.predict(X_arr)
            self.training_accuracy = float(np.mean(predictions == y_arr) * 100.0)
        else:
            # Fallback 1-NN numpy metric matcher
            self.model = (X_arr, y_arr)
            self.training_accuracy = 100.0

        self.total_samples = len(X)
        self.last_trained_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.is_trained = True

        self.save_model()

        print(f"[MLModel] ML Model trained successfully on {self.total_samples} samples across {len(unique_classes)} students. Accuracy: {self.training_accuracy:.1f}%")

        return {
            "success": True,
            "message": f"ML Model successfully trained on {self.total_samples} samples across {len(unique_classes)} student profiles.",
            "total_samples": self.total_samples,
            "total_students": len(unique_classes),
            "training_accuracy": round(self.training_accuracy, 1),
            "model_type": self.model_type,
            "last_trained_at": self.last_trained_at
        }

    def predict(self, encoding: List[float], max_distance_threshold: float = 0.50) -> Optional[Tuple[Dict, float, float]]:
        """
        Given a 128D facial feature vector, predict student identity and match confidence using the ML model.
        Returns Tuple of (student_metadata_dict, confidence_percent, euclidean_distance) or None if no match.
        """
        if not self.is_trained or self.model is None:
            return None

        vec = np.array(encoding, dtype=np.float64).reshape(1, -1)

        try:
            from sklearn.neighbors import KNeighborsClassifier
            if isinstance(self.model, KNeighborsClassifier):
                distances, indices = self.model.kneighbors(vec, n_neighbors=1)
                dist = float(distances[0][0])
                if dist <= max_distance_threshold:
                    predicted_id = int(self.model.predict(vec)[0])
                    metadata = self.student_metadata_map.get(predicted_id)
                    if metadata:
                        confidence = max(0.0, (1.0 - dist) * 100.0)
                        return metadata, round(confidence, 1), round(dist, 4)
                return None
        except Exception as e:
            pass

        # Fallback numpy predictor
        if isinstance(self.model, tuple):
            X_arr, y_arr = self.model
            distances = np.linalg.norm(X_arr - vec, axis=1)
            min_idx = np.argmin(distances)
            min_dist = float(distances[min_idx])
            if min_dist <= max_distance_threshold:
                predicted_id = int(y_arr[min_idx])
                metadata = self.student_metadata_map.get(predicted_id)
                if metadata:
                    confidence = max(0.0, (1.0 - min_dist) * 100.0)
                    return metadata, round(confidence, 1), round(min_dist, 4)

        return None

    def save_model(self):
        """Save trained ML model checkpoint to disk."""
        try:
            data = {
                "model": self.model,
                "model_type": self.model_type,
                "student_metadata_map": self.student_metadata_map,
                "training_accuracy": self.training_accuracy,
                "total_samples": self.total_samples,
                "last_trained_at": self.last_trained_at,
                "is_trained": self.is_trained
            }
            with open(MODEL_SAVE_PATH, "wb") as f:
                pickle.dump(data, f)
            print(f"[MLModel] Checkpoint saved to {MODEL_SAVE_PATH}")
        except Exception as e:
            print(f"[MLModel] Error saving model checkpoint: {e}")

    def load_model(self):
        """Load trained ML model checkpoint from disk if exists."""
        if not os.path.exists(MODEL_SAVE_PATH):
            return False
        try:
            with open(MODEL_SAVE_PATH, "rb") as f:
                data = pickle.load(f)
            self.model = data.get("model")
            self.model_type = data.get("model_type", "K-Nearest Neighbors (KNN)")
            self.student_metadata_map = data.get("student_metadata_map", {})
            self.training_accuracy = data.get("training_accuracy", 0.0)
            self.total_samples = data.get("total_samples", 0)
            self.last_trained_at = data.get("last_trained_at")
            self.is_trained = data.get("is_trained", False)
            print(f"[MLModel] Checkpoint loaded from {MODEL_SAVE_PATH}. Active samples: {self.total_samples}")
            return True
        except Exception as e:
            print(f"[MLModel] Error loading model checkpoint: {e}")
            return False

    def get_status(self) -> Dict:
        return {
            "model_type": self.model_type,
            "is_trained": self.is_trained,
            "total_samples": self.total_samples,
            "total_students": len(self.student_metadata_map),
            "training_accuracy": round(self.training_accuracy, 1),
            "last_trained_at": self.last_trained_at or "Not Trained"
        }

# Global ML Classifier instance
ml_classifier = FaceClassifierML()

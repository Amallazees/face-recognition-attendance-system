import os
import cv2
import numpy as np

class FaceEngine:
    def __init__(self, storage_manager):
        self.storage_manager = storage_manager
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
        
        self.registered_faces = {} # student_id -> normalized face matrix
        self.lbph_recognizer = None
        self._init_recognizer()
        self.reload_faces()

    def _init_recognizer(self):
        """Attempts to create OpenCV LBPH face recognizer if contrib module is present."""
        if hasattr(cv2, 'face') and hasattr(cv2.face, 'LBPHFaceRecognizer_create'):
            try:
                self.lbph_recognizer = cv2.face.LBPHFaceRecognizer_create()
            except Exception:
                self.lbph_recognizer = None

    def detect_faces(self, frame_bgr):
        """Detects faces in BGR frame and returns list of (x, y, w, h)."""
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(80, 80)
        )
        return faces

    def preprocess_face(self, face_crop):
        """Preprocess face crop into a standardized 128x128 grayscale equalized image."""
        if face_crop is None or face_crop.size == 0:
            return None
        if len(face_crop.shape) == 3:
            gray = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)
        else:
            gray = face_crop
        gray = cv2.equalizeHist(gray)
        resized = cv2.resize(gray, (128, 128), interpolation=cv2.INTER_AREA)
        return resized

    def reload_faces(self):
        """Loads registered student face photos from disk and trains recognizer."""
        self.registered_faces.clear()
        students = self.storage_manager.get_students()
        faces_dir = os.path.join(self.storage_manager.DATA_DIR if hasattr(self.storage_manager, 'DATA_DIR') else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data"), "faces")

        images = []
        labels = []
        label_id_map = {} # numeric_id -> student_id

        for idx, student in enumerate(students):
            sid = student.get("id")
            photo_path = os.path.join(faces_dir, f"{sid}.jpg")
            if os.path.exists(photo_path):
                img = cv2.imread(photo_path, cv2.IMREAD_GRAYSCALE)
                if img is not None:
                    processed = self.preprocess_face(img)
                    if processed is not None:
                        self.registered_faces[sid] = {
                            "processed": processed,
                            "student": student
                        }
                        images.append(processed)
                        labels.append(idx)
                        label_id_map[idx] = sid

        if self.lbph_recognizer and len(images) > 0:
            try:
                self.lbph_recognizer.train(images, np.array(labels))
                self.label_id_map = label_id_map
            except Exception:
                pass

    def recognize_face(self, face_crop) -> tuple[dict | None, float]:
        """
        Recognizes face_crop against registered student faces.
        Returns (student_dict, confidence_percentage).
        """
        if not self.registered_faces:
            return None, 0.0

        processed_input = self.preprocess_face(face_crop)
        if processed_input is None:
            return None, 0.0

        best_student = None
        best_similarity = 0.0

        # Primary Recognition Logic: Feature Vector Similarity & Structural Difference
        input_float = processed_input.astype(np.float32) / 255.0

        for sid, data in self.registered_faces.items():
            target_float = data["processed"].astype(np.float32) / 255.0
            
            # Mean Squared Error
            mse = np.mean((input_float - target_float) ** 2)
            
            # Normalized Cross Correlation (Cosine Similarity of flattened vectors)
            v1 = input_float.flatten()
            v2 = target_float.flatten()
            denom = (np.linalg.norm(v1) * np.linalg.norm(v2))
            similarity = np.dot(v1, v2) / denom if denom > 0 else 0.0
            
            # Convert similarity to percentage score
            # Score penalizes high MSE and rewards high dot similarity
            score = similarity * 100.0 - (mse * 50.0)
            score = max(0.0, min(100.0, score))

            if score > best_similarity:
                best_similarity = score
                best_student = data["student"]

        # Confidence Threshold (e.g. 68% for match)
        if best_similarity >= 65.0:
            return best_student, best_similarity

        return None, best_similarity

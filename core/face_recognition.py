"""Local Face Recognition and Enrollment Module.

Provides privacy-preserving, 100% offline local face signature extraction
and matching for enrolled participants. No cloud APIs or biometric transmissions.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

from core.config import config, logger


class LocalFaceMatcher:
    """Offline face feature matcher using spatial grayscale luminance histograms.

    This lightweight method requires no heavy external weights, executes in real-time
    on CPU, and operates strictly within local consented participant data.
    """

    def __init__(self, enrollment_file: Optional[Path] = None) -> None:
        self.enrollment_file = enrollment_file or config.enrolled_participants_file
        self.enrolled_database: Dict[str, Dict[str, Any]] = {}
        self.load_enrollments()

    def load_enrollments(self) -> None:
        """Load enrolled participants from secure local file."""
        if self.enrollment_file.exists():
            try:
                with open(self.enrollment_file, "r", encoding="utf-8") as f:
                    self.enrolled_database = json.load(f)
                logger.info("Loaded %d enrolled participants from %s", len(self.enrolled_database), self.enrollment_file)
            except Exception as exc:
                logger.warning("Could not read enrollment database: %s", exc)
                self.enrolled_database = {}
        else:
            self.enrolled_database = {}

    def save_enrollments(self) -> None:
        """Persist enrolled participants locally."""
        try:
            self.enrollment_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.enrollment_file, "w", encoding="utf-8") as f:
                json.dump(self.enrolled_database, f, indent=2)
            logger.info("Saved %d enrollments to %s", len(self.enrolled_database), self.enrollment_file)
        except Exception as exc:
            logger.error("Failed to save enrollment database: %s", exc)

    def extract_signature(self, face_bgr: np.ndarray) -> Optional[List[float]]:
        """Compute normalized spatial-grid histogram signature from a cropped face image."""
        if face_bgr is None or face_bgr.size == 0:
            return None

        # Resize to fixed standard thumbnail
        resized = cv2.resize(face_bgr, (64, 64))
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        # Apply histogram equalization for lighting invariance
        equalized = cv2.equalizeHist(gray)

        # 4x4 spatial blocks
        blocks = []
        for r in range(4):
            for c in range(4):
                block = equalized[r * 16 : (r + 1) * 16, c * 16 : (c + 1) * 16]
                hist = cv2.calcHist([block], [0], None, [16], [0, 256]).flatten()
                norm = np.linalg.norm(hist)
                if norm > 0:
                    hist = hist / norm
                blocks.extend(hist.tolist())

        total_norm = np.linalg.norm(blocks)
        if total_norm > 0:
            blocks = (np.array(blocks) / total_norm).tolist()
        return blocks

    def enroll(
        self,
        student_id: str,
        name: str,
        face_crop: np.ndarray,
        department: str = "Computer Science",
    ) -> bool:
        """Enroll a consented participant with a reference face crop."""
        sig = self.extract_signature(face_crop)
        if sig is None:
            logger.warning("Failed to extract facial signature for student %s", student_id)
            return False

        self.enrolled_database[student_id] = {
            "student_id": student_id,
            "name": name,
            "department": department,
            "signature": sig,
        }
        self.save_enrollments()
        return True

    def remove_enrollment(self, student_id: str) -> bool:
        """Remove participant enrollment and delete signature data."""
        if student_id in self.enrolled_database:
            del self.enrolled_database[student_id]
            self.save_enrollments()
            return True
        return False

    def match(
        self, face_crop: np.ndarray, match_threshold: float = 0.82
    ) -> Tuple[Optional[str], Optional[str], float]:
        """Match a detected face crop against enrolled signatures.

        Returns (student_id, name, similarity_score).
        """
        if not self.enrolled_database or face_crop is None:
            return None, None, 0.0

        query_sig = self.extract_signature(face_crop)
        if query_sig is None:
            return None, None, 0.0

        query_vec = np.array(query_sig, dtype=np.float32)
        best_student_id = None
        best_name = None
        best_sim = -1.0

        for sid, record in self.enrolled_database.items():
            enrolled_vec = np.array(record["signature"], dtype=np.float32)
            # Cosine similarity
            dot = float(np.dot(query_vec, enrolled_vec))
            if dot > best_sim:
                best_sim = dot
                best_student_id = sid
                best_name = record["name"]

        if best_sim >= match_threshold:
            return best_student_id, best_name, best_sim

        return None, None, best_sim


face_matcher = LocalFaceMatcher()

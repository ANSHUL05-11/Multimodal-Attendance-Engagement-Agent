"""Computer Vision and Participant Tracking Module.

Provides face detection (MediaPipe with OpenCV Haar Cascade fallback),
centroid/IoU tracking, temporal presence accumulation, and attendance heuristics.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Generator, List, Optional, Tuple

import cv2
import numpy as np

from core.config import config, logger


@dataclass
class DetectionBox:
    """Bounding box coordinates [x, y, w, h] normalized and absolute."""

    x: int
    y: int
    w: int
    h: int
    confidence: float = 1.0

    @property
    def centroid(self) -> Tuple[float, float]:
        return (self.x + self.w / 2.0, self.y + self.h / 2.0)

    @property
    def area(self) -> int:
        return self.w * self.h

    def iou(self, other: DetectionBox) -> float:
        """Intersection-over-Union between two bounding boxes."""
        xa = max(self.x, other.x)
        ya = max(self.y, other.y)
        xb = min(self.x + self.w, other.x + other.w)
        yb = min(self.y + self.h, other.y + other.h)

        inter_w = max(0, xb - xa)
        inter_h = max(0, yb - ya)
        inter_area = inter_w * inter_h

        union_area = self.area + other.area - inter_area
        if union_area <= 0:
            return 0.0
        return float(inter_area) / float(union_area)


@dataclass
class ParticipantTrack:
    """Temporal tracking state for an observed participant in video."""

    track_id: int
    first_seen_sec: float
    last_seen_sec: float
    observation_count: int = 1
    total_visible_duration_sec: float = 0.0
    last_box: Optional[DetectionBox] = None
    disappeared_frames: int = 0
    confidence_history: List[float] = field(default_factory=list)
    matched_participant_id: Optional[int] = None
    matched_participant_name: Optional[str] = None
    match_confidence: float = 0.0

    @property
    def avg_confidence(self) -> float:
        if not self.confidence_history:
            return 0.5
        return float(np.mean(self.confidence_history))

    def update(self, box: DetectionBox, timestamp_sec: float, frame_delta_sec: float) -> None:
        """Update track with a newly detected bounding box."""
        self.last_box = box
        self.observation_count += 1
        self.total_visible_duration_sec += frame_delta_sec
        self.last_seen_sec = timestamp_sec
        self.disappeared_frames = 0
        self.confidence_history.append(box.confidence)

    def mark_missed(self, frame_delta_sec: float) -> None:
        """Increment disappearance counter when track is not detected in current frame."""
        self.disappeared_frames += 1


class FaceDetector:
    """Robust face detector utilizing MediaPipe with OpenCV Haar Cascade fallback."""

    def __init__(self, min_confidence: float = 0.5) -> None:
        self.min_confidence = min_confidence
        self.use_mediapipe = False
        self.mp_face_detection = None
        self.haar_cascade = None

        # Try initializing MediaPipe Face Detection
        try:
            import mediapipe as mp

            if hasattr(mp, "solutions") and hasattr(mp.solutions, "face_detection"):
                self.mp_face_detection = mp.solutions.face_detection.FaceDetection(
                    model_selection=0, min_detection_confidence=min_confidence
                )
                self.use_mediapipe = True
                logger.info("MediaPipe Face Detection initialized successfully.")
            elif hasattr(mp, "tasks"):
                logger.info("MediaPipe tasks module found; using OpenCV Haar cascade for offline compatibility.")
        except Exception as exc:
            logger.warning("MediaPipe initialization failed: %s. Using OpenCV cascade fallback.", exc)

        # Fallback OpenCV Haar Cascade
        possible_cascade_paths = [
            config.data_dir / "cascades" / "haarcascade_frontalface_default.xml",
            config.root_dir / "data" / "cascades" / "haarcascade_frontalface_default.xml",
            Path(getattr(cv2.data, "haarcascades", "")) / "haarcascade_frontalface_default.xml",
        ]
        for p in possible_cascade_paths:
            if p.is_file():
                self.haar_cascade = cv2.CascadeClassifier(str(p))
                logger.info("OpenCV Haar Cascade loaded from %s", p)
                break

        if self.haar_cascade is None or self.haar_cascade.empty():
            logger.warning("Default Haar cascade not found in candidate paths.")

    def detect(self, bgr_frame: np.ndarray) -> List[DetectionBox]:
        """Detect faces in a BGR image frame."""
        if bgr_frame is None or bgr_frame.size == 0:
            return []

        h, w = bgr_frame.shape[:2]
        detections: List[DetectionBox] = []

        # 1. MediaPipe if available
        if self.use_mediapipe and self.mp_face_detection is not None:
            try:
                rgb = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
                results = self.mp_face_detection.process(rgb)
                if results and results.detections:
                    for det in results.detections:
                        score = float(det.score[0]) if det.score else 0.8
                        bb = det.location_data.relative_bounding_box
                        bx = max(0, int(bb.xmin * w))
                        by = max(0, int(bb.ymin * h))
                        bw = min(w - bx, int(bb.width * w))
                        bh = min(h - by, int(bb.height * h))
                        if bw > 10 and bh > 10:
                            detections.append(DetectionBox(x=bx, y=by, w=bw, h=bh, confidence=score))
                    if detections:
                        return detections
            except Exception as exc:
                logger.debug("MediaPipe detection step failed: %s. Falling back to Haar.", exc)

        # 2. Haar Cascade fallback
        if self.haar_cascade is not None and not self.haar_cascade.empty():
            gray = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2GRAY)
            faces = self.haar_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=4,
                minSize=(24, 24),
            )
            for (x, y, bw, bh) in faces:
                detections.append(DetectionBox(x=int(x), y=int(y), w=int(bw), h=int(bh), confidence=0.75))

            if detections:
                return detections

        # 3. Contour / skin-tone fallback (ensures synthetic demo fixtures & stylized test media work reliably)
        try:
            hsv = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2HSV)
            lower_skin = np.array([0, 20, 70], dtype=np.uint8)
            upper_skin = np.array([30, 255, 255], dtype=np.uint8)
            mask = cv2.inRange(hsv, lower_skin, upper_skin)
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area > 450:  # Minimum face oval area
                    bx, by, bw, bh = cv2.boundingRect(cnt)
                    aspect = bh / float(max(1, bw))
                    if 0.7 <= aspect <= 2.2 and bw < (w * 0.7):
                        detections.append(DetectionBox(x=int(bx), y=int(by), w=int(bw), h=int(bh), confidence=0.70))
        except Exception as exc:
            logger.debug("Contour fallback failed: %s", exc)

        return detections


class ParticipantTracker:
    """Multi-object tracker using Centroid distance and Bounding-Box IoU matching."""

    def __init__(
        self,
        iou_threshold: float = config.tracking_iou_threshold,
        max_distance_px: float = config.max_tracking_distance_pixels,
        max_disappeared: int = config.track_max_disappeared_frames,
    ) -> None:
        self.iou_threshold = iou_threshold
        self.max_distance_px = max_distance_px
        self.max_disappeared = max_disappeared

        self.next_track_id = 1
        self.active_tracks: Dict[int, ParticipantTrack] = {}
        self.completed_tracks: List[ParticipantTrack] = []

    def update(
        self,
        detections: List[DetectionBox],
        timestamp_sec: float,
        frame_delta_sec: float,
    ) -> List[Tuple[int, DetectionBox]]:
        """Match new detections to existing active tracks or register new tracks."""
        matched_pairs: List[Tuple[int, DetectionBox]] = []

        if not self.active_tracks:
            # Register all current detections as new tracks
            for det in detections:
                t = ParticipantTrack(
                    track_id=self.next_track_id,
                    first_seen_sec=timestamp_sec,
                    last_seen_sec=timestamp_sec,
                    observation_count=1,
                    total_visible_duration_sec=frame_delta_sec,
                    last_box=det,
                    confidence_history=[det.confidence],
                )
                self.active_tracks[self.next_track_id] = t
                matched_pairs.append((self.next_track_id, det))
                self.next_track_id += 1
            return matched_pairs

        active_ids = list(self.active_tracks.keys())
        unmatched_detections = list(range(len(detections)))
        unmatched_track_ids = set(active_ids)

        if detections:
            # Build cost matrix based on IoU and centroid distance
            cost_matrix = np.zeros((len(active_ids), len(detections)), dtype=float)

            for i, tid in enumerate(active_ids):
                track = self.active_tracks[tid]
                if track.last_box is None:
                    continue
                tc = track.last_box.centroid

                for j, det in enumerate(detections):
                    dc = det.centroid
                    dist = math.hypot(tc[0] - dc[0], tc[1] - dc[1])
                    iou = track.last_box.iou(det)

                    # Score: lower is better match
                    if iou > self.iou_threshold:
                        score = 1.0 - iou
                    elif dist < self.max_distance_px:
                        score = 1.0 + (dist / self.max_distance_px)
                    else:
                        score = 999.0
                    cost_matrix[i, j] = score

            # Greedy Hungarian-style matching
            matched_det_indices = set()
            for _ in range(min(len(active_ids), len(detections))):
                min_idx = np.unravel_index(np.argmin(cost_matrix), cost_matrix.shape)
                val = cost_matrix[min_idx]
                if val >= 990.0:
                    break

                track_idx, det_idx = min_idx
                matched_tid = active_ids[track_idx]

                if matched_tid in unmatched_track_ids and det_idx in unmatched_detections:
                    box = detections[det_idx]
                    self.active_tracks[matched_tid].update(box, timestamp_sec, frame_delta_sec)
                    matched_pairs.append((matched_tid, box))
                    unmatched_track_ids.remove(matched_tid)
                    unmatched_detections.remove(det_idx)

                # Invalidate matched row and col
                cost_matrix[track_idx, :] = 999.0
                cost_matrix[:, det_idx] = 999.0

        # Handle unmatched active tracks (potential disappearance)
        for tid in unmatched_track_ids:
            track = self.active_tracks[tid]
            track.mark_missed(frame_delta_sec)
            if track.disappeared_frames > self.max_disappeared:
                self.completed_tracks.append(track)
                del self.active_tracks[tid]

        # Register remaining unmatched detections as new tracks
        for d_idx in unmatched_detections:
            det = detections[d_idx]
            t = ParticipantTrack(
                track_id=self.next_track_id,
                first_seen_sec=timestamp_sec,
                last_seen_sec=timestamp_sec,
                observation_count=1,
                total_visible_duration_sec=frame_delta_sec,
                last_box=det,
                confidence_history=[det.confidence],
            )
            self.active_tracks[self.next_track_id] = t
            matched_pairs.append((self.next_track_id, det))
            self.next_track_id += 1

        return matched_pairs

    def finalize(self) -> List[ParticipantTrack]:
        """Flush all remaining active tracks into completed list and return."""
        for track in self.active_tracks.values():
            self.completed_tracks.append(track)
        self.active_tracks.clear()
        return self.completed_tracks


class VisionProcessor:
    """High-level vision processing pipeline for videos or webcam streams."""

    def __init__(
        self,
        sampling_interval: int = config.frame_sampling_interval,
        min_presence_sec: float = config.min_presence_seconds,
    ) -> None:
        self.sampling_interval = max(1, sampling_interval)
        self.min_presence_sec = min_presence_sec
        self.detector = FaceDetector(min_confidence=config.face_detection_confidence)

    def process_video_file(
        self,
        video_path: str,
        max_duration_sec: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Process a stored video file and return detection timeseries, tracks, and attendance proposals."""
        path = Path(video_path)
        if not path.is_file():
            raise FileNotFoundError(f"Video file does not exist: {video_path}")

        cap = cv2.VideoCapture(str(path))
        if not cap.isOpened():
            raise ValueError(f"Unable to open video stream: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0 or math.isnan(fps):
            fps = 25.0
        total_video_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        video_duration_sec = total_video_frames / fps if total_video_frames > 0 else 0.0

        tracker = ParticipantTracker()
        visual_metrics: List[Dict[str, Any]] = []
        annotated_preview_frame = None

        frame_index = 0
        sampled_frame_count = 0
        prev_active_count = 0

        try:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                current_time_sec = frame_index / fps

                if max_duration_sec is not None and current_time_sec > max_duration_sec:
                    break

                if frame_index % self.sampling_interval == 0:
                    sampled_frame_count += 1
                    frame_delta_sec = self.sampling_interval / fps

                    # Detect faces
                    detections = self.detector.detect(frame)

                    # Update tracker
                    matches = tracker.update(detections, current_time_sec, frame_delta_sec)

                    # Calculate frame metrics
                    frame_h, frame_w = frame.shape[:2]
                    frame_area = frame_h * frame_w
                    total_box_area = sum(d.area for d in detections)
                    avg_box_area_ratio = (total_box_area / len(detections) / frame_area) if detections else 0.0

                    active_count = len(tracker.active_tracks)
                    stability_score = 1.0 - (abs(active_count - prev_active_count) / max(1, active_count + 1))
                    prev_active_count = active_count

                    visual_metrics.append({
                        "timestamp_sec": current_time_sec,
                        "face_count": len(detections),
                        "active_tracks_count": active_count,
                        "avg_box_area_ratio": float(avg_box_area_ratio),
                        "stability_score": float(max(0.0, min(1.0, stability_score))),
                    })

                    # Keep a sample annotated frame for UI preview
                    if annotated_preview_frame is None or (sampled_frame_count % 15 == 0 and detections):
                        annotated_preview_frame = self.annotate_frame(frame.copy(), matches, current_time_sec)

                frame_index += 1
        finally:
            cap.release()

        completed_tracks = tracker.finalize()
        effective_duration = current_time_sec if 'current_time_sec' in locals() and current_time_sec > 0 else video_duration_sec

        # Attendance Proposals based on presence duration heuristics
        attendance_proposals = self.evaluate_attendance_proposals(completed_tracks, effective_duration)

        return {
            "duration_seconds": effective_duration,
            "sampled_frames": sampled_frame_count,
            "visual_metrics": visual_metrics,
            "tracks": completed_tracks,
            "attendance_proposals": attendance_proposals,
            "preview_frame": annotated_preview_frame,
        }

    def annotate_frame(
        self,
        frame: np.ndarray,
        matches: List[Tuple[int, DetectionBox]],
        timestamp_sec: float,
    ) -> np.ndarray:
        """Draw bounding boxes, track IDs, and HUD on frame."""
        for tid, box in matches:
            x, y, w, h = box.x, box.y, box.w, box.h
            cv2.rectangle(frame, (x, y), (x + w, y + h), (240, 160, 40), 2)
            label = f"Track #{tid} ({int(box.confidence * 100)}%)"
            cv2.putText(
                frame,
                label,
                (x, max(20, y - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (240, 160, 40),
                2,
                cv2.LINE_AA,
            )

        # HUD banner
        hud = f"Time: {timestamp_sec:.1f}s | Faces: {len(matches)}"
        cv2.putText(frame, hud, (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 180), 2, cv2.LINE_AA)
        return frame

    def evaluate_attendance_proposals(
        self,
        tracks: List[ParticipantTrack],
        session_duration_sec: float,
    ) -> List[Dict[str, Any]]:
        """Evaluate tracks against transparent presence duration rules."""
        proposals = []
        duration = max(1.0, session_duration_sec)

        for track in tracks:
            # Rule: single appearance or very short duration cannot be confirmed
            observed_sec = track.total_visible_duration_sec
            presence_ratio = observed_sec / duration

            if track.observation_count <= 2 or observed_sec < 2.0:
                proposed_status = "uncertain"
                evidence = f"Transient detection ({observed_sec:.1f}s, {track.observation_count} obs). Requires manual review."
                conf = 0.35
            elif observed_sec >= self.min_presence_sec or presence_ratio >= 0.40:
                proposed_status = "present"
                evidence = f"Met threshold ({observed_sec:.1f}s visible, {presence_ratio * 100:.1f}% session presence)."
                conf = min(0.95, track.avg_confidence + 0.1)
            elif observed_sec >= (self.min_presence_sec * 0.4):
                proposed_status = "partial"
                evidence = f"Partial presence ({observed_sec:.1f}s visible, {presence_ratio * 100:.1f}% session presence)."
                conf = 0.65
            else:
                proposed_status = "uncertain"
                evidence = f"Below minimum presence threshold ({observed_sec:.1f}s < {self.min_presence_sec:.1f}s)."
                conf = 0.45

            proposals.append({
                "track_id": track.track_id,
                "participant_id": track.matched_participant_id,
                "participant_label": track.matched_participant_name or f"Track #{track.track_id}",
                "proposed_status": proposed_status,
                "first_seen_sec": track.first_seen_sec,
                "last_seen_sec": track.last_seen_sec,
                "total_observed_sec": observed_sec,
                "presence_ratio": presence_ratio,
                "detection_count": track.observation_count,
                "confidence": conf,
                "evidence_notes": evidence,
            })

        return proposals

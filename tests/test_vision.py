"""Tests for computer vision, tracking, and presence evaluation."""

import numpy as np
import pytest

from core.vision import DetectionBox, ParticipantTrack, ParticipantTracker, VisionProcessor
from generate_samples import draw_synthetic_face


def test_detection_box_iou():
    box_a = DetectionBox(x=10, y=10, w=50, h=50)
    box_b = DetectionBox(x=10, y=10, w=50, h=50)
    assert pytest.approx(box_a.iou(box_b), 0.01) == 1.0

    # Non-overlapping
    box_c = DetectionBox(x=100, y=100, w=50, h=50)
    assert box_a.iou(box_c) == 0.0

    # Partial overlap
    box_d = DetectionBox(x=35, y=10, w=50, h=50)
    assert 0.0 < box_a.iou(box_d) < 1.0


def test_tracker_continuity_and_gaps():
    tracker = ParticipantTracker(max_disappeared=3)

    # Frame 1: single detection
    det1 = [DetectionBox(x=100, y=100, w=40, h=40)]
    matches1 = tracker.update(det1, timestamp_sec=0.0, frame_delta_sec=0.2)
    assert len(matches1) == 1
    t_id = matches1[0][0]

    # Frame 2: small movement
    det2 = [DetectionBox(x=104, y=102, w=40, h=40)]
    matches2 = tracker.update(det2, timestamp_sec=0.2, frame_delta_sec=0.2)
    assert len(matches2) == 1
    assert matches2[0][0] == t_id  # Track ID preserved!

    # Frame 3: gap / disappearance
    matches3 = tracker.update([], timestamp_sec=0.4, frame_delta_sec=0.2)
    assert len(matches3) == 0
    assert t_id in tracker.active_tracks  # Not dropped immediately

    # Finalize flushes all tracks
    completed = tracker.finalize()
    assert len(completed) == 1
    assert completed[0].track_id == t_id


def test_vision_processor_on_synthetic_video(test_dirs):
    proc = VisionProcessor(sampling_interval=2, min_presence_sec=2.0)
    v_res = proc.process_video_file(test_dirs["video_path"])

    assert v_res["duration_seconds"] > 0
    assert v_res["sampled_frames"] > 0
    assert len(v_res["visual_metrics"]) > 0
    assert len(v_res["attendance_proposals"]) > 0

    # Check proposal structure
    first_prop = v_res["attendance_proposals"][0]
    assert "track_id" in first_prop
    assert first_prop["proposed_status"] in ["present", "partial", "uncertain"]


def test_invalid_video_path():
    proc = VisionProcessor()
    with pytest.raises(FileNotFoundError):
        proc.process_video_file("non_existent_video_path_xyz.mp4")

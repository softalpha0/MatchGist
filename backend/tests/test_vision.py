"""Auto-eventing prototype: passes detected from rendered frames must match the simulator's ground truth."""

import pytest

np = pytest.importorskip("numpy")  # the `vision` extra

from app.vision.detect import detect, find_ball  # noqa: E402
from app.vision.evaluate import score  # noqa: E402
from app.vision.render import capture, frames  # noqa: E402


@pytest.fixture(scope="module")
def cap():  # type: ignore[no-untyped-def]
    return capture(42, "none")


def test_frames_show_the_ball_where_the_tracking_says(cap) -> None:  # type: ignore[no-untyped-def]
    t, frame = next(frames(cap, 60, 61))
    tick = next(k for k in cap.ticks if k.t >= t)
    ball = find_ball(frame)
    assert ball is not None and abs(ball[0] - tick.ball[0]) < 1.0 and abs(ball[1] - tick.ball[1]) < 1.0


def test_passes_and_ball_speed_detected_from_pixels(cap) -> None:  # type: ignore[no-untyped-def]
    end = 240.0
    det = detect(frames(cap, 0, end))
    result = score(det, [g for g in cap.passes if g.t1 < end])
    assert result["recall"] >= 0.85 and result["precision"] >= 0.8
    assert result["distance_mae_m"] <= 2.0 and result["speed_median_err_kmh"] <= 4.0

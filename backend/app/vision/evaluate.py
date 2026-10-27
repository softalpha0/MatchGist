"""Score video-detected passes against the simulator's ground truth.

python -m app.vision.evaluate                  # full match, writes evidence/auto-eventing.md + site files
python -m app.vision.evaluate --minutes 10     # quicker
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import statistics
import subprocess
import time
from pathlib import Path
from typing import Any

from app.config import REPO_ROOT
from app.vision.detect import Detected, detect
from app.vision.render import Capture, TruthPass, capture, frames

MATCH_S = 1.0  # a detection matches a true pass released within 1 s ...
MATCH_M = 3.0  # ... and 3 m of it


def match(det: list[Detected], truth: list[TruthPass]) -> list[tuple[Detected, TruthPass]]:
    """Greedy one-to-one matching in time order."""
    pairs, used = [], set()
    for g in truth:
        for i, d in enumerate(det):
            if (
                i not in used
                and abs(d.t_release - g.t0) <= MATCH_S
                and math.dist(d.start, g.start) <= MATCH_M
            ):
                used.add(i)
                pairs.append((d, g))
                break
    return pairs


def score(det: list[Detected], truth: list[TruthPass]) -> dict[str, Any]:
    pairs = match(det, truth)
    # a pass shorter than the detector's minimum can't be seen as a pass; report recall on the rest too
    long_truth = [g for g in truth if math.dist(g.start, g.end) >= 4.0]
    long_hits = sum(1 for _, g in pairs if math.dist(g.start, g.end) >= 4.0)
    d_err = [abs(d.distance_m - math.dist(g.start, g.end)) for d, g in pairs]
    s_err = [abs(d.speed_kmh - g.speed_kmh) for d, g in pairs]
    return {
        "true_passes": len(truth),
        "detected": len(det),
        "matched": len(pairs),
        "recall": round(len(pairs) / max(len(truth), 1), 3),
        "recall_4m_plus": round(long_hits / max(len(long_truth), 1), 3),
        "precision": round(len(pairs) / max(len(det), 1), 3),
        "distance_mae_m": round(statistics.mean(d_err), 2) if d_err else None,
        "speed_mae_kmh": round(statistics.mean(s_err), 2) if s_err else None,
        "speed_median_err_kmh": round(statistics.median(s_err), 2) if s_err else None,
        "completion_accuracy": round(sum(d.completed == g.success for d, g in pairs) / max(len(pairs), 1), 3),
    }


def run(seed: int, storyline: str, minutes: float | None) -> tuple[Capture, list[Detected], dict[str, Any]]:
    cap = capture(seed, storyline)
    end = minutes * 60 if minutes else None
    started = time.perf_counter()
    det = detect(frames(cap, 0, end))
    took = time.perf_counter() - started
    truth = [g for g in cap.passes if end is None or g.t1 < end]
    result = score(det, truth)
    result["frames_per_second_processed"] = round((end or cap.ticks[-1].t) * 10 / took)
    return cap, det, result


CLIP_S = 40


def busiest_window(det: list[Detected], length: float = CLIP_S) -> float:
    """Start time of the window with the most detected passes (a lively clip for the demo)."""
    times = sorted(d.t_release for d in det)
    best, start = 0, 0.0
    for i, t in enumerate(times):
        n = sum(1 for u in times[i:] if u < t + length)
        if n > best:
            best, start = n, max(t - 2, 0.0)
    return start


def write_clip(cap: Capture, det: list[Detected], truth: list[TruthPass], start: float, path: Path) -> None:
    """An annotated clip: each detected pass with its measured distance and speed, next to the truth."""
    from PIL import Image, ImageDraw

    from app.vision.render import FPS, PX_PER_M, H, W

    proc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
         "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "23",
         "-movflags", "+faststart", str(path)],
        stdin=subprocess.PIPE,
    )  # fmt: skip
    pairs = {id(d): g for d, g in match(det, truth)}
    px = lambda p: (p[0] * PX_PER_M, p[1] * PX_PER_M)  # noqa: E731
    prev = None
    for t, frame in frames(cap, start, start + CLIP_S):
        img = Image.fromarray(frame)
        draw = ImageDraw.Draw(img)
        for d in det:
            if d.t_receive <= t <= d.t_receive + 1.6:
                draw.line([px(d.start), px(d.end)], fill=(255, 220, 0), width=3)
                x, y = px(d.end)
                draw.ellipse([x - 4, y - 4, x + 4, y + 4], outline=(255, 220, 0), width=2)
                g = pairs.get(id(d))
                result = "completed" if d.completed else "lost"
                label = f"pass {d.distance_m:.0f} m, {d.speed_kmh:.0f} km/h, {result}"
                truth_label = (
                    f"truth {math.dist(g.start, g.end):.0f} m, {g.speed_kmh:.0f} km/h" if g else "no match"
                )
                box_w = 6 * max(len(label), len(truth_label)) + 8
                lx = x + 6 if x + 6 + box_w < W else x - 6 - box_w  # keep the label inside the frame
                ly = min(max(y - 22, 0), H - 30)
                draw.rectangle([lx, ly, lx + box_w, ly + 30], fill=(0, 0, 0))
                draw.text((lx + 4, ly + 3), label, fill=(255, 220, 0))
                draw.text((lx + 4, ly + 16), truth_label, fill=(190, 190, 190))
        from app.vision.detect import find_ball

        ball = find_ball(frame)
        kmh = math.dist(prev[1], ball) / (t - prev[0]) * 3.6 if prev and ball and t > prev[0] else 0.0
        prev = (t, ball) if ball else prev
        draw.rectangle([8, 8, 330, 30], fill=(0, 0, 0))
        draw.text((14, 13), f"AUTO-EVENTING (from pixels)  ball {kmh:4.0f} km/h", fill=(184, 243, 90))
        assert proc.stdin
        proc.stdin.write(img.tobytes())
    assert proc.stdin
    proc.stdin.close()
    proc.wait()


def publish(cap: Capture, det: list[Detected], result: dict[str, Any], storyline: str, seed: int) -> None:
    """evidence/auto-eventing.md, and the summary and clip the website shows."""
    site = REPO_ROOT / "frontend" / "public" / "vision"
    site.mkdir(parents=True, exist_ok=True)
    start = busiest_window(det)
    result = {
        **result,
        "storyline": storyline,
        "seed": seed,
        "clip_start_s": round(start, 1),
        "clip_s": CLIP_S,
    }
    (site / "summary.json").write_text(json.dumps(result, indent=1), encoding="utf-8")
    if shutil.which("ffmpeg"):
        write_clip(cap, det, cap.passes, start, site / "clip.mp4")
    r = result
    md = f"""# Auto-eventing from video (prototype)

Passes, pass distance and ball speed detected from a synthetic match video, using only the pixels, then
scored against the simulator's ground truth. Generated by `python -m app.vision.evaluate`
(seed {seed}, `{storyline}`).

## How it works

1. **Video.** The simulator moves all 22 players and the ball every 0.5 s. `app/vision/render.py` draws
   that as a top-down tactical-camera video at 10 frames per second: pitch, two kits as coloured discs, a
   white ball, light sensor noise. Detection runs at about {r["frames_per_second_processed"]} frames a second.
2. **Detection** (`app/vision/detect.py`) sees only the frames. The ball is the white blob; the team in
   control is the kit touching the ball while it moves at dribbling speed. A pass is the ball leaving one
   team's control, reaching kicking speed, and being controlled again. Distance and ball speed come from the
   ball's pixel track.
3. **Scoring** (`app/vision/evaluate.py`) matches each detection to a true pass released within 1 s and 3 m.

## Results (full match)

| Metric | Value |
|---|---|
| True passes | {r["true_passes"]} |
| Detected passes | {r["detected"]} |
| Recall (true passes found) | {r["recall"]:.1%} |
| Precision (detections that were real passes) | {r["precision"]:.1%} |
| Pass distance error (mean) | {r["distance_mae_m"]} m |
| Ball speed error (mean / median) | {r["speed_mae_kmh"]} / {r["speed_median_err_kmh"]} km/h |
| Completed vs lost, correct | {r["completion_accuracy"]:.1%} |

## Limits

- The video is synthetic and top-down; real broadcast footage needs a trained detector, camera calibration and
  player identification. The rules allow no real footage, so this is a prototype of the method.
- It identifies the team, not the individual player, and does not detect shots, tackles or set pieces.
- It runs offline on the recorded match; the live pipeline uses the simulator's events.
"""
    (REPO_ROOT / "evidence" / "auto-eventing.md").write_text(md, encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--storyline", default="late_drama")
    ap.add_argument("--minutes", type=float)
    ap.add_argument("--no-publish", action="store_true", help="print the scores only")
    args = ap.parse_args()
    cap, det, result = run(args.seed, args.storyline, args.minutes)
    print(json.dumps(result, indent=1))
    if not args.no_publish:
        publish(cap, det, result, args.storyline, args.seed)


if __name__ == "__main__":
    main()

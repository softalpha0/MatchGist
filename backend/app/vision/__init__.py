"""Auto-eventing prototype: pass and speed metrics detected from a synthetic match video.

``render`` turns the simulator's 0.5 s tracking (22 players + ball) into a top-down tactical-camera video.
``detect`` reads only the pixels and finds passes, their distance and ball speed. ``evaluate`` scores the
detections against the simulator's ground truth. Needs the ``vision`` extra (numpy, pillow).
"""

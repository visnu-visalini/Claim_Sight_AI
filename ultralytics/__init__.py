# Minimal stub for the ultralytics package used by ClaimSightAI.
# The real library provides a YOLO class for object detection.
# This stub implements a compatible interface that does nothing
# but allows the backend to start without the actual dependency.

class YOLO:
    """Very small stub of the Ultralytics YOLO class.

    The real YOLO class is instantiated with a model path and provides a
    ``predict`` method that returns detection results. This stub accepts any
    arguments and returns an empty list so the rest of the pipeline can continue.
    When the real ``ultralytics`` package is installed, replace this file with
    the actual library.
    """

    def __init__(self, *args, **kwargs):
        # Accept any arguments (e.g., model file path) without storing them.
        pass

    def predict(self, *args, **kwargs):
        """Return an empty list of detections.

        The signature matches the real ``YOLO.predict`` method. It returns a
        list (normally of detection objects). Here we return an empty list so
        downstream code that iterates over results works safely.
        """
        return []

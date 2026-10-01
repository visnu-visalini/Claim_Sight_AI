from ultralytics import YOLO


MODEL_PATH = "ai_models/cardd/v2.0/best.pt"

model = YOLO(MODEL_PATH)


def detect_damage(image_path):
    results = model.predict(
        source=image_path,
        conf=0.25,
        verbose=False
    )

    result = results[0]

    detections = []

    for box in result.boxes:
        class_id = int(box.cls[0])
        confidence = float(box.conf[0])

        class_name = model.names[class_id]

        coordinates = box.xyxy[0].tolist()

        detections.append({
            "damage_type": class_name,
            "confidence": confidence,
            "bounding_box": coordinates
        })

    return detections
import cv2
from ultralytics import YOLO
import time
from gemini_lens import analyze_image
#import ocr later

# Load model only once
model = YOLO("yolo11n.pt")
def vision_search(user_prompt):

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        return "Sorry, I couldn't open the webcam."

    countdown = 5
    start_time = time.time()
    captured_frame = None

    while True:

        ret, frame = cap.read()

        if not ret:
            cap.release()
            cv2.destroyAllWindows()
            return "Failed to capture image."

        h, w = frame.shape[:2]

        # Optional guide box
        box_size = 320
        x1 = (w - box_size) // 2
        y1 = (h - box_size) // 2
        x2 = x1 + box_size
        y2 = y1 + box_size

        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        elapsed = int(time.time() - start_time)
        remaining = countdown - elapsed

        if remaining > 0:

            cv2.putText(
                frame,
                f"Capturing in {remaining}",
                (30, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                2,
            )

        else:

            captured_frame = frame.copy()
            image_path = "captured_image.jpg"
            cv2.imwrite(image_path, captured_frame)
            break

        cv2.imshow("Jarvis Vision", frame)

        if cv2.waitKey(1) & 0xFF == 27:
            cap.release()
            cv2.destroyAllWindows()
            return "Vision cancelled."

    cap.release()
    cv2.destroyAllWindows()

    # YOLO Detection
    results = model(captured_frame)

    detected = []

    for box in results[0].boxes:

        cls = int(box.cls[0])
        name = model.names[cls]
        detected.append(name)

    detected = list(set(detected))

    if "person" in detected and len(detected) > 1:
        detected.remove("person")

    if not detected:
        return "I couldn't detect anything. Please try again."

    response = analyze_image("captured_image.jpg", user_prompt)

    return response


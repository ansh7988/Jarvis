import getpass
import face_recognition
import cv2
import os
import webbrowser
from datetime import datetime
from voice import speak
import numpy as np
# -------------------- TTS --------------------

def write_log(message):

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open("login_log.txt", "a") as file:

        file.write(f"[{current_time}] {message}\n")


# -------------------- Load Known Faces --------------------

known_encodings = []
known_names = []

folder = "known_faces"

for file in os.listdir(folder):

    image_path = os.path.join(folder, file)

    image = face_recognition.load_image_file(image_path)

    encodings = face_recognition.face_encodings(image)

    if len(encodings) > 0:

        known_encodings.append(encodings[0])

        known_names.append("Anshdeep Singh")

print("Loaded", len(known_encodings), "face(s)")

# -------------------- Variables --------------------

jarvis_started = False

failed_attempts = 0
MAX_ATTEMPTS = 3

# -------------------- Camera --------------------

cap = cv2.VideoCapture(0)

while True:

    ret, frame = cap.read()

    if not ret:
        break

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    face_locations = face_recognition.face_locations(rgb_frame)

    face_encodings = face_recognition.face_encodings(
        rgb_frame,
        face_locations
    )

    for (top, right, bottom, left), face_encoding in zip(
        face_locations,
        face_encodings
    ):

        matches = face_recognition.compare_faces(
            known_encodings,
            face_encoding,
            tolerance=0.6
        )

        face_distances = face_recognition.face_distance(
            known_encodings,
            face_encoding
        )

        best_match_index = np.argmin(face_distances)

        name = "Unknown"

        if matches[best_match_index] and face_distances[best_match_index] < 0.6:
            name = "Anshdeep"

            speak("Welcome Anshdeep")
            speak("Face verified")

            ...

            # gui_path = os.path.abspath("Jarvis_UI/index.html")
            # webbrowser.open_new_tab(f"file:///{gui_path}")
            import time
            time.sleep(2)
            write_log("AUTHORIZED USER: Anshdeep")

            jarvis_started = True

            break

        else:

            failed_attempts += 1

            print(
                f"Unknown face detected! Attempt {failed_attempts}/{MAX_ATTEMPTS}"
            )

            if failed_attempts >= MAX_ATTEMPTS:

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

                filename = f"intruders/intruder_{timestamp}.jpg"

                cv2.imwrite(filename, frame)

                write_log(f"UNAUTHORIZED USER | Photo Saved: {filename}")

                print(f"Intruder photo saved: {filename}")

                speak("Warning")
                speak("Unauthorized person detected")
                speak("Photo captured")
                speak("Access Denied")

                cap.release()
                cv2.destroyAllWindows()

                exit()

        cv2.rectangle(
            frame,
            (left, top),
            (right, bottom),
            (0, 255, 0),
            2
        )

        cv2.putText(
            frame,
            name,
            (left, top - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )

    if jarvis_started:
        break

    cv2.imshow("Jarvis Face Recognition", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# -------------------- Cleanup --------------------

cap.release()
cv2.destroyAllWindows()

# -------------------- Start Jarvis --------------------

if jarvis_started:

    import subprocess

subprocess.run(["py","login_window.py"])
exit()

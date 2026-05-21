import cv2
import mediapipe as mp
import pygame
import time
import os

from utils.ear import eye_aspect_ratio
from utils.visualization import draw_ui_panel, show_text

from config import (
    EAR_THRESHOLD,
    CLOSED_EYES_FRAME,
    LOG_FILE
)

# ----------------------------------
# CREATE FOLDERS
# ----------------------------------
os.makedirs("screenshots", exist_ok=True)
os.makedirs("logs", exist_ok=True)

# ----------------------------------
# INITIALIZE ALARM
# ----------------------------------
pygame.mixer.init()
pygame.mixer.music.load("alarm.wav")

# ----------------------------------
# MEDIAPIPE SETUP
# ----------------------------------
mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils

# Eye landmarks
LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]

# ----------------------------------
# VARIABLES
# ----------------------------------
counter = 0
blink_count = 0

alarm_on = False

log_written = False

drowsy_start = None

prev_time = 0

fatigue_time = 0

# Screenshot cooldown
last_screenshot_time = 0
SCREENSHOT_COOLDOWN = 10

# ----------------------------------
# START WEBCAM
# ----------------------------------
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not cap.isOpened():
    print("Cannot access webcam")
    exit()

# ----------------------------------
# FACE MESH
# ----------------------------------
with mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
) as face_mesh:

    while True:

        success, frame = cap.read()

        if not success:
            break

        # Mirror effect
        frame = cv2.flip(frame, 1)

        # Convert to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Process Face Mesh
        results = face_mesh.process(rgb_frame)

        h, w = frame.shape[:2]

        # Draw UI panel
        draw_ui_panel(frame)

        # ----------------------------------
        # FACE DETECTION
        # ----------------------------------
        if results.multi_face_landmarks:

            for face_landmarks in results.multi_face_landmarks:

                # ----------------------------------
                # DRAW ONLY EYE MESH
                # ----------------------------------
                mp_drawing.draw_landmarks(
                    frame,
                    face_landmarks,
                    mp_face_mesh.FACEMESH_LEFT_EYE
                )

                mp_drawing.draw_landmarks(
                    frame,
                    face_landmarks,
                    mp_face_mesh.FACEMESH_RIGHT_EYE
                )

                left_eye = []
                right_eye = []

                # ----------------------------------
                # LEFT EYE
                # ----------------------------------
                for idx in LEFT_EYE:

                    x = int(
                        face_landmarks.landmark[idx].x * w
                    )

                    y = int(
                        face_landmarks.landmark[idx].y * h
                    )

                    left_eye.append((x, y))

                    cv2.circle(
                        frame,
                        (x, y),
                        2,
                        (0, 255, 0),
                        -1
                    )

                # ----------------------------------
                # RIGHT EYE
                # ----------------------------------
                for idx in RIGHT_EYE:

                    x = int(
                        face_landmarks.landmark[idx].x * w
                    )

                    y = int(
                        face_landmarks.landmark[idx].y * h
                    )

                    right_eye.append((x, y))

                    cv2.circle(
                        frame,
                        (x, y),
                        2,
                        (0, 255, 0),
                        -1
                    )

                # ----------------------------------
                # FACE BOUNDING BOX
                # ----------------------------------
                x_min = int(
                    min(
                        [lm.x for lm in face_landmarks.landmark]
                    ) * w
                )

                y_min = int(
                    min(
                        [lm.y for lm in face_landmarks.landmark]
                    ) * h
                )

                x_max = int(
                    max(
                        [lm.x for lm in face_landmarks.landmark]
                    ) * w
                )

                y_max = int(
                    max(
                        [lm.y for lm in face_landmarks.landmark]
                    ) * h
                )

                cv2.rectangle(
                    frame,
                    (x_min, y_min),
                    (x_max, y_max),
                    (255, 0, 0),
                    2
                )

                # ----------------------------------
                # EAR CALCULATION
                # ----------------------------------
                leftEAR = eye_aspect_ratio(left_eye)

                rightEAR = eye_aspect_ratio(right_eye)

                ear = (
                    leftEAR + rightEAR
                ) / 2.0

                # ----------------------------------
                # DROWSINESS DETECTION
                # ----------------------------------
                if ear < EAR_THRESHOLD:

                    counter += 1

                    if drowsy_start is None:

                        drowsy_start = time.time()

                    fatigue_time = (
                        time.time() - drowsy_start
                    )

                    # Eyes closed too long
                    if counter >= CLOSED_EYES_FRAME:

                        # ALERT BOX
                        cv2.rectangle(
                            frame,
                            (70, 60),
                            (620, 130),
                            (0, 0, 255),
                            -1
                        )

                        cv2.putText(
                            frame,
                            "DROWSINESS DETECTED!",
                            (100, 110),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1,
                            (255, 255, 255),
                            3
                        )

                        # PLAY ALARM
                        if not alarm_on:

                            pygame.mixer.music.play(-1)

                            alarm_on = True

                        # SCREENSHOT COOLDOWN
                        current_time = time.time()

                        if (
                            current_time
                            - last_screenshot_time
                            > SCREENSHOT_COOLDOWN
                        ):

                            timestamp = time.strftime(
                                "%Y%m%d_%H%M%S"
                            )

                            filename = (
                                f"screenshots/"
                                f"drowsy_{timestamp}.jpg"
                            )

                            cv2.imwrite(
                                filename,
                                frame
                            )

                            last_screenshot_time = (
                                current_time
                            )

                        # WRITE LOG ONLY ONCE
                        if not log_written:

                            with open(
                                LOG_FILE,
                                "a"
                            ) as f:

                                f.write(
                                    f"Drowsiness "
                                    f"detected at "
                                    f"{time.ctime()}\n"
                                )

                            log_written = True

                else:

                    # BLINK DETECTION
                    if counter >= 2:

                        blink_count += 1

                    counter = 0

                    drowsy_start = None

                    fatigue_time = 0

                    log_written = False

                    # STOP ALARM
                    if alarm_on:

                        pygame.mixer.music.stop()

                        alarm_on = False

                # ----------------------------------
                # FPS
                # ----------------------------------
                current_time = time.time()

                fps = int(
                    1 / max(
                        current_time - prev_time,
                        0.001
                    )
                )

                prev_time = current_time

                # ----------------------------------
                # DISPLAY TEXT
                # ----------------------------------
                show_text(
                    frame,
                    f"EAR: {ear:.2f}",
                    (20, 40),
                    (255, 255, 255)
                )

                show_text(
                    frame,
                    f"Blinks: {blink_count}",
                    (20, 75),
                    (0, 255, 255)
                )

                show_text(
                    frame,
                    f"Fatigue: "
                    f"{fatigue_time:.1f}s",
                    (20, 110),
                    (0, 255, 0)
                )

                show_text(
                    frame,
                    f"FPS: {fps}",
                    (20, 145),
                    (255, 0, 255)
                )

        # ----------------------------------
        # SHOW WINDOW
        # ----------------------------------
        cv2.imshow(
            "Driver Drowsiness Detection",
            frame
        )

        # PRESS Q TO QUIT
        if cv2.waitKey(1) & 0xFF == ord("q"):

            break

# ----------------------------------
# RELEASE RESOURCES
# ----------------------------------
cap.release()

cv2.destroyAllWindows()
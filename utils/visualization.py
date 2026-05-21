import cv2

def draw_ui_panel(frame):

    cv2.rectangle(
        frame,
        (10, 10),
        (320, 170),
        (40, 40, 40),
        -1
    )

def show_text(frame, text, position, color):

    cv2.putText(
        frame,
        text,
        position,
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        color,
        2
    )
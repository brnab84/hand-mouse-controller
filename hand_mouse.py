"""
Hand Gesture Mouse Controller
Requiere: pip install mediapipe opencv-python-headless pynput numpy
"""

import cv2
import mediapipe as mp
import numpy as np
import time
from pynput.mouse import Button, Controller as MouseController
from pynput.mouse import Controller

mouse = Controller()

# --- Config ---
SMOOTHING = 5
CLICK_THRESHOLD = 0.04
DEAD_ZONE = 10
SCROLL_SPEED = 5

# Obtener resolución de pantalla
try:
    import subprocess
    out = subprocess.check_output("xrandr | grep '*' | awk '{print $1}'", shell=True).decode().strip().split('\n')[0]
    screen_w, screen_h = map(int, out.split('x'))
except:
    screen_w, screen_h = 1920, 1080

print(f"Resolución detectada: {screen_w}x{screen_h}")

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

pos_buffer = []
prev_x, prev_y = 0, 0
click_cooldown = 0
scroll_cooldown = 0

def get_distance(p1, p2):
    return np.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2)

def smooth_position(x, y, buffer, size=SMOOTHING):
    buffer.append((x, y))
    if len(buffer) > size:
        buffer.pop(0)
    return int(np.mean([p[0] for p in buffer])), int(np.mean([p[1] for p in buffer]))

def count_fingers_up(lm):
    tips = [8, 12, 16, 20]
    fingers = [1 if lm[4].x < lm[3].x else 0]
    for tip in tips:
        fingers.append(1 if lm[tip].y < lm[tip - 2].y else 0)
    return fingers

def main():
    global prev_x, prev_y, click_cooldown, scroll_cooldown

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    with mp_hands.Hands(
        max_num_hands=1,
        min_detection_confidence=0.75,
        min_tracking_confidence=0.75
    ) as hands:

        print("=" * 50)
        print("  HAND MOUSE CONTROLLER - Activo")
        print("=" * 50)
        print("  Gestos:")
        print("  • Índice extendido     → Mover mouse")
        print("  • Pulgar + Índice      → Click izquierdo")
        print("  • Índice + Medio       → Click derecho")
        print("  • Puño cerrado         → Arrastrar")
        print("  • 4 dedos arriba       → Scroll")
        print("  • ESC / Q              → Salir")
        print("=" * 50)

        dragging = False

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)
            h, w = frame.shape[:2]
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = hands.process(rgb)

            status_text = "Sin mano"
            color = (100, 100, 100)

            if result.multi_hand_landmarks:
                lm = result.multi_hand_landmarks[0].landmark
                mp_draw.draw_landmarks(frame, result.multi_hand_landmarks[0], mp_hands.HAND_CONNECTIONS)

                fingers = count_fingers_up(lm)
                finger_count = sum(fingers)

                ix = int(lm[8].x * w)
                iy = int(lm[8].y * h)

                margin = 0.15
                mx = int(np.interp(lm[8].x, [margin, 1 - margin], [0, screen_w]))
                my = int(np.interp(lm[8].y, [margin, 1 - margin], [0, screen_h]))
                mx, my = smooth_position(mx, my, pos_buffer)

                d_thumb_index = get_distance(lm[4], lm[8])
                d_index_middle = get_distance(lm[8], lm[12])
                now = time.time()

                # MOVER
                if fingers == [0, 1, 0, 0, 0]:
                    dx = abs(mx - prev_x)
                    dy = abs(my - prev_y)
                    if dx > DEAD_ZONE or dy > DEAD_ZONE:
                        mouse.position = (mx, my)
                        prev_x, prev_y = mx, my
                    if dragging:
                        mouse.release(Button.left)
                        dragging = False
                    status_text = "Moviendo"
                    color = (0, 255, 0)

                # CLICK IZQUIERDO
                elif d_thumb_index < CLICK_THRESHOLD and fingers[1] == 1:
                    if now - click_cooldown > 0.4:
                        mouse.click(Button.left)
                        click_cooldown = now
                    status_text = "Click Izq"
                    color = (0, 200, 255)

                # CLICK DERECHO
                elif fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 0 and d_index_middle < CLICK_THRESHOLD:
                    if now - click_cooldown > 0.4:
                        mouse.click(Button.right)
                        click_cooldown = now
                    status_text = "Click Der"
                    color = (0, 100, 255)

                # ARRASTRAR
                elif finger_count == 0:
                    if not dragging:
                        mouse.press(Button.left)
                        dragging = True
                    mouse.position = (mx, my)
                    prev_x, prev_y = mx, my
                    status_text = "Arrastrando"
                    color = (255, 0, 100)

                # SCROLL
                elif fingers == [0, 1, 1, 1, 1]:
                    if now - scroll_cooldown > 0.15:
                        if lm[8].y < 0.4:
                            mouse.scroll(0, SCROLL_SPEED)
                        elif lm[8].y > 0.6:
                            mouse.scroll(0, -SCROLL_SPEED)
                        scroll_cooldown = now
                    status_text = "Scroll"
                    color = (255, 200, 0)

                else:
                    if dragging:
                        mouse.release(Button.left)
                        dragging = False

                cv2.circle(frame, (ix, iy), 10, color, -1)

            cv2.rectangle(frame, (0, 0), (300, 35), (0, 0, 0), -1)
            cv2.putText(frame, f"Estado: {status_text}", (10, 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

            cv2.imshow("Hand Mouse Controller", frame)

            key = cv2.waitKey(1) & 0xFF
            if key in [27, ord('q')]:
                break

    if dragging:
        mouse.release(Button.left)
    cap.release()
    cv2.destroyAllWindows()
    print("Cerrado.")

if __name__ == "__main__":
    main()

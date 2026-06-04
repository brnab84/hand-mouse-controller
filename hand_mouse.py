"""
Hand Gesture Mouse Controller
Requiere: pip install mediapipe opencv-python pyautogui numpy
No necesita TensorFlow directamente - MediaPipe ya incluye los modelos de mano
"""

import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import time

# --- Config ---
SMOOTHING = 5           # Suavizado del movimiento (más alto = más suave pero más lento)
CLICK_THRESHOLD = 0.04  # Distancia para detectar click (pulgar-índice)
SCROLL_THRESHOLD = 0.05 # Distancia para scroll (índice-medio separados)
DEAD_ZONE = 10          # Pixeles de zona muerta para evitar micro-movimientos

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

screen_w, screen_h = pyautogui.size()

# Buffer para suavizado
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
    avg_x = int(np.mean([p[0] for p in buffer]))
    avg_y = int(np.mean([p[1] for p in buffer]))
    return avg_x, avg_y

def count_fingers_up(lm):
    """Cuenta dedos extendidos"""
    tips = [8, 12, 16, 20]  # Índice, Medio, Anular, Meñique
    fingers = []
    # Pulgar (eje X)
    fingers.append(1 if lm[4].x < lm[3].x else 0)
    # Resto de dedos (eje Y)
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

                # Posición del índice (tip)
                ix = int(lm[8].x * w)
                iy = int(lm[8].y * h)

                # Mapear a pantalla (margen del 15%)
                margin = 0.15
                mx = np.interp(lm[8].x, [margin, 1 - margin], [0, screen_w])
                my = np.interp(lm[8].y, [margin, 1 - margin], [0, screen_h])
                mx, my = smooth_position(int(mx), int(my), pos_buffer)

                # Distancias clave
                d_thumb_index = get_distance(lm[4], lm[8])
                d_index_middle = get_distance(lm[8], lm[12])

                now = time.time()

                # --- GESTOS ---

                # MOVER: solo índice extendido
                if fingers == [0, 1, 0, 0, 0]:
                    dx = abs(mx - prev_x)
                    dy = abs(my - prev_y)
                    if dx > DEAD_ZONE or dy > DEAD_ZONE:
                        pyautogui.moveTo(mx, my)
                        prev_x, prev_y = mx, my
                    if dragging:
                        pyautogui.mouseUp()
                        dragging = False
                    status_text = "Moviendo"
                    color = (0, 255, 0)

                # CLICK IZQUIERDO: pulgar + índice juntos
                elif d_thumb_index < CLICK_THRESHOLD and fingers[1] == 1:
                    if now - click_cooldown > 0.4:
                        pyautogui.click()
                        click_cooldown = now
                    status_text = "Click Izq"
                    color = (0, 200, 255)

                # CLICK DERECHO: índice + medio extendidos y juntos
                elif fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 0 and d_index_middle < CLICK_THRESHOLD:
                    if now - click_cooldown > 0.4:
                        pyautogui.rightClick()
                        click_cooldown = now
                    status_text = "Click Der"
                    color = (0, 100, 255)

                # ARRASTRAR: puño cerrado
                elif finger_count == 0:
                    if not dragging:
                        pyautogui.mouseDown()
                        dragging = True
                    pyautogui.moveTo(mx, my)
                    prev_x, prev_y = mx, my
                    status_text = "Arrastrando"
                    color = (255, 0, 100)

                # SCROLL: 4 dedos arriba (sin pulgar)
                elif fingers == [0, 1, 1, 1, 1]:
                    if now - scroll_cooldown > 0.15:
                        # Mano arriba = scroll up, abajo = scroll down
                        if lm[8].y < 0.4:
                            pyautogui.scroll(3)
                        elif lm[8].y > 0.6:
                            pyautogui.scroll(-3)
                        scroll_cooldown = now
                    status_text = "Scroll"
                    color = (255, 200, 0)

                # Soltar arrastre si no es puño
                else:
                    if dragging:
                        pyautogui.mouseUp()
                        dragging = False

                # Dibujar punto en índice
                cv2.circle(frame, (ix, iy), 10, color, -1)

            # UI en pantalla
            cv2.rectangle(frame, (0, 0), (300, 35), (0, 0, 0), -1)
            cv2.putText(frame, f"Estado: {status_text}", (10, 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

            cv2.imshow("Hand Mouse Controller", frame)

            key = cv2.waitKey(1) & 0xFF
            if key in [27, ord('q')]:
                break

    if dragging:
        pyautogui.mouseUp()
    cap.release()
    cv2.destroyAllWindows()
    print("Cerrado.")

if __name__ == "__main__":
    main()

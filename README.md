# 🖐️ Hand Mouse Controller

Control your mouse using hand gestures via webcam — no physical mouse needed.

Built with **MediaPipe** + **OpenCV** + **PyAutoGUI**.

---

## 📋 Requirements

- Python 3.8+
- Webcam

## ⚙️ Installation

```bash
git clone https://github.com/TU_USUARIO/hand-mouse-controller.git
cd hand-mouse-controller
pip install -r requirements.txt
```

## 🚀 Run

```bash
python hand_mouse.py
```

Press `Q` or `ESC` to exit.

---

## 🤌 Gestures

| Gesture | Action |
|---------|--------|
| ☝️ Index finger only | Move mouse |
| 🤌 Thumb + index pinch | Left click |
| ✌️ Index + middle pinch | Right click |
| ✊ Closed fist | Drag |
| 🖐️ 4 fingers (no thumb) | Scroll ↑↓ |

> **Tip:** Keep your hand centered in frame, good lighting improves tracking accuracy.

---

## 🗂️ Project Structure

```
hand-mouse-controller/
├── hand_mouse.py       # Main script
├── requirements.txt    # Dependencies
└── README.md
```

## 📦 Dependencies

| Package | Purpose |
|---------|---------|
| `mediapipe` | Hand landmark detection |
| `opencv-python` | Webcam capture & display |
| `pyautogui` | Mouse/keyboard control |
| `numpy` | Coordinate math & smoothing |

---

## 🛠️ Configuration

Edit these values at the top of `hand_mouse.py` to tune behavior:

```python
SMOOTHING = 5           # Higher = smoother but slower
CLICK_THRESHOLD = 0.04  # Lower = needs tighter pinch to click
SCROLL_THRESHOLD = 0.05
DEAD_ZONE = 10          # Pixels — reduces micro-jitter
```

## 📄 License

MIT

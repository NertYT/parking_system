import cv2
import mysql.connector
import time
import re
import os
import threading
import queue
import requests
import datetime
import difflib
import numpy as np
from collections import Counter
from flask import Flask, Response
from ultralytics import YOLO

os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp|fflags;nobuffer|flags;low_delay"

app = Flask(__name__)

# ================= НАСТРОЙКИ =================
DB_CONFIG = {
    'host': 'localhost', 'user': 'root', 'password': '', 'database': 'parking_system'
}
RTSP_URL = "rtsp://admin:admin@192.168.0.105:554/live/ch0"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SNAPSHOTS_DIR = os.path.join(BASE_DIR, "snapshots")

# ================= ИНИЦИАЛИЗАЦИЯ МОДЕЛЕЙ =================
print("[INFO] Загрузка моделей...")
plate_model = YOLO('best.pt')                          # детектор номера
char_model  = YOLO('best_rus.pt')   # ← новая OCR модель
print("[INFO] Все модели загружены успешно.")

# ================= МАППИНГ КЛАССОВ =================
# Новая модель обучена с именами классов напрямую:
# '0'-'9' — цифры, 'A','B','C','E','H','K','M','O','P','T','X','Y' — буквы (латиница)

# Перевод латиницы → кириллица для записи в БД
EN_TO_RU = str.maketrans("ABCEHKMOPTXY", "АВСЕНКМОРТХУ")

output_frame = None
frame_lock = threading.Lock()
log_queue = queue.Queue()


# ================= ЛОГИКА ОБРАБОТКИ ТЕКСТА =================
def positional_fix(raw_chars):
    """
    Позиционная коррекция для РФ номера: Б ЦЦЦ ББ ЦЦ(Ц)
    Позиции: 0=буква, 1-3=цифры, 4-5=буквы, 6-7(8)=цифры региона.
    """
    letter_to_digit = {
        'O': '0', 'C': '0', 'Q': '0', 'D': '0',
        'B': '8', 'S': '5', 'T': '7',
        'I': '1', 'L': '1', 'G': '6',
    }
    digit_to_letter = {
        '0': 'O', '8': 'B', '4': 'A',
        '5': 'S', '1': 'I', '6': 'G',
    }
    fixed = []
    for i, char in enumerate(raw_chars):
        if i in (1, 2, 3) or i >= 6:      # зона цифр
            fixed.append(letter_to_digit.get(char, char))
        elif i in (0, 4, 5):               # зона букв
            fixed.append(digit_to_letter.get(char, char))
        else:
            fixed.append(char)
    return "".join(fixed)


def get_plate_text(crop):
    """Извлекает текст номера из кропа изображения."""

    # Увеличиваем кроп — помогает на мелких и размытых номерах
    crop = cv2.resize(crop, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)

    # conf=0.15 — чтобы не терять буквы с низкой уверенностью (особенно B/В)
    res = char_model.predict(crop, imgsz=640, conf=0.15, verbose=False)

    boxes = res[0].boxes
    if boxes is None or len(boxes) == 0:
        return ""

    detected = []
    for box in boxes:
        coords   = box.xywh[0].cpu().numpy()
        cls_idx  = int(box.cls[0].item())
        char     = char_model.names.get(cls_idx, None)

        if char is None:
            print(f"[WARN] Неизвестный класс: idx={cls_idx}")
            continue

        detected.append({
            'x':    coords[0],
            'y':    coords[1],
            'w':    coords[2],
            'h':    coords[3],
            'conf': box.conf[0].item(),
            'char': char,
        })

    if not detected:
        return ""

    # NMS по X: убираем дубли близких детекций, оставляем более уверенную
    detected.sort(key=lambda d: d['conf'], reverse=True)
    final_detected = []
    for d in detected:
        keep = True
        for f in final_detected:
            if abs(d['x'] - f['x']) < max(d['w'], f['w']) * 0.4:
                keep = False
                break
        if keep:
            final_detected.append(d)

    # Фильтр по Y: убираем артефакты выше/ниже строки номера
    if len(final_detected) > 3:
        ys = [d['y'] for d in final_detected]
        median_y = sorted(ys)[len(ys) // 2]
        avg_h = sum(d['h'] for d in final_detected) / len(final_detected)
        final_detected = [d for d in final_detected if abs(d['y'] - median_y) < avg_h * 0.6]

    # Сортировка слева направо
    final_detected.sort(key=lambda d: d['x'])

    raw_chars = [d['char'] for d in final_detected]

    print(f"[OCR] raw: {''.join(raw_chars)}  conf: {[round(d['conf'],2) for d in final_detected]}")

    if len(raw_chars) < 6:
        return ""

    return positional_fix(raw_chars)


# ================= РАБОТА С БД И ШЛАГБАУМОМ =================
def process_db_logic(plate_en, full_frame):
    try:
        plate_ru = plate_en.translate(EN_TO_RU)
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT plate_number FROM allowed_cars WHERE is_active = 1")
        allowed_cars = [row['plate_number'] for row in cursor.fetchall()]

        matches = difflib.get_close_matches(plate_ru, allowed_cars, n=1, cutoff=0.8)
        status = 'access_granted' if matches else 'access_denied'
        final_plate = matches[0] if matches else plate_ru

        date_folder = datetime.datetime.now().strftime('%d.%m.%Y')
        path_to_save = os.path.join(SNAPSHOTS_DIR, date_folder)
        os.makedirs(path_to_save, exist_ok=True)
        filename = f"{final_plate}_{datetime.datetime.now().strftime('%H%M%S')}.jpg"
        cv2.imwrite(os.path.join(path_to_save, filename), full_frame)

        db_path = f"{date_folder}/{filename}"
        cursor.execute(
            "INSERT INTO entry_logs (plate_number, status, snapshot_path) VALUES (%s, %s, %s)",
            (final_plate, status, db_path)
        )
        conn.commit()

        if status == 'access_granted':
            print(f" >>> [OPEN] Доступ разрешен: {final_plate}")
            # requests.get("http://192.168.0.200/relay?state=1", timeout=1)
        else:
            print(f" >>> [CLOSED] Доступ запрещен: {final_plate}")

    except Exception as e:
        print(f"[ERROR DB]: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            conn.close()


def db_worker():
    while True:
        plate, frame = log_queue.get()
        process_db_logic(plate, frame)
        log_queue.task_done()


# ================= ГЛАВНЫЙ ЦИКЛ ВИДЕО =================
def process_video():
    global output_frame
    cap = cv2.VideoCapture(RTSP_URL)
    track_history = {}
    last_logged_time = {}
    frame_count = 0

    print("[INFO] Видеопоток запущен.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[WARN] Переподключение к потоку...")
            cap.release()
            time.sleep(1)
            cap = cv2.VideoCapture(RTSP_URL)
            continue

        frame_count += 1
        display_frame = frame.copy()

        results = plate_model.track(frame, persist=True, conf=0.5, verbose=False)

        if results[0].boxes.id is not None:
            boxes     = results[0].boxes.xyxy.cpu().numpy()
            track_ids = results[0].boxes.id.int().cpu().tolist()

            for box, track_id in zip(boxes, track_ids):
                x1, y1, x2, y2 = map(int, box)

                crop = frame[max(0, y1 - 5):min(frame.shape[0], y2 + 5),
                             max(0, x1 - 5):min(frame.shape[1], x2 + 5)]

                if frame_count % 5 == 0:
                    text = get_plate_text(crop)
                    if len(text) >= 6:
                        if track_id not in track_history:
                            track_history[track_id] = []
                        track_history[track_id].append(text)
                        if len(track_history[track_id]) > 20:
                            track_history[track_id] = track_history[track_id][-20:]

                if track_id in track_history and track_history[track_id]:
                    stable_text = Counter(track_history[track_id]).most_common(1)[0][0]
                    # Переводим в кириллицу только для отображения
                    display_text = stable_text.translate(EN_TO_RU)

                    cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(display_frame, display_text, (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                    if len(track_history[track_id]) >= 3:
                        now = time.time()
                        if now - last_logged_time.get(stable_text, 0) > 15:
                            log_queue.put((stable_text, frame.copy()))
                            last_logged_time[stable_text] = now

        if frame_count % 100 == 0:
            current_ids = (results[0].boxes.id.int().tolist()
                           if results[0].boxes.id is not None else [])
            track_history = {k: v for k, v in track_history.items() if k in current_ids}

        with frame_lock:
            output_frame = display_frame.copy()


# ================= FLASK & RUN =================
@app.route('/video_feed')
def video_feed():
    def gen():
        while True:
            with frame_lock:
                if output_frame is None:
                    continue
                _, buffer = cv2.imencode('.jpg', output_frame)
                yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n'
                       + buffer.tobytes() + b'\r\n')
            time.sleep(0.04)
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/')
def index():
    return "<h1>ANPR Barrier System Running</h1><a href='/video_feed'>Watch Stream</a>"


if __name__ == '__main__':
    os.makedirs(SNAPSHOTS_DIR, exist_ok=True)
    threading.Thread(target=db_worker, daemon=True).start()
    threading.Thread(target=process_video, daemon=True).start()
    app.run(host='0.0.0.0', port=5000, threaded=True)
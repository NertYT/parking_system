import argparse
import os
import time
import threading
import datetime
from collections import Counter
from typing import List, Dict, Any

import cv2
import torch
import torch.nn as nn
from torchvision import transforms
from ultralytics import YOLO
import torch.ao.quantization.quantize_fx as quantize_fx
from torch.ao.quantization import QConfigMapping
import numpy as np
import mysql.connector
from mysql.connector import Error
from flask import Flask, Response

# --- ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ---
# outputFrame: хранит последний обработанный кадр для передачи в браузер
outputFrame = None
# lock: обеспечивает потокобезопасность при записи/чтении кадра
lock = threading.Lock()

# Инициализация веб-сервера
app = Flask(__name__)

# --- КОНФИГУРАЦИЯ ---
class Config:
    # Пути к моделям
    YOLO_MODEL_PATH: str = 'models/yolo/model/best.pt'
    OCR_MODEL_PATH: str = 'models/ocr_crnn/quant/crnn_ocr_model_int8_fx.pth'
   
    # Параметры для OCR
    OCR_IMG_HEIGHT: int = 32
    OCR_IMG_WIDTH: int = 128
    OCR_ALPHABET: str = '0123456789ABCEHKMOPTXYАВСЕНКМОРТХУ'
   
    # Порог уверенности детектора
    DETECTION_CONFIDENCE_THRESHOLD: float = 0.5
   
    # Устройство (GPU если есть, иначе CPU)
    DEVICE: torch.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    # Настройки Базы Данных
    DB_HOST = "localhost"
    DB_USER = "root"
    DB_PASSWORD = ""
    DB_NAME = "parking_system"
    
    # Папка для сохранения фото
    SNAPSHOTS_DIR = "snapshots"

# --- МОДЕЛЬ НЕЙРОСЕТИ (CRNN) ---
# Этот класс необходим для загрузки весов OCR модели
class CRNN(nn.Module):
    def __init__(self, num_classes):
        super(CRNN, self).__init__()
        # CNN (Сверточная сеть для извлечения признаков)
        self.cnn = nn.Sequential(
            nn.Conv2d(1, 64, kernel_size=3, padding=1), nn.ReLU(True), nn.MaxPool2d(2, 2),
            nn.Conv2d(64, 128, kernel_size=3, padding=1), nn.ReLU(True), nn.MaxPool2d(2, 2),
            nn.Conv2d(128, 256, kernel_size=3, padding=1), nn.BatchNorm2d(256), nn.ReLU(True),
            nn.Conv2d(256, 256, kernel_size=3, padding=1), nn.ReLU(True), nn.MaxPool2d((2, 1), (2, 1)),
            nn.Conv2d(256, 512, kernel_size=3, padding=1), nn.BatchNorm2d(512), nn.ReLU(True),
            nn.Conv2d(512, 512, kernel_size=3, padding=1), nn.ReLU(True), nn.MaxPool2d((2, 1), (2, 1))
        )
        # RNN (Рекуррентная сеть для анализа последовательности символов)
        self.rnn = nn.LSTM(512 * 2, 256, bidirectional=True, num_layers=2, batch_first=True)
        # Классификатор
        self.classifier = nn.Linear(512, num_classes)

    def forward(self, x):
        x = self.cnn(x)
        batch, channels, height, width = x.size()
        x = x.reshape(batch, channels * height, width)
        x = x.permute(0, 2, 1) # [batch, width, features]
        x, _ = self.rnn(x)
        x = self.classifier(x)
        x = x.permute(1, 0, 2) # [width, batch, num_classes]
        return nn.functional.log_softmax(x, dim=2)

# --- КЛАСС ДЛЯ РАБОТЫ С YOLO (Поиск номера) ---
class YOLODetector:
    def __init__(self, model_path: str, device: torch.device):
        print(f"Загрузка YOLO из {model_path}...")
        self.model = YOLO(model_path)
        self.model.to(device)
        self.device = device

    def track(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        # persist=True сохраняет ID объектов между кадрами
        detections = self.model.track(frame, persist=True, verbose=False, device=self.device)
        results = []
        
        if detections[0].boxes.id is None:
            return results
           
        track_ids = detections[0].boxes.id.int().cpu().tolist()
        boxes = detections[0].boxes.xyxy.cpu().numpy()
        confs = detections[0].boxes.conf.cpu().numpy()
        
        for box, track_id, conf in zip(boxes, track_ids, confs):
            if conf >= Config.DETECTION_CONFIDENCE_THRESHOLD:
                results.append({
                    "bbox": [int(b) for b in box],
                    "confidence": float(conf),
                    "track_id": track_id
                })
        return results

# --- КЛАСС ДЛЯ РАБОТЫ С OCR (Чтение текста) ---
class CRNNRecognizer:
    def __init__(self, model_path: str, device: torch.device):
        print(f"Загрузка OCR (INT8) из {model_path}...")
        self.device = device
        self.transform = transforms.Compose([
            transforms.ToPILImage(), transforms.Grayscale(),
            transforms.Resize((Config.OCR_IMG_HEIGHT, Config.OCR_IMG_WIDTH)),
            transforms.ToTensor(), transforms.Normalize(mean=[0.5], std=[0.5])
        ])
        self.int_to_char = {i + 1: char for i, char in enumerate(Config.OCR_ALPHABET)}
        self.int_to_char[0] = ''
       
        # Подготовка модели для квантования (ускорения)
        num_classes = len(Config.OCR_ALPHABET) + 1
        model_to_load = CRNN(num_classes).eval()
        
        qconfig_mapping = QConfigMapping().set_global(torch.ao.quantization.get_default_qconfig('fbgemm'))
        example_inputs = (torch.randn(1, 1, Config.OCR_IMG_HEIGHT, Config.OCR_IMG_WIDTH),)
        model_prepared = quantize_fx.prepare_fx(model_to_load, qconfig_mapping, example_inputs)
        model_quantized = quantize_fx.convert_fx(model_prepared)
       
        # Загрузка весов
        model_quantized.load_state_dict(torch.load(model_path, map_location=device))
        self.model = model_quantized

    @torch.no_grad()
    def recognize(self, plate_image: np.ndarray) -> str:
        if plate_image.size == 0: return ""
        preprocessed = self.transform(plate_image).unsqueeze(0).to(self.device)
        preds = self.model(preprocessed)
        return self._decode(preds)

    def _decode(self, preds: torch.Tensor) -> str:
        preds = preds.permute(1, 0, 2).argmax(dim=2)[0]
        decoded_seq = []
        last_char_idx = 0
        for char_idx in preds:
            char_idx = char_idx.item()
            if char_idx != 0 and char_idx != last_char_idx:
                decoded_seq.append(self.int_to_char.get(char_idx, ''))
            last_char_idx = char_idx
        return "".join(decoded_seq)

# --- ФУНКЦИИ БАЗЫ ДАННЫХ И ЛОГИРОВАНИЯ ---
def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME
        )
        return conn
    except Error as e:
        print(f"Ошибка подключения к БД: {e}")
        return None

def normalize_plate(plate: str) -> str:
    """Заменяет латиницу на кириллицу для корректного поиска в БД"""
    latin_to_rus = {'A':'А','B':'В','C':'С','E':'Е','H':'Н','K':'К','M':'М','O':'О','P':'Р','T':'Т','X':'Х','Y':'У'}
    return "".join([latin_to_rus.get(c, c) for c in plate.upper()])

def log_plate_event(plate_text, frame_cutout):
    """
    1. Проверяет номер в БД.
    2. Создает папку с текущей датой.
    3. Сохраняет фото.
    4. Записывает событие в MySQL.
    """
    conn = get_db_connection()
    if not conn: return
    
    clean_plate = normalize_plate(plate_text)
    is_allowed = False
    
    try:
        cursor = conn.cursor()
        # Проверка белого списка
        cursor.execute("SELECT 1 FROM allowed_cars WHERE plate_number = %s", (clean_plate,))
        if cursor.fetchone():
            is_allowed = True
            
        status = "access_granted" if is_allowed else "access_denied"
        
        # --- ЛОГИКА СОЗДАНИЯ ПАПОК ---
        # Получаем дату в формате 18.12.2025
        date_folder_name = datetime.datetime.now().strftime('%d.%m.%Y')
        
        # Полный путь к папке на диске: snapshots/18.12.2025
        full_folder_path = os.path.join(Config.SNAPSHOTS_DIR, date_folder_name)
        
        # Если папки нет, создаем
        if not os.path.exists(full_folder_path):
            os.makedirs(full_folder_path)
        
        # Имя файла: A777AA77_123055.jpg
        filename = f"{clean_plate}_{datetime.datetime.now().strftime('%H%M%S')}.jpg"
        
        # Полный путь для сохранения (OS зависимый)
        file_save_path = os.path.join(full_folder_path, filename)
        cv2.imwrite(file_save_path, frame_cutout)
        
        # Путь для базы данных (должен быть с прямыми слешами для браузера)
        # snapshots/18.12.2025/filename.jpg
        db_path = f"{Config.SNAPSHOTS_DIR}/{date_folder_name}/{filename}"
        
        # Запись в БД
        query = "INSERT INTO entry_logs (plate_number, status, snapshot_path) VALUES (%s, %s, %s)"
        cursor.execute(query, (clean_plate, status, db_path))
        conn.commit()
        
        print(f"LOG: {clean_plate} -> {status} | Фото: {db_path}")
        
    except Error as e:
        print(f"SQL Error: {e}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

# --- КОНВЕЙЕР ОБРАБОТКИ (PIPELINE) ---
class ANPR_Pipeline:
    def __init__(self, recognizer):
        self.recognizer = recognizer
        self.track_history = {} # История распознаваний для стабилизации
        self.last_logged = {}   # Таймштампы последних логов, чтобы не спамить

    def process_frame(self, frame: np.ndarray, detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            
            # Вырезаем область номера с отступом
            h, w, _ = frame.shape
            pad = 5
            ny1, ny2 = max(0, y1-pad), min(h, y2+pad)
            nx1, nx2 = max(0, x1-pad), min(w, x2+pad)
            
            plate_img = frame[ny1:ny2, nx1:nx2]
            
            # Распознаем текст
            raw_text = self.recognizer.recognize(plate_img).strip()
            final_text = raw_text
            
            # Стабилизация текста (Voting) по Track ID
            track_id = det.get('track_id')
            if track_id is not None:
                if track_id not in self.track_history:
                    self.track_history[track_id] = []
                
                self.track_history[track_id].append(raw_text)
                # Храним последние 10 кадров
                if len(self.track_history[track_id]) > 10:
                    self.track_history[track_id].pop(0)
                
                # Выбираем самый частый вариант
                counts = Counter(self.track_history[track_id])
                if counts:
                    final_text = counts.most_common(1)[0][0]
            
            det['text'] = final_text
            
            # Логирование
            if len(final_text) >= 6: # Минимальная длина номера
                now = time.time()
                # Логируем только если прошло 15 секунд с последней записи этого номера
                if now - self.last_logged.get(final_text, 0) > 15.0:
                    # Запускаем в отдельном потоке, чтобы не тормозить видео
                    threading.Thread(target=log_plate_event, args=(final_text, plate_img)).start()
                    self.last_logged[final_text] = now

        return detections

# --- ОТРИСОВКА РЕЗУЛЬТАТОВ ---
def draw_results(frame, results):
    for res in results:
        x1, y1, x2, y2 = res['bbox']
        text = res.get('text', '')
        conf = res.get('confidence', 0)
        
        # Зеленая рамка
        color = (0, 255, 0)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        
        # Текст над рамкой
        label = f"{text}"
        (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.9, 2)
        cv2.rectangle(frame, (x1, y1 - 30), (x1 + w, y1), color, -1)
        cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 2)
    return frame

# --- ПОТОК ОБРАБОТКИ ВИДЕО ---
def video_processing_thread(source):
    global outputFrame, lock
    
    # Инициализация моделей
    try:
        detector = YOLODetector(Config.YOLO_MODEL_PATH, Config.DEVICE)
        recognizer = CRNNRecognizer(Config.OCR_MODEL_PATH, Config.DEVICE)
        pipeline = ANPR_Pipeline(recognizer)
    except Exception as e:
        print(f"Критическая ошибка загрузки моделей: {e}")
        return

    # Подключение к камере или файлу
    src = int(source) if source.isdigit() else source
    # CAP_DSHOW ускоряет запуск веб-камеры на Windows
    cap = cv2.VideoCapture(src, cv2.CAP_DSHOW) if isinstance(src, int) else cv2.VideoCapture(src)
    
    if not cap.isOpened():
        print(f"Ошибка открытия источника: {source}")
        return

    print(f"🎥 Трансляция и обработка запущены: {source}")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            # Если это файл, начинаем сначала
            if isinstance(src, str): 
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            else:
                print("Потеря соединения с камерой.")
                break
        
        # 1. Детекция и трекинг (YOLO)
        detections = detector.track(frame)
        
        # 2. Распознавание и логика (Pipeline)
        results = pipeline.process_frame(frame, detections)
        
        # 3. Отрисовка
        vis_frame = frame.copy()
        vis_frame = draw_results(vis_frame, results)
        
        # 4. Обновление кадра для веб-сервера
        with lock:
            outputFrame = vis_frame.copy()
            
        # Небольшая задержка для разгрузки CPU
        time.sleep(0.01)

    cap.release()

# --- ГЕНЕРАТОР ДЛЯ FLASK ---
def generate_mjpeg():
    """Генерирует поток кадров в формате MJPEG для браузера"""
    global outputFrame, lock
    while True:
        with lock:
            if outputFrame is None:
                continue
            # Кодируем кадр в JPEG
            (flag, encodedImage) = cv2.imencode(".jpg", outputFrame)
            if not flag:
                continue
        
        # Отправляем кадр как часть multipart ответа
        yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encodedImage) + b'\r\n')
        # Ограничиваем частоту отправки в браузер (~25-30 FPS)
        time.sleep(0.04)

# --- МАРШРУТЫ FLASK ---
@app.route("/video_feed")
def video_feed():
    # Этот URL вставляется в <img src="..."> в PHP
    return Response(generate_mjpeg(), mimetype = "multipart/x-mixed-replace; boundary=frame")

@app.route("/")
def index():
    return "Python AI Server is running. Video stream is at <a href='/video_feed'>/video_feed</a>"

# --- ТОЧКА ВХОДА ---
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default='0', help="ID веб-камеры (0) или путь к видеофайлу")
    args = parser.parse_args()
    
    # 1. Запускаем обработку видео в отдельном потоке
    t = threading.Thread(target=video_processing_thread, args=(args.source,))
    t.daemon = True # Поток закроется при закрытии скрипта
    t.start()
    
    # 2. Запускаем Flask веб-сервер
    print("🚀 Сервер запущен. Видео доступно по адресу: http://localhost:5000/video_feed")
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True, use_reloader=False)
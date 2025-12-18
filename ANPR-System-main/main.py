import cv2
import mysql.connector
import easyocr
import time
import re

# ================= НАСТРОЙКИ =================

# 1. Настройки Базы Данных
DB_CONFIG = {
    'host': 'localhost',
    'user': 'admin',         # Ваш логин phpMyAdmin
    'password': 'admin',         # Ваш пароль phpMyAdmin
    'database': 'parking_system'
}

# 2. Настройки Камеры (RTSP поток)
# Формат обычно: rtsp://admin:password@192.168.1.XX:554/stream
RTSP_URL = 0 

# 3. Настройки распознавания
MIN_AREA = 500  # Минимальная площадь номера (чтобы не ловить мусор)
CONFIDENCE_THRESHOLD = 0.4 # Уверенность OCR (от 0 до 1), ниже этого игнорируем

# ================= ИНИЦИАЛИЗАЦИЯ =================

print("[INFO] Загрузка модели OCR (это может занять время)...")
reader = easyocr.Reader(['ru', 'en'], gpu=False) # gpu=True, если есть видеокарта NVIDIA

print("[INFO] Загрузка каскада Хаара...")
plate_cascade = cv2.CascadeClassifier('haarcascade_russian_plate_number.xml')

# Функция очистки текста (убираем скобки, пробелы, оставляем только буквы и цифры)
def clean_plate_text(text):
    return re.sub(r'[^A-ZА-Я0-9]', '', text.upper())

# Функция открытия шлагбаума (Заглушка)
def open_barrier():
    print(">>> СИГНАЛ НА ОТКРЫТИЕ ШЛАГБАУМА ОТПРАВЛЕН <<<")
    # Здесь будет код для реле (об этом ниже)
    time.sleep(5) # Держим открытым 5 секунд

# Функция проверки в БД
def check_db(plate_number):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        # Запрос: есть ли такой номер и активен ли он?
        query = "SELECT * FROM allowed_cars WHERE plate_number = %s AND is_active = 1"
        cursor.execute(query, (plate_number,))
        result = cursor.fetchone()
        
        # Логируем попытку (опционально)
        log_query = "INSERT INTO entry_logs (plate_number, status) VALUES (%s, %s)"
        status = 'access_granted' if result else 'access_denied'
        cursor.execute(log_query, (plate_number, status))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return True if result else False

    except mysql.connector.Error as err:
        print(f"[ERROR] Ошибка БД: {err}")
        return False

# ================= ГЛАВНЫЙ ЦИКЛ =================

print(f"[INFO] Подключение к камере: {RTSP_URL}")
cap = cv2.VideoCapture(RTSP_URL)

if not cap.isOpened():
    print("[ERROR] Не удалось подключиться к камере. Проверьте RTSP ссылку.")
    exit()

# Переменная чтобы не спамить запросами к БД каждую миллисекунду
last_checked_plate = ""
last_check_time = 0

while True:
    ret, frame = cap.read()
    if not ret:
        print("[ERROR] Поток прерван. Попытка переподключения...")
        # Проверяем, был ли исходный URL строкой (RTSP), чтобы пытаться переподключиться
        if isinstance(RTSP_URL, str):
            cap.open(RTSP_URL)
        else:
            # Если это веб-камера (int), то, вероятно, произошла серьезная ошибка.
            print("[FATAL] Ошибка чтения веб-камеры. Выход.")
            break 
        time.sleep(2)
        continue

    # 1. Подготовка изображения (перевод в ч/б для поиска рамки)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # 2. Поиск прямоугольников номеров
    plates = plate_cascade.detectMultiScale(gray, 1.1, 4)

    for (x, y, w, h) in plates:
        area = w * h
        if area > MIN_AREA:
            # Рисуем рамку вокруг номера на видео
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
            # Вырезаем кусочек с номером (ROI - Region of Interest)
            plate_img = frame[y:y+h, x:x+w]
            
            # 3. Распознавание текста (OCR)
            # detail=0 возвращает просто список найденных строк
            result = reader.readtext(plate_img, detail=0) 
            
            if result:
                full_text = "".join(result)
                cleaned_text = clean_plate_text(full_text)
                
                # Простая фильтрация: номер должен быть длиннее 5 символов
                if len(cleaned_text) >= 6:
                    # Текст на экране
                    cv2.putText(frame, cleaned_text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36,255,12), 2)
                    
                    # Проверяем, не проверяли ли мы эту машину только что (защита от спама)
                    current_time = time.time()
                    if cleaned_text != last_checked_plate or (current_time - last_check_time) > 10:
                        
                        print(f"[INFO] Распознан номер: {cleaned_text}")
                        
                        # 4. Проверка в БД
                        allowed = check_db(cleaned_text)
                        
                        if allowed:
                            print(f"[ACCESS] Доступ РАЗРЕШЕН для {cleaned_text}")
                            open_barrier()
                        else:
                            print(f"[ACCESS] Доступ ЗАПРЕЩЕН для {cleaned_text}")
                        
                        last_checked_plate = cleaned_text
                        last_check_time = current_time

    #Показываем видео  # <-- Эта часть вызывает ошибку
    # cv2.resize можно использовать, если видео 4к и не влезает в экран
    # cv2.imshow("Parking Camera System", frame)

    # Нажмите 'q' для выхода
    # if cv2.waitKey(1) & 0xFF == ord('q'):
    #     break

    # Вместо этого — просто задержка, чтобы цикл не жрал 100% CPU
    time.sleep(0.033)  # ~30 FPS, регулируйте по вкусу (0.01 для быстрее, 0.1 для медленнее)

cap.release()
cv2.destroyAllWindows()
from ultralytics import YOLO
import cv2
import sys
from pathlib import Path

if __name__ == '__main__':

    # Загрузка моделей
    plate_detector = YOLO('best.pt')
    char_detector  = YOLO('best_rus.pt')

    # Маппинг латиница → кириллица
    LAT_TO_CYR = {
        'A':'А', 'B':'В', 'C':'С', 'E':'Е',
        'H':'Н', 'K':'К', 'M':'М', 'O':'О',
        'P':'Р', 'T':'Т', 'X':'Х', 'Y':'У'
    }

    # Путь к фото
    image_path = sys.argv[1] if len(sys.argv) > 1 else r'C:\Users\Admin\Desktop\plate\duster1.jpg'

    if not Path(image_path).exists():
        print(f"Файл не найден: {image_path}")
        sys.exit(1)

    frame = cv2.imread(image_path)
    output = frame.copy()

    # 1. Детектируем номерные знаки
    plates = plate_detector(frame)[0]

    if len(plates.boxes) == 0:
        print("Номера не найдены")
        sys.exit(0)

    print(f"Найдено номеров: {len(plates.boxes)}\n")

    for i, box in enumerate(plates.boxes):
        x1, y1, x2, y2 = map(int, box.xyxy[0])

        # Небольшой отступ вокруг номера для надёжности
        pad = 5
        x1 = max(0, x1 - pad)
        y1 = max(0, y1 - pad)
        x2 = min(frame.shape[1], x2 + pad)
        y2 = min(frame.shape[0], y2 + pad)

        crop = frame[y1:y2, x1:x2]

        # Увеличиваем кроп — помогает на мелких номерах
        scale = 2.0
        crop_big = cv2.resize(crop, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

        # 2. Детектируем символы — порог 0.15 чтобы не терять буквы
        chars = char_detector(crop_big, conf=0.15)[0]

        # --- ДИАГНОСТИКА ---
        print(f"  [Номер {i+1}] Найдено символов (conf>0.15): {len(chars.boxes)}")
        for b in chars.boxes:
            cls  = int(b.cls[0])
            conf = float(b.conf[0])
            label = char_detector.names[cls]
            print(f"    символ={label}  conf={conf:.3f}")
        print()

        # 3. Сортировка слева направо
        detections = []
        for b in chars.boxes:
            cx   = float(b.xywh[0][0])
            cls  = int(b.cls[0])
            conf = float(b.conf[0])
            detections.append((cx, cls, conf))
        detections.sort(key=lambda x: x[0])

        # 4. Фильтрация дублей — если два bbox слишком близко, берём с большим conf
        filtered = []
        for det in detections:
            if filtered and abs(det[0] - filtered[-1][0]) < 15 * scale:
                # Оставляем тот у кого conf выше
                if det[2] > filtered[-1][2]:
                    filtered[-1] = det
            else:
                filtered.append(det)

        # 5. Собираем текст
        plate_lat = ''.join(char_detector.names[d[1]] for d in filtered)
        plate_cyr = ''.join(LAT_TO_CYR.get(c, c) for c in plate_lat)
        confs     = [round(d[2], 2) for d in filtered]

        print(f"  Номер {i+1}: {plate_cyr}  (latin: {plate_lat})")
        print(f"  Confidence символов: {confs}\n")

        # 6. Рисуем bbox номера и текст на итоговом фото
        cv2.rectangle(output, (x1, y1), (x2, y2), (0, 255, 0), 2)

        # Фон под текст чтобы было читаемо
        text = plate_cyr
        (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1.2, 2)
        cv2.rectangle(output, (x1, y1 - th - 14), (x1 + tw, y1), (0, 255, 0), -1)
        cv2.putText(output, text, (x1, y1 - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 2)

        # 7. Рисуем bbox символов на увеличенном кропе
        crop_out = crop_big.copy()
        for b in chars.boxes:
            bx1, by1, bx2, by2 = map(int, b.xyxy[0])
            cls  = int(b.cls[0])
            conf = float(b.conf[0])
            label = char_detector.names[cls]
            color = (0, 255, 0) if conf >= 0.4 else (0, 165, 255)  # зелёный / оранжевый
            cv2.rectangle(crop_out, (bx1, by1), (bx2, by2), color, 2)
            cv2.putText(crop_out, f"{label} {conf:.2f}", (bx1, by1 - 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 1)

        # Сохраняем кроп
        crop_path = f'crop_{i+1}_{plate_lat}.jpg'
        cv2.imwrite(crop_path, crop_out)
        print(f"  → кроп сохранён: {crop_path}")

    # Сохраняем итоговое фото
    out_path = f'result_{Path(image_path).stem}.jpg'
    cv2.imwrite(out_path, output)
    print(f"\nРезультат сохранён: {out_path}")

    cv2.imshow('Result', output)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
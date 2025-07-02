import cv2
import json

def draw_labels_on_video(video_path, json_path):
    # Video yakalayıcıyı başlat
    video_capture = cv2.VideoCapture(video_path)
    if not video_capture.isOpened():
        raise ValueError("Video açılamadı")

    with open(json_path, 'r') as f:
        data = json.load(f)

    # Video özelliklerini al
    fps = video_capture.get(cv2.CAP_PROP_FPS)
    width = int(video_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Etiketleri timestamp'e göre grupla
    labels_by_timestamp = {}
    for item in data['Labels']:
        timestamp = item.get('Timestamp', 0)
        label_info = item.get('Label', {})
        name = label_info.get('Name', 'Unknown')
        instances = label_info.get('Instances', [])
        if timestamp not in labels_by_timestamp:
            labels_by_timestamp[timestamp] = []
        labels_by_timestamp[timestamp].append({
            'name': name,
            'instances': instances
        })

    current_labels = []  # En sonki aktif etiketler

    while True:
        ret, frame = video_capture.read()
        if not ret:
            break

        current_time_ms = video_capture.get(cv2.CAP_PROP_POS_MSEC)
        current_timestamp = int(current_time_ms)

        # Eğer yeni bir timestamp varsa güncelle
        if current_timestamp in labels_by_timestamp:
            current_labels = labels_by_timestamp[current_timestamp]

        # Mevcut aktif etiketleri çiz
        y_offset = 30
        for label in current_labels:
            name = label['name']
            instances = label['instances']
            if instances:
                for inst in instances:
                    box = inst.get('BoundingBox', None)
                    if box:
                        x1 = int(box['Left'] * width)
                        y1 = int(box['Top'] * height)
                        x2 = x1 + int(box['Width'] * width)
                        y2 = y1 + int(box['Height'] * height)

                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(frame, name, (x1, y1 - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            else:
                cv2.putText(frame, name, (10, y_offset),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                y_offset += 30

        # Frame'i JPEG'e dönüştür
        ret, jpeg = cv2.imencode('.jpg', frame)
        if not ret:
            break
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')

    video_capture.release()
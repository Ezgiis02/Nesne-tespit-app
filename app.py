from flask import Flask, request, jsonify, render_template, Response
from flask_cors import CORS
import os
from mongo_handler import MongoDBHandler
from s3_uploader import upload_video_to_s3
from rekognition_handler import start_label_detection, get_label_detection_result, save_result_to_file
from video_drawer import draw_labels_on_video
import atexit
import signal
import sys

app = Flask(__name__)
CORS(app)

# Yapılandırma
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# MongoDB bağlantısı
mongo_handler = MongoDBHandler()

# Global değişkenler
current_video_path = None
current_json_path = None

def cleanup(signum=None, frame=None):
    """Kaynakları temizle ve bağlantıyı kapat"""
    try:
        if mongo_handler:
            mongo_handler.close_connection()
        print("\nKaynaklar temizlendi, uygulama kapatılıyor...")
    except Exception as e:
        print(f"Temizleme sırasında hata: {e}")
    
    if signum is not None:
        sys.exit(0)
    

# Çıkış sinyallerini yakala
atexit.register(cleanup)
signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    global current_video_path, current_json_path
    
    if 'video' not in request.files:
        return jsonify({"error": "Video dosyası bulunamadı"}), 400

    file = request.files['video']
    if file.filename == '':
        return jsonify({"error": "Dosya seçilmedi"}), 400

    try:
        video_filename = file.filename
        video_path = os.path.join(UPLOAD_FOLDER, video_filename)
        file.save(video_path)

        # AWS işlemleri
        bucket_name = 'video-akisi-bucket'
        s3_key = video_filename
        json_filename = os.path.splitext(video_filename)[0] + '_labels.json'
        json_path = os.path.join(UPLOAD_FOLDER, json_filename)

        upload_video_to_s3(video_path, bucket_name, s3_key)
        job_id = start_label_detection(bucket_name, s3_key)
        result = get_label_detection_result(job_id)
        save_result_to_file(result, json_path)

        # MongoDB'ye kaydet
        mongo_id = mongo_handler.save_analysis_results(video_filename, json_path)

        # Global değişkenleri güncelle
        current_video_path = video_path
        current_json_path = json_path

        return jsonify({
            "success": True,
            "message": "İşlem başarıyla tamamlandı",
            "mongo_id": str(mongo_id)
        })

    except Exception as e:
        return jsonify({
            "error": str(e),
            "message": "İşlem sırasında hata oluştu"
        }), 500

@app.route('/video_feed')
def video_feed():
    global current_video_path, current_json_path
    
    if not current_video_path or not current_json_path:
        return jsonify({"error": "Video veya etiket dosyası bulunamadı"}), 404

    try:
        return Response(
            draw_labels_on_video(current_video_path, current_json_path),
            mimetype='multipart/x-mixed-replace; boundary=frame'
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/results')
def get_all_results():
    try:
        results = mongo_handler.get_results()
        return jsonify({
            "success": True,
            "results": results
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/results/<video_name>')
def get_single_result(video_name):
    try:
        result = mongo_handler.get_results(video_name=video_name)
        if result:
            return jsonify({
                "success": True,
                "result": result
            })
        return jsonify({
            "success": False,
            "message": "Sonuç bulunamadı"
        }), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    try:
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            use_reloader=False
        )
    except Exception as e:
        print(f"Uygulama hatası: {e}")
    finally:
        cleanup()
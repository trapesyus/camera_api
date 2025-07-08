from flask import Flask, request, jsonify, send_from_directory
import subprocess, signal, os, uuid

app = Flask(__name__)
VIDEO_DIR = os.path.join(os.getcwd(), 'videos')
os.makedirs(VIDEO_DIR, exist_ok=True)

# Global değişken kayıt sürecini tutar
proc = None
current_name = None

@app.route('/api/start', methods=['POST'])
def start_record():
    global proc, current_name
    if proc:
        return jsonify(status='already_running'), 400

    # Rastgele isim üret (örn. 'a1b2c3d4e5f6')
    current_name = uuid.uuid4().hex
    h264_path = os.path.join(VIDEO_DIR, f"{current_name}.h264")

    cmd = [
        'libcamera-vid',
        '--codec', 'h264', '--inline',
        '--width', '1920', '--height', '1080', '--framerate', '30',
        '--sharpness', '1', '--denoise', 'cdn_off',
        '-o', h264_path
    ]
    proc = subprocess.Popen(cmd)
    return jsonify(status='started', file=f"{current_name}.h264")

@app.route('/api/stop', methods=['POST'])
def stop_record():
    global proc, current_name
    if not proc:
        return jsonify(status='not_running'), 400

    # Kayıt işlemini durdur
    proc.send_signal(signal.SIGINT)
    proc.wait()
    proc = None

    # H.264 dosyasını MP4'e dönüştür
    h264_file = os.path.join(VIDEO_DIR, f"{current_name}.h264")
    mp4_file  = os.path.join(VIDEO_DIR, f"{current_name}.mp4")
    subprocess.run([
        'ffmpeg', '-y',
        '-i', h264_file,
        '-c:v', 'copy',
        mp4_file
    ], check=True)

    # Dilersen .h264 dosyasını silebilirsin:
    # os.remove(h264_file)

    # Yanıt olarak MP4 dosyasının adını ver
    resp_name = f"{current_name}.mp4"
    current_name = None
    return jsonify(status='stopped', file=resp_name)

@app.route('/api/videos', methods=['GET'])
def list_videos():
    files = [f for f in os.listdir(VIDEO_DIR) if f.endswith('.mp4')]
    return jsonify(files)

@app.route('/api/videos/<filename>', methods=['GET'])
def serve_video(filename):
    return send_from_directory(VIDEO_DIR, filename, as_attachment=False, conditional=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

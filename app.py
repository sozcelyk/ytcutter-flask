import os
import re
import subprocess
import tempfile
from flask import Flask, request, send_file, render_template_string
import urllib.parse

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8">
  <title>YT Cutter Basit Arayüz</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body { font-family: system-ui, sans-serif; background: #f6f6f9; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
    .ytcutter-box { background: #fff; padding: 2rem 2.5rem 2rem 2.5rem; border-radius: 1.5rem; box-shadow: 0 4px 24px 0 rgba(0,0,0,0.07); min-width: 330px; display: flex; flex-direction: column; gap: 1.1rem; align-items: stretch; }
    .ytcutter-box h1 { font-size: 1.35rem; font-weight: bold; margin-bottom: 0.6rem; color: #222; text-align: center; }
    label { font-size: 1rem; color: #444; margin-bottom: 0.2rem; }
    input[type="text"] { width: 100%; padding: 0.55rem; font-size: 1rem; border: 1px solid #d0d0da; border-radius: 0.7rem; margin-bottom: 0.4rem; background: #f9f9fc; }
    .input-row { display: flex; gap: 0.7rem; }
    .input-row > div { flex: 1 1 0; }
    button { margin-top: 0.4rem; padding: 0.8rem 0; background: #e72a2a; color: #fff; border: none; border-radius: 0.8rem; font-size: 1.1rem; font-weight: bold; cursor: pointer; transition: background 0.19s; letter-spacing: 0.05em; }
    button:hover { background: #b91d1d; }
  </style>
</head>
<body>
  <form class="ytcutter-box" autocomplete="off" method="POST">
    <h1>YT Cutter</h1>
    <label for="yt-url">YouTube Video Linki</label>
    <input type="text" id="yt-url" name="url" placeholder="https://www.youtube.com/watch?v=..." autocomplete="off" required>
    <div class="input-row">
      <div>
        <label for="start">Başlangıç (mm:ss)</label>
        <input type="text" id="start" name="start" pattern="^([0-9]{1,3}):([0-5][0-9])$" placeholder="örn: 65:14" title="Dakika ve saniye olarak girin (mm:ss)" required>
      </div>
      <div>
        <label for="end">Bitiş (mm:ss)</label>
        <input type="text" id="end" name="end" pattern="^([0-9]{1,3}):([0-5][0-9])$" placeholder="örn: 67:25" title="Dakika ve saniye olarak girin (mm:ss)" required>
      </div>
    </div>
    <button type="submit">Download</button>
  </form>
</body>
</html>
"""

def mmss_to_seconds(mmss):
    m, s = mmss.split(':')
    return int(m) * 60 + int(s)

def clean_yt_url(url):
    parsed = urllib.parse.urlparse(url)
    q = urllib.parse.parse_qs(parsed.query)
    video_id = q.get('v', [''])[0]
    return f"https://www.youtube.com/watch?v={video_id}" if video_id else url

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return render_template_string(HTML)
    url = request.form.get('url')
    start = request.form.get('start')
    end = request.form.get('end')
    # Validasyon
    if not url or not start or not end or not re.match(r'^\d{1,3}:[0-5][0-9]$', start) or not re.match(r'^\d{1,3}:[0-5][0-9]$', end):
        return "Hatalı giriş.", 400
    start_sec = mmss_to_seconds(start)
    end_sec = mmss_to_seconds(end)
    duration = end_sec - start_sec
    if duration <= 0:
        return "Bitiş, başlangıçtan büyük olmalı.", 400

    cleaned_url = clean_yt_url(url)

    with tempfile.TemporaryDirectory() as tmpdir:
        video_path = os.path.join(tmpdir, 'input.webm')
        output_path = os.path.join(tmpdir, f'output_{start_sec}_{end_sec}.mp4')
        # Videoyu indir (format seçmeden)
        yt_dlp_cmd = [
            'yt-dlp',
            cleaned_url,
            '-o', video_path
        ]
        try:
            subprocess.run(yt_dlp_cmd, check=True)
        except Exception as e:
            return f"Video indirilemedi: {e}", 500
        # Kırp
        ffmpeg_cmd = [
            'ffmpeg',
            '-ss', str(start_sec),
            '-t', str(duration),
            '-i', video_path,
            '-y',
            '-c', 'copy',
            output_path
        ]
        try:
            subprocess.run(ffmpeg_cmd, check=True)
        except Exception as e:
            return f"ffmpeg hatası: {e}", 500
        # İndir
        return send_file(output_path, as_attachment=True, download_name=f'ytcutter_{start_sec}_{end_sec}.mp4')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

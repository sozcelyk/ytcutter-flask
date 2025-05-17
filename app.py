import subprocess
from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    try:
        result = subprocess.run(
            ["yt-dlp", "https://www.youtube.com/watch?v=N8HLxbAcMy0"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        return "<pre>" + result.stdout + "\n" + result.stderr + "</pre>"
    except Exception as e:
        return f"Hata: {e}"

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

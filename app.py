from flask import Flask

app = Flask(__name__)

@app.get("/")
def home():
    return """
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>Zero W Game</title>
      <style>
        body { font-family: system-ui, sans-serif; background: #101820; color: #f0f4f8;
               min-height: 100vh; margin: 0; display: grid; place-items: center; text-align: center; }
        main { padding: 32px; }
        button { background: #86efac; border: 0; border-radius: 8px; padding: 14px 24px;
                 font-size: 18px; cursor: pointer; }
      </style>
    </head>
    <body>
      <main>
        <h1>Raspberry Pi Zero W</h1>
        <p>Game server is online.</p>
        <p id="score">Clicks: 0</p>
        <button onclick="document.getElementById('score').textContent='Clicks: '+(++window.count)">Click me</button>
      </main>
      <script>window.count = 0;</script>
    </body>
    </html>
    """

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)

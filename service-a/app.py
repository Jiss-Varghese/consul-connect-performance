from flask import Flask
import requests

app = Flask(__name__)

SERVICE_B_URL = "http://127.0.0.1:22000"


@app.route("/health")
def health():
    return "Service A is healthy"


@app.route("/api")
def api():
    response = requests.get(
        f"{SERVICE_B_URL}/api",
        timeout=5
    )

    return f"Service A received: {response.text}"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
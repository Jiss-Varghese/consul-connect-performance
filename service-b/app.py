from flask import Flask

app = Flask(__name__)


@app.route("/health")
def health():
    return "Service B is healthy"


@app.route("/api")
def api():
    return "Response from Service B"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)


   
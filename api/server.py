from flask import Flask, jsonify, request

app = Flask(__name__)


@app.route("/api/add-idea", methods=["POST"])
def add_idea():
    data = request.json
    print("📩 Received from Chrome:", data)
    return jsonify({"status": "ok", "received": data}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

#!/usr/bin/env python3
import json
import os

from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/trending", methods=["GET"])
def get_trending():
    path = os.path.join(os.path.dirname(__file__), "logs/github_trending.json")
    if not os.path.exists(path):
        return jsonify({"error": "No trending data found"}), 404
    with open(path, "r") as f:
        data = json.load(f)
    return jsonify(data)


@app.route("/code", methods=["GET"])
def get_code():
    path = os.path.join(os.path.dirname(__file__), "logs/github_code_stats.json")
    if not os.path.exists(path):
        return jsonify({"error": "No code stats found"}), 404
    with open(path, "r") as f:
        data = json.load(f)
    return jsonify(data)


if __name__ == "__main__":
    port = int(os.getenv("TREND_API_PORT", "5050"))
    app.run(host="0.0.0.0", port=port)

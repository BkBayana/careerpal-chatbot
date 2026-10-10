"""
CareerPal - Flask web application for the Career Assistant chatbot.

Run:
    pip install -r requirements.txt
    python app.py
Then open http://127.0.0.1:5000 in Google Chrome or Microsoft Edge
(needed for voice input via the Web Speech API).
"""

import os
import uuid

from flask import Flask, jsonify, render_template, request, session

from chatbot import CareerBot

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "careerpal-dev-secret-change-me")

bot = CareerBot()
STATES = {}  # session id -> conversation state (in-memory, fine for a demo / single server)


def get_state():
    sid = session.get("sid")
    if not sid or sid not in STATES:
        sid = sid or uuid.uuid4().hex
        session["sid"] = sid
        STATES[sid] = bot.new_state()
    return STATES[sid]


@app.route("/")
def index():
    return render_template("index.html")


@app.get("/api/welcome")
def welcome():
    get_state()
    return jsonify(bot.welcome())


@app.post("/api/chat")
def chat():
    payload = request.get_json(silent=True) or {}
    message = str(payload.get("message", ""))
    state = get_state()
    return jsonify(bot.reply(message, state))


@app.post("/api/reset")
def reset():
    sid = session.get("sid")
    if sid:
        STATES[sid] = bot.new_state()
    return jsonify(bot.welcome())


@app.get("/api/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="127.0.0.1", port=port, debug=True)

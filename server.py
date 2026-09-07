from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

OPENROUTER_KEY = os.environ.get("OPENROUTER_KEY", "")
GROQ_KEY = os.environ.get("GROQ_KEY", "")

PRO_MODEL = "anthropic/claude-haiku-4.5"
GROQ_MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = "You are CodeMate, an AI coding assistant. Give detailed, thorough answers with clear explanations and code examples when relevant. Don't be overly brief."


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True)
    message = data.get("message", "")
    history = data.get("history", [])
    tier = data.get("tier", "free")

    if not message.strip():
        return jsonify({"error": "empty message"}), 400

    is_pro = tier == "pro"
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history + [{"role": "user", "content": message}]

    try:
        if is_pro:
            reply = call_openrouter(messages)
        else:
            reply = call_groq(messages)
        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def call_openrouter(messages):
    if not OPENROUTER_KEY:
        raise RuntimeError("server misconfigured: missing OPENROUTER_KEY")

    payload = {
        "model": PRO_MODEL,
        "messages": messages,
        "plugins": [{"id": "web", "max_results": 3}]
    }

    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_KEY}",
            "Content-Type": "application/json"
        },
        json=payload,
        timeout=60
    )
    result = resp.json()
    return result["choices"][0]["message"]["content"]


def call_groq(messages):
    if not GROQ_KEY:
        raise RuntimeError("server misconfigured: missing GROQ_KEY")

    payload = {
        "model": GROQ_MODEL,
        "messages": messages
    }

    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_KEY}",
            "Content-Type": "application/json"
        },
        json=payload,
        timeout=30
    )
    result = resp.json()
    return result["choices"][0]["message"]["content"]


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

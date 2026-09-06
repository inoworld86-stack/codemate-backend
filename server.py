from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

OPENROUTER_KEY = os.environ.get("OPENROUTER_KEY", "")
FREE_MODEL = "poolside/laguna-xs-2.1:free"
PRO_MODEL = "anthropic/claude-haiku-4.5"

SYSTEM_PROMPT = "You are CodeMate, an AI coding assistant. Give detailed, thorough answers with clear explanations and code examples when relevant. Don't be overly brief."

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True)
    message = data.get("message", "")
    history = data.get("history", [])
    tier = data.get("tier", "free")

    if not message.strip():
        return jsonify({"error": "empty message"}), 400
    if not OPENROUTER_KEY:
        return jsonify({"error": "server misconfigured: missing OPENROUTER_KEY"}), 500

    is_pro = tier == "pro"
    model = PRO_MODEL if is_pro else FREE_MODEL
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history + [{"role": "user", "content": message}]

    payload = {"model": model, "messages": messages}
    if is_pro:
        payload["plugins"] = [{"id": "web", "max_results": 3}]

    try:
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
        reply = result["choices"][0]["message"]["content"]
        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

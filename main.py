import os
import logging
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from alerts.gmail_sender import send_signal_alert

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

REQUIRED_FIELDS = {"symbol", "action", "price", "secret"}
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")


def parse_signal(data: dict) -> dict | None:
    missing = REQUIRED_FIELDS - data.keys()
    if missing:
        logger.warning(f"Signal rejected — missing fields: {missing}")
        return None

    if data["secret"] != WEBHOOK_SECRET:
        logger.warning("Signal rejected — invalid secret")
        return None

    action = data["action"].upper()
    if action not in ("BUY", "SELL"):
        logger.warning(f"Signal rejected — unknown action: {data['action']}")
        return None

    return {
        "symbol": str(data["symbol"]).upper(),
        "action": action,
        "price": float(data["price"]),
    }


@app.route("/webhook", methods=["POST"])
def webhook():
    if not WEBHOOK_SECRET:
        logger.error("WEBHOOK_SECRET not set in .env — refusing all requests")
        return jsonify({"status": "error", "message": "server misconfigured"}), 500

    data = request.get_json(silent=True)

    if not data:
        logger.warning("Received empty or non-JSON payload")
        return jsonify({"status": "error", "message": "invalid payload"}), 400

    logger.info(f"Raw signal received: { {k: v for k, v in data.items() if k != 'secret'} }")

    signal = parse_signal(data)
    if signal is None:
        return jsonify({"status": "error", "message": "invalid signal"}), 400

    logger.info(f"Signal accepted: {signal}")

    email_sent = send_signal_alert(signal)
    if not email_sent:
        logger.warning("Signal processed but email notification failed")

    return jsonify({"status": "ok", "signal": signal}), 200


def main():
    print("AegisTradeAI starting...")
    logger.info("Starting webhook server on port 5000")
    app.run(host="0.0.0.0", port=5000, debug=False)


if __name__ == "__main__":
    main()
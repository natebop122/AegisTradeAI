import os
import csv
import logging
import traceback
from datetime import datetime
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from alerts.gmail_sender import send_signal_alert, send_error_alert

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

REQUIRED_FIELDS = {"symbol", "action", "price", "secret"}
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "signals.csv")
CSV_HEADERS = ["timestamp", "symbol", "action", "price", "status", "reason"]


def ensure_log_file():
    os.makedirs(LOG_DIR, exist_ok=True)
    if not os.path.isfile(LOG_FILE):
        with open(LOG_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADERS)


def log_signal(symbol: str, action: str, price, status: str, reason: str = ""):
    ensure_log_file()
    with open(LOG_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.utcnow().isoformat(),
            symbol,
            action,
            price,
            status,
            reason,
        ])


def parse_signal(data: dict) -> dict | None:
    missing = REQUIRED_FIELDS - data.keys()
    if missing:
        logger.warning(f"Signal rejected — missing fields: {missing}")
        log_signal(
            data.get("symbol", ""), data.get("action", ""), data.get("price", ""),
            "rejected", f"missing fields: {missing}"
        )
        return None

    if data["secret"] != WEBHOOK_SECRET:
        logger.warning("Signal rejected — invalid secret")
        log_signal(
            data.get("symbol", ""), data.get("action", ""), data.get("price", ""),
            "rejected", "invalid secret"
        )
        return None

    action = data["action"].upper()
    if action not in ("BUY", "SELL"):
        logger.warning(f"Signal rejected — unknown action: {data['action']}")
        log_signal(
            data.get("symbol", ""), action, data.get("price", ""),
            "rejected", f"unknown action: {data['action']}"
        )
        return None

    return {
        "symbol": str(data["symbol"]).upper(),
        "action": action,
        "price": float(data["price"]),
    }


@app.route("/webhook", methods=["POST"])
def webhook():
    try:
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
        log_signal(signal["symbol"], signal["action"], signal["price"], "accepted")

        email_sent = send_signal_alert(signal)
        if not email_sent:
            logger.warning("Signal processed but email notification failed")

        return jsonify({"status": "ok", "signal": signal}), 200

    except Exception:
        error_text = traceback.format_exc()
        logger.error("Unhandled exception in webhook:")
        logger.error(error_text)
        send_error_alert(error_text, context="webhook endpoint")
        return jsonify({"status": "error", "message": "internal server error"}), 500


def main():
    print("AegisTradeAI starting...")
    logger.info("Starting webhook server on port 5000")
    app.run(host="0.0.0.0", port=5000, debug=False)


if __name__ == "__main__":
    main()
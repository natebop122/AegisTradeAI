import os
import smtplib
import logging
import traceback
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587


def send_email(subject: str, body: str, to_address: str = None) -> bool:
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        logger.error("Gmail credentials missing from .env — cannot send email")
        return False

    recipient = to_address or GMAIL_ADDRESS

    msg = MIMEMultipart()
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        logger.info(f"Email sent successfully to {recipient}")
        return True
    except Exception:
        logger.error("Failed to send email.")
        logger.error(traceback.format_exc())
        return False


def send_signal_alert(signal: dict) -> bool:
    subject = f"AegisTradeAI Signal: {signal['action']} {signal['symbol']}"
    body = (
        "New signal received:\n\n"
        f"Symbol: {signal['symbol']}\n"
        f"Action: {signal['action']}\n"
        f"Price: {signal['price']}\n"
    )
    return send_email(subject, body)


def send_error_alert(error_message: str, context: str = "") -> bool:
    """
    Sends an alert email when the bot encounters an unexpected error.
    """
    subject = "AegisTradeAI ERROR — Action Needed"
    body = (
        "AegisTradeAI encountered an error.\n\n"
        f"Context: {context}\n\n"
        f"Error:\n{error_message}\n"
    )
    return send_email(subject, body)
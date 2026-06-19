import os
import smtplib
import logging
import traceback
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Read Gmail credentials from .env
GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587


def send_email(subject: str, body: str, to_address: str = None) -> bool:
    """
    Sends an email via Gmail SMTP.
    Returns True on success, False on failure.
    """

    # Diagnostic logging
    logger.info(f"Gmail address loaded: {GMAIL_ADDRESS}")
    logger.info(
        f"Gmail app password length: "
        f"{len(GMAIL_APP_PASSWORD) if GMAIL_APP_PASSWORD else 0}"
    )

    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        logger.error(
            "Gmail credentials missing from .env — cannot send email"
        )
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

            logger.info("Attempting Gmail login...")
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)

            logger.info("Login successful. Sending email...")
            server.send_message(msg)

        logger.info(f"Email sent successfully to {recipient}")
        return True

    except Exception:
        logger.error("Failed to send email.")
        logger.error(traceback.format_exc())
        return False


def send_signal_alert(signal: dict) -> bool:
    """
    Formats and sends an alert email for a received trading signal.
    """

    subject = (
        f"AegisTradeAI Signal: "
        f"{signal['action']} {signal['symbol']}"
    )

    body = (
        "New signal received:\n\n"
        f"Symbol: {signal['symbol']}\n"
        f"Action: {signal['action']}\n"
        f"Price: {signal['price']}\n"
    )

    return send_email(subject, body)